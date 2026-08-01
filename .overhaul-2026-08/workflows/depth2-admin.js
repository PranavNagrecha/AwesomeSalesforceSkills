export const meta = {
  name: 'sfskills-depth-admin',
  description: 'Best-practice research for the declarative admin atoms — the everyday work: fields, objects, profiles, permission sets, record types, layouts, validation rules, picklists, users, reports, approvals',
  phases: [
    { title: 'Atom research' },
    { title: 'Map to skills' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'
const OUT = SCRATCH + '/depth-admin'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY WITH RESPECT TO THE REPO. Do NOT create, edit or delete anything under
${REPO}. Working notes go ONLY under ${OUT}/ (mkdir -p it).
Other agents are actively building in this repo right now; touching it corrupts their work.

WHY THIS WAVE EXISTS. The owner's point: "there are best practices while creating a field, a
profile, a permission and so much more." These declarative atoms are the highest-traffic work
in Salesforce — an admin creates fields every week — and they carry enormous non-obvious
practice that a generic LLM does not have. admin is also the LARGEST domain in this library
(253 of 1,027 skills), so the leverage here is the highest of anywhere.

THE STANDARD (from this repo's own best skills). Generic advice is worthless. The bar is:
  BAD : "use a clear naming convention for fields"
  GOOD: "the API name is immutable after creation in practice — renaming it breaks every
         formula, flow, report filter, Apex reference and integration mapping that points at
         it; Salesforce does not cascade the rename to Apex or to external systems"
  GOOD: "a Roll-Up Summary field only works from the DETAIL side of a master-detail
         relationship; lookup relationships cannot be rolled up declaratively"
Every practice must carry the exact numbers, exact API/metadata names, exact error strings,
and the exact consequence. If you cannot source-ground it officially, leave it out.

NEVER claim a topic is uncovered without pasting real output from
  python3 scripts/search_knowledge.py "<topic>"
The corpus is saturated and things hide under other names. On the last diagnosis 66 of 84 gap
claims were REFUTED. Assume it is already covered until search proves otherwise.

RETRIEVAL IS ZERO-SUM (measured): the lexical window is 30 chunks. Bulking one skill can push a
neighbour below the coverage threshold. Depth must be DISTINCTIVE, never generic padding.
`

const ATOMS = [
  {
    key: 'fields',
    label: 'Custom fields',
    focus: `The single most common admin action. Territory:
- Data type selection and its permanence: Text vs Long Text Area vs Rich Text (filtering,
  reporting, search and SOQL consequences); Number vs Currency vs Percent precision/scale;
  Picklist vs Multi-Select Picklist (and why multi-select is a reporting and querying trap);
  Checkbox vs Picklist for tri-state data; Date vs Date/Time and timezone behaviour.
- API naming: immutability in practice, the __c suffix, namespace behaviour, what breaks on
  rename (formulas, flows, reports, Apex, integrations) and what Salesforce does NOT cascade.
- Description and help text as a governance obligation, not decoration.
- Required-at-field-level vs validation rule vs page-layout-required: the three are different
  and only one is enforced everywhere (API included).
- Unique, External ID, and case sensitivity — and their role in upsert idempotency.
- Indexing: which fields are indexed automatically, what a custom index is, selectivity
  thresholds, and why an unindexed filter on a large object times out.
- Formula fields: compile size limit, nesting, cross-object formula spanning limits,
  the performance cost of formulas in list views and reports, and formula fields that
  reference other formula fields.
- Roll-Up Summary: master-detail only, the per-object cap, filter criteria, and why they
  recalculate.
- Field history tracking: the per-object cap, what is and is not captured, retention.
- Field-Level Security defaults on creation and the profile/permission-set implications.
- Deletion vs deprecation: the restore window, what deletion breaks, and why deprecate-then-
  remove is the safe pattern.
- Field limits per object by edition, and how field count affects page-layout and query cost.`,
  },
  {
    key: 'perms',
    label: 'Profiles, permission sets, permission set groups',
    focus: `Territory:
- The modern model: minimum-access profile + permission sets + permission set groups, and
  Salesforce's own direction of travel on profiles. Verify the CURRENT state of profile
  deprecation/retirement plans against official sources — do not assert from memory.
- What can ONLY live on a profile (login hours, login IP ranges, page layout assignment,
  record type default) vs what belongs on a permission set.
- Permission set groups and muting permission sets: how muting resolves, and the evaluation
  order when a user has several sources.
- Permissions are additive and never subtractive — the single most common misconception.
- The difference between View All / Modify All (object-level) and View All Data / Modify All
  Data (org-wide), and why the latter bypasses sharing entirely.
- Permission set licences vs user licences vs feature licences.
- Object permissions vs FLS vs record access: the three-layer model and the order it applies.
- Custom permissions and how they are consumed in formulas, validation rules and Apex.
- Delegated administration and its boundaries.
- Session-based permission sets.
- Deployment ordering and what breaks when permission sets deploy before the objects/fields
  they reference.
- Auditing: how to actually answer "who can see this field" and "why does this user have this".`,
  },
  {
    key: 'objects',
    label: 'Objects, relationships, record types, layouts',
    focus: `Territory:
- Custom object design: naming, plural labels, record name field (Text vs Auto Number) and
  the consequences of Auto Number for user searchability and data loads.
- Master-detail vs Lookup: ownership and sharing inheritance, cascade delete, roll-up
  eligibility, reparenting, the per-object master-detail cap, and converting between them
  (and when conversion is blocked).
- Junction objects for many-to-many, and which relationship is primary.
- External objects and Salesforce Connect boundaries.
- Record types: what they legitimately control (picklist values, page layout, business
  process) vs what people misuse them for; the interaction with profiles/permission sets;
  record type proliferation as a known technical-debt pattern.
- Page layouts vs Dynamic Forms vs Compact layouts; the Lightning record page and when
  layout assignment still governs; field-level required on layout vs field vs validation.
- List views and search layouts; list view sharing.
- Object-level limits by edition and the practical cost of very wide objects.`,
  },
  {
    key: 'logic',
    label: 'Validation rules, picklists, duplicate/matching rules, approvals',
    focus: `Territory:
- Validation rules: order of execution position and what has already happened when they fire;
  why they also fire on API/data loads and integrations (a very common surprise); bypass
  patterns via custom permission or hierarchy custom setting; error location (field vs top of
  page); the per-object cap; and why an over-strict rule blocks migrations.
- The Salesforce order of execution end-to-end, since almost every declarative bug traces to
  it — where before/after flows, validation rules, assignment rules, workflow field updates,
  roll-ups and sharing recalculation sit relative to each other.
- Picklists: global value sets vs local; restricted picklists; deactivating vs deleting a
  value and what happens to existing records; the reporting consequences of inactive values;
  the per-picklist and per-org value limits; dependent picklists and their controlling-field
  constraints; picklist values in formulas (ISPICKVAL/TEXT).
- Duplicate management: matching rules vs duplicate rules, fuzzy vs exact matching, the
  behaviour on API/data-load inserts, and the performance cost at scale.
- Approval processes: entry criteria, initial submitters, record locking behaviour, recall,
  delegated approvers, dynamic approval routing, and the migration path given Salesforce's
  current direction (verify the CURRENT status of Approval Processes vs newer orchestration
  against official sources).
- Assignment rules and auto-response rules: evaluation order and the single-active-rule model.`,
  },
  {
    key: 'users',
    label: 'Users, roles, sharing setup, queues, groups',
    focus: `Territory:
- User setup: licence types, the difference between deactivating and freezing, why users
  cannot be deleted, and what to do with their records (ownership transfer, running-user
  dependencies on dashboards/reports/flows/scheduled jobs).
- Integration users and the modern integration-user licence; why a named human's account
  should never be an integration identity.
- Role hierarchy: what it actually controls (record access rollup and reporting), why it is
  NOT an org chart, role-count practical limits, and the cost of deep hierarchies on sharing
  recalculation.
- OWD selection and the consequence order: OWD -> role hierarchy -> sharing rules -> teams ->
  manual -> Apex managed. Grant Access Using Hierarchies for custom objects.
- Public groups vs queues vs teams: what each is for and how they compose.
- Ownership skew and lookup skew: the record-count thresholds where they start causing lock
  contention, and the mitigation.
- Sharing recalculation: when it is triggered, how long it takes on large orgs, deferred
  sharing maintenance during loads.
- Territory management basics and when it is the right answer over role hierarchy.
- License/permission auditing and access reviews.`,
  },
  {
    key: 'reporting',
    label: 'Reports, dashboards, folders, and admin governance',
    focus: `Territory:
- Report types: standard vs custom, with/without related records, and why the wrong report
  type silently hides data.
- Filters, cross filters, bucketing, row-level formulas and their limits; joined reports.
- Report performance on large data volumes: selective filters, the timeout behaviour, and
  what makes a report un-runnable.
- Dashboards: running user (as-me vs as-specified vs dynamic), the dynamic-dashboard cap by
  edition, refresh limits and scheduling.
- Folder sharing and the access model; why report/dashboard folder sprawl is a real
  governance problem.
- Historical trending and reporting snapshots and their limits.
- Governance practices an admin should apply org-wide: naming conventions, a change-control
  process, sandbox usage before production config, documenting config decisions, the
  deprecate-then-delete discipline, and periodic access review.
- Setup Audit Trail: what it captures, its retention limit, and why that limit matters.`,
  },
]

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    atom: { type: 'string' },
    practices: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          practice: { type: 'string', description: 'stated as an actionable rule an admin can follow' },
          specifics: { type: 'string', description: 'exact numbers, limits, metadata/API names, error strings, consequences — the part that makes it non-generic' },
          why_it_matters: { type: 'string', description: 'the concrete failure it prevents' },
          irreversible: { type: 'boolean', description: 'true if getting this wrong is hard or impossible to undo later — these are the highest-value practices' },
          official_source_url: { type: 'string' },
          llm_gets_this_wrong: { type: 'string', description: 'what a competent LLM actually produces here and why it is wrong. Empty if LLMs usually get it right.' },
          already_covered_by: { type: 'string', description: 'existing skill id, or NONE — must be backed by search output' },
        },
        required: ['practice', 'specifics', 'why_it_matters', 'irreversible', 'official_source_url', 'llm_gets_this_wrong', 'already_covered_by'],
      },
    },
    order_of_execution_notes: { type: 'string', description: 'anything this atom depends on in the Salesforce order of execution' },
    coverage_verification: { type: 'array', description: 'literal search_knowledge.py output backing already_covered_by', items: { type: 'string' } },
    sources_consulted: { type: 'array', items: { type: 'string' } },
  },
  required: ['atom', 'practices', 'coverage_verification', 'sources_consulted'],
}

phase('Atom research')
log(`Researching ${ATOMS.length} declarative admin atoms — the everyday work.`)

const research = await parallel(ATOMS.map((a) => () => agent(`${COMMON}

YOU ARE THE RESEARCH AGENT FOR: ${a.label.toUpperCase()}.

TERRITORY:
${a.focus}

METHOD:
1. Research with WebSearch/WebFetch, priority order: official Salesforce admin/developer
   documentation, Salesforce Well-Architected and Architects content, current release notes
   (Spring '26 / Summer '26 — today is 2026-08-01), then reputable practitioner sources.
   Record every URL. Salesforce renames and retires constantly — verify CURRENT product and
   feature names rather than relying on memory.
2. Capture SPECIFICS. Exact caps and limits with numbers, exact metadata/API names, exact
   error messages, and the exact consequence of getting it wrong. A practice without a
   specific is not worth embedding.
3. Mark 'irreversible' honestly. Decisions that are painful or impossible to undo later — API
   names, master-detail vs lookup, Auto Number record names, field data type — are the
   highest-value practices in this whole exercise, because that is exactly where an AI
   assistant's confident wrong answer costs someone months.
4. 'llm_gets_this_wrong' IS THE MOST VALUABLE FIELD. For each practice, what does a competent
   LLM actually output when asked, and why is it wrong? These seed references/llm-anti-patterns.md,
   which is this library's real moat — anyone can copy Salesforce docs; a catalogue of how AI
   fails at Salesforce is not copyable.
5. CHECK EXISTING COVERAGE for every practice:
     python3 scripts/search_knowledge.py "<practice in natural language>"
   Record the top hits in already_covered_by and paste literal output into
   coverage_verification. Most WILL be covered — report that honestly, do not inflate gaps.
6. Aim for 20-35 practices. Depth over breadth. Drop anything you cannot source-ground.

Write nothing into the repo. Notes under ${OUT}/ only.`, {
  label: `admin:${a.key}`,
  phase: 'Atom research',
  schema: RESEARCH_SCHEMA,
  effort: 'high',
})))

const good = research.filter(Boolean)
const total = good.reduce((n, r) => n + (r.practices || []).length, 0)
const irreversible = good.reduce((n, r) => n + (r.practices || []).filter((p) => p.irreversible).length, 0)
log(`${good.length} atoms researched, ${total} practices, ${irreversible} flagged irreversible.`)

phase('Map to skills')

const MAP_SCHEMA = {
  type: 'object',
  properties: {
    atom: { type: 'string' },
    absorb: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          target_skill: { type: 'string' },
          target_file: { type: 'string' },
          practice: { type: 'string' },
          why_here: { type: 'string' },
          estimated_added_bytes: { type: 'string' },
        },
        required: ['target_skill', 'target_file', 'practice', 'why_here', 'estimated_added_bytes'],
      },
    },
    new_skills: { type: 'array', items: { type: 'object', properties: { proposed_slug: { type: 'string' }, rationale: { type: 'string' }, search_proof: { type: 'string' } }, required: ['proposed_slug', 'rationale', 'search_proof'] } },
    agent_upgrades: { type: 'array', items: { type: 'object', properties: { agent: { type: 'string' }, upgrade: { type: 'string' } }, required: ['agent', 'upgrade'] } },
    already_covered_count: { type: 'string' },
    retrieval_risk: { type: 'string' },
    highest_value_additions: { type: 'array', description: 'the 5 additions that would most improve real-world output quality, ranked', items: { type: 'string' } },
  },
  required: ['atom', 'absorb', 'new_skills', 'agent_upgrades', 'already_covered_count', 'retrieval_risk', 'highest_value_additions'],
}

const maps = await parallel(good.map((r) => () => agent(`${COMMON}

YOU ARE THE MAPPING AGENT for ${r.atom}. Research is done; decide exactly WHERE each practice
belongs. You write nothing into the repo — you produce the build plan.

RESEARCH:
${JSON.stringify(r, null, 2).slice(0, 24000)}

DO THIS:
1. Find each practice's correct home. READ the candidate skill before assigning — confirm the
   practice belongs there and is not already present. Route by file:
     hard rule / procedure          -> SKILL.md
     working config or code         -> references/examples.md
     non-obvious behaviour, a trap  -> references/gotchas.md
     an LLM failure mode            -> references/llm-anti-patterns.md   (PRIORITISE — the moat)
     trade-off / pillar framing     -> references/well-architected.md
   Relevant admin skills to consider include admin/custom-field-creation,
   admin/object-creation-and-design, admin/permission-set-architecture,
   admin/permission-sets-vs-profiles, admin/validation-rules, admin/picklist-and-value-sets,
   admin/record-type-strategy-at-scale, admin/user-management, admin/duplicate-management,
   admin/approval-processes, admin/reports-and-dashboards — but VERIFY each path exists
   (ls skills/admin/ | grep ...) before assigning to it.
2. Skip anything already covered UNLESS the existing treatment is materially thinner. If you
   propose absorbing something already present, quote the existing text and say what is missing.
3. Propose a NEW skill only where a cluster genuinely has no home. The corpus is saturated —
   default to absorb. Every new_skills entry needs literal search_knowledge.py proof.
4. Route behavioural guidance (how an agent should ACT) to agent_upgrades rather than a skill
   (what is TRUE). Relevant agents: object-designer, permission-set-architect,
   field-impact-analyzer, analyze-field-impact, migrate-profile-to-permset, design-object.
5. RETRIEVAL RISK: total estimated bytes per target skill; flag any skill growing more than
   ~30% and name the neighbours that could be starved from the 30-chunk window.
6. Rank the 5 highest-value additions — the ones that would most change real-world output
   quality for a working admin. Prioritise irreversible-decision practices.`, {
  label: `map:${r.atom}`,
  phase: 'Map to skills',
  schema: MAP_SCHEMA,
  effort: 'high',
})))

const goodMaps = maps.filter(Boolean)
log(`Admin build plan: ${goodMaps.reduce((n, m) => n + (m.absorb || []).length, 0)} absorptions across ${goodMaps.length} atoms.`)

return {
  research: good,
  build_plan: goodMaps,
  totals: {
    practices: total,
    irreversible,
    absorb: goodMaps.reduce((n, m) => n + (m.absorb || []).length, 0),
    new_skills: goodMaps.reduce((n, m) => n + (m.new_skills || []).length, 0),
  },
}
