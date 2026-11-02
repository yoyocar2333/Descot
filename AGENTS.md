# Research continuity

User-facing explanations are in Traditional Chinese. Code, technical tables and final slides may use English. The formal report is on 2026-11-09 (UTC+8).

Read `docs/ROADMAP_2026-11-09_ZH.md`, the latest `docs/updates/` entry and the actual result records before continuing. Complete one bounded, testable increment, then explain what changed, why it matters, the recorded evidence, remaining boundary conditions and the next step. The user advanced the completion deadline on Nov 2: finish development, experiments, figures, the final English slides/PDF, separate Chinese read-aloud script and detailed explanations, Q&A and a reproducible snapshot by Nov 5, 23:59 Asia/Taipei (before Nov 6). The presentation remains Nov 9. Use Markdown and scientific figures for routine updates; prepare final slides on Nov 5, not Nov 8. Nov 6-8 are for the user's rehearsal and explicit corrections; defer no required work to those dates.

The TA approved the direction and current measurements. Pursue both scheduling improvements and geometry/waiting/resource trade-offs. Prefer existing public workloads, preserving their complete semantics and recording source revision/file hashes, dependencies and supported gates. Consult `docs/BENCHMARK_AND_NOVELTY_PLAN_ZH.md` before benchmark selection or novelty claims. Routing steps, QEC cycles/rounds, template blocks and Stim TICKs are separate units; declare the conversion policy. Treat a new risk-aware decision rule as a research hypothesis until related-work checks and ablations support a concrete contribution.

The user clarified: compress the calendar, not the content. Preserve public-benchmark integration, complete decoded-circuit comparisons, fair routing controls and timing, geometry/waiting/resource analysis, a risk-aware method with calibration/held-out evaluation/ablations/related-work checks, reproducible data, and all final report materials. Fixtures and compatibility audits are intermediate validation, not substitutes for those deliverables. Keep unresolved work visible and continue solving it instead of reducing scope to meet the date. Scientific improvement and novelty still require evidence.

Preserve frozen Phase 1 records. Put new experiments in separate result directories with explicit circuit/noise/decoder IDs, seeds, shot counts and confidence intervals. Keep Monte Carlo runtimes separate from routing timing experiments. Never claim an experiment ran unless recorded evidence exists.

The quantum-risk weight in the DASCOT scheduler stays at zero until a supported geometry adapter and complete physical-circuit composition are validated. A TQEC bridge span is not a DASCOT hop count. Isolated gadget survival products are an unvalidated proxy for a full decoded circuit.

Use Python 3.12 and the pinned dependency lock. Run the tests relevant to changed code; run the suite before publishing a milestone. Commit tested changes with concise messages and link the commit in the progress response. Preserve unrelated user edits. Do not create issue/comment notifications or contact other people.

Third-party CNOT graphs, graph composition and physical compilation are TQEC work. Attribute those components separately from our adapters, scheduling experiments, validation and calibration. The repository spelling is `Descot`; the underlying research method is DASCOT.
