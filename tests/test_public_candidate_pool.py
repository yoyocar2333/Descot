from collections import Counter
from functools import lru_cache
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_clifford import load_program, schedule_program
from public_candidate_pool import enumerate_plans, features, digest, fit_model, select

@lru_cache
def program():
    return load_program(Path(__file__).resolve().parents[1]/'benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm')


def test_exact_pool_includes_all_structural_controls_and_preserves_source():
    p=program(); plans=enumerate_plans(p)
    signatures=lambda plan: [l['operation_ids'] for l in plan['layers'] if l['kind']=='cx']
    assert len(plans)==13
    assert Counter((features(p,s)['cx_routing_steps'],features(p,s)['logical_h_layers']) for s in plans)=={(4,12):6,(3,10):4,(3,9):2,(2,7):1}
    for mode in ('parallel','serial','serial_reverse'):
        assert signatures(schedule_program(p,mode)) in [signatures(s) for s in plans]
    assert all(sorted(i for l in s['layers'] for i in l['operation_ids'])==list(range(32)) for s in plans)


def test_pool_cap_rejects_instead_of_selection_bias_and_geometry_is_deterministic():
    with pytest.raises(ValueError,match='exceeds'): enumerate_plans(program(),cap=12)
    assert digest(enumerate_plans(program()))==digest(enumerate_plans(program()))
    assert len(enumerate_plans(program(),5))==13


def test_features_distinguish_equal_depth_and_count_all_live_waiting():
    rows=[features(program(),p) for p in enumerate_plans(program())]
    serial=[r for r in rows if r['cx_routing_steps']==4]
    assert {r['template_block_z'] for r in serial}=={48}
    assert len({r['cx_gap_squared_block_z2'] for r in serial})>1
    assert {r['total_protected_idle_block_z'] for r in serial}=={108}
    assert all(r['stim_ticks'] is None and r['qec_rounds'] is None for r in rows)


def test_guard_ablation_and_hard_depth_constraint_use_no_test_labels():
    rows=[{'candidate_id':f'p{i:02d}','features':features(program(),p),'shots':100000,'failures_any':45000+i*500}
          for i,p in enumerate(enumerate_plans(program()))]
    model=fit_model(rows)
    blind=[{k:v for k,v in r.items() if k not in ('shots','failures_any')} for r in rows]
    assert select(blind,model)['candidate_id']=='p12'
    assert select(blind,model,pool='serial_matched')['pool_size']==6
    guarded=select(blind,{**model,'loo_max_abs_logit_residual':1e6},pool='serial_matched',guarded=True)
    assert guarded['candidate_id']==guarded['baseline_candidate_id']=='p00'
    assert fit_model(rows,False)['fields']==['physical_layers']


def test_interval_metadata_cannot_overwrite_selector_name():
    from memory_calibration_previous import wilson_interval
    from report_public_candidates import evaluate_decisions
    observed={}
    for name,k in [('p00',62000),('p03',59000)]:
        lo,hi=wilson_interval(k,100000)
        observed[name]={'sample_id':name,'shots':100000,'failures_any':k,'p_fail_any':k/100000,
                        'wilson95_low':lo,'wilson95_high':hi}
    decisions=[{'method':'depth_wait','candidate_id':'p03','baseline_candidate_id':'p00'},
               {'method':'depth_wait_guard','candidate_id':'p00','baseline_candidate_id':'p00'}]
    rows=evaluate_decisions(observed,decisions)
    assert [r['method'] for r in rows]==['depth_wait','depth_wait_guard']
    assert rows[0]['difference']==pytest.approx(-.03)
    assert 'Newcombe' in rows[0]['interval_method']
    assert rows[1]['difference']==0 and rows[1]['ci95']==[0,0]
