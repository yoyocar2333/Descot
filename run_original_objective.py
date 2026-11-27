"""DASCOT's original routing objective: fixed mapping, depth and CPU cost.

Public source instructions remain in a complete logical trace. Only CX/T/TDG
consume abstract routing steps, as in the pinned author interface. This is
SCMR routing evaluation, not full physical compilation or decoded-error work.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import tempfile
import time

import numpy as np
from qiskit import qasm2
from core import COMMIT,load_core
from lookahead import Config,schedule
from saturation import routing_hooks
from validation import validate
from run_public_audit import inspect_qasm

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'results/original_objective_2026-11-30'
METHODS=['original','one_budget48','two_budget48']
SOURCES=['benchmarks/original_route_2026-11-30/3_17_13.qasm',
 'benchmarks/public_2026-11-02/qasmbench/qec_en_n5.qasm',
 'benchmarks/public_2026-11-02/qasmbench/error_correctiond3_n5.qasm']


def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def complete_source(path):
    audit=inspect_qasm(path);ops=audit['operations']
    allowed={'cx','t','tdg','h','x','y','z','s','sdg','id','measure','barrier'}
    if set(audit['operation_counts'])-allowed:raise ValueError('Unsupported source instruction retained and rejected')
    for op in ops:
        if op['name']=='measure' and any(set(op['qubits'])&set(l['qubits']) for l in ops[op['id']+1:]):
            raise ValueError('Only terminal measurement supported')
    routed=[o for o in ops if o['name'] in ('cx','t','tdg')]
    if not routed:raise ValueError('No routed operations')
    audit.update(routed_source_ids=[o['id'] for o in routed],routing_gates=[o['qubits'] for o in routed],
        routing_operations=[o['name'] for o in routed],
        routed_active_qubits=sorted({q for o in routed for q in o['qubits']}),
        model='Pinned author SCMR abstraction: CX/T/TDG occupy one routed step; local Clifford/readout retained as zero-duration logical events. No physical gate timing/noise claims.')
    return audit


def trace_source(program,steps):
    times={gid:t for t,step in enumerate(steps) for gid,_,_ in step}
    route_ids={source_id:i for i,source_id in enumerate(program['routed_source_ids'])};ends={};trace=[]
    for op in program['operations']:
        ready=max((ends[p] for p in op['predecessors']),default=0)
        if op['id'] in route_ids:
            start=times[route_ids[op['id']]];end=start+1
            if start<ready:raise ValueError('Complete source quantum/classical dependency violated')
        else:start=end=ready
        ends[op['id']]=end;trace.append(dict(**op,start_routing_boundary=start,end_routing_boundary=end,
            routed_id=route_ids.get(op['id']),implementation='author routed primitive' if op['id'] in route_ids else 'retained zero-duration event in abstract SCMR model'))
    return trace


def route(core,program,arch,mapping,seed,method):
    router=core['sarouting'];gates=program['routing_gates']
    if method=='original':
        with routing_hooks(router,'original',seed) as count:
            began=time.perf_counter()
            steps,_,interrupted=router.sim_anneal_route(gates,arch,mapping,10,.1,.1,1,300,'random','criticality',False)
            seconds=time.perf_counter()-began
            if interrupted:raise RuntimeError('Author policy timeout')
            record=dict(steps=steps,time_steps=len(steps),routing_seconds=seconds,cost=dict(count))
    else:record=schedule(router,gates,arch,mapping,seed,Config('one_step' if method=='one_budget48' else 'two_step',48))
    record.update(validation=validate(gates,arch,mapping,record['steps']),source_trace=trace_source(program,record['steps']),
                  schedule_sha256=sha(json.dumps(record['steps']).encode()))
    return record


def run(output,seeds=10):
    if output.exists():raise FileExistsError('Fresh output required')
    if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
    core=load_core(ROOT.parent/'external/wisq')
    programs={Path(p).stem:complete_source(ROOT/p) for p in SOURCES}
    # Native extraction is checked, never silently drops unsupported source gates.
    for path in SOURCES:
        p=programs[Path(path).stem];gates,ops=core['dascot'].extract_gates_from_file(ROOT/path)
        p['native_original_text_route_count']=len(gates)
        # The author's line regex misses an indented CX in error_correctiond3.
        # Canonical QASM preserves the whole source and normalizes formatting.
        circuit=qasm2.load(ROOT/path)
        canonical=qasm2.dumps(circuit)+'\n';p['canonical_qasm_sha256']=sha(canonical.encode())
        with tempfile.NamedTemporaryFile(mode='w',suffix='.qasm') as f:
            f.write(canonical);f.flush();gates,ops=core['dascot'].extract_gates_from_file(f.name)
        if list(map(tuple,p['routing_gates']))!=gates or p['routing_operations']!=ops:raise AssertionError('Complete canonical routing frontend differs')
        p['native_canonical_route_count']=len(gates)
    output.mkdir(parents=True);(output/'records').mkdir();(output/'inputs').mkdir()
    save(output/'protocol.json',dict(id='original_dascot_objective_20261130_v1',
        priority='Latest TA/professor feedback: improve original paper routing result. Readout-sensitive/DEM work remains archived and leaves the presentation main line.',
        source_paths=SOURCES,methods=METHODS,mapping_seed=1001,routing_seeds=list(range(1,seeds+1)),repeats=3,
        layouts=['square_sparse','compact'],fixed_mapping=True,front_budget=48,
        comparison='All methods use complete canonical source frontend. One48/Two48 share per-decision evaluation units. Author reference uses original search with controlled state-seeded RNG; not equal-CPU or full232-paper reproduction.',
        metric='Primary routing steps and cost ratio steps / CX-T-TDG dependency depth. Independent routing-only median wall seconds and route calls. Mapping timed separately.',
        role='All seen families/development. Historical24 synthetic test remains a separate frozen result; no reclassification of data.',
        full_source='All operations and dependencies retained in source trace. No arbitrary rotations/feedback discarded. Only original abstract routing, not full physical application compilation.',
        shots=0,physical_compilations=0,mu=0,sampling_permission=False))
    save(output/'environment.json',dict(python=platform.python_version(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        wisq_commit=COMMIT,code_sha256={n:sha((ROOT/n).read_bytes()) for n in ['run_original_objective.py','lookahead.py','saturation.py','validation.py','core.py','requirements-lock.txt']},
        source_sha256={p:sha((ROOT/p).read_bytes()) for p in SOURCES}))
    index=[]
    for name,p in programs.items():
        circuit=qasm2.load(ROOT/next(x for x in SOURCES if Path(x).stem==name))
        depth=circuit.depth(filter_function=lambda x:x.operation.name in ('cx','t','tdg'))
        for layout in ['square_sparse','compact']:
            arch=getattr(core['architecture'],layout+'_layout')(len(p['routed_active_qubits']),'all_sides')
            random.seed(1001);np.random.seed(1001);began=time.perf_counter()
            mapping,proxy=core['phased_graph'].build_phased_map(p['routed_active_qubits'],circuit,arch,100,.1/depth,1/depth,timeout=300,include_t=True)
            mapping_seconds=time.perf_counter()-began
            identifier=name+'_'+layout
            save(output/'inputs'/(identifier+'.json'),dict(program=p,architecture=arch,mapping=mapping,mapping_seconds=mapping_seconds,mapping_proxy=proxy,routing_dependency_depth=depth))
            for seed in range(1,seeds+1):
                for method in METHODS[(seed-1)%3:]+METHODS[:(seed-1)%3]:
                    records=[route(core,p,arch,mapping,seed,method) for _ in range(3)]
                    if len({r['schedule_sha256'] for r in records})!=1:raise AssertionError('Repeated schedule differs')
                    r=records[0];row=dict(instance=identifier,source=name,layout=layout,method=method,seed=seed,depth=r['time_steps'],
                        cost_ratio=r['time_steps']/depth,median_seconds=statistics.median(x['routing_seconds'] for x in records),
                        repeat_seconds=[x['routing_seconds'] for x in records],schedule_sha256=r['schedule_sha256'],
                        gate_route_calls=r['cost']['gate_route_calls'],source_sha256=p['source_sha256'])
                    save(output/'records'/(identifier+'_'+method+f'_s{seed:02}.json'),{**row,**r});index.append(row)
            print(identifier,'complete',3*seeds,'records',flush=True)
    save(output/'index.json',index)
    paired=[];by={(r['instance'],r['seed'],r['method']):r for r in index}
    for instance in sorted({r['instance'] for r in index}):
        for comparator in ['original','one_budget48']:
            pairs=[(by[instance,s,'two_budget48'],by[instance,s,comparator]) for s in range(1,seeds+1)]
            paired.append(dict(instance=instance,baseline=comparator,pairs=len(pairs),
                median_depth_change_percent=statistics.median(100*(a['depth']-b['depth'])/b['depth'] for a,b in pairs),
                mean_baseline_depth=statistics.mean(b['depth'] for a,b in pairs),mean_two_depth=statistics.mean(a['depth'] for a,b in pairs),
                wins=sum(a['depth']<b['depth'] for a,b in pairs),ties=sum(a['depth']==b['depth'] for a,b in pairs),losses=sum(a['depth']>b['depth'] for a,b in pairs),
                median_time_ratio=statistics.median(a['median_seconds']/b['median_seconds'] for a,b in pairs)))
    save(output/'summary.json',dict(configurations=len(index),routing_executions=3*len(index),all_legal=True,paired=paired,new_shots=0,
        decision='Report every case including ties and regressions. No positive outcome guaranteed or used for source selection.'))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--output',type=Path,default=DEFAULT);p.add_argument('--seeds',type=int,default=10);a=p.parse_args();run(a.output,a.seeds)
