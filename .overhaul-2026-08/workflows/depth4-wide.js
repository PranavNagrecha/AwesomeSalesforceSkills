export const meta = {
  name: 'sfskills-depth-wide',
  description: 'Wide parallel best-practice research: the six declarative admin atoms plus the five domains depth-1 did not cover, using memory-light coverage checks so eleven agents can run at once',
  phases: [{ title: 'Wide research' }],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'
const OUT = SCRATCH + '/depth-wide'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY WITH RESPECT TO THE REPO. Create/edit/delete NOTHING under ${REPO}.
Notes go only under ${OUT}/ (mkdir -p it). Other agents are building in this repo right now.

*** MEMORY RULE — ELEVEN AGENTS ARE RUNNING IN PARALLEL ON A 16 GB MACHINE ***
DO NOT RUN scripts/search_knowledge.py. One invocation peaks at ~2.9 GB; eleven would kill the
box (it has already been OOM-killed once on this project). Use these CHEAP coverage checks
instead — they are nearly free and sufficient for "does a skill about X already exist":

  ls skills/*/ | grep -i "<term>"
  ls -d skills/*/*"<term>"* 2>/dev/null
  grep -ril "<term>" --include=SKILL.md skills/ | head -20
  python3 -c "import json;d=json.load(open('registry/skills.json'));rs=d if isinstance(d,list) else d.get('skills',[]);[print(r.get('id') or r.get('name'), '|', (r.get('description') or '')[:110]) for r in rs if '<term>' in json.dumps(r).lower()][:15]"

Also DO NOT run validate_repo.py, skill_sync.py or build_index.py. WebSearch/WebFetch are fine
and are your primary tool — they cost no local memory.

THE GOAL, IN THE OWNER'S WORDS: make this library "so perfect that no one else in the world can
combine and compete." The moat is NOT skill count — it is depth a generic LLM does not have and
a competitor will not hand-author.

THE QUALITY BAR, measured from this repo's own best packages. Two markers are badly
under-served corpus-wide and are where the leverage is:
  - VERBATIM PLATFORM ERROR STRINGS — present in only 11.0% of 1,027 skills. Biggest upside.
  - THE EXACT LICENCE / PERMISSION SET / PERMISSION-SET-LICENCE that gates a feature —
    present in only 8.4%. Second biggest.
Also valued: exact numeric limits, named API/object/field identifiers, silent-failure modes,
"what happens if you don't", and version/release caveats.

The standard, from a real skill in this repo:
  BAD : "use a clear naming convention for fields"
  GOOD: "Without the Data Pipelines Base User permission set license, the DPE job that
         populates CareProviderSearchableField fails silently and provider search returns
         zero results."
If a practice has no specific — no number, no identifier, no error string, no named licence —
it is not worth embedding. Drop it.

NEVER claim something is uncovered without pasting real output from one of the cheap checks
above. This corpus has 1,027 skills and hides things under other names; a recent diagnosis had
66 of 84 "gap" claims REFUTED. Assume covered until your grep proves otherwise.

CRITICAL — RETRIEVAL IS ZERO-SUM (measured): the lexical window is 30 chunks and the per-package
ceiling is ~50 KB. Adding bulk to one skill can starve a neighbour. So depth must be
DISTINCTIVE, never generic prose.

VERIFY CURRENT PRODUCT NAMES. Salesforce renames and retires constantly (Spring '26 / Summer '26
are current). Do not describe a retired product as current.
`

const SCHEMA = {
  type: 'object',
  properties: {
    area: { type: 'string' },
    practices: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          practice: { type: 'string', description: 'an actionable rule' },
          specifics: { type: 'string', description: 'the exact numbers, API/metadata names, error strings, licences — the non-generic part' },
          why_it_matters: { type: 'string' },
          irreversible: { type: 'boolean', description: 'true if getting it wrong is hard/impossible to undo — highest value' },
          verbatim_error_string: { type: 'string', description: 'the literal platform message a user sees, if any. Empty if none.' },
          gating_licence_or_permission: { type: 'string', description: 'the exact licence/permission/org preference that gates it, if any' },
          official_source_url: { type: 'string' },
          llm_gets_this_wrong: { type: 'string', description: 'what a competent LLM actually outputs here and why it is wrong — the anti-pattern seed' },
          already_covered_by: { type: 'string', description: 'existing skill id, or NONE — must be backed by a cheap-check result' },
        },
        required: ['practice', 'specifics', 'why_it_matters', 'irreversible', 'official_source_url', 'llm_gets_this_wrong', 'already_covered_by'],
      },
    },
    coverage_evidence: { type: 'array', description: 'literal output of the cheap coverage checks backing already_covered_by', items: { type: 'string' } },
    suggested_targets: { type: 'array', description: 'existing skill package each uncovered practice should be absorbed into, verified to exist', items: { type: 'string' } },
    stale_or_wrong_found: { type: 'array', description: 'anything you noticed in the corpus that looks factually wrong or describes a retired product', items: { type: 'string' } },
    sources_consulted: { type: 'array', items: { type: 'string' } },
  },
  required: ['area', 'practices', 'coverage_evidence', 'suggested_targets', 'stale_or_wrong_found', 'sources_consulted'],
}

const AREAS = [
  { key: 'fields', label: 'Custom fields', focus: `The most common admin action. Data type permanence (Text vs Long Text Area vs Rich Text and their filtering/reporting/SOQL consequences; Number vs Currency vs Percent precision; Picklist vs Multi-Select and why multi-select is a reporting trap; Date vs Date/Time timezone behaviour). API-name immutability in practice and exactly what breaks on rename that Salesforce does NOT cascade (formulas, flows, reports, Apex, integrations). Required-at-field vs validation rule vs page-layout-required — only one is enforced via the API. Unique / External ID / case sensitivity and upsert idempotency. Indexing: what is auto-indexed, custom indexes, selectivity thresholds, why an unindexed filter times out on a large object. Formula fields: compile-size limit, cross-object spanning limits, list-view/report cost, formulas referencing formulas. Roll-Up Summary: master-detail only, per-object cap, recalculation. Field history tracking: per-object cap, what is not captured, retention. FLS defaults on creation. Deletion vs deprecation and the restore window. Field limits per object by edition.` },
  { key: 'perms', label: 'Profiles, permission sets, permission set groups', focus: `Minimum-access profile + permission sets + PSGs, and the CURRENT state of Salesforce's profile-retirement direction (verify against official sources; do not assert from memory). What can ONLY live on a profile (login hours, login IP ranges, page layout assignment, record type default). Muting permission sets and evaluation order across multiple sources. Permissions are additive, never subtractive. View All / Modify All (object) vs View All Data / Modify All Data (org-wide, bypasses sharing). Permission set licences vs user licences vs feature licences. The three-layer model: object permissions vs FLS vs record access, and the order they apply. Custom permissions in formulas/validation rules/Apex. Delegated administration boundaries. Session-based permission sets. Deployment ordering failures when permission sets deploy before the fields they reference. How to actually answer "who can see this field" and "why does this user have this".` },
  { key: 'objects', label: 'Objects, relationships, record types, layouts', focus: `Custom object design: naming, record name field Text vs Auto Number and the consequences of Auto Number for search and data loads. Master-detail vs Lookup: ownership/sharing inheritance, cascade delete, roll-up eligibility, reparenting, per-object master-detail cap, conversion between them and when it is blocked. Junction objects and which relationship is primary. External objects and Salesforce Connect boundaries. Record types: what they legitimately control vs what people misuse them for, interaction with profiles/permission sets, record-type proliferation as technical debt. Page layouts vs Dynamic Forms vs Compact layouts. List views and search layouts, list view sharing. Object limits by edition and the cost of very wide objects.` },
  { key: 'logic', label: 'Validation rules, picklists, duplicate rules, approvals', focus: `Validation rules: position in the order of execution and what has already happened when they fire; that they also fire on API/data loads (a very common surprise); bypass via custom permission or hierarchy custom setting; error location; per-object cap; how an over-strict rule blocks migrations. THE FULL SALESFORCE ORDER OF EXECUTION — almost every declarative bug traces to it; where before/after flows, validation rules, assignment rules, workflow field updates, roll-ups and sharing recalculation sit relative to each other. Picklists: global value sets vs local, restricted picklists, deactivating vs deleting a value and the effect on existing records and reports, per-picklist limits, dependent picklists, ISPICKVAL/TEXT. Duplicate management: matching vs duplicate rules, fuzzy vs exact, behaviour on API inserts, cost at scale. Approval processes: entry criteria, record locking, recall, delegated approvers, dynamic routing, and the CURRENT status of Approval Processes vs newer orchestration (verify). Assignment and auto-response rules: evaluation order, single-active-rule model.` },
  { key: 'users', label: 'Users, roles, sharing setup, queues, groups', focus: `User setup: licence types, deactivate vs freeze, why users cannot be deleted, and what to do with their records (ownership transfer, running-user dependencies on dashboards/reports/scheduled jobs). Integration users and the modern integration-user licence; why a human's account must not be an integration identity. Role hierarchy: what it actually controls, why it is NOT an org chart, practical role-count limits, cost of deep hierarchies on sharing recalculation. OWD selection and the precedence order OWD -> role hierarchy -> sharing rules -> teams -> manual -> Apex managed; Grant Access Using Hierarchies for custom objects. Public groups vs queues vs teams. Ownership skew and lookup skew: the record-count thresholds where lock contention starts, and mitigations. Sharing recalculation triggers, duration on large orgs, deferred sharing maintenance. Territory management vs role hierarchy. Access reviews.` },
  { key: 'reporting', label: 'Reports, dashboards, folders, governance', focus: `Report types: standard vs custom, with/without related records, and how the wrong report type silently hides data. Filters, cross filters, bucketing, row-level formulas and their limits; joined reports. Report performance on large data volumes: selective filters, timeout behaviour, what makes a report un-runnable. Dashboards: running user (as-me / as-specified / dynamic), dynamic-dashboard caps by edition, refresh limits, scheduling. Folder sharing and the access model; folder sprawl as a governance problem. Historical trending and reporting snapshots and their limits. Org-wide governance: naming conventions, change control, sandbox-before-production, documenting config decisions, deprecate-then-delete, periodic access review. Setup Audit Trail: what it captures and its retention limit.` },
  { key: 'devops', label: 'DevOps and release engineering', focus: `Source-tracked vs source-linked orgs; scratch org definition files and shape. Unlocked vs managed vs 2GP packaging, package versioning and ancestry, what cannot be removed from a released package. Deployment: metadata API vs source deploy, destructive changes, deployment ordering dependencies, why permission sets/profiles deploy last. Test levels (NoTestRun, RunSpecifiedTests, RunLocalTests, RunAllTestsInOrg) and the SILENT DEFAULT for sandbox vs production deploys. The 75% coverage rule and what actually counts. CI/CD: sf CLI auth via JWT, secret handling, deployment validation vs quick deploy. DevOps Center vs sfdx workflows. Rollback strategy — Salesforce has no true rollback, so what people actually do. Environment/sandbox refresh strategy and what does not copy.` },
  { key: 'architect', label: 'Architecture, limits and scale', focus: `Governor limits as an architecture input, not a coding detail: the per-transaction limits, the 24-hour rolling limits, and which are shared org-wide. Large data volume thresholds: where skinny tables, custom indexes, selectivity and query plans start to matter. Ownership and lookup skew thresholds. Multi-org vs single-org strategy and the real decision criteria. Tenant isolation, Hyperforce implications, data residency. HA/DR realities on Salesforce. Licensing as an architectural constraint. Technical debt assessment. The Limits API and how to check rather than guess. When to choose declarative vs programmatic vs off-platform (Heroku/AppLink). API request allocation and how it is actually consumed.` },
  { key: 'agentforce', label: 'Agentforce and Einstein', focus: `Agentforce agent design: topics, classification, and why topic overlap causes misrouting. Custom actions via Apex/Flow and the invocable contract. Grounding: what data an agent can and cannot see, and how record access applies to an agent's queries. Prompt templates and Prompt Builder; the Einstein Trust Layer (masking, zero retention, audit) and what it does and does not guarantee. Guardrails and prompt injection defence specific to Salesforce. Agent testing and evaluation. Deployment/production readiness. Current Spring '26 / Summer '26 Agentforce surface — verify what actually shipped and its exact current naming. Einstein feature licences and permission sets that gate agent features (name them exactly).` },
  { key: 'omnistudio', label: 'OmniStudio', focus: `OmniScript design, versioning and activation. FlexCards: data sources, actions, and the LWC compilation model. DataRaptors: Extract/Transform/Load/Turbo, and when Turbo cannot be used. Integration Procedures: chainable vs standalone, caching, and the sync/async boundary with its real timeout numbers. Business Rules Engine / calculation procedures and matrices. DataPack deployment and the migration pain points between orgs. Performance: what makes an OmniScript slow, caching layers, and governor interaction. The standard-vs-OmniStudio decision (when NOT to use it). NOTE: OmniStudio is the THINNEST domain in this library (median package 24.7 KB vs 40 KB corpus median) so depth here has outsized value. Also verify current productisation/naming.` },
  { key: 'service', label: 'Service Cloud and Experience Cloud', focus: `Case management: assignment rules, escalation rules and their evaluation order; Email-to-Case and Web-to-Case limits and failure modes; Omni-Channel routing (distinct from OmniStudio) — presence, capacity model, skills-based routing. Entitlements, milestones and business hours interaction. Knowledge: article types, data categories, publishing lifecycle, search behaviour. Experience Cloud: guest user hardening (a repeated real-world breach source — name the exact settings), sharing sets, audience targeting, LWR vs Aura sites, and performance. Service Cloud Voice basics. Case merge and duplicate handling. Verify current product naming.` },
]

phase('Wide research')
log(`Wide depth research: ${AREAS.length} areas in parallel (web-research heavy, memory-light).`)

const results = await parallel(AREAS.map((a) => () => agent(`${COMMON}

YOU ARE THE RESEARCH AGENT FOR: ${a.label.toUpperCase()}.

TERRITORY:
${a.focus}

METHOD:
1. Research with WebSearch/WebFetch. Priority: official Salesforce admin/developer docs and
   Well-Architected content, Salesforce Architects material, current release notes, then
   reputable practitioner sources. Record every URL.
2. Capture SPECIFICS or drop the practice. Populate verbatim_error_string and
   gating_licence_or_permission wherever they exist — those are the two measured gaps in this
   library and the highest-value thing you can return.
3. Mark 'irreversible' honestly. Decisions that cannot be undone later — API names, master-detail
   vs lookup, Auto Number record names, field data type, package release contents — are the
   highest-value practices here, because that is exactly where an AI's confident wrong answer
   costs someone months.
4. 'llm_gets_this_wrong' IS THE MOST VALUABLE FIELD. What does a competent LLM actually output
   for this, and why is it wrong? These seed references/llm-anti-patterns.md, which is this
   library's real moat — anyone can copy Salesforce docs; a catalogue of how AI fails at
   Salesforce is not copyable.
5. Check existing coverage with the CHEAP checks only (never search_knowledge.py) and paste the
   literal output into coverage_evidence. Most practices WILL already be covered — report that
   honestly rather than inflating gaps. For anything genuinely uncovered, name an EXISTING
   skill package it should be absorbed into and verify that package exists with ls.
6. If you notice existing corpus content that is factually WRONG or describes a retired
   product, record it in stale_or_wrong_found — a recent pass found fabricated error strings
   and inverted mechanisms shipping in this library, so this is a live concern.
7. Aim for 18-30 high-quality practices. Depth over breadth. Drop anything you cannot
   source-ground.`, { label: `wide:${a.key}`, phase: 'Wide research', schema: SCHEMA, effort: 'high' })))

const good = results.filter(Boolean)
const total = good.reduce((n, r) => n + (r.practices || []).length, 0)
const irrev = good.reduce((n, r) => n + (r.practices || []).filter((p) => p.irreversible).length, 0)
const errs = good.reduce((n, r) => n + (r.practices || []).filter((p) => p.verbatim_error_string).length, 0)
const lics = good.reduce((n, r) => n + (r.practices || []).filter((p) => p.gating_licence_or_permission).length, 0)
const uncovered = good.reduce((n, r) => n + (r.practices || []).filter((p) => (p.already_covered_by || '').toUpperCase() === 'NONE').length, 0)
const stale = good.reduce((n, r) => n + (r.stale_or_wrong_found || []).length, 0)

log(`${good.length}/${AREAS.length} areas. ${total} practices | ${irrev} irreversible | ${errs} with verbatim error strings | ${lics} with named licences | ${uncovered} uncovered | ${stale} stale/wrong findings`)

return {
  areas: good,
  totals: { areas: good.length, practices: total, irreversible: irrev, with_error_string: errs, with_licence: lics, uncovered, stale_or_wrong: stale },
}
