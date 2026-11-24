"""Full-source paper projection policy using fixed author's search/priority code.

Native voxel heights are retained; no flattening to old layer templates.
The H/X/readout time policy is an explicit adapter, not the native full loop.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time

from tqec import compile_block_graph
from tqec.computation.block_graph import BlockGraph
from tqec.computation.cube import ZXCube
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction
from public_clifford import positions_for
from schedule_circuit import component_correlation_surfaces
from surgery import TQEC_COMMIT

ROOT=Path(__file__).resolve().parent
VENDOR=ROOT/'third_party/hamada_projection_2026-11-24'
KINDS=('XXZ','XZX','XZZ','ZXX','ZXZ','ZZX')


def build_driver(binary):
    for row in json.loads((VENDOR/'manifest.json').read_text())['files']:
        if hashlib.sha256((VENDOR/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Fixed native projection source changed')
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra',str(ROOT/'hamada_projection_driver.cpp'),'-o',str(binary)],check=True,capture_output=True,text=True)


def schedule(program,binary,policy='height_priority',spacing=3):
    if policy not in ('source_order','height_priority'):raise ValueError('Unknown frozen policy')
    lines=[f"{program['logical_qubits']} {len(program['operations'])} {spacing}"]
    for op in program['operations']:
        lines.append(' '.join(map(str,[op['name'],len(op['qubits']),*op['qubits'],len(op['predecessors']),*op['predecessors']])))
    payload='\n'.join(lines)+'\n';began=time.perf_counter()
    run=subprocess.run([str(binary),policy],input=payload,text=True,capture_output=True,timeout=60)
    if run.returncode:raise ValueError(f'Full-source driver rejected ({run.returncode}): {run.stderr}')
    seconds=time.perf_counter()-began;rows=iter(run.stdout.splitlines());events=[];end=None
    for line in rows:
        words=line.split()
        if words[0]=='END':end=int(words[1]);break
        tag,op_id,start,length,kinks=words
        if tag!='OP':raise ValueError('Bad native trace')
        path=[list(map(int,next(rows).split())) for _ in range(int(length))]
        before=next(rows).split();after=next(rows).split()
        if before[0]!='BEFORE' or after[0]!='AFTER':raise ValueError('Missing height trace')
        events.append(dict(operation_id=int(op_id),start=int(start),path=path,kinks=int(kinks),
                           heights_before=list(map(int,before[1:])),heights_after=list(map(int,after[1:]))))
    plan=dict(policy=policy,spacing=spacing,events=events,elapsed_height=end,mu=0)
    validate(program,plan)
    return dict(plan=plan,stdin=payload,stdout=run.stdout,stderr=run.stderr,
                routing_seconds_including_subprocess=seconds)


def validate(program,plan):
    ops=program['operations'];positions=positions_for(program['logical_qubits'],plan['spacing'])
    if {op['name'] for op in ops}-{'h','x','cx','measure','barrier'}:raise ValueError('Unsupported gate: do not delete')
    width=max(x for x,y in positions)+1;height=max(y for x,y in positions)+1
    heights=[0]*(width*height);done=set();orientation=[0]*len(positions);data=set(positions);occupied=set();trace=[]
    def index(p):return p[0]+p[1]*width
    for event in plan['events']:
        ready=[o for o in ops if o['id'] not in done and set(o['predecessors'])<=done]
        if not ready:raise ValueError('Invalid full source DAG')
        key=lambda o: o['id'] if plan['policy']=='source_order' else (max([heights[index(positions[q])] for q in o['qubits']],default=0),o['id'])
        expected=min(ready,key=key)
        if event['operation_id']!=expected['id']:raise ValueError('Source dependency/priority differs')
        if event['heights_before']!=heights:raise ValueError('Operand/ancilla height trace differs')
        op=expected;start=max([heights[index(positions[q])] for q in op['qubits']],default=0)
        if event['start']!=start:raise ValueError('Start height differs')
        endpoints=[]
        if op['name']=='cx':
            c,t=op['qubits'];path=event['path']
            if len(path)<4 or len(set(map(tuple,path)))!=len(path):raise ValueError('Invalid native path')
            if path[0][:2]!=list(positions[c]) or path[-1][:2]!=list(positions[t]):raise ValueError('Wrong native endpoints')
            axes=[]
            for j,(x,y,z) in enumerate(path):
                if min(x,y,z)<0 or x>=width or y>=height:raise ValueError('Outside declared layout envelope')
                if (x,y) in data and j not in (0,len(path)-1):raise ValueError('Ancilla crosses live data')
                if heights[index((x,y))]>z or (x,y,z) in occupied:raise ValueError('Native voxel/lifetime overlap')
            for a,b in zip(path,path[1:]):
                diff=[abs(x-y) for x,y in zip(a,b)]
                if sum(diff)!=1:raise ValueError('Disconnected native path')
                if not axes or axes[-1]!=diff.index(1):axes.append(diff.index(1))
            if axes[0]!=(0 if orientation[c] else 1) or axes[-1]!=(1 if orientation[t] else 0):raise ValueError('Wrong oriented endpoints')
            kinks=sum(axes[i]==2 and axes[i-1]!=axes[i+1] for i in range(1,len(axes)-1))
            if kinks%2!=1 or kinks!=event['kinks']:raise ValueError('Kink condition differs')
            for x,y,z in path:heights[index((x,y))]=max(heights[index((x,y))],z+1);occupied.add((x,y,z))
            endpoints=[path[0][2],path[-1][2]]
        elif op['name']=='h':
            q=op['qubits'][0];heights[index(positions[q])]=start+3;orientation[q]^=1
        if event['heights_after']!=heights:raise ValueError('Native height update differs')
        trace.append(dict(**op,start_block_z=start,end_block_z=(start+3 if op['name']=='h' else max(endpoints)+1 if endpoints else start),endpoint_heights=endpoints))
        done.add(op['id'])
    if done!=set(range(len(ops))) or max(heights)!=plan['elapsed_height']:raise ValueError('Incomplete source or final heights')
    return positions,trace,orientation


def color_path(path,first_kind,last_kind):
    """Deterministic finite-state wall constraint solve; no Hadamards on routes.

    Six ZX cubes, ordinary matching walls on every path edge. This is geometry
    inference, not outcome fitting or a new routing/scoring algorithm.
    """
    def compatible(a,b,axis):
        walls=[d for d in range(3) if d!=axis]
        return a[walls[0]]!=a[walls[1]] and all(a[d]==b[d] for d in walls)
    choices={first_kind:[first_kind]}
    for i in range(1,len(path)):
        axis=next(d for d in range(3) if path[i][d]!=path[i-1][d]);nxt={}
        for b in ([last_kind] if i==len(path)-1 else KINDS):
            options=[v+[b] for a,v in choices.items() if compatible(a,b,axis)]
            if options:nxt[b]=min(options)
        choices=nxt
    if not choices:raise ValueError('Projection path has no supported no-Hadamard cube coloring')
    return min(choices.values())


def graph(program,plan,input_bases=None,output_bases=None):
    positions,trace,orientation=validate(program,plan);n=len(positions);end=plan['elapsed_height']+1
    input_bases=input_bases or 'z'*n;output_bases=output_bases or 'z'*n
    if len(input_bases)!=n or len(output_bases)!=n or set(input_bases+output_bases)-{'x','z'}:raise ValueError('Unsupported boundaries')
    kinds={};frame_x=[0]*n;frame_z=[0]*n;physical_orientation=[0]*n
    for q,(x,y) in enumerate(positions):
        current=0
        hs=sorted(e['start'] for e in plan['events'] if program['operations'][e['operation_id']]['name']=='h' and program['operations'][e['operation_id']]['qubits']==[q])
        for z in range(end+1):
            if z in {t+2 for t in hs}:
                kinds[(x,y,z)]='ZXX' if current else 'XZX';current^=1
            else:kinds[(x,y,z)]='XZZ' if current else 'ZXZ'
    assigned=[];events=[]
    for event,entry in zip(plan['events'],trace):
        op=program['operations'][event['operation_id']];qs=op['qubits'];before=list(physical_orientation)
        if op['name']=='x':frame_x[qs[0]]^=1
        elif op['name']=='h':
            q=qs[0];frame_x[q],frame_z[q]=frame_z[q],frame_x[q];physical_orientation[q]^=1
        elif op['name']=='cx':
            c,t=qs;path=[[x,y,z+1] for x,y,z in event['path']]
            first='XZX' if before[c] else 'ZXX';last='XZZ' if before[t] else 'ZXZ'
            colors=color_path(path,first,last)
            for p,kind in zip(path,colors):
                if tuple(p) in kinds and tuple(p) not in (tuple(path[0]),tuple(path[-1])):raise ValueError('Path intersects existing geometry')
                kinds[tuple(p)]=kind
            assigned.append(dict(operation_id=op['id'],path_block_xyz=path,cube_kinds=colors,native_kinks=event['kinks']))
            frame_x[t]^=frame_x[c];frame_z[c]^=frame_z[t]
        entry={**entry,'frame_x_after':list(frame_x),'frame_z_after':list(frame_z)}
        if op['name']=='measure':entry.update(source_ready_block_z=entry['start_block_z'],start_block_z=end,end_block_z=end)
        events.append(entry)
    g=BlockGraph('Complete H/X/CX source with native projection heights')
    for p,kind in sorted(kinds.items()):
        q=positions.index(p[:2]) if p[:2] in positions else None
        label=f'in_q{q}' if q is not None and p[2]==0 else f'out_q{q}' if q is not None and p[2]==end else ''
        g.add_cube(Position3D(*p),'P' if label else kind,label)
    for x,y in positions:
        for z in range(end):g.add_pipe(Position3D(x,y,z),Position3D(x,y,z+1))
    for row in assigned:
        for a,b in zip(row['path_block_xyz'],row['path_block_xyz'][1:]):
            u,v=Position3D(*a),Position3D(*b)
            if g.has_pipe_between(u,v):raise ValueError('Duplicate route edge')
            g.add_pipe(u,v)
            if g.get_pipe(u,v).kind.has_hadamard:raise ValueError('Unexpected route Hadamard')
    ports=[g.ports[f'{side}_q{q}'] for side in ('in','out') for q in range(n)]
    fill={}
    for side,bases,orient in [('in',input_bases,[0]*n),('out',output_bases,orientation)]:
        for q,(b,o) in enumerate(zip(bases,orient)):fill[f'{side}_q{q}']=ZXCube.from_str(('XZ' if o else 'ZX')+b.upper())
    g.fill_ports(fill);g.validate()
    return g,ports,dict(profile_id='full_source_height_projection_v1',logical_qubits=n,distance=3,
        logical_block_xy=[list(p) for p in positions],input_bases=input_bases,output_bases=output_bases,
        input_z=0,output_z=end,source_sha256=program['source_sha256'],operation_counts=program['operation_counts'],
        instruction_trace=events,routed_geometry=assigned,frame_x=frame_x,frame_z=frame_z,
        terminal_readout=program['terminal_readout'],final_orientations=orientation,tqec_commit=TQEC_COMMIT,
        projection_plan=plan,mu=0,
        timing_policy='Projection heights map explicitly to block-z vertices; H consumes 3 block-z, X virtual; readouts at common final boundary. Not native code beats or inferred QEC rounds/TICKs.')


def generate(program,plan,input_bases=None,output_bases=None):
    g,ports,meta=graph(program,plan,input_bases,output_bases)
    surfaces=component_correlation_surfaces(g)
    compiled=compile_block_graph(g,observables=surfaces,block_temporal_height=LinearFunction(2,-1))
    circuit=compiled.generate_stim_circuit(k=1,database_path=None)
    meta.update(external_flows=[s.external_stabilizer(ports) for s in surfaces],num_qubits=circuit.num_qubits,
        num_ticks=circuit.num_ticks,num_observables=circuit.num_observables,num_detectors=circuit.num_detectors)
    return circuit,meta
