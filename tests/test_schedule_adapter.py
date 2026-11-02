import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import load_core
from lookahead import schedule, Config
from schedule_adapter import ProfileRouter, certify, lower, request_for, canonical_path
from route_adapter import UnsupportedSchedule
from validation import validate

ROOT = Path(__file__).resolve().parents[1]


def request():
    gates = [[0, 1], [2, 3], [1, 2]]
    base = load_core(ROOT.parent / "external/wisq")["sarouting"]
    router = ProfileRouter(base, 4)
    result = schedule(router, gates, router.architecture, list(router.mapping.items()), 1, Config("two_step", 48))
    return request_for(gates, result["steps"], 4)


def test_source_router_produces_certified_parallel_layers_and_memory():
    req = request()
    validate(req["gates"], req["architecture"], req["mapping"], req["steps"])
    circuit, certificate = lower(req, 8)
    assert certificate["layers"] == [[0, 1], [2]]
    assert certificate["all_live_memory_verified"]
    assert certificate["block_footprint_matches_backend"]
    assert certificate["num_ticks"] == circuit.num_ticks == 146
    assert certificate["mu"] == 0


def test_author_policy_adaptation_uses_same_reservations_without_mutating_base():
    base = load_core(ROOT.parent / "external/wisq")["sarouting"]
    before = base.try_order
    router = ProfileRouter(base, 4)
    result = router.author_search([[0, 1], [2, 3], [1, 2]], 3)
    assert certify(request_for([[0, 1], [2, 3], [1, 2]], result["steps"], 4))["source_step_count"] == 2
    assert base.try_order is before


@pytest.mark.parametrize("field,value", [
    ("distance", True), ("distance", 5), ("basis", "y"),
    ("ops", ["cx", "h", "cx"]), ("schema_id", "wrong"),
    ("timing", {"policy": "one_tick_per_step"}), ("steps", []),
])
def test_unsupported_request_fields_are_rejected(field, value):
    req = copy.deepcopy(request())
    req[field] = value
    with pytest.raises(UnsupportedSchedule):
        certify(req)


def test_unknown_hardware_and_boolean_mapping_are_rejected():
    req = request()
    req["architecture"]["disabled_vertices"] = [10]
    with pytest.raises(UnsupportedSchedule):
        certify(req)
    req = request()
    req["mapping"][0][0] = False
    with pytest.raises(UnsupportedSchedule):
        certify(req)


def test_gate_timing_is_indexed_by_original_ids_after_legal_reordering():
    req = request()
    mapping = dict(req["mapping"])
    width = req["architecture"]["width"]
    req["steps"] = [[[gid, req["gates"][gid], canonical_path(req["gates"][gid], mapping, width)]] for gid in [1, 0, 2]]
    certificate = certify(req)
    assert [entry["block_z"] for entry in certificate["gate_block_z"]] == [[3, 6], [0, 3], [6, 9]]


def test_pre_noise_fixture_selection_reproduces_positive_and_negative_cases():
    import json
    from select_schedule_fixtures import select
    base = load_core(ROOT.parent / "external/wisq")["sarouting"]
    stored = json.loads((ROOT / "benchmarks/schedule_pilot_2026-11-02.json").read_text())
    assert select(base) == stored
    assert stored["trials_visited"] == 35
