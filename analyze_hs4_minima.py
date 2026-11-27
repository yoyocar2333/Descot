"""Preserve all13 old full hs4 circuits alongside the completed initial minimum batch."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import zipfile
import stim

from run_hs4_minimum_frontier import ROOT,DEFAULT,reference
from public_clifford import load_program,graph_program
from public_candidate_pool import digest,canonical
from common_physical_pool import physical_memory_features,select,POLICIES


def analyze(result):
    load=lambda p:json.loads(p.read_text())
    rows=load(result/'physical_index.json');summary=load(result/'summary.json')
    pool=load(result/'candidate_pool.json');program=load(result/'program.json')
    if len(rows)!=summary['qualified_minimum_plans'] or {r['candidate_id'] for r in rows}!={r['candidate_id'] for r in pool[:len(rows)]}:
        raise ValueError('Every initial-batch candidate must pass; no survivor selection')
    if len({r['noisy_sha256'] for r in rows})!=len(rows):raise ValueError('Minimum physical candidates must be distinct')
    cert,_,base=reference();device=base.get_final_qubit_coordinates();ref=summary['reference_id']
    old=load(ROOT/'results/public_candidates_2026-11-02/development_summary.json')['records']
    plans={r['candidate_id']:r for r in load(ROOT/'results/public_candidates_2026-11-02/development_pool.json')}
    aliases=[];raw=[]
    with zipfile.ZipFile(ROOT/'archives/public_candidates_2026-11-02.zip') as z:
        for r in old:
            pid=r['candidate_id'];h=r['noisy_circuit_sha256'];same=[x for x in rows if x['noisy_sha256']==h]
            if same:
                aliases.append(dict(old_id=pid,current_id=same[0]['candidate_id'],noisy_sha256=h));continue
            # Old files include a final newline. Keep both exact asset-byte and
            # canonical Stim hashes, instead of changing frozen old records.
            objs={};art={}
            for k,ext,post in [('ideal','.stim','_ideal'),('noisy','.stim',''),('dem','.dem','')]:
                name='results/public_candidates_2026-11-02/samples/sample_'+h+post+ext
                data=z.read(name);o=stim.DetectorErrorModel(data.decode()) if k=='dem' else stim.Circuit(data.decode())
                expected=r['dem_sha256'] if k=='dem' else r[k+'_circuit_sha256']
                assert hashlib.sha256(str(o).encode()).hexdigest()==expected
                art[k+'_sha256']=expected;objs[k]=o
                raw.append(dict(old_id=pid,archive='archives/public_candidates_2026-11-02.zip',member=name,
                    bytes_sha256=hashlib.sha256(data).hexdigest(),canonical_stim_sha256=expected))
            if objs['ideal'].get_final_qubit_coordinates()!=device:raise ValueError('Old layout differs')
            graph,_,gm=graph_program(program,plans[pid]['plan']);f=physical_memory_features(graph,gm)
            f.update(stim_ticks=objs['ideal'].num_ticks,qec_rounds=None,static_site_ticks=len(device)*objs['ideal'].num_ticks,
                active_physical_sites=objs['ideal'].num_qubits,device_physical_sites=len(device))
            rows.append(dict(candidate_id='old:'+pid,source_sha256=program['source_sha256'],plan_sha256=digest(plans[pid]['plan']),
                **art,features=f,profile_features=r['features'],qualified_complete_output=True,outside_device_sites=0,
                external_flows=cert['backend_meta']['external_flows'],device_sha256=digest(device),
                qualification='Frozen original complete physical hs4 certificate and exact archived hashes; no recompile or resampling.',
                original_shots=r['shots'],new_shots=0))
    if len(rows)!=19 or aliases or {r['candidate_id'] for r in rows if r['candidate_id'].startswith('old:')}!={'old:p%02d'%i for i in range(13)}:
        raise ValueError('All original13 circuits must survive with only exact p12 duplicate coalesced')
    selections=[select(rows,k,ref,len(rows)) for k in POLICIES]
    fields=['template_block_z','total_lifetime_block_z','plain_data_storage_cubes','static_site_ticks']
    minima=[r for r in rows if not r['candidate_id'].startswith('old:')]
    signatures=lambda rows,k:len({canonical(r['features'][k]) for r in rows})
    a=dict(total_complete_physical_pool=len(rows),logical_minimum_frontier=144,qualified_minima=6,pending_minima=138,complete_frontier=False,all_old13_preserved=True,exact_aliases=aliases,
        full_pool_sha256=digest(rows),selections=selections,
        minimum_geometry_distinct={k:signatures(minima,k) for k in fields},
        minimum_geometry_values={k:sorted({r['features'][k] for r in minima}) for k in fields},
        minimum_profile_wait_patterns=len({canonical(r['profile_features']['protected_idle_intervals_block_z']) for r in minima}),
        minimum_total_idle_values=sorted({r['profile_features']['total_protected_idle_block_z'] for r in minima}),
        old_raw_assets=raw,new_shots=0,counts=None,confidence_interval=None,
        interpretation='The former H-first unique minimum is one of144 minima in the larger declared homogeneous pool. No decoded efficacy or novelty inferred. Four resource baselines share the19 currently qualified full circuits; all original13 remain. This is a partial qualification checkpoint, not an all144-minima comparison. Retired raw cost not rerun.')
    (result/'complete_physical_pool.json').write_text(json.dumps(rows,indent=2)+'\n')
    (result/'analysis.json').write_text(json.dumps(a,indent=2)+'\n')
    return a

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--result',type=Path,default=DEFAULT);a=p.parse_args();r=analyze(a.result)
    print(json.dumps({k:v for k,v in r.items() if k not in ('old_raw_assets','selections')},indent=2))
