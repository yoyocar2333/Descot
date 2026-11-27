from copy import deepcopy
from pathlib import Path
import pytest
import stim
from public_partial_readout import load_partial_program, original_output_view
from public_minimum_pool import minimum_gate_plans
from public_gate_pool import enumerate_gate_plans
from run_bv_public_family import generate_source, PROTOCOL

ROOT = Path(__file__).resolve().parents[1]


def test_complete_upstream_source_and_lossless_partial_output_dag():
    p=generate_source(); original=p['original_program']; ops=p['operations']
    assert original['operation_counts']=={'cz':2,'h':4,'measure':2,'x':1}
    assert p['operation_counts']=={'cx':2,'h':8,'measure':2,'x':1}
    assert p['terminal_readout']==[{'qubit':1,'classical_bit':0},{'qubit':2,'classical_bit':1}]
    assert p['unmeasured_logical_qubits']==[0] and p['classical_bits']==2
    traces=p['lowering_trace']; assert sorted(i for t in traces for i in t['lowered_ids'])==list(range(13))
    for t in traces:
        parents=original['operations'][t['original_id']]['predecessors']
        assert ops[t['lowered_ids'][0]]['predecessors']==sorted(traces[j]['lowered_ids'][-1] for j in parents)
        if t['original_name']=='cz':
            assert [ops[i]['name'] for i in t['lowered_ids']]==['h','cx','h']


def test_all_minima_match_complete_uncapped_exhaustive_pool():
    p=generate_source(); full=enumerate_gate_plans(p); a=minimum_gate_plans(p)
    def layers(r): return sum(x['kind']!='virtual_or_readout' for x in r['layers'])
    assert len(full)==a['all_legal_plan_count']==66 and a['minimum_physical_layers']==8
    assert len([x for x in full if layers(x)==8])==a['minimum_plan_count']==9
    assert a['nonminimum_plan_count']==57
    assert PROTOCOL['physical_compile_request_ceiling']==9*7


@pytest.mark.parametrize('instruction',['t q[0];','reset q[0];','measure q[1] -> c[0];\nh q[1];'])
def test_unsupported_or_nonterminal_source_rejected_without_deleting(instruction,tmp_path):
    path=tmp_path/'bad.qasm'
    path.write_text('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[1];\n'+instruction+'\nmeasure q[0] -> c[0];\n')
    with pytest.raises(ValueError): load_partial_program(path)


def test_output_view_inverts_nontrivial_internal_basis_and_preserves_physics():
    p={'logical_qubits':3,'terminal_readout':[{'qubit':2,'classical_bit':0},{'qubit':1,'classical_bit':1}],
       'unmeasured_logical_qubits':[0]}
    c=stim.Circuit('R 0 1 2\nTICK\nM 0 1 2\nOBSERVABLE_INCLUDE(0) rec[-3] rec[-2]\nOBSERVABLE_INCLUDE(1) rec[-2]\nOBSERVABLE_INCLUDE(2) rec[-1]')
    # Internal outputs Z0Z1,Z1,Z2, so q2 maps to row2 and q1 to row1.
    m={'external_flows':['ZZIZZI','IZIIZI','IIZIIZ'],'input_bases':'zzz','output_bases':'zzz'}
    v,meta=original_output_view(c,m,p)
    assert v.num_observables==2 and v.num_measurements==c.num_measurements and v.num_ticks==1
    assert meta['external_flows']==['IIZIIZ','IZIIZI'] and meta['original_output_masks']==[4,2]
    assert [i for i in v.flattened() if i.name!='OBSERVABLE_INCLUDE']==[i for i in c.flattened() if i.name!='OBSERVABLE_INCLUDE']
    q=deepcopy(p);q['terminal_readout']=[{'qubit':0,'classical_bit':0}]
    _,b=original_output_view(c,m,q)
    assert b['original_output_masks']==[3] and b['external_flows']==['ZIIZII']


def test_incomplete_internal_basis_is_rejected():
    p={'logical_qubits':3,'terminal_readout':[{'qubit':1,'classical_bit':0}], 'unmeasured_logical_qubits':[0,2]}
    with pytest.raises(ValueError,match='Full internal'):
        original_output_view(stim.Circuit(),{'external_flows':[]},p)
