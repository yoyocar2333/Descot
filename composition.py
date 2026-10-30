"""Continuous same-pair CNOT chains, using upstream TQEC graph composition.

This validates a small composition family before any arbitrary-route lowering.
It compiles one connected circuit; it does not concatenate destructive-readout
gadget circuits or multiply independently measured gadget survival rates.
"""
import numpy as np
from tqec import compile_block_graph
from tqec.computation.cube import ZXCube
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction
from surgery import cnot_graph, signed_input, inject_final_logical_flip, TQEC_COMMIT

def generate_chain(basis, distance, span=1, count=2):
    if basis not in ['x', 'z'] or distance not in [3, 5] or count not in [1, 2, 3]:
        raise ValueError('Validated domain: X/Z, d=3/5, count=1/2/3')
    graph = cnot_graph(None, span)
    for _ in range(count-1):
        graph = graph.compose(cnot_graph(None, span), 'Out_Control', 'In_Control')
    # compose() glues both overlapping output/input ports automatically.
    assert set(graph.ports) == {'In_Control', 'In_Target', 'Out_Control', 'Out_Target'}
    ports = [Position3D(0,0,0), Position3D(span,1,0),
             Position3D(0,0,3*count), Position3D(span,1,3*count)]
    assert [graph.ports[k] for k in ['In_Control','In_Target','Out_Control','Out_Target']] == ports
    graph.fill_ports(ZXCube.from_str('ZXX' if basis == 'x' else 'ZXZ'))
    surfaces = graph.find_correlation_surfaces()
    flows = [s.external_stabilizer(ports) for s in surfaces]
    compiled = compile_block_graph(graph, observables=surfaces,
                                   block_temporal_height=LinearFunction(2,-1))
    circuit = compiled.generate_stim_circuit(k=(distance-1)//2, database_path=None)
    meta = {'basis':basis, 'distance':distance, 'bridge_span_blocks':span,
            'cnot_count':count, 'expected_logical_action':'identity' if count%2==0 else 'CNOT',
            'external_flows':flows, 'flow_port_order':['in_control','in_target','out_control','out_target'],
            'tqec_commit':TQEC_COMMIT, 'temporal_factor':1,
            'num_qubits':circuit.num_qubits, 'num_ticks':circuit.num_ticks,
            'num_detectors':circuit.num_detectors, 'num_observables':circuit.num_observables,
            'scope':'Continuous same-pair CNOT chain with no intermediate logical readout/reinitialization. Not an arbitrary DASCOT schedule translator.'}
    return circuit, meta

def validate_chain(circuit, meta, shots=128):
    basis=meta['basis']; count=meta['cnot_count']; flows=meta['external_flows']
    assert len(flows) == 2 and len(set(flows)) == 2
    inputs=[tuple(p!='I' for p in f[:2]) for f in flows]
    assert all(any(row) for row in inputs) and inputs[0]!=inputs[1], 'Input Pauli generators must be independent'
    # Check each external Pauli relation against the classical basis action.
    for a in [0,1]:
        for b in [0,1]:
            out_a, out_b = a,b
            if count%2:
                if basis == 'z':out_b ^= a
                else:out_a ^= b
            for flow in flows:
                assert set(flow) <= {basis.upper(),'I'} and len(flow)==4
                parity=sum(bit for bit,pauli in zip([a,b,out_a,out_b],flow) if pauli!='I')%2
                if parity:raise AssertionError('External flow does not match expected logical action')
    converter=circuit.compile_m2d_converter(); signed=[]
    for a in [0,1]:
        for b in [0,1]:
            changed=signed_input(circuit,basis,meta['distance'],meta['bridge_span_blocks'],a,b)
            samples=changed.compile_sampler(seed=123).sample(shots)
            dets,obs=converter.convert(measurements=samples,separate_observables=True)
            expected=np.array([(a*(f[0]!='I')+b*(f[1]!='I'))%2 for f in flows],dtype=bool)
            assert not np.any(dets) and np.all(obs==expected), 'Signed input check failed'
            signed.append({'input_signs':[a,b], 'observable_parities':expected.astype(int).tolist(), 'shots':shots})
    fault=inject_final_logical_flip(circuit,basis,meta['distance'],meta['bridge_span_blocks'])
    dets,obs=fault.compile_detector_sampler(seed=123).sample(shots,separate_observables=True)
    expected=np.array([f[2]!='I' for f in flows],dtype=bool)
    assert not np.any(dets) and np.all(obs==expected), 'Known final flip check failed'
    assert any(expected), 'Final control fault must be observable'
    return {'zero_noise_and_signed_inputs_passed':True,'external_logical_action_passed':True,
            'signed_inputs':signed,'final_logical_flip_observables':expected.astype(int).tolist()}
