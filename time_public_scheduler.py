"""Separate scheduler-only measurement after other research jobs finish."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time

from public_clifford import schedule_program
from run_public_clifford import CONDITIONS, PROTOCOL
from run_surgery import save

ROOT=Path(__file__).resolve().parent


def measure(results,output):
    if output.exists():raise FileExistsError('Preserve earlier timing records')
    program=json.loads((results/'program.json').read_text());env=json.loads((results/'environment.json').read_text())
    for name,sha in env['source_files_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise AssertionError('Experiment source differs')
    records=[]
    for mode,spacing in CONDITIONS:
        for _ in range(3):schedule_program(program,mode,spacing)
        seconds=[]
        for _ in range(25):
            start=time.perf_counter();schedule_program(program,mode,spacing);seconds.append(time.perf_counter()-start)
        records.append({'record_id':f'hs4_{mode}_spacing{spacing}','seconds':seconds,'median_seconds':statistics.median(seconds)})
    save(output,{'protocol_id':PROTOCOL['id'],'scope':'Full-instruction DAG scheduler only, 3 warmups and 25 repetitions; after complete Monte Carlo and test jobs. No other local research job intentionally running. Host may be shared.',
                 'initial_timing_note':'scheduler_timing.json was recorded before sampling while a separate validation-test process was active; diagnostic only. This separate later file is the reported timing evidence.',
                 'source_sha256':program['source_sha256'],'timing_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':platform.python_version(),'records':records})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,default=ROOT/'results/public_hs4_2026-11-02');p.add_argument('--output',type=Path,required=True);a=p.parse_args();measure(a.results,a.output)
