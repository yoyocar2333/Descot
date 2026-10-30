"""Separate held-out primary timing pass, run after other heavy work finishes."""
from pathlib import Path
import hashlib
import json
import random
import statistics
from core import load_core
from lookahead import schedule
from run_routing import ROOT,METHODS,save

router=load_core(ROOT.parent/'external/wisq')['sarouting']
tasks=[]
for inp in sorted((ROOT/'inputs').glob('*/input.json')):
    data=json.loads(inp.read_text())
    if data['split']!='held_out':continue
    for seed in [1,2,3]:
        for method in ['one_budget48','two_budget48','guided_budget48']:
            tasks.append((inp,data,seed,method))
random.Random(20261030).shuffle(tasks)
for inp,data,seed,method in tasks:
    out=ROOT/'results/isolated_timing'/inp.parent.name/f'{method}_s{seed}.json'
    if out.exists():continue
    expected=json.loads((ROOT/'results/routing'/inp.parent.name/f'{method}_s{seed}.json').read_text())
    elapsed=[]
    for rep in range(3):
        result=schedule(router,data['gates'],data['architecture'],data['mapping'],seed,METHODS[method])
        h=hashlib.sha256(json.dumps(result['steps']).encode()).hexdigest()
        if h!=expected['repeats'][0]['schedule_hash']:raise AssertionError('Timing pass changed schedule')
        elapsed.append(result['routing_seconds'])
    save(out,{'instance':inp.parent.name,'method':method,'seed':seed,'seconds':elapsed,'median_seconds':statistics.median(elapsed),
              'schedule_hash':h,'protocol':'Randomized configuration order, three repeats, no simultaneous local sampling/compilation benchmark; shared host is not exclusively reserved.'})
    print(inp.parent.name,method,seed,elapsed,flush=True)
