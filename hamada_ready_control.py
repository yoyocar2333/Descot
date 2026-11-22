"""Paper 2401.15829v6 Alg2 ready-order policy in the declared TQEC profile.

The shortest-path primitive is REPLACED by the common fixed full footprint.
H-first closure/durations come from our backend. Not native Hamada BFS/3D.
"""
from pathlib import Path
import hashlib
import json
import subprocess

from public_clifford import cnot_paths, positions_for, validate_plan

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "third_party/hamada_dependency_2026-11-22"


def author_check(program, events, binary):
    lines = [f"{program['logical_qubits']} {len(program['operations'])}"]
    for op in program['operations']:
        lines.append(" ".join(map(str,[len(op['qubits']),*op['qubits']])))
    for event in events:
        if event[0]=='R': lines.append(" ".join(map(str,['R',len(event[1]),*event[1]])))
        else: lines.append(f"P {event[1]}")
    lines.append('F')
    payload='\n'.join(lines)+'\n'
    result=subprocess.run([str(binary)],input=payload,text=True,capture_output=True)
    if result.returncode:
        raise ValueError(f"Original C++ DAG oracle disagrees ({result.returncode})")
    queries,processed=map(int,result.stdout.split())
    return dict(ready_queries=queries,processed_source_instructions=processed,
                stdin=payload,stdout=result.stdout,input_sha256=hashlib.sha256(payload.encode()).hexdigest())


def build_oracle(binary):
    manifest=json.loads((VENDOR/'manifest.json').read_text())
    for row in manifest['files']:
        if hashlib.sha256((VENDOR/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Original author header differs')
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra',str(ROOT/'hamada_dependency_oracle.cpp'),'-o',str(binary)],check=True,capture_output=True,text=True)


def schedule(program, budget=48, spacing=3):
    if type(budget) is not int or budget<1: raise ValueError('Positive front budget required')
    if {o['name'] for o in program['operations']}-{'h','x','cx','measure','barrier'}:
        raise ValueError('Unsupported source gate must not be dropped')
    ops=program['operations'];done=set();orientation=[0]*program['logical_qubits']
    positions=positions_for(program['logical_qubits'],spacing);layers=[];events=[];fronts=[]
    while len(done)<len(ops):
        ready=[o for o in ops if o['id'] not in done and set(o['predecessors'])<=done]
        if not ready: raise ValueError('Invalid complete source DAG')
        events.append(['R',[o['id'] for o in ready]])
        instant=[o for o in ready if o['name'] in ('x','measure','barrier')]
        hs=[o for o in ready if o['name']=='h']
        if instant: chosen=instant;kind='virtual_or_readout'
        elif hs: chosen=hs;kind='h'
        else:
            chosen=[];reserved=set();attempts=[]
            # Paper Alg2: snapshot of all ready indices, ascending ORIGINAL id.
            for op in ready:
                footprint=cnot_paths(*op['qubits'],positions,orientation)[2]
                accepted=not (reserved & footprint)
                attempts.append(dict(operation_id=op['id'],footprint=sorted(footprint),accepted=accepted))
                if accepted: chosen.append(op);reserved |= footprint
            if not chosen: raise ValueError('No complete-footprint progress')
            fronts.append(dict(ready_ids=[o['id'] for o in ready],chosen_ids=[o['id'] for o in chosen],
                attempts=attempts,front_evaluations=1,gate_route_calls=len(attempts),budget=budget,
                candidate_orders=[list(range(len(ready)))]))
            kind='cx'
        before=list(orientation)
        for op in chosen:
            if op['name']=='h':orientation[op['qubits'][0]]^=1
            done.add(op['id']);events.append(['P',op['id']])
        layers.append(dict(kind=kind,operation_ids=[o['id'] for o in chosen],
            orientation_before=before,orientation_after=list(orientation)))
    plan=dict(mode='hamada_alg2_ready_order_fixed_tqec_adapter_v1',spacing=spacing,layers=layers)
    validate_plan(program,plan)
    return dict(plan=plan,fronts=fronts,dag_oracle_events=events,mu=0,
                scope='Paper Alg2 ready snapshot/order reproduced; H-first/full-source timing and fixed footprints are explicit adaptations. Not original shortest-path BFS, 3D Dijkstra or 2606 native scheduler.')
