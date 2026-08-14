export const meta = {
  name: 'add-skill',
  description: 'Add a skill from a bare topic: screen coverage, decide build-vs-deepen, scaffold, author from official docs, adversarially review, wire retrieval, and land it green',
  whenToUse: 'Pass args {topic: "<what the skill should cover>"}. Optionally {domain, slug, force}. Screens the topic against the live corpus FIRST and will refuse to build a duplicate — deepening the existing package is usually the right answer in a 1,027-package library.',
  phases: [
    { title: 'Screen', detail: 'deterministic coverage check against the live index' },
    { title: 'Decide', detail: 'build vs deepen vs stop, on the screen evidence' },
    { title: 'Research', detail: 'official-docs fact sheet, developer.salesforce.com only' },
    { title: 'Author', detail: 'fill the scaffold from the fact sheet' },
    { title: 'Review', detail: 'adversarial fact-check; revert anything unverifiable' },
    { title: 'Land', detail: 'fixture, agent wiring, sync, validate, doctor to 100%' },
  ],
}

// ---------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------
const a = typeof args === 'string' ? JSON.parse(args) : (args || {})
const TOPIC = a.topic
if (!TOPIC) throw new Error('args.topic is required — describe what the skill should cover, in a sentence')
const WANT_DOMAIN = a.domain || null
const WANT_SLUG = a.slug || null
// force:true proceeds even when the screen says the topic is already owned.
// It does not skip the screen — the evidence is still reported, so an override
// is a recorded decision rather than an invisible one.
const FORCE = a.force === true

const REPO = process?.env?.SFSKILLS_ROOT || '/Users/pranavnagrecha/VS Code/Personal/SfSkills'

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const SCREEN = {
  type: 'object',
  required: ['topic', 'verdict', 'evidence', 'nearest'],
  properties: {
    topic: { type: 'string' },
    verdict: { type: 'string', enum: ['GAP', 'ADJACENT', 'DUPLICATE'] },
    evidence: { type: 'string', description: 'the verbatim search output the verdict rests on' },
    nearest: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'score', 'covers'],
        properties: {
          id: { type: 'string' },
          score: { type: 'number' },
          covers: { type: 'string', description: 'what that package actually covers, from reading it' },
          states_the_facts: { type: 'boolean', description: 'does it already state the facts this topic needs' },
        },
      },
    },
  },
}

const DECISION = {
  type: 'object',
  required: ['action', 'rationale'],
  properties: {
    action: { type: 'string', enum: ['BUILD', 'DEEPEN', 'STOP'] },
    domain: { type: 'string' },
    slug: { type: 'string' },
    deepen_target: { type: 'string', description: 'for DEEPEN: the package to add the facts to' },
    rationale: { type: 'string' },
    boundary: { type: 'string', description: 'the NOT-for boundary against the nearest neighbour' },
  },
}

const FACTS = {
  type: 'object',
  required: ['facts', 'sources'],
  properties: {
    facts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'source_url', 'verified'],
        properties: {
          claim: { type: 'string' },
          source_url: { type: 'string' },
          verbatim_quote: { type: 'string' },
          verified: { type: 'boolean' },
          error_string: { type: 'string' },
          gating_permission: { type: 'string' },
          llm_gets_wrong: { type: 'string' },
        },
      },
    },
    sources: { type: 'array', items: { type: 'string' } },
    unverifiable: { type: 'array', items: { type: 'string' }, description: 'claims dropped for want of a renderable source' },
  },
}

const AUTHORED = {
  type: 'object',
  required: ['skill', 'files_written', 'doctor_score'],
  properties: {
    skill: { type: 'string' },
    files_written: { type: 'array', items: { type: 'string' } },
    doctor_score: { type: 'number' },
    remaining: { type: 'array', items: { type: 'string' } },
  },
}

const VERDICT = {
  type: 'object',
  required: ['skill', 'verdict', 'findings'],
  properties: {
    skill: { type: 'string' },
    verdict: { type: 'string', enum: ['CLEAN', 'FIXED', 'NEEDS_OWNER'] },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'severity', 'problem', 'action_taken'],
        properties: {
          file: { type: 'string' },
          severity: { type: 'string', enum: ['BLOCKER', 'MAJOR', 'MINOR'] },
          problem: { type: 'string' },
          action_taken: { type: 'string', enum: ['FIXED', 'REVERTED', 'LEFT_FOR_OWNER'] },
          detail: { type: 'string' },
        },
      },
    },
  },
}

const LANDED = {
  type: 'object',
  required: ['skill', 'doctor_score', 'validate_errors', 'fixture_pass'],
  properties: {
    skill: { type: 'string' },
    doctor_score: { type: 'number' },
    validate_errors: { type: 'number' },
    fixture_pass: { type: 'boolean' },
    fixture_added: { type: 'string' },
    agent_wiring: { type: 'string', description: 'agent it was wired to, or the recorded runtime_orphan reason' },
    outstanding: { type: 'array', items: { type: 'string' } },
  },
}

// ---------------------------------------------------------------------------
// 1. Screen — deterministic, before anyone writes anything
// ---------------------------------------------------------------------------
phase('Screen')
const screen = await agent(
  `Decide whether the SfSkills corpus already covers a topic. Repo: ${REPO}

TOPIC: ${TOPIC}

This library has 1,027 packages and is SATURATED at topic level. Three independent screens in Aug 2026 found that of 94 research-claimed "gaps", only 12 were real; of 31 hand-picked topics, 1; of 88 verified platform changes, 0. The default answer to "should we add a skill" is NO — the facts belong in a package that already owns the topic. Your job is to find that package, not to clear the way for a new one.

METHOD — run the real search, do not reason from memory:
1. \`cd "${REPO}" && python3 scripts/search_knowledge.py "<a natural phrasing of the topic>"\`
   Run it 2-3 times with DIFFERENT phrasings: how a practitioner would describe the symptom, the formal feature name, and the error/limit if there is one.
2. Record the VERBATIM output. A prior session had agents assert "no skill found" twice without running anything; the verbatim output is the guard against that.
3. Score: top-1 >= 3.0 -> DUPLICATE, 1.5-3.0 -> ADJACENT, < 1.5 -> GAP.
4. Then READ the top 2-3 packages' SKILL.md. The score says the TOPIC is owned; it does not say the FACTS are present. For each, say what it actually covers and whether it already states the specific facts this topic needs.
5. Also check \`ls ${REPO}/skills/<plausible-domain>/\` — a rename or near-synonym may exist that search ranked low.

Be honest. A GAP verdict that is wrong costs the corpus a duplicate package forever.

Return the structured object.`,
  { label: 'screen', phase: 'Screen', schema: SCREEN }
)

// ---------------------------------------------------------------------------
// 2. Decide
// ---------------------------------------------------------------------------
phase('Decide')
const decision = await agent(
  `Decide what to do about this topic, on the screen evidence. Repo: ${REPO}

TOPIC: ${TOPIC}
SCREEN RESULT:
${JSON.stringify(screen ?? {}, null, 1)}
${WANT_DOMAIN ? `\nThe requester suggested domain: ${WANT_DOMAIN}` : ''}${WANT_SLUG ? `\nThe requester suggested slug: ${WANT_SLUG}` : ''}${FORCE ? '\nThe requester passed force:true — build even if the topic looks owned, but say plainly in the rationale that the screen disagreed and why you proceeded.' : ''}

CHOOSE:
- **DEEPEN** (usually correct) — a package owns the topic but is silent on these facts. Name it in \`deepen_target\`. This is the right call whenever the screen says DUPLICATE, and usually when it says ADJACENT.
- **BUILD** — no package owns the topic, OR one is adjacent but the boundary is genuinely clean and a reader would not find these facts there. Give \`domain\` and \`slug\`.
- **STOP** — the topic is fully covered, facts included. Nothing to do.

IF BUILD:
- \`domain\` must be one of: admin, apex, lwc, flow, omnistudio, agentforce, security, integration, data, devops, architect.
- \`slug\` is kebab-case, specific, and must not read as a near-clone of an existing package. Check \`ls ${REPO}/skills/<domain>/\` first.
- \`boundary\` is REQUIRED: the true "NOT for <adjacent question> — use <existing-package-slug>" clause that separates this from its nearest neighbour. On a fresh install Claude picks skills by reading one-line glosses generated from the description, so this clause is the single most load-bearing thing you will write. It must name a package that EXISTS.

Return the structured object.`,
  { label: 'decide', phase: 'Decide', schema: DECISION }
)

if (decision?.action === 'STOP') {
  log(`STOP — already covered. ${decision.rationale}`)
  return { action: 'STOP', topic: TOPIC, screen, decision }
}

const isBuild = decision?.action === 'BUILD'
const target = isBuild ? `${decision.domain}/${decision.slug}` : decision?.deepen_target
log(`${decision?.action} -> ${target}`)

// ---------------------------------------------------------------------------
// 3. Research — official docs only
// ---------------------------------------------------------------------------
phase('Research')
const facts = await agent(
  `Build an official-docs fact sheet. Repo: ${REPO}

TOPIC: ${TOPIC}
TARGET PACKAGE: ${target}   (${decision?.action})

Gather the facts the package needs, each tied to a page you actually fetched.

SOURCE RULES, which decide whether a fact may be written at all:
- Prefer **developer.salesforce.com** — it renders for WebFetch.
- **help.salesforce.com is a client-side SPA that blocks crawlers.** It returns a loading shell, not content. A fact whose ONLY source is a help.salesforce.com page is UNVERIFIABLE — put it in \`unverifiable\` and do not claim it. A sibling wave documented seven distinct fetch attempts (URL variants, curl with different user-agents, Zoomin backing paths, Wayback) before correctly refusing a fact. Refusing is the right outcome.
- Set \`verified: false\` for anything you could not confirm on a page you rendered. Do not pad the sheet.

WHAT TO PRIORITISE — these are the two things this corpus measurably lacks (only ~11% of packages quote a verbatim platform error string, ~8% name the gating licence or permission):
1. The exact **error string** the platform emits, verbatim.
2. The exact **licence or permission** that gates the feature, by its real name.
3. Hard limits and their EXACT dimension. Number-relabelling is the commonest defect here: a real Salesforce number attached to the wrong thing (a display cap written as an export cap, an API processing limit written as a UI hard stop). Re-read the page rather than trusting a summary.
4. What an LLM trained on older material gets WRONG about this — the specific wrong answer.

CURRENCY: today is 2026-08-14. API 67.0 (Summer '26) removed \`WITH SECURITY_ENFORCED\` and inverted the Apex defaults (user mode, and \`with sharing\` for a class with no keyword), gated on the class's \`.cls-meta.xml\` apiVersion — not the org's release. Apex TRIGGERS still run in system mode at every version. See \`${REPO}/agents/_shared/AGENT_CONTRACT.md\` § "Apex security idiom by API version".

Return the structured object.`,
  { label: 'research', phase: 'Research', schema: FACTS }
)

// ---------------------------------------------------------------------------
// 4. Author
// ---------------------------------------------------------------------------
phase('Author')
const authored = await agent(
  `${isBuild ? 'Scaffold and author a new skill package.' : 'Deepen an existing skill package.'} Repo: ${REPO}

TOPIC: ${TOPIC}
TARGET: ${target}
BOUNDARY (the NOT-for clause that must end the description): ${decision?.boundary || '(none supplied — derive one and say so)'}

FACT SHEET — write ONLY what is here with \`verified: true\`:
${JSON.stringify(facts ?? {}, null, 1)}

${isBuild ? `SCAFFOLD FIRST, do not hand-create directories:
    cd "${REPO}" && python3 scripts/new_skill.py ${decision.domain} ${decision.slug} --strict
\`--strict\` refuses a name that collides with an existing package — if it refuses, STOP and report that, because it means the screen was wrong.
Then fill every TODO it left.` : `Add the new facts to the existing package. Do NOT restate what it already says — read it first. Corrections take priority over additions: if the package states something the fact sheet contradicts, fix that first.`}

WHAT GOOD LOOKS LIKE HERE:
- \`SKILL.md\` — frontmatter complete; \`description\` ends with the boundary clause naming a REAL package; 3+ \`triggers:\` written as what a user TYPES (verb-first symptom phrasing, "my flow keeps hitting the SOQL limit", not the topic name); a \`## Recommended Workflow\` with 3-7 numbered steps.
- \`references/gotchas.md\` — non-obvious behaviour that bites in production, with the exact limit, error string and permission name.
- \`references/llm-anti-patterns.md\` — 5+ entries. Each: what the model generates, why it is wrong, the corrected version. Either house style works (\`## Anti-Pattern N:\` sections, or a flat numbered list).
- \`references/examples.md\` — at least one worked artifact in a fenced block that would actually run. Not prose describing one.
- \`references/well-architected.md\` — the trade-off mapped to a pillar, plus \`## Official Sources Used\` listing every page from the fact sheet with what it confirms and "(verified 2026-08-14)".

CONSTRAINTS:
- Do not write a fact that is not on the sheet, or is marked \`verified: false\`. Gaps are acceptable; invention is not.
- Verify every Apex identifier against \`${REPO}/templates/apex/\`. There is no \`stripInaccessibleFields\`; \`Security.stripInaccessible(AccessType, records)\` returns an \`SObjectAccessDecision\` you call \`.getRecords()\` on. Use \`AccessType.CREATABLE\` on insert paths, \`UPDATABLE\` on update paths.
- Never emit \`WITH SECURITY_ENFORCED\`.
- BE PROPORTIONATE — 1,027 packages share a fixed 30-chunk retrieval window; padding this one demotes its neighbours. Match the size of a sibling package in the same domain.

FINISH BY RUNNING: \`python3 scripts/skill_doctor.py ${target}\` and report the score and whatever it still lists.

Return the structured object.`,
  { label: `author:${target}`, phase: 'Author', schema: AUTHORED }
)

// ---------------------------------------------------------------------------
// 5. Review — adversarial
// ---------------------------------------------------------------------------
phase('Review')
const review = await agent(
  `Adversarially review a ${isBuild ? 'newly authored' : 'newly deepened'} skill package. Repo: ${REPO}

TARGET: ${target}
AUTHOR REPORTED:
${JSON.stringify(authored ?? {}, null, 1)}
FACT SHEET IT WAS GIVEN:
${JSON.stringify(facts ?? {}, null, 1)}

This content is new and has had exactly one pass. Measured across sibling waves, unreviewed authoring produces roughly one fabricated claim per three packages, and the fabrications concentrate in CITATIONS, not numbers. Review the real diff: \`cd "${REPO}" && git diff -- skills/${target}\` (plus untracked files for a new package: \`git status --porcelain -- skills/${target}\`).

CHECK, hardest first:
1. **FABRICATED CITATIONS.** Re-fetch every URL in \`## Official Sources Used\`. Does it exist and say what it is cited for? Caught previously: a manufactured verbatim quotation with a named attribution where the source's quote field was EMPTY; an author that fetched its page, saw it did not support the claim, and quietly swapped in a different URL that returns only an SPA shell. If a claim rests solely on help.salesforce.com, revert it.
2. **CLAIMS BEYOND THE SHEET.** Anything asserted that is not on the fact sheet, or is marked \`verified: false\`, must be reverted. Drift from the brief is a real failure mode — one wave shifted "referenced" to "already installed" and changed the claim's whole dimension.
3. **FABRICATED IDENTIFIERS.** Every Apex symbol, sObject, field, permission, licence, metadata type and error string must be real.
4. **WRONG-DIMENSION NUMBERS.** Re-read the page. But do not delete a specific-looking number because it seems improbable — several such numbers are correct.
5. **THE BOUNDARY CLAUSE.** The description must end with \`NOT for X — use <slug>\` naming a package that EXISTS on disk. Confirm it. This is what routes a misdirected reader, and a dead target is the defect it exists to prevent.
6. **TRIGGERS ARE USER PHRASINGS**, not restatements of the skill name.
7. **EXAMPLES ARE REAL ARTIFACTS** in fenced blocks.
8. **BLOAT.** Compare with a sibling package in the same domain.

ACT: fix with Edit, or revert. Reverting is a success — a thinner honest package beats a fuller confident one. Then re-run \`python3 scripts/skill_doctor.py ${target}\`.

Return the structured verdict.`,
  { label: `review:${target}`, phase: 'Review', schema: VERDICT }
)

// ---------------------------------------------------------------------------
// 6. Land — retrieval wiring, sync, validate
// ---------------------------------------------------------------------------
phase('Land')
const landed = await agent(
  `Land the package: make it discoverable and make the gates pass. Repo: ${REPO}

TARGET: ${target}
REVIEW VERDICT:
${JSON.stringify(review ?? {}, null, 1)}

DO THESE IN ORDER, and report what each actually returned:

1. **Query fixture.** \`vector_index/query-fixtures.json\` needs an entry for every skill — a missing one is a validator ERROR. If \`${target}\` has none, add:
   \`{"query": "<what a practitioner would actually type>", "domain": "<domain>", "expected_skill": "${target}", "top_k": 3}\`
   The query must be a natural phrasing, NOT the skill name echoed back — a fixture that restates the slug tests nothing.

2. **Agent wiring — a real decision, not a formality.** Check whether any run-time agent should cite this. Wire it ONLY if some agent's output would be wrong without it, and then add a Mandatory Reads line WITH a reason clause (a bare path is a validator WARN). If no agent genuinely owns the topic, record that honestly in the skill's frontmatter instead:
   \`runtime_orphan: true\` and \`runtime_orphan_reason: <why no agent owns this>\`.
   Do not manufacture a citation to clear a warning — that inflates an agent's reading list with something it will never read.

3. **Sync:** \`python3 scripts/skill_sync.py --skill skills/${target}\`

4. **Retrieval check:** \`python3 scripts/search_knowledge.py "<the fixture query>"\` — confirm \`${target}\` comes back in the top 3. If it does not, the description and triggers are not carrying the vocabulary a user would use. Fix them and re-sync. Do NOT re-point the fixture at whatever currently wins; that hides the defect.

5. **Validate:** \`python3 scripts/validate_repo.py --changed-only\` — must be 0 errors. Fix anything it reports and re-run.

6. **Doctor:** \`python3 scripts/skill_doctor.py ${target}\` — report the score and anything outstanding.

Report honestly. If something will not go green, say exactly what and why rather than reporting success.

Return the structured object.`,
  { label: `land:${target}`, phase: 'Land', schema: LANDED }
)

const blockers = (review?.findings ?? []).filter((f) => f.severity === 'BLOCKER')
log(`${decision?.action} ${target} — doctor ${landed?.doctor_score ?? '?'}%, validate errors ${landed?.validate_errors ?? '?'}, ${blockers.length} blocker(s)`)

return {
  topic: TOPIC,
  action: decision?.action,
  skill: target,
  screen,
  decision,
  facts_verified: (facts?.facts ?? []).filter((f) => f.verified).length,
  facts_dropped: (facts?.unverifiable ?? []).length,
  review_verdict: review?.verdict,
  blockers,
  landed,
}
