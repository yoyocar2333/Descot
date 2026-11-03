"""Audit complete-source algorithm controls and plot actual work separately."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from memory_calibration_previous import wilson_interval
from public_candidate_pool import digest
from public_clifford import validate_plan
from run_public_candidates import checked_program
from run_public_lookahead import ROOT, METHODS, PROTOCOL, signature
from run_surgery import save, MODEL, DECODER


def audit(folder):
    summary=json.loads((folder/'summary.json').read_text());p=checked_program()
    if digest(summary['protocol'])!=digest(PROTOCOL):raise AssertionError('Changed protocol')
    env=json.loads((folder/'environment.json').read_text())
    for f,h in env['source_files_sha256'].items():
        if hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h:raise AssertionError('Changed experiment source')
    refs=set();replayed=set()
    for r in summary['compile_replays']:
        if r['complete_original_instructions']!=32 or r['shortest_graphlike_error']!=3:raise AssertionError('Incomplete physical replay')
        if len(r['signed_z_validation']['signed_inputs'])!=16 or len(r['signed_z_validation']['final_faults'])!=4:raise AssertionError('Incomplete signed/fault replay')
        replayed.add(r['noisy_circuit_sha256'])
    for r in summary['records']:
        route=json.loads((folder/'routes'/(r['id']+'.json')).read_text())
        validate_plan(p,route['plan'])
        if route['mu']!=0 or route['plan']['spacing']!=r['spacing']:raise AssertionError('Unexpected risk/geometry')
        ref=json.loads((ROOT/r['reference_record']).read_text());refs.add(ref['noisy_circuit_sha256'])
        cert=ROOT/'results/public_candidates_2026-11-02/certificates'/(ref['record_id']+'.json')
        cert=json.loads(cert.read_text())
        if signature(route['plan'])!=signature(cert['candidate_plan']):raise AssertionError('Complete plan not identical')
        if r['source_sha256']!=p['source_sha256'] or ref['source_sha256']!=p['source_sha256']:raise AssertionError('Changed complete public source')
        if (ref['distance'],ref['physical_p'],ref['model_id'],ref['decoder_id'])!=(3,.001,MODEL,DECODER):raise AssertionError('Comparison condition differs')
        for k in ('num_ticks','num_qubits','failures_any','noisy_circuit_sha256'):
            if r[k]!=ref[k]:raise AssertionError('Reused metric differs')
        if r['wilson95']!=list(wilson_interval(ref['failures_any'],ref['shots'])) or r['new_shots']!=0:raise AssertionError('CI/shot accounting differs')
        if r['cost']!=route['cost'] or r['cost']!={k:sum(f['cost'][k] for f in route['fronts']) for k in route['cost']}:raise AssertionError('Cost accounting differs')
        if r['method']!='author_profile' and any(f['cost']['front_evaluations']>48 for f in route['fronts']):raise AssertionError('Budget violation')
    if refs!=replayed or len(refs)!=2 or len(summary['records'])!=30:raise AssertionError('Coverage differs')
    for spacing in (3,5):
        for seed in (1,2,3):
            a=json.loads((folder/'routes'/f'spacing{spacing}_one_pool16_s{seed}.json').read_text())
            b=json.loads((folder/'routes'/f'spacing{spacing}_two_pool16_s{seed}.json').read_text())
            if [(f['ready_ids'],f['candidate_orders']) for f in a['fronts']]!=[(f['ready_ids'],f['candidate_orders']) for f in b['fronts']]:raise AssertionError('Observed fixed pool not identical')
    result={'passed':True,'source_conditions':30,'complete_source_instructions':32,'unique_recompiled_complete_circuits':2,
            'new_shots':0,'unique_reused_shots':200000,'distance':3,'physical_p':.001,'model_id':MODEL,'decoder_id':DECODER,
            'all_select_p12':all(r['candidate_id']=='p12' for r in summary['records']),
            'same_observed_fixed_pools':True,'mu':0,
            'scope':'Development integration/replay of previously observed geometries, not fresh held-out evaluation. Exact same full circuit means shared counts and identically zero algorithm contrasts.'}
    save(folder/'record_audit.json',result)
    return summary


def report(folder):
    s=audit(folder)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(10,4.5))
    names=['Author profile','One-step','Two-step'];methods=['author_profile','one_pool16','two_pool16']
    rows=[next(r for r in s['records'] if r['spacing']==3 and r['seed']==1 and r['method']==m) for m in methods]
    ax.bar(names,[r['cost']['front_evaluations'] for r in rows],color=['#64748b','#187c9a','#b45d24'])
    ax.set_ylabel('Actual front evaluations (whole source)');ax.set_ylim(0,8)
    for i,r in enumerate(rows):ax.text(i,r['cost']['front_evaluations']+.15,str(r['cost']['front_evaluations']),ha='center')
    ax.set_title('Search work differs; schedules coincide');ax.grid(axis='y',alpha=.2)
    for spacing,color in [(3,'#187c9a'),(5,'#b45d24')]:
        rows=[next(r for r in s['records'] if r['spacing']==spacing and r['seed']==1 and r['method']==m) for m in methods]
        p=np.array([r['failures_any']/1000 for r in rows])
        lo=np.array([r['wilson95'][0]*100 for r in rows]);hi=np.array([r['wilson95'][1]*100 for r in rows])
        bx.errorbar(np.arange(3),p,yerr=[p-lo,hi-p],fmt='o-',capsize=3,color=color,label=f'Spacing {spacing}, same p12 circuit')
    bx.set_xticks(np.arange(3),names);bx.set_ylabel('Any decoded output error (%)');bx.set_ylim(43,53);bx.legend(fontsize=8);bx.grid(alpha=.2)
    fig.suptitle('Complete hs4_n4: full-DAG algorithm controls',fontweight='bold')
    fig.text(.5,.025,'All: 2 CX steps, 7 H layers, 27 block-z, 636 TICKs. QEC rounds not inferred.\nPrior exact full-circuit counts: 100,000 shots/geometry, d=3, p=0.001, ordinary MWPM; Wilson95. New shots=0.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.10,1,.94]);dest=ROOT/'docs/figures'
    fig.savefig(dest/'public_lookahead_controls.png',dpi=180);fig.savefig(dest/'public_lookahead_controls.pdf');plt.close(fig)
    print(json.dumps(json.loads((folder/'record_audit.json').read_text()),indent=2))


if __name__=='__main__':report(ROOT/'results/public_lookahead_2026-11-03')
