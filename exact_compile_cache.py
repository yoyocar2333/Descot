"""Deduplicate identical complete physical compile requests, never validation targets.

Each cache lives inside one candidate task. Every request includes the entire
program, plan, bases, fixed profile/compiler and k=1. Returned objects are copies.
The existing exact generator checker runs unchanged with dependency injection.
"""
from copy import deepcopy
import hashlib
from types import FunctionType
import time

from public_candidate_pool import digest
from public_clifford import PROFILE, generate_program
from surgery import TQEC_COMMIT
from exact_program_validation import check_generators_exact


class ExactCompileCache:
    def __init__(self,compiler=generate_program):
        self.compiler=compiler;self.values={};self.requests=[]
    def generate(self,program,plan,input_bases=None,output_bases=None):
        n=program['logical_qubits'];a=input_bases or 'z'*n;b=output_bases or 'z'*n
        key=digest(dict(program=program,plan=plan,input_bases=a,output_bases=b,
                        profile=PROFILE,tqec_commit=TQEC_COMMIT,k=1,distance=3))
        start=time.perf_counter();hit=key in self.values;seconds=None
        if not hit:
            t=time.perf_counter();c,m=self.compiler(program,plan,a,b);seconds=time.perf_counter()-t
            self.values[key]=(c.copy(),deepcopy(m))
        c,m=self.values[key];raw=str(c).encode()
        self.requests.append(dict(key=key,input_bases=a,output_bases=b,cache_hit=hit,
            ideal_sha256=hashlib.sha256(raw).hexdigest(),physical_compile_seconds=seconds,
            request_seconds=time.perf_counter()-start))
        return c.copy(),deepcopy(m)
    def generators(self,program,plan,artifact_dir):
        checker=FunctionType(check_generators_exact.__code__,
            {**check_generators_exact.__globals__,'generate_program':self.generate},
            check_generators_exact.__name__,check_generators_exact.__defaults__,check_generators_exact.__closure__)
        records=checker(program,plan,artifact_dir)
        for r in records:r['compile_request_seconds']=r.pop('compile_seconds')
        return records
