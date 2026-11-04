"""Prepare/freeze, then validate/sample a second *complete* public workload."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time

from bell_benchmark import SOURCE_DIR, ROOT, original_qasm, readout_validation
from core import load_core, COMMIT
from memory_calibration_previous import wilson_interval
from public_clifford import (load_program, schedule_program, generate_program,
    validate_physical, validate_clifford_generators)
from public_candidate_pool import enumerate_plans, features, digest
from run_public_lookahead import METHODS, choose, signature
from run_surgery import MODEL, DECODER, sample, save
from run_three_qubit import verify_tqec_installation
from surgery import add_noise

SOURCE = SOURCE_DIR/'bell_n6.qasm'
FILES = ['bell_benchmark.py','run_bell_benchmark.py','public_clifford.py',
    'public_candidate_pool.py','public_lookahead.py','lookahead.py','run_public_lookahead.py',
    'run_public_audit.py','schedule_circuit.py','surgery.py','run_surgery.py',
    'run_three_qubit.py','memory_calibration_previous.py','requirements-lock.txt']
PROTOCOL = {
    'id':'complete_mqt_bell6_new_workload_20261104_v1',
    'source':'Exact MQT Bench create_circuit(6); original H/CX/barrier/readout retained',
    'spacings':[3,5],'seeds':[1,2,3],'front_budget':48,'methods':METHODS,
    'controls':['parallel','serial'], 'distance':3,'physical_p':.001,
    'shots_per_unique_circuit':100000,'batch_size':5000,'model_id':MODEL,'decoder_id':DECODER,
    'metric':'Any of three independent original terminal ZZ-correlation observables misdecoded. Individual outputs are random; not full-bitstring error or fidelity.',
    'validation':'64 signed Z inputs; all 12 X/Z Clifford generators via separate mixed boundaries; six known final logical faults; complete terminal Z subgroup; source statevector distribution; graphlike distance3.',
    'timing_policy':'H/CX layer=3 template block-z; barrier is zero-time synchronization fence preserving full DAG; terminal readout at common end; compiler TICK counted; QEC rounds null.',
    'fairness':'Same full-footprint source primitive and DAG closure; one/two-step budget48 and fixed-pool cap16 controls. Author search is a separate unmatched-cost reference. Structural serial control is not one-step.',
    'selection':'All algorithm routes and all13 exact-pool features fixed before new labels; four physical controls (2 geometries x parallel/serial), deduplicate exact physical identity.',
    'heldout_scope':'Prospective new-workload test, selected for backend support without looking at its noisy counts. No tuning on this workload. Single new family, not a broad generalization study.',
    'risk_transfer':'Prior hs4 absolute any-error fit has four observables and four qubits; Bell has three and six. Abstain on target/domain mismatch, retain baseline, mu=0. No absolute-risk transfer or held-out risk benefit claimed.',
    'timing':'After all physics/tests:3 warmups,25 repetitions, rotated method order; scheduler only. No MC, compiler, training or exact offline pool enumeration.',
    'mu':0}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def objsha(obj): return hashlib.sha256(str(obj).encode()).hexdigest()


def program():
    if SOURCE.read_text()!=original_qasm(): raise AssertionError('Full upstream generation differs')
    return load_program(SOURCE)


def prepare(output):
    if output.exists(): raise FileExistsError('Use a new output; preserve frozen records')
    p=program();base=load_core(ROOT.parent/'external/wisq')['sarouting']
    output.mkdir(parents=True);(output/'routes').mkdir();(output/'samples').mkdir();(output/'certificates').mkdir()
    save(output/'protocol.json',PROTOCOL);save(output/'program.json',p)
    direct=json.loads(importlib.metadata.distribution('tqec').read_text('direct_url.json'))
    save(output/'environment.json',{'python':platform.python_version(),'platform':platform.platform(),
        'packages':{k:importlib.metadata.version(k) for k in ('tqec','stim','pymatching','qiskit','numpy')},
        'tqec_direct_url':direct,'tqec_verification':verify_tqec_installation(direct),'wisq_commit':COMMIT,
        'source_files_sha256':{f:sha(ROOT/f) for f in FILES},
        'upstream_manifest':json.loads((SOURCE_DIR.parent/'manifest.json').read_text())})
    routes=[];pools=[];checks=[]
    for spacing in PROTOCOL['spacings']:
        for seed in PROTOCOL['seeds']:
            for method in METHODS:
                result=choose(p,base,method,spacing,seed)
                name=f'spacing{spacing}_{method}_s{seed}'
                save(output/'routes'/(name+'.json'),result)
                routes.append({'id':name,'spacing':spacing,'seed':seed,'method':method,
                    'plan':result['plan'],'features':features(p,result['plan']),'cost':result['cost']})
            a=json.loads((output/'routes'/f'spacing{spacing}_one_pool16_s{seed}.json').read_text())
            b=json.loads((output/'routes'/f'spacing{spacing}_two_pool16_s{seed}.json').read_text())
            same=[(x['ready_ids'],x['candidate_orders'])==(y['ready_ids'],y['candidate_orders']) for x,y in zip(a['fronts'],b['fronts'])]
            if len(a['fronts'])!=len(b['fronts']) or not all(same):raise AssertionError('Fixed evaluated pools differ')
            checks.append({'spacing':spacing,'seed':seed,'same_candidate_orders_at_same_states':True})
        pools.append({'spacing':spacing,'candidates':[{'candidate_id':f'p{i:02d}','plan':plan,'features':features(p,plan)} for i,plan in enumerate(enumerate_plans(p,spacing))]})
    prior=ROOT/'results/public_candidates_2026-11-02/frozen_selection.json'
    save(output/'frozen_design.json',{'prepared_utc':datetime.now(timezone.utc).isoformat(),
        'protocol_sha256':sha(output/'protocol.json'),'source_files_sha256':{f:sha(ROOT/f) for f in FILES},
        'routes':routes,'exact_pools':pools,'fixed_pool_checks':checks,
        'calibration_transfer_audit':{'prior_frozen_selection_sha256':sha(prior),
            'calibration_logical_qubits':4,'new_logical_qubits':6,
            'calibration_observables':4,'new_observables':3,
            'accepted':False,'reasons':['Different any-error observable count/target','Different qubit count and no matched absolute-risk calibration'],
            'action':'Abstain, retain pure progress baseline; no refit and mu=0'}})
    print('Prepared 30 source routes, two exact 13-plan pools; no new noisy labels read.',flush=True)


def worker(output_string, mode, spacing):
    output=Path(output_string);p=program();plan=schedule_program(p,mode,spacing)
    name=f'bell6_{mode}_spacing{spacing}'
    print('compile/validate '+name,flush=True);began=time.perf_counter()
    ideal,meta=generate_program(p,plan)
    validation=validate_physical(ideal,meta,p,4)
    validation['original_readout']=readout_validation(ideal,meta,p,4)
    print('all X/Z generators '+name,flush=True)
    validation['all_clifford_generators']=validate_clifford_generators(p,plan,2)
    noisy=add_noise(ideal,.001);distance=len(noisy.shortest_graphlike_error())
    if distance!=3:raise AssertionError('Graphlike distance differs')
    validation['shortest_graphlike_error']=distance
    generation_seconds=time.perf_counter()-began
    sample_id='sample_'+objsha(noisy);seed=int.from_bytes(hashlib.sha256((PROTOCOL['id']+objsha(noisy)).encode()).digest()[:8],'little')
    print('sample '+name,flush=True);began=time.perf_counter()
    fail,per,batches,dem=sample(noisy,100000,seed,5000);sampling_seconds=time.perf_counter()-began
    lo,hi=wilson_interval(fail,100000)
    record={'record_id':name,'sample_id':sample_id,'source_sha256':p['source_sha256'],
        'mode':mode,'spacing':spacing,'ideal_circuit_sha256':objsha(ideal),
        'noisy_circuit_sha256':objsha(noisy),'dem_sha256':objsha(dem),
        'distance':3,'physical_p':.001,'model_id':MODEL,'decoder_id':DECODER,
        'num_qubits':noisy.num_qubits,'num_ticks':noisy.num_ticks,
        'num_observables':noisy.num_observables,'num_detectors':noisy.num_detectors,
        'features':features(p,plan),'shots':100000,'new_shots':100000,'seed':seed,'batch_size':5000,
        'failures_any':fail,'failures_by_observable':per,'batches':batches,'p_fail_any':fail/100000,
        'wilson95_low':lo,'wilson95_high':hi,'generation_validation_seconds':generation_seconds,
        'sampling_decode_seconds':sampling_seconds,'shortest_graphlike_error':distance}
    ideal.to_file(output/'samples'/(sample_id+'_ideal.stim'));noisy.to_file(output/'samples'/(sample_id+'.stim'));dem.to_file(output/'samples'/(sample_id+'.dem'))
    save(output/'samples'/(sample_id+'.json'),record)
    save(output/'certificates'/(name+'.json'),{'backend_meta':meta,'physical_validation':validation})
    print(f'{name}: {fail}/100000; {noisy.num_ticks} TICKs; {noisy.num_qubits} qubits',flush=True)
    return record


def run(output):
    frozen=json.loads((output/'frozen_design.json').read_text())
    if (output/'run_start.json').exists():raise FileExistsError('Never overwrite a started frozen run')
    for f,h in frozen['source_files_sha256'].items():
        if sha(ROOT/f)!=h:raise AssertionError('Frozen implementation differs: '+f)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    committed=subprocess.check_output(['git','show',commit+':'+str((output/'frozen_design.json').relative_to(ROOT))],cwd=ROOT)
    if committed!=(output/'frozen_design.json').read_bytes():raise AssertionError('Design must be committed before new labels')
    save(output/'run_start.json',{'source_freeze_commit':commit,'frozen_design_sha256':sha(output/'frozen_design.json'),
        'started_utc':datetime.now(timezone.utc).isoformat()})
    records=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(worker,str(output),mode,spacing) for spacing in PROTOCOL['spacings'] for mode in PROTOCOL['controls']]
        for job in as_completed(futures):
            records.append(job.result());save(output/'records_partial.json',records)
    if len({r['noisy_circuit_sha256'] for r in records})!=4:raise AssertionError('Unexpected duplicate: do not double-count shots')
    matches=[]
    for route in frozen['routes']:
        options=[r for r in records if r['spacing']==route['spacing'] and r['mode']=='parallel']
        if len(options)!=1 or signature(route['plan'])!=signature(schedule_program(program(),'parallel',route['spacing'])):
            raise AssertionError('Method output not an exact complete compiled plan')
        matches.append({'route_id':route['id'],'sample_id':options[0]['sample_id'],'new_shots':0,'evidence':'Exact source/layout/full instruction layers; shared complete circuit and counts'})
    save(output/'summary.json',{'protocol':PROTOCOL,'records':sorted(records,key=lambda r:r['record_id']),
        'source_routes':30,'unique_sampled_circuits':4,'new_monte_carlo_shots':400000,'method_sample_matches':matches,
        'algorithm_outcome':'All methods select the same parallel plan. Extra lookahead gain=0 on this workload; serial is a structural control.',
        'coverage':{'validated':2,'pinned_complete_sources':8,'names':['QASMBench hs4_n4','MQT Bench bell(6)']},
        'risk_transfer':frozen['calibration_transfer_audit'],'mu':0})


def timing(output):
    summary=json.loads((output/'summary.json').read_text());frozen=json.loads((output/'frozen_design.json').read_text());p=program();base=load_core(ROOT.parent/'external/wisq')['sarouting']
    rows=frozen['routes'];durations={r['id']:[] for r in rows}
    for r in rows:
        for _ in range(3):choose(p,base,r['method'],r['spacing'],r['seed'])
    for repeat in range(25):
        offset=repeat%len(rows)
        for r in rows[offset:]+rows[:offset]:
            began=time.perf_counter();result=choose(p,base,r['method'],r['spacing'],r['seed']);elapsed=time.perf_counter()-began
            if digest(result['plan'])!=digest(r['plan']):raise AssertionError('Timing changed frozen plan')
            durations[r['id']].append(elapsed)
    save(output/'routing_timing_isolated.json',{'scope':PROTOCOL['timing'],'records':[{'id':k,'seconds':v,'median_seconds':statistics.median(v)} for k,v in durations.items()]})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','run','timing'])
    parser.add_argument('--output',type=Path,default=ROOT/'results/public_bell_2026-11-04')
    args=parser.parse_args();globals()[args.stage](args.output)
