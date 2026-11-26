from copy import deepcopy

import pytest

from run_grover_depth_frontier import (LOGICAL_POOL, PRIOR, finalize_pool, load,
                                      next_frontier, source_program)
from public_gate_pool import enumerate_gate_plans


def test_actual_complete_next_frontier_without_depth_pruning():
    pool = load(LOGICAL_POOL)
    _, program = source_program()
    assert [r['plan'] for r in pool] == enumerate_gate_plans(program)
    prior = load(PRIOR / 'candidate_pool.json')
    qualified = [r['candidate_id'].split(':')[1] for r in prior if r['candidate_id'].startswith('fixed:')]
    selected = next_frontier(pool, qualified)
    assert len(pool) == 175 and len(qualified) == 12 and len(selected) == 52
    assert all(r['features']['physical_layers'] == 10 for r in selected)
    assert len({r['candidate_id'] for r in pool} - set(qualified) - {r['candidate_id'] for r in selected}) == 111
    assert len(prior) == 25  # better parallel candidates and all lowerings retained


@pytest.mark.parametrize('mutation', ['missing_minimum', 'unknown', 'duplicate', 'empty', 'already_compiled'])
def test_frontier_fail_closed(mutation):
    pool = [dict(candidate_id=str(i), features=dict(physical_layers=d)) for i, d in enumerate([2, 2, 3, 3, 4])]
    qualified = ['0', '1']
    if mutation == 'missing_minimum':
        qualified.pop()
    elif mutation == 'unknown':
        qualified.append('missing')
    elif mutation == 'duplicate':
        pool.append(deepcopy(pool[-1]))
    elif mutation == 'empty':
        pool = []
    else:
        qualified.append('2')
    with pytest.raises(ValueError):
        next_frontier(pool, qualified)


@pytest.mark.parametrize('ids', [[], ['a'], ['a', 'a'], ['a', 'c'], ['a', 'b', 'c']])
def test_no_selector_after_missing_duplicate_or_failed_compilation(ids):
    frontier = [dict(candidate_id='a'), dict(candidate_id='b')]
    # No common rows are provided: completeness must fail before any scoring.
    with pytest.raises(ValueError, match='Incomplete/duplicate frontier'):
        finalize_pool([], [dict(candidate_id=i) for i in ids], frontier)
