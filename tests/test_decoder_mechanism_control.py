import shutil

import pytest
import stim

from decoder_mechanism_control import (FrozenCircuitDEM, VENDOR, diagnose,
                                       load_author, mechanisms)


def test_original_author_and_chunk_trace_agree_on_complete_two_bit_residuals():
    dem = stim.DetectorErrorModel("""error(0.1) D0 L0
error(0.05) D1 L1
error(0.001) D0 D1 L0 L1
""")
    a, raw, _ = diagnose(dem, chunk=1)
    b, other, _ = diagnose(dem, chunk=1024)
    assert a == b and raw == other
    assert a["mechanisms"] == 3 and a["decoded_any_mismatch_mechanisms"] == 0
    assert {r[1] for r in raw} == {1, 2, 3}
    assert a["num_observables"] == 2 and a["counts"] is None and a["shots"] == 0


def test_uncorrectable_single_is_recorded_without_rejecting_input():
    # No detector evidence can repair this observable-only mechanism.
    dem = stim.DetectorErrorModel("error(0.01) L0\nlogical_observable L1")
    result, raw, _ = diagnose(dem)
    assert result["decoded_any_mismatch_mechanisms"] == 1
    assert result["decoded_mismatch_mechanisms_per_observable"] == [1, 0]
    assert raw == [[0, 1, 0, 1]]


def test_correlated_separator_components_are_one_xor_mechanism():
    dem = stim.DetectorErrorModel("""repeat 2 {
error(0.01) D0 L0 ^ D1 L1 ^ D0 L0
shift_detectors 2
}
error(0.02) L0
""")
    assert list(mechanisms(dem)) == [([1], [1]), ([3], [1]), ([], [0])]


def test_frozen_dem_adapter_matches_original_circuit_api_without_sampling():
    circuit = stim.Circuit("R 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]")
    dem = circuit.detector_error_model(decompose_errors=True)
    original, _ = load_author()
    direct = original(circuit)
    cached = original(FrozenCircuitDEM(dem))
    assert direct[1:] == cached[1:] == (0, 1)


@pytest.mark.parametrize("dem", ["detector D0", "logical_observable L0"])
def test_empty_or_zero_output_is_not_a_clean_diagnostic(dem):
    with pytest.raises(ValueError):
        diagnose(stim.DetectorErrorModel(dem))


def test_modified_author_bytes_fail_before_execution(tmp_path):
    copy = tmp_path / "circls"
    shutil.copytree(VENDOR, copy)
    path = copy / "experiments/formula_deviation.py"
    path.write_text(path.read_text() + "\n# changed\n")
    with pytest.raises(ValueError, match="original"):
        load_author(copy)


def test_invalid_chunk_budget_is_rejected():
    with pytest.raises(ValueError, match="chunk"):
        diagnose(stim.DetectorErrorModel("error(0.01) D0 L0"), chunk=0)
