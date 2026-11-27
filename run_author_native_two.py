"""Frozen development comparison: original native search vs reward-only two-step.

Prepare first; execute checks the exact frozen source/input hashes. No mapping,
physical compilation or Monte Carlo work runs in the timing pass.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess

from author_two_step import route_native
from core import COMMIT,load_core
from run_original_objective import ROOT,DEFAULT,save

OUT=ROOT/'results/author_native_two_2026-11-28'
METHODS=['author','author_two']
CODE=['author_two_step.py','run_author_native_two.py','saturation.py','validation.py','run_original_objective.py','core.py','requirements-lock.txt']


def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()


def cases():
    result=[]
    public=read(DEFAULT/'index.json')
    for p in sorted((DEFAULT/'inputs').glob('*.json')):
        d=read(p)
        result.append(dict(id=p.stem,cohort='public_development',input_path=str(p.relative_to(ROOT)),
            input_sha256=sha(p.read_bytes()),program=d['program'],architecture=d['architecture'],mapping=d['mapping'],
            reused_mapping_seconds=d['mapping_seconds'],seeds=list(range(1,11)),
            reference={str(r['seed']):r['schedule_sha256'] for r in public if r['instance']==p.stem and r['method']=='original'}))
    old=read(DEFAULT/'historical_retiming/records.json')
    for name in sorted({r['instance'] for r in old}):
        p=ROOT/'inputs'/name/'input.json';d=read(p);last={};operations=[]
        for i,qs in enumerate(d['gates']):
            parents=sorted({last[q] for q in qs if q in last})
            operations.append(dict(id=i,name=d['ops'][i],qubits=qs,clbits=[],params=[],predecessors=parents))
            for q in qs:last[q]=i
        result.append(dict(id=name,cohort='historical_seen_synthetic',input_path=str(p.relative_to(ROOT)),input_sha256=sha(p.read_bytes()),
            program=dict(routing_gates=d['gates'],routing_operations=d['ops'],routed_source_ids=list(range(len(operations))),operations=operations),
            architecture=d['architecture'],mapping=d['mapping'],reused_mapping_seconds=d['mapping_seconds'],seeds=[1,2,3],
            reference={str(r['seed']):r['schedule_sha256'] for r in old if r['instance']==name and r['method']=='original'}))
    return result


def prepare(out):
    if out.exists():raise FileExistsError('Prepare a fresh output directory')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
    load_core(ROOT.parent/'external/wisq')
    cs=cases();out.mkdir(parents=True)
    save(out/'protocol.json',dict(id='author_native_reward_only_v1',prepared_utc=now(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        question='Does adding one next-front feasibility reward inside native author search improve full routing depth, and at what CPU cost?',
        methods=METHODS,cases=[dict(id=c['id'],cohort=c['cohort'],seeds=c['seeds'],input_path=c['input_path']) for c in cs],repeats=3,
        mapping='Reused exact previously frozen author mappings; no new mapping in this pass.',
        native_parameters=dict(temperature=10,cooling_rate=.1,termination_temp=.1,order_fraction=1,take_first_ms=False,timeout_seconds=300),
        rng='Same existing original-control per-state seeding. No stochastic rollout; criticality then gate-ID order.',
        score='Original: sum criticality now. Two: original score plus one native greedy route of the actual successor front. Weight1, no guard, no tuning.',
        successor='Rebuild from actual current remaining state minus executed IDs; ignore stale remaining argument passed by upstream.',
        search='Unchanged native driver, enumeration/SA proposals and acceptance rule. Reward changes SA acceptance, so later adaptive candidates may differ. Not a fixed-pool comparison.',
        budget='No cap added. Same native search parameters, not equal CPU or equal gate-route calls. Retain uncapped original. Record phase calls and independent timings. No fixed-CPU superiority claim.',
        caching='Within one front, cache successor rollouts by executed IDs. Paths release at the boundary; no cross-step occupancy.',
        timing='Serial alternating method order by seed/repeat. Total=search_other+scorer_exclusive+lookahead_route; scorer inclusive overlaps rollout. Legality/source trace outside route time. Shared host.',
        decision='Report every pair and cohort separately. Depth benefit with overhead is a trade-off, not automatic adoption. No rerouting tuning or new sources after labels. Fixed-CPU and broad unseen-family evidence remain future gates.',
        scope='All seen sources are development. Full source traces retained under original zero-duration local/readout SCMR abstraction; not full physical compilation.',
        new_shots=0,physical_compilations=0,mu=0,sampling_permission=False))
    save(out/'inputs.json',cs)
    upstream=ROOT.parent/'external/wisq/src/wisq/sarouting.py'
    save(out/'freeze.json',dict(python=platform.python_version(),wisq_commit=COMMIT,upstream_sarouting_sha256=sha(upstream.read_bytes()),cpu_count=os.cpu_count(),platform=platform.platform(),
        code_sha256={p:sha((ROOT/p).read_bytes()) for p in CODE},protocol_sha256=sha((out/'protocol.json').read_bytes()),inputs_sha256=sha((out/'inputs.json').read_bytes())))
    print(json.dumps(dict(prepared=True,cases=len(cs),pairs=sum(len(c['seeds']) for c in cs),planned_executions=6*sum(len(c['seeds']) for c in cs),new_shots=0)))


def summarize(out):
    rows=[]
    for p in sorted((out/'records').glob('*.json')):
        r=read(p);samples=r['repeats'];rows.append(dict(instance=r['instance'],cohort=r['cohort'],seed=r['seed'],method=r['method'],depth=r['depth'],schedule_sha256=r['schedule_sha256'],
            median_seconds=statistics.median(x['timing']['routing_total_seconds'] for x in samples),
            median_phase_seconds={k:statistics.median(x['timing'][k] for x in samples) for k in samples[0]['timing']},
            main_orders=r['stats']['main_order_evaluations'],rollout_orders=r['stats']['rollout_order_evaluations'],
            main_gate_calls=r['stats']['main_gate_route_calls'],rollout_gate_calls=r['stats']['rollout_gate_route_calls']))
    assert len(rows)==168
    by={(r['instance'],r['seed'],r['method']):r for r in rows};pairs=[]
    for a in rows:
        if a['method']!='author_two':continue
        b=by[a['instance'],a['seed'],'author']
        pairs.append(dict(instance=a['instance'],cohort=a['cohort'],seed=a['seed'],author_depth=b['depth'],two_depth=a['depth'],depth_change_percent=100*(a['depth']-b['depth'])/b['depth'],
            time_ratio=a['median_seconds']/b['median_seconds'],author_ms=1000*b['median_seconds'],two_ms=1000*a['median_seconds'],
            gate_call_ratio=(a['main_gate_calls']+a['rollout_gate_calls'])/b['main_gate_calls'],main_orders_author=b['main_orders'],main_orders_two=a['main_orders'],rollout_orders=a['rollout_orders']))
    def aggregate(ps):return dict(pairs=len(ps),wins=sum(p['two_depth']<p['author_depth'] for p in ps),ties=sum(p['two_depth']==p['author_depth'] for p in ps),losses=sum(p['two_depth']>p['author_depth'] for p in ps),
        median_depth_change_percent=statistics.median(p['depth_change_percent'] for p in ps),median_paired_time_ratio=statistics.median(p['time_ratio'] for p in ps),median_gate_call_ratio=statistics.median(p['gate_call_ratio'] for p in ps))
    save(out/'index.json',rows);save(out/'pairs.json',pairs)
    save(out/'summary.json',dict(status='complete',configurations=len(rows),routing_executions=3*len(rows),baseline_exact_matches=84,
        cohorts={name:aggregate([p for p in pairs if p['cohort']==name]) for name in sorted({p['cohort'] for p in pairs})},
        instances={name:aggregate([p for p in pairs if p['instance']==name]) for name in sorted({p['instance'] for p in pairs})},
        strongest_depth_gain=min(pairs,key=lambda p:p['depth_change_percent']),worst_depth_regression=max(pairs,key=lambda p:p['depth_change_percent']),
        all_legal=True,new_shots=0,physical_compilations=0,decision='Depth and time trade-offs only; same search parameters, not same CPU or fixed pool. No automatic default change.'))


def execute(out):
    frozen=read(out/'freeze.json');assert platform.python_version()==frozen['python']
    for p,h in frozen['code_sha256'].items():assert sha((ROOT/p).read_bytes())==h,p
    assert sha((out/'protocol.json').read_bytes())==frozen['protocol_sha256']
    assert sha((out/'inputs.json').read_bytes())==frozen['inputs_sha256']
    upstream=ROOT.parent/'external/wisq/src/wisq/sarouting.py';assert sha(upstream.read_bytes())==frozen['upstream_sarouting_sha256']
    cs=read(out/'inputs.json')
    for c in cs:assert sha((ROOT/c['input_path']).read_bytes())==c['input_sha256']
    if (out/'records').exists():raise FileExistsError('Preserve prior run; use a fresh prepared output')
    (out/'records').mkdir();router=load_core(ROOT.parent/'external/wisq')['sarouting']
    with (out/'journal.jsonl').open('x') as journal:
        def event(record):journal.write(json.dumps(record)+'\n');journal.flush()
        for c in cs:
            for seed in c['seeds']:
                retained={};repeats={m:[] for m in METHODS}
                for repeat in range(3):
                    order=METHODS if (seed+repeat)%2 else list(reversed(METHODS))
                    for method in order:
                        key=dict(instance=c['id'],seed=seed,repeat=repeat,method=method)
                        event(dict(**key,event='start',utc=now()))
                        r=route_native(router,c['program'],c['architecture'],c['mapping'],seed,method)
                        if method=='author':assert r['schedule_sha256']==c['reference'][str(seed)],'Native author schedule changed'
                        if method in retained:assert r['schedule_sha256']==retained[method]['schedule_sha256'],'Nondeterministic schedule'
                        else:retained[method]=r
                        repeats[method].append(dict(timing=r['timing'],schedule_sha256=r['schedule_sha256']))
                        save(out/'records'/(c['id']+'_'+method+f'_s{seed:02}.json'),dict(**retained[method],instance=c['id'],cohort=c['cohort'],method=method,seed=seed,repeats=repeats[method]))
                        event(dict(**key,event='complete',utc=now(),schedule_sha256=r['schedule_sha256'],depth=r['depth']))
            print(c['id'],'complete',len(c['seeds'])*6,'executions',flush=True)
    summarize(out)
    print(json.dumps(read(out/'summary.json')['cohorts']),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--output',type=Path,default=OUT);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--execute',action='store_true');g.add_argument('--summarize',action='store_true');a=p.parse_args()
    (prepare if a.prepare else execute if a.execute else summarize)(a.output)
