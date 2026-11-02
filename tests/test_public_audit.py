from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_public_audit import inspect_qasm

FOLDER = Path(__file__).resolve().parents[1] / "benchmarks/public_2026-11-02/qasmbench"


def test_hs4_is_a_complete_clifford_candidate_with_parallel_choices():
    result = inspect_qasm(FOLDER / "hs4_n4.qasm")
    assert result["all_unitaries_clifford"]
    assert result["max_ready_cx"] == 2
    assert result["operation_counts"]["h"] > 0
    assert result["operation_counts"]["measure"] == 4
    assert not result["full_physical_profile_supported"]


def test_dynamic_syndrome_macro_is_expanded_but_feedback_is_not_deleted():
    result = inspect_qasm(FOLDER / "qec_sm_n5.qasm")
    assert result["operation_counts"]["cx"] == 4
    assert result["operation_counts"]["if_else"] == 3
    assert result["max_ready_cx"] == 1
    assert "if_else" in result["dynamic_or_opaque_names"]
    assert not result["full_physical_profile_supported"]


def test_nonclifford_and_shared_qubit_chains_are_identified():
    encoder = inspect_qasm(FOLDER / "qec_en_n5.qasm")
    assert "t" in encoder["non_clifford_operation_names"]
    chain = inspect_qasm(FOLDER / "cat_state_n4.qasm")
    assert chain["max_ready_cx"] == 1
    assert chain["operation_counts"]["cx"] == 3


def test_delayed_parallel_choices_are_not_confused_with_asap_front_count():
    result = inspect_qasm(FOLDER / "error_correctiond3_n5.qasm")
    assert result["max_ready_cx"] == 1
    assert len(result["incomparable_cx_pairs"]) > 0


def test_complete_cnot_program_can_retain_explicit_terminal_readout(tmp_path):
    path = tmp_path / "cnot.qasm"
    path.write_text('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\ncx q[0],q[1];\nmeasure q -> c;\n')
    result = inspect_qasm(path)
    assert result["full_physical_profile_supported"]
    assert result["terminal_readout"] == [{"qubit": 0, "classical_bit": 0}, {"qubit": 1, "classical_bit": 1}]
