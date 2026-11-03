"""Budgeted lookahead on the complete public DAG and oriented full footprints.

This adapts the Phase1 progress rule, not its abstract path primitive. H/X and
readout remain source instructions. No noisy labels or risk terms are read.
"""
from types import FunctionType
import random
import numpy as np

from lookahead import candidate_orders, state_seed
from public_clifford import positions_for, cnot_paths, validate_plan


def ready(program, done):
    return [o for o in program['operations'] if o['id'] not in done and set(o['predecessors']) <= done]


def layer(chosen, orientation, kind):
    after = list(orientation)
    for op in chosen:
        if op['name'] == 'h': after[op['qubits'][0]] ^= 1
    return {'operation_ids':sorted(o['id'] for o in chosen), 'kind':kind,
            'orientation_before':list(orientation), 'orientation_after':after}


def close(program, done, orientation):
    """Drain zero-time ops and all ready H layers before the next CX front."""
    done=set(done); orientation=list(orientation); layers=[]
    while len(done)<len(program['operations']):
        front=ready(program,done)
        if not front: raise ValueError('Invalid complete source DAG')
        instant=[o for o in front if o['name'] in ('x','measure')]
        hs=[o for o in front if o['name']=='h']
        if not instant and not hs: break
        chosen=instant or hs
        item=layer(chosen,orientation,'virtual_or_readout' if instant else 'h')
        layers.append(item); done.update(item['operation_ids']); orientation=item['orientation_after']
    return done,orientation,layers


def criticality(program):
    """Longest remaining CX count through the full quantum/classical DAG."""
    successors={o['id']:[] for o in program['operations']}
    for op in program['operations']:
        for parent in op['predecessors']: successors[parent].append(op['id'])
    values={}
    for op in reversed(program['operations']):
        values[op['id']]=int(op['name']=='cx')+max((values[s] for s in successors[op['id']]),default=0)
    return values


class Frontier:
    def __init__(self, program, spacing):
        self.program=program; self.positions=positions_for(program['logical_qubits'],spacing)
        self.width=self.positions[-1][0]+2
        self.mapping={q:x+self.width*y for q,(x,y) in enumerate(self.positions)}
        self.counts={'front_evaluations':0,'gate_route_calls':0,'closure_evaluations':0}

    def route(self, front, order, orientation):
        self.counts['front_evaluations']+=1; self.counts['gate_route_calls']+=len(front)
        reserved=set(); result=[]
        for i in order:
            op=front[i]; footprint=cnot_paths(*op['qubits'],self.positions,orientation)[2]
            if not footprint & reserved:
                result.append(op); reserved |= footprint
        return result

    def author(self, base, front, orientation, remaining, crit, seed):
        """Call the pinned author's search with only the route-order primitive changed."""
        def try_order(order, executable, *args):
            ops=[self.program['operations'][gid] for gid in executable]
            return [(o['id'],o['qubits'],[]) for o in self.route(ops,order,orientation)]
        namespace=dict(vars(base)); namespace['try_order']=try_order
        original=base.best_realizable_set_found
        function=FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
        state=random.getstate(); npstate=np.random.get_state()
        try:
            random.seed(seed); np.random.seed(seed % (2**32))
            result,tried=function(remaining,{o['id']:o['qubits'] for o in front},
                {'width':self.width,'height':self.width,'magic_states':[]},self.mapping,
                'random','criticality',crit,1,temperature=10,cooling_rate=.1,termination_temp=.1)
        finally:
            random.setstate(state);np.random.set_state(npstate)
        return [self.program['operations'][g[0]] for g in result],tried


def schedule(program, mode, spacing=3, seed=1, budget=48, candidate_cap=None, base=None):
    if mode not in ('one_step','two_step','author_profile'): raise ValueError('Unknown full-DAG method')
    cost=2 if mode=='two_step' else 1
    if type(budget) is not int or budget<cost: raise ValueError('Insufficient per-front budget')
    if candidate_cap is not None and (type(candidate_cap) is not int or candidate_cap<1): raise ValueError('Invalid candidate cap')
    engine=Frontier(program,spacing);crit=criticality(program);done=set();orientation=[0]*program['logical_qubits'];layers=[];records=[]
    while len(done)<len(program['operations']):
        done,orientation,added=close(program,done,orientation);layers.extend(added)
        if len(done)==len(program['operations']): break
        front=ready(program,done)
        if any(o['name']!='cx' for o in front): raise ValueError('Unsupported ready operation')
        before=dict(engine.counts)
        remaining={o['id']:o['qubits'] for o in program['operations'] if o['id'] not in done and o['name']=='cx'}
        local_seed=state_seed(seed,remaining)
        candidates=[]
        if mode=='author_profile':
            if base is None: raise ValueError('Pinned author module required')
            chosen,tried=engine.author(base,front,orientation,remaining,crit,local_seed)
            orders=None
        else:
            cap=min(budget//cost,candidate_cap) if candidate_cap is not None else budget//cost
            orders=candidate_orders({o['id']:o['qubits'] for o in front},crit,engine.mapping,engine.width,cap,local_seed)
            best_key=None
            for order in orders:
                current=engine.route(front,order,orientation)
                now=sum(crit[o['id']] for o in current);future=0;closure_layers=0
                if mode=='two_step':
                    engine.counts['closure_evaluations']+=1
                    after,rot,closure=close(program,done|{o['id'] for o in current},orientation)
                    closure_layers=sum(l['kind']=='h' for l in closure)
                    following=ready(program,after)
                    if following:
                        priority=sorted(range(len(following)),key=lambda i:(-crit[following[i]['id']],following[i]['id']))
                        rollout=engine.route(following,priority,rot)
                        future=sum(crit[o['id']] for o in rollout)
                record={'order':list(order),'ids':[o['id'] for o in current],'now':now,'future':future,
                        'progress':now+future,'rollout_h_layers':closure_layers}
                candidates.append(record)
                key=(now+future,now,len(current))
                if best_key is None or key>best_key:best_key=key;chosen=current
            tried=len(orders)
        if not chosen: raise ValueError('No legal full-footprint routing progress')
        delta={k:engine.counts[k]-before[k] for k in before}
        if mode!='author_profile' and delta['front_evaluations']>budget: raise AssertionError('Per-front budget exceeded')
        records.append({'ready_ids':[o['id'] for o in front],'chosen_ids':[o['id'] for o in chosen],
                        'candidate_orders':None if orders is None else [list(o) for o in orders],
                        'candidates':candidates,'orders_tried':tried,'cost':delta,
                        'budget':None if mode=='author_profile' else budget})
        item=layer(chosen,orientation,'cx');layers.append(item);done.update(item['operation_ids'])
    plan={'mode':mode,'spacing':spacing,'layers':layers}
    validate_plan(program,plan)
    return {'plan':plan,'fronts':records,'cost':engine.counts,'mu':0,
            'criticality':crit,'seed':seed,'candidate_cap':candidate_cap,'budget':budget,
            'scope':'Full-DAG/H-first and oriented-footprint adaptation. Author search uses the pinned search function; additional reference, not budget matched. Rollout crosses H closure, not a fixed physical time horizon.'}
