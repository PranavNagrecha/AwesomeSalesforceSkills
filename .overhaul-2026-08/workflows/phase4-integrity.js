export const meta = {
  name: 'sfskills-phase4-integrity',
  description: 'Wave 3: make a fresh clone actually work, un-rig the validator, de-pad the agent citations, and remove the retrieval-poisoning stub skills',
  phases: [
    { title: 'Requirements' },
    { title: 'Build' },
    { title: 'QA' },
    { title: 'Review' },
    { title: 'Remediate' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
EVIDENCE BRIEF: ${SCRATCH}/EVIDENCE.md — READ IT FIRST, especially sections 4b, 4c and 4d.
Its numbers were measured by the orchestrator and are established fact.

HOUSE RULES (CLAUDE.md / AGENT_RULES.md — violations fail review):
- Never hand-edit generated artifacts: registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md.
- Do NOT run scripts/skill_sync.py or scripts/build_index.py — the orchestrator runs those
  centrally. Concurrent runs corrupt shared artifacts.
- Never make a factual Salesforce claim without official-source grounding.
- Never claim a topic is uncovered without pasting real search_knowledge.py output.
- 'timeout' does NOT exist on this macOS shell.
- Today is 2026-07-31.

FILE OWNERSHIP IS STRICT — other agents work this repo concurrently. Touch only your item's
paths. Anything else gets reverted and fails review.

DO NOT BREAK WHAT WORKS. This repo's content layer is genuinely strong (1,027 uniform skill
packages, 100% structural completeness, a well-reasoned .gitignore). You are fixing the
machinery around it. Prefer the smallest change that removes the defect.
`

const ITEMS = [
  {
    id: 'fresh-clone-works',
    title: 'Make a fresh clone actually usable — currently 0 of 5 user personas can start',
    owns: [
      'scripts/bootstrap.py (new)',
      'Makefile (new, optional)',
      'mcp/sfskills-mcp/pyproject.toml',
      'mcp/sfskills-mcp/docs/CONNECT.md',
      'docs/installing.md (new)',
      '.gitignore',
    ],
    goal: `THIS IS THE HIGHEST-IMPACT ITEM IN THE ENTIRE PROJECT. A lens cloned the repo as a new
user would and drove five personas through it: ZERO could get started. Every downstream
improvement is worthless until this is fixed.

The four independent breakages (all verified — re-verify each yourself before fixing):

(a) NO SLASH COMMANDS ON CLONE. .gitignore line 63 excludes '.claude/*' (only
    '.claude/workflows/' is exempted), so exactly ONE file is tracked under .claude/.
    A fresh clone has zero slash commands, while README claims '.claude/commands/ ships
    in-tree'. The fixer, scripts/install_local_commands.py, is documented only in its own
    docstring. DECIDE: either track .claude/commands/ (63 files, small — check the real
    size) so the claim becomes true, or keep it ignored and make bootstrap generate it.
    Either is defensible; pick one, implement it, and make the docs match reality.
    NOTE: README.md is owned by another agent. Do NOT edit README.md — instead report the
    exact false sentence and the corrected wording for central application.

(b) SEARCH RETURNS NOTHING ON CLONE. vector_index/lexical.sqlite is gitignored (>50 MB,
    correctly so) and no setup step rebuilds it, so the README's own demo command
    'python3 scripts/search_knowledge.py "trigger recursion"' returns "Coverage: NONE".
    Worse, the rebuild ran >14m36s with zero progress output, so a user cannot tell it from
    a hang. Deliver scripts/bootstrap.py as the ONE command a new user runs: it should build
    the index (with real progress reporting), install the commands, verify the result with a
    known-good query, and print clear next steps. Time it and report the real duration.
    If the 14-minute build can be made materially faster or resumable, do that; if not,
    at minimum report progress so it is obviously working.

(c) pip install sfskills-mcp IS BROKEN. mcp/sfskills-mcp/pyproject.toml:34 declares
    'mcp>=1.4.0' with no upper bound; it resolves to mcp 2.0.0 which crashes on import.
    Verify the actual failure (create a throwaway venv under ${SCRATCH}, not in the repo),
    then pin a correct, tested range. Confirm the package imports and the server starts
    after your pin. This is the repo's most-advertised install path.

(d) sfskills-mcp-init 404s because the repo has ZERO GitHub releases, though a workflow
    builds the data bundle for them. Diagnose exactly what URL it requests and what would
    have to exist. You may NOT create a public GitHub release yourself — that is an
    outward-facing publish and the owner's call. Instead: make the failure mode graceful
    and self-explanatory (clear error telling the user what to do), and write the exact
    release-cutting steps into docs/installing.md so the owner can run them.

ACCEPTANCE: a simulated fresh clone into ${SCRATCH}/freshclone must reach a working search in
one documented command. Actually perform that simulation and paste the transcript.`,
  },
  {
    id: 'validator-integrity',
    title: 'Stop the validator being red by construction, and enforce the gates that already exist',
    owns: [
      'scripts/generate_queue_dashboard.py',
      'scripts/validate_repo.py',
      '.github/workflows/validate.yml',
      '.githooks/',
      'AGENT_RULES.md',
    ],
    goal: `Two compounding problems: the gate is permanently red, and the gates that matter are
not run.

1. RED BY CONSTRUCTION. scripts/generate_queue_dashboard.py:279 stamps
   date.today().isoformat() into docs/queue-progress.md, which is then drift-checked. So
   validate_repo.py has exited 1 on a clean tree every single day since 2026-07-09. The
   README badge is permanently failing and the gate can no longer distinguish a broken PR
   from a normal one. Fix the CAUSE: stop embedding a volatile date in a drift-checked
   artifact (e.g. derive the date from the newest BACKLOG.yaml history entry, or exclude the
   date line from the drift hash). Do not just regenerate the file — that fixes it until
   midnight. Prove the fix by generating twice and diffing.

2. GATES THAT DO NOT RUN.
   - The 1,356-fixture retrieval gate runs in 0 CI jobs and 0 hooks. Another agent is
     concurrently fixing retrieval and re-enabling this in validate.yml — CHECK the current
     contents of .github/workflows/validate.yml before editing, and do not revert their work.
     Coordinate by adding only what is missing.
   - evals/scripts/run_evals.py runs nowhere. Add a CI job that at least runs
     '--structure' so the 30 golden P0 cases and 15 agent baselines stop being decorative.
   - 233 of 248 MCP tests never run in CI (15 run, across 3 of 24 modules), including the
     SOQL DML blocklist and secret-redaction tests. These are SECURITY tests for a tool that
     touches live orgs. Wire the full MCP suite into CI. If some modules genuinely cannot run
     without an org, mark and skip them explicitly rather than silently omitting them.
   - Full validate_repo.py is 708s. Keep CI sharded; do not make the contributor loop slower.

3. CONTRADICTION. AGENT_RULES.md says orphan skills are a WARN that "do not block the
   commit"; CLAUDE.md and the generated standards/validation-gates.md both say ERROR. You own
   AGENT_RULES.md — make it match the code's actual behaviour (verify which the code really
   does). Do NOT edit CLAUDE.md (not yours).

Report every gate you turned on and what it currently reports — if turning a gate on reveals
pre-existing failures, DO NOT paper over them: list them precisely for the owner.`,
  },
  {
    id: 'citation-integrity',
    title: 'Un-rig the agent citation gate and remove the >50% Mandatory Reads padding',
    owns: [
      'scripts/patch_agent_skill.py',
      'agents/*/AGENT.md (Mandatory Reads sections only)',
      'agents/_shared/AGENT_CONTRACT.md',
    ],
    goal: `Orchestrator-verified: 555 of 1,058 numbered Mandatory Reads (52.5%) are echo stubs
whose description is just the slug title-cased. object-designer 123/142, waf-assessor 80/91,
apex-builder 57/74, data-model-reviewer 57/61, agentforce-builder 44/45.

object-designer — an sObject design agent — is instructed that it MUST read
'b2b-commerce-store-setup', 'care-plan-configuration', 'donor-lifecycle-requirements' and
'email-studio-administration' before starting. That is not a reading list, it is ballast.

ROOT CAUSE: _check_orphan_skills in scripts/validate_repo.py ERRORs on any skill not cited in
some agent's dependencies.skills:, with no cap per agent, so mass-citation via
patch_agent_skill.py is the cheapest way to clear the gate. Goodhart's law inside the
validator.

ORDER MATTERS — fix the incentive before the symptom, or the next contributor re-pads it:
1. Change the gate's shape. NOTE: scripts/validate_repo.py is owned by the 'validator-integrity'
   agent working concurrently. You do NOT own it. Instead, specify precisely what the gate
   should become and hand that to the orchestrator — e.g. a cap on Mandatory Reads per agent,
   a rule that a read's description must not equal its slug, and/or demoting bare orphan-ness
   to WARN while making echo-stub citations the ERROR. Write your recommendation into your
   report; do not edit validate_repo.py.
2. What you DO own: strip the echo-stub entries from agents/*/AGENT.md Mandatory Reads.
   For each affected agent, decide which skills it GENUINELY needs — read the agent's actual
   job first — and keep those with real, human-written one-line descriptions explaining WHY
   that agent needs that skill. Target a defensible list per agent (roughly 8-25 reads),
   not a number hit for its own sake.
3. Removing citations WILL make skills orphaned and trip the current ERROR gate. That is
   expected and is the whole point — report exactly which skills become orphaned and how
   many, so the orchestrator can apply the gate change from step 1. Do not re-pad to keep
   the gate green.
4. Encode the standard in agents/_shared/AGENT_CONTRACT.md so this cannot recur: Mandatory
   Reads must be human-authored, justified, and bounded.
5. Add a guard to scripts/patch_agent_skill.py so it refuses to write a citation whose
   description merely echoes the slug.

Be conservative about REMOVING a read that an agent plausibly needs; be ruthless about ones
it obviously does not.`,
  },
  {
    id: 'stub-skill-cleanup',
    title: 'Fix the 48 stub skills that are actively poisoning retrieval',
    owns: [
      'skills/** (only the 48 stub skills you identify, and only those)',
    ],
    goal: `The corpus-quality lens found a single wave dated 2026-04-28 that shipped stubs:
48 skills whose references/llm-anti-patterns.md is under 600 bytes (as small as 178 bytes),
and examples.md files with zero code. Distribution: security 10, devops 8, integration 7,
agentforce 7, lwc 6, omnistudio 5, flow 5. All are version 1.0.0, all dated 2026-04-28.

These are not merely thin — they are ACTIVELY HARMFUL. The lens verified with
search_knowledge.py that a 220-byte stub chunk ranks #1 for a query where a deep, correct
skill already exists. A stub outranking real content is worse than no skill at all, because
the assistant confidently reads the stub and stops.

IDENTIFY them precisely (do not trust the count — measure):
  cd "${REPO}" && for f in skills/*/*/references/llm-anti-patterns.md; do s=$(wc -c < "$f"); [ "$s" -lt 600 ] && echo "$s $f"; done | sort -n

For EACH stub, decide one of three dispositions and justify it:
  (A) DEEPEN — the topic is genuinely distinct and valuable. Author real content: 5+ concrete
      LLM anti-patterns with wrong-code/right-code pairs, real examples with code, specific
      gotchas. Ground every claim in official Salesforce docs.
  (B) MERGE/REDIRECT — the topic duplicates an existing deep skill (several do; the lens found
      topic-duplicates of skills that already existed). Verify the overlap with
      search_knowledge.py and paste the output. Recommend the merge in your report — do NOT
      delete a skill directory yourself; deletion is the owner's call and affects the registry.
  (C) LEAVE — genuinely fine as a short skill. Justify why.

OWNERSHIP EXCLUSION — READ THIS BEFORE PICKING TARGETS. A separate agent is concurrently
deepening skills under skills/security/**. You do NOT own that directory. EXCLUDE every
security skill from your target list, including the ~10 security stubs, even though they are
the highest-consequence ones. They are already covered by that agent. Report them as
"handled by security-depth" and move on.

Your targets are therefore the stubs in devops, integration, agentforce, lwc, omnistudio and
flow. Prioritise agentforce and integration — both are core to the library's differentiation.
Do as many as you can do WELL; quality beats coverage. Report exactly which you completed and
which remain.

CRITICAL — RETRIEVAL IS ZERO-SUM (measured): the lexical window is 30 chunks, so deepening
one skill can push a neighbour below the coverage threshold. Add DISTINCTIVE depth (exact
error strings, real limits with numbers, named permissions, concrete failure modes), not
generic prose competing for the same tokens. After your changes, spot-check that neighbouring
untouched skills in the same domain still retrieve.

Do not change any skill's name, category or description identity — the registry and retrieval
depend on them. Do not touch the 3 near-duplicate skills owned by the repo-hygiene agent:
admin/flexcard-requirements, architect/omnistudio-vs-standard-architecture,
flow/flow-custom-property-editors.`,
  },
]

const REQ_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    understanding: { type: 'string' },
    verified_starting_state: { type: 'array', description: 'commands run to confirm the defect is real, with output', items: { type: 'string' } },
    deliverables: {
      type: 'array',
      items: {
        type: 'object',
        properties: { path: { type: 'string' }, action: { type: 'string' }, what: { type: 'string' } },
        required: ['path', 'action', 'what'],
      },
    },
    acceptance_criteria: {
      type: 'array',
      items: {
        type: 'object',
        properties: { criterion: { type: 'string' }, verify_command: { type: 'string' }, expected: { type: 'string' } },
        required: ['criterion', 'verify_command', 'expected'],
      },
    },
    handoffs: { type: 'array', description: 'things this item must NOT do itself and must hand to the orchestrator', items: { type: 'string' } },
    out_of_scope: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'understanding', 'verified_starting_state', 'deliverables', 'acceptance_criteria', 'handoffs', 'out_of_scope'],
}

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    files_changed: {
      type: 'array',
      items: {
        type: 'object',
        properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } },
        required: ['path', 'action', 'summary'],
      },
    },
    commands_run: { type: 'array', items: { type: 'string' } },
    measurements: { type: 'array', items: { type: 'string' } },
    handoff_to_orchestrator: { type: 'array', description: 'exact changes the orchestrator must apply centrally (files you do not own)', items: { type: 'string' } },
    newly_revealed_problems: { type: 'array', description: 'pre-existing failures your change exposed — do not hide these', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'commands_run', 'measurements', 'handoff_to_orchestrator', 'newly_revealed_problems', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    criteria_results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          criterion: { type: 'string' },
          result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT_TESTABLE'] },
          command_run: { type: 'string' },
          actual_output: { type: 'string' },
        },
        required: ['criterion', 'result', 'command_run', 'actual_output'],
      },
    },
    defects: {
      type: 'array',
      items: {
        type: 'object',
        properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' }, repro: { type: 'string' } },
        required: ['severity', 'file', 'description', 'repro'],
      },
    },
    regression_check: { type: 'string', description: 'what previously-working behaviour you confirmed still works' },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'defects', 'regression_check'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    factual_errors: {
      type: 'array',
      items: {
        type: 'object',
        properties: { file: { type: 'string' }, claim: { type: 'string' }, why_wrong: { type: 'string' }, correction: { type: 'string' } },
        required: ['file', 'claim', 'why_wrong', 'correction'],
      },
    },
    canon_violations: { type: 'array', items: { type: 'string' } },
    solves_stated_problem: { type: 'boolean' },
    reasoning: { type: 'string' },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'factual_errors', 'canon_violations', 'solves_stated_problem', 'reasoning', 'required_changes'],
}

phase('Requirements')
log(`Wave 3 integrity: ${ITEMS.length} items — fresh-clone, validator, citations, stub skills.`)

const results = await pipeline(
  ITEMS,

  (item) => agent(`${COMMON}

YOU ARE THE REQUIREMENTS AGENT for "${item.id}". You SPECIFY ONLY — you create and modify
nothing. Read anything; run read-only commands.

ITEM: ${item.title}

FILES THIS ITEM OWNS:
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

FIRST re-verify the defect is real and still present — paste the commands and output into
verified_starting_state. The orchestrator's evidence is good but the repo is being modified
concurrently, so confirm current state. Then write mechanically-checkable acceptance criteria
(one command + expected result each); the QA agent runs exactly these. List in 'handoffs'
anything that must be done by the orchestrator because this item does not own the file.`,
    { label: `req:${item.id}`, phase: 'Requirements', schema: REQ_SCHEMA }),

  (spec, item) => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}". Implement the spec. Separate QA and reviewer agents check
you afterwards, so report weaknesses honestly rather than concealing them.

ITEM: ${item.title}

FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

SPEC:
${JSON.stringify(spec, null, 2)}

Run every verify_command and make it pass. Every number you write must come from a command you
ran. If your change EXPOSES pre-existing failures, list them in newly_revealed_problems —
never suppress a newly-failing check to look green. Put anything requiring a file you do not
own into handoff_to_orchestrator with the exact change needed.`,
    { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA })
    .then((build) => ({ item, spec, build })),

  (ctx) => agent(`${COMMON}

YOU ARE THE QA AGENT for "${ctx.item.id}". You TEST and MODIFY NOTHING.

SPEC:
${JSON.stringify(ctx.spec, null, 2)}
BUILDER CLAIMS:
${JSON.stringify(ctx.build, null, 2)}

DO THIS:
1. Run every acceptance-criteria verify_command. Paste real output. Trust nothing.
2. REGRESSION IS THE MAIN RISK for this wave — these items change shared machinery. Confirm
   previously-working behaviour still works:
     python3 scripts/validate_repo.py --agents
     python3 scripts/validate_repo.py --changed-only
     python3 scripts/search_knowledge.py "trigger recursion"
     python3 scripts/check_doc_counts.py
   Paste results. NOTE: an agent-count mismatch from concurrent OmniStudio agent work is
   expected and is NOT a blocker; the orchestrator reconciles it centrally.
3. For citation-integrity specifically: confirm every remaining Mandatory Read still resolves
   to a real skills/<domain>/<slug>/SKILL.md — an unresolvable citation is a BLOCKER.
4. For stub-skill-cleanup: verify the touched skills still retrieve, AND spot-check 3
   untouched neighbours in the same domain still retrieve (zero-sum window).
5. Confirm the builder stayed inside owned paths: git status --short, git diff --stat.
FAIL on any blocker.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  (ctx) => agent(`${COMMON}

YOU ARE THE REVIEWER for "${ctx.item.id}". You modify nothing. QA proved it runs; you judge
whether it is RIGHT and whether it actually solves the problem.

SPEC:
${JSON.stringify(ctx.spec, null, 2)}
BUILD:
${JSON.stringify(ctx.build, null, 2)}
QA:
${JSON.stringify(ctx.qa, null, 2)}

DO THIS:
1. Read the real diff: cd "${REPO}" && git diff -- <owned paths>, plus new files.
2. Ask the hard question: does this fix the CAUSE or just the SYMPTOM? This wave is explicitly
   about root causes — a change that makes a check pass without removing the underlying defect
   is a REQUEST_CHANGES. Specifically:
   - validator-integrity: does the date fix survive a day rollover, or only until midnight?
     (Test by generating twice and comparing, and by reasoning about the drift hash.)
   - citation-integrity: were echo stubs actually removed, or just reworded to dodge a check?
   - fresh-clone-works: did the simulated clone genuinely reach a working search?
   - stub-skill-cleanup: is the new content REAL and source-grounded, or padding that merely
     clears a byte threshold? Read the actual prose. Verify Salesforce claims with WebFetch.
3. Fact-check every Salesforce and repo claim. Confident fabrication is the failure mode here.
4. Check canon compliance and that no generated artifact was hand-edited.
REQUEST_CHANGES on any factual error, canon violation, or symptom-only fix.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),

  (ctx) => {
    const blockers = (ctx.qa?.defects || []).filter((d) => d.severity !== 'minor')
    const changes = ctx.review?.required_changes || []
    const factual = ctx.review?.factual_errors || []
    if (!blockers.length && !changes.length && !factual.length) {
      log(`${ctx.item.id}: clean — QA ${ctx.qa?.verdict}, review ${ctx.review?.verdict}.`)
      return { ...ctx, remediation: null }
    }
    return agent(`${COMMON}

YOU ARE THE REMEDIATION AGENT for "${ctx.item.id}". Fix EXACTLY these findings, nothing else.

FILES YOU MAY TOUCH:
${ctx.item.owns.map((o) => '  - ' + o).join('\n')}

QA DEFECTS (blocker/major):
${JSON.stringify(blockers, null, 2)}
REVIEWER REQUIRED CHANGES:
${JSON.stringify(changes, null, 2)}
REVIEWER FACTUAL ERRORS:
${JSON.stringify(factual, null, 2)}

If a reported defect is not real, leave it and explain why in not_done. Re-run the relevant
verify commands afterwards and paste real output.`,
      { label: `fix:${ctx.item.id}`, phase: 'Remediate', schema: BUILD_SCHEMA })
      .then((remediation) => ({ ...ctx, remediation }))
  },
)

const done = results.filter(Boolean)
log(`Wave 3 complete: ${done.length}/${ITEMS.length}.`)

return done.map((r) => ({
  item_id: r.item?.id,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  solves_root_cause: r.review?.solves_stated_problem,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  measurements: r.build?.measurements,
  handoff_to_orchestrator: r.build?.handoff_to_orchestrator,
  newly_revealed_problems: r.build?.newly_revealed_problems,
  not_done: r.build?.not_done,
  qa_defects: r.qa?.defects,
  factual_errors: r.review?.factual_errors,
  remediated: r.remediation ? 'yes' : 'not needed',
  remediation_not_done: r.remediation?.not_done,
}))
