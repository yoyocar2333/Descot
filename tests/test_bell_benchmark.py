import copy
from functools import lru_cache
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bell_benchmark import original_qasm, SOURCE_DIR, readout_validation
from public_clifford import load_program, schedule_program, validate_plan, generate_program, validate_physical, validate_clifford_generators
from public_lookahead import schedule
from public_candidate_pool import enumerate_plans
from public_readout import classical_bits


@lru_cache
def program():
    return load_program(SOURCE_DIR/'bell_n6.qasm')


@lru_cache
def physical():
    p=program()
    return generate_program(p,schedule_program(p))


def test_exact_upstream_generation_full_instructions_and_random_outputs():
    assert original_qasm()==(SOURCE_DIR/'bell_n6.qasm').read_text()
    p=program()
    assert p['operation_counts']=={'barrier':1,'cx':3,'h':3,'measure':6}
    assert len(p['incomparable_cx_pairs'])==3
    c,m=physical()
    assert len(m['instruction_trace'])==13
    assert validate_physical(c,m,p,2)['all_signed_inputs_passed']
    check=readout_validation(c,m,p,2)
    assert check['independent_z_observables']==3
    assert len(check['original_output_distribution'])==8
    assert all(abs(r['probability']-.125)<1e-12 for r in check['original_output_distribution'])
    # The deterministic hs4 readout map must refuse this random-output source.
    with pytest.raises(ValueError,match='complete observables'):
        classical_bits(m,[0,0,0])


def test_barrier_cannot_move_before_its_original_dependencies():
    p=program();plan=schedule_program(p)
    fence=next(l for l in plan['layers'] if 6 in l['operation_ids'])
    bad=copy.deepcopy(plan);bad['layers'].remove(fence);bad['layers'].insert(0,fence)
    with pytest.raises(ValueError):
        validate_plan(p,bad)


def test_readout_subgroup_and_missing_original_h_fail_closed():
    p=program();c,m=physical()
    bad=copy.deepcopy(m);bad['external_flows'].pop()
    with pytest.raises(AssertionError,match='Incomplete'):
        readout_validation(c,bad,p,2)
    changed=copy.deepcopy(p);changed['operations'][0]['name']='x'
    # ZZ-only checks cannot detect every phase/H error. The independent full
    # generator path must reject this inconsistent complete source/plan.
    with pytest.raises(ValueError):
        validate_clifford_generators(changed,schedule_program(p),2)


def test_exact_pool_and_budgeted_methods_preserve_all_source_operations():
    p=program();assert len(enumerate_plans(p))==13
    for mode in ('one_step','two_step'):
        r=schedule(p,mode,budget=48,candidate_cap=16)
        assert sum(l['kind']=='cx' for l in r['plan']['layers'])==1
        assert sorted(i for l in r['plan']['layers'] for i in l['operation_ids'])==list(range(13))
        assert all(f['cost']['front_evaluations']<=48 for f in r['fronts'])
