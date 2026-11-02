import copy
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np
import pytest
import stim

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_clifford import (load_program, schedule_program, validate_plan, generate_program,
                             validate_physical, validate_x_generators, logical_circuit, cnot_paths)
from surgery import add_noise

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'benchmarks/public_2026-11-02/qasmbench/hs4_n4.qasm'

@lru_cache
def program(): return load_program(SOURCE)

@lru_cache
def compiled(mode='parallel'):
    p=program();plan=schedule_program(p,mode)
    return generate_program(p,plan)


def test_full_source_instructions_and_classical_mapping_preserved():
    p=program();plan=schedule_program(p)
    assert p['operation_counts']=={'cx':4,'h':20,'measure':4,'x':4}
    assert sorted(i for l in plan['layers'] for i in l['operation_ids'])==list(range(32))
    assert p['terminal_readout']==[{'qubit':q,'classical_bit':q} for q in range(4)]
    original=stim.TableauSimulator();original.do(logical_circuit(p))
    assert [str(s) for s in original.canonical_stabilizers()]==['-Z___','+_Z__','-__Z_','+___Z']


@pytest.mark.parametrize('mode',['parallel','serial'])
def test_complete_program_signed_inputs_frame_faults_and_distance(mode):
    c,m=compiled(mode)
    check=validate_physical(c,m,program(),8,True)
    assert len(check['signed_inputs'])==16
    assert len(check['final_faults'])==4
    assert check['full_source_tableau_including_frame_passed']
    assert m['frame_x']==[1,0,1,0] and m['frame_z']==[0,1,0,1]
    assert len(m['instruction_trace'])==32
    assert len(add_noise(c,.001).shortest_graphlike_error())==3
    assert len(m['gate_footprints'])==4


def test_x_generator_checks_protect_against_phase_only_mistakes():
    p=program(); checks=validate_x_generators(p,schedule_program(p),4)
    assert len(checks)==4
    assert all(r['observable_combination'] for r in checks)


def test_disabling_original_x_frame_is_detected():
    c,m=compiled();bad=copy.deepcopy(m);bad['frame_x']=[0]*4
    with pytest.raises(AssertionError,match='frame'):
        validate_physical(c,bad,program(),4,True)


@pytest.mark.parametrize('fault',['missing_h','duplicate','reorder','orientation'])
def test_changed_source_dependencies_or_orientation_fail_closed(fault):
    p=program();plan=schedule_program(p)
    if fault=='missing_h': plan['layers'][0]['operation_ids'].pop()
    if fault=='duplicate': plan['layers'][1]['operation_ids'].append(plan['layers'][0]['operation_ids'][0])
    if fault=='reorder':plan['layers'][0],plan['layers'][3]=plan['layers'][3],plan['layers'][0]
    if fault=='orientation':plan['layers'][0]['orientation_after'][0]^=1
    with pytest.raises(ValueError):validate_plan(p,plan)


def test_all_four_cnot_orientation_pairs_have_reserved_paths():
    for a in (0,1):
        for b in (0,1):
            first,second,footprint=cnot_paths(0,1,[(0,0),(3,3)],[a,b])
            assert first[0]==(0,0) and second[-1]==(3,3)
            assert first[-1]==second[0]
            assert footprint==set(first+second)


def test_non_clifford_and_dynamic_sources_rejected():
    for name in ('qec_en_n5','qec_sm_n5'):
        with pytest.raises(ValueError,match='Unsupported'):
            load_program(SOURCE.with_name(name+'.qasm'))


def test_both_rotated_cnot_endpoints_preserve_the_conjugate_program(tmp_path):
    source=tmp_path/'rotated.qasm'
    source.write_text('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; h q[1]; cx q[0],q[1]; h q[0]; h q[1]; measure q[0] -> c[0]; measure q[1] -> c[1];')
    p=load_program(source);plan=schedule_program(p)
    c,m=generate_program(p,plan)
    assert validate_physical(c,m,p,8,True)['all_signed_inputs_passed']
    assert len(validate_x_generators(p,plan,4))==2
    assert len(add_noise(c,.001).shortest_graphlike_error())==3


def test_original_classical_outputs_for_all_signed_inputs_and_frame():
    from public_readout import classical_bits
    c,m=compiled();p=program()
    rows=validate_physical(c,m,p,4,True)['signed_inputs']
    for row in rows:
        sim=stim.TableauSimulator()
        for q,bit in enumerate(row['input_signs']):
            if bit:sim.x(q)
        sim.do(logical_circuit(p))
        expected=[int(sim.measure(q)) for q in range(4)]
        assert classical_bits(m,row['observable_parities'])==expected
    assert classical_bits(m,[0]*4)==[1,0,1,0]
