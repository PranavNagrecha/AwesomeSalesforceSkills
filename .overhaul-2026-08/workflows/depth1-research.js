export const meta = {
  name: 'sfskills-depth-research',
  description: 'Establish the quality bar from the repo own best skills, then research authoritative best practices per domain and map each one to a specific skill that should absorb it',
  phases: [
    { title: 'Define the bar' },
    { title: 'Domain research' },
    { title: 'Map to skills' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'
const OUT = SCRATCH + '/depth'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01. NOTE: config/retrieval-config.yaml currently has embeddings.enabled: false
for build-agent memory safety, so a search costs ~2.9 GB and ~6 s. Run searches ONE AT A TIME. 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY WITH RESPECT TO THE REPO. Do NOT create, edit or delete anything under
${REPO}. Write your working notes ONLY under ${OUT}/ (mkdir -p it).
Other agents are actively building in this repo right now; touching it will corrupt their work.

THE GOAL, IN THE OWNER'S WORDS: make this knowledge library "so perfect that no one else in the
world can combine and compete." The moat is not skill count — it is depth per topic that a
generic LLM does not have and that a competitor will not hand-author.

WHAT ALREADY EXISTS (do not propose re-doing it): 1,027 skill packages across 11 domains, each
with SKILL.md + references/{examples,gotchas,well-architected,llm-anti-patterns}.md. The top
~85% is genuinely excellent. Verified weak spots: 111 packages under 15 KB, 48 stub skills
(llm-anti-patterns.md under 600 bytes, all dated 2026-04-28), 196 examples.md with zero code
fences, 149 skills sharing a byte-identical filler "Recommended Workflow", and 972/1,027 still
pinned to salesforce-version "Spring '25+".

NEVER claim a topic is uncovered without pasting real output from
  python3 scripts/search_knowledge.py "<topic>"
This repo is large and things hide under different names. Prior agents have wrongly declared
topics missing more than once; on the last diagnosis 66 of 84 gap claims were refuted.

CRITICAL CONSTRAINT — RETRIEVAL IS ZERO-SUM (measured): the lexical window is 30 chunks. Adding
bulk to one skill can push a NEIGHBOURING skill below the coverage threshold and make it
unreachable. So depth must be DISTINCTIVE — exact error strings, real numeric limits, named
permissions and licences, specific silent-failure modes, version/release caveats — never
generic prose that competes for the same tokens as its neighbours.
`

// ---------------------------------------------------------------------------
phase('Define the bar')

const BAR_SCHEMA = {
  type: 'object',
  properties: {
    exemplars: {
      type: 'array',
      description: 'the repo own best skill packages, with what specifically makes each one good',
      items: {
        type: 'object',
        properties: {
          skill: { type: 'string' },
          why_excellent: { type: 'string' },
          quoted_example: { type: 'string', description: 'a real short quote from the file demonstrating the quality' },
        },
        required: ['skill', 'why_excellent', 'quoted_example'],
      },
    },
    quality_markers: {
      type: 'array',
      description: 'the concrete, checkable properties that separate an excellent skill from an average one',
      items: {
        type: 'object',
        properties: {
          marker: { type: 'string' },
          how_to_detect: { type: 'string', description: 'a command or heuristic that measures presence of this marker' },
          present_in_corpus_pct: { type: 'string' },
        },
        required: ['marker', 'how_to_detect', 'present_in_corpus_pct'],
      },
    },
    anti_pattern_taxonomy: {
      type: 'array',
      description: 'the recurring SHAPES of good llm-anti-patterns entries — this file is the library most differentiated asset',
      items: { type: 'string' },
    },
    scoring_rubric: { type: 'string', description: 'a rubric a builder agent can apply to judge whether new content hits the bar' },
  },
  required: ['exemplars', 'quality_markers', 'anti_pattern_taxonomy', 'scoring_rubric'],
}

log('Mining the repo own best skills to define the quality bar empirically...')

const bar = await agent(`${COMMON}

YOU ARE THE QUALITY-BAR AGENT. Before anyone researches anything, we need to know — from
evidence, not opinion — what "excellent" already looks like in THIS library.

DO THIS:
1. Find the richest packages and read them in full. Start with size as a proxy, then judge:
     for d in skills/*/*/; do echo "$(find "$d" -name '*.md' -exec cat {} + | wc -c) $d"; done | sort -rn | head -30
   Read at least 12 complete packages spanning several domains. Also read 4-5 known-good ones:
   skills/security/data-classification-labels, skills/admin/referral-management-health,
   skills/integration/loyalty-management-setup, and any others you find outstanding.
2. Read 6-8 WEAK packages too (the thin tail) so the contrast is grounded:
     for d in skills/*/*/; do echo "$(find "$d" -name '*.md' -exec cat {} + | wc -c) $d"; done | sort -n | head -20
3. Extract what SPECIFICALLY makes the good ones good. Be concrete. "More detailed" is useless.
   Look for things like: named API/object/field names a model would not know
   (e.g. CareProviderSearchableField), named permission-set licences, exact governor limits
   with numbers, silent-failure modes, "what happens if you don't" consequences, version
   caveats, and anti-patterns that model the LLM's actual failure mode plus a detection hint.
4. Study references/llm-anti-patterns.md across the good tier and derive a TAXONOMY of the
   shapes that work. This file is the library's single most differentiated asset — a
   competitor can copy Salesforce docs but not this. Characterise it precisely.
5. Produce a scoring rubric a builder can actually apply, and quality markers with a
   detection command so we can MEASURE corpus-wide adoption later.

Read files. Do not theorise. Every claim needs a quote or a command.`, {
  label: 'bar:define',
  phase: 'Define the bar',
  schema: BAR_SCHEMA,
  effort: 'high',
})

log(`Quality bar defined: ${(bar?.quality_markers || []).length} markers, ${(bar?.exemplars || []).length} exemplars.`)

// ---------------------------------------------------------------------------
phase('Domain research')

const DOMAINS = [
  {
    key: 'flow',
    label: 'Flow',
    focus: `Record-triggered / screen / scheduled / auto-launched flows, Flow Orchestration.
The owner named Flow explicitly as the example, so this is the pilot — set the standard here.
Best-practice territory to mine: before-save vs after-save record-triggered flows and the
performance difference for same-record field updates; entry criteria vs a Decision element for
skipping work; fault paths on EVERY element that can fail (and what a missing fault path does
in production); bulkification inside loops and the Get/Update-outside-loop discipline; the
per-transaction element limit and interview limits; scheduled-path behaviour and race
conditions; subflow reuse and versioning/activation strategy; Flow-vs-Apex boundaries; testing
flows; error-email noise and how to route it; migrating Workflow Rules / Process Builder;
transaction boundaries and what commits when; ordering when multiple flows fire on one object.`,
  },
  {
    key: 'apex',
    label: 'Apex',
    focus: `Triggers, async (Queueable/Batch/Schedulable/@future/Platform Events), SOQL, security.
Territory: one-trigger-per-object handler discipline and recursion control; bulkification and
the 101-query class of failures; selective queries, custom indexes, and the query-optimiser
thresholds; CPU/heap/DML governor boundaries and how they actually manifest; WITH SECURITY_ENFORCED
vs Security.stripInaccessible vs manual CRUD/FLS checks and when each is correct; with/without
sharing semantics and inherited sharing; async chaining limits and Queueable depth; the modern
Assert class vs legacy System.assertEquals; test data factory discipline and why SeeAllData is
a defect; mocking callouts; Platform Event publish behaviour and retry semantics.`,
  },
  {
    key: 'lwc',
    label: 'LWC',
    focus: `Lightning Web Components.
Territory: reactivity rules and why mutating an object/array in place does not re-render;
@wire vs imperative Apex and when each is right; Lightning Data Service and when LDS avoids
Apex entirely; component communication (parent/child props and events, Lightning Message
Service, pub/sub) and how to choose; performance — rendering cost, lazy instantiation,
lwc:if vs if:true, list virtualisation; accessibility obligations (labels, focus management,
ARIA) since Salesforce enforces these; Locker/Lightning Web Security constraints; Jest testing
patterns; error boundaries; caching and refreshApex/notifyRecordUpdateAvailable semantics.`,
  },
  {
    key: 'data',
    label: 'Data & migration',
    focus: `Data model, migration, large data volumes.
Territory: external IDs and upsert idempotency; load ordering with self- and circular
references; Bulk API 2.0 vs REST vs Data Loader selection and real throughput; parallel vs
serial load modes and lock contention (especially parent-child and Account hierarchies);
skinny tables, custom indexes, and selectivity; LDV thresholds and what actually degrades;
deferred sharing calculation during loads; record-ownership skew and lookup skew — the numbers
where they bite; deduplication and matching-rule behaviour at scale; archival strategy; the
storage model and what counts against it.`,
  },
  {
    key: 'security',
    label: 'Security & sharing',
    focus: `Platform security, sharing, compliance. Highest-consequence domain in the platform —
and measured as the THINNEST (37% of its skills under 15 KB).
Territory: OWD / role hierarchy / sharing rules / manual / team / Apex-managed sharing and the
correct selection order; implicit sharing behaviour that surprises people; permission-set
groups and muting; the real difference between View All / Modify All and View All Data /
Modify All Data; guest-user hardening and the sharing rules that apply to them; Shield Platform
Encryption limits (what you lose: filtering, sorting, some SOQL) and deterministic vs
probabilistic; Event Monitoring and what each event type actually captures; session policies
and high-assurance; connected-app / External Client App auth flows; CRUD-FLS enforcement in
code; secure coding against injection and XSS in Salesforce specifically.`,
  },
  {
    key: 'integration',
    label: 'Integration',
    focus: `Inbound/outbound integration.
Territory: pattern selection (REST, SOAP, Bulk, Platform Events, CDC, Pub/Sub API, Salesforce
Connect / external objects, middleware) and the decision criteria that actually matter —
volume, latency, ordering, delivery guarantees; Named Credentials and External Credentials as
the correct secret-handling mechanism; API limits and how to avoid burning them; idempotency
and replay for event-driven flows; Pub/Sub API replay IDs and retention; error handling,
retry with backoff, and dead-letter patterns; long-running callouts and Continuation; mutual
TLS; webhook signature verification; API versioning and deprecation exposure.`,
  },
]

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    domain: { type: 'string' },
    practices: {
      type: 'array',
      description: 'the best practices worth embedding — each must be specific, checkable and source-grounded',
      items: {
        type: 'object',
        properties: {
          practice: { type: 'string', description: 'stated as an actionable rule' },
          why_it_matters: { type: 'string', description: 'the concrete failure it prevents' },
          specifics: { type: 'string', description: 'the exact numbers, limits, API names, error strings that make this non-generic' },
          official_source_url: { type: 'string' },
          llm_gets_this_wrong: { type: 'string', description: 'how a generic LLM typically gets this wrong — the anti-pattern seed. Empty if the LLM usually gets it right.' },
          already_covered_by: { type: 'string', description: 'the existing skill that covers it, with search_knowledge.py output as proof, or NONE' },
        },
        required: ['practice', 'why_it_matters', 'specifics', 'official_source_url', 'llm_gets_this_wrong', 'already_covered_by'],
      },
    },
    coverage_verification: { type: 'array', description: 'literal search_knowledge.py output backing the already_covered_by judgements', items: { type: 'string' } },
    sources_consulted: { type: 'array', items: { type: 'string' } },
  },
  required: ['domain', 'practices', 'coverage_verification', 'sources_consulted'],
}

log(`Researching best practices across ${DOMAINS.length} domains (Flow first — the owner's example)...`)

// MEMORY: each search_knowledge.py call peaks ~2.9 GB on a 16 GB machine. Running all six
// domains at once would need ~17 GB and OOM the box (it has already been killed once).
// Process in batches of 2 and accumulate.
const research = []
for (let i = 0; i < DOMAINS.length; i += 2) {
  const batch = DOMAINS.slice(i, i + 2)
  log(`Domain research batch ${i / 2 + 1}/${Math.ceil(DOMAINS.length / 2)}: ${batch.map((b) => b.key).join(', ')}`)
  const got = await parallel(batch.map((d) => () => agent(`${COMMON}

THE QUALITY BAR (derived from this repo's own best skills — match it):
${JSON.stringify(bar, null, 2).slice(0, 6000)}

YOU ARE THE ${d.label.toUpperCase()} RESEARCH AGENT. Produce the definitive set of best
practices a senior Salesforce ${d.label} practitioner knows and a generic LLM does not.

TERRITORY TO COVER:
${d.focus}

METHOD:
1. Research authoritative sources with WebSearch/WebFetch. In priority order: official
   Salesforce developer/admin documentation and Well-Architected content, Salesforce Architects
   material, official release notes (Spring '26 / Summer '26 are current — today is 2026-08-01),
   then reputable practitioner sources. Record every URL.
2. For EACH practice, capture the SPECIFICS that make it non-generic: exact limit numbers,
   exact error messages, exact API/object/field/permission names, version boundaries. A
   practice stated as "bulkify your code" is worthless; "a Get Records inside a loop consumes
   one of the 100 SOQL queries per transaction and fails at the 101st with
   System.LimitException: Too many SOQL queries: 101" is the bar.
3. THE MOST VALUABLE FIELD IS 'llm_gets_this_wrong'. For each practice, ask: what does a
   competent LLM actually produce when asked this, and why does it get it wrong? Draw on what
   you know about how models handle Salesforce. These seed the llm-anti-patterns files, which
   are this library's true moat — a competitor can copy Salesforce docs but cannot copy a
   catalogue of how AI fails at Salesforce.
4. CHECK EXISTING COVERAGE before claiming anything is new. For every practice run
     python3 scripts/search_knowledge.py "<the practice in natural language>"
   and record the top hits in already_covered_by, pasting the literal output into
   coverage_verification. Most practices WILL already be covered — that is expected and useful.
   Mark those honestly rather than inflating a gap.
5. Aim for 20-35 high-quality practices. Depth over breadth. Anything you cannot source-ground
   from an official page, leave out or flag explicitly.

Do not write anything into the repo. Notes go under ${OUT}/ only.`, {
  label: `research:${d.key}`,
  phase: 'Domain research',
  schema: RESEARCH_SCHEMA,
  effort: 'high',
})))
  research.push(...got)
}

const goodResearch = research.filter(Boolean)
const totalPractices = goodResearch.reduce((n, r) => n + (r.practices || []).length, 0)
log(`${goodResearch.length} domains researched, ${totalPractices} practices captured.`)

// ---------------------------------------------------------------------------
phase('Map to skills')

const MAP_SCHEMA = {
  type: 'object',
  properties: {
    domain: { type: 'string' },
    absorb: {
      type: 'array',
      description: 'practices that should be added to an EXISTING skill',
      items: {
        type: 'object',
        properties: {
          target_skill: { type: 'string' },
          target_file: { type: 'string', description: 'SKILL.md or references/<which>.md' },
          practice: { type: 'string' },
          why_here: { type: 'string' },
          estimated_added_bytes: { type: 'string' },
        },
        required: ['target_skill', 'target_file', 'practice', 'why_here', 'estimated_added_bytes'],
      },
    },
    new_skills: {
      type: 'array',
      description: 'only where a practice cluster genuinely has no home — justify hard, the corpus is saturated',
      items: {
        type: 'object',
        properties: { proposed_slug: { type: 'string' }, rationale: { type: 'string' }, search_proof: { type: 'string' } },
        required: ['proposed_slug', 'rationale', 'search_proof'],
      },
    },
    agent_upgrades: {
      type: 'array',
      description: 'practices that belong in a run-time AGENT.md playbook rather than a skill',
      items: { type: 'object', properties: { agent: { type: 'string' }, upgrade: { type: 'string' } }, required: ['agent', 'upgrade'] },
    },
    decision_tree_upgrades: { type: 'array', items: { type: 'string' } },
    already_covered_count: { type: 'string' },
    retrieval_risk: { type: 'string', description: 'which skills would grow most, and the zero-sum risk to their neighbours' },
  },
  required: ['domain', 'absorb', 'new_skills', 'agent_upgrades', 'decision_tree_upgrades', 'already_covered_count', 'retrieval_risk'],
}

const mappings = []
for (let i = 0; i < goodResearch.length; i += 2) {
  const batch = goodResearch.slice(i, i + 2)
  log(`Mapping batch ${i / 2 + 1}/${Math.ceil(goodResearch.length / 2)}`)
  const got = await parallel(batch.map((r) => () => agent(`${COMMON}

YOU ARE THE MAPPING AGENT for the ${r.domain} domain. Research is done; your job is to decide
exactly WHERE each practice belongs. You write nothing into the repo — you produce the build plan.

THE RESEARCH:
${JSON.stringify(r, null, 2).slice(0, 24000)}

THE QUALITY BAR:
${JSON.stringify(bar?.scoring_rubric || '', null, 2).slice(0, 2000)}

DO THIS:
1. For every practice, find its correct home. Read the candidate skill before assigning to it —
   confirm the practice genuinely belongs there and is not already present. Assign to the most
   specific file:
     - a hard rule or procedure -> SKILL.md
     - working code / config -> references/examples.md
     - non-obvious platform behaviour or a trap -> references/gotchas.md
     - an LLM failure mode -> references/llm-anti-patterns.md   <- prioritise these, it is the moat
     - a pillar/trade-off framing -> references/well-architected.md
2. Skip anything already_covered_by an existing skill UNLESS the existing treatment is
   materially thinner than the research. If you propose absorbing something already covered,
   quote the existing text and say what is missing from it.
3. Propose a NEW skill only where a cluster genuinely has no home. The corpus is saturated at
   1,027 skills — the default answer is absorb, not create. Every new_skills entry needs
   literal search_knowledge.py output as proof.
4. Some practices belong in an AGENT playbook (how the agent should behave) rather than a
   skill (what is true). Route those to agent_upgrades. Likewise route technology-choice
   criteria to standards/decision-trees/.
5. RETRIEVAL RISK: total the estimated bytes per target skill. Flag any skill that would grow
   by more than ~30%, and name the neighbouring skills that could be starved out of the
   30-chunk window. This directly shapes how the build wave is sequenced.

Be ruthless about relevance. A practice bolted onto a loosely-related skill hurts retrieval for
both.`, {
  label: `map:${r.domain}`,
  phase: 'Map to skills',
  schema: MAP_SCHEMA,
  effort: 'high',
})))
  mappings.push(...got)
}

const goodMaps = mappings.filter(Boolean)
const totalAbsorb = goodMaps.reduce((n, m) => n + (m.absorb || []).length, 0)
const totalNew = goodMaps.reduce((n, m) => n + (m.new_skills || []).length, 0)
log(`Build plan ready: ${totalAbsorb} absorptions, ${totalNew} proposed new skills, across ${goodMaps.length} domains.`)

return {
  quality_bar: bar,
  research: goodResearch,
  build_plan: goodMaps,
  totals: { practices: totalPractices, absorb: totalAbsorb, new_skills: totalNew },
}
