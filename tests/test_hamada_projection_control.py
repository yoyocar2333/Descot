from copy import deepcopy
from pathlib import Path
import pytest

from hamada_projection_control import build_driver,schedule,validate,graph,color_path
from run_grover_competition import source_program

@pytest.fixture(scope='module')
def native(tmp_path_factory):
    _,p=source_program();binary=tmp_path_factory.mktemp('projection')/'driver';build_driver(binary)
    return p,binary

@pytest.mark.parametrize('policy',['source_order','height_priority'])
def test_complete_public_source_keeps_native_heights_and_backtracking(native,policy):
    p,binary=native;r=schedule(p,binary,policy);positions,trace,_=validate(p,r['plan'])
    assert sorted(x['operation_id'] for x in r['plan']['events'])==list(range(18))
    assert sum(x['name']=='h' for x in trace)==10 and sum(x['name']=='measure' for x in trace)==2
    cx=[e for e in r['plan']['events'] if e['path']]
    assert len(cx)==2 and any(b[2]<a[2] for e in cx for a,b in zip(e['path'],e['path'][1:]))
    assert any(e['kinks']==3 for e in cx)
    g,_,meta=graph(p,r['plan'])
    assert meta['terminal_readout']==p['terminal_readout'] and meta['mu']==0
    for e in cx:
        target=next(x for x in meta['routed_geometry'] if x['operation_id']==e['operation_id'])
        assert target['path_block_xyz']==[[x,y,z+1] for x,y,z in e['path']]

@pytest.mark.parametrize('damage',['missing','dependency','height','kink','path','gate'])
def test_invalid_source_or_projection_never_uses_flattening_fallback(native,damage):
    p,binary=native;p=deepcopy(p);r=schedule(p,binary);plan=r['plan']
    if damage=='missing':plan['events'].pop()
    elif damage=='dependency':plan['events'][0]['operation_id']=3
    elif damage=='height':plan['events'][3]['heights_before'][0]+=1
    elif damage=='kink':next(x for x in plan['events'] if x['path'])['kinks']=0
    elif damage=='path':next(x for x in plan['events'] if x['path'])['path'][1][0]+=2
    else:p['operations'][0]['name']='s'
    with pytest.raises(ValueError):validate(p,plan)

def test_classical_dependency_not_expressible_by_native_queues_is_rejected(native):
    p,binary=native;p=deepcopy(p);p['operations'][1]['predecessors']=[0]
    with pytest.raises(ValueError,match='rejected'):schedule(p,binary)

def test_coloring_has_two_distinct_matching_walls_for_every_plain_pipe():
    path=[[0,0,0],[0,1,0],[0,2,0],[0,2,1],[1,2,1],[2,2,1]]
    colors=color_path(path,'ZXX','ZXZ')
    for a,b,ka,kb in zip(path,path[1:],colors,colors[1:]):
        d=next(i for i in range(3) if a[i]!=b[i]);walls=[i for i in range(3) if i!=d]
        assert ka[walls[0]]!=ka[walls[1]] and all(ka[i]==kb[i] for i in walls)

def test_exact_ancilla_lifetime_metrics_preserve_every_native_voxel(native):
    from projection_geometry_metrics import measure_geometry
    p,binary=native;r=schedule(p,binary);g,_,m=graph(p,r['plan'])
    metric=measure_geometry(g,m['logical_block_xy'],0,m['output_z'])
    expected=sum(len(e['path'])-2 for e in r['plan']['events'] if e['path'])
    assert metric['ancilla_voxel_count']==expected==metric['ancilla_lifetime_block_z']
    assert metric['data_lifetime_block_z']==2*m['output_z']
    assert sum(x['temporal_pipe_count'] for x in metric['ancilla_lifetime_segments'])>0
