export const meta = {
  name: 'sfskills-agent-playbook-review',
  description: 'Read-only deep review of all 48 run-time agent playbooks: would each actually produce expert Salesforce output, or does it only satisfy the contract structurally',
  phases: [{ title: 'Review' }],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const OUT = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad/agentreview'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY. Create/edit/delete NOTHING under ${REPO}. Notes go only under ${OUT}/.
Several build agents are writing to this repo right now.

*** MEMORY RULE — MANY AGENTS IN PARALLEL ON A 16 GB MACHINE ***
DO NOT run scripts/search_knowledge.py (~2.9 GB peak), validate_repo.py, skill_sync.py or
build_index.py. Use grep/ls/sed/file reads. WebSearch/WebFetch are free of local memory.

WHY THIS EXISTS. The run-time agents ARE the product — a user types /refactor-apex or
/design-object and what comes back is the entire value proposition. They have been checked
for STRUCTURAL compliance (all 48 pass the 8-section AGENT_CONTRACT shape) but nobody has ever
asked the only question that matters: WOULD FOLLOWING THIS PLAYBOOK ACTUALLY PRODUCE EXPERT
SALESFORCE WORK, or does it merely look complete?

Relevant history you should assume as fact:
- 555 of 1,058 "Mandatory Reads" entries were machine-generated echo stubs (description = the
  slug, title-cased). Those were removed in a cleanup, so lists are now much shorter — but the
  cleanup also left 133 entries with NO justification at all across 23 agents, and some agents
  lost citations they genuinely needed.
- A parallel fabrication hunt is finding invented Salesforce facts in the skill corpus. Agents
  that quote Salesforce facts inline (rather than deferring to a skill) carry the same risk.
- The measured corpus gaps: only 11% of skills quote a verbatim platform error string and only
  8.4% name the exact licence/permission that gates a feature.

READ THESE FIRST (they define the contract you are judging against):
  agents/_shared/AGENT_CONTRACT.md
  agents/_shared/DELIVERABLE_CONTRACT.md
  agents/_shared/AGENT_DISAMBIGUATION.md
Then read one agent widely regarded as strong and one that looks thin, so your bar is calibrated
against this repo rather than against an abstract ideal.
`

const SCHEMA = {
  type: 'object',
  properties: {
    batch: { type: 'string' },
    agents_reviewed: { type: 'array', items: { type: 'string' } },
    assessments: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          agent: { type: 'string' },
          would_produce_expert_output: { type: 'string', enum: ['YES', 'PARTIALLY', 'NO'] },
          strongest_aspect: { type: 'string' },
          weakest_aspect: { type: 'string' },
          missing_decision_points: { type: 'array', description: 'judgement calls a real practitioner makes that the playbook never asks about', items: { type: 'string' } },
          unresolvable_citations: { type: 'array', description: 'cited skills/templates/trees that do not exist on disk — verify with ls', items: { type: 'string' } },
          undescribed_reads: { type: 'string', description: 'count of Mandatory Reads entries with no justification' },
          inline_salesforce_claims: { type: 'array', description: 'Salesforce facts asserted in the AGENT.md itself rather than deferred to a skill — these are unreviewed fabrication risk', items: { type: 'string' } },
          top_improvement: { type: 'string', description: 'the single change that would most improve this agent output' },
        },
        required: ['agent', 'would_produce_expert_output', 'strongest_aspect', 'weakest_aspect', 'missing_decision_points', 'unresolvable_citations', 'undescribed_reads', 'inline_salesforce_claims', 'top_improvement'],
      },
    },
    cross_cutting_patterns: { type: 'array', description: 'weaknesses shared across this batch that should be fixed contract-wide rather than per agent', items: { type: 'string' } },
    ranked_priorities: { type: 'array', description: 'the improvements in this batch ranked by user impact', items: { type: 'string' } },
  },
  required: ['batch', 'agents_reviewed', 'assessments', 'cross_cutting_patterns', 'ranked_priorities'],
}

const BATCHES = [
  { key: 'apex-core', agents: 'apex-refactorer trigger-consolidator test-class-generator soql-optimizer apex-builder security-scanner', note: 'The developer core. Judge whether the playbook would actually produce bulk-safe, CRUD/FLS-enforcing, testable Apex — or generic advice. Check they route through templates/apex/ rather than improvising a trigger framework.' },
  { key: 'lwc-flow', agents: 'lwc-builder lwc-auditor lwc-debugger flow-builder flow-analyzer flow-orchestrator-designer', note: 'Judge whether the LWC agents would catch real accessibility/performance/security defects, and whether the Flow agents genuinely apply the Flow-vs-Apex decision tree rather than defaulting.' },
  { key: 'admin-design', agents: 'object-designer permission-set-architect field-impact-analyzer design-duplicate-rule custom-metadata-and-settings-designer path-designer', note: 'The highest-traffic admin work. These make IRREVERSIBLE decisions (API names, master-detail vs lookup, record-name type). Judge whether the playbook forces the agent to surface irreversibility BEFORE acting — that is the single most valuable behaviour an admin agent can have.' },
  { key: 'admin-service', agents: 'assignment-and-auto-response-rules-designer business-hours-and-holidays-configurator entitlement-and-milestone-designer omni-channel-routing-designer knowledge-article-taxonomy-agent lead-routing-rules-designer', note: 'Service/routing configuration. Judge whether they account for the Salesforce order of execution and rule-evaluation ordering, which is where these configurations actually break.' },
  { key: 'data-integration', agents: 'data-loader-pre-flight data-model-reviewer csv-to-object-mapper bulk-migration-planner integration-catalog-builder', note: 'Data and integration. Judge whether they surface the failure modes that actually bite: load ordering, external-id idempotency, skew, API limit consumption, rollback strategy.' },
  { key: 'devops-arch', agents: 'deployment-risk-scorer changeset-builder release-train-planner sandbox-strategy-designer waf-assessor audit-router', note: 'DevOps and governance. Judge whether the risk scoring is grounded in real deployment failure modes or is a generic checklist. audit-router consolidates 15 auditors — check the dispatch is coherent.' },
  { key: 'strategic-vertical', agents: 'fit-gap-analyzer story-drafter process-flow-mapper config-workbook-author experience-cloud-admin-designer omnistudio-designer', note: 'Strategic + vertical. omnistudio-designer is brand new this session — review it hardest. config-workbook-author was flagged for hard-coding references to deprecated agents; verify.' },
  { key: 'agentforce-misc', agents: 'agentforce-builder agentforce-action-reviewer user-access-diff profile-to-permset-migrator sales-stage-designer email-template-modernizer automation-migration-router', note: 'Agentforce + remaining. Agentforce naming changed repeatedly through 2025-2026 — flag any stale product naming. automation-migration-router consolidates 4 migrators; check the dispatch table is real.' },
]

phase('Review')
log(`Deep playbook review across ${BATCHES.length} batches of run-time agents.`)

const results = await parallel(BATCHES.map((b) => () => agent(`${COMMON}

YOU ARE THE PLAYBOOK REVIEWER FOR BATCH: ${b.key}
AGENTS: ${b.agents}
FOCUS: ${b.note}

For EACH agent in your batch:
1. Read its full agents/<name>/AGENT.md and its inputs.schema.json if present. Read its
   commands/ wrapper too if one exists.
2. THE CENTRAL TEST — simulate it. Take a realistic request this agent would receive and walk
   the playbook literally, step by step, as a competent-but-not-expert model would. Where does
   it under-specify? What judgement call does a real senior practitioner make that the playbook
   never prompts for? That gap is the finding.
3. VERIFY ITS CITATIONS RESOLVE. For each cited skill/template/decision tree:
     ls skills/<domain>/<slug>/SKILL.md   /   ls templates/...   /   ls standards/decision-trees/...
   Report every unresolvable citation — an agent told to read a file that does not exist will
   either hallucinate its contents or silently skip its grounding.
4. COUNT UNDESCRIBED READS: Mandatory Reads entries that are just a path with no justification.
     grep -cE '^\\s*[0-9]+\\. \`skills/[a-z-]+/[a-z0-9-]+\`\\s*$' agents/<name>/AGENT.md
5. INLINE SALESFORCE CLAIMS — important. Where does the AGENT.md itself assert a Salesforce
   fact (a limit, an error string, an API name, a permission) instead of deferring to a skill?
   Those assertions never went through skill review and carry the same fabrication risk a
   parallel hunt is finding in the corpus. List them; spot-check the riskiest against official
   docs with WebFetch.
6. Judge would_produce_expert_output honestly. YES means a careful model following this
   playbook produces work a senior Salesforce practitioner would sign off. Most agents will
   be PARTIALLY — that is fine and useful. Grade-inflation makes this whole exercise worthless.

Then step back: what weaknesses recur across your whole batch? Those belong in
AGENT_CONTRACT.md as a contract-level fix, not in eight separate agents.
Rank your batch's improvements by USER IMPACT — what would most change the quality of what a
real user receives.`, { label: `agents:${b.key}`, phase: 'Review', schema: SCHEMA, effort: 'high' })))

const good = results.filter(Boolean)
const all = good.flatMap((r) => r.assessments || [])
const yes = all.filter((a) => a.would_produce_expert_output === 'YES').length
const partial = all.filter((a) => a.would_produce_expert_output === 'PARTIALLY').length
const no = all.filter((a) => a.would_produce_expert_output === 'NO').length
const broken = all.flatMap((a) => a.unresolvable_citations || [])
const inline = all.flatMap((a) => a.inline_salesforce_claims || [])

log(`Reviewed ${all.length} agents: ${yes} YES / ${partial} PARTIALLY / ${no} NO. ${broken.length} unresolvable citations, ${inline.length} inline Salesforce claims flagged.`)

return {
  batches: good.map((r) => ({ batch: r.batch, cross_cutting: r.cross_cutting_patterns, priorities: r.ranked_priorities })),
  assessments: all,
  totals: { reviewed: all.length, yes, partial, no, unresolvable_citations: broken.length, inline_claims: inline.length },
  unresolvable_citations: broken,
}
