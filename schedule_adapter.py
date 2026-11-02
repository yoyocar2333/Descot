"""Source routing and strict lowering for the bounded forward-CNOT profile."""
import copy
import hashlib
from types import FunctionType

from route_adapter import UnsupportedSchedule, sha256_json
from schedule_circuit import (
    PROFILE_ID, generate_schedule, graph_schedule, gate_footprint,
    logical_positions, validate_layers, validate_schedule,
)
from validation import validate

SCHEMA = "dascot_forward_layer_request_v1"
TIMING = "three_block_z_per_source_step_v1"


def profile_architecture(qubits, span=1):
    positions = logical_positions(qubits, span)
    width, height = 2 * positions[-1][0] + 3, 2 * positions[-1][1] + 3
    mapping = [[q, (1 + 2 * x) + width * (1 + 2 * y)] for q, (x, y) in enumerate(positions)]
    return {"width": width, "height": height,
            "alg_qubits": [v for _, v in mapping], "magic_states": []}, mapping


def canonical_path(gate, mapping, width):
    control, target = [mapping[q] for q in gate]
    cx, cy = control % width, control // width
    tx, ty = target % width, target // width
    return [y * width + cx for y in range(cy + 1, ty + 1)] + [ty * width + x for x in range(cx + 1, tx)]


class ProfileRouter:
    """Use a common conservative physical reservation primitive for all methods.

    The source centreline is validated in the ordinary abstract model. The
    entire data/ancilla block footprint is additionally reserved for the full
    layer, including ancillas that are used at only one template sub-phase.
    """
    def __init__(self, base_router, qubits, span=1):
        self.positions = logical_positions(qubits, span)
        self.architecture, pairs = profile_architecture(qubits, span)
        self.mapping = dict(pairs)
        self.base_router = base_router
        self.build_crit_dict_fast = base_router.build_crit_dict_fast

    @staticmethod
    def initialize_to_remove(magic_states, mapping):
        return set(mapping.values()) | set(magic_states)

    def _check(self, width, height, magic_states, mapping):
        if width != self.architecture["width"] or height != self.architecture["height"] or magic_states or mapping != self.mapping:
            raise ValueError("Router architecture/mapping differs from the declared physical profile")

    def route_gate(self, indexed_gate, width, height, magic_states, mapping, blocked, take_first_ms):
        self._check(width, height, magic_states, mapping)
        gid, gate = indexed_gate
        if len(gate) != 2:
            raise ValueError("This profile routes CNOTs only")
        footprint = gate_footprint(*gate, self.positions)
        resources = set(footprint["data"] + footprint["ancillas"])
        path = canonical_path(gate, mapping, width)
        if resources & blocked or set(path) & blocked:
            return [], blocked
        blocked.update(resources)
        blocked.update(path)
        return [(gid, gate, path)], blocked

    def try_order(self, order, front, width, height, magic_states, mapping, take_first_ms):
        blocked = self.initialize_to_remove(magic_states, mapping)
        step = []
        items = list(front.items())
        for i in order:
            route, blocked = self.route_gate(items[i], width, height, magic_states, mapping, blocked, take_first_ms)
            step.extend(route)
        return step

    def author_search(self, gates, seed):
        """Pinned author's search policy with the same new reservation primitive.

        This is explicitly a constrained adaptation, not the unmodified author
        router. Function globals are copied instead of monkey-patching upstream.
        """
        import random
        import numpy as np
        base = self.base_router
        namespace = dict(vars(base))
        namespace["try_order"] = self.try_order
        namespace["route_gate"] = self.route_gate
        namespace["shortest_path"] = lambda gate, mapping, width, height, ms: len(canonical_path(gate, mapping, width))
        for name in ("best_realizable_set_found", "sim_anneal_route"):
            function = getattr(base, name)
            namespace[name] = FunctionType(function.__code__, namespace, function.__name__, function.__defaults__, function.__closure__)
        random_state, numpy_state = random.getstate(), np.random.get_state()
        try:
            random.seed(seed)
            np.random.seed(seed)
            steps, tried, interrupted = namespace["sim_anneal_route"](
                gates, self.architecture, list(self.mapping.items()),
                temperature=10, cooling_rate=.1, termination_temp=.1,
                order_fraction=1, timeout=30, initial_order="random",
                reward_name="criticality", take_first_ms=False)
        finally:
            random.setstate(random_state)
            np.random.set_state(numpy_state)
        if interrupted:
            raise TimeoutError("Author search did not finish")
        return {"steps": steps, "time_steps": len(steps), "orders_tried": tried,
                "seed": seed, "method": "author_search_with_profile_reservations",
                "scope": "Pinned author search with our conservative physical routing primitive; not the unmodified DASCOT baseline."}


def request_for(gates, steps, qubits, basis="z", span=1):
    architecture, mapping = profile_architecture(qubits, span)
    return {"schema_id": SCHEMA, "gates": copy.deepcopy(gates),
            "ops": ["cx"] * len(gates), "architecture": architecture,
            "mapping": mapping, "steps": copy.deepcopy(steps), "basis": basis,
            "distance": 3, "timing": {"policy": TIMING}}


def certify(request):
    fields = {"schema_id", "gates", "ops", "architecture", "mapping", "steps", "basis", "distance", "timing"}
    def reject(code, message):
        raise UnsupportedSchedule(code, message)
    if type(request) is not dict or set(request) != fields or request["schema_id"] != SCHEMA:
        reject("schema", "Use the exact forward-layer request schema")
    if request["basis"] not in ("x", "z") or type(request["distance"]) is not int or request["distance"] != 3:
        reject("qec_conditions", "Only X/Z and d=3 are supported")
    if request["timing"] != {"policy": TIMING}:
        reject("timing", "Declare three physical block-z per source layer; steps are not TICKs")
    gates, mapping, steps = request["gates"], request["mapping"], request["steps"]
    if type(gates) is not list or not gates or request["ops"] != ["cx"] * len(gates):
        reject("program", "Provide a nonempty CNOT-only program")
    if type(mapping) is not list or any(type(pair) not in (list, tuple) or len(pair) != 2 or any(type(v) is not int for v in pair) for pair in mapping):
        reject("mapping", "Provide the complete declared mapping")
    n = len(mapping)
    try:
        matches = [span for span in (1, 3) if (request["architecture"], mapping) == profile_architecture(n, span)]
    except (ValueError, TypeError):
        matches = []
    if len(matches) != 1:
        reject("geometry", "Architecture and mapping must match one declared profile; hardware extras are not ignored")
    span = matches[0]
    if type(steps) is not list or not steps:
        reject("schedule", "Provide source route records for every nonempty layer")
    layers = []
    try:
        for step in steps:
            if type(step) is not list or not step:
                raise ValueError("Each step must be a nonempty list")
            layer = []
            for item in step:
                if type(item) not in (tuple, list) or len(item) != 3:
                    raise ValueError("Use gate ID / operands / path records")
                gid, args, path = item
                if type(gid) is not int or not 0 <= gid < len(gates):
                    raise ValueError("Invalid gate ID")
                if type(args) not in (tuple, list) or list(args) != list(gates[gid]) or any(type(q) is not int for q in args):
                    raise ValueError("Gate operands differ")
                if type(path) not in (tuple, list) or any(type(v) is not int for v in path):
                    raise ValueError("Path vertices must be integers")
                if list(path) != canonical_path(args, dict(mapping), request["architecture"]["width"]):
                    reject("corridor", "Only the declared canonical L corridor is supported")
                layer.append(gid)
            layers.append(layer)
        positions, footprints = validate_layers(gates, layers, n, span)
        source_validation = validate(gates, request["architecture"], mapping, steps)
    except UnsupportedSchedule:
        raise
    except (ValueError, TypeError, IndexError, KeyError) as error:
        reject("schedule", str(error))
    lifetimes = []
    for q in range(n):
        active = [t for t, layer in enumerate(layers) if any(q in gates[gid] for gid in layer)]
        lifetimes.append({"logical_qubit": q, "lifetime_block_z": [0, 3 * len(layers)],
                          "active_layers": active, "memory_layers": [t for t in range(len(layers)) if t not in active]})
    return {"profile_id": PROFILE_ID, "request_sha256": sha256_json(request),
            "source_validation": source_validation, "basis": request["basis"], "distance": 3,
            "logical_qubits": n, "x_spacing_blocks": span, "layers": layers,
            "logical_block_xy": positions, "gate_footprints": footprints,
            "gate_block_z": sorted([{"gate_id": gid, "source_layer": t, "block_z": [3 * t, 3 * (t + 1)]} for t, layer in enumerate(layers) for gid in layer], key=lambda row: row["gate_id"]),
            "timing_policy": TIMING, "source_step_count": len(layers),
            "all_live_qubits_block_z": [0, 3 * len(layers)], "lifetimes": lifetimes,
            "conservative_ancilla_reservation_block_z": 3 * sum(len(f["ancillas"]) for f in footprints),
            "data_reservation_block_z": n * 3 * len(layers), "mu": 0,
            "scope": "Restricted layer synthesis with full footprint reservations; not arbitrary route support or algorithm-performance evidence."}


def lower(request, validation_shots=32):
    certificate = certify(request)
    args = (request["gates"], certificate["layers"], certificate["logical_qubits"], request["basis"], certificate["x_spacing_blocks"])
    graph, ports, positions, footprints = graph_schedule(*args)
    occupied = {(cube.position.x, cube.position.y) for cube in graph.cubes}
    declared = set(positions)
    for footprint in footprints:
        declared.update(footprint["ancillas"])
    if occupied != declared:
        raise AssertionError("Declared footprint differs from physical backend")
    for x, y in positions:
        from tqec.utils.position import Position3D
        for z in range(certificate["all_live_qubits_block_z"][1]):
            if not graph.has_pipe_between(Position3D(x, y, z), Position3D(x, y, z + 1)):
                raise AssertionError("A live data patch is missing memory")
    circuit, metadata = generate_schedule(*args)
    certificate["physical_validation"] = validate_schedule(circuit, metadata, validation_shots)
    certificate["occupied_block_xy"] = sorted(occupied)
    certificate["block_footprint_matches_backend"] = True
    certificate["all_live_memory_verified"] = True
    certificate["backend_meta"] = metadata
    certificate["ideal_circuit_sha256"] = hashlib.sha256(str(circuit).encode()).hexdigest()
    certificate["num_qubits"] = circuit.num_qubits
    certificate["num_ticks"] = circuit.num_ticks
    return circuit, certificate
