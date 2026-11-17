"""Signed stabilizer validation without Monte Carlo or ideal sampling.

Uses exact DEM determinism plus tableau reference trajectories and existing
TQEC/source certificates. Tests
only the declared real-Clifford H/X/CX profile, not arbitrary geometry/gates.
"""
from itertools import product
import hashlib
import time

import stim
import numpy as np

from public_clifford import (generate_program, logical_circuit, signed_input,
                             final_fault)
from schedule_circuit import _rank


def check_exact(circuit, meta, program, complete_z=False):
    n = program["logical_qubits"]
    flows = meta["external_flows"]
    physical_unitary = stim.Tableau.from_circuit(logical_circuit(program, False))
    original_unitary = stim.Tableau.from_circuit(logical_circuit(program, True))
    relations = []
    for f in flows:
        a, b = stim.PauliString(f[:n]), stim.PauliString(f[n:])
        if physical_unitary(a) != b:
            raise AssertionError("Physical relation differs from complete source H/CX unitary")
        parity = sum(meta["frame_x"][q] if axis == "Z" else
                     meta["frame_z"][q] if axis == "X" else 0
                     for q, axis in enumerate(f[n:])) % 2
        framed = b.copy()
        framed.sign = (-1) ** parity
        if original_unitary(a) != framed:
            raise AssertionError("Original X-frame propagation differs")
        relations.append(dict(input=str(a), output=str(framed)))
    if complete_z:
        if meta["input_bases"] != "z" * n or meta["output_bases"] != "z" * n:
            raise AssertionError("Complete original Z boundaries required")
        if len(flows) != n or circuit.num_observables != n:
            raise AssertionError("Incomplete output basis")
        for part in (slice(0, n), slice(n, 2*n)):
            if any(set(f[part]) - {"I", "Z"} for f in flows):
                raise AssertionError("Not a Z-readout space")
            if _rank([[p != "I" for p in f[part]] for f in flows], n) != n:
                raise AssertionError("Output/input basis lacks full rank")
    circuit.detector_error_model()  # Reject nondeterministic detectors/observables.
    converter = circuit.compile_m2d_converter()

    def check_reference(c, parities):
        # DEM construction proves branch-independent annotated parities. The
        # exact tableau reference then fixes their signs, relative to the
        # original converter's reference. No sampler or random shots.
        c.detector_error_model()
        dets, obs = converter.convert(measurements=c.reference_sample()[None, :],
                                      separate_observables=True)
        if np.any(dets) or not np.array_equal(obs[0], np.array(parities, dtype=bool)):
            raise AssertionError("Exact signed detector/observable reference differs")
    records = []
    for bits in product((0, 1), repeat=n):
        c = signed_input(circuit, meta, bits)
        parities = [sum(bit for bit, p in zip(bits, f[:n]) if p != "I") % 2 for f in flows]
        check_reference(c, parities)
        records.append(dict(input_signs=list(bits), observable_parities=parities))
    faults = []
    if complete_z:
        for q in range(n):
            # has_flow intentionally ignores noise. Turn the known p=1
            # final readout fault into an actual deterministic Pauli gate.
            injected = stim.Circuit()
            for inst in final_fault(circuit, meta, q):
                if inst.name in ("X_ERROR", "Z_ERROR"):
                    if inst.gate_args_copy() != [1.0]:
                        raise AssertionError("Expected deterministic validation fault")
                    injected.append(inst.name[0], inst.targets_copy())
                else:
                    injected.append(inst)
            parities = [int(f[n+q] != "I") for f in flows]
            if not any(parities):
                raise AssertionError("Known final logical fault not preserved")
            check_reference(injected, parities)
            faults.append(dict(qubit=q, observable_flips=parities))
    return dict(exact=True, sampler_calls=0, signed_inputs=records, final_faults=faults,
                detector_checks=circuit.num_detectors, logical_relations=relations,
                checker="DEM determinism plus exact tableau reference signs; no sampler",
                full_z_readout_rank=n if complete_z else None)


def check_generators_exact(program, plan, artifact_dir=None):
    """Compile all 2n mixed-boundary generator experiments; exact checks only."""
    n = program["logical_qubits"]
    unitary = stim.Tableau.from_circuit(logical_circuit(program, False))
    records = []
    for axis in "xz":
        for q in range(n):
            out = unitary.x_output(q) if axis == "x" else unitary.z_output(q)
            outputs = str(out)[1:].replace("_", "Z").lower()
            if set(outputs) - {"x", "z"} or out.sign != 1:
                raise ValueError("Generator requires an unsupported signed/Y boundary")
            inputs = "z"*q + axis + "z"*(n-q-1)
            began = time.perf_counter()
            circuit, meta = generate_program(program, plan, inputs, outputs)
            compile_seconds = time.perf_counter() - began
            began = time.perf_counter()
            target = "I"*q + axis.upper() + "I"*(n-q-1) + str(out)[1:].replace("_", "I")
            found = False
            for mask in range(1, 1 << len(meta["external_flows"])):
                row = stim.PauliString("I"*(2*n))
                for i, f in enumerate(meta["external_flows"]):
                    if mask >> i & 1:
                        row *= stim.PauliString(f)
                if row == stim.PauliString(target):
                    found = True
                    break
            if not found:
                raise AssertionError("Required source generator missing from physical span")
            validation = check_exact(circuit, meta, program)
            validation_seconds = time.perf_counter() - began
            raw = str(circuit).encode()
            sha = hashlib.sha256(raw).hexdigest()
            if artifact_dir is not None:
                (artifact_dir / (sha + ".stim")).write_bytes(raw)
            records.append(dict(input_generator=axis.upper()+str(q), target_flow=target,
                                ideal_sha256=sha, backend_meta=meta,
                                compile_seconds=compile_seconds,
                                exact_validation_seconds=validation_seconds,
                                validation=validation))
    return records
