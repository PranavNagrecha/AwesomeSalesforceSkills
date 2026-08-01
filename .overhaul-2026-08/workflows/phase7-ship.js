export const meta = {
  name: 'sfskills-phase7-ship',
  description: 'Final wave: reconcile generated artifacts, validate the repo, prove a fresh install produces expert Salesforce output, then publish and prepare launch',
  phases: [
    { title: 'Reconcile' },
    { title: 'Validate' },
    { title: 'Prove it works' },
    { title: 'Publish' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
EVIDENCE: ${SCRATCH}/EVIDENCE.md, ${SCRATCH}/diagnosis.json (18 adversarially-confirmed gaps).
Today is 2026-07-31. 'timeout' does NOT exist on this macOS shell.

THE OWNER'S GOAL, IN THEIR WORDS: "any new person who wants to work with Salesforce goes in and
installs it and then it just creates things like no Claude could. It is an entire builder with
brains that no one had." That sentence is the acceptance bar for this entire wave. The library
has real depth (1,027 source-grounded skill packages, 48+ run-time agents); what it has lacked
is marketing, installs and tests. This wave closes that.
`

// ---------------------------------------------------------------------------
// PHASE 1 — RECONCILE. One agent. Regenerates every derived artifact.
// ---------------------------------------------------------------------------
phase('Reconcile')
log('Reconciling generated artifacts after ~5 parallel build waves...')

const RECONCILE_SCHEMA = {
  type: 'object',
  properties: {
    commands_run: { type: 'array', items: { type: 'string' } },
    counts: {
      type: 'object',
      properties: {
        skills: { type: 'string' }, runtime_agents: { type: 'string' },
        build_agents: { type: 'string' }, deprecated_agents: { type: 'string' },
        mcp_tools: { type: 'string' }, commands: { type: 'string' },
      },
    },
    files_updated: { type: 'array', items: { type: 'string' } },
    conflicts_found: { type: 'array', description: 'contradictions left behind by concurrent waves', items: { type: 'string' } },
    unresolved: { type: 'array', items: { type: 'string' } },
  },
  required: ['commands_run', 'counts', 'files_updated', 'conflicts_found', 'unresolved'],
}

const reconcile = await agent(`${COMMON}

YOU ARE THE RECONCILER. Roughly five build waves ran concurrently against this repo. Each was
forbidden from running the shared generators so they would not corrupt each other. That is
YOUR job now, and only yours.

DO THIS IN ORDER:
1. Survey what changed: git status --short | wc -l, and git status --short. Get oriented.
2. New agents were added this session (an OmniStudio designer, and possibly several vertical
   designers). Several waves were told to expect a doc-count mismatch and to hand the
   reconciliation to you. Find the REAL counts:
     ls -d agents/*/ | wc -l
     grep -l "class: runtime" agents/*/AGENT.md | wc -l   (check the real frontmatter key first)
     ls commands/*.md | wc -l
     find skills -name SKILL.md | wc -l
   Then read scripts/check_doc_counts.py to learn exactly which files carry which counts, and
   update EVERY doc that carries a now-stale count — including README.md, CLAUDE.md,
   agents/_shared/RUNTIME_VS_BUILD.md and agents/_shared/SKILL_MAP.md as needed.
   Run python3 scripts/check_doc_counts.py until it passes. Paste the final output.
3. Regenerate the derived artifacts, in this order, and report timings:
     python3 scripts/skill_sync.py --all
     python3 scripts/generate_validation_index.py   (if it exists — check scripts/)
     python3 scripts/generate_queue_dashboard.py    (check --help first)
   NOTE: another wave may have changed how the queue dashboard stamps its date. Run it TWICE
   and diff the output — if two consecutive runs differ, that fix did not land and you must
   report it as a conflict, not paper over it.
4. Rebuild the retrieval index so search reflects all the new/edited skills:
     python3 scripts/build_index.py
   This is slow (~15 min). Run it and report the real duration.
5. Look for CONTRADICTIONS between waves: two docs disagreeing on a number, a skill citing an
   agent that was renamed, a gate turned on by one wave that another wave's output now fails.
   Report every one you find in conflicts_found. Do NOT silently fix a contradiction by
   weakening a gate.

You own every generated artifact and every count-bearing doc. Do not edit skill or agent
CONTENT — if content is wrong, report it.`, {
  label: 'reconcile',
  phase: 'Reconcile',
  schema: RECONCILE_SCHEMA,
  effort: 'high',
})

log(`Reconcile done. Counts: ${JSON.stringify(reconcile?.counts || {})}. Conflicts: ${(reconcile?.conflicts_found || []).length}`)

// ---------------------------------------------------------------------------
// PHASE 2 — VALIDATE. Parallel: full repo gates + a genuine fresh-clone test.
// ---------------------------------------------------------------------------
phase('Validate')

const VALIDATE_SCHEMA = {
  type: 'object',
  properties: {
    green: { type: 'boolean' },
    errors: { type: 'array', items: { type: 'string' } },
    warnings_count: { type: 'string' },
    gate_results: { type: 'array', items: { type: 'string' } },
    regressions_vs_session_start: { type: 'array', description: 'anything that worked at session start and does not now', items: { type: 'string' } },
  },
  required: ['green', 'errors', 'warnings_count', 'gate_results', 'regressions_vs_session_start'],
}

const FRESHCLONE_SCHEMA = {
  type: 'object',
  properties: {
    install_works: { type: 'boolean' },
    steps: { type: 'array', description: 'each documented step, the command, and what really happened', items: { type: 'string' } },
    time_to_first_useful_output: { type: 'string' },
    blockers: { type: 'array', items: { type: 'string' } },
    doc_inaccuracies: { type: 'array', description: 'places the docs do not match what actually happens', items: { type: 'string' } },
  },
  required: ['install_works', 'steps', 'time_to_first_useful_output', 'blockers', 'doc_inaccuracies'],
}

const [validation, freshclone] = await parallel([
  () => agent(`${COMMON}

YOU ARE THE VALIDATION AGENT. Run every gate this repo has and report the truth. You FIX
NOTHING and you MODIFY NOTHING — if a gate fails, that is the finding.

RUN AND PASTE REAL OUTPUT FOR EACH:
  python3 scripts/validate_repo.py --all          (slow, ~12 min on 1027 skills — let it finish)
  python3 scripts/check_doc_counts.py
  python3 evals/scripts/run_evals.py --structure
  python3 evals/measurement/run_heldout.py        (added this session; may take a few minutes)
  cd mcp/sfskills-mcp && python3 -m unittest discover -s tests 2>&1 | tail -30
  python3 -m unittest discover -s tests 2>&1 | tail -30   (repo-level suite, if it exists)
  python3 scripts/export_skills.py --check

Report the exact error count and every ERROR line. Set green=true ONLY if
validate_repo.py --all exits 0.

REGRESSION CHECK — important: this session made large concurrent changes. Confirm the core
promise still works:
  python3 scripts/search_knowledge.py "trigger recursion"
  python3 scripts/search_knowledge.py "why is my LWC slow"
  python3 scripts/search_knowledge.py "create a validation rule"
The last two were BROKEN at session start (false "Coverage: NONE" and a misroute to
data/data-migration-planning respectively) and should now work. Confirm, and report the
held-out benchmark's Hit@1 / Hit@3 / NONE-rate numbers.`,
    { label: 'validate:gates', phase: 'Validate', schema: VALIDATE_SCHEMA, effort: 'high' }),

  () => agent(`${COMMON}

YOU ARE THE FRESH-CLONE AGENT. At session start, five simulated user personas were driven
against a fresh clone and ZERO could get started. Your job is to find out whether that is
still true, by being that user.

DO IT FOR REAL:
1. git clone the local repo into ${SCRATCH}/freshclone2 (clone from the local path — the
   working-tree changes are not pushed, so clone the working directory itself, e.g.
   git clone "${REPO}" ${SCRATCH}/freshclone2 — note this takes the committed state; if the
   session's work is uncommitted, instead copy the working tree excluding .git, and SAY which
   method you used because it changes what you are testing).
2. Now follow ONLY the documented instructions, exactly as written, as a stranger would.
   Start at README.md. Do not use any knowledge from this prompt to shortcut a broken step.
3. Record every step: the command, the real output, how long it took.
4. The bar: can you get to a genuinely useful answer to a real Salesforce question? Run the
   documented search demo. Does it return coverage, or "Coverage: NONE"?
5. Try the MCP install path too if it is documented: create a throwaway venv under ${SCRATCH}
   and 'pip install sfskills-mcp'. At session start this crashed on import because
   'mcp>=1.4.0' was unpinned and resolved to mcp 2.0.0. Report whether it still does.
6. Note EVERY place the docs say something that does not match what actually happens.

Be a hostile, impatient user. Do not fix anything. Report exactly what a stranger would hit.`,
    { label: 'validate:freshclone', phase: 'Validate', schema: FRESHCLONE_SCHEMA, effort: 'high' }),
])

log(`Validation green=${validation?.green}. Fresh clone install_works=${freshclone?.install_works}.`)

// ---------------------------------------------------------------------------
// PHASE 3 — PROVE IT WORKS. The owner's actual acceptance bar.
// ---------------------------------------------------------------------------
phase('Prove it works')

const PROOF_SCHEMA = {
  type: 'object',
  properties: {
    task: { type: 'string' },
    with_library_output_summary: { type: 'string' },
    baseline_output_summary: { type: 'string', description: 'what a competent LLM would produce WITHOUT this library' },
    concrete_advantages: { type: 'array', description: 'specific things the library produced that the baseline did not — names, limits, failure modes', items: { type: 'string' } },
    where_it_added_nothing: { type: 'array', description: 'be honest — where did the library not help', items: { type: 'string' } },
    verdict: { type: 'string', enum: ['CLEARLY_BETTER', 'MARGINALLY_BETTER', 'NO_DIFFERENCE', 'WORSE'] },
    quotable_evidence: { type: 'string', description: 'a short, concrete before/after suitable for the README' },
  },
  required: ['task', 'with_library_output_summary', 'baseline_output_summary', 'concrete_advantages', 'where_it_added_nothing', 'verdict', 'quotable_evidence'],
}

const PROOF_TASKS = [
  {
    key: 'admin-lead-routing',
    task: 'A non-technical Salesforce admin says: "Leads are piling up unassigned and reps complain they get bad ones. Set up lead routing for us." Produce the complete deliverable you would hand them.',
  },
  {
    key: 'dev-trigger',
    task: 'A developer says: "Here is a 400-line AccountTrigger with logic inline, three SOQL queries in a for-loop, and no test class. Refactor it properly." Invent a representative legacy trigger, then produce the refactored result plus its test class.',
  },
  {
    key: 'architect-decision',
    task: 'An architect says: "We need to sync 2M orders/day from SAP into Salesforce and reflect status changes back in near-real-time. What integration pattern, and why?" Produce the recommendation with its trade-offs.',
  },
]

const proofs = await parallel(PROOF_TASKS.map((t) => () => agent(`${COMMON}

YOU ARE THE PROOF AGENT for task "${t.key}". You are answering the owner's real question:
does this library actually make an AI produce Salesforce work that a plain LLM could not?

THE TASK:
${t.task}

METHOD — do both halves honestly:
A) BASELINE FIRST, and do it before you look at any skill. From your own general knowledge
   alone, write the answer a competent LLM would give without this library. Make it a GOOD
   answer — steel-man it. A rigged baseline makes the whole exercise worthless.
B) THEN use the library properly, the way a user would:
     python3 scripts/search_knowledge.py "<natural language version of the task>"
   Read the SKILL.md files it returns, plus their references/gotchas.md and
   references/llm-anti-patterns.md. Check standards/decision-trees/ if the task involves a
   technology choice. Check templates/ for canonical building blocks. If a relevant run-time
   agent exists under agents/, read its AGENT.md and follow it.
   Then produce the answer.
C) COMPARE. What did the library give you that you did not have? Be specific and concrete:
   named objects and fields, exact governor limits, named permission-set licenses, silent
   failure modes, the anti-pattern it stopped you generating. Vague claims of "more thorough"
   are worthless — cite the actual fact and the skill it came from.
D) BE HONEST about where it added nothing, was stale, or sent you the wrong way. That finding
   is as valuable as a success, and the owner explicitly wants to know.

Set verdict honestly. Produce 'quotable_evidence' as a short, real before/after the owner
could put in the README — it must be literally true and attributable to a named skill file.`,
  { label: `proof:${t.key}`, phase: 'Prove it works', schema: PROOF_SCHEMA, effort: 'high' })))

const goodProofs = proofs.filter(Boolean)
const clearlyBetter = goodProofs.filter((p) => p.verdict === 'CLEARLY_BETTER').length
log(`Proof: ${clearlyBetter}/${goodProofs.length} tasks CLEARLY_BETTER with the library.`)

// ---------------------------------------------------------------------------
// PHASE 4 — PUBLISH. Gated on the repo actually working.
// ---------------------------------------------------------------------------
phase('Publish')

const readyToPublish = Boolean(validation?.green) && Boolean(freshclone?.install_works)

const PUBLISH_SCHEMA = {
  type: 'object',
  properties: {
    actions_taken: { type: 'array', description: 'things actually executed against GitHub/PyPI, with the command and result', items: { type: 'string' } },
    actions_prepared_not_executed: { type: 'array', description: 'ready-to-run commands or drafts the owner must run', items: { type: 'string' } },
    blocked: { type: 'array', items: { type: 'string' } },
    urls: { type: 'array', items: { type: 'string' } },
  },
  required: ['actions_taken', 'actions_prepared_not_executed', 'blocked', 'urls'],
}

if (!readyToPublish) {
  log(`PUBLISH GATE CLOSED — validation green=${validation?.green}, fresh clone works=${freshclone?.install_works}. Preparing launch assets but NOT publishing.`)
}

const publishResults = await parallel([
  () => agent(`${COMMON}

YOU ARE THE RELEASE AGENT.

PUBLISH GATE: ${readyToPublish ? 'OPEN — validation is green and a fresh clone works.' : 'CLOSED'}
Validation green: ${validation?.green}. Fresh clone works: ${freshclone?.install_works}.
Fresh-clone blockers: ${JSON.stringify((freshclone?.blockers || []).slice(0, 6))}
Validation errors: ${JSON.stringify((validation?.errors || []).slice(0, 6))}

The owner has explicitly authorised publishing ("I am happy for you to do the entire thing").
So you MAY execute GitHub actions via the gh CLI. But you must NOT publish a broken front door
— a launch is one-shot and drives strangers to whatever exists at that moment.

IF THE GATE IS OPEN, do these for real:
1. Fix the stale repo metadata. The description currently claims "982+ skills"; use the REAL
   count from python3 scripts/check_doc_counts.py.
     gh repo edit PranavNagrecha/AwesomeSalesforceSkills --description "<accurate, capability-led>"
   Lead with what it does for a person, not the count.
2. Write docs/release-plans/v1.0.0.md release notes (open with the concrete before/after, not
   a changelog), then cut the release:
     git tag -a v1.0.0 -m "..." && git push origin v1.0.0
     gh release create v1.0.0 --title "..." --notes-file docs/release-plans/v1.0.0.md
   IMPORTANT: only tag if the working tree is committed. If there are uncommitted changes,
   DO NOT commit them yourself — report that the owner/orchestrator must commit first.
3. The MCP data bundle: .github/workflows/publish-mcp.yml builds sfskills-data.tar.gz on tag.
   'sfskills-mcp-init' currently 404s because zero releases exist. Determine the exact tag
   that fires it and whether cutting it fixes the 404. Execute if safe; otherwise report.
4. Check whether an mcp version bump is needed for the dependency pin fix, and tag it.

IF THE GATE IS CLOSED: do NOT tag, do NOT create a release, do NOT edit the repo description
to advertise something broken. Instead prepare everything as exact copy-paste commands in
actions_prepared_not_executed, and clearly state what must be fixed first.

Never force-push, never rewrite history, never delete a branch or release.`,
    { label: 'publish:release', phase: 'Publish', schema: PUBLISH_SCHEMA, effort: 'high' }),

  () => agent(`${COMMON}

YOU ARE THE DISTRIBUTION AGENT. Get the project listed where people actually look. Research
each surface's CURRENT submission process with WebSearch/WebFetch — do not guess.

Verified context: the project is absent from essentially every discovery surface except Glama,
while ~20 rival Salesforce MCP servers are listed in the official MCP registry. Two channels
already work but are undocumented: 'npx skills add PranavNagrecha/AwesomeSalesforceSkills',
and a Claude Code plugin (.claude-plugin/marketplace.json + tiered router skills + agents)
that was built this session.

FOR EACH SURFACE: find the real submission requirements and produce a ready-to-submit artifact.
Where submission is a PR to a public repo, PREPARE the exact file content and the fork/PR
commands, but DO NOT open PRs against third-party repositories without the owner present —
those carry his name and reputation. Executing changes on the owner's OWN repo is authorised;
submitting to someone else's is not.
  1. The official MCP registry (modelcontextprotocol) — server.json / publishing requirements.
  2. Glama, Smithery, PulseMCP and any other live MCP directory.
  3. Claude Code plugin marketplace discovery — how do third-party marketplaces get found in
     2026? Document the exact 'claude plugin marketplace add' style command a user runs.
  4. awesome-* lists: awesome-mcp-servers, awesome-claude-code, awesome-salesforce.
  5. The vercel-labs 'skills' CLI ecosystem / skillspool.org or equivalent.
PyPI already has sfskills-mcp v0.4.6 — verify it is current and installable.

Deliver, in actions_prepared_not_executed, a ranked checklist with the exact command or exact
file content per surface. Put every URL in urls.`,
    { label: 'publish:distribution', phase: 'Publish', schema: PUBLISH_SCHEMA, effort: 'high' }),

  () => agent(`${COMMON}

YOU ARE THE LAUNCH-COPY AGENT. Write the announcement copy. You have no social accounts, so
you PREPARE drafts only — put every draft in actions_prepared_not_executed.

READ FIRST: docs/positioning.md, docs/comparison.md and docs/go-to-market.md (written earlier
this session), plus the final README.md. Stay consistent with the positioning already chosen.

THE PROOF YOU MUST BUILD THE COPY AROUND — real comparisons run this session:
${JSON.stringify(goodProofs.map((p) => ({ task: p.task, verdict: p.verdict, quote: p.quotable_evidence })), null, 2)}

Use the strongest genuinely-true before/after. Never inflate a number — the real counts come
from python3 scripts/check_doc_counts.py; run it.

WRITE:
1. r/salesforce post — that audience is allergic to marketing. Lead with the concrete problem
   (an LLM confidently writes Salesforce code that violates platform rules), show the real
   example, be plain about limitations. No hype words.
2. SFXD Discord / Trailblazer Community post — shorter, practitioner-to-practitioner.
3. LinkedIn post — the origin story plus one striking concrete fact.
4. A Salesforce Ben / community-blog pitch email — one paragraph on why their readers care.
5. Hacker News 'Show HN' title + first comment (the comment carries the technical substance).
6. A 20-second demo script: the exact terminal commands to screen-record that show the
   difference most vividly.

Tone: a practitioner sharing something useful, not a product launch. Any claim in this copy
must be checkable in the repo. Flag anything you could not verify rather than smoothing over it.`,
    { label: 'publish:copy', phase: 'Publish', schema: PUBLISH_SCHEMA, effort: 'high' }),
])

return {
  reconcile,
  validation,
  fresh_clone: freshclone,
  publish_gate_open: readyToPublish,
  proofs: goodProofs,
  publish: publishResults.filter(Boolean),
}
