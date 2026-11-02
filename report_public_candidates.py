"""Audit frozen offline decisions and full decoded geometry-held-out evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import stim

from memory_calibration_previous import wilson_interval
from public_candidate_pool import digest, features, fit_model, select, predict
from public_clifford import validate_plan, logical_circuit
from public_readout import classical_bits
from report_schedule_pilot import contrast
from run_public_candidates import PROTOCOL, ROOT, checked_program, pool
from run_public_clifford import digest as circuit_digest
from run_surgery import save


def audit(folder):
    protocol=json.loads((folder/'protocol.json').read_text())
    if protocol!=PROTOCOL:raise AssertionError('Protocol changed')
    program=checked_program()
    if program!=json.loads((folder/'program.json').read_text()):raise AssertionError('Complete source changed')
    env=json.loads((folder/'environment.json').read_text())
    for name,sha in env['source_files_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise AssertionError('Experiment source changed: '+name)
    frozen=json.loads((folder/'frozen_selection.json').read_text())
    if frozen['protocol_sha256']!=digest(protocol) or frozen['development_summary_sha256']!=hashlib.sha256((folder/'development_summary.json').read_bytes()).hexdigest():
        raise AssertionError('Freeze inputs changed')
    start=json.loads((folder/'heldout_start.json').read_text())
    if start['frozen_selection_sha256']!=hashlib.sha256((folder/'frozen_selection.json').read_bytes()).hexdigest():raise AssertionError('Post-test selection changed')
    import subprocess
    relative=(folder/'frozen_selection.json').resolve().relative_to(ROOT).as_posix()
    if subprocess.check_output(['git','-C',str(ROOT),'show',start['source_head']+':'+relative])!=(folder/'frozen_selection.json').read_bytes():
        raise AssertionError('Freeze absent from pre-test commit')
    stages={stage:json.loads((folder/(stage+'_summary.json')).read_text()) for stage in ('development','heldout')}
    if frozen['heldout_pool']!=pool(program,5):raise AssertionError('Heldout candidate pool changed')
    for name,wait in [('depth_only',False),('depth_wait',True)]:
        if digest(frozen['models'][name])!=digest(fit_model(stages['development']['records'],wait)):raise AssertionError('Development-only fit differs')
    for d in frozen['decisions']:
        m=frozen['models']['depth_only' if d['method']=='depth_only' else 'depth_wait']
        actual={'method':d['method'],**select(frozen['heldout_pool'],m,d['pool'],d['guarded'])}
        if actual!=d:raise AssertionError('Pretest decision changed')
    hashes=set(); readout_checks=0
    for stage,s in stages.items():
        candidates=pool(program,3 if stage=='development' else 5)
        ids=[r['candidate_id'] for r in candidates] if stage=='development' else frozen['heldout_sample_ids']
        if [r['candidate_id'] for r in s['records']]!=ids:raise AssertionError('Missing/preselected subset differs')
        local_hashes=set()
        for r in s['records']:
            if r['noisy_circuit_sha256'] in hashes:raise AssertionError('Duplicate sampled circuit')
            hashes.add(r['noisy_circuit_sha256']);local_hashes.add(r['noisy_circuit_sha256'])
            candidate=next(c for c in candidates if c['candidate_id']==r['candidate_id'])
            cert=json.loads((folder/'certificates'/(r['record_id']+'.json')).read_text());m=cert['backend_meta'];v=cert['physical_validation']
            if cert['candidate_plan']!=candidate['plan'] or features(program,candidate['plan'])!=r['features']:raise AssertionError('Candidate feature/plan differs')
            validate_plan(program,cert['candidate_plan']);validate_plan(program,m['plan'])
            if m['plan']['spacing'] != (3 if stage=='development' else 5) or m['tqec_commit']!=env['tqec_verification']['commit']:
                raise AssertionError('Geometry/compiler differs from stage')
            if [l['operation_ids'] for l in m['plan']['layers']]!=[l['operation_ids'] for l in candidate['plan']['layers']]:raise AssertionError('Compiled plan differs')
            if sorted(o['id'] for o in m['instruction_trace'])!=list(range(32)):raise AssertionError('Missing complete instruction')
            for op in m['instruction_trace']:
                if any(op[k]!=val for k,val in program['operations'][op['id']].items()):raise AssertionError('Original instruction changed')
            if not v['all_signed_inputs_passed'] or not v['full_source_tableau_including_frame_passed'] or len(v['signed_inputs'])!=16 or len(v['final_faults'])!=4 or len(v['conjugate_x_generators'])!=4 or v['shortest_graphlike_error']!=3:raise AssertionError('Physical validation incomplete')
            for g in v['conjugate_x_generators']:
                if len(g['validation']['signed_inputs'])!=16 or not g['validation']['all_signed_inputs_passed']:raise AssertionError('X validation incomplete')
            for signed in v['signed_inputs']:
                sim=stim.TableauSimulator()
                for q,bit in enumerate(signed['input_signs']):
                    if bit:sim.x(q)
                sim.do(logical_circuit(program))
                expected=[int(sim.measure(q)) for q in range(4)]
                if classical_bits(m,signed['observable_parities'])!=expected:raise AssertionError('Original classical output changed')
                readout_checks+=1
            for suffix,key in (('_ideal.stim','ideal_circuit_sha256'),('.stim','noisy_circuit_sha256'),('.dem','dem_sha256')):
                path=folder/'samples'/(r['sample_id']+suffix)
                a=stim.DetectorErrorModel.from_file(path) if suffix=='.dem' else stim.Circuit.from_file(path)
                if circuit_digest(a)!=r[key]:raise AssertionError('Full circuit/DEM hash mismatch')
                if suffix=='.stim':
                    for field in ('num_ticks','num_qubits','num_detectors','num_observables'):
                        if r[field]!=getattr(a,field):raise AssertionError('Compiled metric mismatch')
            if (r['ideal_circuit_sha256'],r['noisy_circuit_sha256'])!=(cert['ideal_circuit_sha256'],cert['noisy_circuit_sha256']):raise AssertionError('Certificate hashes mismatch')
            for key,value in [('model_id',PROTOCOL['model_id']),('decoder_id',PROTOCOL['decoder_id']),('physical_p',.001),('distance',3),('shots',100000),('source_sha256',program['source_sha256'])]:
                if r[key]!=value:raise AssertionError('Comparison condition mismatch')
            if sum(b['shots'] for b in r['batches'])!=r['shots'] or sum(b['failures_any'] for b in r['batches'])!=r['failures_any']:raise AssertionError('Batch counts mismatch')
            if np.sum([b['failures_by_observable'] for b in r['batches']],axis=0).tolist()!=r['failures_by_observable']:raise AssertionError('Observable counts mismatch')
            if list(wilson_interval(r['failures_any'],r['shots']))!=[r['wilson95_low'],r['wilson95_high']] or r['p_fail_any']!=r['failures_any']/r['shots']:raise AssertionError('Rate/CI mismatch')
            if r['reused_from']:
                old=json.loads((ROOT/r['reused_from']).read_text())
                for key in ('ideal_circuit_sha256','noisy_circuit_sha256','dem_sha256','shots','seed','batches','failures_any'):
                    if old[key]!=r[key]:raise AssertionError('Prior full-circuit sample differs')
                if stage!='development' or r['new_shots']!=0:raise AssertionError('Heldout leaked/reuse miscount')
            elif r['new_shots']!=r['shots']:raise AssertionError('New shot count mismatch')
        if len(local_hashes)!=s['sampled_unique_circuits'] or sum(r['new_shots'] for r in s['records'])!=s['new_shots']:raise AssertionError('Unique sample accounting differs')
    result={'passed':True,'complete_original_instructions':program['operation_counts'],'development_candidates':13,'heldout_sampled':7,
        'heldout_complete_candidate_pool':13,'unique_circuits':len(hashes),'new_shots':sum(s['new_shots'] for s in stages.values()),
        'reused_shots':sum(r['shots'] for r in stages['development']['records'] if r['reused_from']),
        'signed_classical_output_checks':readout_checks,'pretest_frozen_commit':start['source_head'],
        'checks':['complete source and dependency/footprint plans','original classical outputs and full Clifford validation records','raw circuits and DEM hashes','batch counts and Wilson intervals','development-only fit, pretest commit and exact frozen decisions','unique new vs reused sample count']}
    save(folder/'record_audit.json',result)
    return stages,frozen


def report(folder):
    stages,frozen=audit(folder);observed={r['candidate_id']:r for r in stages['heldout']['records']};evaluations=[]
    for d in frozen['decisions']:
        first=observed[d['baseline_candidate_id']];second=observed[d['candidate_id']]
        evaluations.append({**d,'baseline_failures':first['failures_any'],'selected_failures':second['failures_any'],
             'shots_each':100000,**contrast(first,second)})
    # Pairwise matched-serial contrasts are descriptive, with Holm-adjusted p
    # intentionally not inferred from the individual score CIs.
    serial=[r for r in stages['heldout']['records'] if r['features']['cx_routing_steps']==4]
    save(folder/'evaluation.json',{'decisions':evaluations,'matched_serial_vs_p00':[{'first':'p00','second':r['candidate_id'],**contrast(observed['p00'],r)} for r in serial if r['candidate_id']!='p00'],
       'interval_note':'Newcombe pointwise95 independent-binomial contrasts. Identical selected circuit reuses identical sample and has exact0 difference. Six predeclared method/pool contrasts; no familywise claim.',
       'scope':'Same public circuit, unseen geometry only. Matched-serial controls do not establish superiority over unrestricted parallel scheduling.'})
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.8))
    model=frozen['models']['depth_wait']
    for stage,color,label in [('development','#187c9a','Development, spacing 3'),('heldout','#b45d24','Geometry held-out, spacing 5')]:
        rows=stages[stage]['records'];x=[r['features']['physical_layers'] for r in rows];y=np.array([r['p_fail_any']*100 for r in rows])
        ax.errorbar(x,y,yerr=[y-np.array([r['wilson95_low']*100 for r in rows]),np.array([r['wilson95_high']*100 for r in rows])-y],fmt='o',capsize=3,label=label,color=color)
    ax.set_xlabel('Physical H/CX layers (3 block-z each)');ax.set_ylabel('Any decoded output error (%)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    y=np.arange(len(serial));p=np.array([r['p_fail_any']*100 for r in serial])
    bx.errorbar(p,y,xerr=[p-np.array([r['wilson95_low']*100 for r in serial]),np.array([r['wilson95_high']*100 for r in serial])-p],fmt='o',capsize=3,color='#b45d24',label='Observed spacing 5')
    predicted=[100/(1+np.exp(-predict(model,r))) for r in serial]
    bx.scatter(predicted,y,marker='x',color='#187c9a',label='Frozen spacing-3 model')
    bx.set_yticks(y,[r['candidate_id'] for r in serial]);bx.invert_yaxis();bx.set_xlabel('Any decoded output error (%)');bx.set_title('Six matched serial plans');bx.grid(axis='x',alpha=.2);bx.legend(fontsize=8)
    fig.suptitle('Complete hs4_n4: exact candidate pool and geometry-held-out pilot',fontweight='bold')
    fig.text(.5,.018,'d=3, p=0.001; TQEC uniform depolarizing; ordinary MWPM; 100,000 shots/circuit; Wilson 95% CI\nOffline risk selection within depth ties. Geometry extrapolation is not held-out workload validation.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.09,1,.94]);dest=ROOT/'docs/figures';fig.savefig(dest/'public_candidate_holdout.png',dpi=180);fig.savefig(dest/'public_candidate_holdout.pdf');plt.close(fig)
    print(json.dumps({'audit':json.loads((folder/'record_audit.json').read_text()),'evaluations':evaluations,'development':[{k:r[k] for k in ('candidate_id','num_ticks','failures_any')} for r in stages['development']['records']],'heldout':[{k:r[k] for k in ('candidate_id','num_ticks','num_qubits','failures_any','wilson95_low','wilson95_high')} for r in stages['heldout']['records']]},indent=2))


def timing(folder):
    """Invoke separately, only after physical jobs and full tests have exited."""
    _,frozen=audit(folder);p=checked_program();records=[]
    for name,model,guarded in [('depth_only',frozen['models']['depth_only'],False),('depth_wait',frozen['models']['depth_wait'],False),('depth_wait_guard',frozen['models']['depth_wait'],True)]:
        def call():
            candidates=pool(p,5)
            return {which:select(candidates,model,which,guarded) for which in ('all','serial_matched')}
        for _ in range(3):call()
        seconds=[]
        for _ in range(25):
            start=time.perf_counter();d=call();seconds.append(time.perf_counter()-start)
        records.append({'method':name,'seconds':seconds,'median_seconds':statistics.median(seconds),'decisions':d,
            'candidate_features_evaluated':13,'frontier_cap':256})
    save(folder/'selector_timing_isolated.json',{'scope':'Exact candidate enumeration + footprint validation + feature extraction + frozen model scoring of both pools; excludes development calibration and physical compilation/Monte Carlo/MWPM. Not online DASCOT routing timing.',
        'warmups':3,'repeats':25,'records':records,'note':'Shared host possible; run separately after physical work and tests.'})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,default=ROOT/'results/public_candidates_2026-11-02');ap.add_argument('--timing',action='store_true');a=ap.parse_args()
    timing(a.results) if a.timing else report(a.results)
