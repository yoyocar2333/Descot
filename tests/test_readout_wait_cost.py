import json
from copy import deepcopy

import pytest
import stim

from readout_wait_cost import METRICS, exact_score, select, wait_cost
from run_grover_competition import ROOT, source_program


@pytest.fixture(scope="module")
def development():
    _, program = source_program()
    rows = json.loads((ROOT / "results/grover_competition_2026-11-17/candidate_pool.json").read_text())
    costs = {r["candidate_id"]: wait_cost(program, r["plan"], ["ZI", "IZ"]) for r in rows}
    return program, rows, costs


def test_full_development_pool_has_no_minimum_depth_proxy_contrast(development):
    _, rows, costs = development
    minima = [r for r in rows if r["features"]["physical_layers"] == 9]
    assert len(rows) == 175 and len(minima) == 12
    assert {exact_score(costs[r["candidate_id"]]) for r in minima} == {10}
    assert {r["features"]["squared_protected_idle_block_z2"] for r in minima} == {36, 54}
    assert all(costs[r["candidate_id"]]["total_protected_idle_block_z"] ==
               r["features"]["total_protected_idle_block_z"] for r in rows)


def test_all_idle_fault_signatures_match_complete_exact_source_execution(development):
    # Independent full execution with one inserted fault, no propagation shortcut
    # and no sampled shots. Grover has a deterministic complete terminal output.
    program, rows, costs = development
    comparisons = 0
    for row in rows:
        if row["features"]["physical_layers"] != 9:
            continue
        for idle in costs[row["candidate_id"]]["idle_layers"]:
            for event in idle["pauli_events"]:
                state = stim.TableauSimulator()
                for index, layer in enumerate(row["plan"]["layers"]):
                    for i in layer["operation_ids"]:
                        op = program["operations"][i]
                        if op["name"] in ("x", "h", "cx"):
                            c = stim.Circuit()
                            c.append(op["name"].upper(), op["qubits"])
                            state.do(c)
                    if index == idle["plan_layer_index"]:
                        c = stim.Circuit()
                        c.append(event["pauli"], [idle["qubit"]])
                        state.do(c)
                # Ideal full Grover output is |11>; a fault flips sign to +1.
                expected = [state.peek_observable_expectation(stim.PauliString(p)) == 1
                            for p in ("ZI", "IZ")]
                assert event["signature"] == expected
                comparisons += 1
    assert comparisons == 144


def test_equivalent_complete_basis_preserves_every_joint_idle_event(development):
    program, rows, costs = development
    for row in rows:
        changed = wait_cost(program, row["plan"], ["ZZ", "IZ"])
        original = costs[row["candidate_id"]]
        assert exact_score(changed) == exact_score(original)
        assert [e["visible_any"] for g in changed["idle_layers"] for e in g["pauli_events"]] == [
            e["visible_any"] for g in original["idle_layers"] for e in g["pauli_events"]]


@pytest.mark.parametrize("basis", [["ZZ"], ["XI", "IX"], ["ZI", "ZI"]])
def test_reject_incomplete_or_wrong_output_space(development, basis):
    program, rows, _ = development
    with pytest.raises(ValueError):
        wait_cost(program, rows[0]["plan"], basis)


def test_shared_budget_ties_and_ablations_do_not_remove_candidates(development):
    _, rows, costs = development
    qualified = [r["candidate_id"] for r in rows if r["features"]["physical_layers"] == 9]
    selected = {m: select(rows, costs, qualified, "g174", m, 175) for m in METRICS}
    assert len({s["pool_sha256"] for s in selected.values()}) == 1
    assert all(s["pool_size"] == 175 and s["shortlist_size"] == 12 for s in selected.values())
    assert selected["raw_readout_wait"]["candidate_id"] == "g174"
    assert len(selected["raw_readout_wait"]["tied_optima"]) == 12
    assert selected["total_wait"]["candidate_id"] == selected["no_position"]["candidate_id"] == "g174"
    assert len(selected["segmented_wait_squared"]["tied_optima"]) == 4
    with pytest.raises(ValueError, match="budget"):
        select(rows, costs, qualified, "g174", "depth", 174)
    with pytest.raises(ValueError, match="qualification"):
        select(rows, costs, qualified[1:], "g174", "depth", 175)
    with pytest.raises(ValueError, match="cost"):
        select(rows, {k: v for k, v in costs.items() if k != "g000"}, qualified, "g174", "depth", 175)


def test_unsupported_source_gate_is_rejected_before_suffix_propagation(development):
    program, rows, _ = development
    changed = deepcopy(program)
    next(o for o in changed["operations"] if o["name"] == "x")["name"] = "s"
    with pytest.raises(ValueError, match="Unsupported"):
        wait_cost(changed, rows[0]["plan"], ["ZI", "IZ"])
