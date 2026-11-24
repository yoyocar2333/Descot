"""Count complete block geometry with separate ancilla lifetimes per time pipe.

An XY coordinate reused by disconnected operations is not one live ancilla.
These block metrics are not QEC-round or Stim-TICK conversions.
"""
from collections import defaultdict
from tqec.utils.position import Position3D


def measure_geometry(graph,positions,input_z,output_z):
    data=set(map(tuple,positions));ancilla=defaultdict(list)
    for cube in graph.cubes:
        p=cube.position
        if (p.x,p.y) not in data:ancilla[(p.x,p.y)].append(p.z)
    for x,y in data:
        for z in range(input_z,output_z):
            if not graph.has_pipe_between(Position3D(x,y,z),Position3D(x,y,z+1)):
                raise ValueError('Missing protected data lifetime')
    segments=[]
    for (x,y),zs in sorted(ancilla.items()):
        runs=[]
        for z in sorted(zs):
            if not runs or z!=runs[-1][-1]+1 or not graph.has_pipe_between(Position3D(x,y,z-1),Position3D(x,y,z)):
                runs.append([z])
            else:runs[-1].append(z)
        for run in runs:
            segments.append(dict(x=x,y=y,first_cube_z=run[0],last_cube_z=run[-1],native_voxels=len(run),
                lifetime_block_z=len(run),temporal_pipe_count=len(run)-1))
    return dict(input_boundary_block_z=input_z,output_boundary_block_z=output_z,
        template_block_z=output_z-input_z,data_lifetime_block_z=len(data)*(output_z-input_z),
        ancilla_voxel_count=sum(x['native_voxels'] for x in segments),
        ancilla_lifetime_block_z=sum(x['lifetime_block_z'] for x in segments),
        ancilla_lifetime_segments=segments,distinct_ancilla_xy=len(ancilla),
        complete_graph_cubes=graph.num_cubes,complete_graph_pipes=len(graph.pipes),
        note='Exact connected same-XY timelike block segments; each ancilla cube contributes one block-z. Disconnected reuse is split even if consecutive z. Data duration is boundary separation. No QEC-round/TICK conversion.')


if __name__=='__main__':
    import argparse,hashlib,json
    from pathlib import Path
    from hamada_projection_control import graph
    from public_clifford import graph_program
    from run_grover_competition import source_program
    from public_candidate_pool import digest
    root=Path(__file__).resolve().parent
    ap=argparse.ArgumentParser();ap.add_argument('--result',type=Path,default=root/'results/hamada_projection_2026-11-24');args=ap.parse_args()
    _,program=source_program();controls=json.loads((args.result/'controls.json').read_text())
    pool=json.loads((root/'results/grover_competition_2026-11-17/candidate_pool.json').read_text())
    baseline=next(r for r in pool if r['candidate_id']=='g174');g,_,m=graph_program(program,baseline['plan'])
    rows=[dict(id='fixed_g174',plan_sha256=baseline['plan_sha256'],**measure_geometry(g,m['logical_block_xy'],0,m['output_z']))]
    for control in controls:
        g,_,m=graph(program,control['plan'])
        rows.append(dict(id=control['policy'],plan_sha256=digest(control['plan']),**measure_geometry(g,m['logical_block_xy'],0,m['output_z'])))
    report=dict(source_sha256=program['source_sha256'],metric_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                control_file_sha256=hashlib.sha256((args.result/'controls.json').read_bytes()).hexdigest(),rows=rows,
                common_domain='Logical block geometry only. Native asynchronous reference differs from old homogeneous candidate pool; no hardware-cap, rate or speedup claim.')
    target=args.result/'footprint_metrics.json'
    if target.exists():raise FileExistsError('Preserve frozen metrics; select fresh result directory')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{k:r[k] for k in ['id','template_block_z','data_lifetime_block_z','ancilla_lifetime_block_z','complete_graph_cubes','complete_graph_pipes']} for r in rows],indent=2))
