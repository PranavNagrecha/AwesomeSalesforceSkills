export const meta = {
  name: 'sfskills-fabrication-hunt',
  description: 'Corpus-wide hunt for fabricated Salesforce facts: verify every quoted error string, numeric limit, API identifier and named permission across all 1,027 skills against official documentation',
  phases: [{ title: 'Hunt' }],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const OUT = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad/fabhunt'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY. Create/edit/delete NOTHING under ${REPO}. Notes go only under ${OUT}/.
Other agents are building in this repo right now — touching it corrupts their work.

*** MEMORY RULE — MANY AGENTS RUN IN PARALLEL ON A 16 GB MACHINE ***
DO NOT run scripts/search_knowledge.py (peaks ~2.9 GB), validate_repo.py, skill_sync.py or
build_index.py. Use grep, ls, sed, awk and file reads — all cheap. WebSearch/WebFetch are your
primary verification tool and cost no local memory.

WHY THIS EXISTS. A depth-research pass over 6 of 11 domains found this library asserting
Salesforce facts that DO NOT EXIST:
  - 'MULTIPLE_CHOICES' as an upsert StatusCode — appears 9 times including inside a checker
    script's user-facing message. Not a real Salesforce StatusCode for that condition.
  - 'EXTERNAL_ID_NON_UNIQUE' — invented.
  - 'InvalidBatch — relationship Who is polymorphic, type required' — invented.
  - A 'Who.Lead.External_Id__c' CSV header syntax propagated across a SKILL.md, its gotchas,
    its anti-patterns, its template AND its validator script.
  - 'expected.equals(signature)' presented as a CONSTANT-TIME comparison in a webhook
    signature-verification skill. String.equals short-circuits — the library was teaching a
    timing side-channel as a defence against one.
  - Inverted mechanisms: subflow version resolution stated backwards; two Apex skills claiming
    you cannot call @future from a Queueable when an allocation of 50 is documented.

Those were found by accident, in the 6 domains a research pass happened to cover. NOBODY HAS
CHECKED THE OTHER ~1,000 SKILLS. That is your job.

WHY IT MATTERS MORE THAN ANYTHING ELSE HERE: this library exists so an AI produces Salesforce
work a generic model cannot. A confidently-stated fake error string or invented API name is
worse than silence — a practitioner ships it to production, and the whole premise of the
product is that it is RIGHT about Salesforce. One fabricated security control costs more trust
than a hundred missing skills.

VERIFICATION STANDARD — be rigorous in BOTH directions:
- CONFIRMED_FABRICATION: you searched official Salesforce documentation and the identifier /
  error string / limit does not exist, or exists with a materially different meaning. Cite the
  official page you checked.
- LIKELY_WRONG: strong evidence it is wrong but you could not find a definitive page.
- UNVERIFIABLE: you could not settle it either way. This is a legitimate outcome — say so.
- CORRECT: you checked and it is right. REPORT THESE TOO. A precision number matters: if you
  check 40 claims and 37 are correct, that is important evidence about corpus health and
  protects the next agent from over-correcting.
DO NOT flag something as fabricated because it merely looks unfamiliar. The previous diagnosis
had 66 of 84 claims REFUTED on verification — over-flagging is the common failure mode here.
`

const SCHEMA = {
  type: 'object',
  properties: {
    slice: { type: 'string' },
    claims_checked: { type: 'string', description: 'how many distinct claims you extracted and how many you verified' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          verdict: { type: 'string', enum: ['CONFIRMED_FABRICATION', 'LIKELY_WRONG', 'UNVERIFIABLE', 'CORRECT'] },
          severity: { type: 'string', enum: ['security', 'data-loss', 'misleading', 'cosmetic'] },
          file: { type: 'string', description: 'path:line' },
          claim: { type: 'string', description: 'the exact text as it appears in the repo' },
          claim_type: { type: 'string', enum: ['error-string', 'numeric-limit', 'api-identifier', 'permission-or-licence', 'mechanism', 'product-name'] },
          why_wrong: { type: 'string' },
          official_source_checked: { type: 'string', description: 'the URL you actually opened' },
          correct_value: { type: 'string', description: 'what it should say, if you could establish it' },
          occurrences: { type: 'string', description: 'how many places in the corpus repeat this claim (grep count)' },
        },
        required: ['verdict', 'severity', 'file', 'claim', 'claim_type', 'why_wrong', 'official_source_checked'],
      },
    },
    retired_product_mentions: { type: 'array', description: 'content describing products that are retired or renamed as of 2026', items: { type: 'string' } },
    corpus_health_note: { type: 'string', description: 'honest assessment of this slice: mostly sound, or systemically unreliable' },
  },
  required: ['slice', 'claims_checked', 'findings', 'retired_product_mentions', 'corpus_health_note'],
}

const SLICES = [
  { key: 'apex', dirs: 'skills/apex', note: '158 skills. Highest density of governor limits, exception names and StatusCodes. Prioritise: System.LimitException texts, limit NUMBERS (SOQL 100/queries, DML 150, CPU 10s sync / 60s async, heap 6MB/12MB, callouts 100, @future 50, Queueable depth), and Security/Schema API identifiers.' },
  { key: 'admin', dirs: 'skills/admin', note: '253 skills — the largest domain. Prioritise: per-object caps (roll-up summaries, field history tracking, validation rules, picklist values), licence and permission names, and Setup UI paths that may have been renamed in Lightning.' },
  { key: 'data', dirs: 'skills/data', note: '101 skills. Prioritise: Bulk API batch sizes and job limits, StatusCode strings on load failures, LDV thresholds, skew thresholds (the specific record counts), and index/selectivity numbers.' },
  { key: 'integration', dirs: 'skills/integration', note: '61 skills. Prioritise: API limits, Platform Event / CDC delivery allocations and retention windows, replay-ID semantics, composite API sub-request caps, OAuth flow names, Named Credential field names. NOTE a security defect was already found in webhook-inbound-patterns — check its neighbours for the same class of error.' },
  { key: 'security', dirs: 'skills/security', note: '48 skills. HIGHEST STAKES — a wrong security control is the worst possible defect. Prioritise: permission names (View All vs View All Data), Shield encryption limits and what it breaks, session policy settings, guest-user rules, and ANY cryptographic code (constant-time comparison, hashing, signing). Read every code fence involving crypto.' },
  { key: 'lwc', dirs: 'skills/lwc', note: '82 skills. Prioritise: decorator and lifecycle-hook names, LDS/wire adapter identifiers, Lightning Web Security vs Locker claims, component size/perf numbers, and base-component attribute names.' },
  { key: 'flow', dirs: 'skills/flow', note: '63 skills. Prioritise: element/interview limits, the order-of-execution position claims, scheduled-path behaviour, fault-path mechanics. NOTE inverted mechanisms were already found here (subflow version resolution, a non-existent fault mechanism) — treat mechanism claims with suspicion.' },
  { key: 'architect-devops', dirs: 'skills/architect skills/devops', note: '174 skills. Prioritise: org-wide 24-hour limits, edition-specific caps, package/deployment behaviour, test-level names and the coverage rule, sf CLI command syntax (heavily renamed from sfdx — flag stale command forms).' },
  { key: 'agentforce-omni', dirs: 'skills/agentforce skills/omnistudio', note: '87 skills. Prioritise: Agentforce/Einstein product naming (renamed repeatedly through 2025-2026 — verify current names), Trust Layer guarantees, feature licence names, and OmniStudio timeout/caching numbers. Flag anything describing a superseded Einstein product as current.' },
]

phase('Hunt')
log(`Fabrication hunt across ${SLICES.length} corpus slices, in parallel.`)

const results = await parallel(SLICES.map((s) => () => agent(`${COMMON}

YOU ARE THE FABRICATION HUNTER FOR: ${s.key.toUpperCase()}  (${s.dirs})
${s.note}

METHOD — extract cheaply first, then verify expensively:
1. EXTRACT candidate claims with grep. Useful starting points (adapt them):
     grep -rhoE '\\b[A-Z][A-Z0-9_]{6,}\\b' ${s.dirs} | sort | uniq -c | sort -rn | head -60
       (SCREAMING_CASE = StatusCodes, exception names, limit names — the richest vein)
     grep -rnE '\\b[0-9]{1,3}(,[0-9]{3})+\\b|\\b[0-9]+ ?(MB|GB|KB|seconds|minutes|hours|records|rows|queries|calls)\\b' ${s.dirs} | head -60
       (numeric limits)
     grep -rnoE '\\b[A-Za-z]+__(c|r|e|mdt|b|x)\\b' ${s.dirs} | sort -u | head -40
       (custom-object/field API names — invented ones hide here)
     grep -rniE 'permission set license|permission-set licence|feature licen|user licen' ${s.dirs} | head -40
     grep -rnE '\`[A-Z][A-Za-z]+\\.[A-Za-z]+\\(' ${s.dirs} | head -40
       (Apex API calls — verify the method actually exists)
2. TRIAGE. You cannot verify everything. Rank by damage-if-wrong:
   security/crypto claims > data-loss claims (limits that govern a load) > mechanism claims >
   cosmetic. Prefer claims that are REPEATED across many files (grep -c), because a fabrication
   that propagated is both more damaging and more valuable to catch.
3. VERIFY the top candidates against official Salesforce documentation with WebFetch. Open the
   actual page. Aim to verify AT LEAST 30-40 distinct claims properly rather than skimming 200.
4. For every finding, record the exact file:line, the verbatim claim, the official page you
   checked, and the correct value where you can establish it. Run a grep to count how many
   places repeat the claim — propagation count drives fix priority.
5. Report CORRECT verdicts too, so the precision of this sweep is measurable.
6. Note any content describing a RETIRED or RENAMED product as current (Salesforce renames
   constantly; Spring '26 / Summer '26 are current).

Be honest in corpus_health_note. If your slice is largely sound, say so plainly — that is a
valuable result and prevents a destructive over-correction pass.`, {
  label: `hunt:${s.key}`, phase: 'Hunt', schema: SCHEMA, effort: 'high',
})))

const good = results.filter(Boolean)
const all = good.flatMap((r) => r.findings || [])
const fab = all.filter((f) => f.verdict === 'CONFIRMED_FABRICATION')
const likely = all.filter((f) => f.verdict === 'LIKELY_WRONG')
const ok = all.filter((f) => f.verdict === 'CORRECT')
const sec = all.filter((f) => f.severity === 'security' && f.verdict !== 'CORRECT')

log(`Checked across ${good.length} slices: ${fab.length} CONFIRMED fabrications, ${likely.length} likely wrong, ${ok.length} verified correct, ${sec.length} security-severity.`)

return {
  slices: good.map((r) => ({ slice: r.slice, claims_checked: r.claims_checked, health: r.corpus_health_note, retired: r.retired_product_mentions })),
  confirmed_fabrications: fab,
  likely_wrong: likely,
  security_severity: sec,
  verified_correct_count: ok.length,
  totals: { confirmed: fab.length, likely: likely.length, correct: ok.length, security: sec.length },
}
