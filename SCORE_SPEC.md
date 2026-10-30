# Implemented score, budget and model boundary

This freezes the first post-proposal implementation. It replaces the proposal's illustrative lambda/mu example, which was never an experimental setting.

## Routing score

For a legal candidate current step S, advance the DAG, release every current path, and get the next ready front F'. Route F' once in descending original criticality (gate-ID tie break), obtaining U(S).

`P2(S) = sum(c(g) for g in S) + sum(c(g) for g in U(S))`.

Independently route every request in F' with fresh available vertices. Let C(S) be the fraction of pairs of these reference paths that share a routing vertex. Use C=0 for fewer than two requests, and C=1 if any request is individually unreachable. The pinned upstream path finder determines shortest-path ties.

`score(S) = P2(S) - 0.25 * C(S)`.

P2 is an integer and C is in [0,1]. Therefore the conflict feature only breaks equal-progress ties. It cannot outweigh one unit of two-step criticality progress. This choice was fixed before evaluating held-out workloads. It is not a fitted physical coefficient. Remaining ties use current-step criticality, number of current gates, then first candidate order.

Criticality is computed once by the pinned author function: terminal gate 1; other gates 1 + maximum immediate per-qubit successor criticality. It is the count of gates on a longest downstream dependency chain, including the present gate. It is not a physical error probability or path length.

## Candidate generation and budget

Every method uses the same deterministic candidate-order stream at the same remaining-gate state and root seed: criticality-first, reverse, Manhattan-span-first, then seeded permutations, with duplicate orders removed. Candidate streams can include CNOT/T interleavings; this differs from parts of the author's search. The paired new controls share this difference.

A front-evaluation unit is (a) one greedy routing-order evaluation or (b) one batch of independent reference paths. Rollouts and conflict batches are charged. The maximum is 48 units **per current decision**, not per whole compilation. Front sizes differ, so gate-route calls and measured runtime are also recorded; this is an evaluation-budget control, not a claim of identical CPU cost.

| Method | Current candidates | Additional work per candidate | Maximum units |
|---|---:|---|---:|
| one_budget48 | 48 | none | 48 |
| two_budget48 | 24 | one rollout | 48 |
| guided_budget48 | 16 | one rollout + one reference batch | 48 |
| one_pool16 | 16 | none | 16 |
| two_pool16 | 16 | one rollout | 32 |
| random_pool16 | 16 | none; seeded random choice | 16 |

Smaller fronts may have fewer distinct orders; empty future fronts incur no fictitious work. `one_pool16`, `two_pool16`, and `guided_budget48` isolate score changes on the same candidate pool at the same state. Their costs differ and are reported. `original`, `limited`, and `saturation` are additional pinned-source references, not budget-matched versions of the new candidate stream.

## Quantum risk

The DASCOT router currently uses **mu=0**. No memory-only shortcut is represented as a route-dependent physical risk. A strict isolated-CNOT calibration lookup is provided separately, conditioned on basis, distance, spatial bridge span, temporal factor, noise model, physical p, decoder and observable definition. Unknown settings raise an error; there is no extrapolation.

`-log(1-p_fail_any)` is returned as a ranking proxy for an isolated calibrated gadget. Multiplying survival probabilities across independently calibrated gadgets is not a validated full-circuit fidelity formula. The next integration requires physical lowering of all live states and validation of correlations across consecutive gadgets.
