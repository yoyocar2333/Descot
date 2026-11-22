"""Full public Grover ready-policy control and native DAG cross-check. Zero shots."""
import argparse
import hashlib
import importlib.metadata as md
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import time

from hamada_ready_control import VENDOR, author_check, build_oracle, schedule
from public_candidate_pool import digest
from public_lookahead import schedule as lookahead
from run_grover_competition import source_program

ROOT=Path(__file__).resolve().parent
PRIOR=ROOT/'results/grover_competition_2026-11-17'
DEFAULT=ROOT/'results/hamada_ready_control_2026-11-22'
CODE=['hamada_ready_control.py','hamada_dependency_oracle.cpp','run_hamada_ready_control.py',
      'tests/test_hamada_ready_control.py','public_lookahead.py','public_clifford.py',
      'lookahead.py','requirements-lock.txt']
PROTOCOL=dict(id='hamada_alg2_common_profile_control_20261122_v1',paper='2401.15829v6 Algorithm 2',
 author_code_release='2606.21192v1 arxiv_ver1 dcaa249878ff365162cf4df930a367dca5fcf5a4',
 code_scope='Unmodified author dependency manager is an independent DAG oracle, NOT original 2401 router implementation',
 policy='Snapshot all ready CX indices in ascending original source order; greedy complete footprints, then next physical layer',
 adaptation='Common eager virtual/readout and H-first closure, explicit 3 block-z H/CX layers. Replace BFS path search with existing complete oriented TQEC template footprint. No 3D path embedding/reordering.',
 family='grover_search development only',pool='Frozen 175 legal plans; retain all 12 certified minima, no concurrency cap',
 front_budget=48,one_two_order_cap=24,seed=1,shots=0,counts=None,confidence_interval=None,
 complete_output_basis='Both original Z output bits, certified rank 2, same source/plan/ideal/noisy/DEM hashes',
 mu=0,stop_rule='No Monte Carlo. Record convergence honestly; no claim of full original BFS/Dijkstra reproduction or risk improvement.')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n')
def sig(p):return [(l['kind'],sorted(l['operation_ids']),l['orientation_before'],l['orientation_after']) for l in p['layers']]


def fingerprints():
 paths=CODE+[str(p.relative_to(ROOT)) for p in sorted(VENDOR.rglob('*')) if p.is_file()]
 paths += ['benchmarks/POST_REPORT_FAMILY_SPLIT_2026-11-18.json',
           'results/grover_competition_2026-11-17/candidate_pool.json',
           'results/grover_competition_2026-11-17/physical_index.json',
           'archives/grover_competition_2026-11-17.zip']
 return {p:sha(ROOT/p) for p in paths}


def build(binary):
 _,program=source_program()
 rows=json.loads((PRIOR/'candidate_pool.json').read_text())
 certs=json.loads((PRIOR/'physical_index.json').read_text())
 minimum=min(r['features']['physical_layers'] for r in rows)
 minima={r['candidate_id'] for r in rows if r['features']['physical_layers']==minimum}
 assert len(rows)==175 and len(minima)==12 and minima=={r['candidate_id'] for r in certs}
 began=time.perf_counter();build_oracle(binary);oracle_build=time.perf_counter()-began
 began=time.perf_counter();result=schedule(program,budget=48);policy_time=time.perf_counter()-began
 began=time.perf_counter();oracle=author_check(program,result['dag_oracle_events'],binary);oracle_time=time.perf_counter()-began
 variants={'paper_alg2_fixed_template':result};times={'paper_alg2_fixed_template':policy_time}
 for mode in ('one_step','two_step'):
  began=time.perf_counter();variants[mode]=lookahead(program,mode,spacing=3,seed=1,budget=48,candidate_cap=24)
  times[mode]=time.perf_counter()-began
 records=[]
 for name,r in variants.items():
  match=[x for x in rows if sig(x['plan'])==sig(r['plan'])]
  if len(match)!=1 or match[0]['candidate_id'] not in minima:raise ValueError('Need exact full certified plan, not depth-only agreement')
  row=match[0];cert=next(c for c in certs if c['candidate_id']==row['candidate_id'])
  records.append(dict(method=name,result=r,candidate_id=row['candidate_id'],
    full_physical_reference=cert,all_source_instruction_ids=sorted(i for l in r['plan']['layers'] for i in l['operation_ids'])))
 a,b=variants['one_step']['fronts'],variants['two_step']['fronts']
 p=result['fronts']
 assert len(p)==len(a)==len(b)
 for x,y,z in zip(p,a,b):
  assert x['ready_ids']==y['ready_ids']==z['ready_ids']
  assert x['candidate_orders']==y['candidate_orders']==z['candidate_orders']
 # On this observed Grover, every CX front is a singleton: common order pool
 # agreement is factual, not a general claim about the three algorithms.
 data=dict(protocol=PROTOCOL,source_sha256=program['source_sha256'],pool_sha256=digest(rows),
   minimum_candidate_ids=sorted(minima),records=records,original_cpp_dag_oracle=oracle,
   observed_same_candidate_order_pools=True,unique_selected_noisy_circuits=len({r['full_physical_reference']['noisy_sha256'] for r in records}),
   new_shots=0,new_physical_compilations=0,counts=None,confidence_interval=None,
   decision='Common-profile paper ready-order policy control converges with one/two-step on g174. Native shortest-path BFS and original 3D Dijkstra remain unimplemented in the common physical backend; no decoded benefit inferred.')
 timing=dict(routing_construction_seconds=times,cpp_oracle_build_seconds=oracle_build,
   cpp_dag_check_seconds=oracle_time,scorer_seconds=None,calibration_seconds=None,
   physical_compile_seconds=None,monte_carlo_seconds=None,decode_seconds=None,
   note='Single-run separated stage accounting, not an independent routing-time benchmark. Native oracle process/startup is not router time.')
 return data,timing


if __name__=='__main__':
 p=argparse.ArgumentParser(__doc__);p.add_argument('--output',type=Path,default=DEFAULT);p.add_argument('--check',action='store_true');args=p.parse_args()
 if platform.python_version_tuple()[:2]!=('3','12'):raise ValueError('Python3.12 required')
 with tempfile.TemporaryDirectory() as t:
  binary=Path(t)/'oracle';data,timing=build(binary)
  if args.check:
   assert json.loads(json.dumps(data))==json.loads((args.output/'records.json').read_text())
   assert fingerprints()==json.loads((args.output/'environment.json').read_text())['files_sha256']
   print('Replayed full 18-instruction policy, 3 same-circuit controls, original C++ ready-state oracle; 175 plans/12 minima retained; 0 new shots')
  else:
   if args.output.exists():raise FileExistsError('Fresh output required')
   args.output.mkdir(parents=True)
   env=dict(python=platform.python_version(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
     packages={p:md.version(p) for p in ('stim','qiskit','numpy','pymatching')},
     gxx=subprocess.check_output(['g++','--version'],text=True),build_flags=['-std=c++17','-O2','-Wall','-Wextra'],
     binary_sha256=sha(binary),files_sha256=fingerprints())
   for n,o in [('protocol',PROTOCOL),('records',data),('timing',timing),('environment',env)]:save(args.output/(n+'.json'),o)
   (args.output/'cpp_oracle_input.txt').write_text(data['original_cpp_dag_oracle']['stdin'])
   (args.output/'cpp_oracle_output.txt').write_text(data['original_cpp_dag_oracle']['stdout'])
   print(data['decision'])
