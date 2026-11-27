"""Plan/run a bounded next lexical batch with durable compile-start journals.

Current checkpoint stays immutable. No-argument execution only prints a plan;
physical compilation requires --execute and a fresh --output directory.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
from types import FunctionType
import os
import time

from public_candidate_pool import digest
from public_minimum_pool import minimum_gate_plans
from public_clifford import generate_program
from exact_compile_cache import ExactCompileCache
from run_hs4_minimum_frontier import DEFAULT,CODE,ROOT,reference,physical_one,read,save,sha


class JournaledCompiler:
    def __init__(self,path,compiler=generate_program):self.path=path;self.compiler=compiler
    def event(self,x):
        with self.path.open('a') as f:f.write(json.dumps(x)+'\n');f.flush();os.fsync(f.fileno())
    def __call__(self,p,r,a,b):
        key=digest(dict(program=p,plan=r,input_bases=a,output_bases=b))
        self.event(dict(event='compile_started',key=key))
        t=time.perf_counter();c,m=self.compiler(p,r,a,b)
        self.event(dict(event='compile_finished',key=key,seconds=time.perf_counter()-t,ideal_sha256=sha(str(c).encode())))
        return c,m


def next_batch(result,limit,completed_indices=()):
    if type(limit) is not int or not 1<=limit<=144:raise ValueError('Explicit1..144 job limit required')
    program=read(result/'program.json');pool=read(result/'candidate_pool.json');known={r['candidate_id']:r for r in pool}
    if [r['plan'] for r in pool]!=minimum_gate_plans(program)['plans']:raise ValueError('Full minimum frontier differs')
    done={}
    for path in [result/'physical_index.json',*completed_indices]:
        for r in read(path):
            if r['candidate_id'] not in known or r['plan_sha256']!=known[r['candidate_id']]['plan_sha256'] or r['source_sha256']!=program['source_sha256']:
                raise ValueError('Completed source/plan differs')
            if not r['qualified_complete_output']:raise ValueError('Unqualified completion supplied')
            done[r['candidate_id']]=r['noisy_sha256']
    selected=[r for r in pool if r['candidate_id'] not in done][:limit]
    plan=dict(source_sha256=program['source_sha256'],full_logical_pool_sha256=digest(pool),
        selected_ids=[r['candidate_id'] for r in selected],complete_ids=sorted(done),
        retained_minimum_count=len(pool),retained_old13=True,physical_compile_request_ceiling=len(selected)*9,
        selection='Next lexical IDs after verified completed certificates; no labels, no candidate deletion or noise-based replacement.',
        physical_resource='Unchanged original620-coordinate/index catalogue. Application concurrency remains uncapped.',
        new_shots=0,sampling_permission=False,held_out_labels='sealed',mu=0)
    return program,selected,plan


def run_one(program,row,output,device,readout):
    cache=ExactCompileCache(JournaledCompiler(output/'journals'/(row['candidate_id']+'.jsonl')))
    fn=FunctionType(physical_one.__code__,{**physical_one.__globals__,'ExactCompileCache':lambda:cache},
        physical_one.__name__,physical_one.__defaults__,physical_one.__closure__)
    return fn(program,row,output,device,readout)


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--result',type=Path,default=DEFAULT);p.add_argument('--limit',type=int,default=6)
    p.add_argument('--completed-index',type=Path,action='append',default=[]);p.add_argument('--execute',action='store_true')
    p.add_argument('--output',type=Path);p.add_argument('--workers',type=int,default=1);a=p.parse_args()
    program,rows,plan=next_batch(a.result,a.limit,a.completed_index)
    if a.execute:
        if not a.output or a.output.exists() or a.workers<1:raise ValueError('Fresh --output and positive workers required')
        a.output.mkdir(parents=True)
        for name in ('circuits','certificates','journals'):(a.output/name).mkdir()
        save(a.output/'batch_protocol.json',plan)
        save(a.output/'environment.json',dict(source_files_sha256={n:sha((ROOT/n).read_bytes()) for n in CODE+['resume_hs4_minima.py']},
            retained_frontier_sha256=plan['full_logical_pool_sha256'],timing='Per-call started/finished journal; unfinished calls stay explicit. No speed comparison.'))
        cert,_,c=reference();index=[]
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            jobs=[ex.submit(run_one,program,row,a.output,c.get_final_qubit_coordinates(),cert['backend_meta']['external_flows']) for row in rows]
            for job in as_completed(jobs):
                r=job.result();index.append(r);save(a.output/'physical_index_partial.json',sorted(index,key=lambda r:r['candidate_id']))
        save(a.output/'physical_index.json',sorted(index,key=lambda r:r['candidate_id']))
    print(json.dumps(plan,indent=2))
