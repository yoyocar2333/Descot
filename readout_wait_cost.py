"""Uncalibrated logical-Pauli idle proxy and outcome-free offline selector.

Known Clifford propagation, not a decoder-risk model or a new routing method.
Only the complete terminal Z space of the supported public backend is accepted.
No physical error probabilities, decoder labels, or risk weights are inferred.
"""
from fractions import Fraction

import stim

from public_candidate_pool import digest
from public_clifford import validate_plan
from readout_visibility import validate_basis


def wait_cost(program, plan, observables):
    """Inject equiprobable abstract X/Y/Z during each protected data-idle layer.

    Each physical H/CX layer is three template block-z. Faults on idle wires
    commute with that layer, so propagate from its end through the full source
    suffix. Deferred terminal measurements and virtual frames follow the backend
    policy. This does not model physical syndrome faults or memory calibration.
    """
    if {o["name"] for o in program["operations"]} - {"h", "x", "cx", "measure", "barrier"}:
        raise ValueError("Unsupported source gates must not be omitted from propagation")
    validate_plan(program, plan)
    n = program["logical_qubits"]
    basis = validate_basis(observables)
    if len(basis) != n or len(basis[0]) != n or any(
            p[q] not in (0, 3) for p in basis for q in range(n)):
        raise ValueError("Complete independent terminal Z readout required")
    layers = plan["layers"]
    ops = program["operations"]
    records = []
    z = 0
    score = Fraction(0)
    for index, layer in enumerate(layers):
        if layer["kind"] == "virtual_or_readout":
            continue
        active = {q for i in layer["operation_ids"] for q in ops[i]["qubits"]}
        suffix = stim.Circuit()
        suffix_ids = []
        for later in layers[index + 1:]:
            for i in later["operation_ids"]:
                op = ops[i]
                if op["name"] in ("h", "x", "cx"):
                    suffix.append(op["name"].upper(), op["qubits"])
                    suffix_ids.append(i)
        for q in sorted(set(range(n)) - active):
            events = []
            for label in "XYZ":
                fault = stim.PauliString(n)
                fault[q] = label
                terminal = fault.after(suffix)
                signature = [not terminal.commutes(p) for p in basis]
                visible = any(signature)
                score += Fraction(3, 3) * visible
                events.append(dict(pauli=label, terminal_pauli=str(terminal),
                                   signature=signature, visible_any=visible))
            records.append(dict(qubit=q, start_block_z=z, stop_block_z=z + 3,
                                plan_layer_index=index, suffix_operation_ids=suffix_ids,
                                pauli_events=events))
        z += 3
    return dict(score_numerator=score.numerator, score_denominator=score.denominator,
                unit="template block-z times raw visibility; not a failure probability",
                complete_terminal_basis=[str(p) for p in basis],
                total_protected_idle_block_z=3 * len(records), idle_layers=records)


def exact_score(record):
    return Fraction(record["score_numerator"], record["score_denominator"])


METRICS = ("depth", "total_wait", "resource", "raw_readout_wait", "no_position",
           "cx_recurrence", "segmented_wait_squared")


def select(rows, costs, qualified_ids, reference_id, metric, evaluation_budget):
    """Shared full pool -> hard minimum depth -> cost -> reference-preserving tie.

    A missing minimum candidate certificate or insufficient evaluation budget
    fails the comparison. Neither silently restricts the pool to favor a method.
    Geometry is held fixed, so geometry ablation is unidentifiable in this gate.
    """
    if metric not in METRICS:
        raise ValueError("Unknown comparison metric")
    ids = [r["candidate_id"] for r in rows]
    if not rows or len(set(ids)) != len(ids) or set(costs) != set(ids):
        raise ValueError("One cost per unique complete-pool candidate required")
    if type(evaluation_budget) is not int or evaluation_budget < len(rows):
        raise ValueError("Insufficient common complete-pool evaluation budget")
    minimum = min(r["features"]["physical_layers"] for r in rows)
    shortlist = [r for r in rows if r["features"]["physical_layers"] == minimum]
    short_ids = {r["candidate_id"] for r in shortlist}
    if not short_ids <= set(qualified_ids) or reference_id not in short_ids:
        raise ValueError("All minimum candidates and the reference need physical qualification")

    def value(row):
        f = row["features"]
        if metric == "raw_readout_wait":
            return exact_score(costs[row["candidate_id"]])
        if metric == "no_position":
            return Fraction(2, 3) * f["total_protected_idle_block_z"]
        if metric == "resource":
            return f["data_reservation_block_z"] + f["ancilla_reservation_block_z"]
        field = {"depth": "physical_layers", "total_wait": "total_protected_idle_block_z",
                 "cx_recurrence": "cx_gap_squared_block_z2",
                 "segmented_wait_squared": "squared_protected_idle_block_z2"}[metric]
        return f[field]

    best = min(shortlist, key=lambda r: (value(r), r["candidate_id"] != reference_id,
                                         r["candidate_id"]))
    optimum = Fraction(value(best))
    return dict(metric=metric, candidate_id=best["candidate_id"], reference_id=reference_id,
                switched=best["candidate_id"] != reference_id,
                optimum_numerator=optimum.numerator, optimum_denominator=optimum.denominator,
                tied_optima=[r["candidate_id"] for r in shortlist if value(r) == optimum],
                pool_size=len(rows), minimum_depth=minimum, shortlist_size=len(shortlist),
                pool_sha256=digest(rows), evaluation_budget=evaluation_budget,
                shared_feature_rows=len(rows), shared_raw_cost_cache_size=len(costs),
                additional_raw_cost_calls=0,
                shortlist_metric_evaluations=len(shortlist), mu=0)
