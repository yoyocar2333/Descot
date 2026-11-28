from copy import deepcopy
import json
from pathlib import Path
import pytest
import stim
from circls_partial_control import source_unitary,record_fault
from public_partial_readout import load_partial_program
from public_clifford import logical_circuit

ROOT=Path(__file__).resolve().parents[1]


def inputs():
    program=load_partial_program(ROOT/'benchmarks/public_2026-11-27/mqt/bv_n3_11.qasm')
    rows=json.loads((ROOT/'results/public_bv_2026-11-27/candidate_pool.json').read_text())
    return program,rows


def test_all_nine_complete_source_traces_and_signed_unitaries():
    p,rows=inputs()
    for row in rows:
        for mask in range(8):
            qasm,c,trace,reads=source_unitary(p,row['plan'],mask)
            assert len(trace)==13 and sorted(trace)==list(range(13))
            assert [r['qubit'] for r in reads]==[1,2]
            assert len(reads)==2 and 'measure' not in qasm
            prefix=stim.Circuit()
            for q in range(3):
                if mask>>q&1:prefix.append('X',[q])
            assert c.to_tableau()==(prefix+logical_circuit(p)).to_tableau()
            assert qasm.count('cx ')==2 and qasm.count('h ')==8


def test_missing_original_output_is_rejected():
    p,rows=inputs();p=deepcopy(p);p['terminal_readout']=p['terminal_readout'][:1]
    with pytest.raises(ValueError,match='all original'):source_unitary(p,rows[0]['plan'])


@pytest.mark.parametrize('measurement,reset,pauli',[('M','R','X'),('MX','RX','Z'),('MY','RY','X')])
def test_physical_readout_fault_is_a_real_pauli(measurement,reset,pauli):
    c=stim.Circuit(f'{reset} 0\n{measurement} 0')
    f=record_fault(c,0)
    assert int(c.reference_sample()[0])^int(f.reference_sample()[0])==1
    assert f[1].name==pauli


def test_invalid_record_fault_rejected():
    with pytest.raises(ValueError,match='out of range'):record_fault(stim.Circuit('R 0\nM 0'),1)
