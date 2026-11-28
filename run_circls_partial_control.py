"""Frozen zero-shot native PPM control for all nine complete public BV minima."""
import argparse
from collections import Counter
import gzip
import importlib.metadata as md
import json
import os
from pathlib import Path
import platform
import subprocess
import time
from types import SimpleNamespace
import stim
import pymatching
from circls_native_control import COMMIT, load_author, basis_view, evaluate, rank
from circls_partial_control import prepare, literal_joint_specs, record_fault
from public_partial_readout import load_partial_program
from public_candidate_pool import digest
from run_circls_native_control import sha, save, normalize, environment
from decoder_mechanism_control import diagnose

ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT/'results/circls_partial_bv_2026-11-28'
CODE = ['circls_partial_control.py','run_circls_partial_control.py',
        'tests/test_circls_partial_control.py','circls_native_control.py',
        'public_partial_readout.py','requirements-lock.txt','requirements-circls-extra-2026-11-21.txt']
PROTOCOL = dict(id='circls_partial_public_bv_native_ppm_v1', author_commit=COMMIT,
    source='benchmarks/public_2026-11-27/mqt/bv_n3_11.qasm',
    source_revision='8f919416457d76b256930443078334021634236f', family='bernstein_vazirani development',
    full_source='All9 original instructions; all13 lowered instruction IDs in each source trace. Original2 measurements become explicit original-output Pauli IR, not deleted or completed to3 application outputs.',
    entry='Documented compile_ppm_sequence after original nwqec pullback, selected original outputs, native re-selection/sweep/schedule passes; not unmodified compile_qasm.',
    configs=['full','no_sched'], plan_count=9, signed_input_masks=list(range(8)),
    main_conditions='Both configs on all9 minima; all7 nonzero signed inputs on b08 only',
    main_compile_ceiling=32, noise='Original CircLS inject_uniform_noise p=0.001; distinct from TQEC noise',
    distance=3, decoder='ordinary uncorrelated PyMatching MWPM, complete original2-output basis',
    units='Native T1_rounds is measurement-containing moments, not a validated QEC-round conversion. QEC rounds=null; native measurement layers and Stim TICK recorded separately.',
    validation='All3 source Clifford pullbacks, original output reconstruction/signs, nonempty rank2 actual record basis, physical measurement fault responses, deterministic DEM, graphlike distance3; exhaustive single-DEM-mechanism audit.',
    shots=0, seeds=[], counts=None, confidence_interval=None, sampler_calls=0,
    calibration=False, held_out_sampling_allowed=False, mu=0,
    scope='Native partial-output compiler/PPM control for a complete public application; not gate-preserving same-pool/equal-CPU scheduler efficacy.',
    stop='Stop on source/pass/record/sign/distance mismatch; preserve all candidates and old results. No noisy sampling or selector tuning.')


def journal(output, event, **kw):
    with (output/'journal.jsonl').open('a') as f:
        f.write(json.dumps(dict(event=event, **kw))+'\n'); f.flush(); os.fsync(f.fileno())


def frozen(repo):
    env = environment(repo)
    env['partial_code_sha256'] = {f:sha((ROOT/f).read_bytes()) for f in CODE}
    for f in ['benchmarks/public_2026-11-27/manifest.json', PROTOCOL['source'],
              'results/public_bv_2026-11-27/candidate_pool.json',
              'benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-27_BV.json']:
        env['partial_code_sha256'][f] = sha((ROOT/f).read_bytes())
    return env


def artifact(output, obj, suffix):
    data = str(obj).encode(); h = sha(data)
    (output/'artifacts'/(h+suffix)).write_bytes(data)
    return h


def run_one(program, row, config, mask, output):
    from ablation import compile_kwargs
    from circls import compile_ppm_sequence
    from circls.pipeline import graphlike_detectors_pass
    from circls.tools.evaluate import inject_uniform_noise
    from circls.tools.reporting import _tracker_bit_specs
    began = time.perf_counter()
    kw = compile_kwargs(config, SimpleNamespace(name='bv_public_partial',tags=()))
    reduction = kw.pop('measure_reduction'); scheduled = kw.pop('step_scheduling')
    assert reduction is True
    prog, reconstruction, trace, meta = prepare(program, row['plan'], mask, scheduled)
    front_seconds = time.perf_counter()-began
    key = f'{config}_{row["candidate_id"]}_m{mask}'
    journal(output,'compile_started',key=key)
    began = time.perf_counter()
    try:
        cp = compile_ppm_sequence(prog,distance=3,**kw)
        cp.circuit = graphlike_detectors_pass(cp.circuit)
        cp.reconstruction = reconstruction; cp.m_load_trace = trace
    except BaseException as e:
        journal(output,'compile_failed',key=key,error=repr(e),seconds=time.perf_counter()-began)
        raise
    compile_seconds = time.perf_counter()-began
    journal(output,'compile_finished',key=key,seconds=compile_seconds,
            native_ideal_sha256=sha(str(cp.circuit).encode()))
    began = time.perf_counter(); specs = literal_joint_specs(cp)
    expected = [((mask>>r['qubit'])^(mask>>0)^1)&1 for r in meta['original_output_mapping']]
    got = evaluate(cp.circuit.reference_sample(),specs)
    if got != expected: raise AssertionError('Original full-output values differ')
    view = basis_view(cp.circuit,specs)
    view.detector_error_model()
    if cp.program.num_data != 3 or len(specs) != 2 or len(cp.experiment.ppm_sequence) != 2:
        raise AssertionError('Flag/original-output/joint-PPM domain changed')
    # Two independent record columns: physical readout Pauli faults must be visible.
    columns = {}; faults = []
    for rec in sorted({i for ids,_ in specs for i in ids}):
        col = sum((rec in ids)<<k for k,(ids,_) in enumerate(specs))
        if rank(list(columns)+[col]) > len(columns): columns[col] = rec
        if len(columns)==2: break
    for col,rec in columns.items():
        changed = evaluate(record_fault(cp.circuit,rec).reference_sample(),specs)
        delta = sum((a^b)<<k for k,(a,b) in enumerate(zip(got,changed)))
        if delta != col: raise AssertionError('Physical readout fault response differs')
        faults.append(dict(record=rec,expected_output_flip_mask=col,observed_output_flip_mask=delta))
    if len(columns)!=2: raise AssertionError('Fault response lacks full output rank')
    exact_seconds = time.perf_counter()-began
    began = time.perf_counter(); noisy = inject_uniform_noise(view,.001)
    dem = noisy.detector_error_model(decompose_errors=True)
    pymatching.Matching.from_detector_error_model(dem)
    dem_seconds = time.perf_counter()-began
    began = time.perf_counter(); distance = len(noisy.shortest_graphlike_error())
    if distance!=3: raise AssertionError('Original two-output basis lacks distance3')
    distance_seconds = time.perf_counter()-began
    hashes = {name+'_sha256':artifact(output,obj,ext) for name,obj,ext in [
        ('native_ideal',cp.circuit,'.stim'),('ideal',view,'.stim'),('noisy',noisy,'.stim'),('dem',dem,'.dem')]}
    record = dict(key=key,candidate_id=row['candidate_id'],config=config,input_mask=mask,
        source_sha256=program['source_sha256'],plan_sha256=row['plan_sha256'],
        unitary_qasm_sha256=sha(meta['unitary_qasm'].encode()),**meta,
        native_program=normalize(cp.program),native_reconstruction=normalize(reconstruction),
        native_m_load_trace=trace,native_compile_kwargs=normalize(kw),
        literal_output_specs=specs,p0_tracker_specs=_tracker_bit_specs(cp),
        expected_original_outputs=expected,physical_original_outputs=got,
        original_output_basis_rank=2,physical_faults=faults,graphlike_distance=distance,
        stats=cp.stats(),native_routes=normalize(cp.routes),native_lifetimes=normalize(cp.lifetimes),
        units=dict(cx_routing_steps=None,h_layers=None,template_block_z=None,
                   qec_rounds=None,native_measurement_layers=cp.stats()['T1_rounds'],stim_tick=view.num_ticks),
        timing=dict(frontend_seconds=front_seconds,physical_compile_seconds=compile_seconds,
            exact_validation_seconds=exact_seconds,noise_dem_decoder_construction_seconds=dem_seconds,
            distance_seconds=distance_seconds,routing_seconds=None,scorer_seconds=None,
            calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None),
        shots=0,counts=None,confidence_interval=None,gate_preserving_pool_admissible=False,**hashes)
    save(output/(key+'.json'),record)
    return record


def run(output,repo):
    if output.exists(): raise FileExistsError('Fresh output required')
    load_author(repo)
    if platform.python_version_tuple()[:2] != ('3','12'): raise ValueError('Python3.12 required')
    env = frozen(repo)
    program = load_partial_program(ROOT/PROTOCOL['source'])
    rows = json.loads((ROOT/'results/public_bv_2026-11-27/candidate_pool.json').read_text())
    assert len(rows)==9 and {r['candidate_id'] for r in rows}=={f'b{i:02}' for i in range(9)}
    output.mkdir(parents=True); (output/'artifacts').mkdir()
    save(output/'protocol.json',PROTOCOL); save(output/'freeze.json',env)
    records = []
    for config in PROTOCOL['configs']:
        for row in rows: records.append(run_one(program,row,config,0,output))
        for mask in range(1,8): records.append(run_one(program,rows[-1],config,mask,output))
    audits = []
    for h in sorted({r['dem_sha256'] for r in records}):
        result, raw, timing = diagnose(stim.DetectorErrorModel((output/'artifacts'/(h+'.dem')).read_text()))
        path = output/(h+'.jsonl.gz')
        with gzip.open(path,'wt') as f:
            for row in raw: f.write(json.dumps(row)+'\n')
        audits.append(dict(dem_sha256=h,raw_sha256=sha(path.read_bytes()),**result,timing=timing))
    main = [r for r in records if r['input_mask']==0]
    summary = dict(status='complete',native_compile_calls=len(records),main_conditions=len(main),
        candidate_count=9,configs=PROTOCOL['configs'],signed_inputs_per_config=8,
        unique_main_ideal_hashes=len({r['ideal_sha256'] for r in main}),
        unique_main_noisy_hashes=len({r['noisy_sha256'] for r in main}),
        native_ppm_steps=2,complete_original_outputs=2,logical_qubits_including_flag=3,
        mechanism_audits=audits,shots=0,counts=None,confidence_interval=None,mu=0,
        decision='Complete public BV now has a literal two-joint-PPM native control via documented entry point. No scheduler/decoded-error superiority inferred; common lowering/space/budget gate remains open.')
    save(output/'summary.json',summary)
    print(json.dumps(summary,indent=2))


def check(output,repo):
    load_author(repo)
    env = frozen(repo); old = json.loads((output/'freeze.json').read_text())
    for key in ['packages','author_source_sha256','partial_code_sha256','family_split_sha256']:
        if env[key]!=old[key]: raise ValueError('Frozen content differs: '+key)
    rows = [json.loads(p.read_text()) for p in output.glob('*_b??_m?.json')]
    assert len(rows)==32
    for r in rows:
        specs=r['literal_output_specs']
        for name in ['native_ideal','ideal','noisy','dem']:
            h=r[name+'_sha256']; ext='.dem' if name=='dem' else '.stim'
            data=(output/'artifacts'/(h+ext)).read_bytes(); assert sha(data)==h
        ideal=stim.Circuit((output/'artifacts'/(r['ideal_sha256']+'.stim')).read_text())
        assert evaluate(ideal.reference_sample(),specs)==r['expected_original_outputs']
        noisy=stim.Circuit((output/'artifacts'/(r['noisy_sha256']+'.stim')).read_text())
        assert str(noisy.detector_error_model(decompose_errors=True))==(output/'artifacts'/(r['dem_sha256']+'.dem')).read_text()
    events=[json.loads(s) for s in (output/'journal.jsonl').read_text().splitlines()]
    assert Counter(e['event'] for e in events)=={'compile_started':32,'compile_finished':32}
    save(output/'verification.json',dict(status='PASS',records=32,compile_started=32,
        compile_finished=32,new_shots=0,scope='Frozen source/author pins, full literal records, exact DEM replay and compile journal; no recompile.'))
    print('PASS:32 complete native partial-output records;0new shots;0recompiles')


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--output',type=Path,default=DEFAULT)
    p.add_argument('--author-repo',type=Path,default=ROOT.parent/'external/CircLS')
    p.add_argument('--check',action='store_true');a=p.parse_args()
    (check if a.check else run)(a.output,a.author_repo)
