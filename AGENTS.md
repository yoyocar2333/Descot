# Research continuity

User-facing explanations are in Traditional Chinese. Code, technical tables and final slides may use English. The formal report is on 2026-11-09 (UTC+8).

Read `docs/ROADMAP_2026-11-09_ZH.md`, the latest `docs/updates/` entry and the actual result records before continuing. Complete one bounded, testable increment, then explain what changed, why it matters, the recorded evidence, remaining boundary conditions and the next step. Before Nov 8, use Markdown and scientific figures for progress instead of regenerating slides.

Preserve frozen Phase 1 records. Put new experiments in separate result directories with explicit circuit/noise/decoder IDs, seeds, shot counts and confidence intervals. Keep Monte Carlo runtimes separate from routing timing experiments. Never claim an experiment ran unless recorded evidence exists.

The quantum-risk weight in the DASCOT scheduler stays at zero until a supported geometry adapter and complete physical-circuit composition are validated. A TQEC bridge span is not a DASCOT hop count. Isolated gadget survival products are an unvalidated proxy for a full decoded circuit.

Use Python 3.12 and the pinned dependency lock. Run the tests relevant to changed code; run the suite before publishing a milestone. Commit tested changes with concise messages and link the commit in the progress response. Preserve unrelated user edits. Do not create issue/comment notifications or contact other people.

Third-party CNOT graphs, graph composition and physical compilation are TQEC work. Attribute those components separately from our adapters, scheduling experiments, validation and calibration. The repository spelling is `Descot`; the underlying research method is DASCOT.
