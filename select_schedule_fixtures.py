"""Reproduce pre-noise development-fixture selection, retaining both directions."""
import argparse
import json
from pathlib import Path
import random

from core import load_core
from lookahead import Config, schedule
from route_adapter import sha256_json
from schedule_adapter import ProfileRouter

ROOT = Path(__file__).resolve().parent


def select(base):
    rng = random.Random(204)
    fixtures, trials = {}, []
    for index in range(3000):
        gates = [sorted(rng.sample(range(6), 2)) for _ in range(rng.randint(8, 16))]
        row = {"index": index, "program_sha256": sha256_json(gates), "gate_count": len(gates)}
        if {q for g in gates for q in g} != set(range(6)):
            trials.append({**row, "skipped": "not all six logical qubits used"})
            continue
        router = ProfileRouter(base, 6)
        args = (router, gates, router.architecture, list(router.mapping.items()), 1)
        one = schedule(*args, Config("one_step", 48, candidate_cap=16))
        two = schedule(*args, Config("two_step", 48, candidate_cap=16))
        row.update(one_depth=one["time_steps"], two_depth=two["time_steps"])
        trials.append(row)
        delta = two["time_steps"] - one["time_steps"]
        label = "two_shorter" if delta < 0 else "two_longer" if delta > 0 else "tie"
        if label != "tie" and label not in fixtures:
            fixtures[label] = {"case_id": label, "development_index": index,
                               "logical_qubits": 6, "gates": gates,
                               "one_depth": one["time_steps"], "two_depth": two["time_steps"]}
        if len(fixtures) == 2:
            break
    if len(fixtures) != 2:
        raise RuntimeError("Did not find both development cases within the declared bound")
    return {"id": "schedule_development_fixtures_20261102_v1", "search_seed": 204,
            "routing_seed": 1, "trials_limit": 3000, "trials_visited": len(trials),
            "logical_qubits": 6, "forward_cnot_count_range": [8, 16],
            "candidate_cap": 16, "front_evaluation_budget": 48,
            "selection": "First shorter and first longer two-step routed depth, before any noisy sampling. Deliberately selected development fixtures, never held-out performance evidence.",
            "trials": trials, "fixtures": fixtures,
            "control": {"case_id": "parallel_control", "logical_qubits": 4,
                        "gates": [[0, 1], [2, 3], [1, 2]],
                        "layers": {"parallel": [[0, 1], [2]], "serial": [[0], [1], [2]], "serial_reordered": [[1], [0], [2]]}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve the pre-sampling fixture definition")
    result = select(load_core(ROOT.parent / "external/wisq")["sarouting"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"trials_visited": result["trials_visited"], "fixtures": {k: {field: row[field] for field in ("development_index", "one_depth", "two_depth")} for k, row in result["fixtures"].items()}}))


if __name__ == "__main__":
    main()
