export const meta = {
  name: 'sfskills-phase6a-tests-agents',
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
    title: 'Build the two in-scope vertical agents: Nonprofit and Education',
    owns: [
      'agents/nonprofit-designer/ (new)',
      'agents/education-designer/ (new)',
      'commands/design-nonprofit.md (new)',
      'commands/design-education.md (new)',
    ],
    goal: `CONFIRMED P0: several Salesforce verticals have skills but no agent that can act on
them. The OWNER HAS SCOPED THIS DELIBERATELY. Build exactly TWO agents:
  - nonprofit-designer   -> /design-nonprofit
  - education-designer   -> /design-education

EXPLICITLY OUT OF SCOPE BY OWNER DECISION — do NOT build these, do not propose them, do not
"helpfully" add them: Health Cloud, Financial Services Cloud, Life Sciences Cloud, Revenue
Cloud. Their skills stay in the corpus and remain reachable by search; they simply get no
dedicated agent. If your research suggests one of them is valuable, note it in your report and
move on — do not build it.

FIRST, ground yourself and CONFIRM the groupings from the actual corpus:
  ls skills/*/ | grep -iE "npsp|nonprofit|education|eda"
  grep -rn "vertical" agents/_shared/RUNTIME_VS_BUILD.md
Report the real skill count for Nonprofit and Education. If either has too few skills to
justify an agent, say so plainly and build only the one that does — an agent with nothing to
cite is worse than no agent.

For EACH agent you build:
- Use scripts/new_agent.py to scaffold (read its --help first) so it is canon-compliant.
- Follow agents/_shared/AGENT_CONTRACT.md exactly — the 8-section shape including the
  mandatory Process Observations block.
- Read 2-3 existing Tier-3 designer agents first to match voice and depth, and read
  agents/_shared/AGENT_DISAMBIGUATION.md so the new agent does not collide with an existing one.
- CITATION DISCIPLINE — CRITICAL: 555 of 1,058 existing Mandatory Reads were machine-generated
  echo stubs (description = slug title-cased) because the old orphan gate rewarded
  mass-citation. That has just been cleaned up and a gate now ERRORs on that exact shape. DO
  NOT REPRODUCE IT. Cite 8-25 skills, each genuinely needed, each with a real human-written
  reason. Verify every citation resolves to an existing skills/<domain>/<slug>/SKILL.md.
- Ship an inputs.schema.json matching its peers, and a commands/ wrapper.
- Give it a real deliverable: what artifact does the user actually get?

Do NOT edit agents/_shared/SKILL_MAP.md or RUNTIME_VS_BUILD.md — a concurrent agent owns
those. Instead report the exact roster rows and counts the orchestrator must add. Expect
scripts/check_doc_counts.py to report an agent-count mismatch; that is anticipated and the
orchestrator reconciles it centrally. Do not edit README.md or CLAUDE.md.`,
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
log(`Wave 5a: ${ITEMS.length} items — tooling tests + the 5 missing vertical agents.`)

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
log(`Wave 5a complete: ${done.length}/${ITEMS.length}.`)

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
