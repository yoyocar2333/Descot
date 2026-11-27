"""Drop-in next-front reward for the pinned native DASCOT search.

Keep the author's driver, enumeration/annealing proposals, acceptance rule,
parameters and path primitive. Change only the reward callback. The native
search is adaptive, so changing rewards can change later SA proposals.
"""
from contextlib import contextmanager
import hashlib
import json
import time

from saturation import routing_hooks


def step_hash(step):
    return hashlib.sha256(json.dumps(step).encode()).hexdigest()


class FrontReward:
    """Reconstruct each candidate's successor from the actual front state.

    Upstream sometimes passes a stale remaining-gate dictionary to its reward.
    Original criticality ignores it. Lookahead must not trust that argument.
    Cache only by executed IDs: paths are released before the next front.
    """
    def __init__(self,router,remaining,architecture,mapping,criticality,mode,rollout):
        self.router=router
        self.remaining=dict(remaining)
        self.arch=architecture
        self.mapping=mapping
        self.criticality=criticality
        self.mode=mode
        self.rollout=rollout
        self.cache={}
        self.requests=0
        self.cache_hits=0
        self.seconds=0.0

    def score(self,step,_supplied_remaining,crit_dict):
        start=time.perf_counter()
        try:
            self.requests+=1
            ids=tuple(sorted(g[0] for g in step))
            now=sum(crit_dict[i] for i in ids)
            if ids in self.cache:
                self.cache_hits+=1
                future=self.cache[ids]['future']
            else:
                future=0
                rolled=[]
                if self.mode=='author_two':
                    next_remaining={i:g for i,g in self.remaining.items() if i not in ids}
                    front,_=self.router.executable_subset(next_remaining)
                    keys=list(front)
                    order=sorted(range(len(keys)),key=lambda j:(-crit_dict[keys[j]],keys[j]))
                    if front:
                        rolled=self.rollout(order,front,self.arch['width'],self.arch['height'],self.arch['magic_states'],self.mapping,False)
                    future=sum(crit_dict[g[0]] for g in rolled)
                self.cache[ids]=dict(ids=list(ids),now=now,future=future,score=now+future,rollout=rolled)
            return now+future
        finally:self.seconds+=time.perf_counter()-start


@contextmanager
def author_reward_hooks(router,mode,seed):
    """No upstream file changes; restore every callback, including on failure."""
    if mode not in ['author','author_two']:raise ValueError('Unknown native reward mode')
    with routing_hooks(router,'original',seed) as native_stats:
        native_select=router.best_realizable_set_found
        native_try=router.try_order
        native_gate=router.route_gate
        native_reward=router.criticality_fast
        active={"probe":None,"phase":"main","orders":[]}
        stats=dict(mode=mode,main_order_evaluations=0,rollout_order_evaluations=0,
                   main_gate_route_calls=0,rollout_gate_route_calls=0,
                   scorer_inclusive_seconds=0.0,rollout_routing_seconds=0.0,fronts=[])

        def counted_gate(*args,**kwargs):
            stats[active['phase']+'_gate_route_calls']+=1
            return native_gate(*args,**kwargs)

        def counted_try(*args,**kwargs):
            stats[active['phase']+'_order_evaluations']+=1
            step=native_try(*args,**kwargs)
            if active['phase']=='main':
                active['orders'].append(dict(order=list(args[0]),ids=[g[0] for g in step],step_sha256=step_hash(step)))
            return step

        def rollout(*args):
            active['phase']='rollout'
            start=time.perf_counter()
            try:return counted_try(*args)
            finally:
                stats['rollout_routing_seconds']+=time.perf_counter()-start
                active['phase']='main'

        def reward(step,remaining,crit_dict):
            return active['probe'].score(step,remaining,crit_dict)

        def select(*args,**kwargs):
            gates,front,arch,mapping=args[:4]
            crit=kwargs.get('crit_dict',args[6] if len(args)>6 else {})
            probe=FrontReward(router,gates,arch,mapping,crit,mode,rollout)
            active['probe']=probe
            active['orders']=[]
            before={k:stats[k] for k in ['main_order_evaluations','rollout_order_evaluations','main_gate_route_calls','rollout_gate_route_calls']}
            chosen,tried=native_select(*args,**kwargs)
            stats['scorer_inclusive_seconds']+=probe.seconds
            stats['fronts'].append(dict(remaining_ids=list(gates),ready_ids=list(front),
                orders=active['orders'],scored_candidates=list(probe.cache.values()),
                chosen_ids=[g[0] for g in chosen],chosen_sha256=step_hash(chosen),
                chosen_score=probe.cache.get(tuple(sorted(g[0] for g in chosen))),
                reward_requests=probe.requests,cache_hits=probe.cache_hits,
                cost={k:stats[k]-before[k] for k in before}))
            return chosen,tried

        router.best_realizable_set_found=select
        router.try_order=counted_try
        router.route_gate=counted_gate
        router.criticality_fast=reward
        try:yield stats
        finally:
            router.best_realizable_set_found=native_select
            router.try_order=native_try
            router.route_gate=native_gate
            router.criticality_fast=native_reward
            stats['native_counters']=native_stats


def route_native(router,program,architecture,mapping,seed,mode):
    from run_original_objective import trace_source
    from validation import validate
    with author_reward_hooks(router,mode,seed) as stats:
        start=time.perf_counter()
        steps,_,interrupted=router.sim_anneal_route(program['routing_gates'],architecture,mapping,10,.1,.1,1,300,'random','criticality',False)
        wall=time.perf_counter()-start
    if interrupted:raise RuntimeError('Native routing timeout; no partial result accepted')
    validation=validate(program['routing_gates'],architecture,mapping,steps)
    trace=trace_source(program,steps)
    scorer=stats['scorer_inclusive_seconds']
    rolled=stats['rollout_routing_seconds']
    return dict(steps=steps,depth=len(steps),schedule_sha256=step_hash(steps),validation=validation,
        source_trace=trace,stats=stats,
        timing=dict(routing_total_seconds=wall,search_other_seconds=wall-scorer,
            scorer_inclusive_seconds=scorer,scorer_exclusive_seconds=scorer-rolled,
            lookahead_route_seconds=rolled),
        timing_policy='Additive: total = search_other + scorer_exclusive + lookahead_route. Scorer inclusive = exclusive + lookahead_route. Post-route legality/source trace excluded.',
        scope='Original native SCMR search with reward-only extension; same parameters, not equal CPU. No physical compilation or new shots.')
