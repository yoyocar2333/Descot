"""Validate routed requests against an exact full-circuit reference, without new Monte Carlo."""
import copy
from collections import Counter
import hashlib
import importlib.metadata
from itertools import product
import json
from pathlib import Path
import subprocess
import zipfile
from core import load_core
from lookahead import schedule,Config
from saturation import routing_hooks
from route_adapter import ADAPTER_ID,profile_architecture,request_for,certify,lower,UnsupportedSchedule,sha256_json
from surgery import add_noise
from run_surgery import MODEL,DECODER,save
from run_three_qubit import verify_tqec_installation
from memory_calibration_previous import wilson_interval

ROOT=Path(__file__).resolve().parent
FOLDER=ROOT/'results/adapter_2026-11-01'

def main():
    if FOLDER.exists():raise FileExistsError('This is a frozen validation run; use a separate checkout/output for a new study')
    for sub in ['requests','certificates','source_routes','physical_checks']:(FOLDER/sub).mkdir(parents=True,exist_ok=True)
    reference_path=ROOT/'results/three_qubit_2026-10-31/summary.json'
    reference=json.loads(reference_path.read_text())
    provenance=json.loads(importlib.metadata.distribution('tqec').read_text('direct_url.json'))
    tqec_check=verify_tqec_installation(provenance)
    protocol={'adapter_id':ADAPTER_ID,'source_methods':['original','one_budget48','two_budget48'],
              'source_seeds':[1,2,3],'spans':[1,3],'bases':['x','z'],'intergate_storage_blocks':[0,1],
              'new_monte_carlo_shots':0,'reuse_policy':'Exact full ideal/noisy circuit hashes, observables, model, decoder, p and distance must match the frozen reference',
              'timing':'Each CNOT uses three block-z units; intergate storage is explicitly specified, not inferred from source depth',
              'normalization':'Source edges can change within the fully reserved empty corridor',
              'mu':0,'tqec_verification':tqec_check,
              'reference_summary_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),
              'source_base_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
              'source_files_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in [
                  'route_adapter.py','run_adapter_validation.py','three_qubit.py','surgery.py','lookahead.py','saturation.py','validation.py']}}
    save(FOLDER/'protocol.json',protocol)
    core=load_core(ROOT.parent/'external/wisq');router=core['sarouting']
    cache={};source_records=[];accepted=[]
    for span,method,seed in product([1,3],protocol['source_methods'],[1,2,3]):
        arch,mapping=profile_architecture(span)
        data={'gates':[[0,1],[1,2]],'ops':['cx','cx'],'architecture':arch,'mapping':mapping}
        if method=='original':
            with routing_hooks(router,'original',seed):
                steps,_,interrupted=router.sim_anneal_route(data['gates'],arch,mapping,temperature=10,cooling_rate=.1,
                    termination_temp=.1,order_fraction=1,timeout=300,initial_order='random',reward_name='criticality',take_first_ms=False)
            if interrupted:raise RuntimeError('Source routing timed out')
        else:
            steps=schedule(router,data['gates'],arch,mapping,seed,Config('one_step' if method=='one_budget48' else 'two_step',48))['steps']
        name=f'span{span}_{method}_s{seed}'
        source={'name':name,'method':method,'seed':seed,'input':data,'steps':steps,
                'source_schedule_sha256':sha256_json(steps),'source_scope':'Custom declared corridor layout; not an application benchmark or performance comparison.'}
        save(FOLDER/'source_routes'/f'{name}.json',source);source_records.append(source)
        for basis,idle in product(['x','z'],[0,1]):
            request=request_for(data,steps,basis,idle);certificate=certify(request)
            key=f'{basis}_span{span}_idle{idle}'
            if key not in cache:
                circuit,lowered=lower(request);noisy=add_noise(circuit,.001)
                row=next(r for r in reference['records'] if (r['basis'],r['distance'],r['bridge_span_blocks'],r['idle_blocks'])==(basis,3,span,idle))
                ideal_hash=hashlib.sha256(str(circuit).encode()).hexdigest();noisy_hash=hashlib.sha256(str(noisy).encode()).hexdigest()
                assert ideal_hash==row['ideal_circuit_sha256'] and noisy_hash==row['circuit_sha256']
                assert circuit.num_observables==3 and lowered['backend_meta']['external_flows']==row['external_flows']
                assert (row['model_id'],row['decoder_id'],row['physical_p'])==(MODEL,DECODER,.001)
                assert wilson_interval(row['failures_any'],row['shots'])==(row['wilson95_low'],row['wilson95_high'])
                distance=len(noisy.shortest_graphlike_error());assert distance==3
                cache[key]={'key':key,'ideal_circuit_sha256':ideal_hash,'circuit_sha256':noisy_hash,
                    'num_qubits':circuit.num_qubits,'num_ticks':circuit.num_ticks,
                    'block_footprint_verification':lowered['block_footprint_verification'],
                    'physical_validation':lowered['physical_validation'],'shortest_graphlike_error':distance,
                    'reference_name':row['name'],'reference_shots':row['shots'],'reference_failures_any':row['failures_any'],
                    'reference_p_fail_any':row['p_fail_any'],'reference_wilson95':[row['wilson95_low'],row['wilson95_high']],
                    'model_id':MODEL,'decoder_id':DECODER,'p':.001,'statistics_reused':True,'new_sampling_shots':0}
                save(FOLDER/'physical_checks'/f'{key}.json',cache[key])
            certificate['physical_check_key']=key
            case=f'{name}_{basis}_idle{idle}'
            save(FOLDER/'requests'/f'{case}.json',request)
            save(FOLDER/'certificates'/f'{case}.json',certificate)
            accepted.append({'case':case,'physical_check_key':key,'request_sha256':certificate['request_sha256'],
                             'normalized':certificate['normalization']['performed']})
    # Rejection cases cover both abstract-illegal and abstract-legal unsupported requests.
    base=json.loads((FOLDER/'requests/span1_original_s1_z_idle0.json').read_text())
    negative=[]
    examples=[]
    q=copy.deepcopy(base);q['steps'][0][0][2]=[1,2,9,16,23];examples.append(('legal_detour','corridor',q))
    q=copy.deepcopy(base);q['steps'][0][0][2]=[15,16,17,18,25];examples.append(('legal_right_entry','corridor',q))
    q=copy.deepcopy(base);q['architecture']['disabled_vertices']=[16];examples.append(('unmodelled_defect','architecture',q))
    q=copy.deepcopy(base);q['ops'][1]='t';examples.append(('non_clifford_operation','operations',q))
    q=copy.deepcopy(base);q['timing']['policy']='infer_from_hops';examples.append(('unjustified_time_conversion','timing',q))
    q=copy.deepcopy(base);q['steps'][0][0][2]=[15,23];examples.append(('disconnected_route','route_legality',q))
    for name,code,request in examples:
        try:certify(request)
        except UnsupportedSchedule as error:
            assert error.code==code
            negative.append({'name':name,'expected_code':code,'observed_code':error.code,'message':str(error),'request':request})
        else:raise AssertionError('Unsupported request was accepted')
    save(FOLDER/'negative_cases.json',negative)
    # Assess the frozen Phase 1 full schedules, not sampled subpaths or cropped motifs.
    rejected=Counter();inputs=set();records=0;supported=0
    with zipfile.ZipFile(ROOT/'archives/phase1_snapshot.zip') as z:
        for name in z.namelist():
            if not name.startswith('dascot_phase1/results/routing/') or not name.endswith('.json'):continue
            row=json.loads(z.read(name));instance=row['instance'];inputs.add(instance);records+=1
            data=json.loads((ROOT/'inputs'/instance/'input.json').read_text())
            try:certify(request_for(data,row['steps']))
            except UnsupportedSchedule as error:rejected[error.code]+=1
            else:supported+=1
    save(FOLDER/'phase1_coverage.json',{'source':'Frozen full Phase 1 schedules','records':records,'input_layouts':len(inputs),
         'supported':supported,'rejections':dict(rejected),'scope':'Whole-program compatibility only; 540 records share 20 input/layout definitions, not 540 independent workloads.'})
    assert len(source_records)==18 and len(accepted)==72 and len(cache)==8 and records==540
    save(FOLDER/'summary.json',{'protocol':protocol,'source_routing_configurations':len(source_records),
         'accepted_requests':len(accepted),'unique_physical_circuits':len(cache),'explicit_negative_cases':len(negative),
         'new_monte_carlo_shots':0,'unique_referenced_shots':sum(v['reference_shots'] for v in cache.values()),
         'physical_checks':cache,'accepted':accepted,'frozen_phase1_supported':supported,'frozen_phase1_records':records})
    print(json.dumps({'source_routes':18,'accepted_requests':72,'unique_physical_circuits':8,'new_shots':0,
         'referenced_unique_shots':800000,'phase1_supported':supported,'phase1_records':records}))

if __name__=='__main__':main()
