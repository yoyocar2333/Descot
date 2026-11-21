from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import pytest
import stim

from circls_native_control import (basis_view, combine_specs, evaluate,
                                  final_record_fault, rank, serialize)
from public_clifford import load_program, logical_circuit

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def development():
    program = load_program(ROOT / "benchmarks/public_2026-11-17/qasmbench/grover_n2.qasm")
    rows = json.loads((ROOT / "results/grover_competition_2026-11-17/candidate_pool.json").read_text())
    return program, rows


def test_every_complete_source_plan_preserves_all_gates_and_full_tableau(development):
    program, rows = development
    want = logical_circuit(program).to_tableau()
    for row in rows:
        qasm, logical, trace = serialize(program, row["plan"])
        assert logical.to_tableau() == want
        assert Counter(trace) == Counter(range(18))
        assert qasm.count("h q[") == 10 and qasm.count("cx q[") == 2
        assert qasm.count("\nx q[") == 4 and qasm.count("measure q[") == 2


def test_all_signed_input_prefixes_are_explicit_validation_gates(development):
    program, rows = development
    for mask in range(4):
        qasm, circuit, trace = serialize(program, rows[0]["plan"], mask)
        assert len(trace) == 18 and qasm.count("\nx q[") == 4 + mask.bit_count()
        state = stim.TableauSimulator()
        state.do(circuit)
        assert all(state.peek_observable_expectation(stim.PauliString(p)) in (-1, 1) for p in ("ZI", "IZ"))


def test_reject_unsupported_gate_before_serialization(development):
    program, rows = development
    bad = deepcopy(program)
    bad["operations"][0]["name"] = "s"
    with pytest.raises(ValueError, match="dropped"):
        serialize(bad, rows[0]["plan"])


def test_record_affine_composition_keeps_permutation_and_signs():
    specs = [([0, 2], 1), ([1], 0)]
    got = combine_specs(specs, [1, 0], [(0, 1), (1,)], [1, 0])
    assert got == [([0, 1, 2], 0), ([0, 2], 1)]
    assert evaluate([1, 0, 0], got) == [1, 0]
    with pytest.raises(ValueError, match="trace"):
        combine_specs(specs, [0, 0])


def test_literal_record_map_exposes_fault_hidden_by_constant_p0_oracle():
    c = stim.Circuit("R 0 1\nTICK\nM 0 1\nOBSERVABLE_INCLUDE(0) rec[-1]")
    specs = [([0], 1), ([1], 1)]
    assert evaluate(c.reference_sample(), specs) == [1, 1]
    assert evaluate(final_record_fault(c, 0).reference_sample(), specs) == [0, 1]
    assert evaluate(final_record_fault(c, 1).reference_sample(), specs) == [1, 0]
    assert evaluate(c.reference_sample(), [([], 1), ([], 1)]) == [1, 1]


def test_basis_view_changes_only_observable_annotations():
    c = stim.Circuit("R 0 1\nM 0 1\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]")
    view = basis_view(c, [([0], 0), ([1], 0)])
    assert view.num_observables == 2
    assert [str(i) for i in c if i.name != "OBSERVABLE_INCLUDE"] == [str(i) for i in view if i.name != "OBSERVABLE_INCLUDE"]
    assert rank([1, 2]) == 2
    with pytest.raises(ValueError, match="incomplete"):
        basis_view(c, [([0], 0), ([0], 1)])


@pytest.mark.parametrize("mask", [-1, 4, True])
def test_invalid_signed_input_is_rejected(development, mask):
    program, rows = development
    with pytest.raises(ValueError, match="input"):
        serialize(program, rows[0]["plan"], mask)
