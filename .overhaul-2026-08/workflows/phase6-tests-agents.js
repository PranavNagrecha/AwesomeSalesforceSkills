export const meta = {
  name: 'sfskills-phase6-tests-agents',
  description: 'Wave 5: real test coverage for the build tooling, the five missing vertical agents, dead cross-reference repair, and the export gates that never fail',
  phases: [
    { title: 'Requirements' },
    { title: 'Build' },
    { title: 'QA' },
    { title: 'Review' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (cd here first; path has a space — quote it)
EVIDENCE: ${SCRATCH}/EVIDENCE.md and ${SCRATCH}/diagnosis.json (the 18 adversarially-CONFIRMED gaps).

HOUSE RULES (CLAUDE.md / AGENT_RULES.md):
- Never hand-edit generated artifacts (registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md).
- Do NOT run scripts/skill_sync.py or scripts/build_index.py — the orchestrator runs those.
- Official Salesforce docs are the authority for every product claim.
- Never claim a topic is uncovered without pasting real search_knowledge.py output.
- 'timeout' does NOT exist on this macOS shell.
- Today is 2026-07-31.

FILE OWNERSHIP IS STRICT — several agents work this repo concurrently.

CONTEXT: these gaps SURVIVED an adversarial verification pass that refuted 66 of 84 candidate
claims. They are real. Do not spend time re-litigating whether the problem exists; verify the
current state (the repo is changing under you) and fix it.
`

const ITEMS = [
  {
    id: 'tooling-tests',
    title: 'Give the build tooling real test coverage — the owner called this out explicitly',
    owns: [
      'tests/ (new, repo-level)',
      '.github/workflows/tests.yml (new)',
      'requirements.txt',
    ],
    goal: `CONFIRMED GAP: pipelines/ (13 modules including validators.py, sync_engine.py,
similarity.py, ranking.py, lexical_index.py, chunker.py) and most of scripts/ have no unit
tests — roughly 16,900 lines of build tooling. The only existing harness tests skill checkers
and is not wired into CI. Separately, 233 of 248 MCP tests never run in CI.

This tooling decides what ships. When ranking.py or validators.py breaks, every downstream
artifact is silently wrong, and nothing catches it.

DELIVER a real repo-level test suite under tests/ using stdlib unittest (matching the
convention already used in mcp/sfskills-mcp/tests/):
1. pipelines/ranking.py — the highest-value target. It now carries the coverage gate and the
   name-match signal that were just added. Test: aggregate_skill_scores ordering, the
   max_score-vs-cumulative distinction, the name/description bonus maths (including the
   empty-query and unknown-skill paths), and that the OPTIONAL metadata argument keeps
   backwards compatibility with positional callers (the MCP server calls it positionally —
   verify that call site still works).
2. pipelines/lexical_index.py — FTS5 query sanitisation. There is a known class of user input
   that used to crash it (+, %, *, quotes, parens). Build a tiny temporary index in a temp dir
   and assert those queries return without raising.
3. pipelines/frontmatter.py and pipelines/validators.py — parsing and each validation gate's
   pass/fail behaviour on small synthetic fixtures. Do NOT depend on the real 1,027-skill
   corpus; build fixtures in tmp dirs so the suite is fast and hermetic.
4. pipelines/similarity.py / chunker.py — deterministic behaviour on known inputs.
5. scripts/check_doc_counts.py — that it actually fails on a wrong count.

Add .github/workflows/tests.yml running the repo-level suite AND the full MCP suite via
'python3 -m unittest discover -s tests' (per the confirmed fix: replace the three hand-named
MCP test modules with discovery so new modules cannot be silently omitted). Keep it fast —
target well under 2 minutes.

Report the real test count and the real runtime. Do NOT write tests that assert current
behaviour without understanding it — if a test reveals an actual bug in the tooling, REPORT IT
rather than encoding the bug as expected behaviour. That is the single most valuable thing
this item can produce.`,
  },
  {
    id: 'vertical-agents',
    title: 'Build the five missing vertical agents — 203 skills (20% of the library) have no agent',
    owns: [
      'agents/health-cloud-designer/ (new)',
      'agents/financial-services-designer/ (new)',
      'agents/nonprofit-designer/ (new)',
      'agents/education-designer/ (new)',
      'agents/revenue-cloud-designer/ (new)',
      'commands/design-health-cloud.md (new)',
      'commands/design-financial-services.md (new)',
      'commands/design-nonprofit.md (new)',
      'commands/design-education.md (new)',
      'commands/design-revenue-cloud.md (new)',
    ],
    goal: `CONFIRMED P0: six whole Salesforce verticals — 203 skills, 20% of the library — have no
agent that can act on them. One of the six (OmniStudio) was closed earlier this session by
agents/omnistudio-designer. Build the remaining five.

FIRST, ground yourself and CONFIRM the vertical groupings from the actual corpus — do not
assume my list is right:
  ls skills/*/ | grep -iE "health|hc-|fsc|financial|npsp|nonprofit|education|eda|revenue|cpq|rlm"
  grep -rn "vertical" agents/_shared/RUNTIME_VS_BUILD.md
Report the real skill count per vertical you find. If a vertical has too few skills to justify
an agent, say so and build fewer than five — justify the call.

For EACH agent you build:
- Use scripts/new_agent.py to scaffold (read its --help first) so it is canon-compliant.
- Follow agents/_shared/AGENT_CONTRACT.md exactly — the 8-section shape including the
  mandatory Process Observations block.
- Read 2-3 existing Tier-3 designer agents first to match voice and depth, and read
  agents/_shared/AGENT_DISAMBIGUATION.md so the new agent does not collide with an existing one.
- CITATION DISCIPLINE — CRITICAL: a concurrent finding is that 52.5% of existing Mandatory
  Reads are machine-generated echo stubs (description = the slug title-cased), because the
  orphan gate rewarded mass-citation. DO NOT REPRODUCE THAT PATTERN. Cite 8-25 skills, each
  one the agent genuinely needs, each with a real human-written reason it is needed. Verify
  every citation resolves to an existing skills/<domain>/<slug>/SKILL.md before writing it.
- Ship an inputs.schema.json matching its peers, and a commands/ wrapper.
- Give it a real deliverable: what artifact does the user get?

Do NOT edit agents/_shared/SKILL_MAP.md or RUNTIME_VS_BUILD.md — a concurrent agent owns
those. Instead report the exact roster rows and counts the orchestrator must add. Expect
scripts/check_doc_counts.py to report an agent-count mismatch; that is anticipated and the
orchestrator reconciles it centrally. Do not edit README.md or CLAUDE.md.`,
  },
  {
    id: 'crossref-and-export-gates',
    title: 'Repair the dead cross-reference graph and fix the export gates that can never fail',
    owns: [
      'pipelines/validators.py',
      'scripts/export_skills.py',
      'scripts/fix_related_skills.py (new)',
      'skills/*/*/SKILL.md (## Related Skills sections ONLY)',
    ],
    goal: `Three confirmed defects that share a theme: links and gates that silently do nothing.

1. DEAD CROSS-REFERENCES (P1, verified HIGH, reproduced digit-for-digit).
   339 of 2,253 domain-prefixed refs inside '## Related Skills' sections (15.0%) point at
   skills that do not exist. 83 are wrong-domain (the slug exists, under a different domain);
   256 name a slug that exists nowhere.
   - Add a validator to pipelines/validators.py: ERROR on any '<domain>/<slug>' inside a
     '## Related Skills' section that does not resolve to skills/<domain>/<slug>/SKILL.md.
     Register it so standards/validation-gates.md picks it up (that file is GENERATED — do not
     hand-edit it; the orchestrator regenerates it).
   - Write scripts/fix_related_skills.py to auto-repair the 83 wrong-domain refs (same slug,
     correct domain — a safe, mechanical fix). Run it.
   - For the 256 that resolve nowhere: do NOT invent targets. For each, either map it to a
     genuinely equivalent existing skill (verify with search_knowledge.py and only when the
     match is obvious) or REMOVE the dead reference. Removing a dead link is strictly better
     than leaving it. Report the counts for each disposition.
   - Turning this gate on will surface the remaining errors — that is intended. Report the
     final error count rather than weakening the gate to make it pass.

2. THE EXPORT-PARITY GATE NEVER FAILS (P1, verified HIGH).
   scripts/export_skills.py discards main()'s return code (around line 1170), so
   'export_skills.py --check' always exits 0 and the CI export-parity job is vacuous.
   Fix: sys.exit(main()), and make the --install branch return 0 explicitly rather than
   falling off the end returning None. Then re-run the export and rebaseline
   registry/export_manifest.json if it legitimately changed — and say clearly in your report
   whether the newly-live gate now passes or fails, and why.

3. WINDSURF EXPORT SHIPS 19 MB, 946 of 1027 FILES OVER THE PER-FILE CAP (P1, verified HIGH,
   reproduced byte-for-byte; largest file 40,581 bytes against a ~6 KB cap).
   The exporter already enforces a cap for workflows but not for rules. Add a per-target
   max_file_bytes and enforce it for windsurf rules: emit a condensed rule (frontmatter +
   Recommended Workflow + anti-pattern summary + a pointer to the full skill path) when the
   full body would exceed the cap, and fail the export if a file still exceeds it.
   Report the resulting file count, total size, and max file size.

Be careful with the Related Skills edits: touch ONLY the '## Related Skills' section of each
SKILL.md. Do not alter frontmatter, body content, or any other section — retrieval and the
registry depend on them.`,
  },
  {
    id: 'stub-transparency',
    title: 'Stop presenting stub skills as confident coverage',
    owns: [
      'scripts/search_knowledge.py (payload/status only)',
      'scripts/search_skills.py (payload/status only)',
    ],
    goal: `CONFIRMED P1 (verified HIGH on four fronts): 28 skills carry an author-set
'status: stub' in frontmatter (registry counts: 999 stable, 28 stub), and
scripts/search_knowledge.py returns them as confident coverage with no indication to the
caller. The MCP contract already exposes status; the CLI/search payload does not.

An AI assistant that receives a stub as "coverage" reads it, finds little, and stops — instead
of falling back to official sources or to the deeper skill that actually covers the topic.
That is worse than returning nothing.

DELIVER:
1. In run_search, join each aggregated skill against ctx.registry_skills and include 'status'
   (and 'description') in the returned payload, matching the shape the MCP server already uses.
2. In the CLI text output, mark stubs visibly (e.g. a '[stub]' marker on the line).
3. Mirror the same change in scripts/search_skills.py so both surfaces agree.
4. Consider — and MEASURE before deciding — whether stubs should take a ranking penalty.
   If you apply one, prove it on both the curated fixtures and
   evals/measurement/run_heldout.py (a held-out benchmark added earlier this session) and
   report before/after Hit@1, Hit@3 and NONE-rate. If it does not measurably help, do NOT
   apply it and say so. A ranking change without a measurement is not acceptable here.

NOTE: another agent recently modified these two files to add the coverage gate and the
name-match signal. READ the current contents first and build on them; do not revert that work.
Keep your change additive and narrow.`,
  },
]

const REQ_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verified_current_state: { type: 'array', description: 'commands run + output confirming the defect is still present', items: { type: 'string' } },
    deliverables: {
      type: 'array',
      items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'action', 'what'] },
    },
    acceptance_criteria: {
      type: 'array',
      items: { type: 'object', properties: { criterion: { type: 'string' }, verify_command: { type: 'string' }, expected: { type: 'string' } }, required: ['criterion', 'verify_command', 'expected'] },
    },
    handoffs: { type: 'array', items: { type: 'string' } },
    out_of_scope: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verified_current_state', 'deliverables', 'acceptance_criteria', 'handoffs', 'out_of_scope'],
}

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } }, required: ['path', 'action', 'summary'] } },
    commands_run: { type: 'array', items: { type: 'string' } },
    measurements: { type: 'array', items: { type: 'string' } },
    bugs_found_in_existing_code: { type: 'array', description: 'real defects your tests or gates exposed — high value, report every one', items: { type: 'string' } },
    handoff_to_orchestrator: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'commands_run', 'measurements', 'bugs_found_in_existing_code', 'handoff_to_orchestrator', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    criteria_results: {
      type: 'array',
      items: { type: 'object', properties: { criterion: { type: 'string' }, result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT_TESTABLE'] }, command_run: { type: 'string' }, actual_output: { type: 'string' } }, required: ['criterion', 'result', 'command_run', 'actual_output'] },
    },
    defects: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } }, required: ['severity', 'file', 'description'] } },
    regression_check: { type: 'string' },
    tests_actually_meaningful: { type: 'string', description: 'for the test item: do the tests fail when you deliberately break the code? prove it' },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'defects', 'regression_check'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    factual_errors: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, claim: { type: 'string' }, why_wrong: { type: 'string' }, correction: { type: 'string' } }, required: ['file', 'claim', 'why_wrong', 'correction'] } },
    canon_violations: { type: 'array', items: { type: 'string' } },
    solves_stated_problem: { type: 'boolean' },
    reasoning: { type: 'string' },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'factual_errors', 'canon_violations', 'solves_stated_problem', 'reasoning', 'required_changes'],
}

phase('Requirements')
log(`Wave 5: ${ITEMS.length} items — tooling tests, 5 vertical agents, cross-refs + export gates, stub transparency.`)

const results = await pipeline(
  ITEMS,
  (item) => agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for "${item.id}". You SPECIFY ONLY — create/modify nothing.

ITEM: ${item.title}
OWNS:
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

Re-verify current state first (the repo is changing under you) and record it. Then write
acceptance criteria that are each one command with a stated expected result.`,
    { label: `req:${item.id}`, phase: 'Requirements', schema: REQ_SCHEMA }),

  (spec, item) => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}". Separate QA and reviewer agents check you afterwards.

ITEM: ${item.title}
FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

SPEC:
${JSON.stringify(spec, null, 2)}

Run every verify_command. Every number you report must come from a command you ran.
If you discover a real bug in existing code, put it in bugs_found_in_existing_code — that is
a valuable finding, not an inconvenience. Never encode an existing bug as expected behaviour
in a test.`,
    { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA })
    .then((build) => ({ item, spec, build })),

  (ctx) => agent(`${COMMON}

YOU ARE THE QA AGENT for "${ctx.item.id}". You TEST and MODIFY NOTHING.

SPEC:
${JSON.stringify(ctx.spec, null, 2)}
BUILDER CLAIMS:
${JSON.stringify(ctx.build, null, 2)}

DO THIS:
1. Run every acceptance-criteria verify_command; paste real output.
2. FOR THE TEST ITEM SPECIFICALLY — the critical check: are the tests MEANINGFUL? Deliberately
   introduce a small break in the code under test (in a scratch copy or via a reverted edit),
   confirm the suite FAILS, then restore. A suite that passes against broken code is worthless.
   Record this in tests_actually_meaningful. Restore the repo to its prior state afterwards
   and confirm with git status.
3. Regression: python3 scripts/validate_repo.py --agents ; python3 scripts/search_knowledge.py "trigger recursion" ;
   python3 evals/measurement/run_heldout.py if it exists. Paste results.
   An agent-count mismatch from concurrent new agents is EXPECTED, not a blocker.
4. For new agents: verify EVERY Mandatory Read citation resolves to a real skill file, and
   check for echo-stub descriptions (description == slug title-cased). Any echo stub in a NEW
   agent is a BLOCKER — that is the exact anti-pattern this wave exists to stop.
5. git status --short / git diff --stat to confirm the builder stayed in its lane.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  (ctx) => agent(`${COMMON}

YOU ARE THE REVIEWER for "${ctx.item.id}". You modify nothing.

SPEC: ${JSON.stringify(ctx.spec, null, 2)}
BUILD: ${JSON.stringify(ctx.build, null, 2)}
QA: ${JSON.stringify(ctx.qa, null, 2)}

1. Read the real diff: cd "${REPO}" && git diff -- <owned paths>, plus new files.
2. Does it fix the CAUSE or the SYMPTOM? A gate that was turned on but then weakened to pass,
   or a test that asserts whatever the code currently does, is REQUEST_CHANGES.
3. For new agents: fact-check the Salesforce claims (vertical cloud object models, licensing,
   feature names) with WebFetch against official docs. Vertical clouds are heavily renamed —
   verify current product names. Also judge whether each agent has a genuinely useful
   deliverable or is ceremony.
4. For cross-reference repairs: spot-check that removed/remapped links were actually dead and
   that no live link was destroyed.
5. Canon compliance; no hand-edited generated artifacts.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),
)

const done = results.filter(Boolean)
log(`Wave 5 complete: ${done.length}/${ITEMS.length}.`)

return done.map((r) => ({
  item_id: r.item?.id,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  solves_root_cause: r.review?.solves_stated_problem,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  measurements: r.build?.measurements,
  bugs_found: r.build?.bugs_found_in_existing_code,
  handoff: r.build?.handoff_to_orchestrator,
  not_done: r.build?.not_done,
  qa_defects: r.qa?.defects,
  tests_meaningful: r.qa?.tests_actually_meaningful,
  factual_errors: r.review?.factual_errors,
  required_changes: r.review?.required_changes,
}))
