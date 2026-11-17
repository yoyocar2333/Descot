"""Exact source-DAG plans within the homogeneous H/CX layer profile.

Unlike the historical H-first pool, ready H gates may be delayed or batched
in any nonempty subset. CX subsets reserve their complete oriented footprint.
Virtual/frame/readout closure remains eager. Mixed H/CX layers are outside
this declared pool, so this is not all conceivable gate-level schedules.
"""
from itertools import combinations

from public_candidate_pool import digest
from public_clifford import cnot_paths, positions_for, validate_plan


def enumerate_gate_plans(program, spacing=3, cap=4096):
    if type(cap) is not int or cap < 1:
        raise ValueError("Positive integer enumeration safety bound required")
    ops = program["operations"]
    if {o["name"] for o in ops} - {"h", "cx", "x", "measure", "barrier"}:
        raise ValueError("Unsupported source operations must not be dropped")
    positions = positions_for(program["logical_qubits"], spacing)
    plans = []

    def visit(done, orientations, layers):
        if len(done) == len(ops):
            if len(plans) >= cap:
                raise ValueError("Exact gate pool exceeds safety bound; no partial pool returned")
            plan = dict(mode="exact_h_cx_subsets_v1", spacing=spacing, layers=layers)
            validate_plan(program, plan)
            plans.append(plan)
            return
        ready = [o for o in ops if o["id"] not in done and set(o["predecessors"]) <= done]
        if not ready:
            raise ValueError("Invalid source DAG")
        instant = [o for o in ready if o["name"] in ("x", "measure", "barrier")]
        choices = []
        if instant:
            choices.append(("virtual_or_readout", instant))
        else:
            for kind in ("h", "cx"):
                candidates = [o for o in ready if o["name"] == kind]
                for count in range(1, len(candidates) + 1):
                    for subset in combinations(candidates, count):
                        footprints = [cnot_paths(*o["qubits"], positions, orientations)[2]
                                      if kind == "cx" else {positions[o["qubits"][0]]}
                                      for o in subset]
                        if all(not (a & b) for i, a in enumerate(footprints) for b in footprints[i+1:]):
                            choices.append((kind, subset))
        for kind, chosen in choices:
            after = list(orientations)
            for op in chosen:
                if op["name"] == "h":
                    after[op["qubits"][0]] ^= 1
            ids = [o["id"] for o in chosen]
            visit(done | set(ids), after, layers + [dict(
                kind=kind, operation_ids=ids, orientation_before=list(orientations),
                orientation_after=after)])

    visit(set(), [0] * len(positions), [])
    if len({digest(p) for p in plans}) != len(plans):
        raise AssertionError("Duplicate plan")
    return plans
