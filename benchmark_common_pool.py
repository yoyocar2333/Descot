"""Isolated feature-only timing on cached complete graphs; no circuit execution."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time

from common_physical_pool import physical_memory_features
from public_candidate_pool import digest
from run_common_physical_pool import ROOT,DEFAULT,descriptors,geometry
from run_grover_competition import source_program


def main(result,output):
    if output.exists():raise FileExistsError('Preserve timing evidence; use fresh output')
    _,program=source_program();rows=json.loads((result/'candidate_pool.json').read_text());ds=descriptors()
    began=time.perf_counter();cache=[(d['candidate_id'],*geometry(program,d)[::2]) for d in ds]
    cache_seconds=time.perf_counter()-began
    # Graph creation and all source checks occur outside feature-only timing.
    reference={r['candidate_id']:r for r in rows}
    signatures={}
    for cid,g,m in cache:
        values=physical_memory_features(g,m)
        if any(reference[cid]['features'][k]!=v for k,v in values.items()):raise ValueError('Feature cache differs')
        signatures[cid]=digest(values)
    def score_all():return [physical_memory_features(g,m) for cid,g,m in cache]
    for _ in range(3):score_all()
    samples=[]
    for _ in range(31):
        began=time.perf_counter();score_all();samples.append(time.perf_counter()-began)
    output.write_text(json.dumps(dict(id='common_pool_cached_feature_timing_20261125',
        input_pool_sha256=digest(rows),benchmark_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        graphs=25,feature_rows_per_repetition=25,warmups=3,repetitions=31,
        cache_graph_rebuild_seconds=cache_seconds,feature_only_samples_seconds=samples,
        median_feature_only_seconds=statistics.median(samples),minimum_feature_only_seconds=min(samples),
        reference_feature_sha256=signatures,routing_seconds=None,physical_compile_seconds=None,
        calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None,new_shots=0,
        scope='Only complete geometry feature extraction on cached graphs; independent from pool building/normalization, selector-only timing, and scientific exact checks. No router/compiler speedup claim.'),indent=2)+'\n')
    print('PASS: 31 isolated complete 25-row feature measurements, median seconds',statistics.median(samples),'0 new shots')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--result',type=Path,default=DEFAULT);p.add_argument('--output',type=Path);a=p.parse_args()
    main(a.result,a.output or a.result/'scorer_timing_isolated.json')
