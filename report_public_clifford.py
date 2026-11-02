"""Reconcile complete public-workload raw records and make scientific figures."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import stim

from memory_calibration_previous import wilson_interval
from public_clifford import validate_plan, load_program, logical_circuit
from public_readout import classical_bits
from report_schedule_pilot import contrast
from run_public_clifford import PROTOCOL
from run_surgery import save

ROOT=Path(__file__).resolve().parent


def audit(folder):
    s=json.loads((folder/'summary.json').read_text())
    if s['protocol']!=PROTOCOL:raise AssertionError('Protocol changed')
    for name,sha in s['environment']['source_files_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise AssertionError('Experiment source changed: '+name)
    source=s['environment']['upstream_source']
    program=load_program(ROOT/source['path'])
    if source['sha256']!=program['source_sha256']:raise AssertionError('Pinned complete source changed')
    if json.loads((folder/'program.json').read_text())!=program:raise AssertionError('Original program changed')
    hashes=set(); readout_records=[]
    for r in s['records']:
        if r['noisy_circuit_sha256'] in hashes:raise AssertionError('Duplicate sampling')
        hashes.add(r['noisy_circuit_sha256'])
        for suffix,key in (('_ideal.stim','ideal_circuit_sha256'),('.stim','noisy_circuit_sha256'),('.dem','dem_sha256')):
            path=folder/'samples'/(r['sample_id']+suffix)
            value=stim.DetectorErrorModel.from_file(path) if suffix=='.dem' else stim.Circuit.from_file(path)
            if hashlib.sha256(str(value).encode()).hexdigest()!=r[key]:raise AssertionError('Circuit/DEM hash changed')
        circuit=stim.Circuit.from_file(folder/'samples'/(r['sample_id']+'.stim'))
        for key in ('num_qubits','num_ticks','num_detectors','num_observables'):
            if r[key]!=getattr(circuit,key):raise AssertionError('Circuit metrics changed')
        if r['source_sha256']!=program['source_sha256'] or r['source_operation_counts']!=program['operation_counts']:
            raise AssertionError('Benchmark instructions changed')
        if sum(b['shots'] for b in r['batches'])!=r['shots'] or sum(b['failures_any'] for b in r['batches'])!=r['failures_any']:
            raise AssertionError('Raw counts differ')
        if np.array([b['failures_by_observable'] for b in r['batches']]).sum(axis=0).tolist()!=r['failures_by_observable']:
            raise AssertionError('Observable counts differ')
        if wilson_interval(r['failures_any'],r['shots'])!=(r['wilson95_low'],r['wilson95_high']):raise AssertionError('CI differs')
        if r['p_fail_any']!=r['failures_any']/r['shots']:raise AssertionError('Rate differs')
        for key,value in (('distance',3),('physical_p',.001),('shots',100000),('model_id',PROTOCOL['model_id']),('decoder_id',PROTOCOL['decoder_id'])):
            if r[key]!=value:raise AssertionError('Comparison conditions differ')
        cert=json.loads((folder/'certificates'/(r['record_id']+'.json')).read_text());meta=cert['backend_meta'];v=cert['physical_validation']
        validate_plan(program,meta['plan'])
        trace=meta['instruction_trace']
        if sorted(row['id'] for row in trace)!=list(range(len(program['operations']))):raise AssertionError('Instruction missing')
        for row in trace:
            if any(row[k]!=value for k,value in program['operations'][row['id']].items()):raise AssertionError('Instruction changed')
            if row['name']=='measure' and row['end_block_z']!=meta['output_z']:raise AssertionError('Readout lifetime changed')
        if not v['all_signed_inputs_passed'] or not v['full_source_tableau_including_frame_passed'] or len(v['signed_inputs'])!=16 or len(v['final_faults'])!=4 or len(v['conjugate_x_generators'])!=4 or v['shortest_graphlike_error']!=3:
            raise AssertionError('Physical validation incomplete')
        if any(len(g['validation']['signed_inputs'])!=16 or not g['validation']['full_source_tableau_including_frame_passed'] for g in v['conjugate_x_generators']):
            raise AssertionError('Conjugate generator validation incomplete')
        for row in v['signed_inputs']:
            reference=stim.TableauSimulator()
            for q,bit in enumerate(row['input_signs']):
                if bit: reference.x(q)
            reference.do(logical_circuit(program))
            expected=[int(reference.measure(q)) for q in range(4)]
            actual=classical_bits(meta,row['observable_parities'])
            if actual!=expected:raise AssertionError('Original classical outputs differ')
            readout_records.append({'record_id':r['record_id'],'input_signs':row['input_signs'],'classical_bits_c0_first':actual,'reference':expected})
        if r['ideal_circuit_sha256']!=cert['ideal_circuit_sha256'] or r['noisy_circuit_sha256']!=cert['noisy_circuit_sha256']:raise AssertionError('Certificate mismatch')
    if len(hashes)!=s['unique_sampled_circuits'] or sum(r['shots'] for r in s['records'])!=s['new_monte_carlo_shots']:raise AssertionError('Unique shot count differs')
    result={'passed':True,'full_original_operations':program['operation_counts'],'conditions':len(hashes),'unique_sampled_circuits':len(hashes),'new_monte_carlo_shots':s['new_monte_carlo_shots'],
        'checks':['fixed complete source and instruction DAG','all H/X/CX/readout trace and original classical mapping','source and circuit/DEM hashes','all signed inputs and final faults','conjugate X-generator physical validation and frame propagation','batch counts, intervals, comparison conditions and unique shot count'],
        'scope':'Audit uses stored physical-validation records; no new sampling or compiler execution'}
    save(folder/'readout_validation.json',{'source_sha256':program['source_sha256'],'readout_helper_sha256':hashlib.sha256((ROOT/'public_readout.py').read_bytes()).hexdigest(),'all_original_classical_outputs_passed':True,'records':readout_records})
    save(folder/'record_audit.json',result)
    return s


def report(folder):
    summary=audit(folder);records=summary['records'];ref=records[0]
    comparisons=[{'first':ref['record_id'],'second':r['record_id'],**contrast(ref,r)} for r in records[1:]]
    comparisons.append({'first':records[1]['record_id'],'second':records[2]['record_id'],**contrast(records[1],records[2])})
    save(folder/'contrasts.json',{'method':'Newcombe independent binomial score; exploratory pointwise 95%, no familywise correction','comparisons':comparisons})
    labels=['Parallel, spacing 3','Serial, spacing 3','Reverse serial, spacing 3','Parallel, spacing 4']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.3),gridspec_kw={'width_ratios':[1.4,1]})
    y=np.arange(len(records));p=np.array([r['p_fail_any']*100 for r in records]);lo=np.array([r['wilson95_low']*100 for r in records]);hi=np.array([r['wilson95_high']*100 for r in records])
    ax.errorbar(p,y,xerr=[p-lo,hi-p],fmt='o',capsize=4,color='#126d90')
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel('Any corrected output-bit decoding error (%)');ax.grid(axis='x',alpha=.2)
    bx.bar(y,[r['num_ticks'] for r in records],color=['#126d90','#85a9ba','#85a9ba','#d8a438'])
    bx.set_xticks(y,['P3','S3','RS3','P4']);bx.set_ylabel('Compiled Stim TICKs');bx.grid(axis='y',alpha=.2)
    for i,r in enumerate(records):bx.text(i,r['num_ticks']+4,str(r['num_qubits'])+' q',ha='center',fontsize=9)
    fig.suptitle('Complete QASMBench hs4_n4: retained H/X/CX/readout',fontweight='bold')
    fig.text(.5,.015,'d=3, p=0.001; TQEC uniform depolarizing; ordinary MWPM; 100,000 shots/condition; Wilson 95% CI\nX uses a declared zero-time Pauli frame. Structural controls; no held-out scheduler claim.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.1,1,.93]);dest=ROOT/'docs/figures';dest.mkdir(exist_ok=True)
    fig.savefig(dest/'public_hs4.png',dpi=180);fig.savefig(dest/'public_hs4.pdf');plt.close(fig)
    plot_timeline(folder,records)
    print(json.dumps({'audit':'passed','records':[{k:r[k] for k in ('record_id','num_ticks','num_qubits','cx_routing_steps','logical_h_layers','template_block_z','failures_any','shots','p_fail_any','wilson95_low','wilson95_high')} for r in records],'comparisons':comparisons},indent=2))


def plot_timeline(folder,records):
    from matplotlib.patches import Rectangle, Patch
    fig,axes=plt.subplots(3,1,figsize=(11,7),sharex=True)
    labels=['Parallel','Serial','Reverse serial']
    for ax,r,label in zip(axes,records[:3],labels):
        meta=json.loads((folder/'certificates'/(r['record_id']+'.json')).read_text())['backend_meta']
        for q in range(4):ax.add_patch(Rectangle((0,q-.35),meta['output_z'],.7,color='#eeeeee'))
        for op in meta['instruction_trace']:
            if op['name'] not in ('h','cx'):continue
            a,b=op['start_block_z'],op['end_block_z'];qs=op['qubits'];color='#126d90' if op['name']=='h' else '#d8a438'
            for q in qs:ax.add_patch(Rectangle((a+.08,q-.3),b-a-.16,.6,color=color,zorder=2))
            if op['name']=='cx':
                x=(a+b)/2;ax.plot([x,x],[min(qs),max(qs)],color=color,lw=2,zorder=3)
        ax.axvline(meta['output_z'],color='#a44338',lw=1.5)
        ax.set_yticks(range(4),['q0','q1','q2','q3']);ax.set_ylim(3.55,-.55)
        ax.set_title(f"{label}: {r['num_ticks']} TICKs, {r['num_qubits']} physical qubits",loc='left',fontweight='bold')
        ax.grid(axis='x',alpha=.15);ax.set_xlim(0,49)
    axes[-1].set_xlabel('Template block-z (not QEC rounds or Stim TICKs)')
    axes[0].legend(handles=[Patch(color='#126d90',label='Physical H'),Patch(color='#d8a438',label='Physical CX'),Patch(color='#eeeeee',label='Protected memory')],loc='upper right',ncol=3,fontsize=8)
    fig.suptitle('Complete hs4_n4 instruction placement and live memory',fontweight='bold')
    fig.text(.5,.012,'All X updates remain in the Pauli frame; all original measurements are deferred to the common final boundary (red).',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.035,1,.96]);dest=ROOT/'docs/figures'
    fig.savefig(dest/'public_hs4_timeline.png',dpi=180);fig.savefig(dest/'public_hs4_timeline.pdf');plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--results',type=Path,default=ROOT/'results/public_hs4_2026-11-02');report(parser.parse_args().results)
