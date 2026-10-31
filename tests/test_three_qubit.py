from functools import lru_cache
from pathlib import Path
import copy
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from three_qubit import basis_action,graph_three_qubit,generate_three_qubit,validate_three_qubit
from surgery import add_noise

@lru_cache
def circuit(basis,span,idle):return generate_three_qubit(basis,3,span,idle)

@pytest.mark.parametrize('basis,inputs,outputs',[
    ('z',[1,0,0],[1,1,1]),('x',[0,1,0],[1,1,0])])
def test_non_cancelling_truth_examples(basis,inputs,outputs):
    assert basis_action(basis,inputs)==outputs

@pytest.mark.parametrize('span',[1,3])
@pytest.mark.parametrize('idle',[0,1])
def test_all_three_live_wires_have_continuous_storage(span,idle):
    graph,ports=graph_three_qubit('z',span,idle)
    assert [p.z for p in ports]==[0]*3+[6+idle]*3
    from tqec.utils.position import Position3D
    for q in range(3):
        for z in range(6+idle):
            assert graph.has_pipe_between(Position3D(q*span,q,z),Position3D(q*span,q,z+1))

@pytest.mark.parametrize('basis',['x','z'])
@pytest.mark.parametrize('idle',[0,1])
def test_eight_inputs_three_final_faults_and_distance(basis,idle):
    c,m=circuit(basis,1,idle)
    result=validate_three_qubit(c,m,64)
    assert len(result['signed_inputs'])==8
    assert len(result['final_logical_faults'])==3
    assert len(add_noise(c,.001).shortest_graphlike_error())==3
    assert c.num_observables==3

@pytest.mark.parametrize('basis',['x','z'])
def test_long_span_and_wait_preserve_logical_action(basis):
    c,m=circuit(basis,3,1)
    short,_=circuit(basis,1,1)
    assert c.num_ticks==short.num_ticks and c.num_qubits>short.num_qubits
    assert validate_three_qubit(c,m,64)['all_eight_signed_inputs_passed']
    assert len(add_noise(c,.001).shortest_graphlike_error())==3

def test_identity_flow_substitution_is_rejected():
    c,m=circuit('z',1,0);wrong=copy.deepcopy(m)
    wrong['external_flows']=['ZIIZII','IZIIZI','IIZIIZ']
    with pytest.raises(AssertionError,match='intended non-cancelling'):
        validate_three_qubit(c,wrong,8)

def test_unsupported_conditions_rejected():
    with pytest.raises(ValueError):generate_three_qubit('z',5)
    with pytest.raises(ValueError):generate_three_qubit('z',3,2)
    with pytest.raises(ValueError):generate_three_qubit('z',3,1,2)
