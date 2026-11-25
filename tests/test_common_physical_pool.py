from copy import deepcopy
import pytest
import stim

from common_physical_pool import catalogue,remap,select,POLICIES


def test_coordinate_remap_keeps_repeats_inverted_readout_records_and_exact_dem():
    c=stim.Circuit('''QUBIT_COORDS(1, 1) 0
QUBIT_COORDS(3, 1) 1
R 0 1
H 0
CX 0 1
REPEAT 2 {
 CX 0 1
 TICK
 CX 0 1
}
X_ERROR(0.001) 0
M !0 1
OBSERVABLE_INCLUDE(0) rec[-1] rec[-2]
''')
    sites=[(0.,0.),(1.,1.),(3.,1.)];n,m=remap(c,sites)
    assert m=={0:1,1:2} and n.num_qubits==3 and n.num_ticks==c.num_ticks
    assert 'M !1 2' in str(n) and 'rec[-1] rec[-2]' in str(n) and 'REPEAT 2' in str(n)
    assert str(n.detector_error_model(decompose_errors=True))==str(c.detector_error_model(decompose_errors=True))


def test_pauli_combiner_sweep_targets_are_not_reinterpreted_as_qubit_indices():
    c=stim.Circuit('''QUBIT_COORDS(1, 1) 0
QUBIT_COORDS(3, 1) 1
R 0 1
CX sweep[5] 0
MPP !Z0*Z1
OBSERVABLE_INCLUDE(0) rec[-1]
''')
    n,_=remap(c,[(0.,0.),(1.,1.),(3.,1.)])
    assert 'sweep[5] 1' in str(n) and '!Z1*Z2' in str(n)
    assert str(n.detector_error_model())==str(c.detector_error_model())


def test_outside_device_is_rejected_instead_of_dropping_operations():
    c=stim.Circuit('QUBIT_COORDS(1,1) 0\nR 0\nM 0')
    with pytest.raises(ValueError,match='outside'):remap(c,[(0.,0.)])


def test_duplicate_physical_coordinate_cannot_merge_two_qubits():
    c=stim.Circuit('QUBIT_COORDS(1,1) 0\nQUBIT_COORDS(1,1) 1\nR 0 1')
    with pytest.raises(ValueError,match='injective'):catalogue([c])


@pytest.fixture
def rows():
    return [dict(candidate_id=i,device_sha256='same',outside_device_sites=0,qualified_complete_output=True,
                 external_flows=['ZIIZ','IZZI'],features=dict(template_block_z=d,total_lifetime_block_z=v,plain_data_storage_cubes=s,static_site_ticks=t))
            for i,d,v,s,t in [('reference',27,66,28,100),('projection',24,90,22,90),('other',27,66,28,100)]]


def test_multi_stage_selectors_use_identical_whole_pool_and_preserve_reference_ties(rows):
    outputs=[select(rows,p,'reference',3) for p in POLICIES]
    assert len({r['pool_sha256'] for r in outputs})==1
    assert all(r['row_evaluations']==r['budget']==r['pool_size']==3 for r in outputs)
    assert outputs[0]['candidate_id']=='projection' and outputs[1]['candidate_id']=='reference'
    assert set(outputs[1]['tied_optima'])=={'reference','other'}


@pytest.mark.parametrize('damage',['budget','infeasible','unqualified','basis','device','retired'])
def test_unfair_or_incomplete_comparison_fails_without_silent_filtering(rows,damage):
    budget=3;policy='duration_then_volume'
    if damage=='budget':budget=2
    elif damage=='infeasible':rows[1]['outside_device_sites']=31
    elif damage=='unqualified':rows[1]['qualified_complete_output']=False
    elif damage=='basis':rows[1]['external_flows']=['ZZII']
    elif damage=='device':rows[1]['device_sha256']='other'
    else:policy='raw_readout_wait'
    with pytest.raises(ValueError):select(rows,policy,'reference',budget)
