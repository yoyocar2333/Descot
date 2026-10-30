import csv
import json
import statistics
from pathlib import Path
from run_routing import ROOT,METHODS,save

def med(xs):return statistics.median(xs)

def main():
    records=[json.loads(p.read_text()) for p in (ROOT/'results/routing').glob('*/*.json')]
    index={(r['instance'],r['seed'],r['method']):r for r in records}
    rows=[]
    for r in records:
        base=index.get((r['instance'],r['seed'],'one_budget48'))
        if not base:continue
        timing=ROOT/'results/isolated_timing'/r['instance']/f'{r["method"]}_s{r["seed"]}.json'
        isolated=json.loads(timing.read_text())['median_seconds'] if timing.exists() else None
        rows.append({'instance':r['instance'],'split':r['split'],'method':r['method'],'seed':r['seed'],
                     'depth':r['time_steps'],'depth_change_percent':100*(r['time_steps']/base['time_steps']-1),
                     'gate_route_calls':r['cost'].get('gate_route_calls'),'seconds_exploratory':r['median_seconds'],
                     'seconds_isolated':isolated,'valid':r['valid']})
    out=ROOT/'results/analysis';out.mkdir(exist_ok=True)
    with (out/'routing.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary={'configurations':len(records),'routing_executions':sum(len(r['repeats']) for r in records),
             'valid_configurations':sum(r['valid'] for r in records),'expected_configurations':len(list((ROOT/'inputs').glob('*/input.json')))*3*len(METHODS),
             'inputs':len(list((ROOT/'inputs').glob('*/input.json'))),'rows':rows,'aggregates':{},'instances':{}}
    for split in ['development','held_out']:
        summary['aggregates'][split]={}
        for method in METHODS:
            values=[r for r in rows if r['split']==split and r['method']==method]
            if not values:continue
            changes=[r['depth_change_percent'] for r in values]
            aggregate={'pairs':len(values),'median_depth_change_percent':med(changes),
                       'min_depth_change_percent':min(changes),'max_depth_change_percent':max(changes),
                       'wins':sum(x<0 for x in changes),'ties':sum(x==0 for x in changes),'losses':sum(x>0 for x in changes)}
            call_ratios=[];original_changes=[]
            for row in values:
                b=index[(row['instance'],row['seed'],'one_budget48')]
                if row['gate_route_calls'] is not None:
                    call_ratios.append(row['gate_route_calls']/b['cost']['gate_route_calls'])
                original=index.get((row['instance'],row['seed'],'original'))
                if original:original_changes.append(100*(row['depth']/original['time_steps']-1))
            if call_ratios:aggregate['median_gate_route_call_ratio_vs_one_budget48']=med(call_ratios)
            if original_changes:
                aggregate['vs_original']={'median_depth_change_percent':med(original_changes),
                    'wins':sum(v<0 for v in original_changes),'ties':sum(v==0 for v in original_changes),'losses':sum(v>0 for v in original_changes)}
            ratios=[]
            for r in values:
                b=next((b for b in rows if b['instance']==r['instance'] and b['seed']==r['seed'] and b['method']=='one_budget48'),None)
                if b and b['seconds_isolated'] and r['seconds_isolated']:ratios.append(b['seconds_isolated']/r['seconds_isolated'])
            if ratios:aggregate['median_isolated_speedup_vs_one_budget48']=med(ratios)
            summary['aggregates'][split][method]=aggregate
    for instance in sorted({r['instance'] for r in rows}):
        vals=[r for r in rows if r['instance']==instance]
        summary['instances'][instance]={'split':vals[0]['split'],'methods':{m:{'median_depth':med([r['depth'] for r in vals if r['method']==m]),'depths':[r['depth'] for r in vals if r['method']==m]} for m in METHODS if any(r['method']==m for r in vals)}}
    witnesses=[]
    for a in records:
        if a['method']!='one_pool16':continue
        b=index.get((a['instance'],a['seed'],'two_pool16'))
        if not b:continue
        for t,(sa,sb) in enumerate(zip(a['steps'],b['steps'])):
            if sa==sb:continue
            old=a['fronts'][t]['chosen'];new=b['fronts'][t]['chosen']
            evaluated=next((x for x in b['fronts'][t]['candidates'] if x['order']==old['order']),None)
            if evaluated and new['progress']>evaluated['progress']:
                witnesses.append({'instance':a['instance'],'seed':a['seed'],'front_index':t,'one_step_choice':evaluated,
                                  'two_step_choice':new,'final_depths':[a['time_steps'],b['time_steps']],
                                  'candidate_pool':'Same first 16 candidate orders at the same state'})
            break
    summary['lookahead_witnesses']=witnesses
    summary['fixed_pool_ablations']={}
    for method,base_method in [('two_pool16','one_pool16'),('guided_budget48','two_pool16')]:
        differences=[]
        for r in rows:
            if r['method']==method and r['split']=='held_out':
                b=index[(r['instance'],r['seed'],base_method)]
                differences.append(100*(r['depth']/b['time_steps']-1))
        summary['fixed_pool_ablations'][method+'_vs_'+base_method]={
            'median_depth_change_percent':med(differences),'wins':sum(x<0 for x in differences),
            'ties':sum(x==0 for x in differences),'losses':sum(x>0 for x in differences)}
    summary['identical_original_saturation_pairs']=sum(
        index[(r['instance'],r['seed'],'original')]['repeats'][0]['schedule_hash']==r['repeats'][0]['schedule_hash']
        for r in records if r['method']=='saturation')
    summary['complete']=summary['configurations']==summary['expected_configurations']
    save(out/'summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['configurations','routing_executions','complete','aggregates']},indent=2))

if __name__=='__main__':main()
