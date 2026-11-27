from copy import deepcopy
from pathlib import Path
import pytest
import stim

from public_clifford import load_program,validate_plan
from public_gate_pool import enumerate_gate_plans
from public_minimum_pool import minimum_gate_plans
from public_candidate_pool import canonical
from exact_compile_cache import ExactCompileCache

ROOT=Path(__file__).resolve().parents[1]

def grover():return load_program(ROOT/'benchmarks/public_2026-11-17/qasmbench/grover_n2.qasm')
def hs4():return load_program(ROOT/'benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm')

def test_dynamic_pool_matches_full_exhaustive_grover_domain():
    p=grover();a=minimum_gate_plans(p);all_plans=enumerate_gate_plans(p)
    depths=[sum(x['kind']!='virtual_or_readout' for x in r['layers']) for r in all_plans]
    assert a['all_legal_plan_count']==len(all_plans)==175
    assert a['minimum_physical_layers']==min(depths)==9
    expected={canonical(p) for p,d in zip(all_plans,depths) if d==9}
    assert {canonical(p) for p in a['plans']}==expected
    assert len(a['plans'])==a['minimum_plan_count']==12

def test_complete_hs4_all_minima_and_nonminimum_domain_retained():
    p=hs4();a=minimum_gate_plans(p)
    assert a['minimum_physical_layers']==9 and a['minimum_plan_count']==144
    assert a['all_legal_plan_count']==545893576119
    assert a['nonminimum_plan_count']==a['all_legal_plan_count']-144
    assert len({canonical(p) for p in a['plans']})==144
    for r in a['plans']:
        validate_plan(p,r)
        assert sorted(i for l in r['layers'] for i in l['operation_ids'])==list(range(32))

def test_fail_rather_than_truncate_or_delete_unsupported_source():
    with pytest.raises(ValueError,match='no partial'):minimum_gate_plans(hs4(),maximum_minima=143)
    with pytest.raises(ValueError,match='Positive'):minimum_gate_plans(grover(),maximum_minima=0)
    p=grover();p['operations'][0]['name']='t'
    with pytest.raises(ValueError,match='not be dropped'):minimum_gate_plans(p)

def test_invalid_dependency_dag_fails():
    p=grover();p['operations'][0]['predecessors']=[17]
    with pytest.raises(ValueError,match='invalid'):minimum_gate_plans(p)

def test_cache_keys_entire_request_and_returns_independent_objects():
    calls=[]
    def compiler(p,r,a,b):
        calls.append((deepcopy(p),deepcopy(r),a,b));return stim.Circuit('H 0'),{'nested':[0]}
    c=ExactCompileCache(compiler);p=grover();r=minimum_gate_plans(p)['plans'][0]
    x,m=c.generate(p,r);x.append('X',[0]);m['nested'].append(1)
    y,n=c.generate(p,r,'zz','zz')
    assert len(calls)==1 and y==stim.Circuit('H 0') and n=={'nested':[0]}
    c.generate(p,r,'xz','zz');s=deepcopy(r);s['spacing']=4;c.generate(p,s)
    pp=deepcopy(p);pp['operations'][0]['params']=['distinct-full-input'];c.generate(pp,r)
    assert len(calls)==4 and len(c.requests)==5
    assert sum(v['cache_hit'] for v in c.requests)==1
    assert c.requests[1]['physical_compile_seconds'] is None
    assert len({v['key'] for v in c.requests})==4
