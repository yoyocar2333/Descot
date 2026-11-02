"""Frozen-protocol complete hs4_n4 experiment; full source, physical H, virtual X."""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time

import stim

from memory_calibration_previous import wilson_interval
from public_clifford import (load_program, schedule_program, generate_program,
                             validate_physical, validate_x_generators, logical_circuit)
from run_surgery import MODEL, DECODER, sample, save
from run_three_qubit import verify_tqec_installation
from surgery import add_noise

ROOT=Path(__file__).resolve().parent
CONDITIONS=[('parallel',3),('serial',3),('serial_reverse',3),('parallel',4)]
PROTOCOL={"id":"complete_public_hs4_20261102_v1","source":"hs4_n4",
    "conditions":[{"mode":m,"spacing_blocks":s} for m,s in CONDITIONS],
    "input":"Original |0000> preparation","readout":"All four original terminal Z measurements with original classical destinations; Pauli-frame XOR retained",
    "distance":3,"physical_p":.001,"shots_per_condition":100000,"batch_size":5000,
    "model_id":MODEL,"decoder_id":DECODER,
    "observable_failure":"Any of four complete independent Z-correlation observables misdecoded, equivalent to any corrected output bit wrong for this deterministic-output program",
    "x_policy":"All four original X instructions execute virtually, zero time/no added physical noise; exact Pauli frame propagation through every retained H/CX, XOR at original classical outputs",
    "h_policy":"All 20 original H instructions physically represented; no cancellation or gate dropping",
    "timing_policy":"3 block-z per physical H/CX layer; virtual X takes zero. TQEC fixed-bulk H realignment has additional physical extent. Stim TICKs counted from compiled circuit, QEC rounds not inferred from block-z or TICKs",
    "selection":"Predeclared parallel/serial/serial-reverse controls at spacing3 plus parallel at spacing4. No noisy selection, held-out or new scheduler-improvement claim",
    "timing_repetitions":25,"timing_warmups":3,
    "timing_scope":"Full-instruction DAG scheduler only, before any compilation/sampling; distinct from DASCOT routing and Monte Carlo",
    "validation":"16 signed Z inputs, four final logical faults, complete Z-correlation rank and full source tableau/frame; four additional mixed-boundary physical X-generator experiments per condition; graphlike distance3",
    "mu":0}


def digest(value): return hashlib.sha256(str(value).encode()).hexdigest()


def run(output):
    if output.exists(): raise FileExistsError('Use a fresh output directory; no frozen result overwrite')
    manifest_path=ROOT/'benchmarks/public_2026-11-02/manifest.json'
    manifest=json.loads(manifest_path.read_text())
    item=next(row for row in manifest['files'] if row['path'].endswith('/hs4_n4.qasm'))
    path=ROOT/item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Pinned complete source differs')
    program=load_program(path)
    direct=importlib.metadata.distribution('tqec').read_text('direct_url.json'); provenance=json.loads(direct)
    source_files=['public_clifford.py','run_public_clifford.py','run_public_audit.py','schedule_circuit.py','surgery.py','run_surgery.py','run_three_qubit.py','memory_calibration_previous.py','requirements-lock.txt']
    env={'python':platform.python_version(),'platform':platform.platform(),
         'packages':{k:importlib.metadata.version(k) for k in ('tqec','stim','pymatching','qiskit','numpy')},
         'source_head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
         'source_files_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_files},
         'tqec_direct_url':provenance,'tqec_verification':verify_tqec_installation(provenance),
         'upstream_source':item,'upstream_manifest':manifest}
    output.mkdir(parents=True)
    save(output/'protocol.json',PROTOCOL);save(output/'environment.json',env);save(output/'program.json',program)
    (output/'samples').mkdir();(output/'certificates').mkdir()
    jobs=[];timings=[]
    for mode,spacing in CONDITIONS:
        name=f'hs4_{mode}_spacing{spacing}'
        plan=schedule_program(program,mode,spacing)
        for _ in range(PROTOCOL['timing_warmups']):schedule_program(program,mode,spacing)
        seconds=[]
        for _ in range(PROTOCOL['timing_repetitions']):
            start=time.perf_counter();schedule_program(program,mode,spacing);seconds.append(time.perf_counter()-start)
        timings.append({'record_id':name,'seconds':seconds,'median_seconds':statistics.median(seconds)})
        jobs.append((name,plan))
    save(output/'scheduler_timing.json',{'scope':PROTOCOL['timing_scope'],'records':timings})
    records=[]
    for name,plan in jobs:
        print('compile '+name,flush=True)
        began=time.perf_counter();ideal,meta=generate_program(program,plan)
        validation=validate_physical(ideal,meta,program,16,True)
        print('validate conjugate X generators '+name,flush=True)
        validation['conjugate_x_generators']=validate_x_generators(program,plan,8)
        noisy=add_noise(ideal,PROTOCOL['physical_p'])
        distance=len(noisy.shortest_graphlike_error())
        if distance!=3:raise AssertionError('Distance differs')
        validation['shortest_graphlike_error']=distance
        validation_seconds=time.perf_counter()-began
        ideal_hash,noisy_hash=digest(ideal),digest(noisy)
        save(output/'certificates'/(name+'.json'),{'backend_meta':meta,'physical_validation':validation,
             'ideal_circuit_sha256':ideal_hash,'noisy_circuit_sha256':noisy_hash,'generation_and_validation_seconds':validation_seconds})
        sample_id='sample_'+noisy_hash
        seed=int.from_bytes(hashlib.sha256((PROTOCOL['id']+noisy_hash).encode()).digest()[:8],'little')
        began=time.perf_counter()
        failures,per,batches,dem=sample(noisy,PROTOCOL['shots_per_condition'],seed,PROTOCOL['batch_size'])
        seconds=time.perf_counter()-began
        lo,hi=wilson_interval(failures,PROTOCOL['shots_per_condition'])
        record={'record_id':name,'sample_id':sample_id,'mode':plan['mode'],'spacing_blocks':plan['spacing'],
            'source_sha256':program['source_sha256'],'ideal_circuit_sha256':ideal_hash,'noisy_circuit_sha256':noisy_hash,'dem_sha256':digest(dem),
            'model_id':MODEL,'decoder_id':DECODER,'distance':3,'physical_p':.001,
            'num_qubits':noisy.num_qubits,'num_ticks':noisy.num_ticks,'num_detectors':noisy.num_detectors,'num_observables':noisy.num_observables,
            'source_operation_counts':program['operation_counts'],'cx_routing_steps':sum(l['kind']=='cx' for l in plan['layers']),
            'logical_h_layers':sum(l['kind']=='h' for l in plan['layers']),
            'template_block_z':meta['output_z'],'qec_rounds':None,
            'qec_rounds_note':'Not equated with routing/block-z/TICK; ordinary block bulk repetitions=1 at k=1, temporal-H realignment adds compiler-specific layers. No round count inferred.',
            'data_patch_reservation_block_z':program['logical_qubits']*meta['output_z'],
            'ancilla_reservation_block_z':sum(3*(len(f['reserved_xy'])-2) for f in meta['gate_footprints']),
            'shots':PROTOCOL['shots_per_condition'],'seed':seed,'batch_size':PROTOCOL['batch_size'],'batches':batches,
            'failures_any':failures,'failures_by_observable':per,'p_fail_any':failures/PROTOCOL['shots_per_condition'],
            'wilson95_low':lo,'wilson95_high':hi,'sampling_decode_seconds':seconds,'shortest_graphlike_error':distance}
        ideal.to_file(output/'samples'/(sample_id+'_ideal.stim'));noisy.to_file(output/'samples'/(sample_id+'.stim'));dem.to_file(output/'samples'/(sample_id+'.dem'))
        save(output/'samples'/(sample_id+'.json'),record);records.append(record)
        save(output/'records_partial.json',records)
        print(f'{name}: {failures}/100000; {noisy.num_ticks} TICKs; {noisy.num_qubits} physical qubits',flush=True)
    if len({r['noisy_circuit_sha256'] for r in records})!=len(records):raise AssertionError('Unexpected duplicate circuit: must deduplicate sampling')
    summary={'protocol':PROTOCOL,'environment':env,'records':records,'unique_sampled_circuits':len(records),
             'new_monte_carlo_shots':sum(r['shots'] for r in records),'full_public_benchmark_coverage':{'validated':1,'audited_sources':7,'validated_names':['hs4_n4'],
             'scope':'Other six sources retain prior audit and are not claimed fully physically supported'}}
    save(output/'summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
