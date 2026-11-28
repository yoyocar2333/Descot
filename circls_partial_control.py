"""Complete terminal-output adapter to CircLS's documented PPM entry point.

Clifford absorption and native re-selection/scheduling are upstream work.
This adapter selects the original terminal outputs BEFORE those passes;
an unmeasured flag is not promoted into an application output.
"""
from collections import Counter
import stim
from circls_native_control import combine_specs, rank, serialize


def source_unitary(program, plan, mask=0):
    """Keep every gate and readout in the trace; hand unitary to PBC loader.

    Original terminal reads are represented by the explicit output map.
    They are not replaced by an unconditional all-qubit readout.
    """
    reads = sorted(program['terminal_readout'], key=lambda r: r['classical_bit'])
    if ([r['classical_bit'] for r in reads] != list(range(program['classical_bits']))
            or len({r['qubit'] for r in reads}) != len(reads)):
        raise ValueError('Require all original terminal outputs, without duplicates')
    qasm, logical, trace = serialize(program, plan, mask)
    if Counter(trace) != Counter(range(len(program['operations']))):
        raise ValueError('Incomplete source trace')
    unitary = '\n'.join(line for line in qasm.splitlines() if not line.startswith('measure '))+'\n'
    return unitary, logical, trace, reads


def prepare(program, plan, mask, scheduled):
    """Use the pinned author's passes on the exact original-output Pauli IR."""
    from circls.interop.nwqec.frontend import load_clifford_mpauli
    from circls.interop.ir.pauli_ir import PauliCircuit
    from circls.compiler.measure_reduce import reduce_measurements, verify_reconstruction
    from circls.interop.ir.pauli_algebra import (reorder_weight1_last, y_free_sweep,
                                                drop_free_prefix, defer_weight1_terminal)
    from circls.compiler.scheduling import schedule_ops, verify_schedule
    from circls.interop.ir.gosc_gadgets import expand_gadgets
    unitary, logical, trace, reads = source_unitary(program, plan, mask)
    raw = load_clifford_mpauli(unitary)
    n = program['logical_qubits']; inverse = logical.to_tableau().inverse()
    for q, op in enumerate(raw.ops):
        p = stim.PauliString(n)
        for k, letter in op.paulis.items(): p[k] = letter
        p.sign = op.sign
        z = stim.PauliString(n); z[q] = 'Z'
        if op.kind != 'm' or p != inverse(z):
            raise AssertionError('Native source pullback differs from full Clifford unitary')
    selected = PauliCircuit(n, [raw.ops[r['qubit']] for r in reads])
    original_paulis = []
    for op in selected.ops:
        p = stim.PauliString(n)
        for q, letter in op.paulis.items(): p[q] = letter
        p.sign = op.sign
        original_paulis.append(str(p))
    reduced, reconstruction = reduce_measurements(selected)
    verify_reconstruction(selected, reduced, reconstruction)
    ordered, perm = reorder_weight1_last(reduced)
    swept, deferred = defer_weight1_terminal(drop_free_prefix(y_free_sweep(ordered)))
    load_trace = [perm[p] for p in deferred]
    if scheduled:
        previous = swept
        swept, order = schedule_ops(swept, parallel=True)
        verify_schedule(previous, swept, order)
        if any(o.kind != 'm' for o in previous.ops):
            raise ValueError('Declared partial-output control requires m-only Z IR')
        load_trace = [load_trace[k] for k in order]
    expanded = expand_gadgets(swept)
    if expanded.num_data != n or expanded.gadgets or any(
            set(op.targets.values())-{'Z'} for op in expanded.ops):
        raise ValueError('Outside declared complete Z-product readout domain')
    return expanded, reconstruction, load_trace, dict(
        unitary_qasm=unitary, source_instruction_trace=trace,
        original_output_mapping=reads, original_input_observables=original_paulis,
        source_tableau=str(logical.to_tableau()))


def literal_joint_specs(cp):
    """Read actual joint POST closures, never a constant p=0 tracker oracle.

    Restricted to gadget-free commuting Z products; other domains fail.
    Signs, measurement-order permutations and re-selection are composed.
    """
    from circls.interop.ir.gosc_gadgets import folded_out_bits, step_roles
    from circls.tools.reporting import _support_recs
    prog = cp.program
    if prog.gadgets or any(set(op.targets.values())-{'Z'} for op in prog.ops):
        raise ValueError('Literal adapter requires gadget-free Z-product outputs')
    roles = step_roles(prog); folded = folded_out_bits(prog)
    steps = {bit: j for j, (kind, bit) in enumerate(roles) if kind == 'm'}
    specs = []
    for i, bit in enumerate(prog.out_bits):
        if bit.gadgets: raise ValueError('Gadget-conditioned outputs unsupported')
        if i in folded:
            q, letter = folded[i]
            ids = _support_recs(cp.experiment, f'q{q}', letter)
        else:
            ids = cp.experiment.step_joint_records_post.get(steps[i])
        if not ids: raise ValueError('Original output lacks actual physical records')
        specs.append((sorted(set(ids)), int(bit.flip)))
    r = cp.reconstruction
    out = combine_specs(specs, cp.m_load_trace,
                        None if r is None else r.inverse, None if r is None else r.const)
    if any(not ids for ids, _ in out) or rank([sum(1 << i for i in ids) for ids, _ in out]) != len(out):
        raise ValueError('Incomplete literal original-output basis')
    return out


def record_fault(circuit, record):
    """One physical anti-commuting Pauli immediately before a readout."""
    out = stim.Circuit(); count = 0; found = False
    gates = {'M':'X', 'MZ':'X', 'MX':'Z', 'MY':'X', 'MR':'X', 'MRZ':'X', 'MRX':'Z', 'MRY':'X'}
    for inst in circuit.flattened():
        k = stim.Circuit(str(inst)).num_measurements
        if count <= record < count+k:
            if inst.name not in gates: raise ValueError('Unsupported measurement fault')
            out.append(gates[inst.name], [inst.targets_copy()[record-count].value]); found = True
        count += k; out.append(inst)
    if not found: raise ValueError('Readout record out of range')
    return out
