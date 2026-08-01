export const meta = {
  name: 'sfskills-depth-build',
  description: 'Apply the depth research: correct the fabricated Salesforce facts first (byte-neutral, actively harmful), then add the highest-leverage depth — verbatim error strings and the exact licences that gate features',
  phases: [
    { title: 'Corrections' },
    { title: 'Corrections QA' },
    { title: 'Additions' },
    { title: 'Additions QA' },
    { title: 'Review' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Branch: overhaul/2026-08-01-checkpoint. Do NOT create branches, commit, or push.
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.
FULL RESEARCH + BUILD PLAN: ${SCRATCH}/depth-plan.json (167 researched practices, 140 mapped
absorptions across flow/apex/lwc/data/security/integration, each with a target skill + file).

MACHINE CONSTRAINT — NON-NEGOTIABLE: 16 GB Mac, already OOM-killed once on this project.
A single search_knowledge.py call peaks ~2.9 GB. Run ONE heavy process at a time, never two
searches or validations concurrently.

HOUSE RULES:
- Official Salesforce docs are the ONLY authority for a product claim. If you cannot ground it
  in an official page, do not write it.
- Do NOT hand-edit generated artifacts: registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md.
- Do NOT run scripts/skill_sync.py or scripts/build_index.py — the orchestrator runs those.
- Never change a skill's name, category or description frontmatter — retrieval and the
  registry key off them.
- FILE OWNERSHIP IS STRICT.

THE QUALITY BAR, derived empirically from this repo's own best packages (measured corpus-wide):
- Anti-patterns carry the full diagnostic quad — what the LLM generates / why it happens /
  the correct version / a mechanically-checkable detection hint. Present in 88.8%.
- examples.md ships a runnable artifact in a code fence. Present in 84.6%.
- **Quotes at least one VERBATIM platform error string — present in only 11.0% (113/1027).
  THE SINGLE BIGGEST UPSIDE IN THE LIBRARY.**
- **Names the exact licence / permission set / permission-set-licence that gates the feature —
  present in only 8.4% (86/1027). SECOND BIGGEST UPSIDE.**
- Salesforce API-identifier density >= 0.8 distinct identifiers/KB — 21.3% pass.
Aim every edit at those two under-served markers. A paragraph of general advice is worthless;
'fails with X_ERROR_STRING unless the Y permission set licence is assigned' is the product.

RETRIEVAL IS ZERO-SUM (measured): the lexical window is 30 chunks. Growth in one package can
starve a neighbour. Hard ceiling G1 is ~50 KB / ~140 chunks per package. Several packages are
ALREADY at or over it — the plan names them. Never push a package further over G1.
`

const ITEMS = [
  {
    id: 'factual-corrections',
    title: 'Remove fabricated Salesforce facts from the corpus — including one that teaches a security vulnerability',
    owns: [
      'skills/data/data-reconciliation-patterns/**',
      'skills/data/data-loader-csv-column-mapping/**',
      'skills/integration/idempotent-integration-patterns/**',
      'skills/integration/webhook-inbound-patterns/**',
      'skills/flow/flow-versioning-strategy/**',
      'skills/flow/flow-bulkification/**',
      'skills/flow/fault-handling/**',
      'skills/apex/async-apex/**',
      'skills/apex/apex-future-method-patterns/**',
      'skills/integration/retry-and-backoff-patterns/**',
    ],
    goal: `THIS IS THE HIGHEST-VALUE ITEM IN THE WHOLE PROGRAM. The research found the library
asserts Salesforce facts that are FABRICATED or INVERTED. A confidently wrong skill is worse
than a missing one: a practitioner ships it to production. These fixes are near byte-neutral,
so they carry no retrieval risk.

VERIFY EVERY ONE YOURSELF against official Salesforce documentation with WebSearch/WebFetch
BEFORE changing it. The research is a lead, not proof. If a claimed fabrication turns out to be
correct, say so and leave it — a wrong "correction" is the same defect in a new costume.

A. INVENTED ERROR STRINGS (grep the corpus; the research found each appears nowhere in
   Salesforce documentation):
   1. 'MULTIPLE_CHOICES' — data/data-reconciliation-patterns, ~9 occurrences INCLUDING a
      checker script's user-facing message. Determine the REAL StatusCode Salesforce returns
      for an ambiguous external-id upsert match. The research indicates the correct string is
      DUPLICATE_EXTERNAL_ID and that it appears NOWHERE in the corpus
      (grep -rl DUPLICATE_EXTERNAL_ID skills/ returns nothing) — verify that against official
      docs, then use whatever the docs actually say.
   2. 'EXTERNAL_ID_NON_UNIQUE' — integration/idempotent-integration-patterns.
   3. 'InvalidBatch — relationship Who is polymorphic, type required' —
      data/data-loader-csv-column-mapping.

B. INVENTED CSV HEADER SYNTAX. A 'Who.Lead.External_Id__c'-style polymorphic-lookup header form
   is propagated across data/data-loader-csv-column-mapping's SKILL.md, gotchas.md,
   llm-anti-patterns.md, its template AND its validator script. Establish the REAL syntax
   Data Loader / Bulk API accept for a polymorphic relationship column, and correct every
   occurrence including the script and template — a validator that enforces invented syntax is
   worse than no validator.

C. SECURITY DEFECT — FIX THIS ONE FIRST. integration/webhook-inbound-patterns SKILL.md
   (~lines 104-111) presents 'expected.equals(signature)' as a constant-time comparison. It is
   NOT constant-time; String.equals short-circuits on the first differing character, which is
   exactly the timing side-channel the surrounding text claims to defend against. The library
   is teaching a vulnerability. Replace with a genuine constant-time comparison in Apex (a
   fixed-iteration loop XOR-accumulating over both byte arrays, comparing lengths separately),
   and make the anti-pattern explicit so a model does not regenerate the flawed version.

D. INVERTED / IMPOSSIBLE MECHANISMS — verify each, correct the ones that hold:
   1. flow/flow-versioning-strategy Gotcha 4 — states subflow version resolution BACKWARDS.
      Establish whether a running flow invokes the ACTIVE version of a subflow or the version
      current at design time, and state it correctly.
   2. flow/flow-bulkification:136 — asserts a partial-success behaviour Flow does not have.
   3. flow/fault-handling AP3 — prescribes a mechanism that does not exist.
   4. apex/async-apex llm-anti-patterns.md #3 AND apex/apex-future-method-patterns SKILL.md —
      both assert you CANNOT call @future from a Queueable. Official docs document an
      allocation of 50 @future calls from a Queueable. Verify and correct both.
   5. integration/retry-and-backoff-patterns — asserts Apex 'cannot introduce meaningful
      delay'. Verify against the current documented Queueable delay capability
      (MinimumQueueableDelayInMinutes / AsyncOptions) and correct.

FOR EACH CORRECTION: cite the official source URL in your report. Where a skill's
references/well-architected.md has '## Official Sources Used', add the source there. Keep the
edits surgical — you are correcting facts, not rewriting packages. Report byte deltas; these
should be close to neutral.`,
  },
  {
    id: 'depth-additions',
    title: 'Add the two highest-leverage kinds of depth: verbatim error strings and the exact licences that gate features',
    owns: [
      'skills/apex/apex-queueable-patterns/**',
      'skills/apex/apex-security-enforcement/**',
      'skills/data/soql-query-optimization/**',
      'skills/architect/org-limits-monitoring/**',
      'skills/integration/change-data-capture-integration/**',
      'skills/integration/pub-sub-api-patterns/**',
      'skills/security/record-access-troubleshooting/**',
      'skills/lwc/lwc-reactive-state-patterns/**',
    ],
    goal: `Apply the highest-value ABSORB items from ${SCRATCH}/depth-plan.json for these eight
packages ONLY. Read the plan file first and work from its per-practice target mapping.

PRIORITISE by the two measured corpus gaps:
  - VERBATIM ERROR STRINGS (only 11.0% of skills have one). Every addition that can carry the
    literal text a user sees — 'System.LimitException: Too many SOQL queries: 101',
    'Non-selective query against large object type', 'Insufficient permissions: secure query' —
    should carry it exactly.
  - NAMED LICENCES / PERMISSIONS (only 8.4%). Where a feature is gated by a permission set
    licence, a user permission, or an org preference, NAME IT precisely.

The plan identifies these specific absent facts, each verified absent by literal grep across
all 1,027 packages — verify against official docs before writing, then add:
  - Security.stripInaccessible getInaccessibleFields(), and the enforceRootObjectCRUD third argument
  - MinimumQueueableDelayInMinutes / AsyncOptions delay
  - QueueableDuplicateSignature deduplication
  - DailyAsyncApexElasticExecutions, ConcurrentPerOrgLongTxn, ConcurrentLongRunningApexLimit
  - Non-selective query behaviour inside a trigger
  - The five-re-enqueue ceiling (on top of the existing '3-5' heuristic)
  - Pub/Sub replay-ID non-contiguity and the ReplayPreset trade-off
  - CDC delivery-allocation subscriber-type rules and the exact failure strings

HARD CONSTRAINTS:
  - Package ceiling G1 is ~50 KB / ~140 chunks. Measure each target BEFORE and AFTER:
      for d in <target>; do find "$d" -name '*.md' -exec cat {} + | wc -c; done
    The plan flags apex/apex-queueable-patterns as the largest grower (37.5 KB -> ~43.9 KB,
    +17%). Do NOT exceed G1 on any package. If an addition would breach it, put the fact in the
    most specific EXISTING sibling package instead, or drop it and report that you did.
  - Do NOT add a fact the plan marked as already covered. The plan lists per domain exactly
    what was verified present; re-adding it duplicates chunks and starves neighbours.
  - Anti-pattern entries must carry the full quad: what the LLM generates / why it happens /
    the correct version / a mechanically-checkable detection hint.

Ground EVERY claim in an official Salesforce page and record the URL. Anything you cannot
verify goes in your report as unverified, NOT into a file.`,
  },
]

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } }, required: ['path', 'action', 'summary'] } },
    corrections_made: { type: 'array', description: 'each fabricated/inverted fact, the official source that settles it, and what it now says', items: { type: 'string' } },
    claims_refuted: { type: 'array', description: 'research claims that did NOT hold up — leaving content alone is a valid, valuable outcome', items: { type: 'string' } },
    official_sources_used: { type: 'array', items: { type: 'string' } },
    byte_deltas: { type: 'array', description: 'per package, bytes before -> after, vs the ~50KB G1 ceiling', items: { type: 'string' } },
    unverified_left_out: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'corrections_made', 'claims_refuted', 'official_sources_used', 'byte_deltas', 'unverified_left_out', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    fabrications_gone: { type: 'string', description: 'grep proof that each invented string no longer appears anywhere in skills/' },
    retrieval_impact: { type: 'string', description: 'do touched skills still retrieve, and do untouched neighbours still retrieve' },
    g1_compliance: { type: 'string', description: 'per-package byte totals vs the ~50KB ceiling' },
    defects: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } }, required: ['severity', 'file', 'description'] } },
  },
  required: ['item_id', 'verdict', 'fabrications_gone', 'retrieval_impact', 'g1_compliance', 'defects'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    factual_errors: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, claim: { type: 'string' }, why_wrong: { type: 'string' }, official_source: { type: 'string' }, correction: { type: 'string' } }, required: ['file', 'claim', 'why_wrong', 'correction'] } },
    security_fix_sound: { type: 'string', description: 'is the constant-time comparison actually constant-time in Apex' },
    new_fabrications_introduced: { type: 'array', description: 'anything the builder asserted that you could not find in official docs', items: { type: 'string' } },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'factual_errors', 'security_fix_sound', 'new_fabrications_introduced', 'required_changes'],
}

phase('Corrections')
log('Correcting fabricated Salesforce facts first — byte-neutral, no retrieval risk, actively harmful today.')

const corr = await agent(`${COMMON}

YOU ARE THE CORRECTIONS BUILDER.

ITEM: ${ITEMS[0].title}
FILES YOU MAY TOUCH (strict):
${ITEMS[0].owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${ITEMS[0].goal}`, { label: 'build:corrections', phase: 'Corrections', schema: BUILD_SCHEMA, effort: 'high' })

phase('Corrections QA')

const corrQA = await agent(`${COMMON}

YOU ARE THE QA AGENT for the corrections. TEST; MODIFY NOTHING.

BUILDER CLAIMS: ${JSON.stringify(corr, null, 2).slice(0, 22000)}

DO THIS (one heavy process at a time):
1. PROVE THE FABRICATIONS ARE GONE, corpus-wide, not just in the touched files:
     grep -rn "MULTIPLE_CHOICES" skills/ | wc -l
     grep -rn "EXTERNAL_ID_NON_UNIQUE" skills/ | wc -l
     grep -rn "relationship Who is polymorphic" skills/ | wc -l
   Then grep for whatever replacement strings the builder introduced and confirm they appear
   where expected. Paste all output.
2. INDEPENDENTLY VERIFY the three highest-stakes corrections against official Salesforce docs
   with WebFetch — the real upsert-ambiguity StatusCode, the @future-from-Queueable allocation,
   and the subflow version-resolution rule. Do not trust the builder's citation; open the page.
3. SECURITY: read the new Apex comparison in integration/webhook-inbound-patterns. Is it
   genuinely constant-time — fixed iteration count over both inputs, no early return, length
   compared separately? An almost-constant-time fix is still a vulnerability. Quote the code.
4. Confirm the checker script and template in data/data-loader-csv-column-mapping were BOTH
   updated — a validator still enforcing invented syntax is the worst residual outcome.
5. Retrieval: confirm each touched skill still retrieves, and spot-check 3 untouched neighbours
   in the same domains (zero-sum window). Paste the commands.
6. python3 scripts/validate_repo.py --changed-only (pre-existing stale-artifact and doc-count
   ERRORs are EXPECTED and not blockers; new ones are).
7. git status --short.`, { label: 'qa:corrections', phase: 'Corrections QA', schema: QA_SCHEMA, effort: 'high' })

log(`Corrections QA: ${corrQA?.verdict}`)

phase('Additions')

const add = await agent(`${COMMON}

YOU ARE THE ADDITIONS BUILDER.

ITEM: ${ITEMS[1].title}
FILES YOU MAY TOUCH (strict):
${ITEMS[1].owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${ITEMS[1].goal}

The corrections pass already ran on OTHER packages; do not revisit its files.`,
  { label: 'build:additions', phase: 'Additions', schema: BUILD_SCHEMA, effort: 'high' })

phase('Additions QA')

const addQA = await agent(`${COMMON}

YOU ARE THE QA AGENT for the additions. TEST; MODIFY NOTHING.

BUILDER CLAIMS: ${JSON.stringify(add, null, 2).slice(0, 22000)}

1. G1 CEILING — the main risk. Measure every touched package:
     for d in skills/apex/apex-queueable-patterns skills/apex/apex-security-enforcement skills/data/soql-query-optimization skills/architect/org-limits-monitoring skills/integration/change-data-capture-integration skills/integration/pub-sub-api-patterns skills/security/record-access-troubleshooting skills/lwc/lwc-reactive-state-patterns; do echo "$(find "$d" -name '*.md' -exec cat {} + | wc -c) $d"; done | sort -rn
   Any package over ~50,000 bytes is a defect. Report all eight.
2. VERIFY THE NEW API IDENTIFIERS ARE REAL. The additions name specific Salesforce identifiers
   (getInaccessibleFields, enforceRootObjectCRUD, MinimumQueueableDelayInMinutes,
   QueueableDuplicateSignature, DailyAsyncApexElasticExecutions, ConcurrentPerOrgLongTxn,
   ConcurrentLongRunningApexLimit). Check each against official docs with WebFetch. A
   plausible-but-nonexistent API name is the exact defect this wave is fixing elsewhere —
   finding one here is a BLOCKER.
3. Confirm no fact was added that the plan marked already-covered (duplicate chunks starve
   neighbours). Spot-check 3.
4. Anti-pattern quality: sample 3 new entries and confirm each carries the full quad —
   what the LLM generates / why / correct version / checkable detection hint.
5. Retrieval: touched skills still retrieve; 3 untouched neighbours still retrieve.
6. git status --short.`, { label: 'qa:additions', phase: 'Additions QA', schema: QA_SCHEMA, effort: 'high' })

log(`Additions QA: ${addQA?.verdict}`)

phase('Review')

const review = await agent(`${COMMON}

YOU ARE THE TECHNICAL REVIEWER for both passes. Modify nothing. Your job is FACTUAL TRUTH.

CORRECTIONS: ${JSON.stringify({ corr, corrQA }, null, 2).slice(0, 24000)}
ADDITIONS: ${JSON.stringify({ add, addQA }, null, 2).slice(0, 20000)}

1. Read the real diff: cd "${REPO}" && git diff -- skills/
2. THE CENTRAL QUESTION: did this wave REPLACE fabricated facts with true ones, or with
   different fabrications? For every Salesforce identifier, error string, limit number and
   mechanism introduced, verify it against official documentation with WebFetch. Anything you
   cannot find in official docs goes in new_fabrications_introduced — that is a blocker.
   This library's whole value proposition is being right about Salesforce; a wave that fixes
   invented content by inventing different content is a net negative.
3. SECURITY: independently assess the constant-time comparison. Reason about the actual Apex
   semantics — does it iterate a fixed number of times regardless of input, avoid early
   return, and handle unequal lengths without leaking? If it is not genuinely constant-time,
   REQUEST_CHANGES; a half-fixed timing side-channel is still exploitable.
4. Check the corrections did not overshoot: an over-eager "correction" that removes a TRUE
   statement is as damaging as the fabrication. Verify a sample of removed text was actually wrong.
5. Confirm no skill's name/category/description frontmatter changed and no generated artifact
   was hand-edited.`, { label: 'review:depth', phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })

log(`Depth build review: ${review?.verdict}`)

return { corrections: corr, corrections_qa: corrQA, additions: add, additions_qa: addQA, review }
