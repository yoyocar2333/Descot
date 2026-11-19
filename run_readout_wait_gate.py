"""Development-only discriminability gate. No sampling and no held-out reads."""
import argparse
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import time

from core import COMMIT, load_core
from public_candidate_pool import digest, features
from public_gate_pool import enumerate_gate_plans
from public_lookahead import schedule
from readout_wait_cost import METRICS, exact_score, select, wait_cost
from run_grover_competition import source_program

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT / "results/grover_competition_2026-11-17"
DEFAULT = ROOT / "results/readout_wait_gate_2026-11-19"
CODE = ["readout_wait_cost.py", "run_readout_wait_gate.py", "readout_visibility.py",
        "public_candidate_pool.py", "public_gate_pool.py", "public_clifford.py",
        "public_lookahead.py", "lookahead.py", "core.py", "requirements-lock.txt"]
CODE += ["run_grover_competition.py", "run_public_audit.py", "tests/test_readout_wait_cost.py"]
INPUTS = ["candidate_pool.json", "physical_index.json", "resource_certificate.json", "program.json"]
PROTOCOL = dict(id="raw_readout_wait_development_gate_20261119_v1",
                status="mechanism test, not calibrated evaluation freeze",
                family="grover_search development only", spacing=3,
                concurrency_cap=None, enumeration_safety_bound=4096,
                common_offline_pool_size=175, per_method_evaluation_budget=175,
                offline_stages=["full legal source-DAG/footprint pool", "minimum physical depth",
                                "all minimum candidates certified", "cost", "preserve parallel reference on ties"],
                complete_readout=["ZI", "IZ"],
                hypothesis="Equiprobable single abstract logical X/Y/Z per unit protected data idle; propagate full scheduled suffix and count any terminal output flip once",
                noise="No calibrated logical noise assumed by proxy; existing physical certificates use d=3, p=.001, TQEC uniform-depolarizing",
                decoder="Existing ordinary uncorrelated PyMatching/decomposed DEM certificates; no decoder invoked by scorer",
                routing_controls="Pinned author search with existing oriented-footprint adapter; one/two front progress controls share cap24 order generator and ceiling48. Separate H-first search domain, not the 175-plan offline evaluation budget.",
                routing_seeds=[1, 2, 3], shots=0, monte_carlo_seeds=[], counts=None,
                confidence_interval=None, stopping_rule="No sampling at this mechanism gate. If no minimum-depth score contrast, stop this proxy version before calibration.",
                mu=0)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(plan):
    return [(l["kind"], sorted(l["operation_ids"]), l["orientation_before"],
             l["orientation_after"]) for l in plan["layers"]]


def build():
    if platform.python_version_tuple()[:2] != ("3", "12"):
        raise ValueError("Python 3.12 required")
    _, program = source_program()
    began = time.perf_counter()
    plans = enumerate_gate_plans(program, spacing=3, cap=4096)
    rows = [dict(candidate_id=f"g{i:03}", plan=p, plan_sha256=digest(p),
                 features=features(program, p)) for i, p in enumerate(plans)]
    construction_seconds = time.perf_counter() - began
    if rows != json.loads((PRIOR / "candidate_pool.json").read_text()) or len(rows) != 175:
        raise AssertionError("Frozen complete legal pool changed")
    physical = json.loads((PRIOR / "physical_index.json").read_text())
    minimum = min(r["features"]["physical_layers"] for r in rows)
    minima = [r for r in rows if r["features"]["physical_layers"] == minimum]
    if {r["candidate_id"] for r in physical} != {r["candidate_id"] for r in minima}:
        raise AssertionError("No minimum-depth candidate may be removed")
    for r in physical:
        certificate = json.loads((PRIOR / "certificates" / (r["candidate_id"] + ".json")).read_text())
        if r["plan_sha256"] != next(x["plan_sha256"] for x in rows if x["candidate_id"] == r["candidate_id"]):
            raise AssertionError("Certificate plan mismatch")
        if any(r[k] != certificate[k] for k in ("plan_sha256", "source_sha256", "ideal_sha256", "noisy_sha256", "dem_sha256")):
            raise AssertionError("Certificate hash index mismatch")
        if not certificate["validation"]["exact"] or certificate["validation"]["full_z_readout_rank"] != 2:
            raise AssertionError("Complete exact output qualification required")
    began = time.perf_counter()
    costs = {r["candidate_id"]: wait_cost(program, r["plan"], PROTOCOL["complete_readout"])
             for r in rows}
    scorer_seconds = time.perf_counter() - began
    if any(costs[r["candidate_id"]]["total_protected_idle_block_z"] !=
           r["features"]["total_protected_idle_block_z"] for r in rows):
        raise AssertionError("Idle accounting mismatch")
    base = load_core(ROOT.parent / "external/wisq")["sarouting"]
    routes = []
    controls_seconds = 0
    for seed in PROTOCOL["routing_seeds"]:
        local = {}
        for mode in ("author_profile", "one_step", "two_step"):
            began = time.perf_counter()
            result = schedule(program, mode, 3, seed, budget=48, candidate_cap=24, base=base)
            controls_seconds += time.perf_counter() - began
            matches = [r["candidate_id"] for r in rows if signature(r["plan"]) == signature(result["plan"])]
            if len(matches) != 1 or matches[0] not in {r["candidate_id"] for r in physical}:
                raise AssertionError("Routing control must match a complete qualified candidate")
            local[mode] = result
            routes.append(dict(mode=mode, seed=seed, candidate_id=matches[0], result=result))
        a, b = local["one_step"]["fronts"], local["two_step"]["fronts"]
        if len(a) != len(b) or any((x["ready_ids"], x["candidate_orders"]) !=
                                  (y["ready_ids"], y["candidate_orders"]) for x, y in zip(a, b)):
            raise AssertionError("Matched routing control pools differ")
    reference = next(r["candidate_id"] for r in routes if r["mode"] == "author_profile" and r["seed"] == 1)
    began = time.perf_counter()
    selections = [select(rows, costs, [r["candidate_id"] for r in physical], reference, m, 175)
                  for m in METRICS]
    selector_seconds = time.perf_counter() - began
    distinct = sorted({exact_score(costs[r["candidate_id"]]) for r in minima})
    if len(distinct) != 1:
        raise AssertionError("Observed flat-proxy decision must be reconsidered")
    data = dict(protocol=PROTOCOL, source_sha256=program["source_sha256"], pool_sha256=digest(rows),
                costs=costs, routing_controls=routes, selections=selections,
                qualified_physical_records=physical,
                score_histogram_by_depth={str(d): {str(s): sum(
                    r["features"]["physical_layers"] == d and exact_score(costs[r["candidate_id"]]) == s
                    for r in rows) for s in sorted({exact_score(costs[r["candidate_id"]])
                    for r in rows if r["features"]["physical_layers"] == d})}
                    for d in sorted({r["features"]["physical_layers"] for r in rows})},
                minimum_candidate_ids=[r["candidate_id"] for r in minima],
                decision="STOP raw equiprobable first-order Pauli visibility v1: no within-minimum-depth contrast. Core question unresolved; no calibration/held-out sampling authorized.",
                geometry_ablation="Unidentifiable: fixed common 310-site geometry and identical resource totals among minima. Proxy contains no geometry-dependent calibrated term.",
                new_shots=0, new_compilations=0, sampler_calls=0, counts=None, confidence_interval=None)
    timing = dict(pool_construction_and_features_seconds=construction_seconds,
                  scorer_only_seconds=scorer_seconds, offline_selector_all_metrics_seconds=selector_seconds,
                  routing_controls_construction_seconds=controls_seconds,
                  routing_benchmark_seconds=None, calibration_seconds=None, compile_seconds=None,
                  monte_carlo_seconds=None, decode_seconds=None,
                  note="Single-run stage accounting, not an independent performance benchmark. Physical timings remain in prior certificates.")
    return data, timing


def fingerprints():
    paths = CODE + [str((PRIOR / p).relative_to(ROOT)) for p in INPUTS]
    paths += ["archives/grover_competition_2026-11-17.zip",
              "benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json"]
    paths += [str(p.relative_to(ROOT)) for p in sorted((PRIOR / "certificates").glob("*.json"))]
    manifest = json.loads((ROOT / "benchmarks/public_2026-11-17/manifest.json").read_text())
    paths += ["benchmarks/public_2026-11-17/manifest.json"] + [f["path"] for f in manifest["files"]]
    paths += ["../external/wisq/src/wisq/" + f + ".py"
              for f in ("sarouting", "architecture", "phased_graph", "dascot")]
    return {p: sha(ROOT / p) for p in paths}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    data, timing = build()
    if args.check:
        assert json.loads(json.dumps(data)) == json.loads((args.output / "records.json").read_text())
        assert fingerprints() == json.loads((args.output / "environment.json").read_text())["files_sha256"]
        print("Replayed 175 costs, 12 qualified minima, 7 selectors and 9 routing controls; 0 new shots")
        return
    if args.output.exists():
        raise FileExistsError("Fresh output required; preserve frozen evidence")
    args.output.mkdir(parents=True)
    environment = dict(python=platform.python_version(), wisq_commit=COMMIT,
                       source_base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       packages={p: md.version(p) for p in ("stim", "pymatching", "tqec", "qiskit", "numpy")},
                       files_sha256=fingerprints())
    for name, obj in (("records", data), ("timing", timing), ("environment", environment)):
        (args.output / (name + ".json")).write_text(json.dumps(obj, indent=2) + "\n")
    print(data["decision"])


if __name__ == "__main__":
    main()
