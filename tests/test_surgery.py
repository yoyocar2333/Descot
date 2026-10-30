from pathlib import Path
import sys
import numpy as np
import pytest
from tqec import Basis,compile_block_graph
from tqec.gallery import cnot
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from surgery import generate,validate_ideal,add_noise,cnot_graph

@pytest.fixture(scope='module')
def circuit():return generate('z',3,1)

def test_base_graph_is_gallery_cnot():
    from tqec.utils.position import Position3D
    ports=[Position3D(0,0,0),Position3D(1,1,0),Position3D(0,0,3),Position3D(1,1,3)]
    a=cnot_graph('z',1);b=cnot(Basis.Z)
    assert {s.external_stabilizer(ports) for s in a.find_correlation_surfaces()}=={s.external_stabilizer(ports) for s in b.find_correlation_surfaces()}

def test_signed_input_truth_and_final_flip(circuit):
    c,m=circuit
    result=validate_ideal(c,m,256)
    assert result['zero_noise_and_signed_inputs_passed']
    assert [x['observable_parities'] for x in result['signed_inputs']]==[[0,0],[0,1],[1,0],[1,1]]

def test_noiseless_determinism(circuit):
    c,_=circuit;d,o=c.compile_detector_sampler(seed=12).sample(1000,separate_observables=True)
    assert not np.any(d) and not np.any(o)

def test_graphlike_distance(circuit):
    c,_=circuit
    assert len(add_noise(c,.001).shortest_graphlike_error())==3

def test_spatial_bridge_preserves_flows_and_time(circuit):
    c,m=circuit;long,meta=generate('z',3,3)
    assert meta['external_flows']==m['external_flows']
    assert long.num_ticks==c.num_ticks
    assert long.num_qubits>c.num_qubits
    assert validate_ideal(long,meta,64)['zero_noise_and_signed_inputs_passed']
    assert len(add_noise(long,.001).shortest_graphlike_error())==3

def test_invalid_settings_rejected():
    with pytest.raises(ValueError):generate('z',4)
    with pytest.raises(ValueError):cnot_graph('z',4)
