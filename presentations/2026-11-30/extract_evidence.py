"""Rebuild presentation evidence from preserved records; no routing or sampling."""
import json
from pathlib import Path
import statistics
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from lookahead import ready_front
R=ROOT/'results/original_objective_2026-11-30'

def read(p):return json.loads(p.read_text())
def extract():
    old=read(ROOT/'results/analysis/summary.json')
    timing=read(R/'historical_retiming/records.json')
    by={(r['instance'],r['seed'],r['method']):r for r in timing};pairs=[]
    for a in timing:
        if a['method']!='two_budget48':continue
        b=by[a['instance'],a['seed'],'original']
        pairs.append(dict(instance=a['instance'],seed=a['seed'],original_depth=b['depth'],two_depth=a['depth'],depth_ratio=a['depth']/b['depth'],time_ratio=a['median_seconds']/b['median_seconds'],original_ms=1000*b['median_seconds'],two_ms=1000*a['median_seconds']))
    index=read(R/'index.json');public=[]
    for instance in sorted({x['instance'] for x in index}):
        inp=read(R/'inputs'/(instance+'.json'));rs=[r for r in index if r['instance']==instance];ref={r['seed']:r for r in rs if r['method']=='original'}
        row=dict(instance=instance,source=rs[0]['source'],layout=inp['architecture'],dependency_depth=inp['routing_dependency_depth'],source_counts=inp['program']['operation_counts'],routed_gates=len(inp['program']['routing_gates']))
        for method in ['original','one_budget48','two_budget48']:
            ms=[r for r in rs if r['method']==method]
            row[method]=dict(mean_depth=statistics.mean(r['depth'] for r in ms),median_ms=1000*statistics.median(r['median_seconds'] for r in ms),relative_time=statistics.median(r['median_seconds']/ref[r['seed']]['median_seconds'] for r in ms),wins=sum(r['depth']<ref[r['seed']]['depth'] for r in ms),ties=sum(r['depth']==ref[r['seed']]['depth'] for r in ms),losses=sum(r['depth']>ref[r['seed']]['depth'] for r in ms))
        public.append(row)
    inp=read(R/'inputs/3_17_13_compact.json');a=read(R/'records/3_17_13_compact_original_s01.json');b=read(R/'records/3_17_13_compact_one_budget48_s01.json');t=8
    before_a={g[0] for step in a['steps'][:t] for g in step};before_b={g[0] for step in b['steps'][:t] for g in step};assert before_a==before_b
    remaining={i:g for i,g in enumerate(inp['program']['routing_gates']) if i not in before_a}
    witness=dict(input=inp,front_index=t,remaining=remaining,front=ready_front(remaining),author=a['steps'][t],one=b['steps'][t],author_depth=a['depth'],one_depth=b['depth'])
    detail=old['lookahead_witnesses'][0];instance=detail['instance'];t=detail['front_index']
    with zipfile.ZipFile(ROOT/'archives/phase1_snapshot.zip') as z:
        rs=[json.loads(z.read(f'dascot_phase1/results/routing/{instance}/{m}_s3.json')) for m in ['one_pool16','two_pool16']]
    look=dict(input=read(ROOT/'inputs'/instance/'input.json'),front_index=t,one=rs[0]['steps'][t],two=rs[1]['steps'][t],detail=detail)
    return dict(historical_summary=read(R/'historical_retiming/summary.json'),historical_pairs=pairs,public_rows=public,public_witness=witness,lookahead_witness=look,negative_case=max(pairs,key=lambda r:r['depth_ratio']),source_circuit=inp['program'],stopping=read(R/'stopping_control/summary.json'),fixed16_ablation=old['fixed_pool_ablations'])

if __name__=='__main__':
    p=Path(__file__).with_name('evidence.json');e=extract()
    if '--check' in sys.argv:
        assert json.loads(json.dumps(e))==read(p),'Presentation differs from recorded evidence'
        print('Presentation evidence matches raw records')
    else:p.write_text(json.dumps(e,indent=2)+'\n')
