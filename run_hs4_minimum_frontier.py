"""Qualify all144 complete public hs4 depth minima outside H-first. Zero shots."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import time
import zipfile

import stim
import pymatching
from public_minimum_pool import minimum_gate_plans
from public_candidate_pool import digest,features,canonical
from public_clifford import load_program,graph_program
from common_physical_pool import physical_memory_features,select,POLICIES
from exact_program_validation import check_exact
from exact_compile_cache import ExactCompileCache
from surgery import add_noise

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'results/hs4_minimum_frontier_2026-11-27'
CODE=['public_minimum_pool.py','exact_compile_cache.py','run_hs4_minimum_frontier.py',
      'public_clifford.py','public_candidate_pool.py','common_physical_pool.py',
      'projection_geometry_metrics.py','exact_program_validation.py','schedule_circuit.py',
      'surgery.py','requirements-lock.txt','tests/test_public_minimum_pool.py']
PROTOCOL=dict(id='full_public_hs4_all_homogeneous_minima_20261127_v1',
 source='Complete unchanged QASMBench hs4_n4, revision357b942396d5c2b7cbc1c229c585a6ef5ccaebac',
 role='Existing hidden_shift family remains development; no new independent family.',
 selection='Every exact global minimum of all homogeneous ready H/CX subsets, eager virtual/readout closure. No H-first closure; no concurrency cap; mixed H/CX layers remain excluded.',
 safety_limit_minima=4096,pool_budget=144,
 device='Exact original hs4 spacing3 physical coordinate/index catalogue, experimental geometry not a real chip cap',
 complete_output='All4 original Z output bits, rank4; original ordered external basis fixed from old parallel certificate',
 physical_model='Existing d3 k1 H/CX TQEC complete graph, X virtual frame, all source instructions/dependencies retained',
 noise='TQEC uniform-depolarizing add_noise p=0.001',decoder='ordinary uncorrelated PyMatching MWPM / decomposed DEM; construction only',
 compile_policy='Per candidate9 requests (main+8 generators), cache exact full request keys; all9 validation targets still checked, no post-hoc deduction of observed calls.',
 expected_compile_ceiling_per_candidate=9,physical_compile_limit_per_candidate=9,
 shots=0,seeds=[],counts=None,confidence_interval=None,sampling_permission=False,held_out_labels='sealed',mu=0,
 stop_rule='Abort on missing minimum, semantic/footprint/site/readout/DEM/distance mismatch. No outcome-selected replacement. Raw equal-Pauli v1 remains stopped; no calibration/revision.',
 units='H/CX layer=3block-z only in this profile. CX steps,H layers,block-z,TICK separate; QEC rounds null.',
 comparability='Offline complete-pool qualification and selectors, not an original O3LS/SPARO/CircLS online equal-CPU comparison.')


def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def reference():
    prior=ROOT/'results/public_hs4_2026-11-02'
    c=read(prior/'certificates/hs4_parallel_spacing3.json')
    r=next(x for x in read(prior/'summary.json')['records'] if x['record_id']=='hs4_parallel_spacing3')
    with zipfile.ZipFile(ROOT/'archives/public_hs4_2026-11-02.zip') as z:
        h=r['ideal_circuit_sha256'];data=z.read('results/public_hs4_2026-11-02/samples/'+r['sample_id']+'_ideal.stim')
    assert sha(str(stim.Circuit(data.decode())).encode())==h
    return c,r,stim.Circuit(data.decode())


def physical_one(program,row,output,device,readout):
    cache=ExactCompileCache();ideal,meta=cache.generate(program,row['plan'])
    if ideal.get_final_qubit_coordinates()!=device:raise AssertionError('Physical coordinate/index catalogue differs')
    if meta['external_flows']!=readout:raise AssertionError('Complete ordered original readout differs')
    t=time.perf_counter();validation=check_exact(ideal,meta,program,True);main_exact=time.perf_counter()-t
    gens=cache.generators(program,row['plan'],output/'circuits')
    if len(gens)!=8 or len(cache.requests)!=9 or sum(not r['cache_hit'] for r in cache.requests)>9:
        raise AssertionError('Validation or declared compile budget incomplete')
    t=time.perf_counter();noisy=add_noise(ideal,.001);dem=noisy.detector_error_model(decompose_errors=True)
    pymatching.Matching.from_detector_error_model(dem);noise_seconds=time.perf_counter()-t
    t=time.perf_counter();distance=len(noisy.shortest_graphlike_error());distance_seconds=time.perf_counter()-t
    if distance!=3:raise AssertionError('Graphlike distance changed')
    arts={}
    for k,obj,ext in [('ideal',ideal,'.stim'),('noisy',noisy,'.stim'),('dem',dem,'.dem')]:
        b=str(obj).encode();h=sha(b);(output/'circuits'/(h+ext)).write_bytes(b);arts[k+'_sha256']=h
    t=time.perf_counter();graph,_,gm=graph_program(program,row['plan']);f=physical_memory_features(graph,gm);geometry_seconds=time.perf_counter()-t
    f.update(stim_ticks=ideal.num_ticks,qec_rounds=None,static_site_ticks=len(device)*ideal.num_ticks,
             active_physical_sites=ideal.num_qubits,device_physical_sites=len(device))
    result=dict(candidate_id=row['candidate_id'],source_sha256=program['source_sha256'],plan_sha256=row['plan_sha256'],
        **arts,backend_meta=meta,validation=validation,generators=gens,compile_requests=cache.requests,
        features=f,profile_features={**row['features'],'stim_ticks':ideal.num_ticks},
        qualified_complete_output=True,outside_device_sites=0,external_flows=readout,
        device_sha256=digest(device),num_qubits=ideal.num_qubits,num_detectors=ideal.num_detectors,
        graphlike_distance=distance,shots=0,counts=None,confidence_interval=None,
        timing=dict(actual_physical_compile_seconds=sum(r['physical_compile_seconds'] or 0 for r in cache.requests),
          main_exact_seconds=main_exact,generator_exact_seconds=sum(g['exact_validation_seconds'] for g in gens),
          compile_request_seconds=sum(r['request_seconds'] for r in cache.requests),geometry_features_seconds=geometry_seconds,
          noise_dem_decoder_construction_seconds=noise_seconds,distance_search_seconds=distance_seconds,
          routing_seconds=None,scorer_seconds=None,calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None))
    save(output/'certificates'/(row['candidate_id']+'.json'),result)
    return {k:v for k,v in result.items() if k not in ('backend_meta','validation','generators')}


def run(output,workers):
    if output.exists():raise FileExistsError('Fresh result directory required')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
    program=load_program(ROOT/'benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm')
    manifest=read(ROOT/'benchmarks/public_2026-11-02/manifest.json')
    item=next(x for x in manifest['files'] if x['path'].endswith('hs4_n4.qasm'))
    if item['sha256']!=program['source_sha256']:raise AssertionError('Pinned source differs')
    t=time.perf_counter();answer=minimum_gate_plans(program);dp_seconds=time.perf_counter()-t
    if answer['minimum_plan_count']!=144 or answer['minimum_physical_layers']!=9:raise AssertionError('Frozen preflight pool differs')
    rows=[dict(candidate_id=f'h{i:03}',plan=p,plan_sha256=digest(p),features=features(program,p)) for i,p in enumerate(answer['plans'])]
    cert,old,reference_circuit=reference();device=reference_circuit.get_final_qubit_coordinates()
    def sig(p):return [(x['kind'],sorted(x['operation_ids']),x['orientation_before'],x['orientation_after']) for x in p['layers']]
    ref=next(r['candidate_id'] for r in rows if sig(r['plan'])==sig(cert['backend_meta']['plan']))
    output.mkdir(parents=True);(output/'circuits').mkdir();(output/'certificates').mkdir()
    save(output/'protocol.json',PROTOCOL);save(output/'program.json',program);save(output/'candidate_pool.json',rows)
    save(output/'dp_summary.json',{k:v for k,v in answer.items() if k!='plans'})
    save(output/'device.json',dict(coordinates=device,sha256=digest(device),reference_id=ref,source='unchanged original hs4 spacing3 catalogue'))
    env=dict(python=platform.python_version(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_files_sha256={p:sha((ROOT/p).read_bytes()) for p in CODE},source_manifest=manifest,
        packages={p:md.version(p) for p in ('stim','tqec','pymatching','numpy','qiskit')},
        tqec_direct_url=json.loads(md.distribution('tqec').read_text('direct_url.json')))
    save(output/'environment.json',env)
    results=[];t=time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        jobs=[ex.submit(physical_one,program,r,output,device,cert['backend_meta']['external_flows']) for r in rows]
        for f in as_completed(jobs):
            r=f.result();results.append(r);print(r['candidate_id'],len(results),'of144',r['noisy_sha256'][:12],'full4-output distance3,0shots',flush=True)
    wall=time.perf_counter()-t;results.sort(key=lambda r:r['candidate_id']);save(output/'physical_index.json',results)
    reference_row=next(r for r in results if r['candidate_id']==ref)
    if any(reference_row[k+'_sha256']!=old[k+'_circuit_sha256' if k!='dem' else 'dem_sha256'] for k in ('ideal','noisy','dem')):
        raise AssertionError('Original parallel baseline hashes changed')
    selections=[select(results,k,ref,144) for k in POLICIES];save(output/'selections.json',selections)
    summary=dict(reference_id=ref,source_sha256=program['source_sha256'],minimum_physical_layers=9,
        full_search_legal_plans=answer['all_legal_plan_count'],counted_nonminimum_plans=answer['nonminimum_plan_count'],
        qualified_minimum_plans=144,unique_noisy_circuits=len({r['noisy_sha256'] for r in results}),
        exact_targets=sum(1+len(read(output/'certificates'/(r['candidate_id']+'.json'))['generators']) for r in results),
        compile_requests=sum(len(r['compile_requests']) for r in results),
        actual_physical_compilations=sum(not v['cache_hit'] for r in results for v in r['compile_requests']),
        exact_cache_hits=sum(v['cache_hit'] for r in results for v in r['compile_requests']),
        unique_wait_profiles=len({canonical(r['profile_features']['protected_idle_intervals_block_z']) for r in results}),
        original_parallel_hashes_preserved=True,new_shots=0,sampler_calls=0,counts=None,confidence_interval=None,
        role='Existing hidden_shift development only; no new held-out labels, calibration or risk revision.',mu=0)
    save(output/'summary.json',summary)
    save(output/'timing.json',dict(dp_construction_seconds=dp_seconds,physical_batch_wall_seconds=wall,workers=workers,
        actual_compile_sum_seconds=sum(r['timing']['actual_physical_compile_seconds'] for r in results),
        routing_benchmark_seconds=None,scorer_benchmark_seconds=None,calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None,
        note='Concurrent compile wall accounting is throughput, not independent CPU-speed comparisons. Cache saves requests, no measured uncached time subtraction.'))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--output',type=Path,default=DEFAULT);p.add_argument('--workers',type=int,default=6);a=p.parse_args();run(a.output,a.workers)
