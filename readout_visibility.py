"""Exact *raw* Pauli visibility diagnostic, not a decoded-risk estimator.

The observables describe one commuting readout space. Their rank is checked,
but completeness for an application must be established by its compiler.
This module neither selects schedules nor enables the general risk weight.
"""
import math

import stim


def validate_basis(observables):
    basis = tuple(stim.PauliString(p) for p in observables)
    if not basis or len({len(p) for p in basis}) != 1 or not len(basis[0]):
        raise ValueError("A nonempty, equal-width observable basis is required")
    pivots = {}
    n = len(basis[0])
    for i, p in enumerate(basis):
        if p.sign not in (1, -1):
            raise ValueError("Readout observables must be Hermitian")
        if any(not p.commutes(q) for q in basis[:i]):
            raise ValueError("Readout observables must commute")
        # Stim's local labels are I=0, X=1, Y=2, Z=3. Ignore global sign.
        row = sum((int(p[q] in (1, 2)) << q)
                  | (int(p[q] in (2, 3)) << (q + n)) for q in range(n))
        while row:
            pivot = row.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = row
                break
            row ^= pivots[pivot]
        if not row:
            raise ValueError("Observable generators must be independent modulo phase")
    return basis


def fault_signature(fault, observables):
    """Return which generators anticommute with one raw terminal Pauli fault."""
    basis = validate_basis(observables)
    error = stim.PauliString(fault)
    if len(error) != len(basis[0]):
        raise ValueError("Fault and readout widths differ")
    return tuple(not error.commutes(p) for p in basis)


def raw_visibility(faults, observables):
    """Sum event weights, counting a visible event once or per generator.

    Weights are nonnegative diagnostic weights. Even if they are individual
    fault probabilities, this is only a first-order sum: it omits joint-event
    cancellation, syndrome information, and decoder corrections. It is not a
    calibrated probability of decoded-circuit failure.
    """
    basis = validate_basis(observables)
    records = []
    for fault, weight in faults:
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("Fault weights must be finite and nonnegative")
        signature = fault_signature(fault, basis)
        records.append(dict(fault=str(stim.PauliString(fault)), weight=weight,
                            signature=list(signature)))
    return {
        "joint_first_order_weight": math.fsum(r["weight"] for r in records
                                              if any(r["signature"])),
        "marginal_sum_weight": math.fsum(r["weight"] * sum(r["signature"])
                                         for r in records),
        "events": records,
    }
