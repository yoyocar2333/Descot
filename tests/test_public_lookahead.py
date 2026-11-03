from copy import deepcopy
from pathlib import Path
import random
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from public_lookahead import schedule, close, criticality, Frontier
from public_clifford import load_program, validate_plan
from public_candidate_pool import enumerate_plans
from core import load_core
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def program():return load_program(ROOT/'benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm')

@pytest.mark.parametrize('mode',['one_step','two_step','author_profile'])
def test_complete_semantics_repeatability_and_upstream_rng_isolation(program,mode):
    original=deepcopy(program);base=load_core(ROOT.parent/'external/wisq')['sarouting']
    random.seed(42);np.random.seed(42);a=random.getstate();b=np.random.get_state()
    result=schedule(program,mode,5,19,candidate_cap=16,base=base)
    again=schedule(program,mode,5,19,candidate_cap=16,base=base)
    assert result==again and program==original
    assert random.getstate()==a and np.array_equal(np.random.get_state()[1],b[1])
    assert sorted(i for l in result['plan']['layers'] for i in l['operation_ids'])==list(range(32))
    assert result['mu']==0
    validate_plan(program,result['plan'])
    assert [l['operation_ids'] for l in result['plan']['layers']]==[l['operation_ids'] for l in enumerate_plans(program,5)[12]['layers']]
    if mode!='author_profile':assert all(f['cost']['front_evaluations']<=48 for f in result['fronts'])


def test_shared_candidate_pool_and_rollout_drains_real_h_instructions(program):
    a=schedule(program,'one_step',candidate_cap=16);b=schedule(program,'two_step',candidate_cap=16)
    assert [r['candidate_orders'] for r in a['fronts']]==[r['candidate_orders'] for r in b['fronts']]
    assert b['fronts'][0]['candidates'][0]['rollout_h_layers']>0
    assert b['fronts'][0]['candidates'][0]['future']>0
    assert b['cost']['front_evaluations']>a['cost']['front_evaluations']
    assert b['cost']['closure_evaluations']>0
    # Closure must not mutate caller state or forget orientation changes.
    done=set();orientation=[0]*4
    after,rot,layers=close(program,done,orientation)
    assert done==set() and orientation==[0]*4 and rot==[1,0,1,0]
    assert {o['id'] for o in program['operations'] if o['name']=='cx'}.isdisjoint(after)


def test_full_footprint_conflict_and_fresh_state():
    p={'logical_qubits':4,'operations':[{'id':0,'name':'cx','qubits':[0,2],'predecessors':[]},
                                      {'id':1,'name':'cx','qubits':[1,3],'predecessors':[]}]}
    engine=Frontier(p,3);ops=p['operations']
    # These vertex footprints may be disjoint in the default orientation;
    # find an oriented profile with actual overlap, then ensure no co-schedule.
    from itertools import product
    from public_clifford import cnot_paths
    found=False
    for rot in product((0,1),repeat=4):
        a=cnot_paths(0,2,engine.positions,rot)[2];b=cnot_paths(1,3,engine.positions,rot)[2]
        if a&b:
            found=True
            assert len(engine.route(ops,[0,1],rot))==1
            assert len(engine.route(ops,[1,0],rot))==1
    assert found


def test_budget_and_invalid_configuration_rejection(program):
    with pytest.raises(ValueError,match='budget'):schedule(program,'two_step',budget=1)
    with pytest.raises(ValueError,match='candidate'):schedule(program,'one_step',candidate_cap=0)
    with pytest.raises(ValueError,match='Unknown'):schedule(program,'fake')
    with pytest.raises(ValueError,match='required'):schedule(program,'author_profile')
