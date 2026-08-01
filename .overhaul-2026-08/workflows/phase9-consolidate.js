export const meta = {
  name: 'sfskills-phase9-consolidate',
  description: 'Un-break the repo after Wave 3: fix the orphan gate that 501 newly-orphaned skills now trip, harden the depth gates that produced the stub wave, and restore the 19 agent citations that were over-removed',
  phases: [
    { title: 'Requirements' },
    { title: 'Build' },
    { title: 'QA' },
    { title: 'Review' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Branch: overhaul/2026-08-01-checkpoint. Do NOT create branches, commit, or push.
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.
Full handoff list from the previous wave: ${SCRATCH}/handoffs.json (41 entries).

MACHINE CONSTRAINT — NON-NEGOTIABLE: 16 GB Mac, already OOM-killed once on this project.
Run ONE heavy process at a time. A single 'validate_repo.py' run peaks around 3 GB. Never run
two validations, benchmarks or searches concurrently. Prefer --changed-only and --agents over
full runs; a full run takes ~12 minutes.

WHY THIS WAVE EXISTS. The previous wave ran four items in parallel against a shared tree and
they interfered. Two facts to internalise before you touch anything:
 1. A citation-cleanup agent removed 487 of 1,031 distinct skill citations from agents/**
    (distinct cited skills: 1031 -> 544). That was mostly CORRECT — 555 of 1,058 Mandatory
    Reads were machine-generated echo stubs whose description was just the slug title-cased.
    BUT the matching gate change never landed, so **501 skills are now orphaned and the
    current ERROR-level orphan gate would emit 501 ERRORs on a full validate run.**
 2. The same cleanup stripped 'admin/agent-output-formats' from 16 agents' frontmatter
    dependencies while leaving the body citation, which **fails the newly-enabled MCP CI job**
    (test_agent_bundle.TestCitationsMatchDependencies), and over-removed 3 citations that
    were legitimately load-bearing.

THE GOAL IS NOT "make the gate green". It is to make the gate MEASURE THE RIGHT THING. The
old gate is what caused the padding: it ERRORed on any uncited skill with no cap, so the
cheapest way to pass was to mass-cite via patch_agent_skill.py. Its message text literally
instructs the reader to do that. That is Goodhart's law encoded in a validator.

HOUSE RULES:
- Do NOT hand-edit generated artifacts: registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md.
- Do NOT run scripts/skill_sync.py or scripts/build_index.py — the orchestrator runs those
  centrally afterwards.
- Never make a Salesforce claim without official-source grounding.
- FILE OWNERSHIP IS STRICT. One other item runs alongside you; touching its files fails review.
`

const ITEMS = [
  {
    id: 'validator-gates',
    title: 'Fix the orphan gate that created the padding, and add the depth gates that would have stopped the stub wave',
    owns: [
      'scripts/validate_repo.py',
      'pipelines/validators.py',
      'CLAUDE.md',
    ],
    goal: `PART 1 — THE ORPHAN GATE (load-bearing; without it the tree is red by 501 ERRORs).

In scripts/validate_repo.py, _check_orphan_skills (around lines 407-459, issue raised ~450):
(a) DEMOTE bare orphan-ness from ERROR to WARN. This RESTORES the already-documented contract:
    AGENT_RULES.md:132, commands/new-skill.md:108,112 and agents/_shared/AGENT_CONTRACT.md:169
    all already say WARN. Only CLAUDE.md:37 and the code say ERROR — so the code and one doc
    are the outliers, not the other four.
(b) REWRITE THE MESSAGE TEXT. The current message instructs the reader to run
    patch_agent_skill.py with a description to clear the ERROR. That string IS the incentive
    loop that produced 555 echo stubs. Replace it with something that makes the right action
    obvious and the wrong action unattractive — roughly: "skill <id> is cited by no run-time
    agent (advisory). Wire it only if an agent's output would be wrong without it; otherwise
    leave it uncited or mark runtime_orphan: true with a reason." Word it yourself, but do not
    reintroduce a 'run this command to make the warning go away' instruction.
(c) ADD THE QUALITY GATES that should carry ERROR severity instead — this is the inversion
    that fixes the incentive:
      - ERROR when a Mandatory Reads entry's description equals the de-kebabed slug (the echo
        stub signature). scripts/patch_agent_skill.py already exports is_echo_description();
        IMPORT AND REUSE IT so writer and gate cannot drift. Verify it is actually importable
        before claiming so — a previous agent documented this as done when it was not.
      - Consider ALSO stripping a leading 'Label: ' prefix before comparing: audit-router has
        25 reads shaped 'Analytics/reporting: Analytics dashboard json' that dodge exact
        match. If you add prefix-stripping, those 25 light up immediately — so either fix
        those 25 lines in the same change, or implement the predicate and leave it at WARN
        with a comment explaining the staged rollout. Decide and justify.
      - WARN above a sensible Mandatory Reads cap per agent (~40).
(d) Update CLAUDE.md:37, which currently asserts the validator "errors on any skill that's
    neither cited by an agent nor explicitly orphaned" — that becomes false. Reword so the
    ERROR is the QUALITY rule (no echo stubs, bounded lists) and the WARN is the coverage
    advisory. You own CLAUDE.md for this purpose only; do not make unrelated edits to it.
    NOTE: CLAUDE.md also has two live doc-count ERRORs (47 vs canonical 48) — a DIFFERENT item
    owns those. Do not fix them and do not fight over the file; make only the gate wording edit.

POLICY — DO NOT bulk-set runtime_orphan: true on the 501 skills. That is the identical gaming
pattern under a different label. The explicit-orphan count must stay at 41.

PART 2 — DEPTH GATES (pipelines/validators.py).
The stub wave shipped because the only depth checks were trivially satisfiable: line ~281
warns only when anti-pattern count < 5 and all 38 stubs sat at exactly 5; line ~296 errors
only on a missing/empty '## Official Sources Used' heading, which one rubber-stamped
per-domain list satisfied. Add (severity WARN unless you can justify ERROR):
  (a) references/llm-anti-patterns.md under ~2,000 bytes (corpus p10 is 2,966)
  (b) references/examples.md containing zero code fences (844/1027 already have one)
  (c) two skills in the same domain sharing a byte-identical '## Official Sources Used' block
Measure the current corpus-wide hit count for each BEFORE choosing severity — a gate that
instantly lights up 200 skills is not shippable as an ERROR. Report the counts.

ACCEPTANCE: after your change, 'python3 scripts/validate_repo.py --skills-only --shard 0/8'
must not report the 501 orphans as ERRORs, and the new quality gates must fire on a
deliberately-constructed bad example. Prove both.`,
  },
  {
    id: 'agent-citations-restore',
    title: 'Restore the 19 citations that were over-removed, without re-introducing padding',
    owns: [
      'agents/agentforce-builder/AGENT.md',
      'agents/apex-builder/AGENT.md',
      'agents/apex-refactorer/AGENT.md',
      'agents/data-loader-pre-flight/AGENT.md',
      'agents/data-model-reviewer/AGENT.md',
      'agents/deployment-risk-scorer/AGENT.md',
      'agents/experience-cloud-admin-designer/AGENT.md',
      'agents/flow-builder/AGENT.md',
      'agents/integration-catalog-builder/AGENT.md',
      'agents/lwc-auditor/AGENT.md',
      'agents/lwc-builder/AGENT.md',
      'agents/object-designer/AGENT.md',
      'agents/security-scanner/AGENT.md',
      'agents/soql-optimizer/AGENT.md',
      'agents/test-class-generator/AGENT.md',
      'agents/waf-assessor/AGENT.md',
      'agents/_shared/SKILL_MAP.md',
    ],
    goal: `PART 1 — THE 16 BROKEN FRONTMATTER DEPENDENCIES (breaks the new MCP CI job).
16 agents cite 'skills/admin/agent-output-formats' in their BODY but no longer declare it in
frontmatter dependencies.skills. test_agent_bundle.TestCitationsMatchDependencies fails with
"16 citation/dependency mismatch(es)".

The 16: agentforce-builder, apex-builder, apex-refactorer, data-loader-pre-flight,
data-model-reviewer, deployment-risk-scorer, experience-cloud-admin-designer, flow-builder,
integration-catalog-builder, lwc-auditor, lwc-builder, object-designer, security-scanner,
soql-optimizer, test-class-generator, waf-assessor.

FIRST DECIDE WHICH DIRECTION IS CORRECT — do not assume restoring is right. For each agent ask:
does it genuinely need admin/agent-output-formats to produce correct output?
  - If YES: restore the '    - admin/agent-output-formats' frontmatter line (or use
    'python3 scripts/migrate_agent_dependencies.py --agent <id> --force' — read its --help first).
  - If NO: remove the BODY citation instead, so the two agree in the other direction.
A blanket restore across all 16 without asking would be exactly the reflex that produced the
padding. Justify your choice per agent, even if the answer is the same for most of them.
Verify with: cd mcp/sfskills-mcp && python3 -m unittest tests.test_agent_bundle -v

PART 2 — THREE OVER-REMOVED CITATIONS. These were legitimately load-bearing at HEAD and their
removal orphaned real skills:
  - agents/lwc-builder/AGENT.md: re-add dependency '- lwc/file-upload-patterns' AND the
    numbered Mandatory Read entry for skills/lwc/file-upload-patterns.
  - agents/integration-catalog-builder/AGENT.md: re-add dependencies
    '- integration/connect-rest-api-patterns' and '- integration/salesforce-data-pipeline-etl',
    plus their numbered Mandatory Reads entries, e.g.
      16. skills/integration/connect-rest-api-patterns — Connect API vs raw SObject
      18. skills/integration/salesforce-data-pipeline-etl — Bulk + CDC lake pipelines
Confirm each of those three skills exists on disk first.

CRITICAL QUALITY RULE: every read you (re)add MUST carry a real, human-written description
explaining WHY THAT AGENT needs THAT skill. Never a description that merely restates the slug
— that is the echo-stub pattern this whole effort exists to remove, and a new gate is being
added in parallel that will ERROR on exactly that shape.

PART 3 — SKILL_MAP.md. Several agents shrank by 100+ reads (lwc-builder 98 -> 49,
integration-catalog-builder 66 -> 26). Any agents/_shared/SKILL_MAP.md entry that enumerated
the padded set is now stale. Spot-check every reworked agent's entry and correct the ones that
no longer match reality. object-designer's entry was already honest — verify rather than assume.

DO NOT touch scripts/validate_repo.py, pipelines/validators.py or CLAUDE.md — a concurrent
item owns those. Do not re-pad any agent to make a gate green.`,
  },
]

const REQ_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verified_current_state: { type: 'array', items: { type: 'string' } },
    decisions: { type: 'array', description: 'judgement calls made and the reasoning', items: { type: 'string' } },
    deliverables: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'action', 'what'] } },
    acceptance_criteria: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, verify_command: { type: 'string' }, expected: { type: 'string' } }, required: ['criterion', 'verify_command', 'expected'] } },
    out_of_scope: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verified_current_state', 'decisions', 'deliverables', 'acceptance_criteria', 'out_of_scope'],
}

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } }, required: ['path', 'action', 'summary'] } },
    measurements: { type: 'array', items: { type: 'string' } },
    judgement_calls: { type: 'array', items: { type: 'string' } },
    handoff_to_orchestrator: { type: 'array', items: { type: 'string' } },
    newly_revealed_problems: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'measurements', 'judgement_calls', 'handoff_to_orchestrator', 'newly_revealed_problems', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    criteria_results: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT_TESTABLE'] }, command_run: { type: 'string' }, actual_output: { type: 'string' } }, required: ['criterion', 'result', 'command_run', 'actual_output'] } },
    defects: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } }, required: ['severity', 'file', 'description'] } },
    gate_behaviour_proof: { type: 'string', description: 'proof the new/changed gates fire on bad input and stay quiet on good input' },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'defects', 'gate_behaviour_proof'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    incentive_analysis: { type: 'string', description: 'does the new gate reward the right behaviour, or has it created a new way to game it' },
    factual_errors: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, claim: { type: 'string' }, why_wrong: { type: 'string' }, correction: { type: 'string' } }, required: ['file', 'claim', 'why_wrong', 'correction'] } },
    canon_violations: { type: 'array', items: { type: 'string' } },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'incentive_analysis', 'factual_errors', 'canon_violations', 'required_changes'],
}

phase('Requirements')
log('Consolidation: fixing the gate that caused the padding, and the 19 over-removed citations.')

const results = await pipeline(
  ITEMS,
  (item) => agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for "${item.id}". SPECIFY ONLY — modify nothing.

ITEM: ${item.title}
OWNS:
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

Verify the current state first — the tree has changed a lot and several prior claims about it
turned out to be stale. Record the commands you ran. Every acceptance criterion must be one
command with a stated expected result.`,
    { label: `req:${item.id}`, phase: 'Requirements', schema: REQ_SCHEMA, effort: 'high' }),

  (spec, item) => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}". A separate QA agent and reviewer check you afterwards.

ITEM: ${item.title}
FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

SPEC:
${JSON.stringify(spec, null, 2)}

Run every verify_command. Every count you report must come from a command you ran. Record the
judgement calls you made — this item is mostly judgement, not mechanics. Put anything needing a
file you do not own into handoff_to_orchestrator.`,
    { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA, effort: 'high' })
    .then((build) => ({ item, spec, build })),

  (ctx) => agent(`${COMMON}

YOU ARE THE QA AGENT for "${ctx.item.id}". TEST; MODIFY NOTHING.

SPEC: ${JSON.stringify(ctx.spec, null, 2)}
BUILDER CLAIMS: ${JSON.stringify(ctx.build, null, 2)}

DO THIS (one heavy process at a time):
1. Run every acceptance-criteria verify_command; paste real output.
2. GATE BEHAVIOUR IS THE CORE TEST. For every gate added or changed, prove BOTH directions:
   construct a deliberately bad example in a temp dir (an echo-stub read, a tiny
   llm-anti-patterns.md, an examples.md with no code fence) and show the gate FIRES; then show
   it stays quiet on a known-good skill. A gate that never fires is exactly the defect this
   wave exists to remove — the repo already shipped several. Restore any temp files afterwards
   and confirm with git status.
3. Orphan count: confirm the 501 newly-orphaned skills no longer produce ERRORs, and that the
   EXPLICIT runtime_orphan count is still 41 (it must NOT have been bulk-set to hide the problem):
     grep -l "runtime_orphan: true" skills/*/*/SKILL.md | wc -l
4. MCP citation test: cd mcp/sfskills-mcp && python3 -m unittest tests.test_agent_bundle -v
5. Sample 5 restored/edited Mandatory Reads and confirm each description is a real human
   explanation, NOT a slug echo. Quote them.
6. Regression: python3 scripts/validate_repo.py --agents and
   python3 scripts/validate_repo.py --skills-only --shard 0/8. Paste results.
   Pre-existing stale-artifact ERRORs (registry/, docs/SKILLS.md) are EXPECTED — the
   orchestrator regenerates centrally. Those are not blockers. New errors are.
7. git status --short to confirm scope.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  (ctx) => agent(`${COMMON}

YOU ARE THE REVIEWER for "${ctx.item.id}". Modify nothing.

SPEC: ${JSON.stringify(ctx.spec, null, 2)}
BUILD: ${JSON.stringify(ctx.build, null, 2)}
QA: ${JSON.stringify(ctx.qa, null, 2)}

1. Read the real diff: cd "${REPO}" && git diff -- <owned paths>.
2. INCENTIVE ANALYSIS — your most important job. The previous gate was well-intentioned and
   produced 555 echo stubs because the cheapest way to satisfy it was to game it. Examine the
   NEW gate the same way: what is the cheapest way for a contributor to make it green? Is that
   cheapest path the behaviour we actually want? If a contributor can satisfy it by writing
   slightly-varied filler, say so — that is a REQUEST_CHANGES.
3. Check the WARN/ERROR split is defensible: an advisory that blocks nothing gets ignored, and
   an ERROR that lights up 200 skills on day one gets disabled (which is exactly what happened
   to the retrieval gate). Judge whether the chosen severities survive contact with a real
   contributor.
4. Verify claims about code you can check — e.g. that is_echo_description() is genuinely
   imported and shared between writer and gate rather than duplicated. A previous agent
   documented that as done when it was not; do not take it on trust.
5. For restored citations: confirm the descriptions are real explanations, and that nothing was
   restored merely to silence a gate.
REQUEST_CHANGES on any gameable gate, unproven claim, or factual error.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),
)

const done = results.filter(Boolean)
log(`Consolidation complete: ${done.length}/${ITEMS.length}`)

return done.map((r) => ({
  item_id: r.item?.id,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  incentive_analysis: r.review?.incentive_analysis,
  gate_behaviour_proof: r.qa?.gate_behaviour_proof,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  measurements: r.build?.measurements,
  judgement_calls: r.build?.judgement_calls,
  handoff_to_orchestrator: r.build?.handoff_to_orchestrator,
  newly_revealed_problems: r.build?.newly_revealed_problems,
  not_done: r.build?.not_done,
  qa_defects: r.qa?.defects,
  factual_errors: r.review?.factual_errors,
  required_changes: r.review?.required_changes,
}))
