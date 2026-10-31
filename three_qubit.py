"""Three-live-qubit CNOT chain with explicit spectator storage.

TQEC supplies graph composition and compilation. We add a supported geometry,
align every logical input/output in time, and check its non-cancelling action.
Supported experiment: d=3, bridge spans 1/3, zero/one extra storage block.
"""
from itertools import product
import numpy as np
import stim
from tqec import compile_block_graph
from tqec.computation.block_graph import BlockGraph
from tqec.computation.cube import ZXCube
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction
from surgery import cnot_graph, TQEC_COMMIT


def _labelled_cnot(prefix, span):
    source=cnot_graph(None,span)
    graph=BlockGraph(prefix+' CNOT')
    for cube in source.cubes:
        graph.add_cube(cube.position,cube.kind,prefix+'_'+cube.label if cube.is_port else '')
    for pipe in source.pipes:
        graph.add_pipe(pipe.u.position,pipe.v.position,pipe.kind)
    return graph


def _extend_port(graph,label,end_z):
    start=graph.ports[label]
    if end_z==start.z:return
    direction=1 if end_z>start.z else -1
    # Convert a logical boundary to a storage junction before extending it.
    graph.fill_ports({label:ZXCube.from_str('ZXZ')})
    previous=start
    for z in range(start.z+direction,end_z+direction,direction):
        pos=Position3D(start.x,start.y,z)
        graph.add_cube(pos,'P' if z==end_z else 'ZXZ',label if z==end_z else '')
        graph.add_pipe(previous,pos);previous=pos


def graph_three_qubit(basis,span=1,idle_blocks=0):
    if basis not in ['x','z'] or span not in [1,3] or idle_blocks not in [0,1]:
        raise ValueError('Supported X/Z, spans 1/3, idle_blocks 0/1')
    first=_labelled_cnot('A',span)
    for label in ['A_Out_Control','A_Out_Target']:
        _extend_port(first,label,3+idle_blocks)
    graph=first.compose(_labelled_cnot('B',span),'A_Out_Target','B_In_Control')
    end=6+idle_blocks
    # q0 survives the second CNOT; q2 must exist before its own first gate.
    _extend_port(graph,'A_Out_Control',end)
    _extend_port(graph,'B_In_Target',0)
    labels=['A_In_Control','A_In_Target','B_In_Target',
            'A_Out_Control','B_Out_Control','B_Out_Target']
    ports=[graph.ports[label] for label in labels]
    expected=[Position3D(i*span,i,z) for z in [0,end] for i in range(3)]
    if ports!=expected:raise AssertionError('Logical ports must share common start/end times')
    graph.fill_ports(ZXCube.from_str('ZXX' if basis=='x' else 'ZXZ'))
    graph.validate()
    return graph,ports


def generate_three_qubit(basis,distance=3,span=1,idle_blocks=0):
    if distance!=3:raise ValueError('This validated pilot is limited to d=3')
    graph,ports=graph_three_qubit(basis,span,idle_blocks)
    surfaces=graph.find_correlation_surfaces()
    compiled=compile_block_graph(graph,observables=surfaces,
                                 block_temporal_height=LinearFunction(2,-1))
    circuit=compiled.generate_stim_circuit(k=1,database_path=None)
    meta={'geometry_id':'three_live_qubit_diagonal_chain_v1','basis':basis,'distance':distance,
          'bridge_span_blocks':span,'idle_blocks':idle_blocks,
          'logical_gates':[[0,1],[1,2]],'logical_qubits':3,
          'external_flows':[s.external_stabilizer(ports) for s in surfaces],
          'flow_port_order':['in_q0','in_q1','in_q2','out_q0','out_q1','out_q2'],
          'logical_block_xy':[[i*span,i] for i in range(3)],
          'input_z':0,'output_z':6+idle_blocks,
          'spectator_memory':{'q0':'stored through second CNOT','q2':'stored before second CNOT',
                              'intergate_extra_blocks_all_three_qubits':idle_blocks},
          'num_qubits':circuit.num_qubits,'num_ticks':circuit.num_ticks,
          'num_observables':circuit.num_observables,'num_detectors':circuit.num_detectors,
          'tqec_commit':TQEC_COMMIT,
          'scope':'Full basis-specific non-cancelling three-qubit CNOT chain, including spectator storage. Not arbitrary DASCOT route lowering or process fidelity.'}
    return circuit,meta


def basis_action(basis,bits):
    """Apply CNOT(0,1), then CNOT(1,2), to X/Z product-state eigenvalue bits."""
    if basis not in ['x','z']:raise ValueError('Use X/Z')
    bits=list(bits)
    if len(bits)!=3:raise ValueError('Expected three logical eigenvalue bits')
    for control,target in [(0,1),(1,2)]:
        if basis=='z':bits[target]^=bits[control]
        else:bits[control]^=bits[target]
    return bits


def patch_data(circuit,meta,index):
    d=meta['distance'];bx,by=meta['logical_block_xy'][index]
    ox,oy=(2*d+2)*bx,(2*d+2)*by
    data=[q for q,coord in circuit.get_final_qubit_coordinates().items()
          if len(coord)>=2 and coord[0]%2==1 and coord[1]%2==1
          and ox<coord[0]<ox+2*d and oy<coord[1]<oy+2*d]
    if len(data)!=d*d:raise AssertionError('Logical patch identification failed')
    return sorted(data)


def change_input(circuit,meta,bits):
    out=stim.Circuit();inserted=False
    flips=[q for i,bit in enumerate(bits) if bit for q in patch_data(circuit,meta,i)]
    for inst in circuit.flattened():
        if not inserted and inst.name=='TICK':
            if flips:out.append('Z' if meta['basis']=='x' else 'X',flips)
            inserted=True
        out.append(inst)
    if not inserted:raise AssertionError('Missing initialization moment')
    return out


def final_flip(circuit,meta,index):
    data=set(patch_data(circuit,meta,index));out=stim.Circuit();insertions=0
    for inst in circuit.flattened():
        if inst.name==('MX' if meta['basis']=='x' else 'M') and data.issubset(
                {t.value for t in inst.targets_copy() if t.is_qubit_target}):
            out.append('Z_ERROR' if meta['basis']=='x' else 'X_ERROR',sorted(data),1)
            insertions+=1
        out.append(inst)
    if insertions!=1:raise AssertionError('Expected one logical final readout')
    return out


def _rank_binary(rows):
    rows=[sum(int(v)<<i for i,v in enumerate(row)) for row in rows];rank=0
    for bit in range(3):
        pivot=next((i for i in range(rank,len(rows)) if rows[i]&(1<<bit)),None)
        if pivot is None:continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        for i in range(len(rows)):
            if i!=rank and rows[i]&(1<<bit):rows[i]^=rows[rank]
        rank+=1
    return rank


def validate_three_qubit(circuit,meta,shots=128):
    flows=meta['external_flows'];basis=meta['basis']
    if len(flows)!=3 or circuit.num_observables!=3:raise AssertionError('Expected three independent observables')
    if any(len(f)!=6 or not set(f)<={basis.upper(),'I'} for f in flows):raise AssertionError('Invalid basis flow')
    if _rank_binary([[p!='I' for p in f[:3]] for f in flows])!=3:raise AssertionError('Input flows are not independent')
    converter=circuit.compile_m2d_converter();signed=[]
    for bits in product([0,1],repeat=3):
        outputs=basis_action(basis,bits)
        for flow in flows:
            if sum(b for b,p in zip([*bits,*outputs],flow) if p!='I')%2:
                raise AssertionError('Flow differs from the intended non-cancelling circuit')
        raw=change_input(circuit,meta,bits).compile_sampler(seed=123).sample(shots)
        dets,obs=converter.convert(measurements=raw,separate_observables=True)
        expected=np.array([sum(b for b,p in zip(bits,f[:3]) if p!='I')%2 for f in flows],dtype=bool)
        if np.any(dets) or not np.all(obs==expected):raise AssertionError('Signed-input check failed')
        signed.append({'input_signs':list(bits),'output_signs':outputs,
                       'observable_parities':expected.astype(int).tolist(),'shots':shots})
    faults=[]
    for i in range(3):
        dets,obs=final_flip(circuit,meta,i).compile_detector_sampler(seed=123).sample(shots,separate_observables=True)
        expected=np.array([f[3+i]!='I' for f in flows],dtype=bool)
        if np.any(dets) or not np.all(obs==expected) or not np.any(expected):raise AssertionError('Final fault check failed')
        faults.append({'logical_qubit':i,'observable_flips':expected.astype(int).tolist(),'shots':shots})
    return {'external_logical_action_passed':True,'all_eight_signed_inputs_passed':True,
            'signed_inputs':signed,'final_logical_faults':faults,
            'common_logical_lifetime_block_z':[meta['input_z'],meta['output_z']]}
