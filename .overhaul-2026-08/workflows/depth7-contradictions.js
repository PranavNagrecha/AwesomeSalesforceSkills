export const meta = {
  name: 'sfskills-contradiction-hunt',
  description: 'Find places where the library contradicts itself: two skills giving opposite advice on the same Salesforce question, or a skill contradicting its own cited sources',
  phases: [{ title: 'Hunt' }],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const OUT = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad/contradictions'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY. Create/edit/delete NOTHING under ${REPO}. Notes only under ${OUT}/.

*** MEMORY RULE — ~20 AGENTS RUN IN PARALLEL ON A 16 GB MACHINE ***
DO NOT run scripts/search_knowledge.py (~2.9 GB peak), validate_repo.py, skill_sync.py or
build_index.py. Use grep/ls/sed/awk/file reads only. WebSearch/WebFetch cost no local memory.

WHY THIS EXISTS. This library has 1,027 skill packages written across many months by many
passes. Nobody has ever checked whether they AGREE WITH EACH OTHER. Two failure shapes matter:

  (A) CROSS-SKILL CONTRADICTION — two skills answer the same Salesforce question in opposite
      ways. This is uniquely damaging here: retrieval surfaces ONE skill, so which advice a
      user gets becomes a coin flip they cannot see. Worse, an agent citing both in its
      Mandatory Reads receives two incompatible instructions in the same context window.

  (B) SELF-CONTRADICTION — a skill's SKILL.md contradicts its own references/, or contradicts
      the official source it cites. A depth pass already found one skill contradicting its own
      Official Sources list in three separate places, and another whose gotcha inverted the
      mechanism its examples demonstrated.

RELATED CONFIRMED HISTORY (assume as fact): a parallel pass found the corpus asserting
fabricated Salesforce facts — an invented StatusCode repeated 9 times including inside a
checker script, invented CSV header syntax propagated across 6 files, and a String comparison
labelled "constant-time" that short-circuits. So do not assume that where two skills disagree,
the more confident one is right. BOTH may be wrong. Verify against official docs.

HOW TO JUDGE: a contradiction is only real if the two statements cannot both be true for the
same Salesforce configuration. Different advice for genuinely different CONTEXTS is correct
behaviour, not a contradiction — e.g. "use before-save for same-record updates" and "use
after-save when you need the record Id" are complementary, not conflicting. Distinguish these
carefully; false positives here would trigger destructive edits to correct content.
`

const SCHEMA = {
  type: 'object',
  properties: {
    topic: { type: 'string' },
    pairs_examined: { type: 'string', description: 'how many candidate skill pairs/claims you compared' },
    contradictions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          kind: { type: 'string', enum: ['cross-skill', 'self-contradiction', 'contradicts-cited-source'] },
          question: { type: 'string', description: 'the Salesforce question both are answering' },
          statement_a: { type: 'string', description: 'file:line + the verbatim claim' },
          statement_b: { type: 'string', description: 'file:line + the verbatim claim' },
          which_is_correct: { type: 'string', enum: ['A', 'B', 'NEITHER', 'BOTH_CONTEXTUAL', 'UNRESOLVED'] },
          official_source_checked: { type: 'string', description: 'the URL you actually opened to settle it' },
          resolution: { type: 'string', description: 'what the corpus should say' },
          severity: { type: 'string', enum: ['security', 'data-loss', 'misleading', 'cosmetic'] },
        },
        required: ['kind', 'question', 'statement_a', 'statement_b', 'which_is_correct', 'official_source_checked', 'resolution', 'severity'],
      },
    },
    false_positives_rejected: { type: 'array', description: 'apparent conflicts that are actually context-dependent and correct — report these, they prevent destructive edits', items: { type: 'string' } },
    health_note: { type: 'string' },
  },
  required: ['topic', 'pairs_examined', 'contradictions', 'false_positives_rejected', 'health_note'],
}

const TOPICS = [
  { key: 'automation-choice', note: 'Flow vs Apex vs Workflow vs Agentforce. Compare skills/flow/*, skills/apex/* and standards/decision-trees/automation-selection.md. Do any two disagree on WHEN to reach for Apex over Flow, on whether Flow can do X, or on the order-of-execution position of before/after-save flows? Also check the decision tree agrees with the skills that cite it.' },
  { key: 'sharing-access', note: 'Record access and sharing. Compare skills/security/*, skills/admin/* and standards/decision-trees/sharing-selection.md. Look for disagreement on: OWD precedence order, what Grant Access Using Hierarchies does for custom objects, View All vs View All Data semantics, whether restriction rules remove __Share rows, implicit sharing behaviour, and guest user rules. This is the highest-stakes topic in the library — wrong sharing advice is a data-exposure bug.' },
  { key: 'async-bulk', note: 'Async Apex and bulk data movement. Compare skills/apex/* and skills/data/*. Look for disagreement on: governor limit NUMBERS (they should be identical everywhere), batch sizes, @future vs Queueable capability claims, Queueable chaining depth, whether Apex can delay execution, Bulk API batch behaviour vs the 200-row trigger transaction, and skew thresholds. Numeric disagreement is the easiest true contradiction to prove — grep the same limit across domains and compare.' },
  { key: 'integration-patterns', note: 'Integration. Compare skills/integration/*, skills/architect/* and standards/decision-trees/integration-pattern-selection.md. Look for disagreement on: Platform Event delivery guarantees and retention windows, CDC retention, replay-ID semantics, API limit consumption, Named Credential vs stored secrets, retry/idempotency advice, and composite API caps.' },
  { key: 'lwc-apex-security', note: 'Security enforcement in code. Compare skills/lwc/*, skills/apex/* and skills/security/*. Look for disagreement on: whether WITH SECURITY_ENFORCED / WITH USER_MODE / Security.stripInaccessible is the right enforcement, whether @AuraEnabled Apex enforces FLS automatically (a classic point of confusion), with/without/inherited sharing semantics, and what Lightning Web Security changes vs Locker. A contradiction here produces insecure generated code.' },
]

phase('Hunt')
log(`Contradiction hunt across ${TOPICS.length} cross-cutting topics.`)

const results = await parallel(TOPICS.map((t) => () => agent(`${COMMON}

YOU ARE THE CONTRADICTION HUNTER FOR: ${t.key.toUpperCase()}
SCOPE: ${t.note}

METHOD:
1. Build the candidate set cheaply. Useful moves:
     grep -rln "<key term>" --include=SKILL.md skills/ | head -30
     grep -rn "<specific limit or mechanism>" --include='*.md' skills/ | head -40
   For NUMERIC claims, grep the same limit across all domains and diff the values — a limit
   stated as two different numbers in two skills is a provable contradiction and the fastest
   true positive available to you.
2. Read the candidates properly. A contradiction needs BOTH verbatim statements with file:line.
   Do not report a paraphrase.
3. SETTLE IT against official Salesforce documentation with WebFetch. Open the page. Record
   which statement is right — and be open to NEITHER, because a parallel pass has already
   confirmed this corpus contains fabricated facts.
4. Be disciplined about false positives. Different advice for different contexts is correct.
   Report those in false_positives_rejected — that list protects correct content from being
   "fixed" by a later pass, and is as valuable as the contradictions themselves.
5. Prioritise by damage: security and data-loss contradictions first, cosmetic last.
6. Also check the DECISION TREE in your scope (standards/decision-trees/) against the skills
   that cite it — a tree that disagrees with its own skills is the worst case, because agents
   are instructed to consult the tree BEFORE the skill.

Aim to settle 12-20 candidate conflicts properly rather than skim 100. Depth over breadth.`,
  { label: `contra:${t.key}`, phase: 'Hunt', schema: SCHEMA, effort: 'high' })))

const good = results.filter(Boolean)
const all = good.flatMap((r) => r.contradictions || [])
const real = all.filter((c) => c.which_is_correct !== 'BOTH_CONTEXTUAL' && c.which_is_correct !== 'UNRESOLVED')
const sec = all.filter((c) => c.severity === 'security' || c.severity === 'data-loss')
const fp = good.flatMap((r) => r.false_positives_rejected || [])

log(`${all.length} contradictions found (${real.length} resolved), ${sec.length} security/data-loss severity, ${fp.length} false positives correctly rejected.`)

return {
  topics: good.map((r) => ({ topic: r.topic, pairs_examined: r.pairs_examined, health: r.health_note })),
  contradictions: all,
  high_severity: sec,
  false_positives_rejected: fp,
  totals: { found: all.length, resolved: real.length, high_severity: sec.length, false_positives: fp.length },
}
