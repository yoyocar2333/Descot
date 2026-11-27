"""Lossless CZ lowering and complete original terminal-output basis.

Unmeasured logical qubits remain live in every existing TQEC graph layer.
Internal cleanup readout is excluded from the original application outputs.
This is a backend extension, not a new scheduling or Pauli-propagation method.
"""
from collections import Counter
from copy import deepcopy
from itertools import product
import numpy as np
import stim

from run_public_audit import inspect_qasm
from public_clifford import logical_circuit, final_fault
from exact_program_validation import check_exact


def load_partial_program(path):
    source = inspect_qasm(path)
    n, m = source['logical_qubits'], source['classical_bits']
    if not 2 <= n <= 6 or not 1 <= m <= n:
        raise ValueError('Require 2..6 logical qubits and 1..n original output bits')
    if set(source['operation_counts']) - {'h', 'x', 'cx', 'cz', 'measure', 'barrier'}:
        raise ValueError('Unsupported source instruction must be preserved and rejected')
    reads = [o for o in source['operations'] if o['name'] == 'measure']
    if (sorted(o['clbits'][0] for o in reads) != list(range(m))
            or len({o['qubits'][0] for o in reads}) != m):
        raise ValueError('Require one terminal, distinct-qubit readout per original classical bit')
    for o in reads:
        if any(o['qubits'][0] in later['qubits'] for later in source['operations'][o['id']+1:]):
            raise ValueError('Mid-circuit measurement is unsupported')
    ops, last, trace = [], {}, []
    for original in source['operations']:
        name, qs = original['name'], original['qubits']
        if name == 'cz':
            c, t = sorted(qs)
            pieces = [('h', [t]), ('cx', [c, t]), ('h', [t])]
        else:
            pieces = [(name, qs)]
        ids = []
        parents = [last[p] for p in original['predecessors']]
        for name, qubits in pieces:
            if name == 'cx' and qubits[0] >= qubits[1]:
                raise ValueError('Reverse CX is outside the declared physical geometry')
            i = len(ops)
            ops.append(dict(id=i, name=name, qubits=list(qubits),
                clbits=original['clbits'] if name == 'measure' else [],
                params=original['params'], predecessors=sorted(parents)))
            ids.append(i); parents = [i]
        last[original['id']] = ids[-1]
        trace.append(dict(original_id=original['id'], original_name=original['name'], lowered_ids=ids))
    out = {**deepcopy(source), 'operations': ops,
           'operation_counts': dict(sorted(Counter(o['name'] for o in ops).items())),
           'original_program': source, 'lowering_trace': trace,
           'unmeasured_logical_qubits': sorted(set(range(n)) - {o['qubits'][0] for o in reads}),
           'partial_profile_supported': True,
           'lowering_policy': 'CZ(a,b)=H(t) CX(c,t) H(t), c=min(a,b), t=max(a,b); no cancellation. All original quantum/classical DAG edges mapped to full lowering chains.'}
    original = stim.Circuit()
    for o in source['operations']:
        if o['name'] not in ('measure', 'barrier'):
            original.append(o['name'].upper(), o['qubits'])
    if stim.Tableau.from_circuit(original) != stim.Tableau.from_circuit(logical_circuit(out)):
        raise AssertionError('Complete lowered unitary differs from the original source')
    return out


def original_output_view(circuit, meta, program):
    """Invert the FULL Z-output span; retain every original classical output.

    No output or fault channel is chosen using noisy outcomes. The flag's
    physical gates, detectors, readouts and storage remain in the circuit.
    """
    n = program['logical_qubits']; flows = meta['external_flows']
    if len(flows) != n or circuit.num_observables != n:
        raise ValueError('Full internal Z-output span required before partial-output mapping')
    if meta['input_bases'] != 'z'*n or meta['output_bases'] != 'z'*n:
        raise ValueError('Original terminal Z readout requires all-Z boundaries')
    reads = sorted(program['terminal_readout'], key=lambda r: r['classical_bit'])
    masks, mapped = [], []
    for read in reads:
        q = read['qubit']; target = stim.PauliString(n); target[q] = 'Z'
        found = []
        for mask in range(1, 1 << n):
            f = stim.PauliString(2*n)
            for i, flow in enumerate(flows):
                if mask >> i & 1: f *= stim.PauliString(flow)
            if f[n:] == target: found.append((mask, f))
        if len(found) != 1:
            raise ValueError('Original output is absent or internal output basis is singular')
        mask, f = found[0]; masks.append(mask)
        mapped.append(str(f)[1:].replace('_', 'I'))
    # XOR measurement-record annotations; all non-annotation instructions survive.
    records = [set() for _ in flows]; count = 0
    for inst in circuit.flattened():
        if inst.name == 'OBSERVABLE_INCLUDE':
            k = int(inst.gate_args_copy()[0])
            for t in inst.targets_copy():
                if not t.is_measurement_record_target: raise ValueError('Non-record observable target')
                r = count + t.value
                if r in records[k]: records[k].remove(r)
                else: records[k].add(r)
        else: count += stim.Circuit(str(inst)).num_measurements
    view = stim.Circuit()
    for inst in circuit.flattened():
        if inst.name != 'OBSERVABLE_INCLUDE': view.append(inst)
    output_records = []
    for k, mask in enumerate(masks):
        ids = set()
        for j, rs in enumerate(records):
            if mask >> j & 1: ids.symmetric_difference_update(rs)
        if not ids: raise ValueError('An original output has no physical readout records')
        view.append('OBSERVABLE_INCLUDE', [stim.target_rec(i-view.num_measurements) for i in sorted(ids)], k)
        output_records.append(sorted(ids))
    newmeta = deepcopy(meta)
    newmeta.update(external_flows=mapped, num_observables=len(reads),
        internal_external_flows=flows, original_output_masks=masks,
        original_output_mapping=reads, original_output_records=output_records,
        internal_cleanup_qubits=program['unmeasured_logical_qubits'])
    return view, newmeta


def check_original_outputs(circuit, meta, program):
    result = check_exact(circuit, meta, program)
    n = program['logical_qubits']; reads = sorted(program['terminal_readout'], key=lambda r:r['classical_bit'])
    if len(meta['external_flows']) != program['classical_bits'] or circuit.num_observables != len(reads):
        raise AssertionError('Incomplete original application output')
    for r, f in zip(reads, meta['external_flows'], strict=True):
        target = ['I']*n; target[r['qubit']] = 'Z'
        if f[n:] != ''.join(target): raise AssertionError('Output basis is not every original bit in classical order')
    converter = circuit.compile_m2d_converter(); faults = []
    for q in range(n):
        injected = stim.Circuit()
        for inst in final_fault(circuit, meta, q):
            if inst.name == 'X_ERROR':
                if inst.gate_args_copy() != [1.0]: raise AssertionError('Expected deterministic fault')
                injected.append('X', inst.targets_copy())
            else: injected.append(inst)
        dets, obs = converter.convert(measurements=injected.reference_sample()[None,:], separate_observables=True)
        expected = [int(q == r['qubit']) for r in reads]
        if np.any(dets) or obs[0].tolist() != expected:
            raise AssertionError('Final logical fault changed the wrong original output')
        faults.append(dict(qubit=q, output_flips=expected, internal_cleanup=q in program['unmeasured_logical_qubits']))
    result.update(full_original_output_rank=len(reads), original_classical_order=reads,
                  final_faults=faults, all_logical_qubits_retained=n)
    return result
