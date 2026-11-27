import math
import pytest
import stim

from review_dem_ambiguity import parse_effects, triangles, scan


def test_separator_preserves_whole_bernoulli_and_xor_not_independent_pieces():
    d=stim.DetectorErrorModel('error(0.1) D0 D1 L0 ^ D1 D2 L0')
    effects,stats=parse_effects(d)
    assert effects=={((0,2),0):[(0,.1)]}
    assert stats['error_instruction_count']==1
    assert stats['separated_error_instructions']==stats['separator_tokens']==1
    assert not triangles(effects)


def test_repeats_and_relative_offsets_are_flattened():
    d=stim.DetectorErrorModel('repeat 2 {\n error(0.1) D0\n shift_detectors 1\n}')
    e,_=parse_effects(d)
    assert set(e)=={((0,),0),((1,),0)}


def test_same_whole_effect_keeps_distinct_parent_probabilities():
    d=stim.DetectorErrorModel('error(0.1) D0\nerror(0.2) D0\nerror(0.1) D1\nerror(0.1) D0 D1 L0')
    e,_=parse_effects(d);ts=triangles(e)
    assert len(ts)==1 and len(ts[0]['A'])==2
    from review_dem_ambiguity import patterns
    # Expected parent-pair count .1*.1+.2*.1; not odd-parity merged .26*.1.
    assert patterns(ts[0])['AC'][2]==pytest.approx(.03)


def test_pair_incidence_is_not_union_probability_for_overlapping_events():
    d=stim.DetectorErrorModel('error(0.1) D0\nerror(0.1) D1\nerror(0.1) D2\nerror(0.1) D0 D1 L0\nerror(0.1) D0 D2 L0')
    s=scan(d)
    assert s['ac_vs_b_pairs']==2 and s['ac_pair_incidence']==pytest.approx(.02)
    union_probability=.1*(1-(1-.1)*(1-.1))
    assert union_probability==pytest.approx(.019)
    assert not math.isclose(s['ac_pair_incidence'],union_probability)


def test_ac_excludes_two_other_malignant_pair_families():
    d=stim.DetectorErrorModel('error(0.01) D0\nerror(0.01) D1\nerror(0.01) D0 D1 L0')
    r=scan(d)
    assert r['ac_pair_incidence']==pytest.approx(.0001)
    for k in ['AC','AB','BC']:
        assert r['pair_families'][k]['decoded_any_error_patterns']==1
    assert r['triangle_family_pair_incidence']==pytest.approx(.0003)
    assert not any(r['single_pattern_failures'].values())


def test_topological_ambiguity_does_not_determine_decoder_choice():
    # The direct B edge is much less likely; matching chooses A+C, so AC succeeds.
    d=stim.DetectorErrorModel('error(0.1) D0\nerror(0.1) D1\nerror(0.000001) D0 D1 L0')
    r=scan(d)
    assert r['ac_vs_b_pairs']==1
    assert r['pair_families']['AC']['decoded_any_error_patterns']==0
    assert r['single_pattern_failures']['B_failed']==1


def test_same_declared_idle_profile_does_not_identify_reported_group():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    rows={x['candidate_id']:x['features'] for x in json.loads((root/'results/grover_depth_frontier_2026-11-26/physical_index.json').read_text())}
    a,b=rows['g052'],rows['g109']
    assert a['protected_idle_intervals_block_z']==b['protected_idle_intervals_block_z']==[[3,3,6,3],[3]]
    assert a['cx_recurrence_separations_block_z']==[9]
    assert b['cx_recurrence_separations_block_z']==[12]
