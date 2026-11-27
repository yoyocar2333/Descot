"""Qualify every minimum of a complete pinned public BV source, zero shots.

The common device is the outcome-free union of all nine physical catalogues,
with no hardware cap or excluded parallel candidate. It is an experimental
resource envelope, not a measured chip or original-method equal-CPU result.
"""
import argparse
import ast
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata as md
import json
import os
from pathlib import Path
import platform
import subprocess
import time

import pymatching
import stim
from qiskit import qasm2
from qiskit.circuit import QuantumCircuit

from public_partial_readout import load_partial_program, original_output_view, check_original_outputs
from public_minimum_pool import minimum_gate_plans
from public_candidate_pool import digest, features
from public_clifford import generate_program, graph_program, schedule_program
from exact_compile_cache import ExactCompileCache
from exact_program_validation import check_exact
from common_physical_pool import catalogue, remap, physical_memory_features, select, POLICIES
from surgery import add_noise, TQEC_COMMIT

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'benchmarks/public_2026-11-27/mqt'
DEFAULT = ROOT/'results/public_bv_2026-11-27'
CODE = ['run_bv_public_family.py', 'public_partial_readout.py', 'public_minimum_pool.py',
        'public_clifford.py', 'public_candidate_pool.py', 'common_physical_pool.py',
        'projection_geometry_metrics.py', 'exact_compile_cache.py', 'exact_program_validation.py',
        'run_public_audit.py', 'schedule_circuit.py', 'surgery.py', 'requirements-lock.txt',
        'tests/test_public_partial_readout.py']
PROTOCOL = dict(id='complete_public_bv_static_n3_hidden11_v1',
    source_revision='8f919416457d76b256930443078334021634236f',
    family='MQT Bench Bernstein-Vazirani; development, distinct from Bell/Grover/hidden_shift',
    parameters=dict(num_qubits=3, dynamic=False, hidden_string='11'),
    source_policy='Execute unchanged upstream create_circuit body; registration decorator omitted only. Export QASM with pinned Qiskit. All9 source instructions retained in13 lowered instructions; no cancellation.',
    pool_policy='All9 minima of exact homogeneous H/CX ready-subset search; no H-first or concurrency cap. All66 plans counted,57 deeper plans retained unqualified. Mixed H/CX layers remain outside this profile.',
    device_policy='Union of all9 compiler coordinate catalogues, then injective coordinate relabeling. No outcome-based exclusion. Common experimental envelope, not hardware-derived cap.',
    full_output='Both original classical bits c0=Z(q1),c1=Z(q2), rank2. Internal q0 cleanup excluded only from observable annotations; its full lifetime/gates/detectors/readout remain.',
    validation='Full original/lowered tableau; all3 logical qubits and6 X/Z generators; all8 signed inputs; each3 final logical faults with predicted original-output response; ideal/noisy DEM remap equality; graphlike distance3.',
    noise='TQEC add_noise uniform depolarizing p=0.001, distance3,k1',
    decoder='ordinary uncorrelated PyMatching MWPM from decomposed DEM; construction only',
    physical_compile_request_ceiling=63, candidate_count=9, requests_per_candidate=7,
    compile_cache='Per-candidate identical full program/plan/bases/compiler requests only; no validation target skipped. Each actual call durably journaled before start.',
    selectors=list(POLICIES), selector_budget_rows=9,
    shots=0, seeds=[], sampler_calls=0, counts=None, confidence_interval=None,
    sampling_permission=False, held_out_labels='sealed', mu=0,
    stopping_rule='Stop on source, DAG, readout, generator, sign, footprint, DEM, distance or budget mismatch; no replacement chosen using noisy outcomes.',
    units='One physical H/CX layer=3 template block-z in this adapter only; routing steps,H layers,block-z,TICK separate; QEC rounds=null.',
    scope='Complete public-family physical integration and offline common-pool resource controls. Not original O3LS/SPARO/CircLS/Hamada equal-CPU comparison, calibrated risk model, held-out evaluation or decoded improvement.')


def sha(data): return hashlib.sha256(data).hexdigest()
def save(path, value): path.write_text(json.dumps(value, indent=2)+'\n')
def read(path): return json.loads(path.read_text())


def generate_source():
    """Reproduce the exact source-generated QASM, fail on upstream drift."""
    path = SOURCE/'bv.py'; raw = path.read_bytes()
    blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if blob != 'e813914a5a7ea7304381bceb06a377c0cdabcdec':
        raise ValueError('Pinned upstream BV blob differs')
    f = next(x for x in ast.parse(raw).body if isinstance(x, ast.FunctionDef))
    f.decorator_list = []
    ns = {'QuantumCircuit': QuantumCircuit}
    exec(compile(ast.Module(body=[f], type_ignores=[]), str(path), 'exec'), ns)
    qasm = qasm2.dumps(ns['create_circuit'](**PROTOCOL['parameters']))+'\n'
    if (SOURCE/'bv_n3_11.qasm').read_text() != qasm:
        raise ValueError('Full source-generated QASM differs')
    return load_partial_program(SOURCE/'bv_n3_11.qasm')


class Journal:
    def __init__(self, path): self.path = path
    def event(self, value):
        with self.path.open('a') as f:
            f.write(json.dumps(value)+'\n'); f.flush(); os.fsync(f.fileno())
    def __call__(self, program, plan, a, b):
        key = digest(dict(program=program, plan=plan, input_bases=a, output_bases=b))
        self.event(dict(event='compile_started', key=key, input_bases=a, output_bases=b))
        t = time.perf_counter()
        try: circuit, meta = generate_program(program, plan, a, b)
        except BaseException as e:
            self.event(dict(event='compile_failed', key=key, error=repr(e), seconds=time.perf_counter()-t))
            raise
        self.event(dict(event='compile_finished', key=key, seconds=time.perf_counter()-t, ideal_sha256=sha(str(circuit).encode())))
        return circuit, meta


def artifact(output, obj, extension):
    raw = str(obj).encode(); h = sha(raw); path = output/'circuits'/(h+extension)
    if path.exists() and path.read_bytes() != raw: raise AssertionError('Artifact hash collision')
    path.write_bytes(raw); return h


def qualify(program, row, output):
    cache = ExactCompileCache(Journal(output/'journals'/(row['candidate_id']+'.jsonl')))
    internal, internal_meta = cache.generate(program, row['plan'])
    t = time.perf_counter()
    full_validation = check_exact(internal, internal_meta, program, True)
    view, meta = original_output_view(internal, internal_meta, program)
    output_validation = check_original_outputs(view, meta, program)
    main_validation_seconds = time.perf_counter()-t
    generators = cache.generators(program, row['plan'], output/'circuits')
    if len(generators) != 6 or len(cache.requests) != 7:
        raise AssertionError('Full3-qubit generator/compile budget differs')
    ih = artifact(output, internal, '.stim'); vh = artifact(output, view, '.stim')
    t = time.perf_counter(); g, _, gm = graph_program(program, row['plan'])
    resource = physical_memory_features(g, gm); geometry_seconds = time.perf_counter()-t
    record = dict(candidate_id=row['candidate_id'], source_sha256=program['source_sha256'],
        plan_sha256=row['plan_sha256'], internal_ideal_sha256=ih, original_output_ideal_sha256=vh,
        original_output_meta=meta, full_internal_validation=full_validation,
        original_output_validation=output_validation, generators=generators, compile_requests=cache.requests,
        features=resource, profile_features=row['profile_features'], shots=0, counts=None, confidence_interval=None,
        timing=dict(actual_physical_compile_seconds=sum(r['physical_compile_seconds'] or 0 for r in cache.requests),
            compile_request_seconds=sum(r['request_seconds'] for r in cache.requests),
            main_exact_seconds=main_validation_seconds,
            generator_exact_seconds=sum(r['exact_validation_seconds'] for r in generators),
            geometry_seconds=geometry_seconds))
    save(output/'certificates'/(row['candidate_id']+'.json'), record)
    return record


def run(output, workers=2):
    if output.exists(): raise FileExistsError('Fresh output required; frozen results cannot be overwritten')
    if platform.python_version_tuple()[:2] != ('3', '12'): raise ValueError('Python3.12 required')
    for line in (ROOT/'requirements-lock.txt').read_text().splitlines():
        if '==' in line:
            name, version = line.split('==')
            if md.version(name) != version: raise ValueError('Dependency pin differs: '+name)
    url = json.loads(md.distribution('tqec').read_text('direct_url.json'))
    if url['vcs_info']['commit_id'] != TQEC_COMMIT: raise ValueError('TQEC commit differs')
    program = generate_source(); t = time.perf_counter(); answer = minimum_gate_plans(program)
    dp_seconds = time.perf_counter()-t
    if (answer['minimum_plan_count'], answer['minimum_physical_layers'], answer['all_legal_plan_count']) != (9, 8, 66):
        raise AssertionError('Outcome-free preflight pool differs')
    rows = [dict(candidate_id=f'b{i:02}', plan=p, plan_sha256=digest(p), profile_features=features(program, p)) for i,p in enumerate(answer['plans'])]
    baseline = schedule_program(program)
    ref = next(r['candidate_id'] for r in rows if r['plan']['layers'] == baseline['layers'])
    output.mkdir(parents=True)
    for name in ('circuits', 'certificates', 'journals'): (output/name).mkdir()
    save(output/'protocol.json', PROTOCOL); save(output/'program.json', program)
    save(output/'candidate_pool.json', rows); save(output/'dp_summary.json', {k:v for k,v in answer.items() if k!='plans'})
    save(output/'environment.json', dict(python=platform.python_version(),
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        code_sha256={p:sha((ROOT/p).read_bytes()) for p in CODE},
        source_sha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in SOURCE.iterdir() if p.is_file()},
        packages={p:md.version(p) for p in ('stim','tqec','pymatching','numpy','qiskit')}, tqec_direct_url=url))
    # The protocol and complete source/pool/code/model hashes exist before the first compile.
    save(output/'freeze.json', {name:sha((output/name).read_bytes()) for name in
        ('protocol.json','program.json','candidate_pool.json','dp_summary.json','environment.json')})
    t = time.perf_counter(); records = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for job in as_completed([ex.submit(qualify, program, row, output) for row in rows]):
            r = job.result(); records.append(r)
            save(output/'completed_ids.json', sorted(r['candidate_id'] for r in records))
            print(r['candidate_id'], len(records), 'of9 full source/original2 outputs + flag/generators verified;0shots', flush=True)
    compile_batch_wall_seconds = time.perf_counter()-t
    records.sort(key=lambda r:r['candidate_id'])
    native = [stim.Circuit((output/'circuits'/(r['original_output_ideal_sha256']+'.stim')).read_text()) for r in records]
    sites = catalogue(native); device_hash = digest(sites)
    save(output/'device.json', dict(sites=sites, sha256=device_hash, physical_sites=len(sites), hardware_cap=False,
        policy=PROTOCOL['device_policy'], all_candidates_retained=True))
    for r, circuit in zip(records, native, strict=True):
        t = time.perf_counter(); view, mapping = remap(circuit, sites)
        noise = add_noise(circuit, .001); noisy = add_noise(view, .001)
        ideal_dem = circuit.detector_error_model(decompose_errors=True)
        dem = noise.detector_error_model(decompose_errors=True)
        if ideal_dem != view.detector_error_model(decompose_errors=True) or dem != noisy.detector_error_model(decompose_errors=True):
            raise AssertionError('Complete ideal/noisy DEM changed after coordinate remap')
        pymatching.Matching.from_detector_error_model(dem)
        noise_decoder_seconds = time.perf_counter()-t
        t = time.perf_counter(); distance = len(noisy.shortest_graphlike_error()); distance_seconds=time.perf_counter()-t
        if distance != 3: raise AssertionError('Original full-output graphlike distance differs')
        t = time.perf_counter(); validation = check_original_outputs(view, r['original_output_meta'], program)
        remap_validation_seconds = time.perf_counter()-t
        r.update(ideal_sha256=artifact(output, view, '.stim'), noisy_sha256=artifact(output, noisy, '.stim'),
            dem_sha256=artifact(output, dem, '.dem'), original_output_noisy_sha256=artifact(output, noise, '.stim'),
            original_output_dem_sha256=artifact(output, dem, '.dem'), ideal_dem_sha256=artifact(output, ideal_dem, '.dem'),
            device_sha256=device_hash, outside_device_sites=0, external_flows=r['original_output_meta']['external_flows'],
            qualified_complete_output=True, active_physical_sites=circuit.num_qubits,
            graphlike_distance=distance, remap_full_dem_equal=True, qubit_mapping=mapping,
            remap_original_output_validation=validation)
        r['features'].update(static_site_ticks=len(sites)*view.num_ticks, stim_ticks=view.num_ticks,
            active_physical_sites=circuit.num_qubits, device_physical_sites=len(sites), qec_rounds=None)
        r['timing'].update(noise_dem_decoder_construction_seconds=noise_decoder_seconds,
            distance_search_seconds=distance_seconds, remap_exact_seconds=remap_validation_seconds)
        save(output/'certificates'/(r['candidate_id']+'.json'), r)
    index = [{k:v for k,v in r.items() if k not in ('original_output_meta','full_internal_validation',
        'original_output_validation','remap_original_output_validation','generators')} for r in records]
    save(output/'physical_index.json', index)
    selections = [select(index, policy, ref, 9) for policy in POLICIES]; save(output/'selections.json', selections)
    # Independent selector-only repeats; compilation, DP/search and decoding excluded.
    measured = []
    for _ in range(31):
        trial = {}
        for policy in POLICIES:
            t = time.perf_counter(); select(index, policy, ref, 9); trial[policy]=time.perf_counter()-t
        measured.append(trial)
    requests = [v for r in records for v in r['compile_requests']]
    summary = dict(reference_id=ref, original_instructions=9, lowered_instructions=13,
        original_outputs=2, live_logical_qubits=3, qualified_minima=9,
        all_legal_plans=66, retained_unqualified_deeper_plans=57,
        unique_common_noisy_circuits=len({r['noisy_sha256'] for r in records}),
        unique_wait_profiles=len({digest(r['profile_features']['protected_idle_intervals_block_z']) for r in records}),
        physical_compile_requests=len(requests), actual_physical_compilations=sum(not r['cache_hit'] for r in requests),
        exact_cache_hits=sum(r['cache_hit'] for r in requests), physical_sites=len(sites),
        role='New complete Bernstein-Vazirani development family; existing held-out source family remains sealed.',
        new_shots=0, sampler_calls=0, counts=None, confidence_interval=None, mu=0,
        risk_revision='None; raw equal-Pauli v1 remains stopped. No calibrated/decoder performance signal measured.')
    if summary['physical_compile_requests'] != 63: raise AssertionError('Budget changed')
    save(output/'summary.json', summary)
    save(output/'timing.json', dict(dp_candidate_construction_seconds=dp_seconds,
        physical_batch_wall_seconds=compile_batch_wall_seconds, workers=workers,
        actual_compile_sum_seconds=sum(r['timing']['actual_physical_compile_seconds'] for r in records),
        selector_only_seconds_31_repeats=measured,
        online_routing_seconds=None, calibration_seconds=None, monte_carlo_seconds=None, decode_seconds=None,
        note='DP construction and independent scorer/selector measurements are separate. Parallel batch wall time is throughput, not equal-CPU native-method speedup.'))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(__doc__); parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--workers', type=int, default=2); args=parser.parse_args()
    if args.workers < 1: parser.error('Positive workers required')
    run(args.output, args.workers)
