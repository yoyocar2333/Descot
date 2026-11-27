"""Archive/replay complete public BV circuits, proofs, records and source.

--check verifies every archived byte and full certificate coverage without
requiring unpacked circuits/certificates. --exact additionally reruns all
signed physical proofs and complete ideal/noisy DEM equality; zero shots.
"""
import argparse
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile

from run_bv_public_family import ROOT, DEFAULT, CODE, sha, read, save

PREFIX='public_bv_2026-11-27.tar.xz'
PART_BYTES=2*1024*1024


def pack(result):
    if (result/'snapshot_manifest.json').exists(): raise FileExistsError('Frozen snapshot exists')
    env=read(result/'environment.json')
    for p,h in env['code_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h: raise ValueError('Executed code changed: '+p)
    assets={}
    for directory in ('circuits','certificates','journals'):
        for p in sorted((result/directory).iterdir()): assets[directory+'/'+p.name]=p
    for p in sorted(result.glob('*.json')):
        if p.name not in ('snapshot_manifest.json','verification.json','exact_verification.json'):
            assets['records/'+p.name]=p
    for p in CODE+['pack_bv_public_family.py','analyze_bv_public_family.py']:
        assets['source/'+p]=ROOT/p
    for p in sorted((ROOT/'benchmarks/public_2026-11-27').rglob('*')):
        if p.is_file(): assets['inputs/'+str(p.relative_to(ROOT))]=p
    for name in ('benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-27_BV.json',
                 'docs/updates/2026-11-27-complete-public-bv-family.md'):
        assets['inputs/'+name]=ROOT/name
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
            if p.exists():raise FileExistsError('Do not overwrite archive part')
            p.write_bytes(data);parts.append(dict(path=name,bytes=len(data),sha256=sha(data)))
    m=dict(archive_sha256=sha(b),archive_bytes=len(b),parts=parts,assets=len(hashes),files_sha256=hashes,
        format='Concatenate ordered parts into standard tar.xz. Python stdlib checker streams all assets.',
        scope='All9 complete public BV minima: raw ideal/noisy/DEM, full6 generators per plan,3-qubit signed proofs,2-original-output mapping, durable compile journals, frozen source/protocol/model hashes. No wheels or evaluation freeze;0shots.')
    save(result/'snapshot_manifest.json',m)
    print(json.dumps({k:v for k,v in m.items() if k!='files_sha256'},indent=2))


def check(result, exact=False):
    import stim
    from public_clifford import logical_circuit, validate_plan
    from public_partial_readout import original_output_view, check_original_outputs
    from exact_program_validation import check_exact
    from common_physical_pool import remap
    from public_candidate_pool import digest
    from surgery import add_noise
    m=read(result/'snapshot_manifest.json');seen={};data={}
    with tempfile.TemporaryDirectory() as temp:
        archive=Path(temp)/PREFIX
        with archive.open('wb') as f:
            for part in m['parts']:
                b=(ROOT/part['path']).read_bytes()
                if sha(b)!=part['sha256'] or len(b)!=part['bytes']:raise ValueError('Archive part differs')
                f.write(b)
        if sha(archive.read_bytes())!=m['archive_sha256']:raise ValueError('Complete archive differs')
        with tarfile.open(archive,'r|xz') as t:
            for member in t:
                if not member.isfile() or member.name in seen:raise ValueError('Regular unique assets required')
                b=t.extractfile(member).read()
                if member.name=='sha256.json':
                    if json.loads(b)!=m['files_sha256']:raise ValueError('Internal manifest differs')
                    continue
                if sha(b)!=m['files_sha256'].get(member.name):raise ValueError('Asset hash differs: '+member.name)
                seen[member.name]=sha(b);data[member.name]=b
        if seen!=m['files_sha256']:raise ValueError('Incomplete archive')
    env=json.loads(data['records/environment.json'])
    for p,h in env['code_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h or sha(data['source/'+p])!=h:raise ValueError('Frozen executed source differs')
    for p,h in env['source_sha256'].items():
        if sha(data['inputs/'+p])!=h:raise ValueError('Pinned input source differs')
    for p,h in json.loads(data['records/freeze.json']).items():
        if sha(data['records/'+p])!=h:raise ValueError('Precompile freeze differs')
    program=json.loads(data['records/program.json']);pool=json.loads(data['records/candidate_pool.json'])
    index=json.loads(data['records/physical_index.json']);device=json.loads(data['records/device.json'])
    if len(pool)!=9 or len(index)!=9 or device['sha256']!=digest(device['sites']):raise ValueError('Whole declared pool/device required')
    u=stim.Tableau.from_circuit(logical_circuit(program,False));requests=starts=finishes=checks=0
    def circuit(h):
        b=data['circuits/'+h+'.stim']
        if sha(b)!=h:raise ValueError('Raw hash-addressed circuit differs')
        return stim.Circuit(b.decode())
    for row, entry in zip(pool,index,strict=True):
        cid=row['candidate_id'];c=json.loads(data['certificates/'+cid+'.json'])
        validate_plan(program,row['plan'])
        if cid!=entry['candidate_id'] or c['plan_sha256']!=digest(row['plan']) or c['source_sha256']!=program['source_sha256']:
            raise ValueError('Source/plan/pool differs')
        meta=c['original_output_meta'];full=deepcopy(meta)
        full.update(external_flows=full['internal_external_flows'],num_observables=3)
        if sorted(o['id'] for o in meta['instruction_trace'])!=list(range(13)):
            raise ValueError('Missing complete source lowering')
        if c['original_output_validation']['full_original_output_rank']!=2 or c['full_internal_validation']['full_z_readout_rank']!=3:
            raise ValueError('Incomplete output/unitary certificate')
        if len(c['generators'])!=6 or len(c['compile_requests'])!=7:raise ValueError('Generator/request missing')
        requests+=len(c['compile_requests'])
        j=[json.loads(x) for x in data['journals/'+cid+'.jsonl'].decode().splitlines()]
        a=[x['key'] for x in j if x['event']=='compile_started'];b=[x['key'] for x in j if x['event']=='compile_finished']
        if a!=b or any(x['event']=='compile_failed' for x in j):raise ValueError('Unfinished/failed compile')
        if len(a)!=sum(not r['cache_hit'] for r in c['compile_requests']):raise ValueError('Journal/actual compile count differs')
        starts+=len(a);finishes+=len(b)
        for field in ('full_internal_validation','original_output_validation','remap_original_output_validation'):
            if len(c[field]['signed_inputs'])!=8 or len(c[field]['final_faults'])!=3:raise ValueError('Full signed/fault proof missing')
        for g in c['generators']:
            axis=g['input_generator'][0];q=int(g['input_generator'][1:]);o=u.x_output(q) if axis=='X' else u.z_output(q)
            target='I'*q+axis+'I'*(2-q)+str(o)[1:].replace('_','I')
            if g['target_flow']!=target or len(g['validation']['signed_inputs'])!=8:raise ValueError('Generator/sign target differs')
            span=set()
            flows=g['backend_meta']['external_flows']
            for mask in range(1,1<<len(flows)):
                flow=stim.PauliString(6)
                for k,f in enumerate(flows):
                    if mask>>k&1:flow*=stim.PauliString(f)
                span.add(str(flow))
            if str(stim.PauliString(target)) not in span:raise ValueError('Required generator absent from physical boundary span')
            raw=circuit(g['ideal_sha256'])
            if exact:check_exact(raw,g['backend_meta'],program);checks+=1
        internal=circuit(c['internal_ideal_sha256']);view,viewmeta=original_output_view(internal,full,program)
        if sha(str(view).encode())!=c['original_output_ideal_sha256'] or viewmeta['external_flows']!=c['external_flows']:
            raise ValueError('Complete original-output mapping differs')
        common,_=remap(view,device['sites'])
        if sha(str(common).encode())!=c['ideal_sha256']:raise ValueError('Common coordinate circuit differs')
        noisy=circuit(c['noisy_sha256']);dem=stim.DetectorErrorModel(data['circuits/'+c['dem_sha256']+'.dem'].decode())
        if exact:
            check_exact(internal,full,program,True);check_original_outputs(view,viewmeta,program)
            check_original_outputs(common,viewmeta,program);checks+=3
            if add_noise(common,.001)!=noisy or noisy.detector_error_model(decompose_errors=True)!=dem:
                raise ValueError('Frozen noisy model/DEM differs')
            if view.detector_error_model(decompose_errors=True)!=common.detector_error_model(decompose_errors=True):raise ValueError('Ideal DEM remap differs')
            if add_noise(view,.001).detector_error_model(decompose_errors=True)!=dem:raise ValueError('Noisy DEM remap differs')
    if (requests,starts,finishes)!=(63,36,36):raise ValueError('Actual complete compile accounting differs')
    result=dict(status='PASS',assets=len(seen),complete_public_minima=9,compile_requests=requests,
        journaled_compile_started=starts,journaled_compile_finished=finishes,unfinished_compilations=0,
        exact_physical_checks_rerun=checks,signed_input_checks_rerun=checks*8,
        mode='All archived bytes/source/freeze/coverage and actual signed physical/DEM replay' if exact else 'All archived bytes/source/freeze/coverage and output/remap reconstruction; stored signed proofs checked',
        new_shots=0,sampler_calls=0)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('--result',type=Path,default=DEFAULT)
    parser.add_argument('--check',action='store_true');parser.add_argument('--exact',action='store_true');a=parser.parse_args()
    if a.exact and not a.check:parser.error('--exact requires --check')
    check(a.result,a.exact) if a.check else pack(a.result)
