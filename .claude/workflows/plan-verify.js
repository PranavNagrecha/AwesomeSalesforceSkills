export const meta = {
  name: 'plan-verify',
  description: 'Adversarially verify a build plan on three lenses (executability, grounding, testability) and write the verdicts into plan.json.verification',
  whenToUse: 'After /plan-build has written a plan (status "planned"). Pass args {build_dir: ".sfskills/builds/<build-id>"}. Returns the blocker list and the exact G2 gate command — it never approves the gate itself. Re-runnable: every agent is idempotent and the synthesis overwrites this plan version\'s verification block rather than appending to it.',
  phases: [
    { title: 'Load', detail: 'run build_plan.py validate and transcribe the plan\'s steps', model: 'sonnet' },
    { title: 'Verify', detail: 'three refutation lenses per step, in parallel, no barrier', model: 'opus' },
    { title: 'Synthesize', detail: 'write verdicts into plan.json.verification and set the plan status', model: 'opus' },
  ],
}

// ---------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------
const a = typeof args === 'string' ? JSON.parse(args) : (args || {})
const BUILD_DIR = a.build_dir
if (!BUILD_DIR) {
  throw new Error('args.build_dir is required — the build directory, e.g. ".sfskills/builds/<build-id>"')
}
const PLAN = `${BUILD_DIR}/plan.json`

// The plan file is the only shared state (build-orchestration.md § 2). This
// script has no filesystem access, so every fact about it arrives through an
// agent that ran scripts/build_plan.py and read plan.json itself.
const HOUSE = `Repo root is the current working directory. The build directory is ${BUILD_DIR}; the plan file is ${PLAN}.
The contract you are working under is standards/build-orchestration.md — read it if anything below is ambiguous.

HARD RULES:
- NEVER deploy. Never run \`sf project deploy start\`, \`sf project deploy validate\`, or any command that touches an org.
- \`python3 scripts/build_plan.py\` is the single writer of plan state and of every rendered view (PLAN.md, CLARIFICATIONS.md, reports). Never hand-edit a rendered view. If an invocation shape you try is rejected, run \`python3 scripts/build_plan.py --help\` and \`python3 scripts/build_plan.py <subcommand> --help\` and use the real flags — do not work around it by editing files.
- Agents never approve a human gate. \`build_plan.py gate\` is the only writer of gate records and a human is the only decider.
- No secrets in output or in the build directory; redact with [REDACTED].
`

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const LOADED = {
  type: 'object',
  required: ['status', 'validate_ok', 'steps'],
  properties: {
    status: { type: 'string', description: 'plan.json "status", verbatim' },
    version: { type: 'number', description: 'plan.json "version"' },
    build_id: { type: 'string' },
    validate_ok: { type: 'boolean', description: 'did `build_plan.py validate` exit 0' },
    validate_output: { type: 'string', description: 'trimmed stdout+stderr of the validate run' },
    milestones: {
      type: 'array',
      items: { type: 'object', properties: { id: { type: 'string' }, title: { type: 'string' } } },
    },
    steps: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'milestone', 'type', 'agent', 'skills', 'acceptance_tests', 'depends_on'],
        properties: {
          id: { type: 'string' },
          milestone: { type: 'string' },
          type: { type: 'string', description: 'a step type from build-orchestration.md § 4' },
          title: { type: 'string' },
          agent: { type: 'string', description: 'owning run-time agent id' },
          skills: { type: 'array', items: { type: 'string' } },
          templates: { type: 'array', items: { type: 'string' } },
          decision_trees: { type: 'array', items: { type: 'string' } },
          inputs: { type: 'string', description: 'the step\'s inputs{} object serialised as JSON' },
          outputs: { type: 'array', items: { type: 'string' } },
          depends_on: { type: 'array', items: { type: 'string' } },
          acceptance_tests: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                type: { type: 'string', description: 'checker | xml | manifest | command | manual' },
                detail: { type: 'string', description: 'the test as the plan words it, verbatim' },
                command: { type: 'string', description: 'the runner command, if the plan states one' },
              },
            },
          },
          status: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT = {
  type: 'object',
  required: ['step_id', 'lens', 'verdict', 'blockers', 'warnings', 'evidence'],
  properties: {
    step_id: { type: 'string' },
    lens: { type: 'string', enum: ['executability', 'grounding', 'testability'] },
    verdict: { type: 'string', enum: ['pass', 'refuted'] },
    blockers: {
      type: 'array',
      items: {
        type: 'object',
        required: ['problem'],
        properties: {
          problem: { type: 'string', description: 'what is wrong, specifically enough to fix' },
          evidence: { type: 'string', description: 'the path you listed or the command output that proves it' },
          fix: { type: 'string', description: 'the smallest plan edit that would clear it' },
        },
      },
    },
    warnings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['problem'],
        properties: { problem: { type: 'string' }, fix: { type: 'string' } },
      },
    },
    evidence: {
      type: 'array',
      items: { type: 'string' },
      description: 'verbatim proof: paths you listed or read, commands you ran and what they printed. A verdict with no evidence is not a verdict.',
    },
  },
}

const SYNTH = {
  type: 'object',
  required: ['status', 'blockers', 'warnings', 'gate_command'],
  properties: {
    status: { type: 'string', enum: ['verified', 'plan-rejected'] },
    blockers: {
      type: 'array',
      items: {
        type: 'object',
        required: ['step_id', 'problem'],
        properties: {
          step_id: { type: 'string' },
          lenses: { type: 'array', items: { type: 'string' } },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
    warnings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['step_id', 'problem'],
        properties: { step_id: { type: 'string' }, lenses: { type: 'array', items: { type: 'string' } }, problem: { type: 'string' } },
      },
    },
    gate_command: { type: 'string', description: 'the real command a human runs to record G2, with the build dir substituted' },
    validate_ok: { type: 'boolean', description: 'did build_plan.py validate exit 0 AFTER your edit' },
    rendered: { type: 'boolean', description: 'did build_plan.py render succeed' },
    notes: { type: 'string' },
  },
}

// ---------------------------------------------------------------------------
// The three lenses (build-orchestration.md § 1.3 and § 6)
// ---------------------------------------------------------------------------
const LENSES = [
  {
    id: 'executability',
    checks: `Can the NAMED AGENT actually execute this step, in this order, with what it is given?
- The step's \`agent\` exists at agents/<id>/AGENT.md, is \`class: runtime\`, and its status is not deprecated. agents/_shared/SKILL_MAP.md and agents/_shared/RUNTIME_VS_BUILD.md are the roster.
- That agent's AGENT.md actually covers this step's job. An agent that designs Permission Sets cannot build a Flow. A plausible-sounding but wrong owner is a blocker, not a nit.
- The step's \`type\` is one of the rows in standards/build-orchestration.md § 4, and the named agent is a listed or credible owner for that row.
- \`inputs\` are sufficient: everything the agent needs is either stated in the step, answered in the plan's clarifications, or produced by a step this one depends_on. Any input the agent would have to invent is a blocker.
- \`outputs\` are concrete paths under artefacts/<step-id>/, not prose describing an artefact.
- Org posture: the named agent's frontmatter is not \`requires_org: true\`. The loop is org-free, so a step owned by an org-requiring agent cannot run unattended — blocker.
- \`depends_on\` ids all exist, contain no cycle, and order the work correctly: nothing consumes an artefact produced by a later step, and nothing depends on a step in a milestone that is not already accepted.
- No other step in the same milestone writes any path this step writes. Two steps sharing an output path force a serialisation the plan does not declare — blocker.
- The step is one unit of work for one agent. A step that quietly bundles three builds cannot be run, tested or rolled back as one.`,
  },
  {
    id: 'grounding',
    checks: `Does every citation resolve, and does the cited thing actually say what the step needs?
- Every id in \`skills[]\` resolves to a real skills/<domain>/<slug>/SKILL.md on disk. An unresolvable citation is a blocker (AGENT_RULES: never invent a skill path).
- Open each cited SKILL.md. Does it actually cover this step's job? A skill cited because its slug sounds right, but which is silent on what the step must decide, is padding — blocker.
- Every path in \`templates[]\` exists (under templates/ or the citing skill's own templates/), and the step uses it rather than freestyling an idiom templates/ already owns.
- Every entry in \`decision_trees[]\` names a real tree under standards/decision-trees/ AND a real branch inside it. A technology choice recorded without a resolvable branch is a blocker.
- Every question in a cited skill's \`## Questions to Ask Before Configuring\` table that this step's approach depends on has an answer in the plan's clarifications. A decision the skill said to ask about, made silently in the plan, is a blocker.
- The fit tier the plan recorded for this capability survives re-tiering against the five-tier rubric in skills/admin/fit-gap-analysis-against-org. A Custom-tier capability scheduled as a config step is a refutation, not a quibble.
- The step does not rest on Salesforce knowledge that no cited skill states. If it does, that is the skill-gap signal (§ 8): raise it as a blocker naming the missing fact. Never as a suggestion to freestyle.
- Nothing in the step implies deploying to an org, and no acceptance test smuggles a deploy in.
- No claim in the step's title/inputs contradicts what the cited skill says (wrong metadata type name, wrong API version behaviour, invented permission).`,
  },
  {
    id: 'testability',
    checks: `Is every acceptance test runnable today, and would it actually fail on a bad build?
- The step declares at least one acceptance test (§ 5 requires ≥ 1).
- Each declared test is runnable NOW:
  * \`checker\` — the script exists at the stated skills/<domain>/<slug>/scripts/check_*.py path and accepts the flags the test uses (\`python3 <path> --help\`). A checker that does not exist means the step would be BLOCKED at test time, never silently passed — blocker.
  * \`xml\` — the step actually produces *.xml / *-meta.xml for the parse to bite on.
  * \`manifest\` — a package.xml is produced by this step or by a step it depends on.
  * \`command\` — stdlib-only and org-free. Anything needing an org, the network, a non-stdlib dependency, or any \`sf project deploy\` invocation is a blocker.
  * \`manual\` — phrased as something a human can tick at the milestone gate, with one unambiguous pass condition.
- The tests test THIS step's outputs. A test that would pass against an empty artefacts/<step-id>/ directory tests nothing — blocker.
- The pass condition is stated and objective (exit 0, parses, member present in package.xml). "Looks correct" is a blocker.
- The milestone this step belongs to has at least one acceptance test of its own; say so if it does not.
- If the step changes who can see or do something (permission sets, PSGs, profiles, sharing rules, org-wide defaults, queue or group membership, guest access) or deletes anything, \`human_gate\` is true. Access and deletion are the two classes where being wrong is not recoverable by re-running the step — blocker.`,
  },
]

// ---------------------------------------------------------------------------
// Phase 1 — Load. Nothing is verified until the plan itself validates.
// ---------------------------------------------------------------------------
phase('Load')
const plan = await agent(
  `${HOUSE}
TASK: load the build plan and report it faithfully. Read-only apart from running the validator.

1. Run \`python3 scripts/build_plan.py validate ${PLAN}\` (the plan path is the positional argument; discover the real shape from --help if that one is rejected — do not skip the validator). Record whether it exited 0 in validate_ok and its trimmed stdout+stderr in validate_output.
2. Read ${PLAN} and transcribe it into the schema. Copy VERBATIM — do not editorialize, reorder, summarise, merge or drop steps. Where a field is absent return an empty array or string; never invent one.
3. Transcribe each acceptance test as {type, detail, command}: \`detail\` is the test exactly as the plan words it, \`command\` only if the plan states one.
4. Serialise each step's \`inputs{}\` object into the \`inputs\` string as JSON.
5. Return EVERY step in the plan, from every milestone. There is no cap and no sampling — a step you omit is a step nobody verifies.`,
  { label: 'load-plan', phase: 'Load', schema: LOADED, model: 'sonnet', effort: 'low' }
)
if (!plan) throw new Error(`could not load ${PLAN} — is ${BUILD_DIR} a build directory produced by /plan-build?`)

// Refuse anything that is not a plan waiting to be verified. build-orchestration
// § 3: Verify runs on a `planned` plan; re-verifying an already `verified` plan
// is allowed (it is how you re-check after an edit), nothing else is.
const VERIFIABLE = ['planned', 'verified']
if (!VERIFIABLE.includes(plan.status)) {
  throw new Error(
    `plan status is "${plan.status}" — /verify-plan runs on a plan at status "planned" (or re-runs on "verified"). ` +
    (plan.status === 'clarifying'
      ? 'Answer the blocking clarifications and record G1, then run /plan-build.'
      : plan.status === 'plan-rejected'
        ? 'This plan was rejected: re-plan as a new version (plan.version + 1) with /plan-build before verifying again.'
        : 'Run /plan-build first.')
  )
}

const steps = plan.steps || []
if (!steps.length) throw new Error(`${PLAN} declares no steps — nothing to verify. Re-run /plan-build.`)
if (!plan.validate_ok) {
  log(`WARNING: \`build_plan.py validate\` did NOT exit 0. Verifying anyway; the synthesis treats this as a blocker. Output: ${String(plan.validate_output || '').slice(0, 400)}`)
}
const milestoneCount = new Set(steps.map((s) => s.milestone)).size
log(`${PLAN}: status ${plan.status}${plan.version ? `, version ${plan.version}` : ''} — ${steps.length} step(s) across ${milestoneCount} milestone(s); ${steps.length * LENSES.length} lens verdicts to gather`)

// ---------------------------------------------------------------------------
// Phase 2 — Verify. Pipeline over steps; the three lenses of one step run
// together (they are the cross-item context each other needs). No barrier
// between steps — step 7's lenses do not wait on step 2's.
// ---------------------------------------------------------------------------
phase('Verify')

// Dependency context every lens needs, without shipping each lens the whole plan.
const SKELETON = JSON.stringify(
  steps.map((s) => ({ id: s.id, milestone: s.milestone, agent: s.agent, type: s.type, depends_on: s.depends_on || [], outputs: s.outputs || [], status: s.status }))
)

function lensPrompt(lens, step) {
  return `${HOUSE}
You are the ${lens.id.toUpperCase()} lens of the plan verifier for build ${BUILD_DIR}. You are ADVERSARIAL: your job is to REFUTE this step, not to bless it. A plan that ships with a defect you waved through costs a whole build round.

STEP UNDER TEST (verbatim from ${PLAN}):
${JSON.stringify(step, null, 1)}

ALL STEPS IN THE PLAN (ids, owners, dependencies and outputs only — for ordering and output-collision checks):
${SKELETON}

WHAT THIS LENS CHECKS:
${lens.checks}

METHOD:
- Verify on disk, never from memory. \`ls\`, \`cat\`, \`grep\`, \`--help\` every path and command you assert about, and quote what you actually saw into evidence[]. A claim with no evidence line is a claim you have not made.
- DEFAULT TO REFUTED WHEN UNSURE. "Probably fine", "presumably exists", "the agent will figure it out" are all refuted. Return verdict "pass" only when every check above is confirmed by something you read or ran.
- A blocker means the step would produce wrong, unrunnable or ungrounded output — it stops the plan. A warning is worth fixing but would not break the build. Choose deliberately; inflating warnings into blockers wastes a re-plan, and demoting a real blocker ships a broken step.
- READ-ONLY. Do not edit ${PLAN}, do not create artefacts, do not run the step, do not deploy.
- Report only what this lens covers. The other two lenses are running concurrently; duplicating their findings makes the blocker list harder to act on.

Return the structured verdict for step_id "${step.id}", lens "${lens.id}".`
}

let lensesIn = 0
let refutedLenses = 0
const TOTAL_LENSES = steps.length * LENSES.length

const perStep = await pipeline(steps, async (prev, step) => {
  const raw = await parallel(
    LENSES.map((lens) => () =>
      agent(lensPrompt(lens, step), {
        label: `${lens.id}:${step.id}`,
        phase: 'Verify',
        schema: VERDICT,
        agentType: 'plan-verifier',
        model: 'opus',
        effort: 'high',
      })
    )
  )
  const verdicts = LENSES.map((lens, i) => {
    const v = raw[i]
    if (!v) {
      // A dead lens is an UNVERIFIED lens. Defaulting it to pass is exactly the
      // silent hole this workflow exists to close.
      return {
        step_id: step.id,
        lens: lens.id,
        verdict: 'refuted',
        blockers: [{ problem: `the ${lens.id} lens returned nothing (agent died or was skipped) — the step is unverified on this lens, so it is refuted by default`, fix: `re-run /verify-plan; resume reuses the lens verdicts that did return` }],
        warnings: [],
        evidence: [],
      }
    }
    return { ...v, step_id: step.id, lens: lens.id }
  })
  lensesIn += LENSES.length
  const refuted = verdicts.filter((v) => v.verdict === 'refuted')
  refutedLenses += refuted.length
  log(`${step.id} [${step.type} -> ${step.agent}]: ${LENSES.length - refuted.length}/${LENSES.length} lenses pass${refuted.length ? ` (refuted: ${refuted.map((v) => v.lens).join(', ')})` : ''} — ${lensesIn}/${TOTAL_LENSES} verdicts in`)
  return verdicts
})

const verdicts = perStep.filter(Boolean).flat()
const unverified = steps.filter((s) => !verdicts.some((v) => v.step_id === s.id)).map((s) => s.id)
for (const id of unverified) log(`step ${id}: NO verdicts returned at all — the synthesis records it as an unverified blocker`)
log(`${verdicts.length}/${TOTAL_LENSES} lens verdicts collected; ${refutedLenses} refuted; ${verdicts.filter((v) => (v.blockers || []).length).length} verdict(s) carry blockers`)

// ---------------------------------------------------------------------------
// Phase 3 — Synthesize. The only barrier, and the only writer.
// ---------------------------------------------------------------------------
phase('Synthesize')
const synth = await agent(
  `${HOUSE}
TASK: record this verification in ${PLAN} and set the plan's status. You are the ONLY writer in this workflow — the lens agents were read-only.

LENS VERDICTS (${verdicts.length} of an expected ${TOTAL_LENSES}; every step should carry exactly ${LENSES.length}):
${JSON.stringify(verdicts)}

STEPS THAT RETURNED NO VERDICT AT ALL (record each as an unverified blocker): ${JSON.stringify(unverified)}
\`build_plan.py validate\` at load time: exit ${plan.validate_ok ? '0' : 'NON-ZERO'} — ${JSON.stringify(String(plan.validate_output || '').slice(0, 800))}
${plan.validate_ok ? '' : 'A plan that does not validate CANNOT be verified: record that as a blocker and set status plan-rejected regardless of the lens verdicts.\n'}
DO, IN ORDER:
1. Make ONE SMALL, surgical JSON edit to ${PLAN}: set the top-level \`status\` — \`verified\` when there are ZERO blockers anywhere, otherwise \`plan-rejected\`; warnings alone never block — and set the top-level \`verification\` object to
   {"status", "verified_at", "by", "plan_version": <plan.version>,
    "lenses": [{"lens":"executability","verdict":"pass"|"fail","notes":"…"}, ...one per lens],
    "steps": [{"step_id", "verdict", "lenses": [{"lens","verdict","blockers","warnings","evidence"}]}],
    "blockers": [{"step","lens","problem","fix"}], "warnings": [...]}
   A step's verdict is "refuted" if ANY of its lenses refuted it, otherwise "pass".
   agents/_shared/schemas/build-plan.schema.json governs this block: top-level \`lenses[]\` entries are OBJECTS requiring {lens, verdict} with verdict "pass" or "fail" — a roll-up across steps, where "fail" means at least one step was refuted on that lens. An array of plain strings fails validation. Each \`blockers[]\` entry requires \`step\` and \`problem\`. The per-step verdict objects keep their own pass/refuted vocabulary and nest under steps[].lenses[], which the schema leaves open.
   Change NOTHING else: do not reword, reorder, renumber or delete an existing field, and never touch \`history[]\` or \`human_gates[]\`.
   The build status is set by this edit because no subcommand sets it: \`set-status\` moves one STEP along the section 4 state machine, and \`gate\` writes only what a human decided.
2. Run \`python3 scripts/build_plan.py validate ${PLAN}\`. It must exit 0. If your edit broke the schema, fix YOUR EDIT — never make the validator pass by deleting plan content.
3. Run \`python3 scripts/build_plan.py render ${PLAN}\` so PLAN.md reflects the verification.
4. Read \`python3 scripts/build_plan.py gate --help\` and return in \`gate_command\` the exact command a human would run to record the G2 plan-approval gate on ${BUILD_DIR} — a real, runnable command with the paths substituted, not a placeholder. You do NOT run it. Agents never approve a gate.

RULES:
- Do not re-adjudicate a lens. You aggregate; you do not overturn a refutation because it looks harsh, and you do not add a blocker no lens raised.
- Deduplicate identical blockers across lenses: keep one, keep its wording, and list which lenses raised it in \`lenses\`.
- Order blockers by step, in plan order, so the fix list reads top-to-bottom.
- IDEMPOTENT: if \`verification\` already exists for this plan version, REPLACE it with this run's result. Never append a second copy.

Return {status, blockers, warnings, gate_command, validate_ok, rendered, notes}.`,
  { label: 'synthesize', phase: 'Synthesize', schema: SYNTH, model: 'opus', effort: 'high' }
)
if (!synth) {
  throw new Error(`synthesis agent failed — ${PLAN} was NOT updated and the plan status is unchanged. Re-run /verify-plan; resume replays the lens verdicts from cache.`)
}

const nBlockers = (synth.blockers || []).length
const nWarnings = (synth.warnings || []).length
log(`plan ${synth.status} — ${nBlockers} blocker(s), ${nWarnings} warning(s) across ${steps.length} step(s)`)
if (synth.validate_ok === false) log('WARNING: build_plan.py validate did not exit 0 after the verification edit — plan.json may be inconsistent; inspect it before building.')
if (synth.status === 'verified') {
  log(`G2 is a HUMAN gate. When you approve the plan, run: ${synth.gate_command}`)
} else {
  log(`Plan rejected. Fix the blockers, re-plan as a new version with /plan-build, then re-run /verify-plan. G2 stays unapproved; /run-build will refuse to start.`)
}

return synth
