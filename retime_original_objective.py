"""Fresh serial routing-only timing for the frozen24 synthetic comparisons."""
import json
from pathlib import Path
import statistics
import time

from run_original_objective import ROOT,DEFAULT,METHODS,route,save,sha
from core import load_core


def main():
    out=DEFAULT/'historical_retiming'
    if out.exists():raise FileExistsError('Preserve measured timing')
    out.mkdir();core=load_core(ROOT.parent/'external/wisq')
    summary=json.loads((ROOT/'results/analysis/summary.json').read_text())
    old={(r['instance'],r['seed'],r['method']):r for r in summary['rows'] if r['split']=='held_out'}
    rows=[]
    for instance in sorted({k[0] for k in old}):
        data=json.loads((ROOT/'inputs'/instance/'input.json').read_text());gates=data['gates'];last={};ops=[]
        for i,qs in enumerate(gates):
            parents=sorted({last[q] for q in qs if q in last});ops.append(dict(id=i,name=data['ops'][i],qubits=qs,clbits=[],params=[],predecessors=parents))
            for q in qs:last[q]=i
        program=dict(routing_gates=gates,routed_source_ids=list(range(len(gates))),operations=ops)
        for seed in [1,2,3]:
            for method in METHODS[(seed-1)%3:]+METHODS[:(seed-1)%3]:
                rs=[route(core,program,data['architecture'],data['mapping'],seed,method) for _ in range(3)]
                if len({r['schedule_sha256'] for r in rs})!=1 or rs[0]['time_steps']!=old[instance,seed,method]['depth']:
                    raise AssertionError('Frozen depth/schedule reproduction failed')
                rows.append(dict(instance=instance,seed=seed,method=method,depth=rs[0]['time_steps'],
                    seconds=[r['routing_seconds'] for r in rs],median_seconds=statistics.median(r['routing_seconds'] for r in rs),
                    gate_route_calls=rs[0]['cost']['gate_route_calls'],schedule_sha256=rs[0]['schedule_sha256'],input_sha256=data['input_sha256']))
        print(instance,'native/one/two24 timing executions complete',flush=True)
    save(out/'records.json',rows)
    by={(r['instance'],r['seed'],r['method']):r for r in rows};comparison=[]
    for base in ['original','one_budget48']:
        pairs=[(r,by[r['instance'],r['seed'],base]) for r in rows if r['method']=='two_budget48']
        comparison.append(dict(baseline=base,pairs=len(pairs),median_paired_time_ratio=statistics.median(a['median_seconds']/b['median_seconds'] for a,b in pairs),
            median_depth_change_percent=statistics.median(100*(a['depth']-b['depth'])/b['depth'] for a,b in pairs),
            wins=sum(a['depth']<b['depth'] for a,b in pairs),ties=sum(a['depth']==b['depth'] for a,b in pairs),losses=sum(a['depth']>b['depth'] for a,b in pairs)))
    save(out/'summary.json',dict(configurations=len(rows),executions=3*len(rows),all_depths_match_frozen=True,comparisons=comparison,
        timing='Serial method-rotated three repeats; routing-only wall time, mapping/source validation/physical compile/MC excluded. Shared host, no claim of paper machine reproduction.',
        code_sha256=sha(Path(__file__).read_bytes()),new_shots=0))


if __name__=='__main__':main()
