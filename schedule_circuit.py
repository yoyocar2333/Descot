"""Bounded CNOT schedules with explicit live memory and whole-template reservations.

TQEC supplies the lattice-surgery CNOT construction, graph composition and
physical compiler. This module extends the graph's two spatial arms and joins
complete layers, keeping every data patch alive between common boundaries.
It is a restricted synthesis profile, not a general surface-code compiler.
"""
from itertools import product

import numpy as np
from tqec import compile_block_graph
from tqec.computation.block_graph import BlockGraph
from tqec.computation.cube import ZXCube
from tqec.utils.position import Position3D
from tqec.utils.scale import LinearFunction

from surgery import TQEC_COMMIT
from three_qubit import change_input, final_flip, patch_data

PROFILE_ID = "diagonal_forward_cnot_layers_v1"


def logical_positions(qubits, span=1):
    if type(qubits) is not int or not 2 <= qubits <= 6:
        raise ValueError("This bounded profile supports 2..6 live logical qubits")
    if type(span) is not int or span not in (1, 3):
        raise ValueError("Use declared x spacing 1 or 3 blocks")
    return [(q * span, q) for q in range(qubits)]


def gate_footprint(control, target, positions):
    if any(type(q) is not int or not 0 <= q < len(positions) for q in (control, target)):
        raise ValueError("Invalid logical operand")
    cx, cy = positions[control]
    tx, ty = positions[target]
    if not (cx < tx and cy < ty):
        raise ValueError("Only forward CNOTs with control left/above target are supported")
    ancillas = [(cx, y) for y in range(cy + 1, ty + 1)]
    ancillas += [(x, ty) for x in range(cx + 1, tx)]
    if set(ancillas) & set(positions):
        raise ValueError("Bridge crosses a live data patch")
    return {"data": [positions[control], positions[target]], "ancillas": ancillas}


def validate_layers(gates, layers, qubits, span=1):
    positions = logical_positions(qubits, span)
    if not gates or any(type(g) not in (list, tuple) or len(g) != 2 for g in gates):
        raise ValueError("Provide a nonempty CNOT-only program")
    footprints = [gate_footprint(*gate, positions) for gate in gates]
    if not layers:
        raise ValueError("Provide nonempty execution layers")
    times = {}
    for time, layer in enumerate(layers):
        if type(layer) not in (list, tuple) or not layer:
            raise ValueError("Empty layers require a separate explicit memory policy")
        occupied = set()
        for gid in layer:
            if type(gid) is not int or not 0 <= gid < len(gates) or gid in times:
                raise ValueError("Invalid or duplicate gate ID")
            footprint = set(footprints[gid]["data"] + footprints[gid]["ancillas"])
            if occupied & footprint:
                raise ValueError("Concurrent CNOT templates overlap, including their ancillas")
            occupied.update(footprint)
            times[gid] = time
    if set(times) != set(range(len(gates))):
        raise ValueError("Every original gate must execute exactly once")
    previous = {}
    for gid, gate in enumerate(gates):
        for qubit in gate:
            if qubit in previous and times[previous[qubit]] >= times[gid]:
                raise ValueError("Per-qubit dependency order changed")
            previous[qubit] = gid
    return positions, footprints


def _layer_graph(positions, gates):
    graph = BlockGraph("CNOT layer with live spectator memory")
    controls = {c for c, _ in gates}
    for q, (x, y) in enumerate(positions):
        for z in range(4):
            kind = "P" if z in (0, 3) else "ZXX" if z == 1 and q in controls else "ZXZ"
            label = f"in_q{q}" if z == 0 else f"out_q{q}" if z == 3 else ""
            graph.add_cube(Position3D(x, y, z), kind, label)
        for z in range(3):
            graph.add_pipe(Position3D(x, y, z), Position3D(x, y, z + 1))
    for control, target in gates:
        cx, cy = positions[control]
        tx, ty = positions[target]
        previous = Position3D(cx, cy, 1)
        for y in range(cy + 1, ty + 1):
            current = Position3D(cx, y, 1)
            graph.add_cube(current, "ZXX")
            graph.add_pipe(previous, current)
            previous = current
        current = Position3D(cx, ty, 2)
        graph.add_cube(current, "ZXZ")
        graph.add_pipe(previous, current)
        previous = current
        for x in range(cx + 1, tx):
            current = Position3D(x, ty, 2)
            graph.add_cube(current, "ZXZ")
            graph.add_pipe(previous, current)
            previous = current
        graph.add_pipe(previous, Position3D(tx, ty, 2))
    graph.validate()
    return graph


def graph_schedule(gates, layers, qubits, basis="z", span=1):
    if basis not in ("x", "z"):
        raise ValueError("Use X/Z input and output bases")
    positions, footprints = validate_layers(gates, layers, qubits, span)
    graph = _layer_graph(positions, [gates[gid] for gid in layers[0]])
    for layer in layers[1:]:
        graph = graph.compose(_layer_graph(positions, [gates[gid] for gid in layer]), "out_q0", "in_q0")
    labels = [f"{side}_q{q}" for side in ("in", "out") for q in range(qubits)]
    ports = [graph.ports[label] for label in labels]
    expected = [Position3D(x, y, z) for z in (0, 3 * len(layers)) for x, y in positions]
    if ports != expected:
        raise AssertionError("All logical states must have a common lifetime")
    graph.fill_ports(ZXCube.from_str("ZXX" if basis == "x" else "ZXZ"))
    graph.validate()
    return graph, ports, positions, footprints


def component_correlation_surfaces(graph):
    """Keep a complete observable basis for independent graph components.

    The pinned upstream finder forms Cartesian products between disconnected
    component generators. Those products need not span each component's
    individual logical faults. Find generators per connected component and
    pass their union to the physical compiler instead.
    """
    neighbours = {cube.position: set() for cube in graph.cubes}
    for pipe in graph.pipes:
        neighbours[pipe.u.position].add(pipe.v.position)
        neighbours[pipe.v.position].add(pipe.u.position)
    unseen = set(neighbours)
    surfaces = []
    while unseen:
        component = set()
        pending = [min(unseen)]
        while pending:
            position = pending.pop()
            if position in component:
                continue
            component.add(position)
            pending.extend(neighbours[position] - component)
        unseen -= component
        subgraph = BlockGraph("Observable component")
        for cube in graph.cubes:
            if cube.position in component:
                subgraph.add_cube(cube.position, cube.kind, cube.label)
        for pipe in graph.pipes:
            if pipe.u.position in component:
                subgraph.add_pipe(pipe.u.position, pipe.v.position, pipe.kind)
        surfaces.extend(subgraph.find_correlation_surfaces())
    return surfaces


def generate_schedule(gates, layers, qubits, basis="z", span=1):
    graph, ports, positions, footprints = graph_schedule(gates, layers, qubits, basis, span)
    surfaces = component_correlation_surfaces(graph)
    compiled = compile_block_graph(graph, observables=surfaces, block_temporal_height=LinearFunction(2, -1))
    circuit = compiled.generate_stim_circuit(k=1, database_path=None)
    metadata = {
        "profile_id": PROFILE_ID, "basis": basis, "distance": 3,
        "logical_gates": [list(g) for g in gates], "layers": [list(s) for s in layers],
        "logical_qubits": qubits, "logical_block_xy": [list(p) for p in positions],
        "x_spacing_blocks": span, "input_z": 0, "output_z": 3 * len(layers),
        "external_flows": [surface.external_stabilizer(ports) for surface in surfaces],
        "gate_footprints": footprints, "num_qubits": circuit.num_qubits,
        "num_ticks": circuit.num_ticks, "num_observables": circuit.num_observables,
        "num_detectors": circuit.num_detectors, "tqec_commit": TQEC_COMMIT,
        "scope": "Restricted full CNOT schedule with common lifetime and protected spectator memory; not arbitrary routes or process fidelity.",
    }
    return circuit, metadata


def basis_action(gates, basis, bits):
    result = list(bits)
    for control, target in gates:
        if basis == "z":
            result[target] ^= result[control]
        elif basis == "x":
            result[control] ^= result[target]
        else:
            raise ValueError("Use X/Z")
    return result


def _rank(rows, width):
    rows = [sum(int(v) << i for i, v in enumerate(row)) for row in rows]
    rank = 0
    for bit in range(width):
        pivot = next((i for i in range(rank, len(rows)) if rows[i] & (1 << bit)), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i] & (1 << bit):
                rows[i] ^= rows[rank]
        rank += 1
    return rank


def validate_schedule(circuit, metadata, shots=32):
    n = metadata["logical_qubits"]
    flows, basis = metadata["external_flows"], metadata["basis"]
    if len(flows) != n or circuit.num_observables != n:
        raise AssertionError("Expected one complete independent correlation basis")
    if any(len(f) != 2 * n or not set(f) <= {basis.upper(), "I"} for f in flows):
        raise AssertionError("Unexpected external flow")
    if _rank([[p != "I" for p in f[:n]] for f in flows], n) != n:
        raise AssertionError("Input observable basis is incomplete")
    if _rank([[p != "I" for p in f[n:]] for f in flows], n) != n:
        raise AssertionError("Output observable basis is incomplete")
    converter = circuit.compile_m2d_converter()
    signed = []
    for bits in product((0, 1), repeat=n):
        outputs = basis_action(metadata["logical_gates"], basis, bits)
        for flow in flows:
            if sum(bit for bit, p in zip([*bits, *outputs], flow) if p != "I") % 2:
                raise AssertionError("Flow differs from the complete intended logical program")
        raw = change_input(circuit, metadata, bits).compile_sampler(seed=123).sample(shots)
        detectors, observables = converter.convert(measurements=raw, separate_observables=True)
        expected = np.array([sum(bit for bit, p in zip(bits, f[:n]) if p != "I") % 2 for f in flows], dtype=bool)
        if np.any(detectors) or not np.all(observables == expected):
            raise AssertionError("Signed-input check failed")
        signed.append({"input_signs": list(bits), "output_signs": outputs, "observable_parities": expected.astype(int).tolist(), "shots": shots})
    faults = []
    for q in range(n):
        detectors, observables = final_flip(circuit, metadata, q).compile_detector_sampler(seed=123).sample(shots, separate_observables=True)
        expected = np.array([f[n + q] != "I" for f in flows], dtype=bool)
        if np.any(detectors) or not np.all(observables == expected) or not np.any(expected):
            raise AssertionError("Final logical fault check failed")
        faults.append({"logical_qubit": q, "observable_flips": expected.astype(int).tolist(), "shots": shots})
    for q in range(n):
        patch_data(circuit, metadata, q)
    return {"all_signed_inputs_passed": True, "signed_inputs": signed,
            "final_logical_faults": faults, "common_lifetime_block_z": [0, metadata["output_z"]]}
