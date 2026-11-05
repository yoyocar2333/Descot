"""Prospective marginal-parity transfer and a bounded Bell(4) front decision."""
import argparse
import ast
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pymatching
from qiskit import QuantumCircuit, QuantumRegister, qasm2
import stim

from bell_benchmark import SOURCE_DIR, UPSTREAM_BLOB, readout_validation
from memory_calibration_previous import wilson_interval
from public_candidate_pool import enumerate_plans, features
from public_clifford import (cnot_paths, generate_program, load_program, positions_for,
                            validate_clifford_generators, validate_physical)
from run_bell_benchmark import sha, objsha
from run_surgery import DECODER, MODEL, save
from surgery import add_noise

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results/transfer_2026-11-05'
BELL4 = ROOT / 'benchmarks/public_2026-11-05/bell_n4.qasm'
CAT = ROOT / 'benchmarks/public_2026-11-02/qasmbench/cat_state_n4.qasm'
DEV = ROOT / 'results/public_bell_2026-11-04'
FIELDS = ('layers', 'bridge_blocks', 'pre_idle', 'post_idle')
SHOTS = 100_000
BATCH = 5_000


def bell4_qasm():
    source = (SOURCE_DIR / 'bell.py').read_bytes()
    if hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest() != UPSTREAM_BLOB:
        raise ValueError('Pinned MQT generator differs')
    function = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'create_circuit')
    function.decorator_list = []
    namespace = {'QuantumCircuit': QuantumCircuit, 'QuantumRegister': QuantumRegister}
    exec(compile(ast.Module(body=[function], type_ignores=[]), 'bell.py', 'exec'), namespace)
    return qasm2.dumps(namespace['create_circuit'](4)) + '\n'


def parity_mask(flows, n, pair):
    target = sum(1 << q for q in pair)
    vectors = []
    for flow in flows:
        output = flow[n:]
        if len(output) != n or set(output) - set('IZ'):
            raise ValueError('Expected original Z-readout generators')
        vectors.append(sum(1 << q for q, axis in enumerate(output) if axis == 'Z'))
    matches = []
    for selection in range(1, 1 << len(vectors)):
        value = 0
        for i, vector in enumerate(vectors):
            if (selection >> i) & 1:
                value ^= vector
        if value == target:
            matches.append(selection)
    if len(matches) != 1:
        raise ValueError('Expected one unique representation of terminal parity')
    return matches[0]


def local_features(program, plan, pair):
    z = 0
    pre_idle = 0
    post_idle = 0
    bridge = None
    extra_cx = 0
    positions = positions_for(program['logical_qubits'], plan['spacing'])
    for layer in plan['layers']:
        if layer['kind'] == 'virtual_or_readout':
            continue
        ops = [program['operations'][i] for i in layer['operation_ids']]
        footprint = {q for op in ops for q in op['qubits']}
        target = next((op for op in ops if op['name'] == 'cx' and tuple(op['qubits']) == pair), None)
        if target is not None:
            if bridge is not None:
                raise ValueError('Target must have exactly one direct CX')
            bridge = len(cnot_paths(*pair, positions, layer['orientation_before'])[2]) - 2
        else:
            idle = 2 - len(footprint.intersection(pair))
            if bridge is None:
                pre_idle += idle
            else:
                post_idle += idle
        extra_cx += sum(op['name'] == 'cx' and op is not target and bool(set(op['qubits']).intersection(pair)) for op in ops)
        z += 1
    if bridge is None:
        raise ValueError('No target CX')
    return dict(zip(FIELDS, (z, bridge, pre_idle, post_idle))) | {'other_incident_cx': extra_cx}


def fit(rows, fields):
    x = np.array([[r['features'][f] for f in fields] for r in rows], dtype=float)
    y = np.array([np.log((r['errors']+.5)/(r['shots']-r['errors']+.5)) for r in rows])
    groups = np.array([r['sample_id'] for r in rows])

    def train(keep):
        center = x[keep].mean(axis=0)
        scale = x[keep].std(axis=0)
        scale[scale == 0] = 1
        a = np.column_stack([np.ones(len(x)), (x-center)/scale])
        ridge = np.diag([0.] + [1.]*len(fields))
        beta = np.linalg.solve(a[keep].T @ a[keep] + ridge, a[keep].T @ y[keep])
        return center, scale, beta, a @ beta

    center, scale, beta, _ = train(np.ones(len(x), dtype=bool))
    errors = {}
    for group in sorted(set(groups)):
        hold = groups == group
        errors[str(group)] = float(np.max(np.abs(y[hold] - train(~hold)[3][hold])))
    return {'fields': list(fields), 'center': center.tolist(), 'scale': scale.tolist(),
            'beta': beta.tolist(), 'bounds': {f: [float(lo), float(hi)] for f,lo,hi in zip(fields, x.min(0), x.max(0))},
            'group_loo_abs_logit': errors, 'guard': 2*max(errors.values())}


def predict(model, row):
    x = np.array([row['features'][f] for f in model['fields']])
    a = np.r_[1., (x-np.array(model['center']))/np.array(model['scale'])]
    return float(a @ np.array(model['beta']))


def supported(model, row):
    f = row['features']
    return f['other_incident_cx'] == 0 and all(lo <= f[k] <= hi for k,(lo,hi) in model['bounds'].items())


def choose_front(rows, models):
    """Same feasible two-CX-front options and deterministic single-CX rollout."""
    if len(rows) != 2:
        raise ValueError('Profile requires exactly two feasible equal-progress actions')
    baseline = rows[0]
    full = models['full']
    best = min(rows, key=lambda row: predict(full, row))
    guard_ok = all(supported(full, row) for row in rows)
    margin = predict(full, baseline) - predict(full, best)
    selected = {'progress': baseline['id'],
                'depth_only': min(rows, key=lambda row: predict(models['depth_only'], row))['id'],
                'no_geometry': min(rows, key=lambda row: predict(models['no_geometry'], row))['id'],
                'no_wait': min(rows, key=lambda row: predict(models['no_wait'], row))['id'],
                'full': best['id'],
                'guarded': (best if guard_ok and margin > full['guard'] else baseline)['id']}
    return {'selected': selected, 'guard_margin': margin, 'guard_passed_domain': guard_ok,
            'progress_score_now_next': [1,1], 'front_candidates': len(rows), 'rollout_front_evaluations': len(rows),
            'candidate_ids': [r['id'] for r in rows]}


def prepare(out):
    if out.exists():
        raise FileExistsError('Use a fresh destination')
    if BELL4.read_text() != bell4_qasm():
        raise ValueError('Complete Bell(4) source differs from original generator')
    summary = json.loads((DEV/'summary.json').read_text())
    from run_bell_benchmark import program
    from public_clifford import schedule_program

    development = []
    for record in summary['records']:
        name = record['record_id']
        cert_path = DEV/'certificates'/f'{name}.json'
        flows = json.loads(cert_path.read_text())['backend_meta']['external_flows']
        dev_program = program()
        plan = schedule_program(dev_program, record['mode'], record['spacing'])
        for pair in [(0,1),(2,3),(4,5)]:
            mask = parity_mask(flows, 6, pair)
            if mask.bit_count() != 1:
                raise ValueError('Expected a stored marginal, never approximate XOR counts')
            development.append({'sample_id': record['sample_id'], 'pair': pair,
                'features': local_features(dev_program, plan, pair), 'shots': record['shots'],
                'errors': record['failures_by_observable'][mask.bit_length()-1],
                'certificate_sha256': sha(cert_path)})
    models = {'depth_only': fit(development, ('layers',)), 'no_geometry': fit(development, ('layers','pre_idle','post_idle')),
              'no_wait': fit(development, ('layers','bridge_blocks')), 'full': fit(development, FIELDS)}
    candidates = []
    decisions = []
    for spacing in (3,5):
        for name,path in [('bell4',BELL4),('cat4',CAT)]:
            p = load_program(path)
            pool = enumerate_plans(p, spacing)
            if len(pool) != (3 if name == 'bell4' else 1):
                raise ValueError('Unexpected exact pool')
            rows = []
            for plan in pool:
                cx = [l['operation_ids'] for l in plan['layers'] if l['kind'] == 'cx']
                f = local_features(p, plan, (0,1))
                label = "chain" if name == "cat4" else ("parallel" if len(cx) == 1 else ("anchor_first" if p["operations"][cx[0][0]]["qubits"] == [0,1] else "anchor_last"))
                row = {'id': f'{name}_s{spacing}_{label}', 'source': name, 'source_sha256': p['source_sha256'],
                       'features': f, 'spacing': spacing, 'plan': plan}
                row['logit_predictions'] = {k: predict(m, row) for k,m in models.items()}
                row['domain_supported'] = supported(models['full'], row)
                rows.append(row)
            if len({r['id'] for r in rows}) != len(rows):
                raise ValueError('Ambiguous plan labels')
            candidates.extend(rows)
            if name == 'bell4':
                legal = sorted((r for r in rows if len([l for l in r['plan']['layers'] if l['kind']=='cx']) == 2), key=lambda r:r['id'])
                decisions.append({'spacing': spacing, **choose_front(legal,models)})
    out.mkdir(parents=True)
    save(out/'frozen.json', {'development': development, 'models': models, 'candidates': candidates,
        'online_bell4_under_one_cx_cap': decisions, 'source_code_sha256': sha(Path(__file__)),
        'fit': 'Bell6 spacing3/5 parallel and serial; 12 marginal parities clustered by 4 circuits; ridge lambda=1.',
        'objective': 'Original terminal Z0Z1 parity under full-circuit MWPM, not any-observable failure.',
        'heldout': 'Complete unseen Bell4 instance and distinct QASMBench cat4 source; no held-out labels used.',
        'guard': 'Feature range + no other incident CX + twice leave-one-circuit-out max residual; sensitivity only.',
        'mu': 0, 'distance':3, 'p':.001, 'shots':SHOTS, 'batch_size':BATCH, 'noise':MODEL, 'decoder':DECODER})


def sample_parity(circuit, mask, seed, shots=SHOTS, batch_size=BATCH):
    dem = circuit.detector_error_model(decompose_errors=True)
    decoder = pymatching.Matching.from_detector_error_model(dem)
    sampler = circuit.compile_detector_sampler(seed=seed)
    batches = []
    for start in range(0, shots, batch_size):
        n = min(batch_size, shots-start)
        detectors, actual = sampler.sample(n, separate_observables=True, bit_packed=True)
        estimated = decoder.decode_batch(detectors, bit_packed_shots=True, bit_packed_predictions=True)
        mismatches = estimated ^ actual
        bits = np.unpackbits(mismatches, axis=1, bitorder='little')[:, :circuit.num_observables]
        parity = np.bitwise_xor.reduce(bits[:,[i for i in range(circuit.num_observables) if mask >> i & 1]], axis=1)
        batches.append({'shots':n,'parity_errors':int(parity.sum()),'any_errors':int(np.any(bits,axis=1).sum()),
                        'per_observable_errors':bits.sum(axis=0).tolist()})
    return batches, dem


def worker(out, row):
    p = load_program(BELL4 if row['source'] == 'bell4' else CAT)
    if p['source_sha256'] != row['source_sha256']:
        raise ValueError('Frozen source changed')
    plan = row['plan']
    ideal,meta = generate_program(p,plan)
    validation = validate_physical(ideal,meta,p,4)
    validation['original_readout'] = readout_validation(ideal,meta,p,4)
    validation['all_generators'] = validate_clifford_generators(p,plan,2)
    mask = parity_mask(meta['external_flows'],4,(0,1))
    noisy = add_noise(ideal,.001)
    if len(noisy.shortest_graphlike_error()) != 3:
        raise AssertionError('Unexpected graphlike distance')
    identifier = objsha(noisy)
    seed = int.from_bytes(hashlib.sha256(('transfer_20261105_v1:'+identifier).encode()).digest()[:8], 'little')
    batches,dem = sample_parity(noisy,mask,seed)
    errors = sum(b['parity_errors'] for b in batches)
    stem = out/'samples'/row['id']
    ideal.to_file(str(stem)+'_ideal.stim')
    noisy.to_file(str(stem)+'.stim')
    dem.to_file(str(stem)+'.dem')
    save(out/'certificates'/(row['id']+'.json'), {'metadata':meta,'validation':validation})
    result = {**{k:v for k,v in row.items() if k!='plan'},'shots':SHOTS,'errors':errors,'rate':errors/SHOTS,
        'wilson95':wilson_interval(errors,SHOTS), 'any_errors':sum(b['any_errors'] for b in batches),
        'parity_mask':mask, 'batch_size':BATCH, 'batches':batches, 'seed':seed,
        'ideal_sha256':objsha(ideal), 'noisy_sha256':identifier, 'dem_sha256':objsha(dem),
        'distance':3,'p':.001,'model_id':MODEL,'decoder_id':DECODER,
        'ticks':noisy.num_ticks,'physical_qubits':noisy.num_qubits, 'timing_and_resources':features(p,plan)}
    save(stem.with_suffix('.json'),result)
    print(f"{row['id']}: {errors}/{SHOTS}",flush=True)
    return result


def run(out):
    path = out/'frozen.json'
    frozen = json.loads(path.read_text())
    rel = path.relative_to(ROOT)
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    committed = subprocess.check_output(['git','show',f'{commit}:{rel}'],cwd=ROOT)
    if committed != path.read_bytes() or frozen['source_code_sha256'] != sha(Path(__file__)):
        raise ValueError('Commit the frozen design and exact runner before sampling')
    (out/'samples').mkdir()
    (out/'certificates').mkdir()
    save(out/'run_start.json',{'freeze_commit':commit,'frozen_sha256':sha(path),
                               'started_utc':datetime.now(timezone.utc).isoformat()})
    with ProcessPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(worker, [out]*len(frozen['candidates']), frozen['candidates']))
    if len({r['noisy_sha256'] for r in records}) != len(records):
        raise ValueError('Duplicate circuit identity')
    save(out/'summary.json', {'records':records, 'new_shots':sum(r['shots'] for r in records), 'mu':0})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('prepare','run'))
    parser.add_argument('--output',type=Path,default=OUT)
    args = parser.parse_args()
    globals()[args.stage](args.output.resolve())
