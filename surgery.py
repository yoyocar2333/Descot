"""TQEC-backed lattice-surgery CNOT calibration, with explicit provenance.

The base block graph is adapted from tqec.gallery.cnot (Apache-2.0), pinned
at 50fa2210597632a79bd266b56a5fb8d9b00747bb. Our extension subdivides its
horizontal spatial bridge into `span` adjacent blocks and validates flows.
This is not yet a translator for arbitrary DASCOT routes.
"""
from pathlib import Path
import hashlib
import json
import stim
import numpy as np
from tqec import Basis,NoiseModel,compile_block_graph
from tqec.computation.block_graph import BlockGraph
from tqec.computation.cube import ZXCube
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction

TQEC_COMMIT='50fa2210597632a79bd266b56a5fb8d9b00747bb'


def cnot_graph(basis='z',span=1):
    if basis not in ['x','z',None] or span not in [1,2,3]:
        raise ValueError('Use X/Z (or open ports) and validated bridge spans 1,2,3')
    g=BlockGraph(f'CNOT, spatial bridge span {span}')
    nodes=[((0,0,0),'P','In_Control'),((0,0,1),'ZXX',''),((0,0,2),'ZXZ',''),((0,0,3),'P','Out_Control'),
           ((0,1,1),'ZXX',''),((0,1,2),'ZXZ',''),((span,1,0),'P','In_Target'),
           ((span,1,1),'ZXZ',''),((span,1,2),'ZXZ',''),((span,1,3),'P','Out_Target')]
    for pos,kind,label in nodes:g.add_cube(Position3D(*pos),kind,label)
    for a,b in [(0,1),(1,2),(2,3),(1,4),(4,5),(6,7),(7,8),(8,9)]:
        g.add_pipe(Position3D(*nodes[a][0]),Position3D(*nodes[b][0]))
    for x in range(1,span):g.add_cube(Position3D(x,1,2),'ZXZ')
    for x in range(span):g.add_pipe(Position3D(x,1,2),Position3D(x+1,1,2))
    if basis is not None:
        g.fill_ports(ZXCube.from_str('ZXX' if basis=='x' else 'ZXZ'))
    return g


def generate(basis,distance,span=1,temporal_factor=1):
    if distance not in [3,5] or temporal_factor not in [1,2]:
        raise ValueError('Validated distances 3/5 and temporal factors 1/2')
    graph=cnot_graph(basis,span)
    surfaces=graph.find_correlation_surfaces()
    ports=[Position3D(0,0,0),Position3D(span,1,0),Position3D(0,0,3),Position3D(span,1,3)]
    external=[s.external_stabilizer(ports) for s in surfaces]
    compiled=compile_block_graph(graph,observables=surfaces,
                                 block_temporal_height=LinearFunction(2*temporal_factor,-1))
    circuit=compiled.generate_stim_circuit(k=(distance-1)//2,database_path=None)
    meta={'basis':basis,'distance':distance,'bridge_span_blocks':span,'temporal_factor':temporal_factor,
          'bulk_repetitions_per_block':temporal_factor*(distance-1)-1,
          'external_flows':external,'flow_port_order':['in_control','in_target','out_control','out_target'],
          'tqec_commit':TQEC_COMMIT,'tqec_convention':'FIXED_BULK_CONVENTION default',
          'num_qubits':circuit.num_qubits,'num_detectors':circuit.num_detectors,
          'num_observables':circuit.num_observables,'num_ticks':circuit.num_ticks,
          'scope':'One TQEC lattice-surgery CNOT with basis-specific initialization/readout. Not full-process fidelity or arbitrary DASCOT route lowering.'}
    return circuit,meta


def qubit_coords(circuit):
    return {q:tuple(v[:2]) for q,v in circuit.get_final_qubit_coordinates().items()}


def patch_data(circuit,distance,span,which):
    coords=qubit_coords(circuit);offset=0 if which=='control' else (2*distance+2)*span
    oy=0 if which=='control' else 2*distance+2
    return [q for q,(x,y) in coords.items() if x%2==1 and y%2==1 and offset<x<offset+2*distance and oy<y<oy+2*distance]


def signed_input(circuit,basis,distance,span,control_bit,target_bit):
    """Change actual input eigenvalues, retaining the unmodified converter."""
    out=stim.Circuit();inserted=False
    flips=[]
    for which,bit in [('control',control_bit),('target',target_bit)]:
        data=patch_data(circuit,distance,span,which)
        if len(data)!=distance**2:raise ValueError('Input patch data identification failed')
        if bit:flips.extend(data)
    for inst in circuit.flattened():
        if not inserted and inst.name=='TICK':
            if flips:out.append('Z' if basis=='x' else 'X',flips)
            inserted=True
        out.append(inst)
    if not inserted:raise ValueError('No initial moment')
    return out


def inject_final_logical_flip(circuit,basis,distance,span):
    data=set(patch_data(circuit,distance,span,'control'))
    out=stim.Circuit();insertions=0
    for inst in circuit.flattened():
        if inst.name==('MX' if basis=='x' else 'M') and data.issubset({t.value for t in inst.targets_copy() if t.is_qubit_target}):
            out.append('Z_ERROR' if basis=='x' else 'X_ERROR',sorted(data),1)
            insertions+=1
        out.append(inst)
    if insertions!=1:raise ValueError(f'Expected one final readout, found {insertions}')
    return out


def validate_ideal(circuit,meta,shots=256):
    basis=meta['basis'];d=meta['distance'];span=meta['bridge_span_blocks']
    flow_sets={'x':{'XIXX','IXIX','XXXI'},'z':{'ZIZI','IZZZ','ZZIZ'}}
    if len(set(meta['external_flows']))!=2 or not set(meta['external_flows']).issubset(flow_sets[basis]):
        raise AssertionError('External flow is inconsistent with a CNOT')
    converter=circuit.compile_m2d_converter()
    signed=[]
    for a in [0,1]:
        for b in [0,1]:
            changed=signed_input(circuit,basis,d,span,a,b)
            samples=changed.compile_sampler(seed=123).sample(shots)
            dets,obs=converter.convert(measurements=samples,separate_observables=True)
            expected=np.array([(a*(f[0]!='I')+b*(f[1]!='I'))%2 for f in meta['external_flows']],dtype=bool)
            if np.any(dets) or not np.all(obs==expected):
                raise AssertionError(f'Signed input flow check failed, basis={basis}, a={a}, b={b}, expected={expected}, observed={np.unique(obs,axis=0)}')
            signed.append({'input_signs':[a,b],'observable_parities':expected.astype(int).tolist(),'shots':shots})
    dets,obs=inject_final_logical_flip(circuit,basis,d,span).compile_detector_sampler(seed=123).sample(shots,separate_observables=True)
    expected=np.array([f[2]!='I' for f in meta['external_flows']],dtype=bool)
    if np.any(dets) or not np.all(obs==expected):raise AssertionError('Final logical flip test failed')
    return {'zero_noise_and_signed_inputs_passed':True,'signed_inputs':signed,'final_logical_flip_observables':expected.astype(int).tolist()}


def add_noise(circuit,p):
    return NoiseModel.uniform_depolarizing(p).noisy_circuit(circuit)
