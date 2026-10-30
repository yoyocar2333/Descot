"""Budgeted routing lookahead over the pinned author's route primitive.

No QEC risk is invented: this first scheduler uses two-step dependency
progress, with reference-path conflict used only to break integer ties.
"""
from dataclasses import dataclass, asdict
import hashlib
import itertools
import math
import random
import time


@dataclass(frozen=True)
class Config:
    mode: str = "two_step_conflict"
    budget: int = 48
    candidate_cap: int | None = None
    conflict_weight: float = .25

    def __post_init__(self):
        if self.mode not in ["one_step", "two_step", "two_step_conflict", "random"]:
            raise ValueError("Unknown mode")
        cost = 1 + (self.mode.startswith("two_step")) + (self.mode == "two_step_conflict")
        if self.budget < cost or not 0 <= self.conflict_weight < 1:
            raise ValueError("Insufficient budget or non-tie-breaking conflict weight")
        if self.candidate_cap is not None and self.candidate_cap < 1:
            raise ValueError("candidate_cap must be positive")


def state_seed(root_seed, remaining):
    key = f"{root_seed}:" + ",".join(map(str, remaining))
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")


def ready_front(remaining):
    """Preserve every per-qubit precedence relation in original gate order."""
    blocked, front = set(), {}
    for gid, gate in remaining.items():
        if not blocked.intersection(gate):
            front[gid] = gate
        blocked.update(gate)
    return front


def advance(remaining, step):
    done = {g[0] for g in step}
    return {gid: gate for gid, gate in remaining.items() if gid not in done}


def candidate_orders(front, criticalities, mapping, width, count, seed):
    ids = list(front)
    m = len(ids)
    if not m:
        return []
    rng = random.Random(seed)
    canonical = tuple(sorted(range(m), key=lambda i: (-criticalities[ids[i]], ids[i])))

    def span(i):
        gate = front[ids[i]]
        if len(gate) == 1:
            return math.inf
        a, b = [mapping[q] for q in gate]
        return abs(a//width-b//width) + abs(a%width-b%width)

    proposed = [canonical, tuple(reversed(canonical)), tuple(sorted(range(m), key=lambda i:(span(i),ids[i])))]
    seen, orders = set(), []

    def add(order):
        if order not in seen:
            seen.add(order);orders.append(order)

    for order in proposed:
        add(order)
    if m <= 7:
        pool = list(itertools.permutations(range(m)))
        rng.shuffle(pool)
        for order in pool:
            if len(orders) >= count:
                break
            add(order)
    else:
        for _ in range(count*100):
            if len(orders) >= count:
                break
            order = list(range(m));rng.shuffle(order);add(tuple(order))
    return orders[:count]


def reference_conflict(paths):
    """Pair-overlap fraction; missing individually feasible route -> 1."""
    if any(path is None for path in paths):
        return 1.0
    m = len(paths)
    if m < 2:
        return 0.0
    return sum(bool(set(a)&set(b)) for a,b in itertools.combinations(paths,2)) / math.comb(m,2)


class Engine:
    def __init__(self, router, architecture, mapping):
        self.router = router
        self.arch = architecture
        self.mapping = dict(mapping)
        self.counts = {"front_evaluations":0,"order_evaluations":0,"reference_batches":0,"gate_route_calls":0}

    def route_order(self, front, order):
        if not front:
            return []
        self.counts["front_evaluations"] += 1
        self.counts["order_evaluations"] += 1
        self.counts["gate_route_calls"] += len(front)
        return self.router.try_order(order,front,self.arch["width"],self.arch["height"],
                                     self.arch["magic_states"],self.mapping,False)

    def conflict(self, front):
        if not front:
            return 0.0
        self.counts["front_evaluations"] += 1
        self.counts["reference_batches"] += 1
        paths=[]
        for item in front.items():
            self.counts["gate_route_calls"] += 1
            blocked=self.router.initialize_to_remove(self.arch["magic_states"],self.mapping)
            route,_=self.router.route_gate(item,self.arch["width"],self.arch["height"],
                                          self.arch["magic_states"],self.mapping,blocked,False)
            paths.append(route[0][2] if route else None)
        return reference_conflict(paths)

    def choose(self, remaining, criticalities, seed, config):
        front=ready_front(remaining)
        max_cost=1+int(config.mode.startswith("two_step"))+int(config.mode=="two_step_conflict")
        cap=config.budget//max_cost
        if config.candidate_cap is not None:
            cap=min(cap,config.candidate_cap)
        orders=candidate_orders(front,criticalities,self.mapping,self.arch["width"],cap,state_seed(seed,remaining))
        if config.mode=="random":
            random.Random(state_seed(seed,remaining)^0x5A5A).shuffle(orders)
        before=dict(self.counts)
        evaluated=[]
        best_key=None;best=None
        for order in orders:
            step=self.route_order(front,order)
            if not step:
                continue
            now=sum(criticalities[g[0]] for g in step)
            next_front=ready_front(advance(remaining,step))
            rollout=[];conflict=0.0
            if config.mode.startswith("two_step"):
                ids=list(next_front)
                next_order=sorted(range(len(ids)),key=lambda i:(-criticalities[ids[i]],ids[i]))
                # Paths from the present step are released. route_order starts
                # with fresh resources, so there is no cross-step occupancy.
                rollout=self.route_order(next_front,next_order)
            if config.mode=="two_step_conflict":
                conflict=self.conflict(next_front)
            future=sum(criticalities[g[0]] for g in rollout)
            progress=now+future
            score=progress-config.conflict_weight*conflict
            record={"ids":[g[0] for g in step],"order":list(order),"now":now,
                    "future":future,"progress":progress,"conflict":conflict,"score":score}
            evaluated.append(record)
            # Random is a fixed-pool selection ablation. All routes are still
            # evaluated and charged; only selection ignores their scores.
            key=(0 if config.mode=="random" else score,now,len(step))
            if config.mode=="random":
                key=(0,0,0)
            if best_key is None or key>best_key:
                best_key=key;best=step;chosen=record
        if best is None:
            raise ValueError("No candidate makes routing progress")
        delta={k:self.counts[k]-before[k] for k in before}
        if delta["front_evaluations"]>config.budget:
            raise AssertionError("Front evaluation budget exceeded")
        return best,{"ready":len(front),"chosen":chosen,"candidates":evaluated,
                     "cost":delta,"budget":config.budget,"candidate_cap":cap}


def schedule(router,gates,architecture,mapping,seed,config):
    began=time.perf_counter()
    engine=Engine(router,architecture,mapping)
    criticalities=router.build_crit_dict_fast(gates)
    remaining=dict(enumerate(gates));steps=[];fronts=[]
    while remaining:
        step,record=engine.choose(remaining,criticalities,seed,config)
        steps.append(step);fronts.append(record);remaining=advance(remaining,step)
        if len(steps)>len(gates):
            raise AssertionError("No progress")
    return {"steps":steps,"time_steps":len(steps),"fronts":fronts,"cost":engine.counts,
            "routing_seconds":time.perf_counter()-began,"config":asdict(config),
            "quantum_risk_weight":0,"scope":"Abstract routing; QEC lookup is not applied to DASCOT paths yet."}
