"""Reconcile complete Bell records, prospective freeze and scientific figures."""
import hashlib
import json
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import stim

from bell_benchmark import ROOT
from public_clifford import validate_plan
from memory_calibration_previous import wilson_interval
from public_candidate_pool import features
from report_schedule_pilot import contrast
from run_bell_benchmark import PROTOCOL, program, sha, objsha
from run_surgery import save

FOLDER=ROOT/'results/public_bell_2026-11-04'


def audit(folder):
    summary=json.loads((folder/'summary.json').read_text())
    frozen=json.loads((folder/'frozen_design.json').read_text())
    start=json.loads((folder/'run_start.json').read_text());p=program()
    if summary['protocol']!=json.loads(json.dumps(PROTOCOL)):raise AssertionError('Protocol differs')
    if start['frozen_design_sha256']!=sha(folder/'frozen_design.json'):raise AssertionError('Post-test design change')
    rel=(folder/'frozen_design.json').relative_to(ROOT).as_posix()
    if subprocess.check_output(['git','show',start['source_freeze_commit']+':'+rel],cwd=ROOT)!=(folder/'frozen_design.json').read_bytes():
        raise AssertionError('Pre-test commit differs')
    for f,h in frozen['source_files_sha256'].items():
        if sha(ROOT/f)!=h:raise AssertionError('Frozen source changed: '+f)
    hashes=set();checks=0
    for r in summary['records']:
        if r['noisy_circuit_sha256'] in hashes:raise AssertionError('Duplicate sample')
        hashes.add(r['noisy_circuit_sha256'])
        cert=json.loads((folder/'certificates'/(r['record_id']+'.json')).read_text())
        m=cert['backend_meta'];v=cert['physical_validation']
        validate_plan(p,m['plan'])
        if features(p,m['plan'])!=r['features']:raise AssertionError('Resource or timing feature differs')
        if sorted(o['id'] for o in m['instruction_trace'])!=list(range(13)):raise AssertionError('Missing source instruction')
        for o in m['instruction_trace']:
            if any(o[k]!=value for k,value in p['operations'][o['id']].items()):raise AssertionError('Source semantic change')
        if not v['all_signed_inputs_passed'] or len(v['signed_inputs'])!=64:raise AssertionError('Signed Z checks incomplete')
        if {g['input_generator'] for g in v['all_clifford_generators']}!={a+str(q) for a in 'XZ' for q in range(6)}:
            raise AssertionError('Full 12-generator validation absent')
        for g in v['all_clifford_generators']:
            if len(g['validation']['signed_inputs'])!=64 or not g['validation']['full_source_tableau_including_frame_passed'] or not g['observable_combination']:
                raise AssertionError('Incomplete generator validation')
        z=v['original_readout']
        if z['independent_z_observables']!=3 or len(z['original_output_distribution'])!=8 or len(z['known_final_logical_faults'])!=6:
            raise AssertionError('Original random-output readout differs')
        for suffix,key in [('_ideal.stim','ideal_circuit_sha256'),('.stim','noisy_circuit_sha256'),('.dem','dem_sha256')]:
            path=folder/'samples'/(r['sample_id']+suffix)
            obj=stim.DetectorErrorModel.from_file(path) if suffix=='.dem' else stim.Circuit.from_file(path)
            if objsha(obj)!=r[key]:raise AssertionError('Complete circuit/DEM differs')
            if suffix=='.stim':
                for k in ('num_qubits','num_ticks','num_detectors','num_observables'):
                    if getattr(obj,k)!=r[k]:raise AssertionError('Compiled metric differs')
                if len(obj.shortest_graphlike_error())!=3:raise AssertionError('Distance mismatch')
        if sum(b['shots'] for b in r['batches'])!=r['shots'] or sum(b['failures_any'] for b in r['batches'])!=r['failures_any']:
            raise AssertionError('Batch count mismatch')
        if np.sum([b['failures_by_observable'] for b in r['batches']],axis=0).tolist()!=r['failures_by_observable']:
            raise AssertionError('Observable counts mismatch')
        if list(wilson_interval(r['failures_any'],r['shots']))!=[r['wilson95_low'],r['wilson95_high']]:raise AssertionError('CI differs')
        if r['source_sha256']!=p['source_sha256'] or r['model_id']!=PROTOCOL['model_id'] or r['decoder_id']!=PROTOCOL['decoder_id'] or r['physical_p']!=.001 or r['distance']!=3 or r['shots']!=100000:
            raise AssertionError('Comparison conditions differ')
        checks+=64+64*12
    if sum(r['new_shots'] for r in summary['records'])!=400000:raise AssertionError('Unique shot accounting differs')
    samples={r['sample_id']:r for r in summary['records']}
    if len(summary['method_sample_matches'])!=30:raise AssertionError('Method mappings missing')
    for match in summary['method_sample_matches']:
        if match['sample_id'] not in samples or match['new_shots']!=0:raise AssertionError('Method double-counted samples')
    result={'passed':True,'unique_circuits':len(hashes),'new_shots':400000,'original_instructions':13,
        'physical_signed_boundary_settings':checks,'source_freeze_commit':start['source_freeze_commit'],
        'checks':['pre-test frozen source/design','all original gate/barrier/classical dependencies','all 12 Clifford generators per circuit','complete original random Z-output subgroup','known final faults and graphlike distance3','full circuit and DEM hashes','raw batches, Wilson95 and unique-shot accounting']}
    save(folder/'record_audit.json',result)
    return summary


def report(folder=FOLDER):
    summary=audit(folder);records=summary['records'];pairs=[];resources=[]
    for r in records:
        m=json.loads((folder/'certificates'/(r['record_id']+'.json')).read_text())['backend_meta']
        times={f['start_block_z'] for f in m['gate_footprints']}
        peak=max((sum(len(f['reserved_xy'])-2 for f in m['gate_footprints'] if f['start_block_z']==z) for z in times),default=0)
        resources.append({'record_id':r['record_id'],'peak_ancilla_reserved_xy_blocks':peak,'peak_data_plus_ancilla_reserved_xy_blocks':6+peak,'compiled_unique_physical_qubits':r['num_qubits'],'template_block_z':r['features']['template_block_z'],'total_protected_idle_block_z':r['features']['total_protected_idle_block_z'],'data_reservation_block_z':r['features']['data_reservation_block_z'],'ancilla_reservation_block_z':r['features']['ancilla_reservation_block_z']})
    for spacing in (3,5):
        serial=next(r for r in records if r['spacing']==spacing and r['mode']=='serial')
        parallel=next(r for r in records if r['spacing']==spacing and r['mode']=='parallel')
        pairs.append({'spacing':spacing,'first':serial['record_id'],'second':parallel['record_id'],**contrast(serial,parallel)})
    save(folder/'evaluation.json',{'serial_to_parallel':pairs,'algorithm_gain':0,'resources':resources,
        'interpretation':'Serial is a structural control, not a one-step algorithm. All source algorithms select the same parallel circuit; exact zero difference using shared counts.',
        'ci_policy':'Wilson95 rates; pointwise independent-binomial Newcombe95 for parallel minus serial, not simultaneous familywise intervals. Cross-geometry resources differ.'})
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(10.6,4.5))
    colors={3:'#187c9a',5:'#b45d24'}
    for spacing in (3,5):
        rows=sorted([r for r in records if r['spacing']==spacing],key=lambda r:r['features']['cx_routing_steps'])
        y=np.array([r['p_fail_any']*100 for r in rows])
        ax.errorbar([r['num_ticks'] for r in rows],y,yerr=[y-np.array([r['wilson95_low']*100 for r in rows]),np.array([r['wilson95_high']*100 for r in rows])-y],fmt='o-',color=colors[spacing],capsize=3,label=f'Spacing {spacing}')
        for r in rows:ax.annotate(r['mode'],(r['num_ticks'],r['p_fail_any']*100),xytext=(5,5),textcoords='offset points',fontsize=8)
        bx.scatter([r['num_qubits'] for r in rows],[r['p_fail_any']*100 for r in rows],c=colors[spacing],marker='s' if spacing==3 else 'o',label=f'Spacing {spacing}')
        for r in rows:bx.annotate(f"{r['mode']}, {r['num_ticks']} TICKs",(r['num_qubits'],r['p_fail_any']*100),xytext=(5,4),textcoords='offset points',fontsize=8)
    ax.set_xlabel('Actual compiled Stim TICKs');ax.set_ylabel('Any decoded ZZ-correlation error (%)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    bx.set_xlabel('Unique physical qubits in complete circuit');bx.set_ylabel('Any decoded ZZ-correlation error (%)');bx.grid(alpha=.2);bx.margins(x=.32)
    fig.suptitle('Complete MQT Bell(6): scheduling and geometry controls',fontweight='bold')
    fig.text(.5,.015,'d=3, p=0.001; TQEC uniform depolarizing; ordinary MWPM; 100,000 shots/circuit; Wilson 95% CI\nAll tested source algorithms choose parallel. Random original outputs retained; metric is three independent ZZ correlations.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.11,1,.94]);dest=ROOT/'docs/figures'
    for suffix in ('png','pdf'):fig.savefig(dest/('public_bell_controls.'+suffix),dpi=180)
    plt.close(fig)
    print(json.dumps({'audit':json.loads((folder/'record_audit.json').read_text()),'contrasts':pairs},indent=2))


if __name__=='__main__':report()
