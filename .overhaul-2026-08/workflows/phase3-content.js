export const meta = {
  name: 'sfskills-phase3-content',
  description: 'Wave 2 content build: an OmniStudio runtime agent (the only domain with zero agent coverage) and depth work on the thinnest security skills, each with separate requirements/builder/QA/reviewer agents',
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
REPO: ${REPO}   (cd here first; the path contains a space — quote it)
EVIDENCE BRIEF: ${SCRATCH}/EVIDENCE.md — read first. Its numbers are established fact.

HOUSE RULES (from CLAUDE.md / AGENT_RULES.md — violations fail review):
- Official Salesforce docs are the primary authority. NEVER make a factual Salesforce claim
  without official-source grounding. Fabricated API names, field names, or limits are the
  worst possible defect in this repo — a user will ship them to a production org.
- '## Official Sources Used' belongs in references/well-architected.md, not SKILL.md.
- Every SKILL.md needs '## Recommended Workflow' with 3-7 numbered steps.
- references/llm-anti-patterns.md must list 5+ mistakes AI assistants make in that domain.
- Skill-local scripts under skills/*/*/scripts/ are stdlib-only AND must have a real
  error path (sys.exit(1) / ERROR print) — the validator flags decorative checkers.
- Do NOT hand-edit generated artifacts: registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md.
- Do NOT run scripts/skill_sync.py or scripts/build_index.py — the orchestrator runs these
  centrally. Running them concurrently corrupts shared artifacts.
- Before claiming any topic is uncovered, run
  python3 scripts/search_knowledge.py "<topic>" and paste the output.
- 'timeout' is NOT available on this macOS shell.
- Today is 2026-07-31.

CRITICAL CONSTRAINT — RETRIEVAL IS ZERO-SUM (measured, see EVIDENCE.md):
The lexical retrieval window is 30 chunks. Bulking up one skill can push a NEIGHBOURING
skill below the coverage threshold, making it unreachable. Depth work is not free.
Add depth that is DISTINCTIVE (specific error messages, real limits, concrete failure
modes) rather than generic prose that competes for the same tokens as its neighbours.
`

const ITEMS = [
  {
    id: 'omnistudio-agent',
    title: 'Create the OmniStudio runtime agent — the only Salesforce domain with zero agent coverage',
    owns: [
      'agents/omnistudio-designer/ (new)',
      'commands/design-omnistudio.md (new)',
      'agents/_shared/SKILL_MAP.md (append its section only)',
      'agents/_shared/RUNTIME_VS_BUILD.md (update roster counts + table)',
    ],
    goal: `MEASURED FACT: of 1,027 skills, 986 (96.0%) are cited by at least one agent. The 41
uncited skills are almost entirely ONE domain — omnistudio, where 34 of 34 skills (100%) are
cited by no agent at all. There is no OmniStudio runtime agent. It is also the weakest domain
by content depth (median package 24.7 KB vs 40 KB corpus median; 35% of its skills under 15 KB).

Build the missing runtime agent so the domain becomes reachable.

FIRST, ground yourself:
- ls skills/omnistudio/ and read enough SKILL.md files to know what the 34 skills actually cover
  (OmniScript, FlexCards, DataRaptors, Integration Procedures, Business Rules Engine, etc.).
- Read agents/_shared/AGENT_CONTRACT.md — the mandatory 8-section AGENT.md shape including the
  Process Observations block.
- Read 3 existing designer-tier agents to match voice, structure and depth, e.g.
  agents/object-designer/AGENT.md, agents/flow-builder/AGENT.md, agents/omni-channel-routing-designer/AGENT.md.
  NOTE: omni-channel-routing-designer is about Omni-Channel (case routing) and is a COMPLETELY
  DIFFERENT product from OmniStudio. Do not conflate them, and make sure your agent's
  description disambiguates the two — users and models confuse them constantly.
- Read agents/_shared/AGENT_DISAMBIGUATION.md and make sure the new agent does not collide
  with an existing one.
- Check whether scripts/new_agent.py should scaffold this (read its --help) and prefer it over
  hand-creating files if it fits.

DECIDE AND JUSTIFY: one OmniStudio agent, or two? Consider that OmniStudio splits fairly
cleanly into (a) declarative UI authoring — OmniScript/FlexCards, and (b) data/integration —
DataRaptors/Integration Procedures. Make a decision, state your reasoning, and build what you
decided. Do not build more than two.

The agent must cite real skills — every citation must resolve to an existing
skills/omnistudio/<slug>/SKILL.md (verify each one with ls before writing it). It must also
carry an inputs.schema.json like its peers, and a commands/ wrapper.

Also register it: append its section to agents/_shared/SKILL_MAP.md and update the roster
table + counts in agents/_shared/RUNTIME_VS_BUILD.md (both of which you own).

COUNT RECONCILIATION — READ CAREFULLY. The active-runtime-agent count is lint-enforced by
scripts/check_doc_counts.py across several files INCLUDING README.md and CLAUDE.md, which
you do NOT own (another agent is editing README.md concurrently right now). Therefore:
- Do NOT edit README.md or CLAUDE.md.
- EXPECT scripts/check_doc_counts.py to FAIL after your change, reporting a mismatch. That
  failure is correct and anticipated; the orchestrator reconciles it centrally at the end.
- Do NOT try to force the lint green by editing files you do not own.
- Instead, state explicitly in your report: the old count (47), the new count (47+N), and
  the exact list of files/lines that still need the count updated. The orchestrator will
  apply that reconciliation once, after all concurrent work has landed.
The QA agent for this item is told the same thing and will not treat that specific
check_doc_counts mismatch as a blocker.`,

  },
  {
    id: 'security-depth',
    title: 'Deepen the thinnest security skills — the highest-stakes domain has the shallowest content',
    owns: [
      'skills/security/** (only the specific thin skills you select)',
    ],
    goal: `MEASURED FACT: security is the thinnest domain in the library by share — 18 of its 48
skills (37%) are under 15 KB total package size, the worst ratio of any domain. Security is
the highest-consequence domain on the platform: wrong guidance here becomes a production
vulnerability, not an inconvenience.

SELECT AND DEEPEN. Identify the thinnest security skill packages with:
  cd "${REPO}" && for d in skills/security/*/; do echo "$(find $d -name '*.md' -exec cat {} + | wc -c) $d"; done | sort -n | head -20
Pick the 6 thinnest where depth genuinely helps a practitioner, and deepen those 6. Quality
over quantity — 6 excellent skills beat 18 padded ones.

For each selected skill:
- Read the existing SKILL.md and all four references/ files first. Preserve what is right;
  you are extending, not rewriting. Do not change the skill's name, scope or frontmatter
  identity (name/category/description) — retrieval and the registry depend on them.
- Ground every new claim in official Salesforce documentation. Read
  standards/official-salesforce-sources.md for the approved source hierarchy. Cite sources
  in references/well-architected.md under '## Official Sources Used'.
- Add depth that only a practitioner would know: exact error messages and their causes,
  real governor/platform limits with numbers, the specific ways the feature fails in
  production, version/release caveats, and the interaction with adjacent features.
- Strengthen references/llm-anti-patterns.md with concrete wrong-code / right-code pairs.
  This file is the library's most differentiated asset — it is what stops an assistant
  generating plausible, insecure Salesforce code. Make each anti-pattern specific enough that
  a model could actually generate it.
- Apex/LWC/config examples must be real, current, compilable, and follow the canonical
  patterns in templates/ (reference templates by relative path instead of duplicating them).
- Respect the zero-sum retrieval constraint above.

HARD RULE: if you are not certain a technical claim is true, either verify it against official
docs or leave it out. An omission is recoverable; a fabricated security control is not.
State in your report exactly which official sources you consulted per skill.`,
  },
]

const REQ_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    understanding: { type: 'string' },
    grounding: { type: 'array', description: 'files actually read + commands actually run to ground the spec', items: { type: 'string' } },
    decisions: { type: 'array', description: 'design decisions made and why', items: { type: 'string' } },
    deliverables: {
      type: 'array',
      items: {
        type: 'object',
        properties: { path: { type: 'string' }, action: { type: 'string', enum: ['create', 'modify'] }, what: { type: 'string' } },
        required: ['path', 'action', 'what'],
      },
    },
    acceptance_criteria: {
      type: 'array',
      items: {
        type: 'object',
        properties: { criterion: { type: 'string' }, verify_command: { type: 'string' }, expected: { type: 'string' } },
        required: ['criterion', 'verify_command', 'expected'],
      },
    },
    out_of_scope: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'understanding', 'grounding', 'decisions', 'deliverables', 'acceptance_criteria', 'out_of_scope'],
}

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    files_changed: {
      type: 'array',
      items: {
        type: 'object',
        properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } },
        required: ['path', 'action', 'summary'],
      },
    },
    official_sources_used: { type: 'array', description: 'the actual Salesforce doc URLs/titles consulted', items: { type: 'string' } },
    commands_run: { type: 'array', items: { type: 'string' } },
    uncertain_claims: { type: 'array', description: 'anything you wrote that you could not fully verify — be honest, the reviewer will hunt these', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'official_sources_used', 'commands_run', 'uncertain_claims', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    criteria_results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          criterion: { type: 'string' },
          result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT_TESTABLE'] },
          command_run: { type: 'string' },
          actual_output: { type: 'string' },
        },
        required: ['criterion', 'result', 'command_run', 'actual_output'],
      },
    },
    structural_defects: {
      type: 'array',
      items: {
        type: 'object',
        properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } },
        required: ['severity', 'file', 'description'],
      },
    },
    retrieval_impact: { type: 'string', description: 'did the change measurably help or hurt retrieval for the touched skills' },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'structural_defects', 'retrieval_impact'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    factual_errors: {
      type: 'array',
      description: 'wrong Salesforce claims — the single most important output of this role',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          claim: { type: 'string' },
          why_wrong: { type: 'string' },
          official_source: { type: 'string' },
          correction: { type: 'string' },
        },
        required: ['file', 'claim', 'why_wrong', 'correction'],
      },
    },
    unverifiable_claims: { type: 'array', items: { type: 'string' } },
    canon_violations: { type: 'array', items: { type: 'string' } },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'factual_errors', 'unverifiable_claims', 'canon_violations', 'required_changes'],
}

phase('Requirements')
log(`Wave 2 content: ${ITEMS.length} items (OmniStudio agent, security depth), each requirements -> build -> QA -> review.`)

const results = await pipeline(
  ITEMS,

  (item) => agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for "${item.id}". You SPECIFY. You do not create or modify any
deliverable file. You may read anything and run read-only commands.

ITEM: ${item.title}

FILES THIS ITEM OWNS:
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

Ground the spec in the actual repo before writing it — list what you read and ran in
'grounding'. Every acceptance criterion must be checkable by one command with a stated
expected result; the QA agent will run exactly these.`,
    { label: `req:${item.id}`, phase: 'Requirements', schema: REQ_SCHEMA }),

  (spec, item) => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}". Implement the spec. You do not review your own work —
separate QA and reviewer agents will check you, so concealing a weakness only wastes cycles.

ITEM: ${item.title}

FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

SPECIFICATION:
${JSON.stringify(spec, null, 2)}

Implement every deliverable, then run every verify_command yourself and make it pass.
Record the real official sources you consulted. Put anything you could not fully verify into
uncertain_claims rather than asserting it — the reviewer will find it either way, and an
honest flag is cheap while a fabricated Salesforce claim shipped to a user is not.`,
    { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA })
    .then((build) => ({ item, spec, build })),

  (ctx) => agent(`${COMMON}

YOU ARE THE QA AGENT for "${ctx.item.id}". You TEST and you MODIFY NOTHING.

SPEC:
${JSON.stringify(ctx.spec, null, 2)}

BUILDER CLAIMS:
${JSON.stringify(ctx.build, null, 2)}

DO THIS:
1. Run every acceptance-criteria verify_command. Paste real output.
2. Run the structural gates the repo will run anyway:
     python3 scripts/validate_repo.py --changed-only
     python3 scripts/check_doc_counts.py
   and, if an agent was added, python3 scripts/validate_repo.py --agents
   Paste the real results.
   EXCEPTION: if a new agent was added, scripts/check_doc_counts.py WILL report an
   agent-count mismatch against README.md / CLAUDE.md. Those files are owned by a different
   agent working concurrently and are reconciled centrally by the orchestrator afterwards.
   Record that mismatch as a NOTE, not a blocker. Any OTHER check_doc_counts failure IS a
   blocker. Do not edit README.md or CLAUDE.md to make it pass.
3. Verify every skill id cited by any new agent actually resolves to
   skills/<domain>/<slug>/SKILL.md. A citation that does not resolve is a BLOCKER.
4. RETRIEVAL IMPACT (required): for each skill whose content changed, check it is still
   retrievable — run python3 scripts/search_knowledge.py with a query that should return it
   and confirm it comes back. The retrieval window is zero-sum, so also spot-check 2-3
   NEIGHBOURING skills in the same domain that you did NOT touch, and confirm they still
   return. Report findings in retrieval_impact with the commands.
5. Confirm the builder stayed inside its owned paths: git status --short and git diff --stat.
FAIL on any blocker.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  (ctx) => agent(`${COMMON}

YOU ARE THE TECHNICAL REVIEWER for "${ctx.item.id}". You modify nothing. QA already proved it
is structurally sound; your distinct and much harder job is whether every Salesforce claim in
it is TRUE.

SPEC:
${JSON.stringify(ctx.spec, null, 2)}
BUILD REPORT:
${JSON.stringify(ctx.build, null, 2)}
QA REPORT:
${JSON.stringify(ctx.qa, null, 2)}

DO THIS:
1. Read the real diff: cd "${REPO}" && git diff -- <owned paths>, plus any new files.
2. FACT-CHECK AGGRESSIVELY. For every substantive technical claim — API names, object and
   field names, governor limits, error messages, permission names, release behaviour, product
   names — verify it against official Salesforce documentation using WebSearch/WebFetch.
   Prioritise: (a) anything in the builder's uncertain_claims list, (b) specific numbers and
   limits, (c) exact error strings, (d) any product name that may have been rebranded, since
   Salesforce renames constantly and the library must not teach retired names.
   LLM-authored security content is exactly where confident fabrication appears. Hunt for it.
3. Check any Apex/LWC code for correctness and for CRUD/FLS/sharing enforcement — insecure
   example code in a SECURITY skill is a blocker.
4. Verify canon: required sections present, 'Official Sources Used' in
   references/well-architected.md, llm-anti-patterns.md has 5+ entries, Recommended Workflow
   has 3-7 steps, skill-local scripts stdlib-only with a real error path.
REQUEST_CHANGES on any factual error. For each, give the official source that contradicts it
and the correction.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),
)

const done = results.filter(Boolean)
log(`Wave 2 complete: ${done.length}/${ITEMS.length}.`)

return done.map((r) => ({
  item_id: r.item?.id,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  official_sources_used: r.build?.official_sources_used,
  builder_uncertain: r.build?.uncertain_claims,
  builder_not_done: r.build?.not_done,
  qa_defects: r.qa?.structural_defects,
  retrieval_impact: r.qa?.retrieval_impact,
  factual_errors: r.review?.factual_errors,
  required_changes: r.review?.required_changes,
}))
