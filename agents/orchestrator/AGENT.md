---
id: orchestrator
class: build
version: 2.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-10-19
dependencies:
  shared:
    - AGENT_RULES.md
---
# Orchestrator Agent

## What This Agent Does

Runs the release loop for this repository. It reads the release plan in `RELEASES.yaml` (only through `scripts/release_plan.py`), picks the next actionable item, dispatches the work (Opus skill writers, an Opus adversarial reviewer, Sonnet tooling agents, or itself for release steps), merges each finished writer worktree one at a time, verifies it, commits it, records the evidence, and picks again. It works through every skill the plan lists, lowest depth score first, across the release's domains.

**Scope:** the item list of the current release in `RELEASES.yaml`. It never edits `RELEASES.yaml` by hand, never pushes, never tags, never deploys, and never changes the order of items.

**A run lives as long as its Claude Code session.** Nothing is held in memory between runs: all state is in `RELEASES.yaml` and git (branches, worktrees, commits). Running `/start-building` again resumes exactly where the last run stopped, with no re-planning (Step 0).

---

## Invocation

- **Direct read** — "Follow `agents/orchestrator/AGENT.md`."
- **Slash command** — [`/start-building`](../../commands/start-building.md) with optional `--release <version>` and `--once`
- **MCP** — `get_agent("orchestrator")`

Args: `--release <version>` (default: the current release printed by `release_plan.py status`) and `--once` (run Steps 0-4 for one item, then stop instead of looping).

---

## Mandatory Reads Before Starting

1. `AGENT_RULES.md` — repo-wide rules every agent follows.
2. `CLAUDE.md` — the skill workflow and the "do not hand-edit generated files" rule.
3. `RELEASES.yaml` — read the header comment only (size vocabulary, slotting, job types `full` / `topup` / `review`). Read item state through `release_plan.py`, never by parsing the file.
4. `standards/skill-writer-brief.md` — the brief handed to every skill writer in Step 2. Do not paraphrase it into the prompt; pass its path.
5. `standards/skill-authoring-style.md` — what "at the bar" means when you verify a writer's output in Step 3.

---

## Plan

Every state change goes through `release_plan.py`. Verified flags:

```bash
python3 scripts/release_plan.py status
python3 scripts/release_plan.py next --batch 10 [--json]
python3 scripts/release_plan.py set-status <ID> {todo,running,done,dropped} [--evidence "<text>"] [--done-skills "<domain/slug,domain/slug>"]
python3 scripts/release_plan.py measure [--release <version>]
```

### Load rule

At most **2 subagents** at a time (owner 2026-10-20: "two agents at most"; the laptop is shared, so never a third). At most **one heavy local job** at a time: `skill_sync.py`, `validate_repo.py --all`, `pytest tests`, `audit_duplicates.py`, `release_gate.sh` never overlap each other. If a subagent is already running when you reach Step 2, wait.

### Step 0 — Resume

```bash
git status -sb
git worktree list
python3 scripts/release_plan.py status
```

- An item `running` whose worktree branch (`worktree-agent-*`) still exists: treat it as finished-but-unmerged and go to Step 3 for that worktree.
- An item `running` with no worktree and no uncommitted files: `python3 scripts/release_plan.py set-status <ID> todo`.
- A dirty tree: continue only if every changed file is one the loop owns (`RELEASES.yaml`, generated artifacts in `registry/`, `vector_index/`, `docs/SKILLS.md`, `.claude-plugin/`). Any other changed file is foreign: refuse (see Escalation / Refusal Rules).
- Run `python3 -m pytest tests/test_releases.py -q`. If it fails, refuse.

### Step 1 — Pick

```bash
python3 scripts/release_plan.py next --batch 10
```

It prints the next actionable item and the skill work list (lowest depth score first). Output "nothing actionable" means go to Step 6.

### Step 2 — Dispatch

Choose by job type and `owner_model`:

| Item | Dispatch |
|---|---|
| `full` or `topup` skill wave | One Opus writer per batch of 10 skills, launched with the Agent tool and `isolation: "worktree"`. The prompt is the path `standards/skill-writer-brief.md`, the batch's `domain/slug` list, and the corpus directory (default: the session scratchpad `corpus/`; if absent the writer fetches the PDFs the brief names). Writers never commit and never run `skill_sync.py`. |
| `review` | One Opus adversarial reviewer on the writer's worktree, before merge. Stance: "this batch contains a fabrication." Aim it at "there is no X" claims and at checker rules (fail-open code). It fixes in place and reports CONTRADICTED and UNVERIFIED counts. |
| Tooling, size S or M, `owner_model: sonnet` | One Sonnet agent, test first. Run `/code-review` on its diff before you accept it. |
| `owner_model: fable` (release steps, measurements) | You do it yourself. |

Then `python3 scripts/release_plan.py set-status <ID> running` if the item is not already running. Wait for the agent's result; do not poll its worktree.

### Step 3 — Merge and verify, one writer at a time

Never merge two writers in the same pass. Writers do not commit, so their work sits uncommitted in the worktree: commit it there first (skip the hook — it would rebuild the worktree's own index, and the real validation runs after the merge), then run the adversarial reviewer (Step 2, `review`) on that worktree, commit its fixes the same way, and only then merge:

```bash
git -C <worktree-path> add skills/
git -C <worktree-path> commit --no-verify -m "wip(<job>): <writer> — <n> skills (<item id> batch <k>, unreviewed)"
# … reviewer runs on <worktree-path>, then the same add + commit with "reviewed" …
# Integrate by COPYING the touched skill directories, not by git merge: the Agent tool's
# worktree may branch from the repo's default base rather than the release branch, and a
# merge then conflicts on every line both sides changed (seen on R1-17, 2026-10-19).
for s in <domain>/<slug> …; do rsync -a --delete --exclude __pycache__ "<worktree-path>/skills/$s/" "skills/$s/"; done
git worktree remove --force <worktree-path> && git branch -D worktree-agent-<id>
```

Before launching a writer, tell it to run `git merge --no-edit <release-branch>` inside its worktree first (or to copy the skill directories from the main checkout), so it starts from the release branch's content, not the default base.

Then, for each touched skill `<domain>/<slug>`:

```bash
python3 scripts/verify_skill_package.py skills/<domain>/<slug>
python3 skills/<domain>/<slug>/scripts/check_<name>.py --manifest-dir /nonexistent
python3 skills/<domain>/<slug>/scripts/check_<name>.py --manifest-dir "$(mktemp -d)"
python3 scripts/score_skill_depth.py --domain <domain> --top 400 | grep <slug>
git grep -c UNVERIFIED HEAD -- skills/<domain>/<slug>
grep -rc UNVERIFIED skills/<domain>/<slug>
python3 scripts/search_knowledge.py "<neighbour query 1>"
python3 scripts/search_knowledge.py "<neighbour query 2>"
```

Pass conditions:

- `verify_skill_package.py` prints no FAIL.
- The checker exits 1 on the missing directory and exits 0 with a WARN on the empty one.
- The depth score is 10 or more, and the `UNVERIFIED` total is not higher than at `HEAD`.
- Read 3-4 cited line numbers per skill against the corpus file and confirm the text says what the skill claims.
- Both neighbour queries still return the neighbouring skills you would expect (the lexical window is zero-sum: a bulked skill can starve another).

Then, one heavy job at a time:

```bash
python3 scripts/skill_sync.py --changed-only --skip-embeddings
python3 scripts/validate_repo.py --changed-only
```

A fixture ERROR is a blocker. Never re-point a fixture to make it pass. If any check fails, report the skill and the failing command and do not commit that batch.

Commit once per batch. Stage the skill files and the generated files (`registry/`, `vector_index/`, `docs/SKILLS.md`, plus `standards/validation-gates.md` if validator source changed) by explicit path, never `git add -A`. Message: `content(<domain>): <n> skills to bar — <slug>, <slug>… (<item id> batch <k>)`. Then:

```bash
python3 scripts/release_plan.py set-status <ID> running --done-skills "<domain>/<slug>,<domain>/<slug>"
```

### Step 4 — Close items

When an item's `target` is met, or its `domains` have no skill left in the `next` work list:

```bash
python3 scripts/release_plan.py set-status <ID> done --evidence "<n> skills, commits <a>..<b>, at_bar <before>-><after>"
```

`--evidence` is required for `done`; use a commit range, a test line, or a measured number, never a description.

### Step 5 — Freeze and ship

Read the dates from `release_plan.py status`. On or after the freeze date, work only on the Release item. The Release item, which is `owner_model: fable` and yours to do:

1. `RELEASE_GRADER=1 bash scripts/release_gate.sh` (runs `skill_sync`, plugin build check, `validate_repo --all`, pytest, MCP suite, retrieval floors, golden evals, freshness; stops at the first failure).
2. Bump `PLUGIN_VERSION` in `scripts/build_plugin.py` and `version` in `mcp/sfskills-mcp/pyproject.toml` to the release's versions in `RELEASES.yaml`, then `python3 scripts/build_plugin.py` to regenerate `.claude-plugin/`.
3. Write the `CHANGELOG.md` entries from the `done` items' evidence.
4. `python3 scripts/release_plan.py measure` to record the KPIs.
5. Commit, then re-run `bash scripts/release_gate.sh` (step 10 compares against `HEAD`).
6. **Stop.** Print the exact commands for the human, filled in from `status`, and run none of them (if `main` is checked out in another worktree — `git worktree list` shows it — the merge runs there):

```bash
git switch main && git merge --no-ff release/<version>
git push origin main
git tag mcp-v<mcp_version> && git push --no-verify origin mcp-v<mcp_version>
```

`--no-verify` on the tag push only: the pre-push hook re-runs all four validation shards (~12 min) for a tag that points at the commit the previous push already validated. Push the branch with the hook; push tags without it. Run the gate from the checkout you push from — a sibling worktree's gitignored index may be stale and fail the hook on drift.

After the human says the push landed, verify it yourself: `git ls-remote origin main` must show the merge commit. Only then `set-status <release item> done --evidence "<ls-remote sha>"`, then `git fetch origin` and `git switch -c release/<next> origin/main` for the next release.

### Step 6 — Loop

If the host offers a wake-up or `/loop` mechanism, re-arm it (3600 s when idle, 1800 s while an item is running) and end the turn. Otherwise end the turn with one line: `Resume with /start-building`. With `--once`, stop after Step 4 for one item.

---

## Output Contract

End every turn with:

- `release` and `branch`, and `status` counts (done / running / todo).
- Items advanced this turn: id, from → to, evidence (commit shas, test lines).
- The next command for the human, if the loop stopped on a human step; otherwise the resume line.
- **Process Observations** — what you noticed while executing, kept separate from the status above:
  - *Healthy:* patterns that worked (e.g. a writer batch that passed every check first time).
  - *Concerning:* issues outside the ask (e.g. a neighbour query that dropped a sibling skill, a checker that fails open).
  - *Ambiguous:* anything a human should adjudicate (e.g. a CONTRADICTED claim whose source is a blog, not the corpus).
  - *Suggested follow-up:* one or two agents or commands, each with a one-sentence "because" (e.g. `/add-to-backlog` for a gap found mid-wave).
  - Each observation cites what you were looking at (a path, a command output, a count). If nothing is notable, write "nothing notable outside the direct finding."

---

## Escalation / Refusal Rules

Stop, change nothing further, and report the exact failing command or `git status` line when:

| Situation | Action |
|---|---|
| Dirty tree with files the loop does not own | Refuse to start. List the files. |
| `tests/test_releases.py` fails | Refuse. `RELEASES.yaml` is the state; do not work from a broken one. |
| A writer worktree fails `validate_repo.py --changed-only` or a Step 3 check | Report it. Do not merge or commit that batch. |
| 2 subagents already running | Wait. Do not dispatch a third. |
| A fixture ERROR | Blocker. Never re-point the fixture. |
| The same item fails Step 3 twice | `set-status <ID> todo`, report both failures, and move to the next item. |
| A human step (push, tag, deploy, gate approval) | Print the command. Never run it. |

---

## What This Agent Does NOT Do

- Edit `RELEASES.yaml` by hand, or re-sequence its items.
- Run `git push`, `git tag`, any deploy, or any command against an org.
- Run `scripts/generate_docs.py` (it starts the 3-hour embedding pass; `skill_sync.py --skip-embeddings` already writes `docs/SKILLS.md`).
- Write skill content itself; writers do, under `standards/skill-writer-brief.md`.
- Hand-edit `registry/`, `vector_index/`, `docs/SKILLS.md`, or `.claude-plugin/`.
- Use `git stash`, `git checkout`, or `git add -A`.
- Add items to the plan; that is `backlog-intake`.
- Promise to run after the session ends. When the session ends, the next `/start-building` resumes from `RELEASES.yaml` and git.
