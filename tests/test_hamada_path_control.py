from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from hamada_path_control import build_oracle, route_plan, routed_graph, validate_path
from public_clifford import positions_for
from run_grover_competition import source_program

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def inputs(tmp_path_factory):
    _,program=source_program()
    pool=json.loads((ROOT/'results/grover_competition_2026-11-17/candidate_pool.json').read_text())
    binary=tmp_path_factory.mktemp('native_path')/'oracle';build_oracle(binary)
    return program,pool[-1]['plan'],binary


@pytest.mark.parametrize('oc,ot',[(0,0),(0,1),(1,0),(1,1)])
def test_unmodified_author_kernel_supports_all_oriented_boundary_pairs(inputs,oc,ot):
    _,_,binary=inputs
    payload=f'4 4 2 0 1 0\n0 0 {oc}\n3 3 {ot}\n'
    raw=subprocess.run([str(binary)],input=payload,text=True,capture_output=True,check=True).stdout.splitlines()
    size,kinks=map(int,raw[0].split());path=[list(map(int,s.split())) for s in raw[1:]]
    first,second,footprint=validate_path(path,positions_for(2,3),[oc,ot],0,1,[4,4])
    # Achieves the spatial Manhattan + mandatory temporal-edge lower bound.
    assert size==8 and kinks==1 and len(footprint)==7
    assert first[-1][:2]==second[0][:2]


def test_search_result_is_actual_ancilla_geometry_in_complete_source_graph(inputs):
    p,plan,binary=inputs;r=route_plan(p,plan,binary);g,_,meta=routed_graph(p,r)
    assert set(r['paths'])=={'3','10'} and len(r['calls'])==2
    assert len(meta['instruction_trace'])==18 and meta['terminal_readout']==p['terminal_readout']
    assert meta['physical_layers']==9 and meta['output_z']==27 and meta['mu']==0
    for footprint in meta['gate_footprints']:
        expected={(x,y) for x,y,z in r['paths'][str(footprint['operation_id'])]}
        assert set(map(tuple,footprint['reserved_xy']))==expected
        start=footprint['start_block_z']
        for x,y,z in r['paths'][str(footprint['operation_id'])]:
            from tqec.utils.position import Position3D
            assert Position3D(x,y,start+1+z) in g


@pytest.mark.parametrize('damage',['missing_gate','nonadjacent','wrong_wall','outside','changed_board'])
def test_bad_routes_fail_without_fixed_route_fallback(inputs,damage):
    p,plan,binary=inputs;r=route_plan(p,plan,binary)
    if damage=='missing_gate':del r['paths']['10']
    elif damage=='nonadjacent':r['paths']['3'][2][0]=0
    elif damage=='wrong_wall':r['paths']['3'][1]=[0,1,0]
    elif damage=='outside':r['paths']['3'][2]=[4,0,0]
    else:r['board_xy']=[5,5]
    with pytest.raises(ValueError):routed_graph(p,r)


def test_reserved_full_footprint_is_never_crossed(inputs):
    p,plan,binary=inputs;r=route_plan(p,plan,binary)
    with pytest.raises(ValueError,match='reserved'):
        validate_path(r['paths']['3'],positions_for(2,3),[1,0],0,1,[4,4],[(2,0)])


def test_temporal_backtracking_is_rejected_instead_of_projected(inputs):
    p,plan,binary=inputs;r=route_plan(p,plan,binary)
    # Distinct vertices, adjacent steps, correct endpoint walls, three switches.
    path=[[0,0,0],[1,0,0],[1,0,1],[2,0,1],[2,0,0],[2,1,0],[2,2,0],[2,2,1],[2,3,1],[3,3,1]]
    with pytest.raises(ValueError,match='one temporal switch'):
        validate_path(path,positions_for(2,3),[1,0],0,1,[4,4])
