from copy import deepcopy
import json
from pathlib import Path
import pytest

from hamada_ready_control import schedule,author_check,build_oracle
from public_clifford import load_program

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def grover():return load_program(ROOT/'benchmarks/public_2026-11-17/qasmbench/grover_n2.qasm')

def test_complete_public_policy_matches_certified_unrestricted_reference(grover):
 r=schedule(grover);rows=json.loads((ROOT/'results/grover_competition_2026-11-17/candidate_pool.json').read_text())
 ref=next(x for x in rows if x['candidate_id']=='g174')
 assert r['plan']['layers']==ref['plan']['layers']
 assert sorted(i for l in r['plan']['layers'] for i in l['operation_ids'])==list(range(18))
 assert [f['gate_route_calls'] for f in r['fronts']]==[1,1] and r['mu']==0

def test_original_cpp_manager_checks_full_dag_and_rejects_changed_ready_set(grover,tmp_path):
 binary=tmp_path/'oracle';build_oracle(binary);r=schedule(grover)
 check=author_check(grover,r['dag_oracle_events'],binary)
 assert check['processed_source_instructions']==18 and check['ready_queries']>9
 bad=deepcopy(r['dag_oracle_events']);bad[0][1]=[]
 with pytest.raises(ValueError,match='disagrees'):author_check(grover,bad,binary)

def test_independent_ready_cxs_keep_complete_footprints_on_full_public_hs4():
 p=load_program(ROOT/'benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm');r=schedule(p)
 assert sorted(i for l in r['plan']['layers'] for i in l['operation_ids'])==list(range(32))
 assert max(len(f['ready_ids']) for f in r['fronts'])>=2
 for f in r['fronts']:
  footprints=[set(map(tuple,a['footprint'])) for a in f['attempts'] if a['accepted']]
  assert all(not (a&b) for i,a in enumerate(footprints) for b in footprints[i+1:])

@pytest.mark.parametrize('budget',[0,-1,True])
def test_insufficient_budget_fails_without_partial_result(grover,budget):
 with pytest.raises(ValueError,match='budget'):schedule(grover,budget=budget)

def test_unsupported_gate_is_not_silently_removed(grover):
 bad=deepcopy(grover);bad['operations'][0]['name']='s'
 with pytest.raises(ValueError,match='dropped'):schedule(bad)
