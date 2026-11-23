"""Fixed author BFS/MITM kernel -> validated two-slice TQEC geometry.

This is a path-kernel control with an explicit coordinate adaptation, not a
reproduction of either complete Hamada scheduler or the old paper's 3D Dijkstra.
Frozen backend/pools remain byte-for-byte unchanged.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time

from tqec import compile_block_graph
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction
from public_clifford import graph_program, positions_for, validate_plan
from schedule_circuit import component_correlation_surfaces

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / 'third_party/hamada_path_2026-11-23'


def build_oracle(binary):
    manifest = json.loads((VENDOR/'manifest.json').read_text())
    for f in manifest['files']:
        if hashlib.sha256((VENDOR/f['path']).read_bytes()).hexdigest() != f['sha256']:
            raise ValueError('Fixed author path header differs')
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra',str(ROOT/'hamada_path_oracle.cpp'),'-o',str(binary)],check=True,capture_output=True,text=True)


def validate_path(path, positions, orientation, c, t, board, blocked=()):
    """Narrow compiler contract: one forward temporal edge with one kink.

    Rejected paths are reported; never replaced by an optimistic fixed route.
    Conservatively reserve the entire XY union for the whole physical layer.
    """
    if len(path)<4 or len(set(map(tuple,path))) != len(path):
        raise ValueError('Empty/short/self-intersecting route')
    if tuple(path[0]) != (*positions[c],0) or tuple(path[-1]) != (*positions[t],1):
        raise ValueError('Wrong route endpoints or slices')
    width,height=board;data=set(positions);blocked=set(map(tuple,blocked))
    for j,(x,y,z) in enumerate(path):
        if not (0<=x<width and 0<=y<height and z in (0,1)):
            raise ValueError('Route outside fixed hardware board')
        if (x,y) in blocked or (0<j<len(path)-1 and (x,y) in data):
            raise ValueError('Route crosses live data or reserved footprint')
    axes=[]
    for a,b in zip(path,path[1:]):
        delta=[abs(x-y) for x,y in zip(a,b)]
        if sum(delta)!=1: raise ValueError('Nonadjacent route')
        axes.append(delta.index(1))
    if axes[0] != (0 if orientation[c] else 1) or axes[-1] != (1 if orientation[t] else 0):
        raise ValueError('Route violates oriented Pauli walls')
    switches=[i for i,a in enumerate(axes) if a==2]
    if len(switches)!=1:
        raise ValueError('Only one temporal switch supported; no silent projection')
    k=switches[0]
    if k==0 or k==len(axes)-1 or path[k+1][2]-path[k][2]!=1 or axes[k-1]==axes[k+1]:
        raise ValueError('Missing forward odd kink')
    footprint={(x,y) for x,y,z in path}
    return path[:k+1],path[k+1:],footprint


def route_plan(program, plan, binary):
    positions,_=validate_plan(program,plan)
    # Board covers the complete fixed diagonal layout; no chosen concurrency cap.
    board=(max(x for x,y in positions)+1,max(y for x,y in positions)+1)
    paths={};calls=[]
    for li,layer in enumerate(plan['layers']):
        if layer['kind']!='cx': continue
        reserved=set()
        for op_id in layer['operation_ids']:
            c,t=program['operations'][op_id]['qubits']
            lines=[f'{board[0]} {board[1]} {len(positions)} {c} {t} {len(reserved)}']
            lines += [f'{x} {y} {o}' for (x,y),o in zip(positions,layer['orientation_before'])]
            lines += [f'{x} {y}' for x,y in sorted(reserved)]
            payload='\n'.join(lines)+'\n';began=time.perf_counter()
            result=subprocess.run([str(binary)],input=payload,text=True,capture_output=True,check=True)
            elapsed=time.perf_counter()-began
            rows=result.stdout.splitlines();length,kinks=map(int,rows[0].split())
            path=[list(map(int,r.split())) for r in rows[1:]]
            if length!=len(path) or kinks!=1: raise ValueError('Author returned unsupported/empty kink path')
            _,_,footprint=validate_path(path,positions,layer['orientation_before'],c,t,board,reserved)
            reserved |= footprint;paths[str(op_id)]=path
            calls.append(dict(layer_index=li,operation_id=op_id,stdin=payload,stdout=result.stdout,
                              subprocess_seconds=elapsed,author_kinks=kinks,path_vertices=length))
    return dict(base_plan=plan,paths=paths,board_xy=list(board),calls=calls,
                scope='Author BFS/MITM path kernel, two-slice coordinate adapter; full XY reservation. Not original native scheduler/3D Dijkstra.',mu=0)


def routed_graph(program, routed, input_bases=None, output_bases=None):
    plan=routed['base_plan'];positions,_=validate_plan(program,plan)
    expected={str(op['id']) for op in program['operations'] if op['name']=='cx'}
    if set(routed['paths'])!=expected: raise ValueError('Exactly every source CX must have a route')
    if routed['board_xy'] != [max(x for x,y in positions)+1,max(y for x,y in positions)+1]:
        raise ValueError('Hardware board differs')
    graph,ports,meta=graph_program(program,plan,input_bases,output_bases)
    # Keep the entire existing data lifetime/H construction and all source/frame
    # records. Replace ALL fixed ancilla geometry, not just its cost annotation.
    data=set(positions)
    for cube in list(graph.cubes):
        if (cube.position.x,cube.position.y) not in data: graph.remove_cube(cube.position)
    footprints=[];start=0
    for layer in plan['layers']:
        if layer['kind']=='virtual_or_readout':continue
        reserved=set()
        for op_id in layer['operation_ids']:
            op=program['operations'][op_id]
            if op['name']!='cx':continue
            first,second,footprint=validate_path(routed['paths'][str(op_id)],positions,layer['orientation_before'],*op['qubits'],routed['board_xy'],reserved)
            reserved|=footprint
            for arm,vertical,horizontal,corner in [(first,'ZXX','XZX','ZZX'),(second,'XZZ','ZXZ','XXZ')]:
                for j,(x,y,z) in enumerate(arm):
                    pos=Position3D(x,y,start+z+1)
                    if pos in graph:continue
                    axes=set()
                    if j:axes.add(int(arm[j-1][1]!=y))
                    if j+1<len(arm):axes.add(int(arm[j+1][1]!=y))
                    kind=corner if len(axes)==2 else vertical if 1 in axes else horizontal
                    graph.add_cube(pos,kind)
                for a,b in zip(arm,arm[1:]):graph.add_pipe(Position3D(a[0],a[1],start+a[2]+1),Position3D(b[0],b[1],start+b[2]+1))
            pivot=first[-1]
            graph.add_pipe(Position3D(pivot[0],pivot[1],start+1),Position3D(pivot[0],pivot[1],start+2))
            footprints.append(dict(operation_id=op_id,reserved_xy=[list(p) for p in sorted(footprint)],
                control_arm=[p[:2] for p in first],target_arm=[p[:2] for p in second],start_block_z=start,end_block_z=start+3))
        start+=3
    graph.validate()
    meta.update(profile_id='complete_hxcx_hamada_path_two_slice_v1',gate_footprints=footprints,
                routed_plan=routed,path_kernel_commit='dcaa249878ff365162cf4df930a367dca5fcf5a4')
    return graph,ports,meta


def generate_routed(program,routed,input_bases=None,output_bases=None):
    graph,ports,meta=routed_graph(program,routed,input_bases,output_bases)
    surfaces=component_correlation_surfaces(graph)
    compiled=compile_block_graph(graph,observables=surfaces,block_temporal_height=LinearFunction(2,-1))
    circuit=compiled.generate_stim_circuit(k=1,database_path=None)
    meta.update(external_flows=[s.external_stabilizer(ports) for s in surfaces],
        num_qubits=circuit.num_qubits,num_ticks=circuit.num_ticks,num_observables=circuit.num_observables,num_detectors=circuit.num_detectors)
    return circuit,meta
