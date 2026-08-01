export const meta = {
  name: 'sfskills-phase10-remediate',
  description: 'Apply the blocking review findings: close the cap-gate evasion, correct three now-false docstrings, add breadth notes, and commit the SKILL_MAP consistency checker',
  phases: [
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

MACHINE CONSTRAINT: 16 GB Mac, already OOM-killed once. ONE heavy process at a time.
validate_repo.py peaks ~3 GB. Prefer --agents and --skills-only --shard N/8 over full runs.

CONTEXT — these are REVIEW-BLOCKING findings from an adversarial review that did its job well.
The previous wave inverted the agent-citation gate (bare orphan-ness ERROR -> WARN; echo-stub
descriptions -> ERROR), which correctly removed the incentive that produced 555 machine-
generated citations. But the review proved one NEW gate reproduces the very defect being fixed,
and that three docstrings became false the moment the change landed.

Do not re-litigate the design. Apply the fixes.

HOUSE RULES:
- Do NOT hand-edit generated artifacts: registry/, vector_index/, docs/SKILLS.md,
  standards/validation-gates.md, docs/queue-progress.md.
- Do NOT run scripts/skill_sync.py or scripts/build_index.py.
- FILE OWNERSHIP IS STRICT — one other item runs alongside you.
`

const ITEMS = [
  {
    id: 'gate-evasion-fix',
    title: 'Close the cap-gate evasion and correct the docstrings that the gate change falsified',
    owns: [
      'scripts/validate_repo.py',
      'scripts/patch_agent_skill.py',
      'CLAUDE.md',
      'agents/_shared/AGENT_CONTRACT.md',
    ],
    goal: `FIX 1 — THE CAP-GATE EVASION (the most important change in this wave).
The reading-list cap counts numbered 'skills/...' reads ONLY while inside a '## Mandatory
Reads*' section. The reviewer PROVED the evasion: a fixture agent with 45 described reads fires
the WARN; moving 6 of those lines verbatim under a new '## Situational Reads (read when
relevant)' heading — same file, same 45 reads, same 45 files the agent will still open —
silences it entirely. pipelines/agent_validators.py only enforces presence and relative order
of required sections, so an extra heading is legal.

Fix: count numbered 'skills/...' reads across the WHOLE AGENT.md, not just inside the Mandatory
Reads section. The reviewer measured this as ZERO-REGRESSION: identical output today — same
four agents at 45/44/44/42, next agent 36 — because no agent currently carries a numbered skill
read outside its Mandatory Reads section. VERIFY that measurement yourself before and after.
KEEP the section scoping for the description-quality branches (echo stub, undescribed,
label-prefix) — those legitimately apply only to Mandatory Reads entries.

FIX 2 — THE CAP-GATE MESSAGE TEACHES THE EVASION.
It currently says "...split the agent, or demote the situational entries to a conditional 'read
when' section." Delete that clause. A gate must never name a move that silences it without
changing the artifact — that is precisely the failure this whole effort exists to undo (the old
orphan message named patch_agent_skill.py, and 555 echo stubs followed). Replace with remedies
that genuinely shorten the list: drop entries the agent does not actually need, or split the
agent into two real agents.

FIX 3 — A ONE-WORD COMMENT REGRESSION.
scripts/validate_repo.py line ~395: the inline comment reads
  '# Step 7 — orphan-skill check: ERROR if a skill is not cited by any agent.'
The diff flipped it the wrong way; it now contradicts the docstring three lines below and the
actual WARN behaviour. Revert that one word to WARN.

FIX 4 — THREE NOW-FALSE DOCSTRINGS. The change made these statements false; they assert the
opposite of current behaviour, which is worse than silence:
 (a) scripts/patch_agent_skill.py module docstring (~lines 19-25) states the predicate is NOT
     imported by validate_repo.py and that a hand-edited echo stub still passes validation.
     Both are now false — validate_repo.py imports is_echo_description() (~line 64) and raises
     it as a per-line ERROR. Rewrite to state current fact.
 (b) agents/_shared/AGENT_CONTRACT.md 'Mandatory Reads rule 2' carries the same false caveat.
     Correct it.
 (c) AGENT_CONTRACT.md:192 documents a reading-list bound (8-25 target, WARN >25, ERROR >45)
     that NO code has ever enforced. Either align the doc to what the code now does (advisory
     WARN at 40) or say plainly that the tighter numbers are a convention, not a gate. Do not
     leave a documented bound that nothing checks.

FIX 5 — CLAUDE.md OVERCLAIMS THE ECHO GATE.
CLAUDE.md line ~37 now tells authors that validate_repo.py ERRORs on citation QUALITY. The
predicate is exact-match after normalisation: "B2b commerce store setup" is caught, but
"B2b commerce store setup guidance" is not — one appended word defeats it. SOFTEN THE CLAIM to
what is actually enforced (an exact-slug-echo regression guard), rather than strengthening the
predicate. The reviewer's reasoning is sound and you should follow it: hardening an echo
detector into a filler detector is a losing arms race, and the incentive to mass-cite is
already gone now that coverage is advisory.

FIX 6 — LATENT HAZARD, document it. _check_agent_citation_quality runs unconditionally in
main(), so its per-line ERROR branch can red a build for an AGENT.md the contributor never
touched, including under the pre-commit --changed-only hook. Zero hits today makes it harmless,
but that is the shape that gets gates disabled. Add a sentence to the docstring noting it.

Prove FIX 1 with a fixture BOTH ways (build the '## Situational Reads' evasion in a scratchpad
fixture and show the gate now still fires), and confirm the real-corpus output is unchanged.`,
  },
  {
    id: 'agent-breadth-and-map',
    title: 'Add human breadth notes to the over-target agents and commit the SKILL_MAP consistency checker',
    owns: [
      'agents/apex-builder/AGENT.md',
      'agents/flow-builder/AGENT.md',
      'agents/object-designer/AGENT.md',
      'agents/security-scanner/AGENT.md',
      'agents/test-class-generator/AGENT.md',
      'scripts/check_skill_map.py (new)',
    ],
    goal: `PART 1 — BREADTH NOTES. Five agents were reworked this wave and now sit above the
AGENT_CONTRACT 8-25 read target with no explanation: apex-builder (30), flow-builder (45),
object-designer (29), security-scanner (30), test-class-generator (27).

Add ONE human-written line under '## Mandatory Reads Before Starting' in each, explaining why
that agent legitimately needs a broader list than the target. This must be a real justification
specific to the agent — e.g. an agent that generates code across many Salesforce surfaces
genuinely needs wider grounding than one that audits a single artifact. A generic sentence
pasted five times is exactly the filler this effort is removing; write five different, true
sentences or do not write them at all.

flow-builder (45 reads) needs more than a note: it is over the new advisory ceiling of 40 and
carries a live WARN. Either the note defends 45 explicitly with a real argument, OR you record
in your handoff that flow-builder is deferred to a scope decision with the WARN knowingly
accepted. It cannot be left silently over the line with a hand-wave.

Read each agent's actual job before writing its note. Do not touch any other part of these files.

PART 2 — SKILL_MAP CONSISTENCY CHECKER (scripts/check_skill_map.py, new, stdlib-only).
agents/_shared/SKILL_MAP.md drifted badly from reality this wave — several agents shrank by
100+ reads and their map entries still enumerate the padded set. A checker prevents recurrence.

Implement BOTH directions as WARN-level:
  - FORWARD: the map says agent X cites skill Y, but Y is absent from X's
    frontmatter dependencies.skills.
  - REVERSE: the map says a skill is '(no runtime agent — uncited)' but some agent now
    declares it.
Give it --json and a non-zero exit under --strict, matching the conventions of the other
scripts/check_*.py tools (read one first). Run it and REPORT the real current drift count —
do not attempt to fix the drift itself in this item; the number is the deliverable.

NOTE: a known residual exists — 25+ stale block-form claims across at least three different
bullet grammars in SKILL_MAP.md, all pre-existing. Your checker should surface them; fixing
them is separate work.

Do NOT touch scripts/validate_repo.py, scripts/patch_agent_skill.py, CLAUDE.md or
agents/_shared/AGENT_CONTRACT.md — the concurrent item owns those.`,
  },
]

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } }, required: ['path', 'action', 'summary'] } },
    fixes_applied: { type: 'array', description: 'one entry per numbered fix, with proof', items: { type: 'string' } },
    measurements: { type: 'array', items: { type: 'string' } },
    handoff_to_orchestrator: { type: 'array', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'files_changed', 'fixes_applied', 'measurements', 'handoff_to_orchestrator', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    evasion_closed_proof: { type: 'string', description: 'for the gate item: proof the Situational-Reads evasion no longer works' },
    criteria_results: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT_TESTABLE'] }, command_run: { type: 'string' }, actual_output: { type: 'string' } }, required: ['criterion', 'result', 'command_run', 'actual_output'] } },
    defects: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } }, required: ['severity', 'file', 'description'] } },
    zero_regression_confirmed: { type: 'string' },
  },
  required: ['item_id', 'verdict', 'criteria_results', 'defects', 'zero_regression_confirmed'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    new_evasions_found: { type: 'array', description: 'cheapest ways a contributor could still silence each gate without improving anything', items: { type: 'string' } },
    docstring_accuracy: { type: 'string', description: 'does every doc statement now match actual code behaviour' },
    filler_check: { type: 'string', description: 'are the breadth notes real justifications or five copies of one sentence' },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verdict', 'new_evasions_found', 'docstring_accuracy', 'filler_check', 'required_changes'],
}

phase('Build')
log('Applying blocking review findings: cap-gate evasion, false docstrings, breadth notes, SKILL_MAP checker.')

const results = await pipeline(
  ITEMS,
  (item) => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}". The fixes below were specified by an adversarial reviewer
that proved each one with a fixture or a measurement. Apply them; do not redesign.

ITEM: ${item.title}
FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

Record one entry in fixes_applied per numbered fix, each with the command/proof. If you believe
a specified fix is wrong, do NOT silently skip it — apply what is right, and explain in
not_done why you deviated.`,
    { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA, effort: 'high' })
    .then((build) => ({ item, build })),

  (ctx) => agent(`${COMMON}

YOU ARE THE QA AGENT for "${ctx.item.id}". TEST; MODIFY NOTHING.

BUILDER CLAIMS: ${JSON.stringify(ctx.build, null, 2)}

DO THIS (one heavy process at a time):
1. FOR THE GATE ITEM — THE CENTRAL TEST: rebuild the evasion yourself. Create a fixture agent
   in a scratchpad temp dir with 45 numbered skill reads so the cap WARN fires. Then move 6 of
   those lines verbatim under a new '## Situational Reads (read when relevant)' heading and
   re-run the gate. It MUST still fire. If it goes quiet, the fix failed — blocker.
   Then confirm ZERO REGRESSION on the real corpus: the same four agents at 45/44/44/42 and the
   next agent silent.
2. Verify every docstring claim against the code it describes. For each of the three corrected
   docstrings, grep the code and confirm the statement is now TRUE. A docstring asserting the
   opposite of behaviour is worse than none.
3. FOR THE BREADTH-NOTE ITEM: read all five notes. Are they five DIFFERENT, agent-specific,
   true justifications, or one sentence pasted five times? Quote them all. Boilerplate here is
   a defect — it is the same filler pattern this whole effort removes.
4. Run scripts/check_skill_map.py if it exists; confirm it runs, has --json, and reports a real
   number. Verify a couple of its claims by hand against the actual files.
5. Regression: python3 scripts/validate_repo.py --agents and
   python3 scripts/validate_repo.py --skills-only --shard 0/8. Paste results.
   Pre-existing stale-artifact and doc-count ERRORs are EXPECTED (owned elsewhere, orchestrator
   regenerates centrally) — not blockers. NEW errors are.
6. git status --short to confirm scope.`,
    { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
    .then((qa) => ({ ...ctx, qa })),

  (ctx) => agent(`${COMMON}

YOU ARE THE REVIEWER for "${ctx.item.id}". Modify nothing.

BUILD: ${JSON.stringify(ctx.build, null, 2)}
QA: ${JSON.stringify(ctx.qa, null, 2)}

1. Read the real diff: cd "${REPO}" && git diff -- <owned paths>.
2. HUNT FOR THE NEXT EVASION. The previous reviewer found that the cap gate could be silenced
   by renaming a heading. For EVERY gate touched here, ask: what is the cheapest edit a
   contributor could make to silence it without improving the artifact at all? Enumerate them
   in new_evasions_found even if you consider them acceptable — the value is in naming them.
3. DOCSTRING ACCURACY: verify each corrected statement against actual code. Do not trust the
   builder; a previous agent documented an import as done when it was not.
4. FILLER CHECK: judge the five breadth notes as a reader would. Five variations on "this agent
   needs broad grounding" is filler and should be REQUEST_CHANGES.
5. Confirm nothing regressed: the orphan gate is still WARN, the echo gate still ERROR, and no
   generated artifact was hand-edited.`,
    { label: `review:${ctx.item.id}`, phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })
    .then((review) => ({ ...ctx, review })),
)

const done = results.filter(Boolean)
log(`Remediation complete: ${done.length}/${ITEMS.length}`)

return done.map((r) => ({
  item_id: r.item?.id,
  qa_verdict: r.qa?.verdict,
  review_verdict: r.review?.verdict,
  evasion_closed: r.qa?.evasion_closed_proof,
  zero_regression: r.qa?.zero_regression_confirmed,
  new_evasions_found: r.review?.new_evasions_found,
  docstring_accuracy: r.review?.docstring_accuracy,
  filler_check: r.review?.filler_check,
  files_changed: (r.build?.files_changed || []).map((f) => `${f.action} ${f.path}`),
  fixes_applied: r.build?.fixes_applied,
  handoff: r.build?.handoff_to_orchestrator,
  not_done: r.build?.not_done,
  qa_defects: r.qa?.defects,
  required_changes: r.review?.required_changes,
}))
