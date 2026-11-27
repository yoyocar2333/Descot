"""Exact minimum-depth full-DAG pool, without the historical H-first closure.

Only homogeneous H/CX layers, eager virtual/readout closure, existing oriented
full footprints. Dynamic programming counts ALL legal plans without dropping
longer plans from the declared search domain. No noise labels or scoring.
"""
from functools import lru_cache
from itertools import combinations

from public_clifford import positions_for, cnot_paths, validate_plan


def minimum_gate_plans(program, spacing=3, maximum_minima=4096):
    if type(maximum_minima) is not int or maximum_minima < 1:
        raise ValueError('Positive safety bound required; never truncate')
    ops=program['operations'];n=program['logical_qubits']
    if [o['id'] for o in ops]!=list(range(len(ops))):
        raise ValueError('Source IDs must be contiguous and ordered')
    if {o['name'] for o in ops}-{'h','cx','x','measure','barrier'}:
        raise ValueError('Unsupported source gates must not be dropped')
    positions=positions_for(n,spacing);end=(1<<len(ops))-1
    parents=[sum(1<<i for i in o['predecessors']) for o in ops]
    def ready(done):
        return [o for o in ops if not done>>o['id']&1 and done&parents[o['id']]==parents[o['id']]]
    def orientation(done):
        return [sum(o['name']=='h' and o['qubits']==[q] and done>>o['id']&1 for o in ops)%2 for q in range(n)]
    def item(done,chosen,kind):
        before=orientation(done);after=before.copy()
        for o in chosen:
            if o['name']=='h':after[o['qubits'][0]]^=1
        return dict(operation_ids=[o['id'] for o in chosen],kind=kind,orientation_before=before,orientation_after=after)
    @lru_cache(None)
    def transitions(done):
        front=ready(done)
        if not front and done!=end:raise ValueError('Cyclic or invalid full source DAG')
        instant=[o for o in front if o['name'] in ('x','measure','barrier')]
        if instant:
            return [(done|sum(1<<o['id'] for o in instant),item(done,instant,'virtual_or_readout'),0)]
        choices=[];rot=orientation(done)
        for kind in ('h','cx'):
            gates=[o for o in front if o['name']==kind]
            for count in range(1,len(gates)+1):
                for subset in combinations(gates,count):
                    fs=[cnot_paths(*o['qubits'],positions,rot)[2] if kind=='cx' else {positions[o['qubits'][0]]} for o in subset]
                    if all(not a&b for i,a in enumerate(fs) for b in fs[i+1:]):
                        choices.append((done|sum(1<<o['id'] for o in subset),item(done,subset,kind),1))
        return choices
    @lru_cache(None)
    def solve(done):
        if done==end:return 0,1,1 # minimum layers, all continuations, minimum continuations
        best=None;total=minimum_count=0
        for nxt,_,cost in transitions(done):
            depth,all_count,min_count=solve(nxt);depth+=cost;total+=all_count
            if best is None or depth<best:best,minimum_count=depth,min_count
            elif depth==best:minimum_count+=min_count
        if best is None:raise ValueError('No complete continuation')
        return best,total,minimum_count
    depth,total,count=solve(0)
    if count>maximum_minima:raise ValueError(f'All {count} minimum plans exceed safety bound; no partial pool returned')
    plans=[]
    def emit(done,layers):
        if done==end:
            plan=dict(mode='exact_h_cx_subsets_v1',spacing=spacing,layers=layers)
            validate_plan(program,plan);plans.append(plan);return
        for nxt,layer,cost in transitions(done):
            if cost+solve(nxt)[0]==solve(done)[0]:emit(nxt,layers+[layer])
    emit(0,[])
    assert len(plans)==count
    return dict(minimum_physical_layers=depth,minimum_plan_count=count,
                all_legal_plan_count=total,nonminimum_plan_count=total-count,
                state_count=solve.cache_info().currsize,plans=plans,
                scope='All homogeneous ready H/CX subsets with eager zero-time closure and existing full oriented footprints. Mixed H/CX layers excluded. No concurrency cap. All deeper plans counted, not deleted.')
