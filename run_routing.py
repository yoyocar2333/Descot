"""Reproducible development/held-out comparison, with three timing repeats."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import statistics
import time
import numpy as np
from qiskit import QuantumCircuit
from core import COMMIT, load_core
from lookahead import Config,schedule
from saturation import routing_hooks
from validation import validate

ROOT=Path(__file__).resolve().parent
METHODS={
 "original":None,"limited":None,"saturation":None,
 "one_budget48":Config("one_step",48),
 "two_budget48":Config("two_step",48),
 "guided_budget48":Config("two_step_conflict",48),
 "one_pool16":Config("one_step",48,16),
 "two_pool16":Config("two_step",48,16),
 "random_pool16":Config("random",48,16),
}

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(path)


def make_inputs(core,repo,recovered):
    for old in sorted(recovered.glob('*/input.json')):
        data=json.loads(old.read_text());data['split']='development';data['origin']='recovered pilot input, mapping retained'
        save(ROOT/'inputs'/old.parent.name/'input.json',data)
    specs=[('held_random24_s41',24,10,41,'random'),('held_random24_s53',24,14,53,'random'),
           ('held_random36_s67',36,10,67,'random'),('held_ring24',24,12,0,'ring')]
    for name,n,layers,seed,kind in specs:
        rng=random.Random(seed);gates=[]
        for layer in range(layers):
            qubits=list(range(n))
            if kind=='random':rng.shuffle(qubits)
            else:qubits=qubits[layer%2:]+qubits[:layer%2]
            gates.extend([qubits[i],qubits[i+1]] for i in range(0,n,2))
        circuit=QuantumCircuit(n)
        for a,b in gates:circuit.cx(a,b)
        for layout in ['square_sparse','compact']:
            path=ROOT/'inputs'/f'{name}_{layout}'/'input.json'
            if path.exists():continue
            arch=getattr(core['architecture'],layout+'_layout')(n,'all_sides')
            random.seed(1001);np.random.seed(1001)
            depth=circuit.depth();began=time.perf_counter()
            mapping,cost=core['phased_graph'].build_phased_map(list(range(n)),circuit,arch,100,.1/depth,1/depth,timeout=300,include_t=True)
            data={'case':name,'layout':layout,'split':'held_out','gates':gates,'ops':['cx']*len(gates),
                  'active_qubits':n,'declared_qubits':n,'routing_program_depth':depth,'architecture':arch,
                  'mapping':mapping,'mapping_seed':1001,'mapping_seconds':time.perf_counter()-began,
                  'mapping_proxy_cost':cost,'commit':COMMIT,'workload_seed':seed,
                  'origin':'Frozen specification before evaluation; not used for parameter selection'}
            data['input_sha256']=hashlib.sha256(json.dumps({k:data[k] for k in ['gates','ops','architecture','mapping']},sort_keys=True).encode()).hexdigest()
            save(path,data)
    manifest={'routing_seed_list':[1,2,3],'timing_repeats':3,'front_budget':48,'conflict_weight':.25,
              'quantum_risk_weight':0,'parameter_selection':'Fixed before evaluation; conflict breaks integer progress ties only.',
              'held_out_specs':specs,'methods':{k:None if v is None else v.__dict__ for k,v in METHODS.items()},
              'budget_unit':'One greedy route-order evaluation or one batch of independently routed reference requests. Includes rollouts and reference batches.',
              'fairness':'Budget-matched primary comparison: one_budget48, two_budget48, guided_budget48. Fixed-pool ablations: one_pool16, two_pool16, guided_budget48, random_pool16. Original/limited/stopping are additional reference methods.',
              'limitations':'Budget units differ in front size; gate-route calls and wall time are also recorded. This is not a matched wall-time experiment.'}
    save(ROOT/'experiment_manifest.json',manifest)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,default=ROOT.parent/'external/wisq')
    parser.add_argument('--recovered',type=Path,default=ROOT.parent/'recovered/unpacked/dascot_work/results')
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--methods',nargs='+',choices=list(METHODS),default=list(METHODS))
    parser.add_argument('--seeds',nargs='+',type=int,default=[1,2,3]);parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--output',type=Path,default=ROOT/'results/routing')
    parser.add_argument('--cases',nargs='*');args=parser.parse_args()
    core=load_core(args.repo);router=core['sarouting'];make_inputs(core,args.repo,args.recovered)
    save(ROOT/'environment.json',{'python':platform.python_version(),'platform':platform.platform(),'wisq_commit':COMMIT,
         'packages':{k:importlib.metadata.version(k) for k in ['numpy','qiskit','rustworkx','stim','pymatching','tqec']}})
    if args.prepare_only:return
    for path in sorted((ROOT/'inputs').glob('*/input.json')):
        name=path.parent.name
        if args.cases and not any(c in name for c in args.cases):continue
        data=json.loads(path.read_text());gates=data['gates'];arch=data['architecture'];mapping=data['mapping']
        for seed in args.seeds:
            methods=args.methods[(seed-1)%len(args.methods):]+args.methods[:(seed-1)%len(args.methods)]
            for method in methods:
                dest=args.output/name/f'{method}_s{seed}.json'
                if dest.exists():continue
                repeats=[];hashes=[];first=None
                for repeat in range(args.repeats):
                    if METHODS[method] is None:
                        with routing_hooks(router,method,seed) as counts:
                            began=time.perf_counter()
                            steps,_,interrupted=router.sim_anneal_route(gates,arch,mapping,temperature=10,cooling_rate=.35 if method=='limited' else .1,termination_temp=.1,order_fraction=1,timeout=300,initial_order='random',reward_name='criticality',take_first_ms=False)
                            if interrupted:raise RuntimeError('Routing timeout')
                            record={'steps':steps,'time_steps':len(steps),'routing_seconds':time.perf_counter()-began,'cost':dict(counts)}
                    else:
                        record=schedule(router,gates,arch,mapping,seed,METHODS[method])
                    check=validate(gates,arch,mapping,record['steps'])
                    h=hashlib.sha256(json.dumps(record['steps']).encode()).hexdigest();hashes.append(h)
                    repeats.append({'seconds':record['routing_seconds'],'time_steps':record['time_steps'],'schedule_hash':h})
                    if first is None:first=record
                if len(set(hashes))!=1:raise AssertionError('Non-reproducible schedule across timing repeats')
                out={'case':data['case'],'instance':name,'layout':data['layout'],'split':data['split'],'method':method,'seed':seed,
                     'input_sha256':data['input_sha256'],'median_seconds':statistics.median(r['seconds'] for r in repeats),
                     'repeats':repeats,'valid':True,'validation':check,**first}
                save(dest,out)
                print(f'{name} {method} s{seed}: depth={out["time_steps"]} seconds={out["median_seconds"]:.4f}',flush=True)

if __name__=='__main__':main()
