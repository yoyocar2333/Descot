from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from composition import generate_chain,validate_chain
from surgery import add_noise

@pytest.mark.parametrize('basis', ['x','z'])
@pytest.mark.parametrize('count', [2,3])
def test_continuous_chain_action_and_faults(basis,count):
    circuit,meta=generate_chain(basis,3,1,count)
    result=validate_chain(circuit,meta,64)
    assert result['external_logical_action_passed']
    assert result['zero_noise_and_signed_inputs_passed']
    assert meta['expected_logical_action']==('identity' if count==2 else 'CNOT')
    assert circuit.num_observables==2
    assert circuit.num_ticks>83
    assert len(add_noise(circuit,.001).shortest_graphlike_error())==3

def test_long_bridge_composes_without_extra_time():
    circuit,meta=generate_chain('z',3,3,2)
    assert circuit.num_ticks==146
    assert circuit.num_qubits==137
    assert validate_chain(circuit,meta,64)['zero_noise_and_signed_inputs_passed']

def test_invalid_chain_domain_rejected():
    with pytest.raises(ValueError):generate_chain('z',3,1,0)
    with pytest.raises(ValueError):generate_chain('y',3,1,2)
