"""Zero-shot, complete-source projection scheduling/physical qualification."""
import argparse
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import zipfile

import stim
import pymatching
from hamada_projection_control import build_driver,schedule,graph,generate,validate,VENDOR
from public_clifford import logical_circuit
from public_candidate_pool import digest
from exact_program_validation import check_exact
from run_grover_competition import source_program
from surgery import add_noise

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'results/hamada_projection_2026-11-24'
ARCHIVE=ROOT/'archives/hamada_projection_2026-11-24.zip'
PROTOCOL=dict(id='complete_source_projection_geometry_20261124_v1',date='2026-11-24',shots=0,seeds=[],counts=None,ci=None,mu=0,
    source='Pinned complete public Grover: 18 instructions and both original terminal measurements; no removed H/X/classical mappings',
    controls=['source_order','height_priority'],
    native_components='Fixed dcaa249 ProjectiveScheduler::find_path<CareKinkParity>, height/kink projection routines, PrioritizedInstructionDependencyManager',
    adapter='Full H/X/readout DAG loop; H=3 block-z, X virtual, terminal readout at common end, native height coordinates retained including backwards edges. Activate children after height update, following old paper rather than new release full-loop ordering.',
    geometry='Native path (x,y,t) -> (x,y,t+1) in block graph; all data lifetimes; ordinary no-H route pipes, deterministic six-ZX-cube matching-wall inference. No flattening or route fallback.',
    resources='Common existing diagonal layout envelope, 4x4 logical cells. Not an inferred real hardware cap; no concurrency cap and all old 175/12+12 candidates retained.',
    scope='Complete source projection policy/geometry reference in declared adapter, not bit-for-bit native whole compiler nor same old 175-plan pool/budget algorithm performance comparison.',
    noise='d=3, p=0.001, fixed TQEC uniform depolarizing add_noise',decoder='ordinary uncorrelated PyMatching MWPM; decomposed DEM construction only',
    acceptance='Complete rank-2 original output, all signed inputs, 4 X/Z generators with original Pauli frame, final logical faults, graphlike distance3. Stop/reject if physical tests fail; do not tune on results.',
    calibration=None,held_out_labels='sealed',sampling_permission=False,stopping_rule='No research sampling at this geometry gate; no held-out access')
FILES=['hamada_projection_control.py','hamada_projection_driver.cpp','run_hamada_projection_control.py',
    'public_clifford.py','public_candidate_pool.py','schedule_circuit.py','exact_program_validation.py',
    'surgery.py','run_public_audit.py','requirements-lock.txt','benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json']


def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def graph_hash(g):return digest(dict(cubes=sorted((tuple(c.position.as_tuple()),str(c.kind),c.label) for c in g.cubes),pipes=sorted((tuple(p.u.position.as_tuple()),tuple(p.v.position.as_tuple()),str(p.kind)) for p in g.pipes)))


def qualify(program,plan,output,label):
    began=time.perf_counter();ideal,meta=generate(program,plan);compile_seconds=time.perf_counter()-began
    began=time.perf_counter();validation=check_exact(ideal,meta,program,True);exact_seconds=time.perf_counter()-began
    artifact=output/'circuits';generators=[];unitary=stim.Tableau.from_circuit(logical_circuit(program,False));n=program['logical_qubits']
    for axis in 'xz':
        for q in range(n):
            pauli=unitary.x_output(q) if axis=='x' else unitary.z_output(q)
            outputs=str(pauli)[1:].replace('_','Z').lower();inputs='z'*q+axis+'z'*(n-q-1)
            if pauli.sign!=1 or set(outputs)-{'x','z'}:raise ValueError('Unsupported signed/Y generator')
            began=time.perf_counter();c,m=generate(program,plan,inputs,outputs);seconds=time.perf_counter()-began
            began=time.perf_counter();v=check_exact(c,m,program)
            target=stim.PauliString('I'*q+axis.upper()+'I'*(n-q-1)+str(pauli)[1:].replace('_','I'));found=None
            for mask in range(1,1<<len(m['external_flows'])):
                product=stim.PauliString(2*n)
                for i,f in enumerate(m['external_flows']):
                    if mask>>i&1:product*=stim.PauliString(f)
                if product==target:found=[i for i in range(len(m['external_flows'])) if mask>>i&1];break
            if found is None:raise AssertionError('Incomplete source Clifford generator span')
            raw=str(c).encode();h=sha(raw);(artifact/(h+'.stim')).write_bytes(raw)
            generators.append(dict(generator=axis.upper()+str(q),input_bases=inputs,output_bases=outputs,target_flow=str(target),span=found,
                ideal_sha256=h,validation=v,backend_meta=m,compile_seconds=seconds,exact_seconds=time.perf_counter()-began))
    began=time.perf_counter();noisy=add_noise(ideal,0.001);noise_seconds=time.perf_counter()-began
    began=time.perf_counter();dem=noisy.detector_error_model(decompose_errors=True);dem_seconds=time.perf_counter()-began
    began=time.perf_counter();pymatching.Matching.from_detector_error_model(dem);decoder_seconds=time.perf_counter()-began
    began=time.perf_counter();distance=len(noisy.shortest_graphlike_error());distance_seconds=time.perf_counter()-began
    hashes={}
    for kind,obj,suffix in [('ideal',ideal,'.stim'),('noisy',noisy,'.stim'),('dem',dem,'.dem')]:
        raw=str(obj).encode();h=sha(raw);(artifact/(h+suffix)).write_bytes(raw);hashes[kind+'_sha256']=h
    record=dict(candidate_id=label,source_sha256=program['source_sha256'],plan_sha256=digest(plan),**hashes,
        graphlike_distance=distance,accepted=distance==3,num_qubits=ideal.num_qubits,num_detectors=ideal.num_detectors,
        num_observables=ideal.num_observables,stim_ticks=ideal.num_ticks,backend_meta=meta,validation=validation,generators=generators,
        shots=0,counts=None,confidence_interval=None,timing=dict(main_compile_seconds=compile_seconds,exact_seconds=exact_seconds,
            generator_compile_seconds=sum(x['compile_seconds'] for x in generators),generator_exact_seconds=sum(x['exact_seconds'] for x in generators),
            noise_seconds=noise_seconds,dem_seconds=dem_seconds,decoder_construction_seconds=decoder_seconds,distance_search_seconds=distance_seconds,
            scorer_seconds=None,calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None))
    save(output/'certificates'/(label+'.json'),record)
    return record


def resources(program,plan,g,meta):
    positions,trace,_=validate(program,plan);end=meta['output_z'];active=[[] for _ in positions]
    for e in plan['events']:
        op=program['operations'][e['operation_id']]
        if op['name']=='h':active[op['qubits'][0]].append((e['start'],e['start']+3))
        elif op['name']=='cx':
            for q,p in zip(op['qubits'],[e['path'][0],e['path'][-1]]):active[q].append((p[2],p[2]+1))
    gaps=[]
    for intervals in active:
        stop=0;idle=[]
        for a,b in sorted(intervals):
            if a<stop:raise AssertionError('Overlapping source operations on data')
            if a>stop:idle.append(a-stop)
            stop=b
        if stop<end:idle.append(end-stop)
        gaps.append(idle)
    data=set(positions);cells={}
    for c in g.cubes:
        if (c.position.x,c.position.y) in data:continue
        cells.setdefault((c.position.x,c.position.y),[]).append(c.position.z)
    # Lifetime is from initialization to final measurement, including every
    # intermediate node; continuous gaps become explicit conservative reservations.
    lifetimes=[dict(x=x,y=y,start_block_z=min(zs)-1,end_block_z=max(zs),lifetime_block_z=max(zs)-min(zs)+1,
                    native_voxel_count=len(zs)) for (x,y),zs in sorted(cells.items())]
    return dict(template_block_z=end,qec_rounds=None,stim_ticks=meta['num_ticks'],routing_steps=None,
        physical_layers=None,source_cx_count=2,source_h_count=10,distinct_h_start_times=len({e['start'] for e in plan['events'] if program['operations'][e['operation_id']]['name']=='h'}),
        data_lifetime_block_z=len(positions)*end,protected_idle_intervals_block_z=gaps,total_protected_idle_block_z=sum(map(sum,gaps)),
        ancilla_native_voxels=sum(x['native_voxel_count'] for x in lifetimes),ancilla_conservative_lifetime_block_z=sum(x['lifetime_block_z'] for x in lifetimes),ancilla_lifetimes=lifetimes,
        geometry_sha256=graph_hash(g),note='Projection has asynchronous endpoint events, not homogeneous 3-block H/CX layers; routing_steps/physical_layers null. Lifetime envelope is conservative if a site has disjoint native intervals. No code-beat/QEC-round/TICK conversion assumed.')


def run(output):
    if output.exists():raise FileExistsError('Use fresh result directory')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
    _,program=source_program();output.mkdir(parents=True);(output/'circuits').mkdir();(output/'certificates').mkdir()
    save(output/'protocol.json',PROTOCOL)
    with tempfile.TemporaryDirectory() as temp:
        binary=Path(temp)/'driver';began=time.perf_counter();build_driver(binary);build_seconds=time.perf_counter()-began
        controls=[dict(policy=p,**schedule(program,binary,p)) for p in PROTOCOL['controls']]
    groups={}
    for control in controls:
        g,_,meta=graph(program,control['plan']);h=graph_hash(g);control['geometry_sha256']=h
        control['resources']=resources(program,control['plan'],g,{**meta,'num_ticks':None})
        groups.setdefault(h,control)
    save(output/'controls.json',controls)
    records=[]
    for i,(h,control) in enumerate(groups.items()):
        r=qualify(program,control['plan'],output,f'projection_{i:02}');records.append(r)
        print(r['candidate_id'],r['num_qubits'],r['stim_ticks'],'distance',r['graphlike_distance'],'accepted',r['accepted'],'0 shots',flush=True)
        for row in controls:
            if row['geometry_sha256']==h:
                row['certificate_id']=r['candidate_id'];row['resources']['stim_ticks']=r['stim_ticks']
                # Exact replay with each control's own frame/metadata, same graph.
                _,_,meta=graph(program,row['plan']);meta.update(external_flows=r['backend_meta']['external_flows'])
                row['reused_main_validation']=check_exact(stim.Circuit((output/'circuits'/(r['ideal_sha256']+'.stim')).read_text()),meta,program,True)
    save(output/'controls.json',controls)
    return finalize(output,controls,records,build_seconds)


def finalize(output,controls,records,build_seconds=None):
    files=FILES+[str(p.relative_to(ROOT)) for p in VENDOR.rglob('*') if p.is_file()]
    save(output/'environment.json',dict(python=platform.python_version(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        files_sha256={p:sha((ROOT/p).read_bytes()) for p in files},packages={p:md.version(p) for p in ['tqec','stim','numpy','pymatching']},
        tqec_direct_url=json.loads(md.distribution('tqec').read_text('direct_url.json')),compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
        compiler_flags=['-std=c++17','-O2','-Wall','-Wextra']))
    summary=dict(protocol_id=PROTOCOL['id'],controls=len(controls),unique_geometries=len({c['geometry_sha256'] for c in controls}),unique_noisy_hashes=len({r['noisy_sha256'] for r in records}),
        main_compilations=len(records),generator_compilations=4*len(records),exploratory_main_compilations=1,exploratory_graph_rejection_before_compilation=1,
        new_research_shots=0,sampler_calls=0,counts=None,confidence_interval=None,
        accepted=all(r['accepted'] for r in records),control_summary=[dict(policy=c['policy'],plan_sha256=digest(c['plan']),geometry_sha256=c['geometry_sha256'],resources=c['resources'],certificate_id=c['certificate_id']) for c in controls],
        timing=dict(driver_build_seconds=build_seconds,routing_seconds_including_subprocess=[c['routing_seconds_including_subprocess'] for c in controls],scorer_seconds=None,calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None,independent_performance_benchmark=False),
        comparison_scope='New asynchronous projection geometry reference; old 175 plans and 24 complete physical candidates retained. Different admissible lowering/search domain; no same-pool/budget speedup or LER claim.',
        held_out_labels='sealed',sampling_permission=False,mu=0)
    save(output/'summary.json',summary);return summary


def check(output):
    _,program=source_program();env=json.loads((output/'environment.json').read_text())
    for p,h in env['files_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h:raise AssertionError('Frozen source changed: '+p)
    if json.loads((output/'protocol.json').read_text())!=PROTOCOL:raise AssertionError('Protocol changed')
    controls=json.loads((output/'controls.json').read_text())
    with tempfile.TemporaryDirectory() as temp,zipfile.ZipFile(ARCHIVE) as z:
        binary=Path(temp)/'driver';build_driver(binary)
        for c in controls:
            if schedule(program,binary,c['policy'])['plan']!=c['plan']:raise AssertionError('Original projection replay differs')
            g,_,m=graph(program,c['plan'])
            if graph_hash(g)!=c['geometry_sha256']:raise AssertionError('Full geometry differs')
            r=json.loads((output/'certificates'/(c['certificate_id']+'.json')).read_text())
            for kind,suffix in [('ideal','.stim'),('noisy','.stim'),('dem','.dem')]:
                h=r[kind+'_sha256'];raw=z.read('circuits/'+h+suffix)
                if sha(raw)!=h:raise AssertionError('Archive differs')
                if kind=='ideal':
                    m.update(external_flows=r['backend_meta']['external_flows']);check_exact(stim.Circuit(raw.decode()),m,program,True)
                elif kind=='noisy' and len(stim.Circuit(raw.decode()).shortest_graphlike_error())!=r['graphlike_distance']:raise AssertionError('Distance differs')
            for gen in r['generators']:
                raw=z.read('circuits/'+gen['ideal_sha256']+'.stim')
                if sha(raw)!=gen['ideal_sha256']:raise AssertionError('Generator hash differs')
                check_exact(stim.Circuit(raw.decode()),gen['backend_meta'],program)
    print('PASS: full-source native projection replay, unflattened geometry, complete original output and all generator checks; no new shots')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=DEFAULT);ap.add_argument('--check',action='store_true');ap.add_argument('--finish-records',action='store_true');a=ap.parse_args()
    if a.check:check(a.output)
    elif a.finish_records:
        if (a.output/'environment.json').exists() or (a.output/'summary.json').exists():raise FileExistsError('Final records already frozen')
        if json.loads((a.output/'protocol.json').read_text())!=PROTOCOL:raise ValueError('Protocol differs')
        controls=json.loads((a.output/'controls.json').read_text());records=[]
        for p in sorted((a.output/'certificates').glob('*.json')):
            r=json.loads(p.read_text())
            for key,suffix in [('ideal','.stim'),('noisy','.stim'),('dem','.dem')]:
                if sha((a.output/'circuits'/(r[key+'_sha256']+suffix)).read_bytes())!=r[key+'_sha256']:raise ValueError('Incomplete raw artifacts')
            records.append(r)
        if not records or any('reused_main_validation' not in c for c in controls):raise ValueError('Physical batch incomplete')
        print(json.dumps(finalize(a.output,controls,records),indent=2))
    else:print(json.dumps(run(a.output),indent=2))
