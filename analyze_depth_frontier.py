"""Outcome-free geometry/request ledger and isolated complete-pool selector timing."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time
import zipfile

import stim

from common_physical_pool import POLICIES, select
from public_candidate_pool import canonical
from run_grover_depth_frontier import DEFAULT, PROTOCOL, ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def analyze(result):
    # summary exists only after every physical job and the whole-pool selection.
    summary = load(result / 'summary.json')
    rows = load(result / 'candidate_pool.json')
    frontier = load(result / 'selected_frontier.json')
    certs = [load(result / 'certificates' / (r['candidate_id'] + '.json')) for r in frontier]
    if len(certs) != 52 or len(rows) != 77 or summary['new_physical_compilations'] != 260:
        raise ValueError('Complete fixed-protocol frontier required')
    reference = next(r for r in rows if r['candidate_id'] == 'fixed:g174')
    axes = ['template_block_z', 'total_lifetime_block_z', 'plain_data_storage_cubes', 'static_site_ticks']
    def dominated(row):
        a, b = row['features'], reference['features']
        return all(b[k] <= a[k] for k in axes) and any(b[k] < a[k] for k in axes)
    ideal_requests = [r['ideal_sha256'] for r in certs]
    ideal_requests += [g['ideal_sha256'] for r in certs for g in r['generators']]
    new_rows = [r['common_row'] for r in certs]
    device_path = ROOT / 'results/grover_competition_2026-11-17/resource_certificate.json'
    original_sites = set(map(tuple, load(device_path)['physical_site_catalogue']))
    outside_original = {}
    for r in certs:
        name = r['ideal_sha256'] + '.stim'
        path = result / 'circuits' / name
        if path.exists():
            raw = path.read_bytes()
        else:
            archive_path = Path(load(result / 'snapshot_manifest.json')['archive'])
            if not archive_path.is_absolute():
                archive_path = ROOT / archive_path
            with zipfile.ZipFile(archive_path) as z:
                raw = z.read('circuits/' + name)
        if hashlib.sha256(raw).hexdigest() != r['ideal_sha256']:
            raise ValueError('Physical site audit source changed')
        coordinates = stim.Circuit(raw.decode()).get_final_qubit_coordinates()
        outside_original[r['candidate_id']] = [list(p) for p in sorted(set(map(tuple, coordinates.values())) - original_sites)]
    fields = axes + ['data_lifetime_block_z', 'ancilla_lifetime_block_z', 'stim_ticks', 'active_physical_sites']
    paths = [result / p for p in ['protocol.json', 'summary.json', 'candidate_pool.json', 'selected_frontier.json', 'physical_index.json']]
    paths += [result / 'certificates' / (r['candidate_id'] + '.json') for r in frontier]
    return dict(
        input_sha256={str(p.relative_to(result)): sha(p) for p in paths},
        analysis_code_sha256=sha(Path(__file__)),
        new_main_candidates=len(certs), unique_new_noisy_circuits=len({r['noisy_sha256'] for r in certs}),
        actual_physical_compile_calls=len(ideal_requests),
        unique_compiled_ideal_hashes=len(set(ideal_requests)),
        repeated_ideal_compilations=len(ideal_requests) - len(set(ideal_requests)),
        repeated_compile_note='Actual calls remain260. Equal hashes are reusable physical representations, not extra independent circuits. No cache saving was executed in this batch.',
        new_feature_ranges={k: dict(min=min(r['features'][k] for r in new_rows), max=max(r['features'][k] for r in new_rows)) for k in fields},
        new_protected_idle_totals=sorted({r['features']['total_protected_idle_block_z'] for r in certs}),
        new_distinct_protected_idle_profiles=len({canonical(r['features']['protected_idle_intervals_block_z']) for r in certs}),
        original_310_device_certificate_sha256=sha(device_path),
        new_required_coordinates_outside_original_310=outside_original,
        geometric_dominance_axes=axes, geometric_dominance_reference='fixed:g174',
        geometrically_dominated_new_candidates=sum(dominated(r) for r in new_rows),
        interpretation='Geometric dominance is not decoded-error dominance; all52 new candidates and all25 prior candidates retained. No risk proxy, outcome-based pruning, new calibration or noisy labels.',
        shots=0, counts=None, confidence_interval=None, mu=0)


def run(result):
    files = [result / 'analysis.json', result / 'selector_timing_isolated.json']
    if any(p.exists() for p in files):
        raise FileExistsError('Do not overwrite frozen analysis/timing')
    analysis = analyze(result)
    rows = load(result / 'candidate_pool.json')
    policies = list(POLICIES)
    for _ in range(3):
        for p in policies:
            select(rows, p, PROTOCOL['reference'], 77)
    samples = {p: [] for p in policies}
    for i in range(31):
        for p in policies[i % len(policies):] + policies[:i % len(policies)]:
            began = time.perf_counter()
            select(rows, p, PROTOCOL['reference'], 77)
            samples[p].append(time.perf_counter() - began)
    timing = dict(code_sha256=sha(Path(__file__)), pool_sha256=sha(result / 'candidate_pool.json'),
        row_budget_per_method=77, warmups=3, repetitions=31, samples_seconds=samples,
        median_seconds={p: statistics.median(v) for p, v in samples.items()},
        scope='Cached table + pool digest + ranking only, after physical batch and before full test suite. Not routing/scorer/compile or online equal-CPU benchmark.',
        routing_seconds=None, scorer_seconds=None, calibration_seconds=None,
        physical_compile_seconds=None, monte_carlo_seconds=None, decode_seconds=None)
    for p, value in zip(files, [analysis, timing]):
        p.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(analysis, indent=2))


def check(result):
    if analyze(result) != load(result / 'analysis.json'):
        raise AssertionError('Geometry/request ledger replay changed')
    timing = load(result / 'selector_timing_isolated.json')
    if timing['code_sha256'] != sha(Path(__file__)) or timing['pool_sha256'] != sha(result / 'candidate_pool.json'):
        raise AssertionError('Timed code/pool changed')
    if set(timing['samples_seconds']) != set(POLICIES) or timing['row_budget_per_method'] != 77:
        raise AssertionError('Timed methods/budget changed')
    for p, samples in timing['samples_seconds'].items():
        if len(samples) != 31 or min(samples) <= 0 or statistics.median(samples) != timing['median_seconds'][p]:
            raise AssertionError('Recorded timing summary changed')
    print('PASS: geometry/request ledger and isolated selector timing integrity; 0 new shots')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--result', type=Path, default=DEFAULT)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    (check if args.check else run)(args.result)
