export const meta = {
  name: 'sfskills-phase2-build',
  description: 'Wave 1 build: one requirements agent, one builder, one QA agent and one reviewer per work item, with disjoint file ownership',
  phases: [
    { title: 'Requirements' },
    { title: 'Build' },
    { title: 'QA' },
    { title: 'Review' },
    { title: 'Remediate' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (always cd here first; the path has a space — quote it)
EVIDENCE BRIEF: ${SCRATCH}/EVIDENCE.md — READ THIS FIRST. Its numbers were measured
directly by the orchestrator and are established fact. Do not re-derive or re-litigate them.

HOUSE RULES (from CLAUDE.md / AGENT_RULES.md — violating these fails review):
- Never hand-edit generated artifacts: registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md.
- Do NOT run scripts/skill_sync.py or scripts/build_index.py. The orchestrator runs
  those centrally at the end. Running them concurrently corrupts shared artifacts.
- Skill-local scripts under skills/*/*/scripts/ are stdlib-only.
- Never make a factual Salesforce claim without an official-source grounding.
- Never claim a topic is uncovered without pasting real search output
  (python3 scripts/search_knowledge.py "<topic>").
- 'timeout' is NOT available on this macOS shell. Do not use it.
- Today is 2026-07-31.

FILE OWNERSHIP IS STRICT. Other agents are editing this repo concurrently. Touch ONLY
the paths listed in YOUR work item. Editing outside them will be reverted and fails review.
`

const WORK_ITEMS = [
  {
    id: 'retrieval-fix',
    title: 'Fix the retrieval coverage gate and skill ranking; build an honest held-out benchmark',
    owns: [
      'pipelines/ranking.py',
      'scripts/search_knowledge.py',
      'scripts/search_skills.py',
      'config/retrieval-config.yaml',
      'mcp/sfskills-mcp/src/sfskills_mcp/skills.py',
      'evals/measurement/ (new files only)',
      '.github/workflows/validate.yml',
    ],
    goal: `The library's single biggest defect: it owns a good answer to almost every realistic
Salesforce question but denies or misroutes roughly half of them. Two fixes are already PROVEN
by the orchestrator (see EVIDENCE.md §1c and §1e). Ship them, plus the benchmark that keeps
them honest.

1. COVERAGE GATE. Today scripts/search_knowledge.py:220 gates on the cumulative 'score' while
   pipelines/ranking.py:67 ranks by 'max_score' — a units mismatch that suppresses a single
   precise match and admits several weak ones. Change the gate to
   'max_score >= min_skill_max_score OR score >= min_skill_score', with the new
   min_skill_max_score defaulting to 1.0 and configured in config/retrieval-config.yaml
   alongside the existing min_skill_score: 1.5. Apply it in BOTH search_knowledge.py and
   search_skills.py so the CLI and MCP paths agree.
   Proven effect: fixture Hit@1 94.8%->95.0%, Hit@3 98.0%->98.8%, fixture false-NONE 3->0,
   held-out NONE rate 23.3%->6.7%.

   1b. CLI/MCP DIVERGENCE (found by the orchestrator — verify it yourself, then fix it).
   The MCP server does NOT go through search_knowledge.py. mcp/sfskills-mcp/src/sfskills_mcp/
   skills.py imports aggregate_skill_scores and rerank_results from pipelines directly, and:
     - calls rerank_results(None, lexical_rows, {}, domain) — query_vector None and embeddings
       {} — so the MCP path is LEXICAL-ONLY while the CLI uses fastembed embeddings. The two
       surfaces answer the same question differently.
     - sets has_coverage = bool(enriched_skills) and never applies min_skill_score at all, so
       it has a different coverage semantic from the CLI.
   Make the two paths agree on both gating and ranking. If you conclude the MCP path should
   stay lexical-only for a deliberate reason (e.g. the shipped package does not carry the
   500 MB embeddings file — CHECK whether it does before assuming), then document that
   decision in a comment and still unify the GATE. Do not silently leave them divergent.
   Because MCP calls aggregate_skill_scores(ranked, bounded_limit) positionally, any new
   parameter you add MUST be optional and keyword-only-safe.

2. SKILL-NAME MATCH SIGNAL. The ranker cannot distinguish "this skill is ABOUT X" from
   "this skill MENTIONS X", so admin/validation-rules loses "create a validation rule" to
   data/data-migration-planning. Add a name/description overlap bonus to the skill-level
   score in pipelines/ranking.py aggregate_skill_scores (it will need the skill name and
   description — source them from registry/skills.json, loaded once and passed in; do NOT
   read the registry per query, and keep aggregate_skill_scores' existing signature working
   for current callers by making the new metadata argument optional).
   Weights: name x1.5 + description x0.5 on the fraction of query tokens matched, added to
   max_score. Make both weights configurable in config/retrieval-config.yaml.
   Proven effect: fixture Hit@1 95.0%->95.5%, held-out Hit@1 50%->65%, Hit@3 60%->75%.
   ${SCRATCH}/name_boost.py has a working reference implementation of the token/overlap
   logic (stopwords, >2 char tokens, hyphen splitting) — port it faithfully.

3. HELD-OUT BENCHMARK. The 1,356 fixtures in vector_index/query-fixtures.json are paraphrases
   of the triggers: frontmatter that is itself indexed, so they measure the easy case and
   overstate quality by ~29x on the NONE metric. Create a NEW, permanent, hand-written
   held-out benchmark under evals/measurement/ (a JSON file of query + expected_skill, plus a
   runner script). Seed it from the labeled sets in ${SCRATCH}/heldout.py and
   ${SCRATCH}/name_boost.py and EXPAND it to at least 120 queries spanning all 11 domains,
   written the way practitioners actually type. Every expected_skill MUST be verified to exist
   on disk — the runner should fail loudly if a label points at a missing skill. Report Hit@1,
   Hit@3 and the NONE rate. This is a product asset, not a session artifact.

4. RE-ENABLE THE CI GATE. .github/workflows/validate.yml currently passes
   --skip-fixture-retrieval, disabling retrieval quality in CI (self-documented as a temporary
   "Wave 1.1" measure that was never lifted). Re-enable the fixture gate, and add a job that
   runs the new held-out benchmark with threshold floors set slightly below the numbers you
   actually measure, so a regression fails the build but normal noise does not. Do not invent
   the floors — measure, then set.

Do not touch skills/ or agents/ content. This item is retrieval machinery only.`,
  },
  {
    id: 'plugin-packaging',
    title: 'Make the library installable in Claude Code as a plugin, using a tiered router architecture',
    owns: [
      '.claude-plugin/ (new)',
      '.claude/skills/ (new)',
      '.claude/agents/ (new)',
      'scripts/build_plugin.py (new)',
      'docs/installing-the-plugin.md (new)',
    ],
    goal: `Today the flagship target tool cannot install this library. There is no .claude-plugin/,
no marketplace.json, no .claude/skills/, no .claude/agents/ — only .claude/commands/ (63 files).
The 47 runtime agents and 1,027 skills are not natively installable.

HARD CONSTRAINT (measured, EVIDENCE.md §3): the 1,027 skill descriptions total 510,946 chars
~= 128k tokens. Claude Agent Skills load every skill's name+description up front, so a flat
1,027-skill plugin would consume most of a context window before the user types anything.
A flat export is NOT an option. Verify this number yourself before designing.

DESIGN A TIERED ARCHITECTURE:
- Tier 1: a small set of ROUTER skills — one per domain (11) plus a top-level entry skill.
  Each router's body teaches the model to call 'python3 scripts/search_knowledge.py "<query>"'
  (or the MCP server's search tool) and then read the specific skills/<domain>/<slug>/SKILL.md
  it returns. Routers must be genuinely useful on their own: each should carry the domain's
  decision-tree pointers and the 5-10 highest-value entry skills by name.
- Tier 2: the 1,027 skill packages stay exactly where they are, reached on demand by path.
- Tier 3: the 47 runtime agents exposed as Claude Code subagents, and the existing 63 commands.
Measure and report the actual token cost of your Tier-1 index; it must be a small fraction of
the 128k a flat export would cost. State the number.

DELIVER:
- .claude-plugin/plugin.json (and marketplace.json if the repo is to be its own marketplace),
  conforming to the current Claude Code plugin schema. RESEARCH the real schema with WebSearch
  / WebFetch against Anthropic's docs before writing it — do not guess field names. Cite the
  doc URL you used in a comment or in the docs file.
- The Tier-1 router skills.
- scripts/build_plugin.py to generate the routers and agent/command wiring deterministically
  from the registry, so this never drifts by hand. Follow the conventions of the existing
  scripts/export_skills.py.
- docs/installing-the-plugin.md with the exact install commands.
Do not modify existing exports/ targets or scripts/export_skills.py.`,
  },
  {
    id: 'docs-ia',
    title: 'Build a real entry path: docs information architecture, getting started, worked example',
    owns: [
      'docs/README.md (new)',
      'docs/getting-started.md (new)',
      'docs/architecture.md (new)',
      'docs/faq.md (new)',
      'docs/troubleshooting.md (new)',
      'docs/worked-example-*.md (new)',
      'docs/glossary.md (new)',
    ],
    goal: `A new user today lands on a 540-line README and several competing, unordered docs
(MIGRATION.md, agent-invocation-modes.md, consumer-responsibilities.md, installing-single-agents.md,
multi-ai-parity.md, QUEUE_FORMAT_PROPOSAL.md) with no path through them. There is no tutorial,
no worked end-to-end example, and no architecture overview.

Walk the real first-15-minutes yourself before writing anything, and let that friction drive
the docs. Then deliver:
- docs/README.md — the index/table of contents for all documentation, ordered by user journey,
  linking every existing doc so none are orphaned. Say plainly which docs are for CONSUMERS of
  the library vs CONTRIBUTORS to it — that split is currently invisible and is the main source
  of confusion.
- docs/getting-started.md — install to first useful output in under 10 minutes, for the three
  realistic entry points (Claude Code, the MCP server, and a plain export to another tool).
  Every command must be one you actually ran.
- docs/worked-example-<something>.md — ONE complete, honest, end-to-end walkthrough of a real
  Salesforce task done with this library. Pick a task the library genuinely does well. Show
  the actual commands and the actual output, including anything imperfect. A polished lie
  is worse than a rough truth here.
- docs/architecture.md — how skills, agents, commands, templates, decision trees, registry,
  vector_index, evals and the MCP server fit together, with a diagram (mermaid) and the data
  flow from "user asks" to "skill answers".
- docs/faq.md, docs/troubleshooting.md, docs/glossary.md — grounded in real failure modes you
  hit while walking the paths, not invented ones.

Accuracy over polish: every command must have been executed, every count must be measured.
The corpus is 1,027 skills / 47 active runtime agents (+14 build-time, +14 deprecated aliases)
/ 38 MCP tools — verify with python3 scripts/check_doc_counts.py before publishing any number.
Do NOT edit README.md; a different agent owns it.`,
  },
  {
    id: 'positioning-readme',
    title: 'Rewrite the README and define positioning and go-to-market',
    owns: [
      'README.md',
      'docs/positioning.md (new)',
      'docs/comparison.md (new)',
      'docs/go-to-market.md (new)',
    ],
    goal: `The owner's blunt assessment is that the marketing is bad. Evidence: public since
2026-06-17 with 9 stars and 2 forks; the GitHub description still claims "982+ skills" when
there are 1,027; zero GitHub releases; and the README is a 540-line wall that opens with
counts rather than with what the thing does for a person.

The positioning problem is that "1,027 skills" is a vanity metric that invites the reader to
think "an LLM already knows Salesforce." The real claim is narrower and far stronger: this
library makes an AI assistant behave like a senior Salesforce practitioner on a specific task —
it knows the platform's non-obvious failure modes, refuses the anti-patterns an LLM reliably
generates, cites official sources, and can interrogate the user's actual org through the MCP
server. Lead with depth and verifiability, not volume.

DELIVER:
- README.md, rewritten. Ruthlessly shorter. Lead with the problem and a concrete before/after
  showing what the AI produces without this library vs with it — use a REAL example drawn from
  an actual skill's llm-anti-patterns.md, quoted accurately. Then a one-command install, then
  proof (validation harnesses, evals, official-source grounding), then depth. Move reference
  material into docs/ (a different agent is building docs/README.md — link to it, do not
  create those files yourself). Keep the badges. Do not inflate any number: 1,027 skills,
  47 active runtime agents, 38 MCP tools — verify with python3 scripts/check_doc_counts.py.
- docs/positioning.md — the positioning statement, the audience segments, the three claims the
  project can defend with evidence, and the claims it must stop making.
- docs/comparison.md — an honest comparison with the alternatives, INCLUDING where this library
  is weaker. Research the real landscape with WebSearch first. Note forcedotcom/sf-skills is
  CC BY-NC while this repo is Apache-2.0, so it is a licensing wall, not a code source.
- docs/go-to-market.md — a ranked, concrete launch plan: which directories/registries accept
  submissions and what each requires, which Salesforce community channels are realistic
  (Trailblazer Community, SFXD Discord, r/salesforce, Salesforce Ben, LinkedIn, TDX), and the
  order to do them in. Include the exact GitHub hygiene fixes needed first (repo description,
  topics, a real v1 release with notes, social preview).
Every external claim needs a URL. Do not touch docs/README.md, getting-started, architecture,
faq, troubleshooting or glossary — another agent owns those.`,
  },
  {
    id: 'repo-hygiene',
    title: 'Get the repo green and remove structural cruft',
    owns: [
      'docs/queue-progress.md (via its generator only)',
      'MASTER_QUEUE.md',
      'BACKLOG.md',
      '.gitignore',
      'skills/admin/flexcard-requirements/SKILL.md',
      'skills/architect/omnistudio-vs-standard-architecture/SKILL.md',
      'skills/flow/flow-custom-property-editors/SKILL.md',
      'skills/*/*/scripts/check_*.py (only the 7 with no error path)',
    ],
    goal: `main currently FAILS its own validator. python3 scripts/validate_repo.py reports:
  ERROR docs/queue-progress.md: generated artifact is stale
plus 23 warnings. Get it to zero errors and materially fewer warnings.

1. The stale docs/queue-progress.md: regenerate it with its proper generator
   (python3 scripts/generate_queue_dashboard.py — check its --help first). Never hand-edit it.
   Also resolve the 2 drift rows the dashboard reports (related-list-configuration,
   duplicate-management are TODO/RESEARCH in BACKLOG.yaml but already exist on disk) by
   flipping them to DUPLICATE with a pointer, per the dashboard's own instructions. Note
   BACKLOG.yaml is 376 KB — edit it surgically, do not rewrite it.
2. MASTER_QUEUE.md and BACKLOG.md: CLAUDE.md says the queue row data moved to BACKLOG.yaml.
   Determine what these two files still contain that is live, and either reduce each to a
   short pointer at the real source or remove it if fully superseded. Check with git log and
   grep -rn for inbound references BEFORE deleting anything, and update every referrer you find.
3. The 7 skill checker scripts flagged "no error-output path" — they can never report a
   problem, so they are decorative. Give each a real failure path (sys.exit(1) plus an ERROR
   line when its check fails). Read what each script is actually supposed to verify and make
   it verify that; do not bolt on a fake failure. stdlib-only.
4. The 5 near-duplicate pairs the validator warns about. For each, decide: genuinely distinct
   (then sharpen the two descriptions/tags so they stop colliding), or a real duplicate (then
   say so in your report and recommend a merge — do NOT delete a skill yourself).
   Pairs: admin/flexcard-requirements vs admin/omniscript-flow-design-requirements;
   architect/omnistudio-vs-standard-architecture vs architect/omnistudio-vs-standard-decision;
   devops/bitbucket-pipelines-for-salesforce vs github-actions / gitlab-ci (these three are
   probably intentional cross-vendor parallels — verify, and if so leave them and say why);
   flow/flow-custom-property-editors vs lwc/custom-property-editor-for-flow.
5. .gitignore: confirm the large generated artifacts stay ignored (vector_index/chunks.jsonl,
   embeddings.jsonl, lexical.sqlite) and report the true clone cost (.git is 524 MB).
   Do not attempt history rewriting — just report it.
Do NOT run skill_sync.py or build_index.py. Report anything you could not fix.`,
  },
]

// `args` may be an array of work-item ids to run this invocation; omit to run all.
const SELECTED = Array.isArray(args) && args.length
  ? WORK_ITEMS.filter((w) => args.includes(w.id))
  : WORK_ITEMS

const REQ_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    understanding: { type: 'string', description: 'what the real problem is, in your own words, after reading the repo' },
    deliverables: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          action: { type: 'string', enum: ['create', 'modify', 'delete'] },
          what: { type: 'string' },
        },
        required: ['path', 'action', 'what'],
      },
    },
    acceptance_criteria: {
      type: 'array',
      description: 'each must be mechanically checkable by running a command',
      items: {
        type: 'object',
        properties: {
          criterion: { type: 'string' },
          verify_command: { type: 'string' },
          expected: { type: 'string' },
        },
        required: ['criterion', 'verify_command', 'expected'],
      },
    },
    constraints: { type: 'array', items: { type: 'string' } },
    out_of_scope: { type: 'array', items: { type: 'string' } },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'understanding', 'deliverables', 'acceptance_criteria', 'constraints', 'out_of_scope'],
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
    commands_run: { type: 'array', items: { type: 'string' } },
    measurements: { type: 'array', description: 'real numbers produced, with the command that produced them', items: { type: 'string' } },
    deviations: { type: 'array', description: 'where you deviated from the spec and why', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
    self_assessment: { type: 'string' },
  },
  required: ['item_id', 'files_changed', 'commands_run', 'measurements', 'deviations', 'not_done', 'self_assessment'],
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
    defects: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          file: { type: 'string' },
          description: { type: 'string' },
          repro: { type: 'string' },
        },
        required: ['severity', 'file', 'description', 'repro'],
      },
    },
    unverified_claims: { type: 'array', description: 'claims the builder made that you could not confirm', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'defects', 'unverified_claims'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    canon_violations: {
      type: 'array',
      items: {
        type: 'object',
        properties: { rule: { type: 'string' }, file: { type: 'string' }, detail: { type: 'string' } },
        required: ['rule', 'file', 'detail'],
      },
    },
    factual_errors: {
      type: 'array',
      description: 'Salesforce or repo claims that are wrong — the most important thing you produce',
      items: {
        type: 'object',
        properties: { file: { type: 'string' }, claim: { type: 'string' }, why_wrong: { type: 'string' }, correction: { type: 'string' } },
        required: ['file', 'claim', 'why_wrong', 'correction'],
      },
    },
    required_changes: { type: 'array', items: { type: 'string' } },
    commendations: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'canon_violations', 'factual_errors', 'required_changes'],
}

phase('Requirements')
log(`Building ${SELECTED.length} work item(s): ${SELECTED.map((w) => w.id).join(', ')} — each through requirements -> build -> QA -> review -> remediate.`)

const results = await pipeline(
  SELECTED,

  // ---- STAGE 1: REQUIREMENTS. Specifies. Does not build. ----
  (item) => agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for work item "${item.id}". Your ONLY job is to produce a precise,
mechanically-verifiable specification. You do NOT write or modify any implementation file.
(You may read anything, and run read-only commands to ground the spec in reality.)

WORK ITEM: ${item.title}

FILES THIS ITEM OWNS (nothing else may be touched by anyone on this item):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL AS STATED BY THE ORCHESTRATOR:
${item.goal}

DO THIS:
1. Read EVIDENCE.md, then read the actual code/docs in scope until you understand the real
   current behaviour. Run read-only commands to confirm the starting state.
2. Turn the goal into concrete deliverables (exact paths) and acceptance criteria. EVERY
   acceptance criterion must be checkable by a single command with a stated expected result —
   the QA agent will run exactly these. Vague criteria are a failure of your job.
3. State the constraints and what is explicitly out of scope.
4. Where the goal cites a measured number, make the criterion reference that number so a
   regression is detectable.
Return only the structured spec.`, { label: `req:${item.id}`, phase: 'Requirements', schema: REQ_SCHEMA }),

  // ---- STAGE 2: BUILD. Implements the spec. Does not review itself. ----
  (spec, item) => agent(`${COMMON}

YOU ARE THE BUILDER for work item "${item.id}". Implement the specification below. You do NOT
review your own work, and you do NOT grade yourself favourably — a separate QA agent and a
separate reviewer will check you, so hiding a problem only wastes everyone's time.

WORK ITEM: ${item.title}

FILES YOU MAY TOUCH (strict — anything else is off-limits):
${item.owns.map((o) => '  - ' + o).join('\n')}

ORIGINAL GOAL:
${item.goal}

SPECIFICATION FROM THE REQUIREMENTS AGENT:
${JSON.stringify(spec, null, 2)}

DO THIS:
1. Implement every deliverable.
2. Run every acceptance_criteria verify_command yourself and make them pass. If one cannot
   pass, say so honestly in not_done with the reason — do not fake it and do not quietly
   redefine the criterion.
3. Every number you write into any file must come from a command you actually ran. Record
   those numbers in measurements with the command.
4. Match the surrounding code and prose style. Read neighbouring files first.
Return the structured build report. Be honest in deviations and not_done — that is what they
are for.`, { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA })
    .then((build) => ({ item, spec, build })),

  // ---- STAGE 3: QA. Tests empirically. Does not fix. ----
  (ctx) => agent(`${COMMON}

YOU ARE THE QA AGENT for work item "${ctx.item.id}". You TEST. You do NOT fix anything, and you
do NOT modify any file in the repo. Assume the builder's report is optimistic until you have
reproduced it yourself.

WORK ITEM: ${ctx.item.title}

THE SPEC THE BUILDER WAS GIVEN:
${JSON.stringify(ctx.spec, null, 2)}

WHAT THE BUILDER CLAIMS THEY DID:
${JSON.stringify(ctx.build, null, 2)}

DO THIS:
1. Run EVERY acceptance-criteria verify_command from the spec. Paste the real output. Do not
   take the builder's word for any of them.
2. Independently verify each claimed measurement. If the builder reports a benchmark number,
   re-run the benchmark. Numbers that cannot be reproduced go in unverified_claims.
3. Try to BREAK it: edge cases, empty input, the path the builder obviously did not test.
   For code changes, confirm existing callers still work — check for other call sites of any
   function whose signature changed (grep the repo).
4. Confirm the builder stayed inside the owned file list: run
   git status --short  and  git diff --stat  and check for stray edits.
5. Verdict: FAIL if any blocker; PASS_WITH_ISSUES if only minor defects; PASS if genuinely clean.
Report defects precisely enough that someone else can fix them without rediscovering them.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  // ---- STAGE 4: REVIEW. Canon + factual correctness. Does not fix. ----
  (ctx) => agent(`${COMMON}

YOU ARE THE REVIEWER for work item "${ctx.item.id}". You judge CORRECTNESS and CONFORMANCE.
You do NOT fix anything and you do NOT modify any file. QA already checked that it works;
your distinct job is whether it is RIGHT and whether it obeys the repo's canon.

WORK ITEM: ${ctx.item.title}

SPEC:
${JSON.stringify(ctx.spec, null, 2)}

BUILD REPORT:
${JSON.stringify(ctx.build, null, 2)}

QA REPORT:
${JSON.stringify(ctx.qa, null, 2)}

DO THIS:
1. Read the actual diff: cd "${REPO}" && git diff -- <the owned paths> (and git status for new files).
   Review the real change, not the description of it.
2. CANON: check against CLAUDE.md and AGENT_RULES.md. Generated artifacts must not be
   hand-edited (registry/, vector_index/, docs/SKILLS.md, standards/validation-gates.md,
   docs/queue-progress.md). Skill packages keep their required shape. Skill-local scripts are
   stdlib-only. Frontmatter contracts hold.
3. FACTUAL CORRECTNESS — your highest-value output. Every Salesforce claim must be true for
   2026 and must not name retired products. Every repo statistic must match reality (verify
   with python3 scripts/check_doc_counts.py and by counting yourself). Every external URL and
   schema claim must be real — check the important ones with WebFetch. Prose written by an LLM
   about a product it is enthusiastic about is exactly where fabrication appears; hunt for it.
4. Judge whether the work actually solves the stated problem or merely appears to.
REQUEST_CHANGES if there is any factual error or canon violation.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),

  // ---- STAGE 5: REMEDIATE. Fixes only what QA and review found. ----
  (ctx) => {
    const blockers = (ctx.qa?.defects || []).filter((d) => d.severity !== 'minor')
    const changes = ctx.review?.required_changes || []
    const factual = ctx.review?.factual_errors || []
    if (!blockers.length && !changes.length && !factual.length) {
      log(`${ctx.item.id}: clean — QA ${ctx.qa?.verdict}, review ${ctx.review?.verdict}. No remediation needed.`)
      return { ...ctx, remediation: null }
    }
    return agent(`${COMMON}

YOU ARE THE REMEDIATION AGENT for work item "${ctx.item.id}". You fix EXACTLY the defects listed
below and nothing else. You do not refactor, do not improve unrelated things, and do not
re-architect. If you believe a reported defect is not real, leave it and say so.

FILES YOU MAY TOUCH:
${ctx.item.owns.map((o) => '  - ' + o).join('\n')}

QA DEFECTS (blocker/major):
${JSON.stringify(blockers, null, 2)}

REVIEWER REQUIRED CHANGES:
${JSON.stringify(changes, null, 2)}

REVIEWER FACTUAL ERRORS (fix every one — these are wrong statements shipped to users):
${JSON.stringify(factual, null, 2)}

After fixing, re-run the relevant verify commands and report the real output.`,
      { label: `fix:${ctx.item.id}`, phase: 'Remediate', schema: BUILD_SCHEMA })
      .then((remediation) => ({ ...ctx, remediation }))
  },
)

const done = results.filter(Boolean)
log(`Complete: ${done.length}/${SELECTED.length} items finished the full chain.`)

return done.map((r) => ({
  item_id: r.item?.id,
  title: r.item?.title,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  measurements: r.build?.measurements,
  builder_not_done: r.build?.not_done,
  qa_defects: r.qa?.defects,
  qa_unverified: r.qa?.unverified_claims,
  review_factual_errors: r.review?.factual_errors,
  review_required_changes: r.review?.required_changes,
  remediated: r.remediation ? r.remediation.files_changed?.map((f) => `${f.action} ${f.path}`) : 'none needed',
  remediation_not_done: r.remediation?.not_done,
}))
