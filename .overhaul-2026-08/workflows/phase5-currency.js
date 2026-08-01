export const meta = {
  name: 'sfskills-phase5-currency',
  description: 'Wave 4: stop the library teaching retired Salesforce products — build a machine-checkable currency layer, flag superseded skills, and cover the 2026 replacements',
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
EVIDENCE BRIEF: ${SCRATCH}/EVIDENCE.md — read it first.

HOUSE RULES (CLAUDE.md / AGENT_RULES.md — violations fail review):
- Official Salesforce docs are the primary authority for every product claim.
- Do NOT hand-edit generated artifacts (registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md).
- Do NOT run scripts/skill_sync.py or scripts/build_index.py — the orchestrator runs those.
- Never claim a topic is uncovered without pasting real search_knowledge.py output.
- 'timeout' does NOT exist on this macOS shell.
- Today is 2026-07-31. Salesforce ships 3 releases/year (Spring/Summer/Winter).

FILE OWNERSHIP IS STRICT — other agents are working this repo concurrently.

THE PROBLEM THIS WAVE SOLVES:
The library is not merely missing new topics — it actively TEACHES RETIRED PRODUCTS. That is
worse than a gap: a practitioner who follows the guidance builds on something Salesforce has
stopped selling. Measured by the platform-coverage lens:
- 18 Salesforce CPQ skills. CPQ has been end-of-sale since March 2025; Revenue Cloud
  Advanced is the successor and has effectively no object-model coverage.
- All 24 marketing skills teach Marketing Cloud Engagement / Pardot. Marketing Cloud Next
  (Growth + Advanced) has zero build coverage.
- Connected App skills are stale against Spring '26, which blocks creating NEW Connected
  Apps in favour of External Client Apps.
- The Functions-retirement skill never mentions Heroku AppLink, the official GA replacement.
- Agentforce Voice (GA in Spring '26) has zero coverage.
- 972 of 1027 skills are pinned to "Spring '25+" — five releases stale — and 32 carry a
  malformed version string that the schema currently accepts.

VERIFY EVERY PRODUCT-LIFECYCLE CLAIM YOURSELF with WebSearch/WebFetch against official
Salesforce sources before acting on it. Salesforce renames and retires constantly and these
claims came from a subagent — treat them as leads, not facts. If a claim turns out to be
wrong, say so plainly; a false deprecation notice is as damaging as a missing one.
`

const ITEMS = [
  {
    id: 'currency-layer',
    title: 'Build a machine-checkable product-currency layer so staleness becomes detectable',
    owns: [
      'config/skill-frontmatter.schema.json',
      'config/product-lifecycle.yaml (new)',
      'scripts/check_currency.py (new)',
      'standards/skill-authoring-style.md',
      'docs/currency-policy.md (new)',
    ],
    goal: `Today nothing in the repo can tell that a skill teaches a dead product. There is no
status field, no supersession link, and no gate. 972/1027 skills claim "Spring '25+" and
nothing ever revisits that. Fix the MECHANISM first — individual skill fixes without it will
rot again within two releases.

DELIVER:
1. config/product-lifecycle.yaml — a curated, source-cited registry of Salesforce product
   lifecycle facts: product name, status (ga | end-of-sale | retired | renamed),
   effective date, successor product, and an official source URL for each. Seed it with the
   cases above that you have VERIFIED, plus any others you confirm. Every entry needs a real
   URL. This file is the single source of truth the rest of the layer reads.
2. Extend the skill frontmatter contract with OPTIONAL fields:
     status: current | superseded | deprecated
     superseded_by: <domain/slug of the replacement skill>
     lifecycle_note: <one line the AI must surface to the user>
   Update config/skill-frontmatter.schema.json. These MUST be optional so all 1,027 existing
   skills stay valid — this wave must not create 1,027 validation errors.
3. scripts/check_currency.py — a script that cross-references skill content against
   product-lifecycle.yaml and reports skills that teach an end-of-sale/retired product
   without a status field. Report-only by default (a --strict flag may exit non-zero).
   stdlib-only if practical; small documented deps are acceptable at repo level.
   Run it and report the real findings.
4. Also fix the 32 malformed salesforce-version values — find them
   (grep -h "salesforce-version:" skills/*/*/SKILL.md | sort | uniq -c | sort -rn),
   report the malformed set, and tighten the schema pattern so new ones cannot be added.
   Do NOT mass-rewrite all 972 "Spring '25+" values — that is a content decision, and a
   blanket bump would be a lie. Recommend a policy in docs/currency-policy.md instead.
5. docs/currency-policy.md — how the project keeps up with 3 releases/year: what triggers a
   review, who owns it, how status/superseded_by are applied, and how check_currency.py runs.

Do NOT edit skills/ in this item — a separate agent applies the flags.`,
  },
  {
    id: 'retired-product-flags',
    title: 'Flag the skills that teach end-of-sale products, and point them at the successor',
    owns: [
      'skills/**/SKILL.md (ONLY the CPQ / Connected App / Functions skills you verify as affected)',
    ],
    goal: `Apply honest, accurate deprecation guidance to the skills that teach superseded products.
This is a SURGICAL item: you are not rewriting these skills, you are making sure a reader is
told the truth about the product's status up front.

STEP 1 — VERIFY THE LIFECYCLE FACTS FIRST, with WebSearch/WebFetch against official
Salesforce sources. Do not take any of these on faith:
  (a) Salesforce CPQ end-of-sale (claimed March 2025) and what exactly replaces it
      (Revenue Cloud Advanced?). What is the precise current product name and status?
      IMPORTANT NUANCE: end-of-sale is NOT end-of-support. Thousands of orgs still run CPQ
      and will for years. The correct guidance for an existing CPQ org is different from the
      guidance for a NEW implementation. Say both.
  (b) Spring '26 Connected Apps: is creating new Connected Apps really blocked in favour of
      External Client Apps? Under what conditions, and with what admin setting?
  (c) Salesforce Functions retirement and whether Heroku AppLink is the GA successor.
If any claim does not hold up, DO NOT apply a flag for it — report the correction instead.

STEP 2 — IDENTIFY the affected skills precisely:
  ls skills/*/ | grep -i cpq
  grep -ril "connected app" --include=SKILL.md skills/ | head -30
  grep -ril "salesforce functions" --include=SKILL.md skills/ | head

STEP 3 — For each VERIFIED affected skill, add:
  - the frontmatter fields the currency-layer agent defined (status/superseded_by/
    lifecycle_note) IF that schema change has landed; check
    config/skill-frontmatter.schema.json first. If it has not landed yet, use a prominent
    in-body notice only and say so in your report.
  - a short, factual notice near the top of SKILL.md stating the product's status, the date,
    the successor, and — critically — that existing implementations remain supported. Cite
    the official source. No alarmism, no marketing language.
  - where the skill would lead someone to BUILD something new on the dead product, add the
    decision guidance: new implementation -> successor; existing org -> this skill applies.

CONSTRAINTS:
- Do NOT delete or rename any skill; the registry and retrieval depend on identity.
- Do NOT change any skill's name/category/description frontmatter.
- Do NOT touch skills owned by other waves: admin/flexcard-requirements,
  architect/omnistudio-vs-standard-architecture, flow/flow-custom-property-editors, or any
  skills/security/** package.
- Accuracy over volume. Ten correctly-flagged skills beat thirty with a wrong date.`,
  },
  {
    id: 'coverage-2026',
    title: 'Cover the 2026 Salesforce surface the library is missing',
    owns: [
      'skills/agentforce/** (new skill packages only)',
      'skills/integration/** (new skill packages only)',
      'BACKLOG.yaml (append new entries only)',
    ],
    goal: `Fill the highest-value genuine coverage gaps for the current platform. Use
scripts/new_skill.py to scaffold (read its --help; it takes domain, name, --strict and
--agent) so the packages come out canon-compliant — do NOT hand-create skill directories.

CANDIDATE GAPS (verify EACH with python3 scripts/search_knowledge.py "<topic>" and paste the
output BEFORE building — this repo has 1,027 skills and prior agents have wrongly declared
topics uncovered; several of these will turn out to be covered under another name):
  1. Agentforce Voice (claimed GA Spring '26)
  2. Agentforce Multi-Agent Orchestration (Spring '26 / Summer '26)
  3. Agentforce in Flow
  4. Heroku AppLink as the Salesforce Functions successor
  5. External Client Apps (the Connected Apps successor)

OWNER SCOPE DECISION — OUT OF SCOPE, do NOT build and do not propose: Life Sciences Cloud,
Health Cloud, Financial Services Cloud, Revenue Cloud Advanced. Even though the diagnosis
flagged Life Sciences as a confirmed gap and its dev guide sits in knowledge/imports, the
owner has excluded it. Note it in your report and move on.
Vertical CPQ/Revenue content is still FLAGGED for deprecation by the retired-product-flags
item (users of the 18 CPQ skills must be told the product is end-of-sale) — but no Revenue
Cloud replacement skills are to be authored in this wave.

BUILD ONLY WHAT YOU CONFIRM IS BOTH (a) genuinely uncovered and (b) genuinely GA or clearly
documented by Salesforce. Do not author a skill about a product you cannot verify exists with
its current name — a confidently-wrong skill about a misremembered 2026 product is the worst
possible output. If you can only confirm 2 of the 5, build 2 and report why the others were
skipped. Quality and truth over count.

For each skill you DO build, meet the full package contract:
- SKILL.md with '## Recommended Workflow' (3-7 numbered steps) and natural-language triggers
- references/examples.md with real, current, working examples
- references/gotchas.md with non-obvious platform behaviour
- references/well-architected.md including '## Official Sources Used' with real URLs
- references/llm-anti-patterns.md with 5+ concrete mistakes AI assistants make here
Reference canonical building blocks in templates/ by relative path rather than duplicating.

Add a BACKLOG.yaml entry for anything you identified but did not build, so it is not lost.
BACKLOG.yaml is 376 KB — append surgically, do not rewrite it.`,
  },
]

const REQ_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    lifecycle_facts_verified: {
      type: 'array',
      description: 'each product-lifecycle claim checked against an official source, with the verdict',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          verdict: { type: 'string', enum: ['CONFIRMED', 'REFUTED', 'PARTIALLY_TRUE', 'UNVERIFIABLE'] },
          official_source_url: { type: 'string' },
          accurate_statement: { type: 'string' },
        },
        required: ['claim', 'verdict', 'official_source_url', 'accurate_statement'],
      },
    },
    deliverables: {
      type: 'array',
      items: {
        type: 'object',
        properties: { path: { type: 'string' }, action: { type: 'string' }, what: { type: 'string' } },
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
  required: ['item_id', 'lifecycle_facts_verified', 'deliverables', 'acceptance_criteria', 'out_of_scope'],
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
    official_sources_used: { type: 'array', items: { type: 'string' } },
    coverage_checks: { type: 'array', description: 'search_knowledge.py output proving a topic was/was not already covered', items: { type: 'string' } },
    claims_refuted: { type: 'array', description: 'orchestrator/lens claims that did NOT hold up on verification', items: { type: 'string' } },
    uncertain_claims: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'official_sources_used', 'coverage_checks', 'claims_refuted', 'uncertain_claims', 'not_done'],
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
        properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } },
        required: ['severity', 'file', 'description'],
      },
    },
    schema_backcompat: { type: 'string', description: 'did any frontmatter change invalidate existing skills? run validate_repo --skills-only on a sample and report' },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'defects', 'schema_backcompat'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    factual_errors: {
      type: 'array',
      items: {
        type: 'object',
        properties: { file: { type: 'string' }, claim: { type: 'string' }, why_wrong: { type: 'string' }, official_source: { type: 'string' }, correction: { type: 'string' } },
        required: ['file', 'claim', 'why_wrong', 'correction'],
      },
    },
    lifecycle_accuracy: { type: 'string', description: 'independent verdict on whether the product-status claims are correct as of 2026-07-31' },
    canon_violations: { type: 'array', items: { type: 'string' } },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'factual_errors', 'lifecycle_accuracy', 'canon_violations', 'required_changes'],
}

phase('Requirements')
log(`Wave 4 currency: ${ITEMS.length} items — lifecycle layer, retired-product flags, 2026 coverage.`)

const results = await pipeline(
  ITEMS,

  (item) => agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for "${item.id}". You SPECIFY ONLY — create and modify nothing.

ITEM: ${item.title}
FILES THIS ITEM OWNS:
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

Your most important job on this wave is VERIFYING THE PRODUCT-LIFECYCLE CLAIMS against
official Salesforce sources before any work is specified. Populate lifecycle_facts_verified
with a verdict and a real URL per claim. A REFUTED claim is a valuable result — say so.`,
    { label: `req:${item.id}`, phase: 'Requirements', schema: REQ_SCHEMA }),

  (spec, item) => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}". Implement the spec. Separate QA and reviewer agents
verify you afterwards.

ITEM: ${item.title}
FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

SPEC (note the verified lifecycle facts — build on those, not on the original claims):
${JSON.stringify(spec, null, 2)}

Run every verify_command. Ground every product claim in an official source and record the URL.
Anything you could not verify goes in uncertain_claims rather than into a file. If a claim the
orchestrator gave you turned out to be wrong, put it in claims_refuted — that is a success,
not a failure.`,
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
2. BACKWARD COMPATIBILITY IS THE MAIN RISK. If frontmatter or its schema changed, confirm
   existing skills are still valid — run
     python3 scripts/validate_repo.py --skills-only --shard 0/8
   and report the real error count. Any NEW error across the untouched corpus is a BLOCKER.
3. If new skills were scaffolded, confirm each has the full package shape (SKILL.md +
   all four references/ files) and that '## Recommended Workflow' has 3-7 numbered steps.
4. Verify the coverage_checks: re-run search_knowledge.py for each topic the builder claimed
   was uncovered and confirm the output really supports that. A skill built on a topic that
   was ALREADY covered is a blocker (it poisons retrieval with a duplicate).
5. git status --short and git diff --stat to confirm the builder stayed in its lane.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  (ctx) => agent(`${COMMON}

YOU ARE THE TECHNICAL REVIEWER for "${ctx.item.id}". You modify nothing.

SPEC:
${JSON.stringify(ctx.spec, null, 2)}
BUILD:
${JSON.stringify(ctx.build, null, 2)}
QA:
${JSON.stringify(ctx.qa, null, 2)}

THIS WAVE IS ABOUT FACTUAL CURRENCY, so your fact-checking IS the deliverable:
1. Read the real diff: cd "${REPO}" && git diff -- <owned paths> plus new files.
2. Independently re-verify EVERY product-lifecycle statement with WebSearch/WebFetch against
   official Salesforce sources: product names, statuses, effective dates, successors. Do not
   trust the builder's or the requirements agent's verification — redo it. A wrong
   deprecation notice actively misleads users and is worse than the stale content it replaced.
3. Check the nuance was preserved: end-of-sale is NOT end-of-support. Any notice implying
   existing implementations are unsupported is a factual error.
4. For new skills: is every API/object/field name real? Verify the important ones.
5. Canon compliance and no hand-edited generated artifacts.
REQUEST_CHANGES on any factual error. Give the official source that contradicts it.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),
)

const done = results.filter(Boolean)
log(`Wave 4 complete: ${done.length}/${ITEMS.length}.`)

return done.map((r) => ({
  item_id: r.item?.id,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  lifecycle_accuracy: r.review?.lifecycle_accuracy,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  claims_refuted: r.build?.claims_refuted,
  official_sources_used: r.build?.official_sources_used,
  uncertain_claims: r.build?.uncertain_claims,
  not_done: r.build?.not_done,
  qa_defects: r.qa?.defects,
  schema_backcompat: r.qa?.schema_backcompat,
  factual_errors: r.review?.factual_errors,
  required_changes: r.review?.required_changes,
}))
