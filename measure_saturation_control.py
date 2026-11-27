"""Paired original-policy timing with certified full-front early stopping."""
import json
from pathlib import Path
import statistics
import time

from core import load_core
from saturation import routing_hooks
from validation import validate
from run_original_objective import ROOT,DEFAULT,save,sha


def main():
    out=DEFAULT/'stopping_control'
    if out.exists():raise FileExistsError('Fresh stopping result required')
    out.mkdir();core=load_core(ROOT.parent/'external/wisq');router=core['sarouting']
    cases=[]
    for p in sorted((DEFAULT/'inputs').glob('*.json')):
        d=json.loads(p.read_text());cases.append((p.stem,'public',d['program']['routing_gates'],d['architecture'],d['mapping'],list(range(1,11))))
    old=json.loads((ROOT/'results/analysis/summary.json').read_text())
    for name in sorted({r['instance'] for r in old['rows'] if r['split']=='held_out'}):
        d=json.loads((ROOT/'inputs'/name/'input.json').read_text());cases.append((name,'historical',d['gates'],d['architecture'],d['mapping'],[1,2,3]))
    save(out/'protocol.json',dict(method='Existing frozen saturation.py from Phase1, no new tuning.',
        rule='When a candidate routes every ready gate, positive criticality reaches a local upper bound. Original strict-greater reward retains the first such candidate. Per-state RNG makes later states comparable.',
        policy='Alternate method order by seed/repeat. Same original mapping, route primitive, annealing parameters and per-state RNG. Exact whole schedule equality required.',
        scope='Compiler stopping control on original criticality policy, separate from changing reward to two-step. No gate-order, depth, physics or novelty claim.',repeats=3,new_shots=0))
    rows=[]
    for name,cohort,gates,arch,mapping,seeds in cases:
        for seed in seeds:
            samples={m:[] for m in ['original','saturation']};hashes={m:[] for m in samples};work={}
            for repeat in range(3):
                order=['original','saturation'] if (seed+repeat)%2 else ['saturation','original']
                for method in order:
                    with routing_hooks(router,method,seed) as stats:
                        start=time.perf_counter();steps,_,interrupt=router.sim_anneal_route(gates,arch,mapping,10,.1,.1,1,300,'random','criticality',False)
                        elapsed=time.perf_counter()-start
                        if interrupt:raise RuntimeError('Routing timeout')
                        work[method]=dict(stats)
                    validate(gates,arch,mapping,steps);samples[method].append(elapsed);hashes[method].append(sha(json.dumps(steps).encode()))
            if len(set(hashes['original']+hashes['saturation']))!=1:raise AssertionError('Saturation changed original schedule')
            rows.append(dict(instance=name,cohort=cohort,seed=seed,depth=len(steps),samples=samples,
                median_seconds={m:statistics.median(v) for m,v in samples.items()},
                time_ratio=statistics.median(samples['saturation'])/statistics.median(samples['original']),
                order_evaluations={m:work[m]['order_evaluations'] for m in work},
                schedule_sha256=hashes['original'][0],saturation_stops=work['saturation']['saturation_stops']))
        print(name,'original/saturation exact equality + paired timing PASS',flush=True)
    save(out/'records.json',rows)
    summary={}
    for cohort in ['historical','public']:
        rs=[r for r in rows if r['cohort']==cohort];summary[cohort]=dict(pairs=len(rs),identical_schedules=len(rs),
            median_paired_time_ratio=statistics.median(r['time_ratio'] for r in rs),
            median_order_evaluation_ratio=statistics.median(r['order_evaluations']['saturation']/r['order_evaluations']['original'] for r in rs))
    save(out/'summary.json',dict(cohorts=summary,executions=6*len(rows),new_shots=0,code_sha256=sha(Path(__file__).read_bytes())))


if __name__=='__main__':main()
