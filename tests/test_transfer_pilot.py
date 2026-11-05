import json
import pytest

from public_candidate_pool import enumerate_plans
from public_clifford import load_program
from transfer_pilot import BELL4, CAT, OUT, bell4_qasm, choose_front, local_features, parity_mask


def test_fixed_sources_and_schedule_choices():
    assert BELL4.read_text() == bell4_qasm()
    bell = load_program(BELL4)
    cat = load_program(CAT)
    assert len(enumerate_plans(bell)) == 3
    assert len(enumerate_plans(cat)) == 1
    assert local_features(cat, enumerate_plans(cat)[0], (0,1))['other_incident_cx'] == 1


def test_parity_must_be_xor_of_a_unique_original_basis():
    assert parity_mask(['IIIZZI','IIIIZZ'],3,(0,2)) == 3
    with pytest.raises(ValueError):
        parity_mask(['IIIZZI','IIIZZI'],3,(0,1))
    with pytest.raises(ValueError):
        parity_mask(['IIIZZI'],3,(0,2))


def test_frozen_equal_progress_ablation_and_guard():
    design = json.loads((OUT/'frozen.json').read_text())
    for decision in design['online_bell4_under_one_cx_cap']:
        rows = [r for r in design['candidates'] if r['id'] in decision['candidate_ids']]
        result = choose_front(rows,design['models'])
        s = result['selected']
        assert result['guard_passed_domain']
        assert result['front_candidates'] == result['rollout_front_evaluations'] == 2
        assert s['progress'] == s['depth_only'] == s['no_wait'] == s['guarded']
        assert s['full'] == s['no_geometry'] != s['progress']
    assert all(not row['domain_supported'] for row in design['candidates'] if row['source']=='cat4')
