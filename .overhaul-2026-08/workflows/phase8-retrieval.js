export const meta = {
  name: 'sfskills-phase8-retrieval',
  description: 'Make retrieval fast, small and accurate: lazy chunk loading to kill the 2.9GB footprint, then lift held-out Hit@1 — each stage measured, reviewed and regression-gated',
  phases: [
    { title: 'A: memory spec' },
    { title: 'A: memory build' },
    { title: 'A: memory QA' },
    { title: 'B: quality spec' },
    { title: 'B: quality build' },
    { title: 'B: quality QA' },
    { title: 'Review' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
READ FIRST: ${SCRATCH}/EVIDENCE.md — especially section 6 (memory) and sections 1a–1f (retrieval).
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.
Branch is overhaul/2026-08-01-checkpoint. Do not create branches, commit, or push.

MACHINE CONSTRAINT — THIS IS NOT NEGOTIABLE: this is a 16 GB Mac and it has already been
OOM-killed once during this project. Do NOT run more than one heavy process at a time. Never
run several searches or benchmarks in parallel. If you need repeated measurements, run them
sequentially. Prefer the in-process SearchContext (build once, reuse) over spawning a process
per query.

HOUSE RULES:
- Do NOT hand-edit generated artifacts: registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md.
- Do NOT run scripts/skill_sync.py or scripts/build_index.py unless your item explicitly says
  to — they are expensive and shared. (An agent violated this earlier and left the registry
  half-synced.)
- Every performance or quality claim must come from a command you actually ran, with output.

MEASUREMENT TOOLING THAT ALREADY EXISTS — use it, do not reinvent it:
  python3 evals/measurement/run_heldout.py                 (honest, hand-written queries)
  python3 evals/measurement/run_heldout.py --no-embeddings
  python3 evals/measurement/run_heldout.py --json
  /usr/bin/time -l python3 <cmd>                           (peak RSS = "maximum resident set size")

BASELINE, measured by the orchestrator on 2026-08-01 (trust these; re-measure to confirm):
| config | held-out Hit@1 | Hit@3 | NONE | peak RSS | wall |
|---|---|---|---|---|---|
| embeddings ON  | 35.7% | 46.8% | 4.5% | 3.84 GB | 27.8 s |
| embeddings OFF | 34.4% | 42.2% | 5.2% | 2.91 GB |  6.35 s |
config/retrieval-config.yaml currently has embeddings.enabled: FALSE, set temporarily for
build-agent memory safety. Restoring it to true is part of item A's acceptance.
`

// =========================================================================
// ITEM A — MEMORY ARCHITECTURE
// =========================================================================
phase('A: memory spec')

const SPEC_SCHEMA = {
  type: 'object',
  properties: {
    item: { type: 'string' },
    current_behaviour: { type: 'string', description: 'what the code does today, with file:line' },
    root_cause: { type: 'string' },
    design: { type: 'string', description: 'the proposed approach, and why it is the right one' },
    rejected_alternatives: { type: 'array', items: { type: 'string' } },
    deliverables: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'action', 'what'] } },
    acceptance_criteria: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, verify_command: { type: 'string' }, expected: { type: 'string' } }, required: ['criterion', 'verify_command', 'expected'] } },
    backward_compat_risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['item', 'current_behaviour', 'root_cause', 'design', 'rejected_alternatives', 'deliverables', 'acceptance_criteria', 'backward_compat_risks'],
}

const specA = await agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for ITEM A: RETRIEVAL MEMORY ARCHITECTURE. Specify only —
create and modify nothing.

THE PROBLEM (orchestrator-measured): one search costs 2.91 GB peak RSS with embeddings off and
3.84 GB with them on. Root cause is that the whole corpus is materialised per process:
- scripts/search_knowledge.py load_chunks() reads the entire 126 MB vector_index/chunks.jsonl
  into a dict, purely to look up snippets for the ~30 rows the lexical pass returned. Python
  object overhead inflates that roughly 20x.
- load_embeddings() reads the 535 MB vector_index/embeddings.jsonl the same way.

WHY IT MATTERS BEYOND THIS BUILD: 3 GB and 6-28 s to answer one question locks out anyone on an
8 GB laptop and makes the documented workflow impractical. This is a PRODUCT defect, not just
an orchestration nuisance. Fixing it is what lets embeddings be restored to ON (they are worth
+4.6pp Hit@3) without the machine dying.

INVESTIGATE, then specify:
1. Read scripts/search_knowledge.py (load_chunks, load_embeddings, build_search_context,
   run_search), pipelines/lexical_index.py, pipelines/ranking.py, pipelines/chunker.py,
   pipelines/sync_engine.py (how chunks.jsonl and lexical.sqlite are produced), and
   mcp/sfskills-mcp/src/sfskills_mcp/skills.py (the MCP path).
2. Determine what is ACTUALLY needed per query. The lexical pass returns ~30 candidate rows;
   only those chunks' text and only those chunks' vectors are needed.
3. Design the fix. Candidate approaches to evaluate on merit — pick one and justify it:
   (a) store chunk text in lexical.sqlite (it is already a SQLite FTS5 DB) and read snippets
       from there by chunk_id — likely simplest, since search_index already queries it;
   (b) build a byte-offset index (chunk_id -> offset) once at build time, then seek/read only
       the needed lines from chunks.jsonl;
   (c) memory-map, or use a small on-disk KV store.
   Do the same for embeddings: load vectors only for candidate chunk_ids.
4. IMPORTANT: whatever you choose must not require a full index rebuild to be usable, or if it
   does, the rebuild must be part of scripts/build_index.py and you must say so. Note that
   vector_index/ artifacts are gitignored and rebuilt by users and CI.
5. Preserve behaviour exactly. Same results, same ranking, same payload shape. The MCP server
   calls aggregate_skill_scores POSITIONALLY — any signature change must stay compatible.

ACCEPTANCE CRITERIA must include, as commands:
- peak RSS of a single search well under 600 MB (from 2.91 GB) with embeddings OFF
- peak RSS under ~1 GB with embeddings ON
- held-out Hit@1 / Hit@3 / NONE unchanged within noise vs the baseline table above
- the 400-fixture sweep unchanged
- config/retrieval-config.yaml restored to embeddings.enabled: true at the end
Remember: run measurements SEQUENTIALLY, never in parallel — 16 GB machine.`, {
  label: 'spec:memory', phase: 'A: memory spec', schema: SPEC_SCHEMA, effort: 'high',
})

phase('A: memory build')

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } }, required: ['path', 'action', 'summary'] } },
    measurements_before_after: { type: 'array', description: 'the real numbers with the command that produced each', items: { type: 'string' } },
    commands_run: { type: 'array', items: { type: 'string' } },
    behaviour_preserved_proof: { type: 'string' },
    deviations: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item', 'files_changed', 'measurements_before_after', 'commands_run', 'behaviour_preserved_proof', 'deviations', 'not_done'],
}

const buildA = await agent(`${COMMON}

YOU ARE THE BUILDER for ITEM A: RETRIEVAL MEMORY ARCHITECTURE.

SPEC:
${JSON.stringify(specA, null, 2)}

Implement it. Then:
1. Measure peak RSS and wall time BEFORE and AFTER with /usr/bin/time -l, one process at a time.
2. Prove behaviour is preserved: run the same queries before and after and diff the ranked
   output. "why is my LWC slow" must still return lwc/lwc-performance first; "create a
   validation rule" must still behave as it does now.
3. Run python3 evals/measurement/run_heldout.py (sequentially, once) and report the numbers.
4. Once memory is genuinely fixed, restore config/retrieval-config.yaml to
   embeddings.enabled: true (remove the temporary comment block that explains the disable),
   re-measure with embeddings ON, and report both.
5. If a full index rebuild is required for the new format, run
   python3 scripts/build_index.py ONCE (it is slow, ~15 min) and report the duration.
   This is the ONE item permitted to run build_index.py.

Never run two heavy processes at once. Report honestly in not_done if a target was missed —
a partial win that is measured is far better than a claimed win that is not.`, {
  label: 'build:memory', phase: 'A: memory build', schema: BUILD_SCHEMA, effort: 'high',
})

phase('A: memory QA')

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    criteria_results: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT_TESTABLE'] }, command_run: { type: 'string' }, actual_output: { type: 'string' } }, required: ['criterion', 'result', 'command_run', 'actual_output'] } },
    independent_measurements: { type: 'array', items: { type: 'string' } },
    defects: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } }, required: ['severity', 'file', 'description'] } },
    regression_check: { type: 'string' },
  },
  required: ['item', 'verdict', 'criteria_results', 'independent_measurements', 'defects', 'regression_check'],
}

const qaA = await agent(`${COMMON}

YOU ARE THE QA AGENT for ITEM A. You TEST and MODIFY NOTHING. Assume the builder's numbers are
optimistic until you reproduce them yourself.

SPEC: ${JSON.stringify(specA, null, 2)}
BUILDER CLAIMS: ${JSON.stringify(buildA, null, 2)}

DO THIS (one process at a time — 16 GB machine):
1. Re-measure peak RSS yourself with /usr/bin/time -l for a single search, both with and
   without embeddings. Paste the raw "maximum resident set size" lines.
2. Re-run python3 evals/measurement/run_heldout.py and compare against the baseline table.
   Any drop in Hit@1 or Hit@3 beyond ~1pp is a REGRESSION and a blocker.
3. Correctness: confirm identical ranked results for a set of queries. Include at least
   "why is my LWC slow", "create a validation rule", "trigger recursion",
   "convert profiles to permission sets", and a query with FTS5-special characters such as
   "100% test coverage" and "salesforce + slack" (these used to crash the tokenizer).
4. Confirm the MCP path still works — it calls aggregate_skill_scores positionally.
   cd mcp/sfskills-mcp && python3 -m unittest discover -s tests 2>&1 | tail -20
5. Cold-cache honesty: if the fix relies on a cache or a prebuilt index, verify it still works
   when that artifact is absent (simulate a fresh clone) — or record clearly that a rebuild
   step is now REQUIRED, because that changes the install story.
6. git status --short to confirm the builder stayed in scope.
FAIL on any correctness regression, however good the memory number looks.`, {
  label: 'qa:memory', phase: 'A: memory QA', schema: QA_SCHEMA, effort: 'high',
})

log(`Item A (memory): QA verdict ${qaA?.verdict}`)

// =========================================================================
// ITEM B — RANKING QUALITY.  Runs only after A settles (same files).
// =========================================================================
phase('B: quality spec')

const specB = await agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for ITEM B: RANKING QUALITY. Specify only — modify nothing.

CONTEXT: item A just changed the retrieval internals for memory. Read the CURRENT code before
specifying anything.
ITEM A OUTCOME: ${JSON.stringify({ verdict: qaA?.verdict, measurements: buildA?.measurements_before_after }, null, 2)}

THE PROBLEM: on the honest held-out benchmark, Hit@1 is ~35.7% and Hit@3 ~46.8%. The
"Coverage: NONE" defect is already fixed (23.3% -> ~4.5%), so the remaining failure is
ROUTING: the right skill exists and is reachable, but the wrong one ranks first.

KNOWN DIAGNOSIS (EVIDENCE.md §1d — already established, do not re-litigate):
- The failure mode is that niche/advanced/adjacent skills outrank the FOUNDATIONAL skill for a
  plain query, because chunk-level lexical scoring cannot tell "this skill is ABOUT X" from
  "this skill MENTIONS X". Examples: "create a validation rule" lost to
  data/data-migration-planning while admin/validation-rules exists; "set up email templates"
  lost to admin/classic-email-template-migration (migration beat setup); "write apex unit
  tests" lost to agentforce/agent-action-unit-tests.
- A name/description match signal (name x1.5 + desc x0.5) is ALREADY IMPLEMENTED in
  pipelines/ranking.py and helped. Read it — your job is what comes NEXT.
- REFUTED, do not pursue: "vertical/industry skills outrank generic ones" (4.0% of generic
  queries hit a vertical skill vs a 10.5% corpus baseline).

INVESTIGATE FIRST, THEN SPECIFY. Run the benchmark, get the per-query failure list
(--json helps), and CLASSIFY the actual failures into mechanisms. Do not guess at fixes before
you have grouped the real misses. Candidate levers worth evaluating against evidence:
  - Stopword/short-token flooding in the FTS5 OR-join (pipelines/lexical_index.py:12-17 does an
    OR over every token, so conversational queries flood the 30-row window).
  - The lexical_limit of 30 being too small for verbose natural-language queries.
  - Title/heading-weighted chunk scoring (a match in an H1/H2 meaning more than in body text).
  - Skill-level priors: a 'stub' status penalty (28 skills carry status: stub), or a
    foundational-vs-niche signal derived from something principled rather than hand-curated.
  - Query preprocessing: dropping interrogatives, keeping the content nouns/verbs.
  - Reciprocal-rank fusion between the lexical and vector rankings rather than a weighted sum.

ACCEPTANCE CRITERIA must be measured, not asserted:
- held-out Hit@1 improves by at least 5pp over the measured post-A baseline
- held-out Hit@3 improves and does not regress
- the 400-fixture sweep does NOT regress by more than 1pp (this is the sacred floor —
  a change that wins on held-out by wrecking the fixtures is a failure)
- peak RSS does not regress past item A's achieved number
Specify the exact commands. One process at a time.`, {
  label: 'spec:quality', phase: 'B: quality spec', schema: SPEC_SCHEMA, effort: 'high',
})

phase('B: quality build')

const buildB = await agent(`${COMMON}

YOU ARE THE BUILDER for ITEM B: RANKING QUALITY.

SPEC: ${JSON.stringify(specB, null, 2)}

Implement, measuring at every step. Rules:
1. Change ONE lever at a time and measure it. A bundle of five simultaneous changes that
   nets +2pp teaches nothing and cannot be tuned later. Report a table: lever -> held-out
   Hit@1/Hit@3/NONE -> fixture Hit@1/Hit@3.
2. KEEP what measures better; REVERT what does not. Reverting a plausible idea that did not
   work is a success, not a failure — say so plainly.
3. The 400-fixture sweep is the sacred floor: do not regress it more than 1pp.
4. Document the final tuned constants in config/retrieval-config.yaml with the measured
   numbers in a comment, matching how the existing coverage-gate constants are documented.
5. Run measurements SEQUENTIALLY. 16 GB machine.
Report every lever you tried, including the ones you reverted and their numbers.`, {
  label: 'build:quality', phase: 'B: quality build', schema: BUILD_SCHEMA, effort: 'high',
})

phase('B: quality QA')

const qaB = await agent(`${COMMON}

YOU ARE THE QA AGENT for ITEM B. TEST; MODIFY NOTHING.

SPEC: ${JSON.stringify(specB, null, 2)}
BUILDER CLAIMS: ${JSON.stringify(buildB, null, 2)}

1. Re-run the held-out benchmark and the 400-fixture sweep yourself. Paste real output.
   Confirm every claimed delta. A number you cannot reproduce is a defect.
2. OVERFITTING CHECK — the most important thing you do here. The builder tuned against the
   held-out set, so it is no longer fully held out. Write 15 NEW realistic queries yourself,
   in your own words, covering domains and phrasings not in heldout-queries.json, verify each
   expected skill exists on disk, and score them. If performance on YOUR fresh queries is much
   worse than on the tuned set, the builder overfit — report that as a blocker.
3. Confirm peak RSS did not regress past item A's number (/usr/bin/time -l, one at a time).
4. Confirm FTS5-special-character queries still do not crash.
5. cd mcp/sfskills-mcp && python3 -m unittest discover -s tests 2>&1 | tail -20
6. git status --short.`, {
  label: 'qa:quality', phase: 'B: quality QA', schema: QA_SCHEMA, effort: 'high',
})

log(`Item B (quality): QA verdict ${qaB?.verdict}`)

// =========================================================================
phase('Review')

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    correctness_concerns: { type: 'array', items: { type: 'string' } },
    overfitting_assessment: { type: 'string' },
    maintainability: { type: 'string', description: 'will the next contributor understand and be able to retune this' },
    install_story_impact: { type: 'string', description: 'did any change alter what a fresh clone must do' },
    required_changes: { type: 'array', items: { type: 'string' } },
    net_result: { type: 'string', description: 'honest before/after summary of memory, speed and accuracy' },
  },
  required: ['verdict', 'correctness_concerns', 'overfitting_assessment', 'maintainability', 'install_story_impact', 'required_changes', 'net_result'],
}

const review = await agent(`${COMMON}

YOU ARE THE REVIEWER for both items. Modify nothing.

ITEM A spec/build/QA: ${JSON.stringify({ specA, buildA, qaA }, null, 2).slice(0, 20000)}
ITEM B spec/build/QA: ${JSON.stringify({ specB, buildB, qaB }, null, 2).slice(0, 20000)}

DO THIS:
1. Read the real diff: cd "${REPO}" && git diff -- scripts/ pipelines/ config/ mcp/ evals/
2. CORRECTNESS over cleverness. A lazy-loading scheme that silently returns a wrong or empty
   snippet on a cache miss is far worse than a 3 GB process. Look specifically for: missing
   chunks handled as empty rather than raising, an index that can go stale relative to
   chunks.jsonl with no detection, and any path that differs between first and subsequent runs.
3. OVERFITTING: form your own judgement on whether item B's gains generalise. Weigh QA's fresh
   queries. If the gain came from tuning constants against the very set it is measured on, say
   so — a real +3pp beats a fictitious +10pp.
4. INSTALL STORY: if the fix now requires a build step a fresh clone did not previously need,
   that is a material change and must be documented. Say where it must be documented.
5. MAINTAINABILITY: are the tuned constants documented with their measured effect, so a future
   contributor can retune rather than guess?
6. Confirm config/retrieval-config.yaml ended with embeddings.enabled: true — it was disabled
   temporarily for build safety and MUST be restored for the shipped product.
REQUEST_CHANGES on any correctness risk or on unproven claims.`, {
  label: 'review:retrieval', phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high',
})

log(`Review verdict: ${review?.verdict}`)

return { memory: { spec: specA, build: buildA, qa: qaA }, quality: { spec: specB, build: buildB, qa: qaB }, review }
