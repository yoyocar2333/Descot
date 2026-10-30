"""Certified local stopping, counters, and a controlled RNG protocol.

The upstream source files remain unchanged. All runtime hooks restore on exit.
"""
from contextlib import contextmanager
import hashlib
import random
import time
import numpy as np


class _Saturated(Exception):
    def __init__(self, step):
        self.step = step


@contextmanager
def routing_hooks(router, method, seed):
    original_best = router.best_realizable_set_found
    original_try = router.try_order
    original_gate = router.route_gate
    stats = {"front_calls": 0, "order_evaluations": 0, "gate_route_calls": 0,
             "order_evaluation_seconds": 0.0, "saturation_stops": 0,
             "full_fronts": 0, "front_records": []}
    active = {"stop": False}

    def counted_gate(*args, **kwargs):
        stats["gate_route_calls"] += 1
        return original_gate(*args, **kwargs)

    def counted_try(*args, **kwargs):
        start = time.perf_counter()
        step = original_try(*args, **kwargs)
        stats["order_evaluation_seconds"] += time.perf_counter() - start
        stats["order_evaluations"] += 1
        executable = args[1] if len(args) > 1 else kwargs["executable"]
        if active["stop"] and len(step) == len(executable):
            raise _Saturated(step)
        return step

    def select(*args, **kwargs):
        gates, front, arch, mapping = args[:4]
        # The stock driver rebuilds a remaining-gate dictionary after every step.
        # Seed from its ordered remaining IDs, rather than a call index, so both
        # methods get identical RNG streams whenever they reach the same state.
        key = f"{seed}:" + ",".join(map(str, gates.keys()))
        state_seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big")
        random.seed(state_seed)
        np.random.seed(state_seed)
        before = stats["order_evaluations"]
        began = time.perf_counter()
        stats["front_calls"] += 1
        crit = kwargs.get("crit_dict", args[6] if len(args) > 6 else {})
        reward = kwargs.get("reward_name", args[5] if len(args) > 5 else None)
        active["stop"] = method == "saturation" and reward == "criticality" and all(crit.get(i, 0) > 0 for i in front)
        stopped = False
        try:
            try:
                step, tried = original_best(*args, **kwargs)
            except _Saturated as result:
                step = result.step
                tried = stats["order_evaluations"] - before
                stats["saturation_stops"] += 1
                stopped = True
        finally:
            active["stop"] = False
        if len(step) == len(front):
            stats["full_fronts"] += 1
        if not step:
            raise RuntimeError("No routing progress: architecture or mapping is infeasible")
        stats["front_records"].append({"ready": len(front), "cnots": sum(len(g) == 2 for g in front.values()),
            "t_gates": sum(len(g) == 1 for g in front.values()), "routed": len(step),
            "orders": stats["order_evaluations"] - before, "saturation_stop": stopped,
            "seconds": time.perf_counter() - began,
            "regime": "single" if len(front) < 2 else "enumeration" if sum(len(g) == 2 for g in front.values()) < 5 and sum(len(g) == 1 for g in front.values()) < 5 and kwargs.get("cooling_rate", .1) != 1 else "annealing"})
        return step, tried

    router.route_gate = counted_gate
    router.try_order = counted_try
    router.best_realizable_set_found = select
    try:
        yield stats
    finally:
        router.route_gate = original_gate
        router.try_order = original_try
        router.best_realizable_set_found = original_best
