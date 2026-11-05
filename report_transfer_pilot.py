"""Audit frozen full-circuit parity labels and replay the decision ablations."""
from collections import defaultdict
import json
import math
import statistics
import subprocess
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import stim

from core import load_core
from memory_calibration_previous import wilson_interval
from public_clifford import load_program
from run_public_lookahead import METHODS, choose, signature
from run_surgery import save
from transfer_pilot import (BELL4, CAT, OUT, ROOT, choose_front, objsha, parity_mask,
                            predict, sha)


def interval_difference(chosen, base):
    a, b = chosen['rate'], base['rate']
    al, ah = chosen['wilson95']
    bl, bh = base['wilson95']
    delta = a-b
    if chosen['noisy_sha256'] == base['noisy_sha256']:
        return [0., 0., 0.]
    return [delta, delta-math.hypot(a-al,bh-b), delta+math.hypot(ah-a,b-bl)]


def audit():
    frozen = json.loads((OUT/'frozen.json').read_text())
    started = json.loads((OUT/'run_start.json').read_text())
    commit = started['freeze_commit']
    committed = subprocess.check_output(['git','show',f"{commit}:{(OUT/'frozen.json').relative_to(ROOT)}"],cwd=ROOT)
    assert committed == (OUT/'frozen.json').read_bytes()
    assert started['frozen_sha256'] == sha(OUT/'frozen.json')
    assert frozen['source_code_sha256'] == sha(ROOT/'transfer_pilot.py')
    summary = json.loads((OUT/'summary.json').read_text())
    by_id = {r['id']:r for r in summary['records']}
    assert len(by_id) == len(frozen['candidates']) == len({r['noisy_sha256'] for r in by_id.values()})
    assert summary['new_shots'] == sum(r['shots'] for r in by_id.values())
    for row in frozen['candidates']:
        record = by_id[row['id']]
        file = OUT/'samples'/row['id']
        assert record == json.loads(file.with_suffix('.json').read_text())
        assert record['ideal_sha256'] == objsha(stim.Circuit.from_file(str(file)+'_ideal.stim'))
        assert record['noisy_sha256'] == objsha(stim.Circuit.from_file(file.with_suffix('.stim')))
        assert record['dem_sha256'] == objsha(stim.DetectorErrorModel.from_file(file.with_suffix('.dem')))
        meta = json.loads((OUT/'certificates'/f"{row['id']}.json").read_text())['metadata']
        assert parity_mask(meta['external_flows'],4,(0,1)) == record['parity_mask']
        batches = record['batches']
        assert sum(b['shots'] for b in batches) == record['shots']
        assert sum(b['parity_errors'] for b in batches) == record['errors']
        assert list(wilson_interval(record['errors'],record['shots'])) == record['wilson95']
        assert all(math.isclose(predict(frozen['models'][k],row), v) for k,v in record['logit_predictions'].items())
    contrasts = []
    for decision in frozen['online_bell4_under_one_cx_cap']:
        rows = [r for r in frozen['candidates'] if r['id'] in decision['candidate_ids']]
        assert {k:v for k,v in decision.items() if k!='spacing'} == choose_front(rows,frozen['models'])
        base = by_id[decision['selected']['progress']]
        for method, name in decision['selected'].items():
            contrasts.append({'spacing':decision['spacing'],'method':method,'selected':name,
                              'difference_and_newcombe95':interval_difference(by_id[name],base)})
    routes = []
    pinned = load_core(ROOT.parent/'external/wisq')['sarouting']
    for workload,path in [('bell4',BELL4),('cat4',CAT)]:
        program = load_program(path)
        for spacing in (3,5):
            natural = by_id[f"{workload}_s{spacing}_{'parallel' if workload=='bell4' else 'chain'}"]
            reference = next(r for r in frozen['candidates'] if r['id']==natural['id'])
            for seed in (1,2,3):
                for method in METHODS:
                    result = choose(program,pinned,method,spacing,seed)
                    assert signature(result['plan']) == signature(reference['plan'])
                    routes.append({'workload':workload,'spacing':spacing,'seed':seed,'method':method,
                        'shared_circuit':natural['noisy_sha256'],'new_shots':0,'fronts':result['fronts'],'cost':result['cost']})
    save(OUT/'evaluation.json', {'freeze_replay':commit,'unique_circuits':len(by_id),'new_shots':summary['new_shots'],
        'contrasts':contrasts,'unconstrained_routes':routes,
        'cat_geometry_contrast':interval_difference(by_id['cat4_s5_chain'],by_id['cat4_s3_chain'])})
    return by_id


def figures(by_id):
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 3.6), layout='constrained')
    order = ['parallel','anchor_last','anchor_first']
    labels = ['Parallel','Target pair last','Target pair first']
    for i,spacing in enumerate((3,5)):
        records = [by_id[f'bell4_s{spacing}_{key}'] for key in order]
        x = [j + (i-.5)*.17 for j in range(len(records))]
        y = [100*r['rate'] for r in records]
        e = [[100*(r['rate']-r['wilson95'][0]) for r in records],
             [100*(r['wilson95'][1]-r['rate']) for r in records]]
        axs[0].errorbar(x,y,yerr=e,fmt='o' if i==0 else 's',capsize=3,label=f'Spacing {spacing}')
    axs[0].set_xticks(range(3),labels,rotation=12)
    axs[0].legend(frameon=False)
    axs[0].set_title('MQT Bell(4) · held-out size')
    axs[0].set_ylabel('Decoded terminal Z₀Z₁ error (%)')
    for i,spacing in enumerate((3,5)):
        r = by_id[f'cat4_s{spacing}_chain']
        y = r['rate']
        axs[1].errorbar(i,100*y,yerr=[[100*(y-r['wilson95'][0])],[100*(r['wilson95'][1]-y)]],fmt='o',capsize=3,color='#0B6771')
        pred = 1/(1+math.exp(-r['logit_predictions']['full']))
        axs[1].scatter(i,100*pred,marker='x',color='#A34E20',label='Out-of-domain fit' if i==0 else None)
    axs[1].set_xticks([0,1],['Spacing 3','Spacing 5'])
    axs[1].set_title('QASMBench cat(4) · distinct source')
    axs[1].set_ylabel('Decoded terminal Z₀Z₁ error (%)')
    axs[1].legend(frameon=False)
    for ax in axs:
        ax.grid(axis='y',alpha=.23)
        ax.spines[['top','right']].set_visible(False)
    fig.supxlabel('100,000 shots per complete circuit · pointwise Wilson 95% intervals',fontsize=9)
    for ext in ('png','pdf'):
        fig.savefig(ROOT/'docs/figures'/f'public_parity_transfer.{ext}',dpi=200)
    plt.close(fig)


def timing():
    frozen = json.loads((OUT/'frozen.json').read_text())
    models = frozen['models']
    times = defaultdict(list)
    for decision in frozen['online_bell4_under_one_cx_cap']:
        rows = [r for r in frozen['candidates'] if r['id'] in decision['candidate_ids']]
        cases = [('fixed_progress',lambda: rows[0]['id']),
                 ('risk_all_ablations',lambda: choose_front(rows,models))]
        for _, fn in cases:
            for _ in range(3):
                fn()
        for i in range(25):
            for label, fn in cases[i%2:]+cases[:i%2]:
                start = time.perf_counter()
                fn()
                times[(decision['spacing'],label)].append(time.perf_counter()-start)
    save(OUT/'selector_timing_isolated.json', {'scope':'Decision scoring only on the same already built two-candidate pool; full method computes all ablations. Excludes routing, compilation, fitting and Monte Carlo.',
        'samples':[{'spacing':s,'scope':k,'seconds':v,'median_seconds':statistics.median(v)} for (s,k),v in times.items()]})


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['timing']:
        timing()
    else:
        figures(audit())
