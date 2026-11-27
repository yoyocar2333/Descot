"""Independent zero-shot review of the supplied 77-Grover DEM scan.

Use whole independent DEM instructions, XOR across ^ components, and the
unchanged full ordinary MWPM. Pair incidence is NOT a circuit failure rate.
No physical compilation, sampler, fit, model revision or pilot selection.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.metadata as md
import json
import math
from pathlib import Path
import platform
import subprocess
import time
import zipfile

import numpy as np
import pymatching
import stim

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'results/dem_ambiguity_review_2026-11-27'


def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')


def parse_effects(dem):
    """One Bernoulli per whole error instruction, never per ^ component."""
    effects=defaultdict(list);mass=0.;separated=separators=mechanisms=0
    for index,inst in enumerate(dem.flattened()):
        if inst.type!='error':continue
        d=set();l=0;count=0;p=inst.args_copy()[0]
        for target in inst.targets_copy():
            if target.is_relative_detector_id():d.symmetric_difference_update({target.val})
            elif target.is_logical_observable_id():l^=1<<target.val
            elif target.is_separator():count+=1
            else:raise ValueError('Unknown DEM error target')
        effects[(tuple(sorted(d)),l)].append((index,p))
        mass+=p;separated+=count>0;separators+=count;mechanisms+=1
    return effects,dict(error_instruction_count=mechanisms,total_error_mass=mass,
        separated_error_instructions=separated,separator_tokens=separators)


def triangles(effects):
    boundary=defaultdict(list);result=[]
    for (d,l),items in effects.items():
        if len(d)==1:boundary[d[0]].append((l,items))
    for (d,bl),b in effects.items():
        if len(d)!=2:continue
        a,c=d
        for al,aa in boundary.get(a,[]):
            for cl,cc in boundary.get(c,[]):
                if al^cl==bl:continue
                result.append(dict(a=a,c=c,al=al,bl=bl,cl=cl,A=aa,B=b,C=cc))
    return result


def patterns(t):
    a,c=t['a'],t['c'];al,bl,cl=t['al'],t['bl'],t['cl']
    masses={k:sum(p for _,p in t[k]) for k in 'ABC'}
    return dict(A=((a,),al,masses['A']),B=((a,c),bl,masses['B']),C=((c,),cl,masses['C']),
        AC=((a,c),al^cl,masses['A']*masses['C']),
        AB=((c,),al^bl,masses['A']*masses['B']),
        BC=((a,),bl^cl,masses['B']*masses['C']))


def scan(dem,raw_path=None):
    began=time.perf_counter();effects,stats=parse_effects(dem);ts=triangles(effects)
    by_d=defaultdict(set)
    for d,l in effects:by_d[d].add(l)
    stats['direct_ambiguous_symptoms']=sum(len(v)>1 for v in by_d.values())
    stats['ac_vs_b_pairs']=len(ts)
    stats['ac_pair_incidence']=sum(patterns(t)['AC'][2] for t in ts)
    parse_seconds=time.perf_counter()-began
    began=time.perf_counter();matching=pymatching.Matching.from_detector_error_model(dem)
    build_seconds=time.perf_counter()-began
    symptoms=sorted({d for t in ts for d,_,_ in patterns(t).values()})
    predictions={};began=time.perf_counter()
    for offset in range(0,len(symptoms),2048):
        rows=symptoms[offset:offset+2048];a=np.zeros((len(rows),dem.num_detectors),dtype=np.uint8)
        for i,d in enumerate(rows):a[i,list(d)]=1
        pred=matching.decode_batch(a)
        for d,bits in zip(rows,pred,strict=True):predictions[d]=sum(int(v)<<i for i,v in enumerate(bits))
    decode_seconds=time.perf_counter()-began
    grouped={k:dict(effect_patterns=0,decoded_any_error_patterns=0,pair_incidence=0.,decoded_failure_incidence=0.) for k in ['AC','AB','BC']}
    singles=Counter();raw=[]
    for t in ts:
        cases={}
        for kind,(d,l,mass) in patterns(t).items():
            prediction=predictions[d];failure=prediction!=l
            cases[kind]=dict(detector_ids=d,actual_logical_mask=l,decoder_prediction_mask=prediction,decoded_any_error=failure)
            if kind in grouped:
                g=grouped[kind];g['effect_patterns']+=1;g['decoded_any_error_patterns']+=failure
                g['pair_incidence']+=mass;g['decoded_failure_incidence']+=mass*failure
            else:singles[kind+'_failed']+=failure
        raw.append(dict(**t,cases=cases))
    raw_hash=None
    if raw_path is not None:
        data=''.join(json.dumps(x,separators=(',',':'))+'\n' for x in raw).encode();raw_path.write_bytes(data);raw_hash=sha(data)
    stats.update(pair_families=grouped,single_pattern_failures=dict(singles),
        triangle_family_pair_incidence=sum(x['pair_incidence'] for x in grouped.values()),
        raw_triangles_sha256=raw_hash,unique_decoded_syndromes=len(symptoms),
        log_probability_no_dem_mechanisms=sum(math.log1p(-p) for items in effects.values() for _,p in items),
        timing=dict(parse_and_topology_seconds=parse_seconds,matching_construction_seconds=build_seconds,deterministic_decode_seconds=decode_seconds),
        warning='Incidence is an expected count of selected co-occurring whole DEM-instruction pairs, not a union probability or full decoded-circuit LER. AC/AB/BC still omit other malignant pairs and higher orders.')
    return stats


def run(output,reference=None):
    if output.exists():raise FileExistsError('Fresh result directory required')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
    pool=read(ROOT/'results/grover_depth_frontier_2026-11-26/candidate_pool.json')
    frontier=read(ROOT/'results/grover_depth_frontier_2026-11-26/physical_index.json');by_front={r['candidate_id']:r for r in frontier}
    supplied=read(reference) if reference else None
    claims={} if supplied is None else {Path(r['dem_asset']).stem:r for r in supplied['records']}
    if len(pool)!=77 or supplied and (len(claims)!=77 or len(supplied['records'])!=77):raise ValueError('Whole77 pool required')
    archives={k:ROOT/('archives/'+v+'.zip') for k,v in dict(old='common_physical_pool_2026-11-25',frontier='grover_depth_frontier_2026-11-26').items()}
    archive_hashes={k:sha(p.read_bytes()) for k,p in archives.items()}
    output.mkdir(parents=True);(output/'raw').mkdir()
    save(output/'protocol.json',dict(id='independent_supplied_dem_scan_review_v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        role='Review only; all Grover development. No new hypothesis/model revision/calibration/pilot selection or performance claim.',
        all_candidates=77,whole_dem_semantics='Independent whole error instructions; XOR all D/L across separators. Duplicate whole effects retain independent parent IDs/probabilities.',
        counted_metric='Unique full-effect triangles D(A)={a},D(C)={c},D(B)={a,c},L(A)^L(C)!=L(B). AC incidence=sum(p_A*p_C) over matching whole parents; not a probability.',
        decoder='Unchanged full2-output ordinary uncorrelated PyMatching MWPM from each frozen complete DEM. Deterministic patterns, not samples.',
        additional_checks='Decode AC,AB,BC and A,B,C for every triangle; join actual certificate idle/recurrence features. Additional pair families are diagnostics, not a replacement risk score.',
        shots=0,seeds=[],counts=None,confidence_interval=None,physical_compilations=0,mu=0,sampling_permission=False,held_out_labels='sealed',risk_revision=False))
    save(output/'environment.json',dict(python=platform.python_version(),stim=md.version('stim'),pymatching=md.version('pymatching'),numpy=md.version('numpy'),
        code_sha256=sha(Path(__file__).read_bytes()),lock_sha256=sha((ROOT/'requirements-lock.txt').read_bytes()),
        reference_sha256=sha(reference.read_bytes()) if reference else None,
        archive_sha256=archive_hashes,pool_sha256=sha((ROOT/'results/grover_depth_frontier_2026-11-26/candidate_pool.json').read_bytes())))
    rows=[];contingency=defaultdict(Counter);gap_groups=defaultdict(Counter);profile_ids=defaultdict(lambda:defaultdict(list))
    for row in pool:
        cid=row['candidate_id'];h=row['normalized_artifacts']['dem_sha256']
        is_front=cid.startswith('fixed:') and cid.split(':')[1] in by_front
        which='frontier' if is_front else 'old'
        with zipfile.ZipFile(archives[which]) as z:data=z.read('circuits/'+h+'.dem')
        if sha(data)!=h:raise ValueError('Frozen DEM differs')
        dem=stim.DetectorErrorModel(data.decode())
        if dem.num_observables!=2 or row['external_flows']!=['ZIIZ','IZZI']:raise ValueError('Complete original readout basis changed')
        result=scan(dem,output/'raw'/(cid.replace(':','_')+'.jsonl'))
        claim=claims.get(h)
        if supplied and claim is None:raise ValueError('Supplied DEM hash absent')
        mapping=True
        if claim:
            alias=claim['plan_id'];expected='projection:00' if alias=='projection_00' else alias.replace('fixed_','fixed:').replace('mitm_','mitm:') if alias.startswith(('fixed_','mitm_')) else 'fixed:'+alias
            mapping=expected==cid
        differences={}
        for key,field in [('hyper_decomposed_cnt','separated_error_instructions'),('ac_vs_b_pairs','ac_vs_b_pairs'),('ac_vs_b_prob','ac_pair_incidence'),('total_error_mass','total_error_mass'),('direct_ambig_cnt','direct_ambiguous_symptoms')]:
            if claim and not math.isclose(claim[key],result[field],rel_tol=0,abs_tol=5.01e-7 if key=='total_error_mass' else 5.01e-10 if key=='ac_vs_b_prob' else 0):
                differences[key]=dict(supplied=claim[key],actual=result[field])
        record=dict(candidate_id=cid,source_depth_frontier=is_front,dem_sha256=h,source_sha256=row['source_sha256'],plan_sha256=row['plan_sha256'],
            normalized_artifacts=row['normalized_artifacts'],mapping_matches=mapping,reported_differences=differences,
            stim_ticks=row['features']['stim_ticks'],physical_layers=row['profile_physical_layers'],
            data_lifetime_block_z=row['features']['data_lifetime_block_z'],ancilla_lifetime_block_z=row['features']['ancilla_lifetime_block_z'],
            **result)
        if is_front:
            name=cid.split(':')[1];f=by_front[name]['features'];record['protected_idle_intervals_block_z']=f['protected_idle_intervals_block_z'];record['cx_recurrence_separations_block_z']=f['cx_recurrence_separations_block_z']
            profile=str(f['protected_idle_intervals_block_z']);gap=str(f['cx_recurrence_separations_block_z']);count=result['ac_vs_b_pairs']
            contingency[profile][count]+=1;gap_groups[gap][count]+=1;profile_ids[profile][count].append(name)
        rows.append(record);print(cid,len(rows),'of77',result['ac_vs_b_pairs'],round(result['ac_pair_incidence'],9),'mismatches',differences,flush=True)
    save(output/'records.json',rows)
    save(output/'feature_contingency.json',dict(idle_profiles=dict(contingency),cx_recurrence_gaps=dict(gap_groups),same_idle_counterexamples={k:v for k,v in profile_ids.items() if len(v)>1}))
    summary=dict(circuits=77,mapping_mismatches=sum(not r['mapping_matches'] for r in rows),numeric_mismatch_rows=sum(bool(r['reported_differences']) for r in rows),
        frontier_groups=dict(Counter(r['ac_vs_b_pairs'] for r in rows if r['source_depth_frontier'])),
        all_AC_patterns=sum(r['ac_vs_b_pairs'] for r in rows),all_AC_decoded_failure_patterns=sum(r['pair_families']['AC']['decoded_any_error_patterns'] for r in rows),
        same_idle_profiles_crossing_groups=sum(len(v)>1 for v in contingency.values()),
        statement='Adopt verified provenance/topology as a development diagnostic. Reject probability/LER, sole-idle causation, validated-v2 and extreme-only pilot claims. No method or sampling gates bypassed.',
        new_shots=0,counts=None,confidence_interval=None,new_physical_compilations=0,mu=0)
    save(output/'summary.json',summary)
    assets={p.relative_to(output).as_posix():p.read_bytes() for p in (output/'raw').iterdir()}
    target=ROOT/'archives/dem_ambiguity_review_2026-11-27.zip'
    if target.exists():raise FileExistsError('Preserve existing raw snapshot')
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_LZMA) as z:
        for name,b in assets.items():z.writestr(name,b)
        z.writestr('sha256.json',json.dumps({n:sha(b) for n,b in assets.items()},indent=2)+'\n')
    save(output/'snapshot_manifest.json',dict(archive=str(target.relative_to(ROOT)),sha256=sha(target.read_bytes()),bytes=target.stat().st_size,
        files_sha256={n:sha(b) for n,b in assets.items()},scope='Every full-effect triangle, whole parent instruction IDs/probabilities and actual full MWPM predictions for all77 frozen DEMs. Source DEMs remain in original unmodified archives. No shots.'))
    if {k:sha(p.read_bytes()) for k,p in archives.items()}!=archive_hashes:raise ValueError('Original archives changed')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--output',type=Path,default=DEFAULT);p.add_argument('--reference',type=Path);a=p.parse_args();run(a.output,a.reference)
