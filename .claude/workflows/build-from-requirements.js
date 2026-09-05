export const meta = {
  name: 'build-from-requirements',
  description: 'Build one milestone of an approved build plan: dependency-ordered runner -> tester -> doc keeper per step, then the milestone verifier and the G3 request',
  whenToUse: 'After G2 (plan approval) and after every earlier milestone\'s G3. Pass args {build_dir: ".sfskills/builds/<build-id>", milestone: "<milestone-id>"}; optional {max_rounds}. It refuses to start if the preceding gate is not approved, builds exactly one milestone, and stops for the human. It never deploys.',
  phases: [
    { title: 'Preflight', detail: 'gate check: refuse unless the preceding gate is approved', model: 'sonnet' },
    { title: 'Build', detail: 'dependency-ordered rounds of runner -> tester -> doc keeper' },
    { title: 'Verify', detail: 'cross-step milestone verification and the acceptance report', model: 'opus' },
  ],
}

// ---------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------
const a = typeof args === 'string' ? JSON.parse(args) : (args || {})
const BUILD_DIR = a.build_dir
const MILESTONE = a.milestone
if (!BUILD_DIR) throw new Error('args.build_dir is required — the build directory, e.g. ".sfskills/builds/<build-id>"')
if (!MILESTONE) throw new Error('args.milestone is required — one milestone id. This workflow builds exactly one milestone per invocation, because G3 is per milestone.')
// A round is one `next` + one wave of runnable steps. 20 is a runaway guard,
// not a coverage limit: a milestone whose dependency chain is deeper than this
// stops with `stopped_because` saying so rather than truncating silently.
const MAX_ROUNDS = Number(a.max_rounds) > 0 ? Math.floor(Number(a.max_rounds)) : 20

const PLAN = `${BUILD_DIR}/plan.json`

const HOUSE = `Repo root is the current working directory. The build directory is ${BUILD_DIR}; the plan file is ${PLAN}; the milestone being built is ${MILESTONE}.
The contract you are working under is standards/build-orchestration.md — read it if anything below is ambiguous. Also follow agents/_shared/AGENT_CONTRACT.md and agents/_shared/DELIVERABLE_CONTRACT.md.

HARD RULES:
- NEVER deploy. Never run \`sf project deploy start\`, \`sf project deploy validate\`, or any command that touches an org. This layer produces deploy-ready artefacts and a deploy order; a human deploys, outside the loop.
- Write ONLY inside ${BUILD_DIR}. Never modify skills/, agents/, templates/, registry/, vector_index/ or docs/ — a build consumes the library, it does not edit it.
- \`python3 scripts/build_plan.py\` is the single writer of plan state and of every rendered view (PLAN.md, CLARIFICATIONS.md, reports). Never hand-edit a rendered view. If an invocation shape is rejected, read \`python3 scripts/build_plan.py --help\` and \`<subcommand> --help\` for the real flags.
- Agents never approve a human gate. \`build_plan.py gate\` is the only writer of gate records and a human is the only decider.
- No secrets in artefacts, envelopes or output; redact with [REDACTED].
- If a step needs Salesforce knowledge no cited skill states, mark it blocked with reason \`skill-gap\` (§ 8). That is the signal to deepen a skill — never to freestyle a pattern.
`

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const PREFLIGHT = {
  type: 'object',
  required: ['ok', 'reason', 'milestone', 'runnable', 'all_steps'],
  properties: {
    ok: { type: 'boolean', description: 'true only if every gate condition below is satisfied' },
    reason: { type: 'string', description: 'if ok=false, the single specific thing missing plus the exact command that fixes it; if ok=true, what you confirmed' },
    milestone: { type: 'string' },
    plan_status: { type: 'string' },
    runnable: { type: 'array', items: { type: 'string' }, description: 'step ids runnable right now' },
    all_steps: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'depends_on', 'status'],
        properties: { id: { type: 'string' }, depends_on: { type: 'array', items: { type: 'string' } }, status: { type: 'string' } },
      },
      description: 'every step in this milestone',
    },
    gates_seen: { type: 'array', items: { type: 'string' }, description: 'the human_gates[] records you actually read, verbatim-ish' },
  },
}

const NEXT_OUT = {
  type: 'object',
  required: ['milestone', 'runnable', 'remaining', 'all_documented'],
  properties: {
    milestone: { type: 'string' },
    runnable: {
      type: 'array',
      items: {
        type: 'object',
        required: ['step_id', 'agent', 'type', 'output_paths'],
        properties: {
          step_id: { type: 'string' },
          agent: { type: 'string', description: 'the step\'s owning run-time agent id, from the plan' },
          type: { type: 'string' },
          title: { type: 'string' },
          depends_on: { type: 'array', items: { type: 'string' } },
          output_paths: {
            type: 'array',
            items: { type: 'string' },
            description: 'EVERY path this step writes, repo-relative. Drives the concurrency guard: two steps writing the same path are never run together. Empty array = undeclared, and the step is run alone.',
          },
        },
      },
    },
    remaining: { type: 'number', description: 'steps in this milestone not yet at status documented' },
    all_documented: { type: 'boolean' },
    note: { type: 'string' },
  },
}

const RUN_OUT = {
  type: 'object',
  required: ['step_id', 'status', 'artefacts'],
  properties: {
    step_id: { type: 'string' },
    status: { type: 'string', enum: ['built', 'blocked', 'failed'] },
    artefacts: { type: 'array', items: { type: 'string' }, description: 'paths actually written under artefacts/<step-id>/' },
    envelope_path: { type: 'string' },
    blocked_reason: { type: 'string', description: 'required when status=blocked; prefix with "skill-gap: " when that is the cause' },
    notes: { type: 'string' },
  },
}

const TEST_OUT = {
  type: 'object',
  required: ['step_id', 'status', 'passed', 'failed'],
  properties: {
    step_id: { type: 'string' },
    status: { type: 'string', enum: ['tested', 'failed', 'blocked'] },
    passed: { type: 'boolean', description: 'true only when every declared test plus the always-on xml and manifest checks passed' },
    failed: { type: 'array', items: { type: 'string' }, description: 'one line per failing or unrunnable test: what it was and what it printed' },
    results_path: { type: 'string' },
    tests_run: { type: 'number' },
  },
}

const DOC_OUT = {
  type: 'object',
  required: ['step_id', 'status'],
  properties: {
    step_id: { type: 'string' },
    status: { type: 'string', enum: ['documented', 'failed'] },
    files_updated: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
}

const MILESTONE_OUT = {
  type: 'object',
  required: ['milestone', 'report_path', 'passed', 'manual_checklist', 'gate_command'],
  properties: {
    milestone: { type: 'string' },
    report_path: { type: 'string', description: `${BUILD_DIR}/reports/MILESTONE-<id>-REPORT.md` },
    passed: { type: 'boolean', description: 'true only when every step is documented and every cross-step check passed' },
    manual_checklist: { type: 'array', items: { type: 'string' }, description: 'the manual acceptance tests the human ticks at G3' },
    gate_command: { type: 'string', description: 'the real command a human runs to record G3 on this milestone' },
    findings: { type: 'array', items: { type: 'object', required: ['problem'], properties: { problem: { type: 'string' }, severity: { type: 'string' }, step_id: { type: 'string' } } } },
    deploy_order: { type: 'array', items: { type: 'string' } },
  },
}

// ---------------------------------------------------------------------------
// Concurrency guard — no two steps writing the same path run at the same time.
// The script cannot read the plan, so it partitions on the output_paths the
// `next` agent reports. Batches run one after another; within a batch every
// step writes a disjoint set of paths.
// ---------------------------------------------------------------------------
function normalisePath(p) {
  return String(p == null ? '' : p).trim().replace(/^\.\//, '').replace(/\/+$/, '')
}
function pathsCollide(x, y) {
  return x === y || x.startsWith(`${y}/`) || y.startsWith(`${x}/`)
}
function conflictFreeBatches(runnable) {
  const batches = []
  for (const step of runnable) {
    const paths = (step.output_paths || []).map(normalisePath).filter(Boolean)
    // Undeclared outputs cannot be proven disjoint from anything, so the step
    // gets a batch to itself rather than a hopeful concurrent slot.
    const isolated = paths.length === 0
    let placed = false
    if (!isolated) {
      for (const batch of batches) {
        if (batch.isolated) continue
        const collides = batch.paths.some((p) => paths.some((q) => pathsCollide(p, q)))
        if (collides) continue
        batch.items.push(step)
        for (const p of paths) batch.paths.push(p)
        placed = true
        break
      }
    }
    if (!placed) batches.push({ items: [step], paths, isolated })
  }
  return batches
}

// ---------------------------------------------------------------------------
// Phase 1 — Preflight. The gate rule is the whole point: refuse, do not warn.
// ---------------------------------------------------------------------------
phase('Preflight')
const pre = await agent(
  `${HOUSE}
TASK: decide whether milestone ${MILESTONE} may start. READ-ONLY — run build_plan.py and read ${PLAN}; change nothing, build nothing.

1. Run \`python3 scripts/build_plan.py status ${PLAN}\` (every subcommand takes the plan file, not the build directory; discover the real argument shape from --help if one is rejected).
2. Run \`python3 scripts/build_plan.py next ${PLAN} --milestone ${MILESTONE}\`. It prints the runnable steps as JSON on stdout, or \`[]\` plus the reason on stderr when nothing may run — read both.
3. Read ${PLAN} — specifically \`status\`, \`human_gates[]\`, \`milestones[]\` and every step whose milestone is ${MILESTONE}.

Set ok=true ONLY IF ALL of these hold, each confirmed by something you actually read:
- the plan validates and its \`status\` is \`approved\` or \`building\` — approving the G2 gate is what moves it off \`verified\`, so a plan still sitting at \`verified\` has not been approved;
- the G2 plan-approval gate is recorded in \`human_gates[]\` with status \`approved\`;
- every milestone ordered BEFORE ${MILESTONE} has its G3 acceptance gate recorded \`approved\` (a milestone with no G3 record has not been accepted);
- milestone ${MILESTONE} exists in the plan and has at least one step not yet at status \`documented\`.

If any condition fails, set ok=false and make \`reason\` name the ONE specific thing that is missing plus the exact command the human should run next (e.g. the \`build_plan.py gate\` invocation, or \`/verify-plan\`). Do not soften it and do not proceed anyway.

You never approve a gate. \`build_plan.py gate\` is the only writer and the human is the only decider — if the gate is missing, the answer is "no", not "record it".

Return {ok, reason, milestone, plan_status, runnable, all_steps, gates_seen}.`,
  { label: 'preflight', phase: 'Preflight', schema: PREFLIGHT, model: 'sonnet', effort: 'low' }
)
if (!pre) throw new Error(`preflight agent failed — nothing was built in ${BUILD_DIR}. Re-run /run-build.`)
if (!pre.ok) throw new Error(`refusing to build milestone ${MILESTONE}: ${pre.reason}`)

const milestoneSteps = pre.all_steps || []
log(`Gate OK — ${pre.reason}`)
log(`milestone ${pre.milestone || MILESTONE}: ${milestoneSteps.length} step(s), ${(pre.runnable || []).length} runnable now, ${milestoneSteps.filter((s) => s.status === 'documented').length} already documented`)

// ---------------------------------------------------------------------------
// Phase 2 — Build. Rounds of: ask for `next`, partition, run -> test -> doc.
// pipeline(), not parallel(): a fast step reaches its doc keeper while a slow
// sibling is still building.
// ---------------------------------------------------------------------------
phase('Build')

function nextPrompt(round, excludedIds) {
  return `${HOUSE}
TASK: report what is runnable RIGHT NOW in milestone ${MILESTONE}. READ-ONLY — run build_plan.py and read ${PLAN}; change nothing, build nothing. This is round ${round} of at most ${MAX_ROUNDS}.

1. Run \`python3 scripts/build_plan.py next ${PLAN} --milestone ${MILESTONE}\` (the plan file, not the build directory). It prints \`[]\` on stdout and the reason on stderr when nothing may run.
2. For each step it returns, read that step in ${PLAN} and report: \`step_id\`, the step's owning \`agent\` id, its \`type\`, its \`depends_on\`, and \`output_paths\`.
3. \`output_paths\` = EVERY path the step writes, repo-relative — its \`outputs[]\` entries resolved against ${BUILD_DIR}/artefacts/<step-id>/, plus any other file it declares it will write (a shared package.xml, a workbook section). This drives a concurrency guard: two steps that write the same path are never run at the same time. A missing or wrong path is a correctness bug, not a formatting one. If a step declares no outputs at all, return an empty array and say so in \`note\` — it will be run alone.
4. \`remaining\` = how many steps in milestone ${MILESTONE} are not yet at status \`documented\`. \`all_documented\` = true only when that count is 0.

EXCLUDE:
- any step whose \`depends_on\` are not ALL at status \`documented\`;
- any step from another milestone;
- any step already at status \`documented\`;
- these step ids, which failed or blocked earlier in this run and must not be retried here: ${JSON.stringify(excludedIds)}.

Return {milestone, runnable, remaining, all_documented, note}.`
}

function runPrompt(step) {
  return `${HOUSE}
TASK: execute build step ${step.step_id} of milestone ${MILESTONE}.
Inputs: {"build_dir": "${BUILD_DIR}", "step_id": "${step.step_id}"}

Read the step in ${PLAN} first: its \`agent\`, \`skills[]\`, \`templates[]\`, \`decision_trees[]\`, \`inputs{}\` and \`outputs[]\`. The plan names ${step.agent} (step type \`${step.type}\`) as the owning agent. Per agents/build-step-runner/AGENT.md Step 6, hand the step to that agent where your host can (Agent tool, \`subagent_type\` = ${step.agent}); otherwise read agents/${step.agent}/AGENT.md end to end — its Mandatory Reads included — and execute its Plan inline. Do not substitute a different agent or a different approach.

- READ every skill, template and decision-tree branch the step cites, before producing anything. That is what makes the output grounded rather than freestyled.
- Write artefacts ONLY under ${BUILD_DIR}/artefacts/${step.step_id}/, at exactly the paths the step's \`outputs[]\` declares. Write the run envelope under ${BUILD_DIR}/envelopes/${step.step_id}/. Touch nothing else.
- Record the run in the step's \`runs[]\` via \`build_plan.py\` and set the step status to \`built\` when the artefacts are complete. Re-running APPENDS a run; it never overwrites history.
- IDEMPOTENT: if this step is already at status \`built\`, do NOT rebuild it — return \`built\` with the artefacts already on disk. \`next\` offers \`pending\` steps only, so a \`tested\` or \`documented\` step never reaches you here; re-running one is a re-plan decision, not yours.
- If the step needs Salesforce knowledge no cited skill states, set status \`blocked\` with \`blocked_reason\` starting "skill-gap: " and name the missing fact. Do not fill the gap from memory.
- If an input the step needs is absent, status \`blocked\` with the missing input named. Do not invent it.
- \`set-status … blocked\` REQUIRES \`--blocked-reason\` (\`skill-gap\` is the reserved value); without it build_plan.py exits 1 and the plan on disk is unchanged.
- NEVER deploy.

Return {step_id, status, artefacts, envelope_path, blocked_reason?, notes}.`
}

function testPrompt(step) {
  return `${HOUSE}
TASK: run the molecular tests for build step ${step.step_id}.
Inputs: {"build_dir": "${BUILD_DIR}", "step_id": "${step.step_id}"}

Run exactly what the plan declares in that step's \`acceptance_tests[]\`, plus the always-on checks from standards/build-orchestration.md § 5:
- \`xml\` — ElementTree-parse every *.xml / *-meta.xml under ${BUILD_DIR}/artefacts/${step.step_id}/;
- \`manifest\` — every artefact type/member appears in package.xml and no package.xml member lacks a file.

RULES:
- NEVER invent a test, and never relax one to make it pass.
- If a declared \`checker\` script does not exist at its stated path, the step is \`blocked\` — not passed. A missing checker is a plan defect, not a free pass.
- \`command\` tests are stdlib-only and org-free. Refuse to run anything that touches an org or the network.
- \`manual\` tests are not runnable here: list them for the milestone gate and do not count them toward \`passed\`.
- Write the full results to ${BUILD_DIR}/tests/${step.step_id}/results.json, the per-test table to summary.md beside it, and set the step status to \`tested\` only when everything runnable passed. A missing declared checker is \`blocked --blocked-reason "missing-checker"\`; a failing test is \`failed\` with the failing test names in \`--result\`.
- IDEMPOTENT: re-running overwrites results.json for this step; it does not append duplicate step statuses.

\`passed\` is true only when every runnable declared test AND both always-on checks passed. Put one line per failure in \`failed\`, quoting what the runner printed.

Return {step_id, status, passed, failed, results_path, tests_run}.`
}

function docPrompt(step) {
  return `${HOUSE}
TASK: update the build's documentation for step ${step.step_id}, which is now tested.
Inputs: {"build_dir": "${BUILD_DIR}", "step_id": "${step.step_id}"}

Update, per standards/build-orchestration.md § 2 and § 6:
- PLAN.md — by running \`python3 scripts/build_plan.py render ${PLAN}\` (the plan file, not the build directory). NEVER hand-edit it or any other rendered view.
- ${BUILD_DIR}/workbook/ — the configuration-workbook section(s) this step's artefacts belong to.
- ${BUILD_DIR}/decisions.md — APPEND-ONLY. Record decisions this step made and the decision-tree branch each cites. If the runner reported a \`skill-gap\`, record the gap here: that is the signal to deepen a skill.
- ${BUILD_DIR}/traceability.md — the REQ -> step -> artefact -> test row(s) for this step.
Then set the step status to \`documented\` via \`build_plan.py set-status\`.

RULES:
- Document what actually happened. Read the artefacts under artefacts/${step.step_id}/ and the results at tests/${step.step_id}/results.json rather than restating the plan's intent.
- IDEMPOTENT per agents/build-doc-keeper/AGENT.md Step 8: workbook rows are keyed by \`row_id\` and traceability rows by \`req_id\` + \`step_id\` — delete this step's existing rows, then write the current set, leaving every other step's rows byte-identical. \`decisions.md\` is the exception: it is append-only and never rewritten, so write an entry only when no entry with the same step id, date and decision text is already there.
- Write only inside ${BUILD_DIR}.

Return {step_id, status, files_updated, notes}.`
}

const runStage = (prev, step) =>
  agent(runPrompt(step), { label: `run:${step.step_id}`, phase: 'Build', schema: RUN_OUT, agentType: 'build-step-runner' })
    .then((run) => ({ step, run, test: null, doc: null }))

const testStage = (prev) => {
  if (!prev || !prev.run || prev.run.status !== 'built') return prev
  return agent(testPrompt(prev.step), { label: `test:${prev.step.step_id}`, phase: 'Build', schema: TEST_OUT, agentType: 'step-tester', model: 'sonnet' })
    .then((test) => ({ ...prev, test }))
}

const docStage = (prev) => {
  if (!prev || !prev.test || prev.test.status !== 'tested' || !prev.test.passed) return prev
  return agent(docPrompt(prev.step), { label: `doc:${prev.step.step_id}`, phase: 'Build', schema: DOC_OUT, agentType: 'build-doc-keeper', model: 'sonnet' })
    .then((doc) => ({ ...prev, doc }))
}

const built = []
const failed = []
const blocked = []
const excluded = new Set()
let round = 0
let stoppedBecause = `reached max_rounds (${MAX_ROUNDS}) with work still outstanding`

while (round < MAX_ROUNDS) {
  round += 1
  const nxt = await agent(nextPrompt(round, [...excluded]), {
    label: `next:round-${round}`,
    phase: 'Build',
    schema: NEXT_OUT,
    model: 'sonnet',
    effort: 'low',
  })
  if (!nxt) {
    stoppedBecause = `the "next" agent returned nothing in round ${round} — stopping rather than guessing what is runnable`
    log(stoppedBecause)
    break
  }
  if (nxt.all_documented) {
    stoppedBecause = 'every step in the milestone is documented'
    log(`round ${round}: ${stoppedBecause}`)
    break
  }

  const offered = (nxt.runnable || []).filter((s) => s && s.step_id)
  const runnable = offered.filter((s) => !excluded.has(s.step_id))
  if (offered.length !== runnable.length) {
    log(`round ${round}: skipping ${offered.length - runnable.length} step(s) already failed or blocked earlier in this run`)
  }
  if (!runnable.length) {
    stoppedBecause = `round ${round}: nothing runnable left — ${nxt.remaining} step(s) still undocumented, held behind a failed or blocked dependency`
    log(stoppedBecause)
    break
  }

  const batches = conflictFreeBatches(runnable)
  const isolatedCount = batches.filter((b) => b.isolated).length
  log(`round ${round}: ${runnable.length} runnable step(s) in ${batches.length} conflict-free batch(es)${isolatedCount ? ` (${isolatedCount} run alone — undeclared output paths)` : ''}; ${nxt.remaining} step(s) still undocumented`)

  let progressed = 0
  for (let b = 0; b < batches.length; b += 1) {
    const batch = batches[b]
    if (batches.length > 1) {
      log(`round ${round} batch ${b + 1}/${batches.length}: ${batch.items.map((s) => s.step_id).join(', ')}`)
    }
    const results = await pipeline(batch.items, runStage, testStage, docStage)
    for (let i = 0; i < batch.items.length; i += 1) {
      const step = batch.items[i]
      const r = results[i]
      if (!r || !r.run) {
        failed.push({ step_id: step.step_id, stage: 'run', reason: 'the step runner returned nothing (agent died or was skipped)' })
        excluded.add(step.step_id)
        log(`  ${step.step_id}: FAILED — runner returned nothing`)
        continue
      }
      if (r.run.status === 'blocked') {
        blocked.push({ step_id: step.step_id, stage: 'run', reason: r.run.blocked_reason || 'blocked, no reason given' })
        excluded.add(step.step_id)
        log(`  ${step.step_id}: BLOCKED — ${r.run.blocked_reason || 'no reason given'}`)
        continue
      }
      if (r.run.status !== 'built') {
        failed.push({ step_id: step.step_id, stage: 'run', reason: `runner ended at status "${r.run.status}"${r.run.notes ? ` — ${r.run.notes}` : ''}` })
        excluded.add(step.step_id)
        log(`  ${step.step_id}: FAILED at run — status "${r.run.status}"`)
        continue
      }
      if (!r.test) {
        failed.push({ step_id: step.step_id, stage: 'test', reason: 'the tester returned nothing (agent died or was skipped) — the step is built but unverified' })
        excluded.add(step.step_id)
        log(`  ${step.step_id}: FAILED — tester returned nothing (artefacts exist but are unverified)`)
        continue
      }
      if (r.test.status === 'blocked') {
        blocked.push({ step_id: step.step_id, stage: 'test', reason: `tests unrunnable: ${(r.test.failed || []).join('; ') || 'no detail given'}` })
        excluded.add(step.step_id)
        log(`  ${step.step_id}: BLOCKED at test — ${(r.test.failed || []).join('; ') || 'no detail given'}`)
        continue
      }
      if (!r.test.passed) {
        failed.push({ step_id: step.step_id, stage: 'test', reason: `tests failed: ${(r.test.failed || []).join('; ') || 'no detail given'}` })
        excluded.add(step.step_id)
        log(`  ${step.step_id}: FAILED ${(r.test.failed || []).length} test(s) — ${(r.test.failed || []).join('; ')}`)
        continue
      }
      if (!r.doc || r.doc.status !== 'documented') {
        failed.push({ step_id: step.step_id, stage: 'doc', reason: r.doc ? `doc keeper ended at status "${r.doc.status}"` : 'the doc keeper returned nothing — the step is built and tested but not documented' })
        excluded.add(step.step_id)
        log(`  ${step.step_id}: FAILED at doc — built and tested, not documented`)
        continue
      }
      built.push({ step_id: step.step_id, agent: step.agent, artefacts: r.run.artefacts || [], tests_run: r.test.tests_run, results_path: r.test.results_path })
      progressed += 1
      log(`  ${step.step_id}: documented (${(r.run.artefacts || []).length} artefact(s), ${r.test.tests_run != null ? r.test.tests_run : '?'} test(s) passed)`)
    }
  }

  log(`round ${round} complete: ${progressed} step(s) documented this round — ${built.length} documented, ${failed.length} failed, ${blocked.length} blocked so far`)
  if (!progressed) {
    stoppedBecause = `round ${round} documented nothing — stopping rather than looping on the same steps`
    log(stoppedBecause)
    break
  }
}
if (round >= MAX_ROUNDS) log(stoppedBecause)

// ---------------------------------------------------------------------------
// Phase 3 — Verify the milestone. Runs even when steps failed: the acceptance
// report is what the human reads to decide G3, and "not ready, here is why" is
// a legitimate report.
// ---------------------------------------------------------------------------
phase('Verify')
const mv = await agent(
  `${HOUSE}
TASK: verify milestone ${MILESTONE} across its steps and produce the acceptance report.
Inputs: {"build_dir": "${BUILD_DIR}", "milestone_id": "${MILESTONE}"}

What this build round did:
- documented: ${JSON.stringify(built.map((s) => s.step_id))}
- failed: ${JSON.stringify(failed)}
- blocked: ${JSON.stringify(blocked)}
- rounds run: ${round} of ${MAX_ROUNDS}; stopped because: ${JSON.stringify(stoppedBecause)}

DO:
1. Re-derive the truth from ${PLAN} and from disk — do not take the list above on trust; it is what the orchestrator observed, not what is on disk.
2. Run the CROSS-STEP checks the per-step tester could not: artefacts consistent across steps (field referenced by an automation step actually exists in the object-model step's XML; a queue referenced by routing exists; permissions cover every object and field the milestone created); one coherent package.xml; the deploy order implied by depends_on is sound; nothing references an artefact no step produced.
3. Run the milestone's own \`acceptance_tests[]\`. List every \`manual\` test in \`manual_checklist\` — those are for the human at G3, and they are not evidence of passing.
4. Write the report to ${BUILD_DIR}/reports/MILESTONE-${MILESTONE}-REPORT.md directly, alongside the merged milestone package.xml. \`build_plan.py\` renders no milestone report, and per agents/milestone-verifier/AGENT.md this agent does not touch plan.json at all — its verdict lives in the report and the envelope. Include: what was built, what each test returned, the failed/blocked steps with their reasons, any \`skill-gap\` recorded in decisions.md, the deploy order, and the validate-only command a human MAY run — never run it yourself.
5. \`passed\` is true ONLY when every step in the milestone is at status \`documented\` AND every cross-step check and milestone test passed. Any failed or blocked step means passed=false. Do not round up.
6. Read \`python3 scripts/build_plan.py gate --help\` and return in \`gate_command\` the exact command a human runs to record the G3 acceptance gate for milestone ${MILESTONE} on ${BUILD_DIR}. You do NOT run it — agents never approve a gate.

IDEMPOTENT: re-running replaces this milestone's report; it does not append a second one.

Return {milestone, report_path, passed, manual_checklist, gate_command, findings, deploy_order}.`,
  { label: `verify-milestone:${MILESTONE}`, phase: 'Verify', schema: MILESTONE_OUT, agentType: 'milestone-verifier', model: 'opus', effort: 'high' }
)
if (!mv) log('WARNING: the milestone verifier returned nothing — no acceptance report was produced. The built artefacts are on disk; re-run /run-build (resume replays the completed steps from cache).')

log(`milestone ${MILESTONE}: ${built.length} documented, ${failed.length} failed, ${blocked.length} blocked — ${mv ? (mv.passed ? 'ACCEPTANCE CHECKS PASSED' : 'NOT READY (see the report)') : 'UNVERIFIED'}`)
if (mv && mv.gate_command) log(`G3 is a HUMAN gate. When you accept this milestone, run: ${mv.gate_command}`)

return {
  milestone: MILESTONE,
  built,
  failed,
  blocked,
  report_path: mv ? mv.report_path : null,
  gate_command: mv ? mv.gate_command : null,
  passed: mv ? mv.passed : false,
  manual_checklist: mv ? mv.manual_checklist || [] : [],
  findings: mv ? mv.findings || [] : [],
  deploy_order: mv ? mv.deploy_order || [] : [],
  rounds: round,
  stopped_because: stoppedBecause,
}
