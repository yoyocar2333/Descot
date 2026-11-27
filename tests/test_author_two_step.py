import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from author_two_step import FrontReward,author_reward_hooks,route_native
from core import load_core
from run_original_objective import ROOT,DEFAULT


def test_successor_uses_actual_candidate_not_stale_native_argument():
    calls=[]
    def executable(gates):
        calls.append(list(gates));return gates,{}
    def rollout(order,front,*args):return [(i,q,[0]) for i,q in front.items()]
    r=FrontReward(SimpleNamespace(executable_subset=executable),{0:[0],1:[1]}, {'width':1,'height':1,'magic_states':[]},{0:0,1:1},{0:2,1:1},'author_two',rollout)
    assert r.score([(0,[0],[0])],{0:[0]}, {0:2,1:1})==3
    assert calls==[[1]]
    assert r.score([(0,[0],[999])],{}, {0:2,1:1})==3
    assert len(calls)==1 and r.cache_hits==1


def test_native_reward_callbacks_restored_on_exception():
    router=load_core(ROOT.parent/'external/wisq')['sarouting']
    names=['best_realizable_set_found','try_order','route_gate','criticality_fast']
    old={n:getattr(router,n) for n in names}
    with pytest.raises(RuntimeError,match='deliberate'):
        with author_reward_hooks(router,'author_two',1):raise RuntimeError('deliberate')
    assert all(getattr(router,n) is value for n,value in old.items())


def test_reward_only_reference_reproduces_published_author_schedule():
    router=load_core(ROOT.parent/'external/wisq')['sarouting']
    inp=json.loads((DEFAULT/'inputs/3_17_13_compact.json').read_text())
    index=json.loads((DEFAULT/'index.json').read_text())
    for seed in [1,4]:
        r=route_native(router,inp['program'],inp['architecture'],inp['mapping'],seed,'author')
        ref=next(a for a in index if a['instance']=='3_17_13_compact' and a['method']=='original' and a['seed']==seed)
        assert r['schedule_sha256']==ref['schedule_sha256']
        assert r['stats']['rollout_order_evaluations']==0


def test_two_step_really_invokes_native_search_and_charges_rollouts():
    router=load_core(ROOT.parent/'external/wisq')['sarouting']
    inp=json.loads((DEFAULT/'inputs/3_17_13_compact.json').read_text())
    r=route_native(router,inp['program'],inp['architecture'],inp['mapping'],1,'author_two')
    assert r['validation']['valid']
    assert r['stats']['main_order_evaluations']>0
    assert r['stats']['rollout_order_evaluations']>0
    t=r['timing']
    assert t['routing_total_seconds']==pytest.approx(t['search_other_seconds']+t['scorer_exclusive_seconds']+t['lookahead_route_seconds'])
    # Enumeration proposals stay native: CX before T, apart from initial shuffle.
    for f in r['stats']['fronts']:
        ready=dict((i,inp['program']['routing_gates'][i]) for i in f['ready_ids'])
        if sum(len(q)==2 for q in ready.values())<5 and sum(len(q)==1 for q in ready.values())<5:
            ids=list(ready)
            for attempt in f['orders'][1:]:
                lengths=[len(ready[ids[j]]) for j in attempt['order']]
                assert lengths==sorted(lengths,reverse=True)
