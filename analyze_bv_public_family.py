"""Independent source-unitary oracle and complete public-family evidence table."""
from collections import defaultdict
import argparse
import statistics
import numpy as np
import stim
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from public_candidate_pool import digest
from public_clifford import logical_circuit
from run_bv_public_family import DEFAULT, generate_source, read, save


def source_verification(program):
    def matrix(ops):
        q=QuantumCircuit(3)
        for op in ops:
            if op['name'] not in ('measure','barrier'):
                getattr(q,op['name'])(*op['qubits'])
        return Operator(q).data
    u=matrix(program['original_program']['operations']);v=matrix(program['operations'])
    error=float(np.max(np.abs(u-v)))
    if not np.allclose(u,v,atol=1e-12,rtol=0):raise AssertionError('Original/lowered complex unitary differs')
    rows=[]
    for k in range(8):
        a=np.zeros(8,complex);a[k]=1;b=u@a;c=v@a
        if not np.allclose(b,c,atol=1e-12,rtol=0):raise AssertionError('Source statevector differs')
        probs=np.abs(b)**2;out=int(np.argmax(probs))
        if not np.isclose(probs[out],1,atol=1e-12,rtol=0):raise AssertionError('Original Z outputs are not deterministic')
        rows.append(dict(input_basis_index=k,full_output_basis_index=out,
            original_classical_bits_c0_c1=[(out>>1)&1,(out>>2)&1]))
    return dict(status='PASS',method='Independent Qiskit8x8 complex Operator equality and all8 exact statevectors; no sampling',
        source_sha256=program['source_sha256'],lowered_operations_sha256=digest(program['operations']),
        max_abs_matrix_error=error,comparison_atol=1e-12,comparison_rtol=0,
        all_computational_inputs=rows,new_shots=0,sampler_calls=0)


def analyze(result):
    p=generate_source();summary=read(result/'summary.json');rows=read(result/'physical_index.json')
    proof=source_verification(p)
    target=result/'source_unitary_verification.json'
    if target.exists() and read(target)!=proof:raise AssertionError('Independent source proof changed')
    if not target.exists():save(target,proof)
    groups=defaultdict(list)
    for r in rows:
        groups[digest(r['profile_features']['protected_idle_intervals_block_z'])].append(r)
    grouped=[]
    for group in groups.values():
        f=group[0]['profile_features']
        grouped.append(dict(candidate_ids=[r['candidate_id'] for r in group],
            intervals_by_logical_qubit=f['protected_idle_intervals_block_z'],
            total_protected_idle_block_z=f['total_protected_idle_block_z'],
            squared_protected_idle_block_z2=f['squared_protected_idle_block_z2']))
    requests=[v for r in rows for v in r['compile_requests']]
    started=finished=0
    for row in rows:
        journal=(result/'journals'/(row['candidate_id']+'.jsonl')).read_text()
        started+=journal.count('"event": "compile_started"');finished+=journal.count('"event": "compile_finished"')
        c=read(result/'certificates'/(row['candidate_id']+'.json'))
        sign=next(x for x in c['original_output_validation']['signed_inputs'] if x['input_signs']==[1,0,0])
        if sign['observable_parities']!=[1,1]:raise AssertionError('Input flag error did not reach both original outputs')
        if c['original_output_validation']['final_faults'][0]['output_flips']!=[0,0]:raise AssertionError('Internal cleanup was counted as an original output')
    if (started,finished,len(requests))!=(36,36,63):raise AssertionError('Incomplete compile accounting')
    timing=read(result/'timing.json');medians={}
    for policy in timing['selector_only_seconds_31_repeats'][0]:
        medians[policy]=statistics.median(x[policy] for x in timing['selector_only_seconds_31_repeats'])
    inverse=stim.Tableau.from_circuit(logical_circuit(p)).inverse()
    preimages=[]
    for r in sorted(p['terminal_readout'],key=lambda r:r['classical_bit']):
        z=stim.PauliString(3);z[r['qubit']]='Z'
        preimages.append(dict(**r,signed_input_pauli=str(inverse(z))))
    if [x['signed_input_pauli'] for x in preimages]!=['-ZZ_','-Z_Z']:
        raise AssertionError('Full-source readout preimage differs')
    report=dict(summary=summary,wait_profile_groups=grouped,
        original_terminal_pauli_preimages=preimages,
        pauli_ir_note='Known Clifford propagation on the full unchanged source. Both rows include the unmeasured flag. This is an interface target, not an executed native CircLS lowering or new method.',
        source_unitary=proof['max_abs_matrix_error'],compile_started=started,compile_finished=finished,
        unfinished_compilations=started-finished,compile_cache_hits=sum(x['cache_hit'] for x in requests),
        independent_selector_median_seconds=medians,
        units_rows=[dict(candidate_id=r['candidate_id'],
            cx_routing_steps=r['profile_features']['cx_routing_steps'],
            h_layers=r['profile_features']['logical_h_layers'],template_block_z=r['features']['template_block_z'],
            qec_rounds=None,stim_ticks=r['features']['stim_ticks'],data_lifetime_block_z=r['features']['data_lifetime_block_z'],
            ancilla_lifetime_block_z=r['features']['ancilla_lifetime_block_z'],
            total_lifetime_block_z=r['features']['total_lifetime_block_z'],
            full_footprint_reservation_block_z=r['profile_features']['ancilla_reservation_block_z'],
            active_physical_sites=r['active_physical_sites'],common_device_sites=r['features']['device_physical_sites']) for r in rows],
        interpretation='Different full physical circuits and wait segmentation on a new public development family. No decoded labels or new risk model; structural identifiability is not efficacy. All9 minima and uncapped baseline remain;57 deeper plans retained unqualified.',
        next_gate='Original-method common Pauli IR/rotation/movement and online equal-CPU controls; only then decide mechanism-based development revision, calibration/ablation and full sampling freeze.',
        new_shots=0,mu=0)
    if (result/'analysis.json').exists():raise FileExistsError('Preserve frozen analysis')
    save(result/'analysis.json',report);print(report)


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('--result',type=__import__('pathlib').Path,default=DEFAULT)
    analyze(parser.parse_args().result)
