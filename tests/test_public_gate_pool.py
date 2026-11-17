import copy
import json
from pathlib import Path
import zipfile

import numpy as np
import pytest
from qiskit.circuit.library import HGate, SGate, U3Gate, XGate
import stim

from exact_program_validation import check_exact
from public_candidate_pool import enumerate_plans, features
from public_clifford import load_program, validate_plan
from public_gate_pool import enumerate_gate_plans
from public_readout import classical_bits
from run_public_audit import is_clifford_matrix

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmarks/public_2026-11-17/qasmbench/grover_n2.qasm"
RESULT = ROOT / "results/grover_competition_2026-11-17"


def test_complete_source_and_h_first_parallel_reference_are_retained():
    program = load_program(SOURCE)
    plans = enumerate_gate_plans(program)
    assert program["operation_counts"] == {"cx": 2, "h": 10, "measure": 2, "x": 4}
    assert len(program["operations"]) == 18
    assert len(plans) == 175
    original = enumerate_plans(program)
    assert len(original) == 1
    assert any(p["layers"] == original[0]["layers"] for p in plans)
    fs = [features(program, p) for p in plans]
    d = min(f["physical_layers"] for f in fs)
    assert d == 9
    assert sum(f["physical_layers"] == d for f in fs) == 12
    for plan in plans:
        assert sorted(i for layer in plan["layers"] for i in layer["operation_ids"]) == list(range(18))
        validate_plan(program, plan)


def test_safety_bound_fails_without_returning_a_biased_partial_pool():
    with pytest.raises(ValueError, match="no partial pool"):
        enumerate_gate_plans(load_program(SOURCE), cap=174)
    for cap in [0, -1, True]:
        with pytest.raises(ValueError):
            enumerate_gate_plans(load_program(SOURCE), cap=cap)


def test_no_unsupported_gate_or_original_h_is_deleted():
    program = load_program(SOURCE)
    bad = copy.deepcopy(program)
    bad["operations"][0]["name"] = "s"
    with pytest.raises(ValueError, match="not be dropped"):
        enumerate_gate_plans(bad)
    plan = enumerate_gate_plans(program)[0]
    bad_plan = copy.deepcopy(plan)
    for layer in bad_plan["layers"]:
        if layer["kind"] == "h":
            layer["operation_ids"].pop()
            break
    with pytest.raises(ValueError):
        validate_plan(program, bad_plan)


@pytest.mark.parametrize("angle", [0.1, 0.58, -0.58, np.pi/4])
def test_small_nonclifford_rotations_are_not_snapped_into_support(angle):
    assert not is_clifford_matrix(U3Gate(angle, 0, 0).to_matrix())


@pytest.mark.parametrize("gate", [HGate(), SGate(), XGate()])
def test_exact_clifford_roundtrip_allows_global_phase(gate):
    assert is_clifford_matrix(np.exp(0.37j) * gate.to_matrix())


def test_committed_physical_competition_has_complete_basis_and_full_unitary_checks():
    summary = json.loads((RESULT / "summary.json").read_text())
    assert summary["minimum_plan_count"] == 12
    assert summary["unique_noisy_circuits"] >= 2
    assert summary["new_shots"] == summary["sampler_calls"] == 0
    # The upstream comment mentions A=10, but the complete unchanged circuit
    # has the exact ideal output 11. Validate code semantics, not its comment.
    assert summary["full_original_output_little_endian"] == [1, 1]
    for name in summary["compiled_minimum_candidate_ids"]:
        record = json.loads((RESULT / "certificates" / (name + ".json")).read_text())
        assert record["num_observables"] == 2
        assert record["shortest_graphlike_error"] == 3
        assert record["validation"]["full_z_readout_rank"] == 2
        assert len(record["generators"]) == 4
        assert {g["input_generator"] for g in record["generators"]} == {"X0", "X1", "Z0", "Z1"}
        assert len(record["backend_meta"]["instruction_trace"]) == 18
        assert classical_bits(record["backend_meta"], [0, 0]) == [1, 1]
        assert record["counts"] is record["confidence_interval"] is None
    resource = json.loads((RESULT / "resource_certificate.json").read_text())
    assert resource["available_physical_sites"] == 310
    assert all(r["uses_exact_common_catalogue"] for r in resource["candidate_rows"])


def test_exact_readout_validation_replays_and_rejects_frame_corruption():
    program = load_program(SOURCE)
    summary = json.loads((RESULT / "summary.json").read_text())
    name = summary["compiled_minimum_candidate_ids"][0]
    cert = json.loads((RESULT / "certificates" / (name + ".json")).read_text())
    with zipfile.ZipFile(ROOT / "archives/grover_competition_2026-11-17.zip") as z:
        path = f"results/grover_competition_2026-11-17/circuits/{cert['ideal_sha256']}.stim"
        circuit = stim.Circuit(z.read(path).decode())
    assert check_exact(circuit, cert["backend_meta"], program, True)["sampler_calls"] == 0
    bad = copy.deepcopy(cert["backend_meta"])
    bad["frame_x"][0] ^= 1
    with pytest.raises(AssertionError, match="X-frame"):
        check_exact(circuit, bad, program, True)
