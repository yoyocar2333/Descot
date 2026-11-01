import copy
from functools import lru_cache
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import load_core
from lookahead import schedule,Config
from route_adapter import profile_architecture,request_for,certify,lower,UnsupportedSchedule,sha256_json
from validation import validate

ROOT=Path(__file__).resolve().parents[1]

@lru_cache
def request(span=1,basis='z',idle=0):
    arch,mapping=profile_architecture(span)
    data={'gates':[[0,1],[1,2]],'ops':['cx','cx'],'architecture':arch,'mapping':mapping}
    router=load_core(ROOT.parent/'external/wisq')['sarouting']
    result=schedule(router,data['gates'],arch,mapping,1,Config('two_step',48))
    return request_for(data,result['steps'],basis,idle)

@pytest.mark.parametrize('span',[1,3])
def test_real_router_routes_and_normalization_are_both_legal(span):
    req=request(span);before=sha256_json(req);cert=certify(req)
    assert sha256_json(req)==before
    assert cert['span_from_embedding']==span and cert['mu']==0
    assert cert['normalization']['performed']
    validate(req['gates'],req['architecture'],req['mapping'],cert['canonical_source_steps'])
    for item in cert['corridors']:
        assert set(item['chosen_source_vertices'])<=set(item['reserved_source_vertices'])
        assert set(item['normalized_source_vertices'])<=set(item['reserved_source_vertices'])

@pytest.mark.parametrize('span',[1,3])
@pytest.mark.parametrize('basis',['x','z'])
def test_lowered_circuit_matches_exact_frozen_full_circuit(span,basis):
    req=request(span,basis);c,cert=lower(req)
    rows=json.loads((ROOT/'results/three_qubit_2026-10-31/summary.json').read_text())['records']
    row=next(r for r in rows if (r['basis'],r['bridge_span_blocks'],r['idle_blocks'])==(basis,span,0))
    assert cert['ideal_circuit_sha256']==row['ideal_circuit_sha256']
    assert c.num_ticks==row['num_ticks'] and c.num_qubits==row['num_qubits']
    assert cert['physical_validation']['all_eight_signed_inputs_passed']
    assert cert['block_footprint_verification']['matched_actual_backend_graph']
    assert len(cert['block_footprint_verification']['occupied_block_xy'])==3+2*span

def test_timing_is_explicit_and_independent_of_source_depth():
    a=certify(request(1,'z',0));b=certify(request(1,'z',1))
    assert a['source_step_count']==b['source_step_count']==2
    assert a['gate_block_z']==[[0,3],[3,6]]
    assert b['gate_block_z']==[[0,3],[4,7]]
    _,cert=lower(request(1,'z',1))
    assert cert['num_ticks']==167

def test_logical_labels_can_be_renamed_without_changing_embedding():
    req=copy.deepcopy(request());rename={0:10,1:20,2:30}
    req['gates']=[[rename[q] for q in g] for g in req['gates']]
    req['mapping']=[[rename[q],v] for q,v in req['mapping']]
    req['steps']=[[[gid,[rename[q] for q in args],path]] for [(gid,args,path)] in req['steps']]
    assert certify(req)['logical_id_to_backend_index']==[[10,0],[20,1],[30,2]]

def test_valid_but_unsupported_detour_is_rejected():
    req=copy.deepcopy(request());w=req['architecture']['width']
    req['steps'][0][0]=[0,[0,1],[1,2,2+w,2+2*w,2+3*w]]
    validate(req['gates'],req['architecture'],req['mapping'],req['steps'])
    with pytest.raises(UnsupportedSchedule) as error:certify(req)
    assert error.value.code=='corridor'

@pytest.mark.parametrize('field,value,code',[
    ('ops',['cx','t'],'operations'),('gates',[[0,1],[0,1]],'program'),
    ('basis','y','qec_conditions'),('distance',5,'qec_conditions'),('distance',True,'qec_conditions'),
    ('schema_id','unknown','schema'),('steps',[],'schedule'),('mapping',[[0,8],[1,8],[2,40]],'mapping'),
    ('timing',{'policy':'guess_from_depth','intergate_storage_blocks':0},'timing'),
    ('timing',{'policy':'three_block_cnot_with_explicit_storage_v1','intergate_storage_blocks':2},'timing'),
    ('timing',{'policy':'three_block_cnot_with_explicit_storage_v1','intergate_storage_blocks':True},'timing')])
def test_unsupported_requests_fail_closed(field,value,code):
    req=copy.deepcopy(request());req[field]=value
    with pytest.raises(UnsupportedSchedule) as error:certify(req)
    assert error.value.code==code

def test_hardware_defects_are_not_silently_ignored():
    req=copy.deepcopy(request());req['architecture']['disabled_vertices']=[16]
    with pytest.raises(UnsupportedSchedule) as error:certify(req)
    assert error.value.code=='architecture'

def test_malformed_route_and_gate_record_are_rejected():
    for item in [[0,None,[15,16,23]],[0,[0,1],[15,23]],[0,[0,1],[]],[0,[False,1],[15,16,23]]]:
        req=copy.deepcopy(request());req['steps'][0][0]=item
        with pytest.raises(UnsupportedSchedule):certify(req)
