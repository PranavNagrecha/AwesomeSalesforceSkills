export const meta = {
  name: 'model-routing-benchmark',
  description: 'Measure the SHIPPED routing path — agents pick a skill from the roster glosses exactly as Claude does on a fresh install',
  phases: [
    { title: 'Route', detail: 'each agent routes a batch of real queries using only what ships' },
    { title: 'Analyse', detail: 'characterise every miss into an actionable defect class' },
  ],
}

const REPO = "/Users/pranavnagrecha/VS Code/Personal/SfSkills"

// 154 held-out queries, split into batches. Each batch is routed independently.
const BATCHES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

const ROUTE = {
  type: 'object',
  required: ['batch', 'results'],
  properties: {
    batch: { type: 'number' },
    results: {
      type: 'array',
      items: {
        type: 'object',
        required: ['query', 'expected', 'router_picked', 'skill_picked', 'correct'],
        properties: {
          query: { type: 'string' },
          expected: { type: 'string' },
          router_picked: { type: 'string', description: 'which salesforce-<domain> router you chose' },
          router_correct: { type: 'boolean', description: 'did the router domain match the expected skill domain' },
          skill_picked: { type: 'string', description: 'domain/slug you chose from the roster' },
          correct: { type: 'boolean' },
          expected_in_top3: { type: 'boolean', description: 'was the expected skill among your top 3 candidates' },
          why_picked: { type: 'string', description: 'the gloss text that made you choose it' },
          miss_reason: {
            type: 'string',
            description: "if wrong: GLOSS_TOO_VAGUE | NO_REDIRECT | WRONG_ROUTER | GLOSS_TRUNCATED | GENUINE_OVERLAP | LABEL_ARBITRARY | OTHER",
          },
        },
      },
    },
  },
}

const ANALYSIS = {
  type: 'object',
  required: ['batch', 'defects'],
  properties: {
    batch: { type: 'number' },
    defects: {
      type: 'array',
      items: {
        type: 'object',
        required: ['query', 'expected', 'picked', 'defect_class', 'concrete_fix'],
        properties: {
          query: { type: 'string' },
          expected: { type: 'string' },
          picked: { type: 'string' },
          defect_class: { type: 'string' },
          concrete_fix: { type: 'string', description: 'the exact description/gloss edit that would fix this miss' },
          label_is_wrong: { type: 'boolean', description: 'true if the benchmark label is arbitrary and the pick was defensible' },
        },
      },
    },
  },
}

phase('Route')
const routed = await pipeline(
  BATCHES,
  (b) => agent(
    `You are simulating how Claude ACTUALLY selects a Salesforce skill on a fresh install. This is a measurement, not an improvement task — do not edit any file.

THE PATH YOU MUST SIMULATE, and its constraint:
On a fresh install there is NO search index. \`vector_index/\` is gitignored and does not ship. Claude sees router skill descriptions, opens one router, reads a roster of one-line glosses, and picks a package. That is the whole mechanism.

So you must route using ONLY these files:
  1. The 11 router descriptions — the \`description:\` frontmatter of each
     \`${REPO}/.claude/skills/salesforce-*/SKILL.md\`
  2. The chosen router's roster —
     \`${REPO}/.claude/skills/salesforce-<domain>/references/skill-index.md\`

**YOU MAY NOT** run \`scripts/search_knowledge.py\`, query \`vector_index/lexical.sqlite\`, grep the \`skills/\` tree, or read any \`skills/**/SKILL.md\`. Doing so measures a mechanism users do not have and invalidates the result. Use Read on the two file types above and nothing else from the repo.

YOUR QUERIES:
Read \`${REPO}/evals/measurement/heldout-queries.json\`. It has a \`queries\` array of {query, expected_skill, domain}. Take every item whose index modulo 10 equals ${b} (0-based). That is your batch.

IMPORTANT: \`expected_skill\` is the benchmark's label. Do NOT look at it before choosing — decide first, then compare. If you peek, the number is worthless. Read the whole batch's queries first, route them, then score.

FOR EACH QUERY:
1. From the 11 router descriptions alone, pick the router a user's question routes to. Record it.
2. Open that router's \`references/skill-index.md\` and scan the glosses. Pick the single best package. Note the gloss text that decided it.
3. Also note whether the expected skill was among your top 3 candidates.
4. Score correct = (skill_picked === expected).
5. If wrong, classify WHY, choosing the most specific that applies:
   - \`WRONG_ROUTER\` — you opened the wrong domain roster, so the right package was never visible
   - \`GLOSS_TOO_VAGUE\` — the correct package's gloss did not convey it covers this
   - \`NO_REDIRECT\` — the package you picked should have carried a "NOT for … use <the expected one>" clause and did not
   - \`GLOSS_TRUNCATED\` — the deciding information was cut off by a "…"
   - \`GENUINE_OVERLAP\` — two packages both legitimately cover the question
   - \`LABEL_ARBITRARY\` — your pick is as good as or better than the label; the benchmark is wrong, not the corpus
   - \`OTHER\`

BE HONEST. Recording a miss is the entire value of this exercise; a flattering number is worthless. \`LABEL_ARBITRARY\` is a real and common outcome in a 1,027-package corpus with near-duplicate neighbours — use it when it is true, but do not use it to excuse a genuine miss.

Return the structured object.`,
    { label: `route:batch-${b}`, phase: 'Route', schema: ROUTE }
  ),
  (res, b) => agent(
    `Turn routing misses into actionable corpus fixes. Repo: ${REPO}

ROUTING RESULTS FOR BATCH ${b}:
${JSON.stringify(res ?? {}, null, 1)}

For EVERY result where \`correct\` is false, now you MAY read the real packages (\`skills/<domain>/<slug>/SKILL.md\`) — the routing measurement is done, so reading them no longer contaminates it.

For each miss, determine:
1. Read BOTH the expected package and the one that was picked. Which genuinely answers the query? If the picked one is as good or better, set \`label_is_wrong: true\` — the benchmark label is arbitrary, and that is a finding about the BENCHMARK, not the corpus. Be rigorous: this is the difference between a real routing defect and a mislabelled test.
2. If the expected package really is the right answer, write the CONCRETE FIX: the exact edit to a \`description:\` that would have made the router pick correctly. Name the skill and give the clause verbatim. Prefer:
   - adding \`NOT for <the picked package's topic> — use <picked-package-slug>\` to the EXPECTED package's neighbour, or
   - adding the query's own vocabulary to the expected package's trigger phrasings, or
   - adding \`NOT for <this query's topic> — use <expected-slug>\` to the PICKED package.
3. Say which of the three levers it is, so a later wave can batch them.

Do not make any edits. This phase produces the work-list, not the work.

Return the structured object.`,
    { label: `analyse:batch-${b}`, phase: 'Analyse', schema: ANALYSIS }
  )
)

const ok = routed.filter(Boolean)
const defects = ok.flatMap((r) => r?.defects ?? [])
log(`${ok.length}/${BATCHES.length} batches analysed; ${defects.length} misses characterised`)
return { batches: ok.length, defects, results: ok }
