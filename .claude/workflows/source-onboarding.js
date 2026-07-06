export const meta = {
  name: 'source-onboarding',
  description: 'Onboard an external source (repo/attachment/topic) into the skill library: verify vs official docs, gate, scaffold, author, adversarial review',
  whenToUse: 'After scripts/onboard_source.py produced an intake report. Pass args {report: "<path to intake report JSON>"}. Models are pinned: Sonnet for research/extraction/scaffolding, Opus for gate/authoring/review — never override to a larger tier.',
  phases: [
    { title: 'Load', detail: 'transcribe the intake report', model: 'sonnet' },
    { title: 'Verify', detail: 'official-docs fact sheet per candidate', model: 'sonnet' },
    { title: 'Gate', detail: 'build/enrich/drop decisions on deterministic evidence', model: 'opus' },
    { title: 'Scaffold', detail: 'serial new_skill.py runs (avoids AGENT.md races)', model: 'sonnet' },
    { title: 'Author', detail: 'one author per skill, official docs only', model: 'opus' },
    { title: 'Review', detail: 'adversarial fact-check per skill', model: 'opus' },
    { title: 'Fix', detail: 'apply blocker fixes', model: 'opus' },
  ],
}

// ---------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------
const a = typeof args === 'string' ? JSON.parse(args) : (args || {})
const REPORT = a.report
if (!REPORT) throw new Error('args.report (path to intake report JSON from scripts/onboard_source.py) is required')
const MAX_VERIFY = a.maxVerify || 12
const MAX_BUILD = a.maxBuild || 6
const EXEMPLAR = 'skills/agentforce/agentforce-custom-lightning-types'

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const LOADED = {
  type: 'object',
  required: ['source', 'mode', 'license', 'license_class', 'candidates'],
  properties: {
    source: { type: 'string' },
    mode: { type: 'string' },
    license: { type: 'string' },
    license_class: { type: 'string', enum: ['permissive', 'clean-room'] },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'topic', 'classification', 'local_hits'],
        properties: {
          id: { type: 'string' },
          topic: { type: 'string' },
          classification: { type: 'string' },
          query: { type: 'string' },
          local_hits: { type: 'array', items: { type: 'object', properties: { skill: { type: 'string' }, score: { type: 'number' } } } },
        },
      },
    },
  },
}

const FACTSHEET = {
  type: 'object',
  required: ['id', 'is_real_capability', 'capability_name', 'ga_status', 'official_urls', 'facts', 'recommendation', 'rationale'],
  properties: {
    id: { type: 'string' },
    is_real_capability: { type: 'boolean' },
    capability_name: { type: 'string' },
    ga_status: { type: 'string', description: 'GA/Beta/Pilot/Developer Preview exactly as docs state, or "unstated"' },
    official_urls: { type: 'array', items: { type: 'string' } },
    facts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'source_url'],
        properties: { claim: { type: 'string' }, source_url: { type: 'string' }, quote: { type: 'string' } },
      },
    },
    gaps_vs_local_skill: { type: 'string' },
    attribution_required: { type: 'boolean', description: 'true only if any expression was adapted from a permissive source (then name it in rationale)' },
    recommendation: { type: 'string', enum: ['NET_NEW', 'ENRICH', 'DROP'] },
    rationale: { type: 'string' },
  },
}

const GATE_OUT = {
  type: 'object',
  required: ['build', 'enrich', 'drop'],
  properties: {
    build: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'domain', 'slug', 'wiring'],
        properties: {
          id: { type: 'string' },
          domain: { type: 'string', description: 'one of the repo skill domains (admin|apex|lwc|flow|omnistudio|agentforce|security|integration|data|devops|architect)' },
          slug: { type: 'string', description: 'kebab-case skill name' },
          wiring: { type: 'string', description: 'either "--agent <id>" (repeatable, space-separated) or \'--runtime-orphan --orphan-reason "<why>"\' — agent ids must exist under agents/' },
          rationale: { type: 'string' },
        },
      },
    },
    enrich: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'skill_path'],
        properties: { id: { type: 'string' }, skill_path: { type: 'string', description: 'existing skills/<domain>/<slug> to extend' }, rationale: { type: 'string' } },
      },
    },
    drop: { type: 'array', items: { type: 'object', required: ['id', 'reason'], properties: { id: { type: 'string' }, reason: { type: 'string' } } } },
  },
}

const AUTHOR_OUT = {
  type: 'object',
  required: ['skill_path', 'files_written', 'official_sources', 'query_fixtures', 'notes'],
  properties: {
    skill_path: { type: 'string' },
    files_written: { type: 'array', items: { type: 'string' } },
    official_sources: { type: 'array', items: { type: 'string' } },
    query_fixtures: {
      type: 'array',
      items: {
        type: 'object',
        required: ['query', 'domain', 'expected_skill', 'top_k'],
        properties: { query: { type: 'string' }, domain: { type: 'string' }, expected_skill: { type: 'string' }, top_k: { type: 'number' } },
      },
    },
    notes: { type: 'string' },
  },
}

const REVIEW_OUT = {
  type: 'object',
  required: ['skill_path', 'verdict', 'issues'],
  properties: {
    skill_path: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'FAIL'] },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'problem', 'severity'],
        properties: { file: { type: 'string' }, problem: { type: 'string' }, severity: { type: 'string', enum: ['blocker', 'minor'] } },
      },
    },
    checked_urls: { type: 'array', items: { type: 'string' } },
  },
}

const SCAFFOLD_OUT = {
  type: 'object',
  required: ['results'],
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        required: ['slug', 'ok', 'skill_path'],
        properties: { slug: { type: 'string' }, ok: { type: 'boolean' }, skill_path: { type: 'string' }, error: { type: 'string' } },
      },
    },
  },
}

// ---------------------------------------------------------------------------
// Rule blocks shared across prompts
// ---------------------------------------------------------------------------
function sourceRules(licenseClass, source) {
  if (licenseClass === 'clean-room') {
    return `SOURCE-ACCESS RULE (clean-room — the source "${source}" is NOT license-compatible):
- NEVER fetch, read, quote, paraphrase, or search for content from ${source} or mirrors of it. You may know only the topic names, which derive from file paths.
- All facts must come from official Salesforce properties: developer.salesforce.com, help.salesforce.com, architect.salesforce.com, trailhead.salesforce.com, *.salesforce.com release notes and blogs.`
  }
  return `SOURCE-ACCESS RULE (permissive license — "${source}"):
- You MAY read the source content for orientation, but the source is NOT a source of truth: every Salesforce behavior claim must be confirmed against an official Salesforce doc you actually fetch (developer/help/architect/trailhead .salesforce.com).
- Rewrite everything in your own words. If you deliberately adapt the source's expression (not just facts), set attribution_required=true and name the file — the orchestrator records attribution.`
}

const HOUSE_RULES = `Repo root is the current working directory. HARD RULES:
- Load WebFetch/WebSearch via ToolSearch ("select:WebFetch,WebSearch") before web access.
- Do NOT run scripts/skill_sync.py, scripts/validate_repo.py, or scripts/build_*.py, and do NOT edit registry/, vector_index/, or docs/ (the orchestrator syncs once at the end).
- Never state a GA/Beta/Pilot maturity official docs do not state. No secrets in output. Match repo house style.
`

// ---------------------------------------------------------------------------
// Phase 1 — Load the intake report (agents have file access; the script does not)
// ---------------------------------------------------------------------------
phase('Load')
const report = await agent(
  `Read the JSON file at ${REPORT} and transcribe it into the required schema EXACTLY as written in the file — do not editorialize, reclassify, or drop fields. candidates[].local_hits and .classification must be copied verbatim.`,
  { label: 'load-report', phase: 'Load', schema: LOADED, model: 'sonnet', effort: 'low' }
)
if (!report) throw new Error('could not load intake report')
log(`${report.source} (${report.license}, ${report.license_class}) — ${report.candidates.length} candidates`)

const actionable = report.candidates.filter(c => c.classification === 'NET_NEW' || c.classification === 'ENRICH')
const covered = report.candidates.filter(c => c.classification === 'COVERED')
if (actionable.length > MAX_VERIFY) log(`Capping verification at ${MAX_VERIFY} of ${actionable.length} actionable candidates — re-run with {maxVerify} raised to cover the rest`)
const toVerify = actionable.slice(0, MAX_VERIFY)
if (toVerify.length === 0) {
  log('Nothing actionable — every candidate is COVERED by the local catalog.')
  return { source: report.source, built: [], enriched: [], dropped: covered.map(c => ({ id: c.id, reason: 'COVERED: ' + JSON.stringify(c.local_hits) })) }
}

// ---------------------------------------------------------------------------
// Phase 2 — Verify each candidate against official docs (Sonnet fan-out)
// ---------------------------------------------------------------------------
phase('Verify')
const sheets = (await parallel(toVerify.map(c => () =>
  agent(
    `${HOUSE_RULES}
${sourceRules(report.license_class, report.source)}

You are verifying whether a Salesforce topic deserves a new skill (or an enrichment) in this library.
Candidate id: ${c.id}
Topic: ${c.topic}
Deterministic local-coverage evidence (search_knowledge.py, authoritative — do not re-litigate): ${JSON.stringify(c.local_hits)} → classification ${c.classification}

1. Research the topic in official Salesforce docs. Determine whether it is a real, current, distinct capability. If you cannot find official documentation, set is_real_capability=false and recommendation=DROP — never fabricate.
2. If classification is ENRICH: READ the top local skill file(s) listed in the evidence and fill gaps_vs_local_skill with what official docs cover that the local skill lacks. Recommend ENRICH only for material gaps; DROP if covered.
3. If NET_NEW: gather an authoring-grade fact sheet (8+ facts, each with the URL you fetched and a short quote under 25 words).
4. State maturity exactly as docs state it.`,
    { label: `verify:${c.id}`, phase: 'Verify', schema: FACTSHEET, model: 'sonnet' }
  ).then(s => s && { ...s, id: c.id })
))).filter(Boolean)
log(`${sheets.length}/${toVerify.length} fact sheets returned`)

// ---------------------------------------------------------------------------
// Phase 3 — Gate (Opus, high effort; deterministic evidence travels with it)
// ---------------------------------------------------------------------------
phase('Gate')
const gate = await agent(
  `${HOUSE_RULES}
You are the onboarding gate for this skill library (925+ skills; saturated — two real gaps beat ten duplicates). Decide build/enrich/drop for each verified candidate.

Deterministic triage evidence (authoritative): ${JSON.stringify(toVerify.map(c => ({ id: c.id, classification: c.classification, local_hits: c.local_hits })))}

Fact sheets from the verification pass: ${JSON.stringify(sheets)}

Rules:
- NEVER promote a candidate to build if is_real_capability=false, or if its fact sheet has fewer than 5 officially-sourced facts, or if the deterministic evidence classified it COVERED.
- Spot-check before trusting: for each candidate you intend to BUILD, run python3 scripts/search_knowledge.py "<a better query than the intake used>" via Bash and read the verbatim output; if a strong hit (score >= 5) appears, demote to enrich/drop and cite it.
- For build items pick domain + kebab slug per repo conventions, and decide agent wiring: read agents/_shared/SKILL_MAP.md and the agents/ directory listing to pick 1-2 run-time agents that would genuinely cite this skill ("--agent <id>"); if none plausibly owns it, use --runtime-orphan with a one-sentence --orphan-reason.
- For enrich items, name the exact existing skills/<domain>/<slug> path.
- Cap builds at ${MAX_BUILD}; overflow goes to drop with reason "deferred — over build cap".`,
  { label: 'gate', phase: 'Gate', schema: GATE_OUT, model: 'opus', effort: 'high' }
)
if (!gate) throw new Error('gate agent failed')
log(`Gate: build ${gate.build.length}, enrich ${gate.enrich.length}, drop ${gate.drop.length}`)

const sheetById = {}
for (const s of sheets) sheetById[s.id] = s

// ---------------------------------------------------------------------------
// Phase 4 — Scaffold builds serially (one agent, one shell — AGENT.md is shared)
// ---------------------------------------------------------------------------
let buildItems = []
if (gate.build.length) {
  phase('Scaffold')
  const scaffold = await agent(
    `Repo root is the CWD. Run these commands ONE AT A TIME via Bash, in order, and report per-command success. Do not parallelize (they edit shared agents/*/AGENT.md files). A non-zero exit from the --strict near-duplicate gate means that item FAILED (ok=false, include stderr) — do not retry with the gate dropped.
${gate.build.map(b => `python3 scripts/new_skill.py ${b.domain} ${b.slug} --strict --assume-yes ${b.wiring}`).join('\n')}
skill_path for each item is skills/<domain>/<slug>.`,
    { label: 'scaffold-serial', phase: 'Scaffold', schema: SCAFFOLD_OUT, model: 'sonnet', effort: 'low' }
  )
  const okBySlug = {}
  for (const r of (scaffold && scaffold.results) || []) okBySlug[r.slug] = r
  buildItems = gate.build
    .filter(b => okBySlug[b.slug] && okBySlug[b.slug].ok)
    .map(b => ({ kind: 'build', id: b.id, skill_path: `skills/${b.domain}/${b.slug}` }))
  const failed = gate.build.filter(b => !(okBySlug[b.slug] && okBySlug[b.slug].ok))
  for (const f of failed) log(`scaffold FAILED for ${f.slug} — dropped (near-duplicate gate or error)`)
}
const enrichItems = gate.enrich.map(e => ({ kind: 'enrich', id: e.id, skill_path: e.skill_path }))
const items = [...buildItems, ...enrichItems]
if (!items.length) {
  return { source: report.source, built: [], enriched: [], dropped: gate.drop, note: 'nothing survived gate/scaffold' }
}

// ---------------------------------------------------------------------------
// Phase 5-7 — Author → adversarial Review → Fix (Opus), pipelined per item
// ---------------------------------------------------------------------------
phase('Author')
function authorPrompt(it) {
  const sheet = JSON.stringify(sheetById[it.id] || {})
  const src = sourceRules(report.license_class, report.source)
  if (it.kind === 'build') {
    return `${HOUSE_RULES}\n${src}\n
TASK: Author the scaffolded skill at ${it.skill_path} to full v1.0.0 quality (scaffold files contain TODO placeholders). Edit ONLY inside ${it.skill_path}/.

Verified fact sheet (re-fetch its URLs for authoring-grade depth; you may add MORE official URLs): ${sheet}

Read first: ${EXEMPLAR}/ (house-style exemplar — match structure/tone/depth: SKILL.md ~200 lines, examples ~170, gotchas ~70, llm-anti-patterns ~110 with 5+ AI-assistant mistakes, well-architected ~50) and CLAUDE.md sections "Required Skill Frontmatter" + "Skill Package Standard". Check templates/<domain>/ and reference canonical templates by relative path instead of re-inventing.

Deliverables: complete SKILL.md frontmatter (description with when-to-use/trigger keywords/what it does NOT cover; 5 natural-language verb-first triggers; version 1.0.0; author Pranav Nagrecha; updated = today) + "## Recommended Workflow" (3-7 numbered steps); the 4 references files (well-architected.md MUST end with "## Official Sources Used" listing exactly the URLs you used); a real stdlib-only scripts/check_*.py validator (python3 -m py_compile it); a genuinely useful templates/ artifact. Preserve every maturity caveat from the fact sheet.

Return files_written, official_sources, exactly 2 query_fixtures ({query, domain, expected_skill: "<domain>/<slug>", top_k: 3}), notes.`
  }
  return `${HOUSE_RULES}\n${src}\n
TASK: Enrich the existing skill at ${it.skill_path} — add verified missing content, do NOT rewrite. Edit ONLY inside ${it.skill_path}/.

Fact sheet (gaps_vs_local_skill lists what to add; re-fetch URLs for depth): ${sheet}

Read the full existing skill first. Weave gap content into the appropriate sections in the skill's own voice; add newly used official URLs to "## Official Sources Used" (in references/well-architected.md); bump frontmatter version by a minor increment and set updated to today; optionally add 1-2 verb-first triggers.

Return files_written, official_sources, query_fixtures: [], notes.`
}

function reviewPrompt(it, author) {
  return `${HOUSE_RULES}\n${sourceRules(report.license_class, report.source)}\n
TASK: Adversarial fact-review of ${it.skill_path} (${it.kind}). Default stance: claims are unproven until verified.
1. Read every file in ${it.skill_path}/ (enrich: git diff -- ${it.skill_path} to focus, but sanity-check SKILL.md).
2. Fetch the URLs in "## Official Sources Used" and try to REFUTE each substantive claim (API names, metadata types, limits, commands, maturity labels, setup paths). Unsupported claim => blocker. Maturity mismatch => blocker.
3. Quality gates: frontmatter complete per CLAUDE.md (${it.kind === 'build' ? '5+ triggers, version 1.0.0' : 'minor version bump'}); "## Recommended Workflow" 3-7 steps; llm-anti-patterns.md 5+ entries; "## Official Sources Used" populated; checker compiles (python3 -m py_compile).
4. ${report.license_class === 'clean-room' ? 'Blocker if any text appears sourced from the excluded upstream rather than official docs.' : 'If expression was adapted from the source, verify the author flagged attribution_required.'}
5. Do NOT fix anything. Report only. Author claimed sources: ${JSON.stringify(((author && author.official_sources) || []).slice(0, 12))}
PASS only with zero blockers.`
}

const results = await pipeline(
  items,
  (it) => agent(authorPrompt(it), { label: `author:${it.id}`, phase: 'Author', schema: AUTHOR_OUT, model: 'opus' })
    .then(author => ({ it, author })),
  (prev) => {
    if (!prev || !prev.author) throw new Error('author failed')
    return agent(reviewPrompt(prev.it, prev.author), { label: `review:${prev.it.id}`, phase: 'Review', schema: REVIEW_OUT, model: 'opus', effort: 'high' })
      .then(review => ({ ...prev, review }))
  },
  (prev) => {
    if (!prev) return null
    const blockers = ((prev.review && prev.review.issues) || []).filter(i => i.severity === 'blocker')
    if (prev.review && prev.review.verdict === 'PASS' && blockers.length === 0) return prev
    return agent(
      `${HOUSE_RULES}\nTASK: Fix review findings in ${prev.it.skill_path} ONLY. Findings:\n${JSON.stringify((prev.review && prev.review.issues) || [], null, 1)}\nFor factual disputes re-fetch the official doc and make the text match it (or delete the claim). Keep structure; update "## Official Sources Used" if sources change; re-py_compile the checker if touched. Return files_written/official_sources/notes; query_fixtures: [].`,
      { label: `fix:${prev.it.id}`, phase: 'Fix', schema: AUTHOR_OUT, model: 'opus' }
    ).then(fix => ({ ...prev, fix }))
  }
)

const done = results.filter(Boolean)
log(`${done.length}/${items.length} items completed authoring`)

return {
  source: report.source,
  license_class: report.license_class,
  built: done.filter(r => r.it.kind === 'build').map(r => r.it.skill_path),
  enriched: done.filter(r => r.it.kind === 'enrich').map(r => r.it.skill_path),
  dropped: gate.drop,
  items: done.map(r => ({
    skill: r.it.skill_path,
    kind: r.it.kind,
    verdict: r.review ? r.review.verdict : 'NO_REVIEW',
    blockers: ((r.review && r.review.issues) || []).filter(i => i.severity === 'blocker').length,
    fixed: !!r.fix,
    fixtures: (r.author && r.author.query_fixtures) || [],
    sources: (r.author && r.author.official_sources) || [],
    issues: (r.review && r.review.issues) || [],
  })),
  next_steps: 'Orchestrator: append fixtures to vector_index/query-fixtures.json; run skill_sync.py per touched skill; validate_repo.py; check_doc_counts.py; update BACKLOG statuses (built->DONE, enrich->DONE, drop->DUPLICATE with evidence); regenerate queue dashboard; commit + draft PR per commands/onboard-source.md.',
}