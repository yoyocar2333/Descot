"""Full-source one/two-step controls; exact complete-circuit reuse, no new shots."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time

import stim
from core import load_core, COMMIT
from public_candidate_pool import digest, features
from public_clifford import generate_program, validate_physical
from public_lookahead import schedule
from run_public_candidates import checked_program
from run_surgery import save, MODEL, DECODER
from surgery import add_noise

ROOT=Path(__file__).resolve().parent
PRIOR=ROOT/'results/public_candidates_2026-11-02'
METHODS={'author_profile':('author_profile',None),'one_budget48':('one_step',None),
         'two_budget48':('two_step',None),'one_pool16':('one_step',16),'two_pool16':('two_step',16)}
PROTOCOL={'id':'complete_public_dag_lookahead_controls_20261103_v1','source':'complete pinned hs4_n4, all 32 instructions',
          'spacings':[3,5],'seeds':[1,2,3],'front_budget':48,'methods':METHODS,'mu':0,
          'metric':'Any of four independent terminal Z-correlation observables misdecoded, not fidelity',
          'status':'Post-pilot development integration; spacing5 is already observed, not new held-out evidence',
          'time_policy':'H and CX layer:3 block-z; X:virtual Pauli frame; all readout deferred to common end. TICKs from compiler; QEC rounds null.',
          'fairness':'Same order generator/physical footprint; fixed-pool one/two cap16 plus same ceiling48. Equal ceiling does not imply equal actual work. Author pinned search is an additional unmatched-cost reference.',
          'rollout':'Drain full ready X/readout and H closure after candidate before next CX rollout; track orientation. H duration counted in final schedule, not in the CX-progress score. Not a two-physical-layer lookahead.',
          'physical_policy':'Exact full-layer source signature and geometry; recompile complete ideal/noisy/DEM once per distinct output. Prior counts and complete validation reused only if exact hashes match.',
          'timing':'After physics and full tests:3 warmups,25 repeats, rotated method order; source scheduling only, no model fit/physical compiler/MC/MWPM. Shared host possible.'}


def signature(plan):
    return [(l['kind'],sorted(l['operation_ids']),l['orientation_before'],l['orientation_after']) for l in plan['layers']]


def choose(program,base,method,spacing,seed):
    mode,cap=METHODS[method]
    return schedule(program,mode,spacing,seed,budget=48,candidate_cap=cap,base=base)


def evidence(output):
    if output.exists():raise FileExistsError('Use fresh output; preserve frozen evidence')
    output.mkdir(parents=True);(output/'routes').mkdir()
    p=checked_program();base=load_core(ROOT.parent/'external/wisq')['sarouting'];records=[];physical=[]
    save(output/'protocol.json',PROTOCOL)
    save(output/'environment.json',{'python':platform.python_version(),'wisq_commit':COMMIT,
        'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_files_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in
        ('public_lookahead.py','run_public_lookahead.py','public_clifford.py','lookahead.py','requirements-lock.txt')}})
    for spacing,stage in [(3,'development'),(5,'heldout')]:
        prior=json.loads((PRIOR/(stage+'_summary.json')).read_text())['records']
        for seed in (1,2,3):
            for method in METHODS:
                result=choose(p,base,method,spacing,seed)
                match=[]
                for record in prior:
                    cert=json.loads((PRIOR/'certificates'/(record['record_id']+'.json')).read_text())
                    if signature(result['plan'])==signature(cert['candidate_plan']):match.append(record)
                if len(match)!=1:raise AssertionError('Must have one exact previously validated complete source plan')
                ref=match[0]; name=f'spacing{spacing}_{method}_s{seed}'
                save(output/'routes'/(name+'.json'),result)
                records.append({'id':name,'spacing':spacing,'method':method,'seed':seed,
                    'candidate_id':ref['candidate_id'],'source_sha256':p['source_sha256'],
                    'features':features(p,result['plan']),'noisy_circuit_sha256':ref['noisy_circuit_sha256'],
                    'reference_record':str((PRIOR/'samples'/(ref['sample_id']+'.json')).relative_to(ROOT)),
                    'new_shots':0,'reused_sample_shots':ref['shots'],'failures_any':ref['failures_any'],
                    'wilson95':[ref['wilson95_low'],ref['wilson95_high']],
                    'num_ticks':ref['num_ticks'],'num_qubits':ref['num_qubits'],'model_id':MODEL,'decoder_id':DECODER,
                    'cost':result['cost']})
                if not any(r['spacing']==spacing for r in physical):
                    start=time.perf_counter();ideal,meta=generate_program(p,result['plan'])
                    noisy=add_noise(ideal,.001);dem=noisy.detector_error_model(decompose_errors=True)
                    hashes={key:hashlib.sha256(str(obj).encode()).hexdigest() for key,obj in
                        [('ideal_circuit_sha256',ideal),('noisy_circuit_sha256',noisy),('dem_sha256',dem)]}
                    if any(ref[k]!=v for k,v in hashes.items()):raise AssertionError('Fresh complete compiler replay differs from prior circuit')
                    validation=validate_physical(ideal,meta,p,8,True)
                    physical.append({'spacing':spacing,'reference_record':ref['record_id'],**hashes,
                        'signed_z_validation':validation,'complete_original_instructions':len(meta['instruction_trace']),
                        'shortest_graphlike_error':len(noisy.shortest_graphlike_error()),
                        'prior_conjugate_x_generator_validation':'Reused only for exact complete ideal/noisy circuit identity; original certificates archived.',
                        'compiler_replay_validation_seconds':time.perf_counter()-start})
    # Compare evaluated candidate order pools at each actual common source state.
    pools=[]
    for spacing in (3,5):
        for seed in (1,2,3):
            a=json.loads((output/'routes'/f'spacing{spacing}_one_pool16_s{seed}.json').read_text())
            b=json.loads((output/'routes'/f'spacing{spacing}_two_pool16_s{seed}.json').read_text())
            checks=[(x['ready_ids'],x['candidate_orders'])==(y['ready_ids'],y['candidate_orders']) for x,y in zip(a['fronts'],b['fronts'])]
            if len(a['fronts'])!=len(b['fronts']) or not all(checks):raise AssertionError('Observed fixed candidate pool comparison differs')
            pools.append({'spacing':spacing,'seed':seed,'same_evaluated_candidate_pools':True,'fronts':len(checks)})
    save(output/'summary.json',{'protocol':PROTOCOL,'records':records,'compile_replays':physical,'fixed_pool_checks':pools,
        'source_conditions':len(records),'unique_complete_circuits':len(physical),'new_shots':0,
        'reused_shots_unique':sum(next(r['reused_sample_shots'] for r in records if r['spacing']==s) for s in (3,5)),
        'conclusion':'All methods select existing p12 parallel schedule. Algorithm and extra-risk gains on this source are zero; no artificial serial one-step baseline.'})
    print(json.dumps({'source_conditions':len(records),'new_shots':0,'unique_reused_circuits':len(physical)},indent=2))


def timing(output):
    summary=json.loads((output/'summary.json').read_text());p=checked_program();base=load_core(ROOT.parent/'external/wisq')['sarouting']
    durations={};hashes={}
    for row in summary['records']:
        key=row['id'];durations[key]=[]
        for _ in range(3):choose(p,base,row['method'],row['spacing'],row['seed'])
        hashes[key]=digest(json.loads((output/'routes'/(key+'.json')).read_text())['plan'])
    for repeat in range(25):
        rows=summary['records'];offset=repeat%len(rows)
        for row in rows[offset:]+rows[:offset]:
            start=time.perf_counter();result=choose(p,base,row['method'],row['spacing'],row['seed'])
            duration=time.perf_counter()-start
            if digest(result['plan'])!=hashes[row['id']]:raise AssertionError('Timing changed schedule')
            durations[row['id']].append(duration)
    save(output/'routing_timing_isolated.json',{'scope':PROTOCOL['timing'],'warmups':3,'repetitions':25,
        'records':[{'id':k,'seconds':v,'median_seconds':statistics.median(v)} for k,v in durations.items()]})


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'results/public_lookahead_2026-11-03');ap.add_argument('--timing',action='store_true');a=ap.parse_args()
    timing(a.output) if a.timing else evidence(a.output)
