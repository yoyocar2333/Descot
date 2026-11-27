"""Independently audit native reward-only results, full source and successor scores."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile

from core import COMMIT,load_core
from lookahead import ready_front
from run_author_native_two import OUT,ROOT,CODE,sha,read
from run_original_objective import trace_source
from validation import validate


def check_rollout(step,front,arch,mapping):
    """Check one proposed successor step with every live data patch blocked."""
    mapping=dict(mapping);w=arch['width'];n=w*arch['height'];blocked=set(mapping.values())|set(arch['magic_states']);used=set();qubits=set();ids=set()
    for gid,args,path in step:
        assert gid in front and args==front[gid] and gid not in ids
        ids.add(gid);assert not qubits.intersection(args);qubits.update(args)
        assert path and len(set(path))==len(path) and all(0<=v<n for v in path)
        assert not blocked.intersection(path) and not used.intersection(path);used.update(path)
        assert all(abs(a//w-b//w)+abs(a%w-b%w)==1 for a,b in zip(path,path[1:]))
        assert path[0] in {mapping[args[0]]-w,mapping[args[0]]+w}
        targets=[mapping[args[1]]] if len(args)==2 else arch['magic_states']
        assert any(abs(path[-1]-v)==1 and path[-1]//w==v//w for v in targets)


def main():
    freeze=read(OUT/'freeze.json')
    for p,h in freeze['code_sha256'].items():assert sha((ROOT/p).read_bytes())==h,p
    assert sha((OUT/'protocol.json').read_bytes())==freeze['protocol_sha256']
    assert sha((OUT/'inputs.json').read_bytes())==freeze['inputs_sha256']
    assert sha((ROOT.parent/'external/wisq/src/wisq/sarouting.py').read_bytes())==freeze['upstream_sarouting_sha256']
    router=load_core(ROOT.parent/'external/wisq')['sarouting']
    inputs={c['id']:c for c in read(OUT/'inputs.json')}
    for c in inputs.values():assert sha((ROOT/c['input_path']).read_bytes())==c['input_sha256']
    index=read(OUT/'index.json');assert len(index)==168
    raw={};archive=ROOT/'archives/author_native_two_2026-11-28.zip'
    if archive.exists():
        meta=read(ROOT/'archives/manifest.json')[archive.name];assert sha(archive.read_bytes())==meta['sha256']
        with zipfile.ZipFile(archive) as z:
            assert z.read('results/author_native_two_2026-11-28/inputs.json')==(OUT/'inputs.json').read_bytes()
            for name in z.namelist():
                if '/records/' in name:raw[Path(name).name]=json.loads(z.read(name))
    else:raw={p.name:read(p) for p in (OUT/'records').glob('*.json')}
    assert len(raw)==168
    rolled=0;exact=0;seen_hashes={};scores=0
    for name,r in raw.items():
        c=inputs[r['instance']];gates=c['program']['routing_gates'];crit=router.build_crit_dict_fast(gates)
        validate(gates,c['architecture'],c['mapping'],r['steps'])
        assert trace_source(c['program'],r['steps'])==r['source_trace']
        assert sha(json.dumps(r['steps']).encode())==r['schedule_sha256']
        if r['method']=='author':assert r['schedule_sha256']==c['reference'][str(r['seed'])];exact+=1
        seen_hashes[r['instance'],r['seed'],r['method']]=r['schedule_sha256']
        assert len(r['repeats'])==3 and all(x['schedule_sha256']==r['schedule_sha256'] for x in r['repeats'])
        for x in r['repeats']:
            t=x['timing'];assert min(t.values())>=0
            assert math.isclose(t['routing_total_seconds'],t['search_other_seconds']+t['scorer_exclusive_seconds']+t['lookahead_route_seconds'],abs_tol=1e-10)
        stats=r['stats'];assert len(stats['fronts'])==len(r['steps'])
        assert stats['main_order_evaluations']+stats['rollout_order_evaluations']==stats['native_counters']['order_evaluations']
        assert stats['main_gate_route_calls']+stats['rollout_gate_route_calls']==stats['native_counters']['gate_route_calls']
        for t,f in enumerate(stats['fronts']):
            remaining={i:gates[i] for i in f['remaining_ids']};assert list(ready_front(remaining))==f['ready_ids']
            assert f['chosen_sha256']==sha(json.dumps(r['steps'][t]).encode())
            assert f['reward_requests']-f['cache_hits']==len(f['scored_candidates'])
            for a in f['scored_candidates']:
                assert set(a['ids'])<=set(f['ready_ids'])
                assert a['now']==sum(crit[i] for i in a['ids'])
                next_front=ready_front({i:g for i,g in remaining.items() if i not in a['ids']})
                check_rollout(a['rollout'],next_front,c['architecture'],c['mapping'])
                assert a['future']==sum(crit[g[0]] for g in a['rollout'])
                assert a['score']==a['now']+a['future'];scores+=1;rolled+=bool(a['rollout'])
            if f['chosen_score'] is not None:assert f['chosen_score']['score']==max(a['score'] for a in f['scored_candidates'])
    events=[json.loads(s) for s in (OUT/'journal.jsonl').read_text().splitlines()];assert len(events)==1008
    keys=lambda event:{(e['instance'],e['seed'],e['repeat'],e['method']) for e in events if e['event']==event}
    assert keys('start')==keys('complete') and len(keys('start'))==504
    public_same=sum(seen_hashes[c['id'],s,'author']==seen_hashes[c['id'],s,'author_two'] for c in inputs.values() if c['cohort']=='public_development' for s in c['seeds'])
    report=dict(status='PASS',code_and_input_freeze=True,full_native_reference_hash_matches=exact,records=168,journal_completed_executions=504,score_entries_checked=scores,nonempty_successor_rollouts_checked=rolled,
        public_same_entire_schedule_hashes=public_same,old_source_files_preserved=True,
        new_shots=0,physical_compilations=0,ideal_sha256=None,noisy_sha256=None,dem_sha256=None)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
