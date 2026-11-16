"""Replay the post-report planning audit. No compilation or Monte Carlo shots.

python audit_post_report.py          # write the derived inventory
python audit_post_report.py --check  # verify without modifying any file
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/post_report_2026-11-16/inventory.json"
SOURCES = [
    "results/public_lookahead_2026-11-03/summary.json",
    "results/public_bell_2026-11-04/summary.json",
    "results/public_candidates_2026-11-02/development_pool.json",
    "results/public_candidates_2026-11-02/evaluation.json",
    "results/transfer_2026-11-05/evaluation.json",
    "benchmarks/public_2026-11-02/manifest.json",
    "benchmarks/public_2026-11-04/manifest.json",
    "benchmarks/public_2026-11-05/manifest.json",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build_inventory():
    data = {p: json.loads((ROOT / p).read_text()) for p in SOURCES}
    lookahead, bell, pool, evaluation, transfer = [data[p] for p in SOURCES[:5]]
    rows = lookahead["records"]
    require(len(rows) == lookahead["source_conditions"] == 30, "hs4 route count changed")
    hs4_groups = []
    for spacing in sorted({r["spacing"] for r in rows}):
        group = [r for r in rows if r["spacing"] == spacing]
        circuits = sorted({r["noisy_circuit_sha256"] for r in group})
        selected = sorted({r["candidate_id"] for r in group})
        require(len(group) == 15 and len(circuits) == 1 and selected == ["p12"],
                "hs4 convergence changed")
        hs4_groups.append(dict(spacing=spacing, route_settings=len(group),
                               selected_candidates=selected, noisy_circuit_sha256=circuits))

    depth_counts = Counter(r["features"]["physical_layers"] for r in pool)
    minimum = min(depth_counts)
    minimum_ids = sorted(r["candidate_id"] for r in pool
                         if r["features"]["physical_layers"] == minimum)
    require(len(pool) == 13 and minimum == 9 and minimum_ids == ["p12"],
            "minimum-depth competition changed")
    decisions = evaluation["decisions"]
    require({r["candidate_id"] for r in decisions if r["pool"] == "all"} == {"p12"},
            "unrestricted hs4 selection changed")
    require({r["pool_size"] for r in decisions if r["pool"] == "serial_matched"} == {6},
            "restricted-pool size changed")

    matches = bell["method_sample_matches"]
    require(len(matches) == bell["source_routes"] == 30, "Bell(6) route count changed")
    bell_groups = []
    for geometry in sorted({r["route_id"].split("_")[0] for r in matches}):
        group = [r for r in matches if r["route_id"].startswith(geometry + "_")]
        samples = sorted({r["sample_id"] for r in group})
        require(len(group) == 15 and len(samples) == 1, "Bell(6) convergence changed")
        bell_groups.append(dict(geometry=geometry, route_settings=len(group),
                                reused_sample_ids=samples))

    routes = transfer["unconstrained_routes"]
    require(len(routes) == 60, "transfer route count changed")
    transfer_groups = []
    for workload, spacing in sorted({(r["workload"], r["spacing"]) for r in routes}):
        group = [r for r in routes if (r["workload"], r["spacing"]) == (workload, spacing)]
        circuits = sorted({r["shared_circuit"] for r in group})
        require(len(group) == 15 and len(circuits) == 1, "transfer convergence changed")
        transfer_groups.append(dict(workload=workload, spacing=spacing,
                                    route_settings=len(group), noisy_circuit_sha256=circuits))
    return {
        "schema": "post_report_planning_audit_v1",
        "date": "2026-11-16",
        "evidence_base_commit": "2e629ac245c32569a656bd3ec88c972a85f53aa0",
        "new_shots": 0,
        "new_routing_measurements": 0,
        "operation": "Read-only reanalysis of already observed records; no circuit recompile.",
        "inputs": [{"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
                   for p in SOURCES],
        "hs4_unrestricted_routes": hs4_groups,
        "hs4_pool": {
            "candidate_count": len(pool),
            "physical_layer_counts": {str(k): v for k, v in sorted(depth_counts.items())},
            "minimum_physical_layers": minimum, "minimum_candidate_ids": minimum_ids,
            "serial_matched_candidate_count": 6,
            "scope": "13 H-first canonical plans, not all possible gate-level schedules.",
        },
        "bell6_unrestricted_routes": bell_groups,
        "transfer_unrestricted_routes": transfer_groups,
        "future_split_policy": "All results observed by 2026-11-16 are development only for new hypotheses.",
        "conclusion": "Existing unrestricted controls often select identical complete circuits. "
                      "Use them as convergence controls; require new fully supported workloads with "
                      "real competing schedules before evaluating a new selection rule.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build_inventory()
    if args.check:
        require(OUT.is_file() and json.loads(OUT.read_text()) == result,
                "inventory missing or inconsistent; rerun audit_post_report.py")
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print("PASS: 120 archived route settings audited; 13-plan hs4 pool; 0 new shots.")


if __name__ == "__main__":
    main()
