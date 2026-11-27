import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results/hs4_minimum_frontier_2026-11-27'

def test_complete_frontier_keeps_original_parallel_and_full_outputs():
    summary=json.loads((R/'summary.json').read_text());rows=json.loads((R/'physical_index.json').read_text())
    assert summary['qualified_minimum_plans']==len(rows)==6
    assert summary['unique_noisy_circuits']==len({r['noisy_sha256'] for r in rows})==6
    assert summary['pending_minimum_plans']==138 and summary['total_minimum_plans']==144
    assert all(r['qualified_complete_output'] and len(r['external_flows'])==4 and r['graphlike_distance']==3 and r['num_qubits']==620 for r in rows)
    assert summary['new_shots']==summary['sampler_calls']==0

def test_compile_cache_never_skips_validation_targets():
    s=json.loads((R/'summary.json').read_text());rows=json.loads((R/'physical_index.json').read_text())
    assert s['compile_requests']==s['exact_targets']==6*9
    assert s['actual_physical_compilations']+s['exact_cache_hits']==s['compile_requests']
    for r in rows:
        requests=r['compile_requests'];first={}
        assert len(requests)==9
        for v in requests:
            if v['cache_hit']:
                assert first[v['key']]==v['ideal_sha256'] and v['physical_compile_seconds'] is None
            else:
                assert v['key'] not in first and v['physical_compile_seconds']>=0
                first[v['key']]=v['ideal_sha256']

def test_all_old_candidates_survive_complete_common_pool():
    a=json.loads((R/'analysis.json').read_text());p=json.loads((R/'complete_physical_pool.json').read_text())
    assert len(p)==a['total_complete_physical_pool']==19
    assert a['all_old13_preserved'] and a['exact_aliases']==[]
    assert {r['candidate_id'] for r in p if r['candidate_id'].startswith('old:')}=={'old:p%02d'%i for i in range(13)}
    assert all(s['pool_size']==s['budget']==s['row_evaluations']==19 for s in a['selections'])
