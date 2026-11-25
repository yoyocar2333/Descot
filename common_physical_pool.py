"""Shared-coordinate physical pool and equal-row-budget offline selectors.

Qubit relabeling changes no gates, noise, detectors, measurements or observable
basis. Device catalogues are explicit experiment resources, not measured chips.
"""
from copy import deepcopy

import stim

from public_candidate_pool import digest
from projection_geometry_metrics import measure_geometry
from tqec.utils.position import Position3D


def catalogue(circuits):
    sites=set()
    for c in circuits:
        coords=c.get_final_qubit_coordinates()
        if len(coords)!=c.num_qubits or len(set(map(tuple,coords.values())))!=len(coords):
            raise ValueError('Static injective physical coordinates required')
        sites.update(map(tuple,coords.values()))
    return sorted(sites)


def remap(circuit,sites):
    if len(set(map(tuple,sites)))!=len(sites):raise ValueError('Duplicate device coordinate')
    lookup={tuple(p):i for i,p in enumerate(sites)}
    coordinates=circuit.get_final_qubit_coordinates()
    if any(tuple(p) not in lookup for p in coordinates.values()):
        raise ValueError('Complete circuit requires sites outside the declared device')
    mapping={q:lookup[tuple(p)] for q,p in coordinates.items()}
    if len(set(mapping.values()))!=len(mapping):raise ValueError('Noninjective remap')

    def target(t):
        if t.is_x_target:return stim.target_x(mapping[t.value],invert=t.is_inverted_result_target)
        if t.is_y_target:return stim.target_y(mapping[t.value],invert=t.is_inverted_result_target)
        if t.is_z_target:return stim.target_z(mapping[t.value],invert=t.is_inverted_result_target)
        if t.is_qubit_target:
            q=mapping[t.value]
            return stim.target_inv(q) if t.is_inverted_result_target else stim.GateTarget(q)
        return t  # Relative records, sweep bits, combiners are NOT qubit IDs.

    def visit(body):
        out=stim.Circuit()
        for op in body:
            if isinstance(op,stim.CircuitRepeatBlock):out.append(stim.CircuitRepeatBlock(op.repeat_count,visit(op.body_copy())))
            else:out.append(op.name,[target(t) for t in op.targets_copy()],op.gate_args_copy())
        return out
    out=stim.Circuit()
    # Unused hardware holds no logical state and receives no synthetic noise.
    used=set(mapping.values())
    for q,p in enumerate(sites):
        if q not in used:out.append('QUBIT_COORDS',[q],p)
    out+=visit(circuit)
    if out.num_qubits!=len(sites) or out.get_final_qubit_coordinates()!={i:list(p) for i,p in enumerate(sites)}:
        raise ValueError('Coordinate normalization differs')
    if (out.num_measurements,out.num_detectors,out.num_observables,out.num_ticks)!=(circuit.num_measurements,circuit.num_detectors,circuit.num_observables,circuit.num_ticks):
        raise ValueError('Quantum/measurement timing changed')
    return out,mapping


def physical_memory_features(graph,meta):
    positions=meta['logical_block_xy'];m=measure_geometry(graph,positions,meta['input_z'],meta['output_z'])
    plain=[]
    for q,(x,y) in enumerate(positions):
        zs=[]
        for z in range(meta['input_z']+1,meta['output_z']):
            pipes=graph.pipes_at(Position3D(x,y,z))
            if len(pipes)==2 and all(p.direction.value==2 and not p.kind.has_hadamard for p in pipes):zs.append(z)
        plain.append(dict(qubit=q,cube_z=zs,count=len(zs)))
    return dict(template_block_z=m['template_block_z'],data_lifetime_block_z=m['data_lifetime_block_z'],
        ancilla_lifetime_block_z=m['ancilla_lifetime_block_z'],total_lifetime_block_z=m['data_lifetime_block_z']+m['ancilla_lifetime_block_z'],
        plain_data_storage_cubes=sum(r['count'] for r in plain),plain_data_storage_detail=plain,
        ancilla_lifetime_segments=m['ancilla_lifetime_segments'],geometry_cubes=m['complete_graph_cubes'],
        storage_definition='Internal data cube with exactly two ordinary temporal pipes and no spatial branch; geometry feature, not the old profile-specific logical protected idle or calibrated error risk.')


POLICIES={
    'duration_then_volume':('template_block_z','total_lifetime_block_z'),
    'volume_then_duration':('total_lifetime_block_z','template_block_z'),
    'plain_storage_then_duration':('plain_data_storage_cubes','template_block_z'),
    'static_sites_tick_then_volume':('static_site_ticks','total_lifetime_block_z'),
}


def select(rows,policy,reference_id,budget):
    if policy not in POLICIES:raise ValueError('Unsupported/unqualified scorer; retired raw proxy must not be revived')
    if type(budget) is not int or budget!=len(rows):raise ValueError('Exact same complete-pool row evaluation budget required')
    ids=[r['candidate_id'] for r in rows]
    if len(set(ids))!=len(ids) or reference_id not in ids:raise ValueError('Missing reference or duplicate candidates')
    if any(not r['qualified_complete_output'] or r['outside_device_sites'] for r in rows):
        raise ValueError('Do not silently remove an infeasible/unqualified physical candidate')
    if len({r['device_sha256'] for r in rows})!=1:raise ValueError('Not one common device')
    if len({tuple(r['external_flows']) for r in rows})!=1:raise ValueError('Complete observable basis differs')
    keys=POLICIES[policy];scored=[(tuple(r['features'][k] for k in keys),r) for r in rows]
    optimum=min(s for s,r in scored);ties=sorted(r['candidate_id'] for s,r in scored if s==optimum)
    winner=reference_id if reference_id in ties else ties[0]
    return dict(policy=policy,stages=list(keys),candidate_id=winner,tied_optima=ties,optimum=list(optimum),
        reference_id=reference_id,switched=winner!=reference_id,pool_size=len(rows),row_evaluations=len(rows),
        budget=budget,pool_sha256=digest(rows),mu=0,
        interpretation='Offline selector on shared preconstructed physical pool. Equal row counts are not equal route-search calls/CPU; no LER or novelty claim.')
