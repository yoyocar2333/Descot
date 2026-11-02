"""Staged development calibration, frozen offline decisions, geometry-held-out test.

Run `development`, commit/freeze `frozen_selection.json`, then `heldout`.
All candidates preserve the entire original hs4_n4. Raw sampling is by full
circuit identity, never an isolated-gadget product. No production risk weight.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import time

from memory_calibration_previous import wilson_interval
from public_clifford import load_program, generate_program, validate_physical, validate_x_generators
from public_candidate_pool import enumerate_plans, features, digest, fit_model, select
from run_public_clifford import digest as circuit_digest
from run_surgery import MODEL, DECODER, sample, save
from run_three_qubit import verify_tqec_installation
from surgery import add_noise

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm'
PREVIOUS=ROOT/'results/public_hs4_2026-11-02'
PROTOCOL={
 'id':'public_hs4_exact_pool_geometry_holdout_20261102_v1',
 'source_sha256':'f362ca9ffd7f045f517dfe4d67350794ac998f4eb427586a804eed9379340f63',
 'development_spacing':3, 'heldout_spacing':5, 'distance':3, 'physical_p':.001,
 'shots_per_unique_circuit':100000, 'batch_size':5000, 'model_id':MODEL, 'decoder_id':DECODER,
 'pool_policy':'Exact all nonempty compatible CX subsets with instant-first then H-ready-first closure; cap256 fails rather than truncates; no H cancellation or dropped original instructions',
 'development_scope':'All 13 plans; existing spacing3 full-circuit samples are development-only and may be reused on exact canonical hashes',
 'heldout_scope':'Same complete source, unseen geometry spacing5; all six matched serial candidates plus unique globally minimum-depth parallel plan. Not held-out workload evidence; not blinded to prior spacing3/4 data.',
 'fit':'Predeclared ridge lambda1, standardized physical_layers and squared same-pair CX recurrence separation; add-half logit(any-error). All 13 development candidates, no hyperparameter search.',
 'ablations':['minimum physical layers then lexicographic ID','depth-only ridge','depth+CX separation ridge','depth+CX separation ridge with empirical LOO-envelope guard'],
 'guard':'Switch only if best logit prediction + max absolute leave-one-plan-out residual < baseline logit prediction - same residual. Empirical sensitivity envelope, NOT a prediction CI or guaranteed coverage.',
 'pools':['all 13 candidates with hard minimum physical-layer depth','six serial candidates matched on physical layers, data memory volume and full ancilla reservation'],
 'freeze':'Serialize model, all candidate features and selected IDs before opening/compiling/sampling spacing5; commit frozen decisions before heldout stage',
 'metric':'Any of four independent original terminal Z-correlation observables misdecoded; complete classical output mapping; not fidelity',
 'physical_validation':'All16 signed Z inputs, four final faults, complete input/output rank and frame/tableau; four mixed-boundary X-generator checks and graphlike distance3 per new circuit',
 'timing':'Routing/feature/selection only after physical jobs end, 3 warmups and 25 repeats; compiler/Monte Carlo separate',
 'scope':'Offline candidate selector pilot; existing DASCOT original/one-step/two-step retained separately. Not a new online router or a novelty proof. mu=0',
 'mu':0}
SOURCES=['public_candidate_pool.py','run_public_candidates.py','public_clifford.py','public_readout.py','run_public_audit.py','schedule_circuit.py','surgery.py','run_surgery.py','run_three_qubit.py','memory_calibration_previous.py','requirements-lock.txt']


def pool(program,spacing):
    return [{'candidate_id':f'p{i:02d}', 'plan':p,'features':features(program,p)}
            for i,p in enumerate(enumerate_plans(program,spacing))]


def checked_program():
    p=load_program(SOURCE)
    if p['source_sha256']!=PROTOCOL['source_sha256']:raise ValueError('Pinned complete source changed')
    return p


def worker(folder_string, stage, candidate):
    folder=Path(folder_string); program=checked_program(); name=stage+'_'+candidate['candidate_id']
    # Reuse old full physical validation only for exactly the same instruction
    # layers, geometry, source, pinned compiler and circuit identity.
    reused=None; old_meta=None; signature=lambda plan:[l['operation_ids'] for l in plan['layers']]
    if stage=='development':
        old=json.loads((PREVIOUS/'summary.json').read_text())
        for record in old['records']:
            cert=json.loads((PREVIOUS/'certificates'/(record['record_id']+'.json')).read_text())
            meta=cert['backend_meta']
            if meta['plan']['spacing']==candidate['plan']['spacing'] and signature(meta['plan'])==signature(candidate['plan']):
                reused=record;old_meta=meta;break
    began=time.perf_counter()
    if reused:
        ideal_path=PREVIOUS/'samples'/(reused['sample_id']+'_ideal.stim')
        import stim
        ideal=stim.Circuit.from_file(ideal_path); noisy=stim.Circuit.from_file(PREVIOUS/'samples'/(reused['sample_id']+'.stim'))
        dem=stim.DetectorErrorModel.from_file(PREVIOUS/'samples'/(reused['sample_id']+'.dem'))
        if (circuit_digest(ideal),circuit_digest(noisy),circuit_digest(dem)) != tuple(reused[k] for k in ('ideal_circuit_sha256','noisy_circuit_sha256','dem_sha256')):
            raise AssertionError('Previous raw artifacts differ')
        if old_meta['source_sha256']!=program['source_sha256'] or circuit_digest(add_noise(ideal,.001))!=reused['noisy_circuit_sha256']:
            raise AssertionError('Previous source/noise differs')
        meta=old_meta;validation=cert['physical_validation'];record={**reused}
        origin=str((PREVIOUS/'samples'/(reused['sample_id']+'.json')).relative_to(ROOT))
        generation_seconds=0.;sampling_seconds=0.
    else:
        ideal,meta=generate_program(program,candidate['plan'])
        validation=validate_physical(ideal,meta,program,8,True)
        validation['conjugate_x_generators']=validate_x_generators(program,candidate['plan'],4)
        noisy=add_noise(ideal,PROTOCOL['physical_p']);distance=len(noisy.shortest_graphlike_error())
        if distance!=3:raise AssertionError('Distance mismatch')
        validation['shortest_graphlike_error']=distance
        generation_seconds=time.perf_counter()-began
        noisy_hash=circuit_digest(noisy)
        seed=int.from_bytes(hashlib.sha256((PROTOCOL['id']+noisy_hash).encode()).digest()[:8],'little')
        began=time.perf_counter();fail,per,batches,dem=sample(noisy,100000,seed,5000);sampling_seconds=time.perf_counter()-began
        lo,hi=wilson_interval(fail,100000)
        record={'ideal_circuit_sha256':circuit_digest(ideal),'noisy_circuit_sha256':noisy_hash,'dem_sha256':circuit_digest(dem),
                'shots':100000,'seed':seed,'batch_size':5000,'batches':batches,'failures_any':fail,'failures_by_observable':per,
                'p_fail_any':fail/100000,'wilson95_low':lo,'wilson95_high':hi,'shortest_graphlike_error':distance}
        origin=None
    sample_id='sample_'+record['noisy_circuit_sha256']
    record.update(record_id=name,candidate_id=candidate['candidate_id'],stage=stage,features=candidate['features'],
                  source_sha256=program['source_sha256'],model_id=MODEL,decoder_id=DECODER,distance=3,physical_p=.001,
                  num_qubits=noisy.num_qubits,num_ticks=noisy.num_ticks,num_detectors=noisy.num_detectors,num_observables=noisy.num_observables,
                  sample_id=sample_id,reused_from=origin,new_shots=0 if origin else record['shots'],
                  generation_and_validation_seconds=generation_seconds,sampling_decode_seconds=sampling_seconds)
    save(folder/'certificates'/(name+'.json'),{'candidate_plan':candidate['plan'],'backend_meta':meta,'physical_validation':validation,
        'ideal_circuit_sha256':record['ideal_circuit_sha256'],'noisy_circuit_sha256':record['noisy_circuit_sha256']})
    ideal.to_file(folder/'samples'/(sample_id+'_ideal.stim'));noisy.to_file(folder/'samples'/(sample_id+'.stim'));dem.to_file(folder/'samples'/(sample_id+'.dem'))
    save(folder/'samples'/(sample_id+'.json'),record)
    return record


def run_stage(folder,stage,workers):
    program=checked_program()
    if stage=='development':
        if folder.exists():raise FileExistsError('Use fresh output; never overwrite frozen results')
        folder.mkdir(parents=True);(folder/'samples').mkdir();(folder/'certificates').mkdir()
        provenance=json.loads(importlib.metadata.distribution('tqec').read_text('direct_url.json'))
        env={'python':platform.python_version(),'platform':platform.platform(),
             'packages':{k:importlib.metadata.version(k) for k in ('tqec','stim','pymatching','numpy','qiskit')},
             'source_head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
             'source_files_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in SOURCES},
             'tqec_verification':verify_tqec_installation(provenance),'tqec_direct_url':provenance}
        save(folder/'environment.json',env);save(folder/'protocol.json',PROTOCOL);save(folder/'program.json',program)
        candidates=pool(program,3);save(folder/'development_pool.json',candidates)
    else:
        if (folder/'heldout_summary.json').exists():raise FileExistsError('Heldout already evaluated')
        freeze_path=folder/'frozen_selection.json'; frozen=json.loads(freeze_path.read_text())
        if frozen['protocol_sha256']!=digest(PROTOCOL):raise AssertionError('Protocol changed after freeze')
        if frozen['development_summary_sha256']!=hashlib.sha256((folder/'development_summary.json').read_bytes()).hexdigest():raise AssertionError('Calibration changed after freeze')
        # Require the exact decisions to be durably committed before test.
        relative=freeze_path.resolve().relative_to(ROOT).as_posix()
        tracked=subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+relative])
        if tracked!=freeze_path.read_bytes():raise AssertionError('Commit frozen selection before heldout stage')
        for s,sha in json.loads((folder/'environment.json').read_text())['source_files_sha256'].items():
            if hashlib.sha256((ROOT/s).read_bytes()).hexdigest()!=sha:raise AssertionError('Experiment source changed: '+s)
        candidates=[r for r in frozen['heldout_pool'] if r['candidate_id'] in frozen['heldout_sample_ids']]
        save(folder/'heldout_start.json',{'frozen_selection_sha256':hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
             'source_head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),'started_utc':datetime.now(timezone.utc).isoformat()})
    records=[]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures=[executor.submit(worker,str(folder),stage,row) for row in candidates]
        for future in as_completed(futures):
            row=future.result();records.append(row)
            save(folder/(stage+'_partial.json'),sorted(records,key=lambda r:r['candidate_id']))
            print(f"{row['record_id']}: {row['failures_any']}/{row['shots']}; {row['num_ticks']} TICKs; new shots {row['new_shots']}",flush=True)
    records.sort(key=lambda r:r['candidate_id'])
    if len({r['noisy_circuit_sha256'] for r in records})!=len(records):raise AssertionError('Unexpected duplicate: rerun with explicit deduplication')
    save(folder/(stage+'_summary.json'),{'stage':stage,'records':records,'new_shots':sum(r['new_shots'] for r in records),
        'sampled_unique_circuits':len(records),'workers':workers,'concurrent_compilation_note':'Compiler and Monte Carlo timings are diagnostic; separate isolated selector timing follows.'})
    if stage=='development':freeze(folder)


def freeze(folder):
    summary=json.loads((folder/'development_summary.json').read_text());rows=summary['records']; program=checked_program()
    test=pool(program,5);models={'depth_only':fit_model(rows,False),'depth_wait':fit_model(rows,True)}
    decisions=[]
    for name,model,guarded in [('depth_only',models['depth_only'],False),('depth_wait',models['depth_wait'],False),('depth_wait_guard',models['depth_wait'],True)]:
        for which in ('all','serial_matched'):
            decisions.append({'method':name,**select(test,model,which,guarded)})
    ids=[r['candidate_id'] for r in test if r['features']['cx_routing_steps']==4 or r['features']['physical_layers']==9]
    save(folder/'frozen_selection.json',{'protocol_sha256':digest(PROTOCOL),'frozen_utc':datetime.now(timezone.utc).isoformat(),
        'development_summary_sha256':hashlib.sha256((folder/'development_summary.json').read_bytes()).hexdigest(),
        'models':models,'heldout_pool':test,'heldout_sample_ids':ids,'decisions':decisions,
        'evaluation_scope':'One complete public source, held-out geometry only; all matched serial controls and unique minimum-depth plan sampled. No unseen-workload claim.',
        'mu':0})


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stage',choices=['development','heldout']);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--workers',type=int,default=3)
    a=ap.parse_args();run_stage(a.output,a.stage,a.workers)
