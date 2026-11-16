import itertools

import pytest
import stim

from probe_readout_basis import build_probe
from readout_visibility import fault_signature, raw_visibility, validate_basis


def test_equivalent_bases_preserve_joint_event_but_reverse_marginal_ranking():
    probe = build_probe()
    assert probe["basis_invariance"]["failures"] == 0
    assert probe["decoder_counterexample"]["residual_any_error"] == 0


def test_raw_signature_matches_exact_state_expectations_after_clifford_suffix():
    # Deterministic tableau oracle; no noisy or ideal shots are sampled.
    preparation = stim.Circuit("H 0\nCX 0 1\nH 2\nCX 1 2")
    observables = [stim.PauliString(p).after(preparation) for p in ["ZII", "IZI", "IIZ"]]
    for chars in itertools.product("IXYZ", repeat=3):
        fault = stim.PauliString("".join(chars))
        state = stim.TableauSimulator()
        state.do(preparation)
        state.do_pauli_string(fault)
        expected = tuple(state.peek_observable_expectation(p) == -1 for p in observables)
        assert fault_signature(fault, observables) == expected


@pytest.mark.parametrize("basis", [["ZI", "XZ"], ["ZI", "ZI"], ["II"], [], ["Z", "ZZ"], ["iZ"]])
def test_reject_invalid_readout_space(basis):
    with pytest.raises(ValueError):
        validate_basis(basis)


def test_validate_width_weights_and_fault_cancellation_boundary():
    with pytest.raises(ValueError):
        fault_signature("X", ["ZZ"])
    for weight in [-1, float("nan"), float("inf")]:
        with pytest.raises(ValueError):
            raw_visibility([("XI", weight)], ["ZI", "IZ"])
    # Two simultaneous X faults cancel: first-order sums are not exact rates.
    assert fault_signature(stim.PauliString("XI") * stim.PauliString("XI"), ["ZI", "IZ"]) == (False, False)
    assert raw_visibility([("XI", 0.01), ("XI", 0.01)], ["ZI", "IZ"])["joint_first_order_weight"] == 0.02
