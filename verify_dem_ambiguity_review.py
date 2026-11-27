"""Replay archived 77-DEM review without unpacked raw patterns or new shots."""
import argparse
import json
from pathlib import Path
import time
import zipfile

import stim

from review_dem_ambiguity import ROOT, DEFAULT, read, sha, scan, save


def verify(result,decode=True):
    env=read(result/'environment.json');manifest=read(result/'snapshot_manifest.json')
    if sha((ROOT/'review_dem_ambiguity.py').read_bytes())!=env['code_sha256']:
        raise ValueError('Executed reviewer source changed')
    data=(ROOT/manifest['archive']).read_bytes()
    if sha(data)!=manifest['sha256']:raise ValueError('Raw-review archive hash differs')
    rows=read(result/'records.json');by_id={r['candidate_id']:r for r in rows}
    pool=read(ROOT/'results/grover_depth_frontier_2026-11-26/candidate_pool.json')
    if len(rows)!=77 or len(by_id)!=77:raise ValueError('Incomplete77 pool')
    if {r['candidate_id'] for r in pool}!=set(by_id):raise ValueError('Candidate set differs')
    with zipfile.ZipFile(ROOT/manifest['archive']) as z:
        hashes=json.loads(z.read('sha256.json'))
        if hashes!=manifest['files_sha256'] or set(z.namelist())!=set(hashes)|{'sha256.json'}:
            raise ValueError('Raw archive inventory differs')
        raw_count=0
        for name,h in hashes.items():
            b=z.read(name)
            if sha(b)!=h:raise ValueError('Raw effect/prediction hash differs')
            cid=Path(name).stem.replace('_',':',1)
            if cid not in by_id or by_id[cid]['raw_triangles_sha256']!=h:raise ValueError('Raw triangle-to-candidate mapping differs')
            count=len(b.splitlines())
            if count!=by_id[cid]['ac_vs_b_pairs']:raise ValueError('Missing raw triangle')
            raw_count+=count
    old_ids={r['candidate_id'] for r in read(ROOT/'results/common_physical_pool_2026-11-25/candidate_pool.json')}
    archives={k:ROOT/('archives/'+v+'.zip') for k,v in dict(old='common_physical_pool_2026-11-25',frontier='grover_depth_frontier_2026-11-26').items()}
    for k,path in archives.items():
        if sha(path.read_bytes())!=env['archive_sha256'][k]:raise ValueError('Original frozen source archive changed')
    began=time.perf_counter();decoded=0
    for source in pool:
        cid=source['candidate_id'];r=by_id[cid];h=source['normalized_artifacts']['dem_sha256']
        if r['dem_sha256']!=h or r['plan_sha256']!=source['plan_sha256']:raise ValueError('Actual source/plan mapping differs')
        with zipfile.ZipFile(archives['old' if cid in old_ids else 'frontier']) as z:b=z.read('circuits/'+h+'.dem')
        if sha(b)!=h:raise ValueError('Original DEM hash differs')
        if decode:
            actual=scan(stim.DetectorErrorModel(b.decode()))
            for key,value in actual.items():
                if key in ('timing','raw_triangles_sha256'):continue
                if r[key]!=value:raise ValueError('Actual full MWPM replay differs: '+cid+' '+key)
            decoded+=1
    answer=dict(status='PASS',raw_assets=len(manifest['files_sha256']),archived_full_effect_triangles=raw_count,
        complete_dem_decoders_replayed=decoded,original_archives_unchanged=True,
        seconds=time.perf_counter()-began,new_shots=0,new_physical_compilations=0,
        note='Every raw archive byte and all77 actual source mappings; full deterministic MWPM/statistics replay when requested. No unpacked raw directory dependency.')
    print(json.dumps(answer,indent=2));return answer


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--result',type=Path,default=DEFAULT)
    p.add_argument('--hashes-only',action='store_true');a=p.parse_args();verify(a.result,not a.hashes_only)
