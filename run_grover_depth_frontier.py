"""Qualify the ENTIRE next gate-depth frontier, without noisy labels.

Retains the original 175 plans and 25 physical candidates. This is physical
coverage expansion, not a risk revision, online budget comparison or pilot.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import time
import zipfile

import stim

from common_physical_pool import POLICIES, physical_memory_features, remap, select
from exact_program_validation import check_exact
from public_candidate_pool import digest, features
from public_clifford import graph_program
from public_gate_pool import enumerate_gate_plans
from run_common_physical_pool import READOUT, proof_metadata
from run_grover_competition import compile_one, source_program

ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / 'results/grover_depth_frontier_2026-11-26'
ARCHIVE = ROOT / 'archives/grover_depth_frontier_2026-11-26.zip'
PRIOR = ROOT / 'results/common_physical_pool_2026-11-25'
LOGICAL_POOL = ROOT / 'results/grover_competition_2026-11-17/candidate_pool.json'
CODE = ['run_grover_depth_frontier.py', 'run_grover_competition.py',
        'run_common_physical_pool.py', 'common_physical_pool.py',
        'exact_program_validation.py', 'public_clifford.py', 'public_gate_pool.py',
        'public_candidate_pool.py', 'projection_geometry_metrics.py',
        'schedule_circuit.py', 'surgery.py', 'run_public_audit.py',
        'requirements-lock.txt', 'benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json']
PROTOCOL = dict(
    id='complete_next_depth_frontier_20261126_v1', date='2026-11-26',
    source_family='QASMBench grover_search development only',
    selection='Every previously uncompiled plan at minimum physical layers + 1; no outcome-dependent subset.',
    expected_full_logical_pool=175, expected_frontier_plans=52,
    retained_prior_physical_candidates=25, expected_expanded_physical_pool=77,
    source_gates='All 18 source instructions, measurements and classical mapping; no cancellation.',
    device='Unchanged Nov25 378-coordinate experimental catalogue; fail on any outside site. Not a measured chip cap.',
    cx_concurrency_cap=None, retained_deeper_plans=True,
    complete_readout=READOUT, noise='d3 p0.001 TQEC uniform depolarizing',
    decoder='ordinary uncorrelated PyMatching MWPM/decomposed DEM; construction only',
    validation='Main rank2 + all signed inputs/final faults; four independent generator compilations per plan; graphlike distance3; identical complete DEM under coordinate remap.',
    selectors=list(POLICIES), reference='fixed:g174', row_budget_per_selector=77,
    shots=0, seeds=[], counts=None, confidence_interval=None,
    stopping_rule='No sampling. Any missing/failed candidate aborts whole frontier and all selections; never silently filter.',
    risk_revision=False, raw_v1='STOPPED', calibration=False,
    held_out_labels='sealed', sampling_permission=False, mu=0,
    timing='Pool generation, graph/features, main compile, generator compile, exact checks, DEM/decoder construction, normalization, selector separated. Concurrent compile times are throughput records, not independent performance claims. Routing/scorer benchmark/calibration/MC/decode absent.',
    method_boundary='No O3LS/SPARO implementation or online equal-CPU claim. Existing original-method support gaps retained.')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')


def next_frontier(pool, qualified_ids):
    """Select the complete first deeper layer; never choose by error labels."""
    ids = [r['candidate_id'] for r in pool]
    if not pool or len(set(ids)) != len(ids):
        raise ValueError('Nonempty unique logical pool required')
    qualified_ids = set(qualified_ids)
    if not qualified_ids <= set(ids):
        raise ValueError('Unknown qualified plan')
    minimum = min(r['features']['physical_layers'] for r in pool)
    minima = {r['candidate_id'] for r in pool if r['features']['physical_layers'] == minimum}
    if not minima <= qualified_ids:
        raise ValueError('Qualify every minimum plan first')
    selected = [r for r in pool if r['features']['physical_layers'] == minimum + 1]
    if not selected or any(r['candidate_id'] in qualified_ids for r in selected):
        raise ValueError('Fresh complete next frontier required; do not silently remove old rows')
    return selected


def compile_frontier_one(program, row, output, sites):
    # Authoritative existing complete-source compiler and exact generator checker.
    result = compile_one(program, row, output)
    meta = result['backend_meta']
    if meta['external_flows'] != READOUT:
        raise AssertionError('Ordered complete observable basis changed')
    began = time.perf_counter()
    graph, _, gm = graph_program(program, row['plan'])
    measured = physical_memory_features(graph, gm)
    geometry_seconds = time.perf_counter() - began
    normalized = {}
    proofs = []
    remap_seconds = dem_seconds = exact_seconds = 0.0
    for kind in ('ideal', 'noisy'):
        raw = (output / 'circuits' / (result[kind + '_sha256'] + '.stim')).read_bytes()
        old = stim.Circuit(raw.decode())
        began = time.perf_counter()
        new, _ = remap(old, sites)
        remap_seconds += time.perf_counter() - began
        data = str(new).encode()
        h = sha(data)
        (output / 'circuits' / (h + '.stim')).write_bytes(data)
        normalized[kind + '_sha256'] = h
        began = time.perf_counter()
        dem = str(new.detector_error_model(decompose_errors=True)).encode()
        expected = str(old.detector_error_model(decompose_errors=True)).encode()
        if dem != expected:
            raise AssertionError('Complete DEM changed under coordinate remap')
        dem_seconds += time.perf_counter() - began
        if kind == 'noisy':
            normalized['dem_sha256'] = sha(dem)
            if sha(dem) != result['dem_sha256']:
                raise AssertionError('Frozen full DEM differs')
        else:
            began = time.perf_counter()
            validation = check_exact(new, proof_metadata(meta), program, True)
            exact_seconds += time.perf_counter() - began
            proofs.append(dict(kind='complete_main', ideal_sha256=h,
                               metadata=proof_metadata(meta), validation=validation))
    for gen in result['generators']:
        old = stim.Circuit((output / 'circuits' / (gen['ideal_sha256'] + '.stim')).read_text())
        began = time.perf_counter()
        new, _ = remap(old, sites)
        remap_seconds += time.perf_counter() - began
        began = time.perf_counter()
        m = proof_metadata(meta, gen)
        validation = check_exact(new, m, program)
        exact_seconds += time.perf_counter() - began
        data = str(new).encode()
        h = sha(data)
        (output / 'circuits' / (h + '.stim')).write_bytes(data)
        proofs.append(dict(kind=gen['input_generator'], ideal_sha256=h,
                           metadata=m, validation=validation))
    measured.update(stim_ticks=result['features']['stim_ticks'], qec_rounds=None,
                    static_site_ticks=len(sites) * result['features']['stim_ticks'],
                    active_physical_sites=result['num_qubits'], device_physical_sites=len(sites))
    common_row = dict(
        candidate_id='fixed:' + row['candidate_id'], lowering_id=meta['profile_id'],
        device_sha256=digest(sites), outside_device_sites=0,
        qualified_complete_output=True, external_flows=READOUT, features=measured,
        profile_specific_protected_idle_block_z=row['features']['total_protected_idle_block_z'],
        profile_routing_steps=row['features']['cx_routing_steps'],
        profile_h_layers=row['features']['logical_h_layers'],
        profile_physical_layers=row['features']['physical_layers'],
        source_sha256=program['source_sha256'], plan_sha256=row['plan_sha256'],
        original_artifacts={k: result[k] for k in ['ideal_sha256', 'noisy_sha256', 'dem_sha256']},
        normalized_artifacts=normalized, full_original_readout_order=[1, 0],
        graphlike_distance=3, shots=0, counts=None, confidence_interval=None)
    result.update(common_row=common_row, normalized_proofs=proofs,
                  normalization_timing=dict(graph_features_seconds=geometry_seconds,
                      coordinate_remap_seconds=remap_seconds, dem_equivalence_seconds=dem_seconds,
                      normalized_exact_seconds=exact_seconds))
    save(output / 'certificates' / (row['candidate_id'] + '.json'), result)
    return result


def finalize_pool(prior, results, frontier):
    expected = {r['candidate_id'] for r in frontier}
    got = [r['candidate_id'] for r in results]
    if len(got) != len(expected) or set(got) != expected:
        raise ValueError('Incomplete/duplicate frontier: cannot filter failures and select')
    rows = prior + [r['common_row'] for r in sorted(results, key=lambda r: r['candidate_id'])]
    selections = [select(rows, p, PROTOCOL['reference'], len(rows)) for p in POLICIES]
    return rows, selections


def run(output, workers):
    if output.exists():
        raise FileExistsError('Fresh result directory required')
    if platform.python_version_tuple()[:2] != ('3', '12'):
        raise ValueError('Python3.12 required')
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError('1..8 physical workers required')
    _, program = source_program()
    began = time.perf_counter()
    pool = load(LOGICAL_POOL)
    if [r['plan'] for r in pool] != enumerate_gate_plans(program):
        raise ValueError('Frozen complete logical pool differs')
    if any(r['plan_sha256'] != digest(r['plan']) or r['features'] != features(program, r['plan']) for r in pool):
        raise ValueError('Original plan/features differ')
    prior = load(PRIOR / 'candidate_pool.json')
    frontier = next_frontier(pool, [r['candidate_id'].split(':')[1] for r in prior if r['candidate_id'].startswith('fixed:')])
    if len(pool) != 175 or len(prior) != 25 or len(frontier) != 52:
        raise ValueError('Protocol pool cardinality changed')
    pool_seconds = time.perf_counter() - began
    sites = load(PRIOR / 'device.json')['physical_site_catalogue']
    output.mkdir(parents=True)
    (output / 'circuits').mkdir()
    (output / 'certificates').mkdir()
    save(output / 'protocol.json', PROTOCOL)
    save(output / 'selected_frontier.json', frontier)
    inputs = [LOGICAL_POOL, PRIOR / 'candidate_pool.json', PRIOR / 'device.json',
              ROOT / 'benchmarks/public_2026-11-17/manifest.json']
    save(output / 'environment.json', dict(python=platform.python_version(),
        base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        source_files_sha256={p: sha((ROOT / p).read_bytes()) for p in CODE},
        input_files_sha256={str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in inputs},
        packages={p: md.version(p) for p in ['stim', 'tqec', 'pymatching', 'numpy', 'qiskit']},
        tqec_direct_url=json.loads(md.distribution('tqec').read_text('direct_url.json'))))
    results = []
    began = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        jobs = [ex.submit(compile_frontier_one, program, row, output, sites) for row in frontier]
        for job in as_completed(jobs):
            r = job.result()  # Never suppress a failed physical compilation.
            results.append(r)
            print(r['candidate_id'], 'main+4 generators, rank2, d3, same device/DEM PASS',
                  f'{len(results)}/{len(frontier)}; 0 shots', flush=True)
    physical_wall_seconds = time.perf_counter() - began
    began = time.perf_counter()
    rows, selections = finalize_pool(prior, results, frontier)
    selector_seconds = time.perf_counter() - began
    save(output / 'candidate_pool.json', rows)
    save(output / 'selections.json', selections)
    save(output / 'physical_index.json', [{k: r[k] for k in ['candidate_id', 'source_sha256',
        'plan_sha256', 'ideal_sha256', 'noisy_sha256', 'dem_sha256', 'features', 'timing',
        'normalization_timing']} for r in sorted(results, key=lambda r: r['candidate_id'])])
    summary = dict(protocol_id=PROTOCOL['id'], retained_logical_plans=175,
        newly_qualified_fixed_plans=52, total_qualified_fixed_plans=64,
        remaining_fixed_plans=111, full_physical_portfolio=len(rows),
        common_device_sites=len(sites), main_physical_compilations=52,
        generator_physical_compilations=208, exploratory_physical_compilations=0,
        new_physical_compilations=260,
        unique_new_noisy_circuits=len({r['noisy_sha256'] for r in results}),
        unique_total_normalized_noisy_circuits=len({r['normalized_artifacts']['noisy_sha256'] for r in rows}),
        full_main_exact_checks=52, generator_exact_checks=208,
        main_dem_equivalence_checks=104, new_research_shots=0, sampler_calls=0,
        counts=None, confidence_interval=None, mu=0, held_out_labels='sealed',
        sampling_permission=False, raw_v1='STOPPED', risk_revision=False,
        decision='Complete next depth frontier added, without noise-label pruning. This is not all175 physical plans or an online original-method budget comparison; no decoded efficacy conclusion.')
    save(output / 'summary.json', summary)
    save(output / 'timing.json', dict(pool_generation_verification_seconds=pool_seconds,
        physical_batch_wall_seconds=physical_wall_seconds, physical_workers=workers,
        final_pool_and_four_selections_seconds=selector_seconds,
        routing_benchmark_seconds=None, scorer_benchmark_seconds=None,
        calibration_seconds=None, monte_carlo_seconds=None, decode_seconds=None,
        note='Per-candidate main/generator compile and exact/noise/DEM stages in physical_index; concurrent throughput, not isolated compiler/routing benchmark.'))
    return summary


def check(output, archive):
    _, program = source_program()
    env = load(output / 'environment.json')
    for group in ('source_files_sha256', 'input_files_sha256'):
        for p, h in env[group].items():
            if sha((ROOT / p).read_bytes()) != h:
                raise AssertionError('Frozen source/input differs: ' + p)
    if load(output / 'protocol.json') != PROTOCOL:
        raise AssertionError('Protocol changed')
    prior = load(PRIOR / 'candidate_pool.json')
    frontier = next_frontier(load(LOGICAL_POOL),
        [r['candidate_id'].split(':')[1] for r in prior if r['candidate_id'].startswith('fixed:')])
    if frontier != load(output / 'selected_frontier.json'):
        raise AssertionError('A frontier candidate was omitted')
    results = [load(output / 'certificates' / (r['candidate_id'] + '.json')) for r in frontier]
    rows, selections = finalize_pool(prior, results, frontier)
    if rows != load(output / 'candidate_pool.json') or selections != load(output / 'selections.json'):
        raise AssertionError('Whole-pool selector replay differs')
    sites = load(PRIOR / 'device.json')['physical_site_catalogue']
    with zipfile.ZipFile(archive) as z:
        def read(h, suffix):
            data = z.read('circuits/' + h + suffix)
            if sha(data) != h:
                raise AssertionError('Artifact hash mismatch')
            return data.decode()
        for row, result in zip(frontier, results):
            common = result['common_row']
            g, _, m = graph_program(program, row['plan'])
            if any(common['features'][k] != v for k, v in physical_memory_features(g, m).items()):
                raise AssertionError('Geometry feature changed')
            for kind in ('ideal', 'noisy'):
                old = stim.Circuit(read(result[kind + '_sha256'], '.stim'))
                normalized = read(common['normalized_artifacts'][kind + '_sha256'], '.stim')
                expected, _ = remap(old, sites)
                if str(expected) != normalized:
                    raise AssertionError('Gate/noise/measurement changed')
                if str(old.detector_error_model(decompose_errors=True)) != str(expected.detector_error_model(decompose_errors=True)):
                    raise AssertionError('DEM changed')
                if kind == 'noisy':
                    if str(expected.detector_error_model(decompose_errors=True)) != read(result['dem_sha256'], '.dem'):
                        raise AssertionError('Full stored DEM changed')
                    if len(expected.shortest_graphlike_error()) != 3:
                        raise AssertionError('Distance changed')
            for proof in result['normalized_proofs']:
                circuit = stim.Circuit(read(proof['ideal_sha256'], '.stim'))
                actual = check_exact(circuit, proof['metadata'], program, proof['kind'] == 'complete_main')
                if actual != proof['validation']:
                    raise AssertionError('Exact proof changed')
            print(row['candidate_id'], 'full physical replay PASS; 0 shots', flush=True)
    print('PASS: all52 complete frontier candidates, 208 generators, 104 unchanged DEMs, all77 retained; 0 new shots', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=DEFAULT)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--archive', type=Path, default=ARCHIVE)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    if args.check:
        check(args.output, args.archive)
    else:
        print(json.dumps(run(args.output, args.workers), indent=2))
