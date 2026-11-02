import copy
from functools import lru_cache
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from schedule_circuit import generate_schedule, graph_schedule, validate_layers, validate_schedule, _rank
from surgery import add_noise
from tqec.utils.position import Position3D


@lru_cache
def compiled(basis="z", kind="parallel", span=1):
    layers = [[0, 1], [2]] if kind == "parallel" else [[0], [1], [2]]
    return generate_schedule([[0, 1], [2, 3], [1, 2]], layers, 4, basis, span)


@pytest.mark.parametrize("basis", ["x", "z"])
@pytest.mark.parametrize("kind", ["parallel", "serial"])
def test_parallel_and_serial_preserve_all_inputs_final_faults_and_distance(basis, kind):
    circuit, metadata = compiled(basis, kind)
    result = validate_schedule(circuit, metadata, 8)
    assert len(result["signed_inputs"]) == 16
    assert len(result["final_logical_faults"]) == 4
    assert len(add_noise(circuit, .001).shortest_graphlike_error()) == 3


@pytest.mark.parametrize("basis", ["x", "z"])
def test_disconnected_parallel_components_keep_individual_observables(basis):
    circuit, metadata = generate_schedule([[0, 1], [2, 3]], [[0, 1]], 4, basis)
    assert _rank([[p != "I" for p in f[:4]] for f in metadata["external_flows"]], 4) == 4
    assert validate_schedule(circuit, metadata, 8)["all_signed_inputs_passed"]


@pytest.mark.parametrize("basis", ["x", "z"])
def test_stretched_vertical_arm_with_never_active_spectator(basis):
    circuit, metadata = generate_schedule([[0, 2]], [[0]], 3, basis)
    assert validate_schedule(circuit, metadata, 8)["all_signed_inputs_passed"]
    assert len(add_noise(circuit, .001).shortest_graphlike_error()) == 3


def test_long_spatial_spacing_and_common_continuous_lifetime():
    circuit, metadata = compiled("z", "parallel", 3)
    assert validate_schedule(circuit, metadata, 8)["all_signed_inputs_passed"]
    assert len(add_noise(circuit, .001).shortest_graphlike_error()) == 3
    graph, ports, positions, _ = graph_schedule([[0, 1], [2, 3], [1, 2]], [[0, 1], [2]], 4, "z", 3)
    assert [p.z for p in ports] == [0] * 4 + [6] * 4
    for x, y in positions:
        for z in range(6):
            assert graph.has_pipe_between(Position3D(x, y, z), Position3D(x, y, z + 1))


def test_redundant_basis_is_rejected_instead_of_silently_losing_faults():
    circuit, metadata = compiled()
    bad = copy.deepcopy(metadata)
    bad["external_flows"][1] = bad["external_flows"][0]
    with pytest.raises(AssertionError, match="incomplete"):
        validate_schedule(circuit, bad, 8)


@pytest.mark.parametrize("gates,layers,n", [
    ([[0, 2], [1, 3]], [[0, 1]], 4),
    ([[0, 1], [1, 2]], [[1], [0]], 3),
    ([[0, 1], [1, 2]], [[0], [0]], 3),
    ([[0, 1]], [[], [0]], 2),
    ([[1, 0]], [[0]], 2),
    ([[False, 1]], [[0]], 2),
])
def test_unsupported_physical_schedules_fail_closed(gates, layers, n):
    with pytest.raises(ValueError):
        validate_layers(gates, layers, n)
