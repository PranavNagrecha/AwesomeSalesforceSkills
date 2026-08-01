export const meta = {
  name: 'sfskills-max-verify',
  description: 'Maximum-breadth verification sweep: the unverified vertical skills, the decision trees that agents read first, the canonical order of execution, and the Agentforce research that failed',
  phases: [{ title: 'Sweep' }],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const OUT = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad/max1'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01 (Summer '26, API 67.0). 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY. Create/edit/delete NOTHING under ${REPO}. Notes only under ${OUT}/.

*** MEMORY RULE — ~15 AGENTS IN PARALLEL ON A 16 GB MACHINE ***
DO NOT run scripts/search_knowledge.py (~2.9 GB peak), validate_repo.py, skill_sync.py or
build_index.py. Use grep/ls/sed/awk/file reads only — cheap. WebSearch/WebFetch are your main
tool and cost no local memory.

CONTEXT — WHAT PRIOR SWEEPS ESTABLISHED (assume as fact, do not re-derive):
- This library asserts fabricated Salesforce facts. A hunt over 9 slices confirmed **76
  fabrications**, 54 likely-wrong, against 75 verified-correct.
- **The failure signature is number-RELABELLING, not number-invention**: a REAL Salesforce
  number attached to the WRONG dimension. Historical Trending's "8" is the Classic
  trackable-field count relabelled as snapshot dates (real: 5). Report export "2,000" is the
  on-screen display cap relabelled as an export cap (real: 100,000). SO: RE-READ THE SOURCE
  PAGE, never just swap a digit.
- **COUNTER-WARNING**: several numbers that look obviously hallucinated are CORRECT — the
  131,021-character Data Cloud SQL limit, the 9,950-segment org cap, the 3-writeback-field
  Einstein Discovery limit. NEVER flag a specific-looking number without opening the page.
- Fabricated identifiers usually sit inside a CORRECT explanation: the author knew the
  mechanism and confabulated a plausible name for it. Keep the prose, fix the identifier.
- Verified removals this release: \`WITH SECURITY_ENFORCED\` is REMOVED at API 67.0 (compiler:
  "WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead"); database
  operations default to user mode at 67.0+; user mode GA'd Spring '23 = API 57.0.

REPORT CORRECT VERDICTS TOO. A precision number protects the corpus from a destructive
over-correction pass. Over-flagging is the known failure mode here — a prior diagnosis had
66 of 84 claims REFUTED on verification.
`

const SCHEMA = {
  type: 'object',
  properties: {
    area: { type: 'string' },
    checked: { type: 'string', description: 'how many claims extracted, triaged, and verified' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          verdict: { type: 'string', enum: ['CONFIRMED_FABRICATION', 'LIKELY_WRONG', 'UNVERIFIABLE', 'CORRECT', 'STALE_PRODUCT'] },
          severity: { type: 'string', enum: ['security', 'data-loss', 'misleading', 'cosmetic'] },
          file: { type: 'string', description: 'path:line' },
          claim: { type: 'string' },
          why_wrong: { type: 'string' },
          official_source_checked: { type: 'string' },
          correct_value: { type: 'string' },
        },
        required: ['verdict', 'severity', 'file', 'claim', 'why_wrong', 'official_source_checked'],
      },
    },
    new_practices: {
      type: 'array',
      description: 'best practices worth embedding that the corpus lacks',
      items: {
        type: 'object',
        properties: {
          practice: { type: 'string' },
          specifics: { type: 'string' },
          verbatim_error_string: { type: 'string' },
          gating_licence_or_permission: { type: 'string' },
          llm_gets_this_wrong: { type: 'string' },
          official_source_url: { type: 'string' },
          target_skill: { type: 'string' },
        },
        required: ['practice', 'specifics', 'llm_gets_this_wrong', 'official_source_url', 'target_skill'],
      },
    },
    health_note: { type: 'string' },
  },
  required: ['area', 'checked', 'findings', 'new_practices', 'health_note'],
}

const AREAS = [
  { k: 'vert-fsc', p: `VERIFY THE FINANCIAL SERVICES CLOUD SKILLS. A prior hunt flagged all vertical skills as almost entirely UNVERIFIED, carrying "plausible, precise, repeated" numbers. Find them: ls skills/*/ | grep -iE "fsc|financial|wealth|insurance|banking". Extract every numeric limit, permission-set-licence name, custom object/field API name (grep -rhoE '[A-Za-z]+__(c|r|e|mdt)' ) and verify against official FSC documentation. FSC ships a large managed-package object model — verify object and field API names actually exist in the FSC data model, and verify the permission set licences by their exact names.` },
  { k: 'vert-health', p: `VERIFY THE HEALTH CLOUD SKILLS. ls skills/*/ | grep -iE "health|hc-|clinical|patient|provider|fhir|care". A prior hunt specifically flagged unverified claims like "30 FHIR bundle entries", "HealthCloudICM permission set", and CareProviderSearchableField behaviour. Verify every numeric limit, permission-set-licence name and object/field API name against official Health Cloud documentation. Health Cloud renames aggressively — check current product/feature naming too.` },
  { k: 'vert-npsp-edu', p: `VERIFY THE NONPROFIT AND EDUCATION SKILLS. ls skills/*/ | grep -iE "npsp|nonprofit|education|eda|donor|grant|student|admissions". IMPORTANT CONTEXT: Salesforce has moved NPSP/EDA toward Nonprofit Cloud and Education Cloud built on the core platform — verify which product each skill is actually describing and whether it presents a superseded architecture as current. Verify object/field API names (npsp__, hed__ namespaces) and any stated limits.` },
  { k: 'vert-commerce-fsl', p: `VERIFY THE COMMERCE AND FIELD SERVICE SKILLS. ls skills/*/ | grep -iE "commerce|b2b|b2c|storefront|cart|fsl|field-service|scheduling|dispatch". Prior hunt flagged "2,000 BuyerGroups per product" and "1,000 Briefcase page references" as unverified, and noted "Field Service Lightning" used as the product name when it has been "Salesforce Field Service" for several releases. Verify limits, object/field API names, and product naming.` },
  { k: 'vert-marketing', p: `VERIFY THE MARKETING SKILLS. ls skills/*/ | grep -iE "marketing|mcae|pardot|journey|email-studio|campaign|engagement". CRITICAL CONTEXT: a prior audit found all 24 marketing skills teach Marketing Cloud Engagement / Pardot while Marketing Cloud Next (Growth + Advanced) has zero coverage. Verify (a) which product each skill actually describes, (b) whether it presents a superseded product as current, (c) every stated limit and API name. Establish the CURRENT official product naming — this family has been renamed repeatedly.` },
  { k: 'trees-automation', p: `AUDIT standards/decision-trees/automation-selection.md AND flow-pattern-selector.md LINE BY LINE. These are the HIGHEST-LEVERAGE files in the repo: standards/decision-trees/README.md:43 instructs agents to cite the tree BEFORE reading any skill, so a defect here overrides correct skill content inside an agent's context window. Confirmed defects to verify and extend: a fabricated "2,000-element execution limit per interview" (~:87); a dead branch where Q3 preempts Q6 on callouts; two different coverage gates 70 lines apart (:54 vs :126); scheduled-flow thresholds 5x apart between the two trees; flow-pattern-selector.md:56 self-contradicting inside one question (<50k vs <250k); and two cited skills that do not resolve (flow/record-triggered-flows, agentforce/agent-creation). Verify EVERY factual claim and EVERY skill reference in both files (ls skills/<domain>/<slug>/SKILL.md for each). Propose the corrected tree content.` },
  { k: 'trees-rest', p: `AUDIT THE REMAINING DECISION TREES line by line: standards/decision-trees/async-selection.md, integration-pattern-selection.md, sharing-selection.md, agentforce-capability-selector.md, performance-tuning.md. Agents read these BEFORE skills, so defects here are maximally damaging. sharing-selection.md is already known to carry a wrong "restriction rules are a security boundary" claim. Verify every numeric threshold, every mechanism claim and every skill reference (confirm each cited skill path exists with ls). Propose corrected content per tree.` },
  { k: 'order-of-exec', p: `REBUILD THE CANONICAL SALESFORCE ORDER OF EXECUTION and map the corpus against it. The corpus is written against STALE numbering: the old text collapsed before-save flows and before triggers into one step, which produced a corpus-wide FALSE claim that before-save-flow vs before-trigger ordering is indeterminate — and an llm-anti-patterns entry that TRAINS consuming agents to "detect and correct" the truth. Fetch the CURRENT Apex Developer Guide "Triggers and Order of Execution" page and write out the authoritative numbered list verbatim. Then grep the corpus for every step-number claim (grep -rnE 'step [0-9]+|Step [0-9]+' skills/apex skills/flow skills/admin | head -80) and list every file:line that contradicts the current list. This single deliverable fixes 5+ known findings.` },
  { k: 'agentforce-redo', p: `AGENTFORCE BEST-PRACTICE RESEARCH — this agent's predecessor FAILED with a server error, so Agentforce is the only un-researched area. Research the CURRENT (Summer '26) Agentforce surface: agent topics and classification, why topic overlap causes misrouting, custom actions via Apex/Flow and the invocable contract, grounding and how record access applies to an agent's queries, prompt templates and Prompt Builder, the Einstein Trust Layer (masking, zero-retention, audit) and what it does and does NOT guarantee, prompt-injection defence specific to Salesforce, agent testing/evaluation, and production readiness. NAME THE EXACT feature licences and permission sets that gate agent features. Verify current product naming — this family renamed repeatedly through 2025-2026. Check existing coverage cheaply (ls skills/agentforce/, grep) and mark each practice covered or NONE.` },
  { k: 'evals-design', p: `DESIGN THE GOLDEN EVAL EXPANSION. Read evals/README.md, evals/framework.md and 3-4 existing files under evals/golden/ to learn the exact format. Measured problem: golden evals cover 10 of 1,027 skills (1.0%) across only 4 of 11 domains, and nothing runs them in CI. Design eval cases for the highest-value UNCOVERED domains — admin, security, data, architect, agentforce, devops, omnistudio. For each proposed case give: the skill under test, the prompt, the assertions (mechanically checkable), the rubric, and what a WRONG answer looks like. Ground the "wrong answer" in the real fabrications this project found — e.g. an eval that fails if the model emits WITH SECURITY_ENFORCED on an API 67 class, or asserts "View Encrypted Data" gates plaintext. Produce ready-to-write case content, not a plan.` },
  { k: 'omnistudio-depth', p: `OMNISTUDIO DEEP RESEARCH — measured as the single biggest opportunity in the library: 26 of 27 researched practices were UNCOVERED, it is the thinnest domain (24.7 KB median package vs 40 KB corpus median), and it had no run-time agent until this session. Research authoritative OmniStudio practice: OmniScript design/versioning/activation; FlexCards data sources, actions and the LWC compilation model; DataRaptor Extract/Transform/Load/Turbo and when Turbo cannot be used; Integration Procedures chainable vs standalone, caching, and the sync/async boundary with REAL timeout numbers; Business Rules Engine and calculation matrices; DataPack deployment and cross-org migration pain; performance and governor interaction; and when NOT to use OmniStudio. Verify current productisation and naming. For each practice: specifics, verbatim error strings, gating licences, what an LLM gets wrong, and the existing skills/omnistudio/<slug> it should be absorbed into (verify the path exists).` },
  { k: 'security-depth', p: `SECURITY DEEP RESEARCH + VERIFICATION. Security is the highest-consequence domain and measured as one of the thinnest (37% of its skills under 15 KB). A prior hunt found FOUR security-severity defects including one claiming the "View Encrypted Data" permission gates plaintext (it does not — Shield is transparent to anyone with field read access) and one listing HmacSHA384 as supported (Apex supports only MD5/SHA1/SHA256/SHA512). VERIFY the rest of skills/security/ with the same lens: every permission name, every crypto claim, every encryption limit, every session/guest-user rule. Read EVERY code fence involving crypto or access control. Then research the best practices the domain is missing, naming exact permissions and licences.` },
  { k: 'data-depth', p: `DATA + LDV DEEP RESEARCH AND VERIFICATION. Research and verify: skew thresholds with the REAL record counts, sharing recalculation triggers and duration, deferred sharing maintenance, skinny tables and custom index eligibility, query selectivity thresholds, Bulk API 2.0 vs 1.0 real behaviour and the 200-row trigger transaction, load ordering with circular references, external-id upsert idempotency and the REAL StatusCode for an ambiguous match, archival and storage model. Verify each against official docs, then list the practices skills/data/ lacks with their target skill path (verify it exists).` },
  { k: 'lwc-depth', p: `LWC DEEP RESEARCH AND VERIFICATION. Verify every decorator/lifecycle-hook name, wire-adapter identifier, Lightning Web Security vs Locker claim, and base-component attribute name in skills/lwc/ against official docs. Then research the practices the domain lacks: reactivity rules and why in-place mutation does not re-render, @wire vs imperative Apex selection, LDS and when it avoids Apex entirely, component communication selection (props/events vs LMS vs pub-sub), performance (rendering cost, lazy instantiation, lwc:if vs if:true, list virtualisation), accessibility obligations Salesforce enforces, Jest patterns, and refreshApex/notifyRecordUpdateAvailable semantics. Give target skill paths (verify they exist).` },
]

phase('Sweep')
log(`Max verification + research sweep: ${AREAS.length} areas in parallel.`)

const res = await parallel(AREAS.map((a) => () => agent(`${COMMON}

YOUR AREA: ${a.k.toUpperCase()}

${a.p}

METHOD:
1. Extract candidates cheaply with grep/ls first. Useful veins:
     grep -rhoE '\\b[A-Z][A-Z0-9_]{6,}\\b' <dir> | sort | uniq -c | sort -rn | head -50
     grep -rnE '\\b[0-9]{1,3}(,[0-9]{3})+\\b|\\b[0-9]+ ?(MB|GB|seconds|minutes|records|rows|queries|calls)\\b' <dir> | head -60
     grep -rnoE '\\b[A-Za-z]+__(c|r|e|mdt|b|x)\\b' <dir> | sort -u | head -40
2. Triage by damage-if-wrong: security > data-loss > misleading > cosmetic. Prefer claims
   REPEATED across files — propagation multiplies both damage and fix value.
3. VERIFY against official Salesforce documentation with WebFetch. Open the actual page.
   Verify 25-40 claims properly rather than skimming 200.
4. Record CORRECT verdicts too — the precision number matters.
5. Then produce new_practices: what should be embedded that is not. Every practice needs
   specifics (a number, an identifier, an error string, a named licence) or drop it.
   Name a target skill path and verify it exists with ls.
6. Be honest in health_note about coverage and about what you could not verify.`,
  { label: `max:${a.k}`, phase: 'Sweep', schema: SCHEMA, effort: 'high' })))

const good = res.filter(Boolean)
const f = good.flatMap((r) => r.findings || [])
const np = good.flatMap((r) => r.new_practices || [])
log(`${good.length}/${AREAS.length} areas. ${f.length} findings (${f.filter((x) => x.verdict === 'CONFIRMED_FABRICATION').length} fabrications, ${f.filter((x) => x.verdict === 'CORRECT').length} correct, ${f.filter((x) => x.severity === 'security').length} security). ${np.length} new practices.`)

return {
  areas: good.map((r) => ({ area: r.area, checked: r.checked, health: r.health_note })),
  findings: f,
  new_practices: np,
  totals: {
    findings: f.length,
    fabrications: f.filter((x) => x.verdict === 'CONFIRMED_FABRICATION').length,
    stale_product: f.filter((x) => x.verdict === 'STALE_PRODUCT').length,
    correct: f.filter((x) => x.verdict === 'CORRECT').length,
    security: f.filter((x) => x.severity === 'security').length,
    new_practices: np.length,
  },
}
