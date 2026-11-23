"""Full-source author-path geometry qualification. No Monte Carlo labels."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import zipfile

import pymatching
import stim
from exact_program_validation import check_exact
from hamada_path_control import build_oracle, route_plan, generate_routed, routed_graph
from public_clifford import logical_circuit
from public_candidate_pool import digest, features
from run_grover_competition import source_program
from surgery import add_noise

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'results/hamada_path_control_2026-11-23'
ARCHIVE=ROOT/'archives/hamada_path_control_2026-11-23.zip'
FILES=['hamada_path_control.py','hamada_path_oracle.cpp','run_hamada_path_control.py',
       'public_clifford.py','exact_program_validation.py','public_candidate_pool.py',
       'schedule_circuit.py','surgery.py','requirements-lock.txt',
       'results/grover_competition_2026-11-17/candidate_pool.json',
       'results/grover_competition_2026-11-17/physical_index.json',
       'benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json']
PROTOCOL=dict(id='hamada_bfs_mitm_geometry_20261123_v1',date='2026-11-23',shots=0,sampler_calls=0,
    counts=None,confidence_interval=None,distance=3,p=0.001,mu=0,
    input='Complete pinned QASMBench Grover; all 18 original instructions and classical mapping retained',
    path_kernel='Unmodified dcaa249 SingleTimeSliceScheduler::find_path<MeetInTheMiddle>; not complete native scheduler nor 2401.15829v6 artifact identity',
    coordinate_adaptation='Author spatial third axis mapped to two TQEC block slices, endpoint directions updated from H orientation. Exactly one forward temporal edge with odd kink required; fail rather than project/fallback.',
    resources='Common 4x4 logical-cell XY board, data locations (0,0),(3,3); whole XY union reserved per 3-block-z layer; full data lifetime. No concurrency cap.',
    candidates='All 12 previously qualified global shortest plans from unchanged 175-plan pool, one deterministic author path per CX. Old fixed routes and all deeper plans retained, not replaced.',
    search_budget='One original kernel call per source CX, ascending layer operation IDs; per call full 4x4x2 graph. Actual calls and vertices recorded. No scorer or outcome selection.',
    readout='Rank-2 complete original terminal Z correlation basis with signs; 2n independent Clifford generators, all signed inputs, final logical faults, decomposed DEM and graphlike distance.',
    noise='Unchanged TQEC uniform-depolarizing add_noise',decoder='ordinary uncorrelated PyMatching MWPM, decomposed DEM construction only',
    held_out_labels='sealed',sampling_permission=False,seeds=[],stop_rule='No sampling authorized at geometry gate',
    efficacy='No decoded-circuit rate, novelty or speedup claim. This adds a supported original path kernel, not the full required original-method comparison.')


def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def stable_route(r):return {k:v for k,v in r.items() if k!='calls'}


def qualify(program,row,routed,output):
    began=time.perf_counter();ideal,meta=generate_routed(program,routed);comp=time.perf_counter()-began
    began=time.perf_counter();exact=check_exact(ideal,meta,program,True);validation_time=time.perf_counter()-began
    artifacts=output/'circuits';gens=[];unitary=stim.Tableau.from_circuit(logical_circuit(program,False))
    for axis in 'xz':
        for q in range(program['logical_qubits']):
            pauli=unitary.x_output(q) if axis=='x' else unitary.z_output(q)
            bases=str(pauli)[1:].replace('_','Z').lower()
            if pauli.sign!=1 or set(bases)-{'x','z'}:raise ValueError('Unsupported generator boundary')
            inputs='z'*q+axis+'z'*(program['logical_qubits']-q-1)
            began=time.perf_counter();c,m=generate_routed(program,routed,inputs,bases);seconds=time.perf_counter()-began
            began=time.perf_counter();v=check_exact(c,m,program)
            target=stim.PauliString('I'*q+axis.upper()+'I'*(program['logical_qubits']-q-1)+str(pauli)[1:].replace('_','I'))
            span=[]
            for mask in range(1,1<<len(m['external_flows'])):
                product=stim.PauliString(2*program['logical_qubits'])
                for i,f in enumerate(m['external_flows']):
                    if mask>>i&1:product*=stim.PauliString(f)
                if product==target:span=[i for i in range(len(m['external_flows'])) if mask>>i&1];break
            if not span:raise AssertionError('Missing complete source generator')
            validation_seconds=time.perf_counter()-began
            raw=str(c).encode();h=sha(raw);(artifacts/(h+'.stim')).write_bytes(raw)
            gens.append(dict(generator=f'{axis.upper()}{q}',ideal_sha256=h,target_flow=str(target),span=span,
                input_bases=inputs,output_bases=bases,validation=v,compile_seconds=seconds,validation_seconds=validation_seconds))
    began=time.perf_counter();noisy=add_noise(ideal,PROTOCOL['p']);noise_time=time.perf_counter()-began
    began=time.perf_counter();dem=noisy.detector_error_model(decompose_errors=True);dem_time=time.perf_counter()-began
    began=time.perf_counter();pymatching.Matching.from_detector_error_model(dem);decoder_time=time.perf_counter()-began
    began=time.perf_counter();distance=len(noisy.shortest_graphlike_error());distance_time=time.perf_counter()-began
    if distance!=3:raise AssertionError('Complete composition loses distance 3')
    hashes={}
    for kind,obj,suffix in [('ideal',ideal,'.stim'),('noisy',noisy,'.stim'),('dem',dem,'.dem')]:
        raw=str(obj).encode();h=sha(raw);(artifacts/(h+suffix)).write_bytes(raw);hashes[kind+'_sha256']=h
    f=features(program,row['plan']);f['stim_ticks']=ideal.num_ticks
    f['ancilla_reservation_block_z']=sum(3*(len(x['reserved_xy'])-2) for x in meta['gate_footprints'])
    result=dict(candidate_id='mitm_'+row['candidate_id'],base_candidate_id=row['candidate_id'],
        source_sha256=program['source_sha256'],base_plan_sha256=row['plan_sha256'],plan_sha256=digest(stable_route(routed)),
        **hashes,num_qubits=ideal.num_qubits,num_detectors=ideal.num_detectors,num_observables=ideal.num_observables,
        graphlike_distance=distance,features=f,backend_meta=meta,validation=exact,generators=gens,
        shots=0,counts=None,confidence_interval=None,
        timing=dict(main_compile_seconds=comp,exact_validation_seconds=validation_time,
            generator_compile_seconds=sum(x['compile_seconds'] for x in gens),generator_validation_seconds=sum(x['validation_seconds'] for x in gens),
            noise_seconds=noise_time,dem_seconds=dem_time,decoder_construction_seconds=decoder_time,distance_search_seconds=distance_time,
            scorer_seconds=None,calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None))
    save(output/'certificates'/(result['candidate_id']+'.json'),result)
    return result


def run(output,workers):
    if output.exists():raise FileExistsError('Use fresh result directory; preserve frozen evidence')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python 3.12 required')
    _,program=source_program()
    pool=json.loads((ROOT/'results/grover_competition_2026-11-17/candidate_pool.json').read_text())
    old=json.loads((ROOT/'results/grover_competition_2026-11-17/physical_index.json').read_text())
    rows=[r for r in pool if r['candidate_id'] in {r['candidate_id'] for r in old}]
    if len(rows)!=12 or len(pool)!=175:raise ValueError('Frozen competition changed')
    output.mkdir(parents=True);(output/'circuits').mkdir();(output/'certificates').mkdir()
    save(output/'protocol.json',PROTOCOL)
    with tempfile.TemporaryDirectory() as temp:
        binary=Path(temp)/'oracle';began=time.perf_counter();build_oracle(binary);build=time.perf_counter()-began
        began=time.perf_counter();routes=[route_plan(program,r['plan'],binary) for r in rows];routing=time.perf_counter()-began
    save(output/'routed_plans.json',[dict(candidate_id='mitm_'+row['candidate_id'],routed=r) for row,r in zip(rows,routes)])
    results=[];began=time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        fs=[ex.submit(qualify,program,row,routed,output) for row,routed in zip(rows,routes)]
        for future in as_completed(fs):
            r=future.result();results.append(r);print(r['candidate_id'],r['num_qubits'],r['features']['stim_ticks'],'distance=3; complete readout+all generators passed; 0 shots',flush=True)
    wall=time.perf_counter()-began;results.sort(key=lambda r:r['candidate_id'])
    save(output/'physical_index.json',[{k:v for k,v in r.items() if k not in ('backend_meta','validation','generators')} for r in results])
    summary=dict(protocol_id=PROTOCOL['id'],new_shots=0,sampler_calls=0,new_physical_compilations=5*len(results),
        main_compilations=len(results),generator_compilations=4*len(results),exploratory_main_compilations=1,
        exploratory_note='Before this frozen batch, one g174 exact main-readout smoke compilation, 0 shots; not counted twice in candidate pool.',
        preserved_base_pool_size=len(pool),preserved_old_physical_count=len(old),new_physical_candidates=len(results),
        unique_new_noisy_hashes=len({r['noisy_sha256'] for r in results}),
        new_noisy_hashes_not_in_old=len({r['noisy_sha256'] for r in results}-{r['noisy_sha256'] for r in old}),
        all_source_instructions=len(program['operations']),all_original_outputs=program['terminal_readout'],
        author_kernel_calls=sum(len(r['calls']) for r in routes),
        old_vs_new=[dict(base_candidate_id=r['base_candidate_id'],old_qubits=next(o['num_qubits'] for o in old if o['candidate_id']==r['base_candidate_id']),
            new_qubits=r['num_qubits'],same_noisy_hash=any(o['noisy_sha256']==r['noisy_sha256'] for o in old),
            stim_ticks=r['features']['stim_ticks'],protected_idle_block_z=r['features']['total_protected_idle_block_z'],
            ancilla_reserved_block_z=r['features']['ancilla_reservation_block_z']) for r in results],
        timing=dict(author_oracle_build_seconds=build,route_construction_including_subprocess_seconds=routing,
            physical_batch_wall_seconds=wall,workers=workers,independent_timing_benchmark=False,scorer_seconds=None,
            calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None),
        status='Two-slice author path-kernel control physically qualified. Full native Hamada/3D Dijkstra, O3LS common method, development revision/calibration/freeze and held-out remain open.',
        held_out_labels='sealed',sampling_permission=False,mu=0)
    save(output/'summary.json',summary)
    vendor=[str(p.relative_to(ROOT)) for p in VENDOR_FILES()]
    save(output/'environment.json',dict(python=platform.python_version(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256={p:sha((ROOT/p).read_bytes()) for p in FILES+vendor},
        packages={p:md.version(p) for p in ['tqec','stim','pymatching','numpy']},
        tqec_direct_url=json.loads(md.distribution('tqec').read_text('direct_url.json')),
        compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],compiler_flags=['-std=c++17','-O2','-Wall','-Wextra']))
    return summary


def VENDOR_FILES():return sorted((ROOT/'third_party/hamada_path_2026-11-23').rglob('*.*'))+ [ROOT/'third_party/hamada_path_2026-11-23/LICENSE']


def check(output):
    _,program=source_program();env=json.loads((output/'environment.json').read_text())
    for p,h in env['source_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h:raise AssertionError('Frozen source changed: '+p)
    protocol=json.loads((output/'protocol.json').read_text())
    if protocol!=PROTOCOL:raise AssertionError('Protocol changed')
    index=json.loads((output/'physical_index.json').read_text());routes=json.loads((output/'routed_plans.json').read_text())
    old=json.loads((ROOT/'results/grover_competition_2026-11-17/physical_index.json').read_text())
    if {r['base_candidate_id'] for r in index}!={r['candidate_id'] for r in old}:raise AssertionError('Minimum candidate dropped')
    with tempfile.TemporaryDirectory() as temp:
        binary=Path(temp)/'oracle';build_oracle(binary)
        for row in routes:
            route=row['routed'];again=route_plan(program,route['base_plan'],binary)
            if stable_route(again)!=stable_route(route):raise AssertionError('Original path replay changed')
            routed_graph(program,route)  # Complete geometry and data lifetime validation, no compile/sampler.
    with zipfile.ZipFile(ARCHIVE) as archive:
        for row in index:
            cert=json.loads((output/'certificates'/(row['candidate_id']+'.json')).read_text())
            if cert['plan_sha256']!=digest(stable_route(next(x['routed'] for x in routes if x['candidate_id']==row['candidate_id']))):raise AssertionError('Route hash differs')
            for kind,suffix in [('ideal','.stim'),('noisy','.stim'),('dem','.dem')]:
                h=row[kind+'_sha256'];raw=archive.read('circuits/'+h+suffix)
                if sha(raw)!=h:raise AssertionError('Circuit hash differs')
                if kind=='ideal':
                    ideal=stim.Circuit(raw.decode());check_exact(ideal,cert['backend_meta'],program,True)
                if kind=='noisy' and len(stim.Circuit(raw.decode()).shortest_graphlike_error())!=3:raise AssertionError('Distance differs')
            for gen in cert['generators']:
                raw=archive.read('circuits/'+gen['ideal_sha256']+'.stim')
                if sha(raw)!=gen['ideal_sha256'] or not gen['validation']['exact']:raise AssertionError('Generator evidence differs')
    print('PASS: all 12 original path replays, complete geometry, archived full outputs, generator hashes, distance3; 0 new shots')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=DEFAULT);parser.add_argument('--workers',type=int,default=2);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check:check(args.output)
    else:
        if not 1<=args.workers<=4:raise ValueError('Use 1..4 bounded workers')
        print(json.dumps(run(args.output,args.workers),indent=2))
