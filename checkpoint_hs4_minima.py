"""Preserve a completed first physical batch after an interrupted large frontier.

Never relabel partial qualification as a complete selector pool. All144 plans
remain in the logical frontier; unqualified rows stay explicitly pending.
"""
import argparse
import json
from pathlib import Path
from run_hs4_minimum_frontier import ROOT,DEFAULT,read,save,sha


def checkpoint(output):
    if (output/'summary.json').exists():raise FileExistsError('Do not overwrite checkpoint')
    rows=read(output/'candidate_pool.json');env=read(output/'environment.json')
    for p,h in env['source_files_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h:raise ValueError('Executed source changed')
    certs=[read(p) for p in sorted((output/'certificates').glob('*.json'))]
    if not certs:raise ValueError('No complete full-public physical result')
    if [c['candidate_id'] for c in certs]!=[r['candidate_id'] for r in rows[:len(certs)]]:
        raise ValueError('Checkpoint must retain the whole completed initial lexical batch')
    for c in certs:
        if len(c['generators'])!=8 or c['validation']['full_z_readout_rank']!=4:
            raise ValueError('No partial validation targets accepted')
    index=[{k:v for k,v in c.items() if k not in ('backend_meta','validation','generators')} for c in certs]
    save(output/'physical_index.json',index)
    done={c['candidate_id'] for c in certs};pending=[r['candidate_id'] for r in rows if r['candidate_id'] not in done]
    calls=sum(not v['cache_hit'] for c in certs for v in c['compile_requests'])
    requests=sum(len(c['compile_requests']) for c in certs)
    status=dict(status='INTERRUPTED_INITIAL_FRONTIER_CHECKPOINT',reason='Measured complete batch physical compilation cost made the planned144-job run too large for this increment; interrupted after the first6 completed. No noisy outcomes used.',
        qualified_ids=sorted(done),pending_ids=pending,complete_frontier=False,
        completed_actual_physical_compilations=calls,completed_compile_requests=requests,
        aborted_inflight_physical_compile_calls_exact=None,
        aborted_inflight_calls_conservative_upper_bound=138*9,
        total_actual_compile_calls_lower_bound=calls,total_actual_compile_calls_upper_bound=calls+138*9,
        accounting='Completed6 certificates give exact30 compile calls. Other requests were not journaled before interruption. The absolute conservative bound retains all138 remaining tasks times9 requests, without inferring an exact aborted count from output files or timing. No matched-budget speed comparison is claimed.',
        new_shots=0,mu=0,sampling_permission=False,held_out_labels='sealed')
    save(output/'run_status.json',status)
    summary=dict(reference_id='old:p12',source_sha256=certs[0]['source_sha256'],minimum_physical_layers=9,
        full_search_legal_plans=read(output/'dp_summary.json')['all_legal_plan_count'],
        qualified_minimum_plans=len(certs),total_minimum_plans=len(rows),pending_minimum_plans=len(pending),
        unique_noisy_circuits=len({c['noisy_sha256'] for c in certs}),exact_targets=requests,
        compile_requests=requests,actual_physical_compilations=calls,exact_cache_hits=requests-calls,
        compile_accounting_scope='Completed certificates only; aborted in-flight unknown and separately bounded in run_status.json.',
        original_parallel_hashes_preserved='Original13 are retained by analysis; no p12 recompile in this checkpoint.',
        new_shots=0,sampler_calls=0,counts=None,confidence_interval=None,mu=0,
        qualification_scope='Partial physical frontier6/144; complete original32-instruction application in each qualified circuit. Not an all144 physical gate pass.')
    save(output/'summary.json',summary)
    save(output/'timing.json',dict(completed_physical_compile_wall_sum_seconds=sum(c['timing']['actual_physical_compile_seconds'] for c in certs),
        completed_exact_validation_seconds=sum(c['timing']['main_exact_seconds']+c['timing']['generator_exact_seconds'] for c in certs),
        completed_noise_dem_decoder_seconds=sum(c['timing']['noise_dem_decoder_construction_seconds'] for c in certs),
        workers=6,full_physical_batch_wall_seconds=None,routing_benchmark_seconds=None,scorer_benchmark_seconds=None,
        calibration_seconds=None,monte_carlo_seconds=None,decode_seconds=None,
        note='Parallel per-call wall sums, not CPU speed. Partial aborted time is not subtracted or claimed as savings; no independent timing benchmark.'))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--result',type=Path,default=DEFAULT);a=p.parse_args();checkpoint(a.result)
