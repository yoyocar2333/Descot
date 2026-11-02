"""Exact bounded candidate pool for a complete public instruction DAG.

This is an offline candidate selector, not a replacement DASCOT router.
All virtual/readout instructions and all ready H instructions are drained first.
At CX fronts every nonempty footprint-compatible subset is enumerated. No gate
cancellation, physical compilation, Monte Carlo, or noisy labels in features.
"""
from itertools import combinations
import hashlib
import json

import numpy as np

from public_clifford import positions_for, cnot_paths, validate_plan


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def enumerate_plans(program, spacing=3, cap=256):
    """Fail rather than silently truncate the pool if the complete pool exceeds cap."""
    if type(cap) is not int or cap < 1:
        raise ValueError('Positive integer candidate cap required')
    ops = program['operations']; n = program['logical_qubits']
    positions = positions_for(n, spacing); plans = []

    def visit(done, orientation, layers):
        if len(done) == len(ops):
            if len(plans) >= cap:
                raise ValueError('Exact candidate pool exceeds declared cap')
            plan = {'mode': 'exact_h_first_pool_v1', 'spacing': spacing, 'layers': layers}
            validate_plan(program, plan)
            plans.append(plan)
            return
        ready = [o for o in ops if o['id'] not in done and set(o['predecessors']) <= done]
        if not ready:
            raise ValueError('Invalid instruction DAG')
        instant = [o for o in ready if o['name'] in ('x', 'measure')]
        hs = [o for o in ready if o['name'] == 'h']
        if instant:
            choices = [instant]; kind = 'virtual_or_readout'
        elif hs:
            choices = [hs]; kind = 'h'
        else:
            if any(o['name'] != 'cx' for o in ready):
                raise ValueError('Unsupported instruction in candidate pool')
            choices = []; kind = 'cx'
            for count in range(1, len(ready)+1):
                for subset in combinations(ready, count):
                    footprints = [cnot_paths(*o['qubits'], positions, orientation)[2] for o in subset]
                    if all(not (a & b) for i, a in enumerate(footprints) for b in footprints[i+1:]):
                        choices.append(subset)
        for chosen in choices:
            after = list(orientation)
            for op in chosen:
                if op['name'] == 'h': after[op['qubits'][0]] ^= 1
            ids = [o['id'] for o in chosen]
            visit(done | set(ids), after, layers + [{'operation_ids': ids, 'kind': kind,
                  'orientation_before': list(orientation), 'orientation_after': after}])
    visit(set(), [0]*n, [])
    if len({digest(p) for p in plans}) != len(plans):
        raise AssertionError('Duplicate candidate plan')
    return plans


def features(program, plan):
    positions, _ = validate_plan(program, plan)
    n = len(positions); z = 0; active = [[] for _ in range(n)]; cx_times = {}
    footprint_volume = 0; cx_steps = h_layers = 0
    for layer in plan['layers']:
        if layer['kind'] == 'virtual_or_readout': continue
        if layer['kind'] == 'h': h_layers += 1
        else: cx_steps += 1
        for i in layer['operation_ids']:
            op = program['operations'][i]
            for q in op['qubits']: active[q].append((z, z+3))
            if op['name'] == 'cx':
                pair = tuple(op['qubits']); cx_times.setdefault(pair, []).append((z, z+3))
                footprint_volume += 3*(len(cnot_paths(*pair, positions, layer['orientation_before'])[2])-2)
        z += 3
    idle = []
    for intervals in active:
        end = 0; gaps = []
        for start, stop in intervals:
            if start > end: gaps.append(start-end)
            end = stop
        if z > end: gaps.append(z-end)
        idle.append(gaps)
    separations = [b[0]-a[1] for intervals in cx_times.values() for a,b in zip(intervals, intervals[1:])]
    flat = [gap for gaps in idle for gap in gaps]
    return {'physical_layers': z//3, 'template_block_z': z, 'cx_routing_steps': cx_steps,
            'logical_h_layers': h_layers, 'qec_rounds': None, 'stim_ticks': None,
            'data_reservation_block_z': n*z, 'ancilla_reservation_block_z': footprint_volume,
            'protected_idle_intervals_block_z': idle, 'total_protected_idle_block_z': sum(flat),
            'max_protected_idle_block_z': max(flat, default=0),
            'squared_protected_idle_block_z2': sum(g*g for g in flat),
            'cx_recurrence_separations_block_z': separations,
            'cx_gap_squared_block_z2': sum(g*g for g in separations),
            'feature_note': 'CX recurrence separation includes intervening H, not just protected idle. No QEC-round or TICK inference.'}


def fit_model(rows, use_wait=True):
    """Fixed ridge on logit(any-error), development labels only; no hyperparameter search.

    Leave-one-plan-out maximum residual is an empirical sensitivity envelope,
    NOT a confidence interval or guaranteed held-out coverage.
    """
    fields = ['physical_layers'] + (['cx_gap_squared_block_z2'] if use_wait else [])
    x = np.array([[r['features'][f] for f in fields] for r in rows], dtype=float)
    y = np.array([np.log((r['failures_any']+.5)/(r['shots']-r['failures_any']+.5)) for r in rows])
    center = x.mean(axis=0); scale = x.std(axis=0); scale[scale == 0] = 1
    a = np.column_stack([np.ones(len(x)), (x-center)/scale])
    penalty = np.diag([0.] + [1.]*len(fields))
    def solve(indices):
        return np.linalg.solve(a[indices].T@a[indices] + penalty, a[indices].T@y[indices])
    indices = np.arange(len(rows)); beta = solve(indices)
    residuals = [float(y[i] - a[i]@solve(indices[indices != i])) for i in indices]
    return {'fields': fields, 'center': center.tolist(), 'scale': scale.tolist(), 'beta': beta.tolist(),
            'ridge_lambda': 1., 'loo_max_abs_logit_residual': max(abs(v) for v in residuals),
            'loo_logit_residuals': residuals, 'calibration_ids': [r['candidate_id'] for r in rows],
            'envelope_note': 'Empirical LOO sensitivity, not statistical prediction coverage; geometry extrapolation is uncalibrated.'}


def predict(model, row):
    x = np.array([row['features'][f] for f in model['fields']])
    a = np.r_[1., (x-np.array(model['center']))/np.array(model['scale'])]
    return float(a@np.array(model['beta']))


def select(rows, model, pool='all', guarded=False):
    if pool not in ('all', 'serial_matched'): raise ValueError('Unknown comparison pool')
    allowed = list(rows)
    if pool == 'serial_matched':
        allowed = [r for r in rows if r['features']['cx_routing_steps'] == 4 and r['features']['physical_layers'] == 16]
    if not allowed: raise ValueError('Empty candidate pool')
    min_layers = min(r['features']['physical_layers'] for r in allowed)
    shortlist = [r for r in allowed if r['features']['physical_layers'] == min_layers]
    baseline = min(shortlist, key=lambda r: r['candidate_id'])
    best = min(shortlist, key=lambda r: (predict(model, r), r['candidate_id']))
    margin = predict(model, baseline)-predict(model, best)
    switched = best['candidate_id'] != baseline['candidate_id']
    if guarded and margin <= 2*model['loo_max_abs_logit_residual']:
        best = baseline; switched = False
    return {'pool': pool, 'candidate_id': best['candidate_id'], 'baseline_candidate_id': baseline['candidate_id'],
            'shortlist_size': len(shortlist), 'pool_size': len(allowed), 'guarded': guarded,
            'switch_from_baseline': switched, 'baseline_minus_best_logit': margin,
            'guard_threshold': 2*model['loo_max_abs_logit_residual'],
            'feature_evaluations': len(rows), 'model_evaluations': len(shortlist),
            'policy': 'Hard minimum physical-layer depth first; fixed ridge risk only within depth ties. Offline selection; scheduler mu=0.'}
