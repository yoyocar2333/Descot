"""Independent checks of the paper's abstract routing model."""


def validate(gates, arch, mapping, steps):
    width, height = arch["width"], arch["height"]
    nvertices = width * height
    mapping = dict(mapping)
    used_qubits = {q for gate in gates for q in gate}
    if set(mapping) != used_qubits or len(set(mapping.values())) != len(mapping):
        raise ValueError("Mapping is incomplete or not injective")
    if not set(mapping.values()) <= set(arch["alg_qubits"]):
        raise ValueError("Mapping uses a non-data location")
    if set(mapping.values()) & set(arch["magic_states"]):
        raise ValueError("Mapping overlaps magic states")

    def vertical(v):
        row = v // width
        return {u for u in [v - width, v + width] if 0 <= u < nvertices and abs(u // width - row) == 1}

    def horizontal(v):
        return {u for u in [v - 1, v + 1] if 0 <= u < nvertices and u // width == v // width}

    ids, time_of, recovered = [], {}, []
    blocked = set(mapping.values()) | set(arch["magic_states"])
    for t, step in enumerate(steps):
        if not step:
            raise ValueError("Empty time step")
        occupied, operands = set(), set()
        for gid, args, path in step:
            if not 0 <= gid < len(gates) or tuple(args) != tuple(gates[gid]):
                raise ValueError("Gate ID or operands differ")
            if gid in time_of:
                raise ValueError("Duplicate gate ID")
            if operands & set(args):
                raise ValueError("Shared qubit in a time step")
            operands.update(args)
            if not path or len(set(path)) != len(path):
                raise ValueError("Path is empty or not simple")
            if any(not isinstance(v, int) or not 0 <= v < nvertices for v in path):
                raise ValueError("Path vertex outside architecture")
            if blocked & set(path):
                raise ValueError("Path traverses data or magic-state patches")
            if occupied & set(path):
                raise ValueError("Overlapping routes")
            occupied.update(path)
            for a, b in zip(path, path[1:]):
                if abs(a // width - b // width) + abs(a % width - b % width) != 1:
                    raise ValueError("Path contains a non-grid edge")
            if path[0] not in vertical(mapping[args[0]]):
                raise ValueError("Wrong control boundary")
            endpoints = horizontal(mapping[args[1]]) if len(args) == 2 else set().union(*(horizontal(m) for m in arch["magic_states"]))
            if path[-1] not in endpoints:
                raise ValueError("Wrong target or magic-state boundary")
            ids.append(gid)
            recovered.append(gid)
            time_of[gid] = t
    if sorted(ids) != list(range(len(gates))):
        raise ValueError("Gate IDs do not appear exactly once")
    last = {}
    for gid, gate in enumerate(gates):
        for q in gate:
            if q in last and time_of[last[q]] >= time_of[gid]:
                raise ValueError("Dependency order differs")
            last[q] = gid
    return {"valid": True, "gate_count": len(ids), "time_steps": len(steps),
            "checks": ["gate_identity", "mapping", "per_qubit_dependencies", "path_connectivity",
                       "boundary_orientation", "vertex_disjointness", "data_preservation"],
            "scope": "Abstract CNOT/T/TDG routing program. No physical QEC or noise simulation."}
