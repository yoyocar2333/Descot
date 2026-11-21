"""Full source serialization and exact literal readout checks for native CircLS.

This is a separate compiler reference, not admission to the gate-preserving
DASCOT/TQEC pool. No Pauli measurement lowering is called a new schedule.
"""
from collections import Counter
from pathlib import Path
import subprocess
import sys

import stim

from public_clifford import validate_plan

COMMIT = "1501f632f28e54188e57042abeaf450c3a300870"


def load_author(repo):
    repo = Path(repo).resolve()
    if subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() != COMMIT:
        raise ValueError("Wrong CircLS revision")
    if subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip():
        raise ValueError("CircLS worktree must be clean")
    sys.path[:0] = [str(repo), str(repo / "experiments")]
    import circls
    if not Path(circls.__file__).resolve().is_relative_to(repo):
        raise ValueError("Wrong CircLS package loaded")
    return circls


def serialize(program, plan, input_mask=0):
    """All source gates once; terminal measurements deferred to common end.

    This is the existing backend policy, not cancellation or gate deletion.
    Prefix X gates are explicit signed-input validation only.
    """
    if {o["name"] for o in program["operations"]} - {"h", "x", "cx", "measure", "barrier"}:
        raise ValueError("Unsupported gate must not be dropped")
    validate_plan(program, plan)
    n = program["logical_qubits"]
    if type(input_mask) is not int or not 0 <= input_mask < 2 ** n:
        raise ValueError("Invalid input mask")
    for o in program["operations"]:
        if o["name"] == "measure" and any(o["qubits"][0] in p["qubits"]
                for p in program["operations"][o["id"] + 1:]):
            raise ValueError("Cannot defer a nonterminal measurement")
    text = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{n}];", f"creg c[{n}];"]
    text += [f"x q[{q}];" for q in range(n) if input_mask & (1 << q)]
    trace, deferred = [], []
    logical = stim.Circuit()
    for q in range(n):
        if input_mask & (1 << q):
            logical.append("X", [q])
    for layer in plan["layers"]:
        for i in layer["operation_ids"]:
            op = program["operations"][i]
            trace.append(i)
            if op["name"] == "measure":
                deferred.append(op)
            else:
                text.append(op["name"] + " " + ",".join(f"q[{q}]" for q in op["qubits"]) + ";")
                if op["name"] != "barrier":
                    logical.append(op["name"].upper(), op["qubits"])
    text += [f"measure q[{o['qubits'][0]}] -> c[{o['clbits'][0]}];" for o in sorted(deferred, key=lambda o: o["id"])]
    if Counter(trace) != Counter(range(len(program["operations"]))):
        raise ValueError("Incomplete source trace")
    return "\n".join(text) + "\n", logical, trace


def rank(rows):
    pivots = {}
    for row in rows:
        while row:
            p = row.bit_length() - 1
            if p not in pivots:
                pivots[p] = row
                break
            row ^= pivots[p]
    return len(pivots)


def combine_specs(specs, trace, inverse=None, const=None):
    """Literal physical-record affine expressions in original qubit load order."""
    if sorted(trace) != list(range(len(specs))):
        raise ValueError("Nonbijective load trace")
    loaded = [None] * len(specs)
    for i, j in enumerate(trace):
        loaded[j] = specs[i]
    if inverse is None:
        return loaded
    out = []
    for indices, value in zip(inverse, const, strict=True):
        records = set()
        for i in indices:
            ids, flip = loaded[i]
            records.symmetric_difference_update(ids)
            value ^= flip
        out.append((sorted(records), int(value)))
    return out


def literal_specs(cp):
    """Only the observed folded-Z/no-gadget native domain; fail elsewhere.

    CircLS's _tracker_bit_specs is a p=0 logical oracle, NOT a noisy record
    decoder. Literal final data-readout parities are used here instead.
    """
    from circls.interop.ir.gosc_gadgets import folded_out_bits
    from circls.tools.reporting import _support_recs
    prog = cp.program
    folded = folded_out_bits(prog)
    if prog.gadgets or len(folded) != len(prog.out_bits) or cp.routes:
        raise ValueError("Literal adapter supports only fully folded terminal data reads")
    specs = []
    for i, ob in enumerate(prog.out_bits):
        q, letter = folded[i]
        if letter != "Z" or ob.gadgets:
            raise ValueError("Outside folded terminal Z support")
        specs.append((_support_recs(cp.experiment, f"q{q}", "Z"), ob.flip))
    r = cp.reconstruction
    return combine_specs(specs, cp.m_load_trace,
                         None if r is None else r.inverse, None if r is None else r.const)


def evaluate(records, specs):
    return [int(flip) ^ (sum(int(records[r]) for r in ids) % 2) for ids, flip in specs]


def basis_view(circuit, specs):
    """Separate annotated view; preserve every physical gate, detector and read.

    The unmodified native circuit remains the authoritative compiler artifact.
    Only OBSERVABLE_INCLUDE annotations are replaced by the complete original
    output basis; signs are in the classical affine map, not DEM flip labels.
    """
    if rank([sum(1 << i for i in ids) for ids, _ in specs]) != len(specs):
        raise ValueError("Literal output record basis is incomplete")
    out = stim.Circuit()
    for inst in circuit.flattened():
        if inst.name != "OBSERVABLE_INCLUDE":
            out.append(inst)
    for k, (ids, _) in enumerate(specs):
        out.append("OBSERVABLE_INCLUDE", [stim.target_rec(i - out.num_measurements) for i in ids], k)
    return out


def final_record_fault(circuit, record):
    """Insert X immediately before the selected final Z measurement; no shots."""
    out = stim.Circuit()
    count = 0
    found = False
    for inst in circuit.flattened():
        if inst.name in ("M", "MZ"):
            targets = inst.targets_copy()
            if count <= record < count + len(targets):
                out.append("X", [targets[record - count].value])
                found = True
            count += len(targets)
        else:
            count += stim.Circuit(str(inst)).num_measurements
        out.append(inst)
    if not found:
        raise ValueError("Selected record is not a Z readout")
    return out
