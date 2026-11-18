import json
from pathlib import Path

import pytest
import stim

from linear_benchmark import generated_qasm, load_selected
from public_candidate_pool import features
from public_clifford import load_program, logical_circuit, schedule_program
from public_gate_pool import enumerate_gate_plans
from public_readout import classical_bits
from run_linear_competition import check

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results/linear_competition_2026-11-18"


def test_public_generation_keeps_every_gate_and_rejected_seed():
    manifest, program = load_selected()
    assert manifest["selected_seed"] == 1
    assert [r["seed"] for r in manifest["seed_search"]] == [0, 1]
    assert program["operation_counts"] == {"barrier": 1, "cx": 5, "measure": 4, "x": 5}
    assert len(program["operations"]) == 15
    for row in manifest["seed_search"]:
        assert (ROOT / row["path"]).read_bytes() == generated_qasm(row["seed"])
    with pytest.raises(ValueError, match="Only forward"):
        load_program(ROOT / manifest["seed_search"][0]["path"])


def test_all_candidates_and_uncapped_parallel_reference_are_retained():
    _, program = load_selected()
    plans = enumerate_gate_plans(program)
    assert len(plans) == 7
    baseline = schedule_program(program, mode="parallel")
    assert any(p["layers"] == baseline["layers"] for p in plans)
    fs = [features(program, p) for p in plans]
    minimum = [f for f in fs if f["physical_layers"] == min(x["physical_layers"] for x in fs)]
    assert len(minimum) == 3
    assert {f["physical_layers"] for f in minimum} == {4}
    assert len({str(f["protected_idle_intervals_block_z"]) for f in minimum}) == 3
    assert {f["total_protected_idle_block_z"] for f in minimum} == {18}
    assert any(len(layer["operation_ids"]) == 2 and layer["kind"] == "cx"
               for p in plans for layer in p["layers"])


def test_complete_physical_four_bit_outputs_match_source_for_all_signed_inputs():
    _, program = load_selected()
    summary = json.loads((RESULT / "summary.json").read_text())
    assert summary["minimum_plans"] == summary["unique_noisy_circuits"] == 3
    assert summary["new_shots"] == summary["sampler_calls"] == 0
    assert summary["complete_z_output_little_endian"] == [1, 1, 0, 1]
    for name in summary["candidate_ids"]:
        row = json.loads((RESULT / "certificates" / (name + ".json")).read_text())
        assert row["num_observables"] == row["validation"]["full_z_readout_rank"] == 4
        assert row["shortest_graphlike_error"] == 3
        assert len(row["generators"]) == 8
        assert {g["input_generator"] for g in row["generators"]} == {axis+str(q) for axis in "XZ" for q in range(4)}
        assert len(row["validation"]["signed_inputs"]) == 16
        assert len(row["validation"]["final_faults"]) == 4
        assert len(row["backend_meta"]["instruction_trace"]) == 15
        for signed in row["validation"]["signed_inputs"]:
            state = stim.TableauSimulator()
            for q, b in enumerate(signed["input_signs"]):
                if b:
                    state.x(q)
            state.do(logical_circuit(program))
            assert classical_bits(row["backend_meta"], signed["observable_parities"]) == [int(state.peek_z(q) == -1) for q in range(4)]
        assert row["counts"] is row["confidence_interval"] is None


def test_family_split_has_no_development_heldout_overlap_or_sampling_permission():
    split = json.loads((ROOT / "benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json").read_text())
    assert set(split["development_families"]).isdisjoint(split["held_out_families"])
    assert "grover_search" in split["development_families"]
    assert split["held_out_families"] == ["qiskit_xcx_linear_reversible"]
    assert not split["held_out_sampling_allowed"]
    assert split["noisy_label_access"]["qiskit_xcx_linear_reversible"] == "sealed"
    assert split["general_scheduler_mu"] == 0


def test_raw_archives_replay_without_compilation_or_sampling():
    check()
    resources = json.loads((RESULT / "resource_certificate.json").read_text())
    assert resources["available_physical_sites"] > 0
    assert all(r["uses_exact_common_catalogue"] for r in resources["candidate_rows"])
