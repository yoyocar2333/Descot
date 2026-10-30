import copy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import load_core
from lookahead import Config,Engine,advance,candidate_orders,ready_front,reference_conflict,schedule
from validation import validate

@pytest.fixture(scope='module')
def core():return load_core(Path(__file__).resolve().parents[2]/'external/wisq')

def test_criticality_max_successor(core):
    assert core['sarouting'].build_crit_dict_fast([(0,1),(0,2),(1,3),(2,3),(4,5)])=={0:3,1:2,2:2,3:1,4:1}

def test_front_preserves_indirect_precedence():
    assert list(ready_front({0:(0,1),1:(1,2),2:(2,3),3:(4,5)}))==[0,3]

def test_advance_does_not_mutate():
    remaining={0:(0,1),1:(1,2)};before=copy.deepcopy(remaining)
    assert advance(remaining,[(0,(0,1),[3])])=={1:(1,2)}
    assert remaining==before

def test_reference_conflict():
    assert reference_conflict([[1,2],[2,3],[9]])==pytest.approx(1/3)
    assert reference_conflict([])==0
    assert reference_conflict([[1]])==0
    assert reference_conflict([None])==1

def test_candidate_pool_prefix_is_shared():
    f={i:(2*i,2*i+1) for i in range(9)};c={i:10-i for i in f};m={i:i for i in range(18)}
    a=candidate_orders(f,c,m,20,16,123);b=candidate_orders(f,c,m,20,48,123)
    assert a==b[:16] and len(set(b))==48

def test_tie_breaker_cannot_override_integer_progress():
    assert 10-.25*1 > 9-.25*0
    with pytest.raises(ValueError):Config(conflict_weight=1)

@pytest.mark.parametrize('mode',['one_step','two_step','two_step_conflict','random'])
def test_budget_legality_repeatability_and_state_isolation(core,mode):
    gates=[(0,1),(2,3),(0,2),(1,3),(0,1),(2,3)]
    arch=core['architecture'].square_sparse_layout(4,'all_sides');mapping=list(zip(range(4),arch['alg_qubits']))
    before=copy.deepcopy((gates,arch,mapping));config=Config(mode,12)
    a=schedule(core['sarouting'],gates,arch,mapping,19,config)
    b=schedule(core['sarouting'],gates,arch,mapping,19,config)
    assert validate(gates,arch,mapping,a['steps'])['valid']
    assert a['steps']==b['steps']
    assert (gates,arch,mapping)==before
    assert all(r['cost']['front_evaluations']<=12 for r in a['fronts'])
    assert a['cost']['front_evaluations']==sum(r['cost']['front_evaluations'] for r in a['fronts'])

def test_empty_rollout_and_conflict_charge_no_phantom_work(core):
    arch=core['architecture'].square_sparse_layout(2,'all_sides');mapping=list(zip(range(2),arch['alg_qubits']))
    result=schedule(core['sarouting'],[(0,1)],arch,mapping,1,Config('two_step_conflict',48))
    assert result['cost']=={'front_evaluations':1,'order_evaluations':1,'reference_batches':0,'gate_route_calls':1}

def test_paths_are_released_between_steps(core):
    arch=core['architecture'].square_sparse_layout(2,'all_sides');mapping=list(zip(range(2),arch['alg_qubits']))
    result=schedule(core['sarouting'],[(0,1),(0,1)],arch,mapping,1,Config('two_step',12))
    assert result['time_steps']==2
    assert result['fronts'][0]['chosen']['future']>0
    assert result['steps'][0][0][2]==result['steps'][1][0][2]
