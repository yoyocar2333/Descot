"""Solid compressed, split, hash-verified snapshot for complete public circuits."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile

from run_hs4_minimum_frontier import ROOT,DEFAULT,CODE

PREFIX='hs4_minimum_frontier_2026-11-27.tar.xz'
PART_BYTES=2*1024*1024

def sha(b):return hashlib.sha256(b).hexdigest()

def pack(result):
    if (result/'snapshot_manifest.json').exists():raise FileExistsError('Frozen snapshot exists')
    summary=json.loads((result/'summary.json').read_text())
    if summary['qualified_minimum_plans']!=6 or not (result/'analysis.json').exists():raise ValueError('Completed initial batch and explicit partial coverage required')
    env=json.loads((result/'environment.json').read_text())
    for p,h in env['source_files_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h:raise ValueError('Frozen executed source changed: '+p)
    assets={}
    for p in sorted((result/'circuits').iterdir()):
        if p.suffix not in ('.stim','.dem') or sha(p.read_bytes())!=p.stem:raise ValueError('Raw hash-addressed asset differs')
        assets['circuits/'+p.name]=p
    for p in sorted((result/'certificates').glob('*.json')):assets['certificates/'+p.name]=p
    for p in sorted(result.glob('*.json')):
        if p.name not in ('snapshot_manifest.json','verification.json'):assets['records/'+p.name]=p
    paths=CODE+['analyze_hs4_minima.py','pack_hs4_minima.py','checkpoint_hs4_minima.py','tests/test_hs4_minimum_frontier.py','resume_hs4_minima.py']
    for p in paths:assets['source/'+p]=ROOT/p
    for p in ['benchmarks/public_2026-11-02/manifest.json','benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm',
              'benchmarks/public_2026-11-02/qasmbench/LICENSE','benchmarks/public_2026-11-02/qasmbench/NOTICE',
              'benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json']:
        assets['inputs/'+p]=ROOT/p
    hashes={n:sha(p.read_bytes()) for n,p in assets.items()}
    def add(t,n,b):
        info=tarfile.TarInfo(n);info.size=len(b);info.mode=0o644;info.mtime=1795737600
        t.addfile(info,io.BytesIO(b))
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/PREFIX
        with tarfile.open(path,'w:xz',preset=6) as t:
            for n,p in assets.items():add(t,n,p.read_bytes())
            add(t,'sha256.json',(json.dumps(hashes,sort_keys=True,indent=2)+'\n').encode())
        b=path.read_bytes();parts=[]
        for i,start in enumerate(range(0,len(b),PART_BYTES)):
            name='archives/'+PREFIX+f'.part-{i:03}';data=b[start:start+PART_BYTES]
            p=ROOT/name
            if p.exists():raise FileExistsError('Do not overwrite part')
            p.write_bytes(data);parts.append(dict(path=name,bytes=len(data),sha256=sha(data)))
    record=dict(archive_format='Concatenate numbered parts in order to obtain a standard tar.xz; Python stdlib replay below automates it.',
        archive_sha256=sha(b),archive_bytes=len(b),parts=parts,assets=len(hashes),files_sha256=hashes,
        scope='Complete raw ideal/noisy/DEM and all8 generator proofs for all6 completed minima; remaining138 not qualified, full source/protocol/models and checks. Existing13 raw circuits retain their original frozen archive. No dependency wheel bundle or evaluation freeze;0shots.')
    (result/'snapshot_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='files_sha256'},indent=2))


def check(result,exact_reference=False):
    m=json.loads((result/'snapshot_manifest.json').read_text());env=json.loads((result/'environment.json').read_text())
    for p,h in env['source_files_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h:raise ValueError('Executed source changed')
    seen={};certs=[];main_bytes=None
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(temp)/PREFIX
        with archive.open('wb') as f:
            for part in m['parts']:
                b=(ROOT/part['path']).read_bytes()
                if sha(b)!=part['sha256'] or len(b)!=part['bytes']:raise ValueError('Part hash differs')
                f.write(b)
        if sha(archive.read_bytes())!=m['archive_sha256']:raise ValueError('Whole archive hash differs')
        with tarfile.open(archive,'r|xz') as t:
            for item in t:
                if not item.isfile():raise ValueError('Only flat regular archive assets accepted')
                b=t.extractfile(item).read()
                if item.name=='sha256.json':
                    if json.loads(b)!=m['files_sha256']:raise ValueError('Internal manifest differs')
                    continue
                if sha(b)!=m['files_sha256'].get(item.name):raise ValueError('Asset differs: '+item.name)
                seen[item.name]=sha(b)
                if item.name.startswith('certificates/'):certs.append(json.loads(b))
        if seen!=m['files_sha256']:raise ValueError('Incomplete snapshot')
    pool=json.loads((result/'candidate_pool.json').read_text());byid={r['candidate_id']:r for r in pool}
    if len(certs)!=6 or {c['candidate_id'] for c in certs}!={r['candidate_id'] for r in pool[:6]}:raise ValueError('Entire initial batch required, incomplete frontier stays explicit')
    from public_clifford import logical_circuit,validate_plan
    import stim
    program=json.loads((result/'program.json').read_text());u=stim.Tableau.from_circuit(logical_circuit(program,False))
    count=0
    for c in certs:
        row=byid[c['candidate_id']];validate_plan(program,row['plan'])
        if c['plan_sha256']!=row['plan_sha256'] or c['source_sha256']!=program['source_sha256']:raise ValueError('Source/plan differs')
        if c['validation']['full_z_readout_rank']!=4 or len(c['validation']['signed_inputs'])!=16 or len(c['validation']['final_faults'])!=4:raise ValueError('Complete main proof missing')
        if sorted(o['id'] for o in c['backend_meta']['instruction_trace'])!=list(range(32)):raise ValueError('Source instruction omitted')
        if len(c['generators'])!=8 or len(c['compile_requests'])!=9:raise ValueError('Generator/request target omitted')
        for g in c['generators']:
            if len(g['validation']['signed_inputs'])!=16:raise ValueError('Signed generator proof incomplete')
            axis=g['input_generator'][0];q=int(g['input_generator'][1:]);out=u.x_output(q) if axis=='X' else u.z_output(q)
            target='I'*q+axis+'I'*(3-q)+str(out)[1:].replace('_','I')
            if g['target_flow']!=target:raise ValueError('Source generator target changed')
            if 'circuits/'+g['ideal_sha256']+'.stim' not in seen:raise ValueError('Missing full generator circuit')
        for k,ext in [('ideal','.stim'),('noisy','.stim'),('dem','.dem')]:
            if 'circuits/'+c[k+'_sha256']+ext not in seen:raise ValueError('Missing full main circuit')
        count+=1+len(c['generators'])
    r=dict(status='PASS',archive_assets=len(seen),complete_minimum_certificates=len(certs),exact_validation_targets=count,
        source_signatures_generators_full=True,new_shots=0,
        replay_scope='Every raw asset/part hash, all full32-instruction plans, all6 rank4 signed-input/final-fault certificates, all48 generator target/source/16-sign proofs and their complete circuits. Stored exact checks verified; no recompile/resampling or new performance claim.')
    print(json.dumps(r,indent=2));return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--result',type=Path,default=DEFAULT);p.add_argument('--check',action='store_true');a=p.parse_args()
    check(a.result) if a.check else pack(a.result)
