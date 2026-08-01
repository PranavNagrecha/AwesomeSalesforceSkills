export const meta = {
  name: 'sfskills-phase0-resume',
  description: 'Resume step 0: assess partial writes from the interrupted waves, resolve the two known anomalies, then checkpoint everything to a branch',
  phases: [
    { title: 'Assess' },
    { title: 'Remediate' },
    { title: 'Checkpoint' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
READ FIRST: ${SCRATCH}/HANDOFF.md — the full state handoff. Also ${SCRATCH}/EVIDENCE.md.
Today is 2026-08-01. 'timeout' does NOT exist on this macOS shell.

SITUATION: a large multi-wave overhaul ran on 2026-07-31 and was STOPPED MID-FLIGHT by the
owner. Waves 1 and 2 were interrupted during their QA/review/remediation stages; Waves 3 and
5a had only reached their requirements stage. Result: 51 modified + 18 untracked files, none
of which passed a full review gate, sitting uncommitted on 'main' at HEAD 14f9b2490.

Five more build waves are about to run against this tree. Before that happens the work must be
assessed and checkpointed.
`

const ASSESS_SCHEMA = {
  type: 'object',
  properties: {
    partial_or_broken_files: {
      type: 'array',
      description: 'files that look half-written, truncated, syntactically invalid, or internally inconsistent',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          problem: { type: 'string' },
          evidence: { type: 'string' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
        },
        required: ['path', 'problem', 'evidence', 'severity'],
      },
    },
    registry_anomaly: { type: 'string', description: 'why registry/** and docs/SKILLS.md are modified when agents were forbidden from running skill_sync.py — and whether they are consistent' },
    sqlite3_anomaly: { type: 'string', description: 'what wrote vector_index/lexical.sqlite3 (note the .sqlite3 suffix vs the real lexical.sqlite) and whether it matters' },
    safe_to_commit: { type: 'boolean' },
    files_to_exclude_from_commit: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['partial_or_broken_files', 'registry_anomaly', 'sqlite3_anomaly', 'safe_to_commit', 'files_to_exclude_from_commit', 'summary'],
}

phase('Assess')
log('Assessing the interrupted tree for partial writes and the two known anomalies...')

const assessment = await agent(`${COMMON}

YOU ARE THE ASSESSMENT AGENT. You READ and MODIFY NOTHING. Your job is to establish whether
the interrupted work is sound enough to checkpoint.

DO THIS:
1. Inventory: git status --short ; git diff --stat
2. For EVERY modified and untracked file, check it is complete and coherent — an interrupted
   builder can leave a truncated file. Prioritise by risk:
   - Python: byte-compile every changed .py to catch syntax errors, e.g.
       git status --short | awk '{print $2}' | grep '\\.py$' | xargs -I{} python3 -m py_compile {}
     and also check the new/untracked ones (scripts/build_plugin.py, evals/measurement/run_heldout.py).
   - JSON: parse every changed/new .json (.claude-plugin/*.json,
     evals/measurement/heldout-queries.json, registry/*.json samples).
   - Markdown: check the new docs/*.md files end mid-sentence or mid-section? Read the tail of
     each. A doc that stops mid-table is a partial write.
   - SKILL.md edits: confirm frontmatter still parses and required sections survive.
3. RESOLVE ANOMALY 1: registry/** and docs/SKILLS.md are modified, yet every build agent was
   explicitly forbidden from running scripts/skill_sync.py. Work out what actually happened
   (check git diff on registry/skills.json and the per-skill json files — do they correspond
   exactly to the skills that were edited?). State whether these generated artifacts are
   CONSISTENT with the current skills/ tree or stale/partial.
4. RESOLVE ANOMALY 2: vector_index/lexical.sqlite3 is untracked. Note the '.sqlite3' suffix —
   the real index is vector_index/lexical.sqlite. Find what writes that filename
   (grep -rn "lexical.sqlite3" scripts/ pipelines/ evals/ mcp/ .github/) and say whether it is
   a stray artifact, a bug in new code, or intentional. Check .gitignore covers it.
5. Run the fast gates to see where the tree stands (do NOT run the full 12-minute validate):
     python3 scripts/validate_repo.py --agents
     python3 scripts/check_doc_counts.py
     python3 scripts/search_knowledge.py "why is my LWC slow"
   The last one was BROKEN at session start (false "Coverage: NONE"); it should now return
   lwc/lwc-performance. Confirm the retrieval fix survived the interruption.
6. Recommend which files, if any, should be EXCLUDED from the checkpoint commit (e.g. stray
   build artifacts, anything half-written).

Set safe_to_commit=false only if something is genuinely broken. A file that is merely
unreviewed is still safe to checkpoint on a branch — that is the point of a checkpoint.`, {
  label: 'assess:tree',
  phase: 'Assess',
  schema: ASSESS_SCHEMA,
  effort: 'high',
})

log(`Assessment: safe_to_commit=${assessment?.safe_to_commit}, ${(assessment?.partial_or_broken_files || []).length} problem files`)

phase('Remediate')

const REMEDIATE_SCHEMA = {
  type: 'object',
  properties: {
    fixed: { type: 'array', items: { type: 'string' } },
    left_alone: { type: 'array', items: { type: 'string' } },
    still_broken: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['fixed', 'left_alone', 'still_broken', 'notes'],
}

const blockers = (assessment?.partial_or_broken_files || []).filter((f) => f.severity !== 'minor')

const remediation = blockers.length || (assessment?.sqlite3_anomaly || '').length
  ? await agent(`${COMMON}

YOU ARE THE REMEDIATION AGENT. Fix ONLY what the assessment found. Do not improve, refactor,
or continue any wave's unfinished work — the waves will be re-run properly.

ASSESSMENT FINDINGS:
${JSON.stringify(assessment, null, 2)}

DO THIS:
1. Repair genuinely broken/truncated files (syntax errors, unparseable JSON, docs that stop
   mid-sentence). For a truncated file, the safest repair is usually to REVERT it
   (git checkout -- <path> for a modified file, or delete an incomplete untracked file) rather
   than to guess what the interrupted agent intended — the wave will regenerate it properly.
   Prefer reverting over inventing. State which you chose per file.
2. Deal with vector_index/lexical.sqlite3 per the assessment: if it is a stray artifact,
   delete it and ensure .gitignore covers it. If it is a BUG in new code writing the wrong
   filename, fix the filename in the offending script and say where.
3. Do NOT touch registry/** — if the assessment says it is stale/inconsistent, leave it and
   report; the reconciler regenerates it centrally later.
Report honestly what remains broken.`, {
      label: 'remediate:partials',
      phase: 'Remediate',
      schema: REMEDIATE_SCHEMA,
    })
  : (log('Nothing to remediate.'), null)

phase('Checkpoint')

const COMMIT_SCHEMA = {
  type: 'object',
  properties: {
    branch: { type: 'string' },
    committed: { type: 'boolean' },
    commit_sha: { type: 'string' },
    files_committed: { type: 'string' },
    excluded: { type: 'array', items: { type: 'string' } },
    verification: { type: 'string', description: 'git log -1 --stat output proving it landed' },
    notes: { type: 'string' },
  },
  required: ['branch', 'committed', 'commit_sha', 'files_committed', 'excluded', 'verification', 'notes'],
}

const checkpoint = await agent(`${COMMON}

YOU ARE THE CHECKPOINT AGENT. Protect the work. This is a safety commit, not a release.

ASSESSMENT:
${JSON.stringify(assessment, null, 2)}
REMEDIATION:
${JSON.stringify(remediation, null, 2)}

DO THIS:
1. The repo is on 'main'. Do NOT commit to main. Create and switch to a branch:
     git checkout -b overhaul/2026-08-01-checkpoint
2. Stage the work, EXCLUDING anything the assessment flagged in files_to_exclude_from_commit
   and any stray build artifact. Be deliberate: 'git add -A' then unstage the exclusions, or
   add paths explicitly. Verify with 'git status --short' before committing.
3. Commit with an honest message that says plainly this is an unreviewed checkpoint of
   interrupted work. Summarise what landed: the retrieval coverage-gate + name-match ranking
   fix (held-out "Coverage: NONE" 23.3%->6.7%, Hit@1 50%->65%, no fixture regression), the
   tiered Claude Code plugin packaging (.claude-plugin/ + 12 router skills + 48 agents), the
   OmniStudio run-time agent, the new docs suite, the held-out retrieval benchmark, and repo
   hygiene fixes. State that QA and review did NOT complete.
   End the commit message with exactly:
Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
4. DO NOT PUSH. Local commit only — the owner has not asked for a push, and the pre-push hook
   is ~12 minutes per shard.
5. Verify it landed: git log -1 --stat | head -40 and paste it into 'verification'.
   Confirm the working tree is clean afterwards (or explain exactly what remains and why).

If the assessment said safe_to_commit=false, still create the branch and commit whatever IS
safe, exclude the rest, and say clearly what you held back.`, {
  label: 'checkpoint:commit',
  phase: 'Checkpoint',
  schema: COMMIT_SCHEMA,
  effort: 'high',
})

log(`Checkpoint: branch=${checkpoint?.branch} committed=${checkpoint?.committed} sha=${checkpoint?.commit_sha}`)

return { assessment, remediation, checkpoint }
