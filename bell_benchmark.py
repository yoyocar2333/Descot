"""Pinned complete MQT Bell program and original random-readout validation."""
import ast
import hashlib
from itertools import product
from pathlib import Path

import numpy as np
from qiskit import qasm2
from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector
import stim

from public_clifford import logical_circuit, final_fault
from schedule_circuit import _rank

ROOT = Path(__file__).resolve().parent
UPSTREAM_COMMIT = '8f919416457d76b256930443078334021634236f'
UPSTREAM_BLOB = '9471d32080bec246ed293b4a100fb5eac4c0fc12'
SOURCE_DIR = ROOT / 'benchmarks/public_2026-11-04/mqt'


def original_qasm():
    """Execute the exact pinned function body; omit only registration metadata."""
    source = (SOURCE_DIR / 'bell.py').read_bytes()
    git_blob = hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()
    if git_blob != UPSTREAM_BLOB:
        raise ValueError('Pinned upstream generator differs')
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'create_circuit')
    function.decorator_list = []
    module = ast.Module(body=[function], type_ignores=[])
    namespace = {'QuantumCircuit': QuantumCircuit, 'QuantumRegister': QuantumRegister}
    exec(compile(module, str(SOURCE_DIR/'bell.py'), 'exec'), namespace)
    return qasm2.dumps(namespace['create_circuit'](6))+'\n'


def readout_validation(circuit, meta, program, shots=8):
    """Verify the *complete* deterministic Z subgroup, not all random bits."""
    n = program['logical_qubits']; flows = meta['external_flows']
    unitary = logical_circuit(program)
    qc = QuantumCircuit(n)
    for op in program['operations']:
        if op['name'] not in ('measure', 'barrier'):
            getattr(qc, op['name'])(*op['qubits'])
    state = Statevector.from_instruction(qc)
    probabilities = state.probabilities()
    # All Z-only deterministic parities of the original full program.
    deterministic = {}
    for bits in product((0,1), repeat=n):
        pauli = stim.PauliString(''.join('Z' if b else 'I' for b in bits))
        sim = stim.TableauSimulator(); sim.do(unitary)
        expectation = sim.peek_observable_expectation(pauli)
        if expectation:
            deterministic[bits] = int(expectation == -1)
    matrix = [[axis != 'I' for axis in f[n:]] for f in flows]
    if any(set(f[n:])-set('IZ') for f in flows):
        raise AssertionError('Original readout must remain Z')
    rank = _rank(matrix, n)
    if rank != len(flows) or 2**rank != len(deterministic):
        raise AssertionError('Incomplete original Z correlation subgroup')
    for f in flows:
        key = tuple(axis != 'I' for axis in f[n:])
        if key not in deterministic:
            raise AssertionError('Observable does not preserve original output distribution')
    if len(program['terminal_readout']) != n:
        raise AssertionError('Original readout mapping incomplete')
    faults = []
    for q in range(n):
        dets, obs = final_fault(circuit, meta, q).compile_detector_sampler(seed=123).sample(shots, separate_observables=True)
        expected = np.array([f[n+q] != 'I' for f in flows], dtype=bool)
        if np.any(dets) or not np.all(obs == expected) or not np.any(expected):
            raise AssertionError('Known final logical error missing from original readout')
        faults.append({'qubit':q,'observable_flips':expected.astype(int).tolist(),'shots':shots})
    outcomes = []
    for value, prob in enumerate(probabilities):
        if prob > 1e-10:
            logical = [(value >> q) & 1 for q in range(n)]
            classical = [None]*n
            for m in program['terminal_readout']:
                classical[m['classical_bit']] = logical[m['qubit']]
            if any(sum(a*b for a,b in zip(mask,logical))%2 != parity for mask,parity in deterministic.items()):
                raise AssertionError('Original random output support differs')
            outcomes.append({'classical_bits_little_endian':classical,'probability':float(prob)})
    return {'independent_z_observables':rank,'deterministic_z_subgroup_size':len(deterministic),
            'original_output_distribution':outcomes,'original_terminal_readout':program['terminal_readout'],
            'known_final_logical_faults':faults,
            'interpretation':'Any decoded original Z-correlation error. Random individual outcomes are retained, not scored against a fixed string; not full-output fidelity.'}
