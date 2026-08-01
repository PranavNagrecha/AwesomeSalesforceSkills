export const meta = {
  name: 'sfskills-phase4b-gapfill',
  description: 'Finish the work the interruption cut off: the half-enriched security skill and the missing held-out benchmark README',
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
REPO: ${REPO}   (cd here first; the path has a space — quote it)
READ FIRST: ${SCRATCH}/EVIDENCE.md. Today is 2026-08-01.
Current branch is overhaul/2026-08-01-checkpoint (commit 38aea1e34). Stay on it; do not
create branches, do not commit, do not push — the orchestrator handles git.

HOUSE RULES (CLAUDE.md / AGENT_RULES.md — violations fail review):
- Official Salesforce docs are the authority. NEVER make a factual Salesforce claim without
  official-source grounding. A fabricated security control is the worst defect possible here.
- '## Official Sources Used' belongs in references/well-architected.md, not SKILL.md.
- references/llm-anti-patterns.md needs 5+ concrete mistakes AI assistants make.
- '## Recommended Workflow' needs 3-7 numbered steps.
- Do NOT hand-edit generated artifacts (registry/, vector_index/, docs/SKILLS.md).
- Do NOT run scripts/skill_sync.py or scripts/build_index.py — the orchestrator runs those.
  (NOTE: an agent violated this last session and left the registry partially synced. Do not repeat it.)
- 'timeout' does NOT exist on this macOS shell.

RETRIEVAL IS ZERO-SUM (measured): the lexical window is 30 chunks, so bulking up one skill can
push a neighbour below the coverage threshold. Add DISTINCTIVE depth (exact error strings, real
limits with numbers, named permissions, concrete failure modes), not generic prose.

FILE OWNERSHIP IS STRICT — another wave is running concurrently against this repo.
`

const ITEMS = [
  {
    id: 'security-partial-completion',
    title: 'Finish the security skill whose enrichment was cut off mid-package',
    owns: ['skills/security/privileged-access-management/**'],
    goal: `An enrichment pass was interrupted mid-package. Verified state:
- Its two sibling skills (security/clickjack-and-frame-protection and
  security/session-high-assurance-policies) each had ALL FIVE files rewritten.
- security/privileged-access-management had only SKILL.md and references/examples.md touched.
- BUT its frontmatter was already bumped to 'version: 1.1.0' and 'updated: 2026-07-31'.

So the package currently CLAIMS to be enriched and is not. That is worse than being untouched:
the version stamp tells every future currency check that this skill is fresh.

DO THIS:
1. Read the whole package first: SKILL.md and all four references/ files. Read the two SIBLING
   skills' completed enrichments to match depth, structure and voice — they are the standard
   you are matching.
2. Bring references/gotchas.md, references/llm-anti-patterns.md and
   references/well-architected.md up to the same standard as the siblings.
   - gotchas.md: non-obvious platform behaviour — the ways privileged access actually goes
     wrong in production.
   - llm-anti-patterns.md: 5+ concrete anti-patterns with wrong/right pairs. This is the
     library's most differentiated asset — make each one specific enough that a model could
     genuinely generate it.
   - well-architected.md: WAF pillar mapping plus '## Official Sources Used' with real URLs.
3. This skill is about PRIVILEGED ACCESS — Modify All Data, View All Data, permission-set
   licences, delegated administration, admin-access review. It is among the highest-stakes
   topics in the platform. Ground EVERY claim in official Salesforce documentation. Verify
   exact permission names against the docs; do not rely on memory for a permission string.
4. Do NOT change the skill's name, category or description frontmatter — retrieval and the
   registry key off them. The version/updated stamps are already correct; leave them.
5. Confirm the skill still retrieves afterwards, and that its two siblings and 2-3 other
   untouched security skills still retrieve (the zero-sum window).

If you find a claim you cannot verify against official docs, LEAVE IT OUT and say so.`,
  },
  {
    id: 'heldout-readme',
    title: 'Write the missing README for the held-out retrieval benchmark',
    owns: ['evals/measurement/README-heldout.md'],
    goal: `evals/measurement/run_heldout.py was added last session and its module docstring ends
"See README-heldout.md." — but that file was never written. The benchmark is the honest
counterpart to the curated fixtures and is about to become a CI gate, so it needs a real
explanation or the next contributor will not understand why it exists or trust its numbers.

READ FIRST: evals/measurement/run_heldout.py (including its --help), heldout-queries.json,
evals/README.md and evals/framework.md for house style.

DOCUMENT, accurately:
- WHY it exists. The 1,356 fixtures in vector_index/query-fixtures.json are paraphrases of the
  'triggers:' frontmatter that is ITSELF indexed, so they measure the easy case. Measured
  2026-07-31: the fixtures reported a 0.8% "Coverage: NONE" rate against 23.3% on hand-written
  realistic phrasings — a 29x gap. Hand-labeled Hit@1 was 95% on fixtures vs 50% held-out.
- WHAT it measures: Hit@1, Hit@3 and the "Coverage: NONE" rate, computed over the GATED skills
  list (what a caller actually sees), not the raw aggregate.
- HOW to run it, including every flag (--check, --min-hit1, --min-hit3, --max-none,
  --no-embeddings, --json, --use-domain, --top-k). Run it yourself and paste REAL current
  numbers, clearly dated — do not copy the numbers above without re-measuring, since the
  retrieval fixes have since landed.
- THE RULES for adding queries: hand-written, never copied from any skill's triggers, every
  expected_skill verified to exist on disk, phrased the way a practitioner actually types.
  Explain that copying trigger text back in would silently re-create the overfitting the
  benchmark exists to detect.
- The relationship to evals/golden/ and to the fixture sweep, so the three are not confused.

Keep it tight and factual. Match the repo's documentation voice.`,
  },
]

const REQ_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verified_current_state: { type: 'array', items: { type: 'string' } },
    deliverables: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'action', 'what'] } },
    acceptance_criteria: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, verify_command: { type: 'string' }, expected: { type: 'string' } }, required: ['criterion', 'verify_command', 'expected'] } },
    out_of_scope: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verified_current_state', 'deliverables', 'acceptance_criteria', 'out_of_scope'],
}

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } }, required: ['path', 'action', 'summary'] } },
    official_sources_used: { type: 'array', items: { type: 'string' } },
    measurements: { type: 'array', items: { type: 'string' } },
    uncertain_claims: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'official_sources_used', 'measurements', 'uncertain_claims', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    criteria_results: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT_TESTABLE'] }, command_run: { type: 'string' }, actual_output: { type: 'string' } }, required: ['criterion', 'result', 'command_run', 'actual_output'] } },
    defects: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } }, required: ['severity', 'file', 'description'] } },
    retrieval_impact: { type: 'string' },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'defects', 'retrieval_impact'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    factual_errors: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, claim: { type: 'string' }, why_wrong: { type: 'string' }, official_source: { type: 'string' }, correction: { type: 'string' } }, required: ['file', 'claim', 'why_wrong', 'correction'] } },
    canon_violations: { type: 'array', items: { type: 'string' } },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'factual_errors', 'canon_violations', 'required_changes'],
}

phase('Requirements')
log(`Gapfill: ${ITEMS.length} items left incomplete by the interruption.`)

const results = await pipeline(
  ITEMS,
  (item) => agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for "${item.id}". SPECIFY ONLY — create/modify nothing.

ITEM: ${item.title}
OWNS:
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

Verify the current state first and record the commands. Acceptance criteria must each be one
command with a stated expected result.`,
    { label: `req:${item.id}`, phase: 'Requirements', schema: REQ_SCHEMA }),

  (spec, item) => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}". Separate QA and reviewer agents check you after.

ITEM: ${item.title}
FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

SPEC:
${JSON.stringify(spec, null, 2)}

Ground every Salesforce claim in an official source and record the URL. Put anything you could
not verify in uncertain_claims rather than into a file — an omission is recoverable, a
fabricated security control is not.`,
    { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA })
    .then((build) => ({ item, spec, build })),

  (ctx) => agent(`${COMMON}

YOU ARE THE QA AGENT for "${ctx.item.id}". TEST; MODIFY NOTHING.

SPEC: ${JSON.stringify(ctx.spec, null, 2)}
BUILDER CLAIMS: ${JSON.stringify(ctx.build, null, 2)}

1. Run every acceptance-criteria verify_command; paste real output.
2. Structure: python3 scripts/validate_repo.py --changed-only (paste result).
   NOTE: pre-existing stale-artifact ERRORs for registry/ and docs/SKILLS.md are EXPECTED —
   a partial sync happened last session and the orchestrator reconciles it centrally. Those
   are NOT blockers. Any NEW error is.
3. For the security skill: verify all four references/ files now exist with real content, that
   llm-anti-patterns.md has 5+ entries, and that '## Official Sources Used' is in
   well-architected.md (not SKILL.md). Confirm frontmatter name/category/description are
   UNCHANGED from the committed version (git diff HEAD -- <path> | grep '^[-+]name:\\|^[-+]category:\\|^[-+]description:').
4. RETRIEVAL (zero-sum window): confirm the touched skill still retrieves, AND spot-check 3
   untouched neighbours in skills/security/ still retrieve. Paste the commands.
5. git status --short to confirm the builder stayed in its lane.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  (ctx) => agent(`${COMMON}

YOU ARE THE TECHNICAL REVIEWER for "${ctx.item.id}". Modify nothing.

SPEC: ${JSON.stringify(ctx.spec, null, 2)}
BUILD: ${JSON.stringify(ctx.build, null, 2)}
QA: ${JSON.stringify(ctx.qa, null, 2)}

1. Read the real diff: cd "${REPO}" && git diff -- <owned paths>, plus new files.
2. FACT-CHECK AGGRESSIVELY — this is your deliverable. For the security skill, verify every
   permission name, object name, licence name, limit and error string against official
   Salesforce docs with WebSearch/WebFetch. Prioritise the builder's uncertain_claims and any
   exact string. LLM-authored security content is precisely where confident fabrication
   appears; an invented permission name would be shipped straight into someone's production org.
3. For the benchmark README: re-run the tool and check the documented numbers match reality.
   A README that states stale metrics is a factual error.
4. Judge whether the content is REAL depth or padding that merely clears a byte threshold.
REQUEST_CHANGES on any factual error, with the official source that contradicts it.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),
)

const done = results.filter(Boolean)
log(`Gapfill complete: ${done.length}/${ITEMS.length}.`)

return done.map((r) => ({
  item_id: r.item?.id,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  official_sources_used: r.build?.official_sources_used,
  measurements: r.build?.measurements,
  uncertain_claims: r.build?.uncertain_claims,
  qa_defects: r.qa?.defects,
  retrieval_impact: r.qa?.retrieval_impact,
  factual_errors: r.review?.factual_errors,
  required_changes: r.review?.required_changes,
}))
