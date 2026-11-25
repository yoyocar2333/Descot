"""Normalize all 25 qualified development circuits; equal-budget offline selection.

No physical compilation, calibration, Monte Carlo or held-out label access.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
import zipfile

import pymatching
import stim
from common_physical_pool import catalogue,remap,physical_memory_features,select,POLICIES
from exact_program_validation import check_exact
from public_candidate_pool import digest
from public_clifford import graph_program
from hamada_path_control import routed_graph
from hamada_projection_control import graph as projection_graph
from run_grover_competition import source_program

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'results/common_physical_pool_2026-11-25'
ARCHIVE=ROOT/'archives/common_physical_pool_2026-11-25.zip'
READOUT=['ZIIZ','IZZI']
CODE=['common_physical_pool.py','run_common_physical_pool.py','projection_geometry_metrics.py','exact_program_validation.py','public_clifford.py','public_candidate_pool.py','hamada_path_control.py','hamada_projection_control.py','schedule_circuit.py','surgery.py','run_public_audit.py','requirements-lock.txt','benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json']
PROTOCOL=dict(id='shared_device_physical_pool_20261125_v1',date='2026-11-25',family='grover_search development only',shots=0,seeds=[],counts=None,confidence_interval=None,mu=0,
    pool='All 12 fixed-route, all 12 MITM variants, one full-source projection. Original 175 abstract plans retained; this is not the exhaustive gate-level physical pool.',
    device='Exact union of static XY physical coordinate sets of all 25 original main circuits; freeze before selector evaluation. Experimental device catalogue, not a measured chip or a manufactured concurrency cap.',
    coordinate_policy='Preserve all gates, noise, record indices, repeats, TICKs, detector/observable annotations and coordinates. Relabel qubits injectively; add only metadata for unused device sites, holding no logical state and receiving no fabricated noise.',
    complete_observables='Unchanged ordered complete basis: Z on original q1/c1 then Z on q0/c0. External flows ZIIZ, IZZI, exact signs and rank2 validated. No parity subset or basis optimization.',
    validation='All main original outputs/signed inputs/final faults and all four independent generator experiments per candidate; exact unchanged ideal/noisy DEM after relabeling. No sampling.',
    selectors=list(POLICIES),reference='fixed:g174',budget_per_selector=25,tie_rule='preserve reference if optimum, otherwise lexicographic candidate ID',
    retired_candidate='Raw equiprobable readout-wait v1 stays STOPPED; no new readout cost or calibration here.',
    geometry_cost='Actual connected time-pipe block volume, common block-z duration, plain data storage cubes, static common sites*TICK; profile-specific logical protected idle separately retained and not ranked across lowerings.',
    noise='Unchanged d3, p0.001 TQEC uniform-depolarizing physical artifacts',decoder='ordinary uncorrelated PyMatching MWPM/decomposed DEM construction only',
    timing='31 isolated selector repetitions after 3 warmups on common cached features, fixed policy order rotated. Pool/resource normalization/DEM/exact verification separate. Equal 25 row costs are not equal router calls/CPU.',
    held_out_labels='sealed',sampling_permission=False,stopping_rule='No samples; fail rather than remove any unqualified, out-of-device, basis-changing or missing candidate')


def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n')
def load(p):return json.loads((ROOT/p).read_text())


def descriptors():
    rows=[]
    pool={x['candidate_id']:x for x in load('results/grover_competition_2026-11-17/candidate_pool.json')}
    for group,result,archive in [('fixed','grover_competition_2026-11-17','grover_competition_2026-11-17'),('mitm','hamada_path_control_2026-11-23','hamada_path_control_2026-11-23')]:
        for r in load('results/'+result+'/physical_index.json'):
            base=r.get('base_candidate_id',r['candidate_id']);cert='results/'+result+'/certificates/'+r['candidate_id']+'.json'
            rows.append(dict(candidate_id=group+':'+base,group=group,certificate_path=cert,archive='archives/'+archive+'.zip',
                archive_prefix='results/'+result+'/circuits/' if group=='fixed' else 'circuits/',record=load(cert),base_plan=pool[base]['plan']))
    cert='results/hamada_projection_2026-11-24/certificates/projection_00.json'
    rows.append(dict(candidate_id='projection:00',group='projection',certificate_path=cert,
        archive='archives/hamada_projection_2026-11-24.zip',archive_prefix='circuits/',record=load(cert)))
    return rows


def raw(desc,h,suffix):
    with zipfile.ZipFile(ROOT/desc['archive']) as z: data=z.read(desc['archive_prefix']+h+suffix)
    if sha(data)!=h:raise ValueError('Frozen artifact hash differs')
    return data


def geometry(program,desc):
    meta=desc['record']['backend_meta']
    if desc['group']=='fixed':return graph_program(program,desc['base_plan'])
    if desc['group']=='mitm':return routed_graph(program,meta['routed_plan'])
    return projection_graph(program,meta['projection_plan'])


def proof_metadata(meta,gen=None):
    m=deepcopy(meta)
    if gen:
        if 'backend_meta' in gen:m=deepcopy(gen['backend_meta'])
        else:
            m['input_bases']=gen['input_bases'];m['output_bases']=gen['output_bases']
            # Existing exact signed relations determine the same physical flows;
            # strip the original virtual-frame sign, checked independently below.
            m['external_flows']=[r['input'][1:].replace('_','I')+r['output'][1:].replace('_','I') for r in gen['validation']['logical_relations']]
    return {k:m[k] for k in ['logical_qubits','distance','logical_block_xy','input_bases','output_bases','frame_x','frame_z','external_flows']}


def run(output):
    if output.exists():raise FileExistsError('Use fresh output; preserve frozen evidence')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
    _,program=source_program();ds=descriptors()
    if len(ds)!=25:raise ValueError('Do not prune the complete declared physical pool')
    output.mkdir(parents=True);(output/'circuits').mkdir();(output/'certificates').mkdir();save(output/'protocol.json',PROTOCOL)
    began=time.perf_counter();originals=[stim.Circuit(raw(d,d['record']['ideal_sha256'],'.stim').decode()) for d in ds];sites=catalogue(originals)
    prior_device=load('results/grover_competition_2026-11-17/resource_certificate.json')['physical_site_catalogue']
    initial=set(map(tuple,prior_device));device_id=digest(sites)
    save(output/'device.json',dict(physical_site_catalogue=sites,available_physical_sites=len(sites),sha256=device_id,
        prior_catalogue_sites=len(initial),prior_catalogue_sha256=digest(prior_device),
        interpretation='Exact experiment-wide coordinate union. Not a measured real-device bitmap; no hardware-cap efficacy claim.'))
    input_seconds=time.perf_counter()-began;rows=[];timings=[]
    for desc,ideal in zip(ds,originals):
        r=desc['record'];meta=r['backend_meta']
        if meta['external_flows']!=READOUT or r['source_sha256']!=program['source_sha256']:raise ValueError('Original source/complete basis mismatch')
        began=time.perf_counter();g,_,gm=geometry(program,desc);features=physical_memory_features(g,gm);feature_seconds=time.perf_counter()-began
        coords=set(map(tuple,ideal.get_final_qubit_coordinates().values()));outside=sorted(coords-initial)
        proof=[];artifacts={};normalize_seconds=dem_seconds=exact_seconds=decoder_seconds=0.0
        for kind in ('ideal','noisy'):
            old=ideal if kind=='ideal' else stim.Circuit(raw(desc,r['noisy_sha256'],'.stim').decode())
            began=time.perf_counter();new,mapping=remap(old,sites);normalize_seconds+=time.perf_counter()-began
            data=str(new).encode();h=sha(data);(output/'circuits'/(h+'.stim')).write_bytes(data);artifacts[kind+'_sha256']=h
            began=time.perf_counter();dem=new.detector_error_model(decompose_errors=True);dem_seconds+=time.perf_counter()-began
            expected=old.detector_error_model(decompose_errors=True) if kind=='ideal' else stim.DetectorErrorModel(raw(desc,r['dem_sha256'],'.dem').decode())
            if str(dem)!=str(expected):raise AssertionError('Qubit normalization changed the complete DEM')
            if kind=='ideal':
                began=time.perf_counter();v=check_exact(new,proof_metadata(meta),program,True);exact_seconds+=time.perf_counter()-began;proof.append(dict(kind='complete_main',metadata=proof_metadata(meta),validation=v))
            else:
                dem_raw=str(dem).encode();dh=sha(dem_raw);(output/'circuits'/(dh+'.dem')).write_bytes(dem_raw);artifacts['dem_sha256']=dh
                began=time.perf_counter();pymatching.Matching.from_detector_error_model(dem);decoder_seconds+=time.perf_counter()-began
        for gen in r['generators']:
            original=stim.Circuit(raw(desc,gen['ideal_sha256'],'.stim').decode())
            began=time.perf_counter();new,_=remap(original,sites);normalize_seconds+=time.perf_counter()-began
            began=time.perf_counter();m=proof_metadata(meta,gen);v=check_exact(new,m,program);exact_seconds+=time.perf_counter()-began
            data=str(new).encode();h=sha(data);(output/'circuits'/(h+'.stim')).write_bytes(data)
            proof.append(dict(kind=gen.get('input_generator',gen.get('generator')),original_ideal_sha256=gen['ideal_sha256'],ideal_sha256=h,metadata=m,validation=v))
        if len(proof)!=5 or not r['validation']['exact'] or r.get('shortest_graphlike_error',r.get('graphlike_distance'))!=3:raise ValueError('Full source qualification incomplete')
        features.update(stim_ticks=ideal.num_ticks,qec_rounds=None,static_site_ticks=len(sites)*ideal.num_ticks,
                        active_physical_sites=len(coords),device_physical_sites=len(sites))
        legacy=r.get('features',{});protected=legacy.get('total_protected_idle_block_z',14 if desc['group']=='projection' else None)
        row=dict(candidate_id=desc['candidate_id'],lowering_id=meta['profile_id'],device_sha256=device_id,outside_device_sites=0,
            required_sites_outside_prior_310=len(outside),outside_prior_coordinates=outside,
            qualified_complete_output=True,external_flows=READOUT,features=features,
            profile_specific_protected_idle_block_z=protected,
            profile_routing_steps=legacy.get('cx_routing_steps'),profile_h_layers=legacy.get('logical_h_layers'),profile_physical_layers=legacy.get('physical_layers'),
            source_sha256=program['source_sha256'],plan_sha256=r['plan_sha256'],original_artifacts={k:r[k] for k in ['ideal_sha256','noisy_sha256','dem_sha256']},
            normalized_artifacts=artifacts,original_certificate=desc['certificate_path'],original_certificate_sha256=sha((ROOT/desc['certificate_path']).read_bytes()),
            full_original_readout_order=[1,0],graphlike_distance=3,shots=0,counts=None,confidence_interval=None)
        save(output/'certificates'/(desc['candidate_id'].replace(':','_')+'.json'),dict(candidate=row,source_complete_proofs=proof,qubit_mapping={str(q):i for q,i in mapping.items()}))
        rows.append(row);timings.append(dict(candidate_id=row['candidate_id'],geometry_features_seconds=feature_seconds,
            coordinate_normalization_seconds=normalize_seconds,dem_verification_seconds=dem_seconds,exact_verification_seconds=exact_seconds,
            decoder_construction_seconds=decoder_seconds,routing_seconds=None,calibration_seconds=None,physical_compile_seconds=None,monte_carlo_seconds=None,decode_seconds=None))
        print(row['candidate_id'],'full output+4 generators+unchanged DEM passed',len(coords),'active sites;',len(outside),'outside prior catalogue; 0 shots',flush=True)
    save(output/'candidate_pool.json',rows)
    selections=[select(rows,p,PROTOCOL['reference'],25) for p in POLICIES]
    # All resource normalization/validation is complete before isolated selector timing.
    order=list(POLICIES)
    for _ in range(3):
        for p in order:select(rows,p,PROTOCOL['reference'],25)
    timing_samples={p:[] for p in order}
    for i in range(31):
        for p in order[i%len(order):]+order[:i%len(order)]:
            began=time.perf_counter();select(rows,p,PROTOCOL['reference'],25);timing_samples[p].append(time.perf_counter()-began)
    save(output/'selections.json',selections)
    save(output/'timing.json',dict(input_and_catalogue_seconds=input_seconds,candidate_stage_timings=timings,
        isolated_selector_samples_seconds=timing_samples,isolated_selector_median_seconds={p:statistics.median(v) for p,v in timing_samples.items()},
        timing_scope='Offline cache/table selection only. Common 25 feature rows and 25 key evaluations each, not matched route-search CPU. No compilation/MC included.'))
    inputs=[d['certificate_path'] for d in ds]+sorted({d['archive'] for d in ds})
    inputs+=['results/grover_competition_2026-11-17/candidate_pool.json','results/grover_competition_2026-11-17/resource_certificate.json']
    save(output/'environment.json',dict(python=platform.python_version(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_files_sha256={p:sha((ROOT/p).read_bytes()) for p in CODE},input_files_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        packages={p:md.version(p) for p in ['tqec','stim','numpy','pymatching']},tqec_direct_url=json.loads(md.distribution('tqec').read_text('direct_url.json'))))
    summary=dict(protocol_id=PROTOCOL['id'],qualified_physical_pool=25,unique_physical_noisy_circuits=25,common_available_physical_sites=len(sites),
        retained_abstract_gate_plans=175,abstract_plan_qualification_note='Only the previously certified 12 shortest fixed plans, their 12 MITM variants and one asynchronous reference are in this physical selector. Deeper abstract plans remain pending, not deleted or declared inferior in decoded error.',
        original_catalogue_310=dict(feasible=sum(not r['required_sites_outside_prior_310'] for r in rows),infeasible=sum(bool(r['required_sites_outside_prior_310']) for r in rows),selection='Not run on silently reduced pool'),
        full_output_exact_checks=25,generator_exact_checks=100,unchanged_main_ideal_and_noisy_dem_checks=50,
        normalized_representations_are_new_physical_compilations=False,new_physical_compilations=0,new_research_shots=0,sampler_calls=0,counts=None,confidence_interval=None,
        retired_readout_v1='STOPPED',new_readout_cost_revision=False,held_out_labels='sealed',sampling_permission=False,mu=0,
        gates_remaining=['O3LS original implementation/common supported physical lowering','online original methods vs same search budget','readout-sensitive revision and development pilot/calibration','complete evaluation freeze before held-out'],
        decision='Shared device/readout/features/offline-budget contract achieved for declared 25 physical candidates. Actual selectors disagree on time vs volume. No decoded-circuit improvement or original-method completion claim.')
    save(output/'summary.json',summary);return summary


def check(output):
    _,program=source_program();env=load(str(output.relative_to(ROOT)/'environment.json')) if output.is_relative_to(ROOT) else json.loads((output/'environment.json').read_text())
    for group in ['source_files_sha256','input_files_sha256']:
        for p,h in env[group].items():
            if sha((ROOT/p).read_bytes())!=h:raise AssertionError('Frozen source/input differs: '+p)
    rows=json.loads((output/'candidate_pool.json').read_text());ds=descriptors()
    if {r['candidate_id'] for r in rows}!={d['candidate_id'] for d in ds} or len(rows)!=25:raise AssertionError('Physical candidate removed')
    if json.loads((output/'selections.json').read_text())!=[select(rows,p,PROTOCOL['reference'],25) for p in POLICIES]:raise AssertionError('Selector replay differs')
    if json.loads((output/'protocol.json').read_text())!=PROTOCOL:raise AssertionError('Protocol differs')
    sites=json.loads((output/'device.json').read_text())['physical_site_catalogue']
    with zipfile.ZipFile(ARCHIVE) as z:
        for r in rows:
            d=next(d for d in ds if d['candidate_id']==r['candidate_id']);cert=json.loads((output/'certificates'/(r['candidate_id'].replace(':','_')+'.json')).read_text())
            g,_,m=geometry(program,d)
            measured=physical_memory_features(g,m)
            if any(r['features'][k]!=v for k,v in measured.items()):raise AssertionError('Common geometry feature differs')
            for kind,suffix in [('ideal','.stim'),('noisy','.stim'),('dem','.dem')]:
                h=r['normalized_artifacts'][kind+'_sha256'];data=z.read('circuits/'+h+suffix)
                if sha(data)!=h:raise AssertionError('Normalized artifact differs')
                if kind!='dem':
                    orig=stim.Circuit(raw(d,r['original_artifacts'][kind+'_sha256'],'.stim').decode());expected,_=remap(orig,sites)
                    if str(expected).encode()!=data:raise AssertionError('Relabeling changed a gate/annotation')
                    if sha(str(expected.detector_error_model(decompose_errors=True)).encode())!= (sha(str(orig.detector_error_model(decompose_errors=True)).encode())):raise AssertionError('Complete DEM differs')
            for proof in cert['source_complete_proofs']:
                h=r['normalized_artifacts']['ideal_sha256'] if proof['kind']=='complete_main' else proof['ideal_sha256'];data=z.read('circuits/'+h+'.stim')
                if sha(data)!=h:raise AssertionError('Generator artifact differs')
                check_exact(stim.Circuit(data.decode()),proof['metadata'],program,proof['kind']=='complete_main')
    print('PASS: all 25 complete physical candidates, same 378-site device and complete readout, 100 generators, unchanged DEMs and all equal-budget selectors; 0 new shots')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=DEFAULT);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    if a.check:check(a.output)
    else:print(json.dumps(run(a.output),indent=2))
