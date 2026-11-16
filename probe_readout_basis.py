"""Replay exact mechanism checks. No workload compilation or Monte Carlo.

python probe_readout_basis.py [--check]
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import pymatching

from readout_visibility import fault_signature, raw_visibility

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/literature_gate_2026-11-16/basis_probe.json"


def build_probe():
    bases = [["ZI", "ZZ"], ["ZZ", "IZ"]]
    scenarios = {"A": [("XI", 0.0011)], "B": [("IX", 0.0010)]}
    rows = []
    for basis in bases:
        scores = {k: raw_visibility(v, basis) for k, v in scenarios.items()}
        rows.append(dict(basis=basis, scores=scores,
                         marginal_winner=min(scores, key=lambda k: scores[k]["marginal_sum_weight"]),
                         joint_winner=min(scores, key=lambda k: scores[k]["joint_first_order_weight"])))
    assert [r["marginal_winner"] for r in rows] == ["B", "A"]
    assert all(r["joint_winner"] == "B" for r in rows)

    # All 168 ordered bases of the three-dimensional Z-readout space,
    # against every three-qubit Pauli, including identity (64).
    basis_count = 0
    comparisons = 0
    for vectors in itertools.permutations(range(1, 8), 3):
        span = {0}
        for v in vectors:
            span |= {s ^ v for s in tuple(span)}
        if len(span) != 8:
            continue
        basis_count += 1
        basis = ["".join("Z" if v >> q & 1 else "I" for q in range(3)) for v in vectors]
        for chars in itertools.product("IXYZ", repeat=3):
            fault = "".join(chars)
            assert any(fault_signature(fault, basis)) == any(fault_signature(fault, ["ZII", "IZI", "IIZ"]))
            comparisons += 1
    assert basis_count == 168 and comparisons == 10752

    # A deterministic decoder example: raw observable flip != decoded failure.
    # This graph is a synthetic mechanism check, not a surface-code benchmark.
    matching = pymatching.Matching()
    matching.add_boundary_edge(0, fault_ids={0}, weight=1, error_probability=0.001)
    prediction = int(matching.decode([1])[0])
    assert prediction == 1
    return {
        "schema": "readout_basis_mechanism_probe_v1",
        "new_research_shots": 0,
        "new_workload_compilations": 0,
        "new_routing_measurements": 0,
        "scope": "Exact synthetic algebra/decoder checks; no public workload or performance evidence.",
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                          for p in ["readout_visibility.py", "probe_readout_basis.py"]},
        "basis_ranking_counterexample": rows,
        "basis_invariance": {"ordered_bases": basis_count, "paulis_per_basis": 64,
                             "exact_comparisons": comparisons, "failures": 0},
        "decoder_counterexample": {"syndrome": [1], "raw_observable_flip": 1,
                                   "decoder_prediction": prediction, "residual_any_error": 0},
        "decision": "Reject marginal-generator-count as a basis-independent any-error cost. "
                    "Joint raw visibility passes this necessary condition but remains an uncalibrated proxy.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build_probe()
    if args.check:
        if json.loads(OUT.read_text()) != result:
            raise ValueError("Stored probe differs from exact replay")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: 10752 exact basis checks; marginal ranking reversal; decoder counterexample; 0 research shots")


if __name__ == "__main__":
    main()
