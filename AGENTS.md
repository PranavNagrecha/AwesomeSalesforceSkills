# AGENTS.md

Entry point for any coding agent working in this repository. The full
rulebook is [AGENT_RULES.md](./AGENT_RULES.md); this file is the short
orientation plus the commands you will actually run.

## Before anything else: build the local index

A `git clone` does not give you a working library. Two retrieval artifacts are
deliberately gitignored, and `.claude/commands/` is not committed either:

```bash
python3 scripts/bootstrap.py
```

Without this, `scripts/search_knowledge.py` returns zero results for every
query **and still exits 0** — which looks like an empty library rather than a
missing index. `pipelines/lexical_index.search_index` returns `[]` when
`vector_index/lexical.sqlite` is absent; nothing errors. Since step 1 of every
skill workflow is "search local coverage first", a skipped bootstrap silently
turns that gate into a rubber stamp.

`bootstrap.py --verify-only` re-runs only the checks (sub-second) and prints
whether retrieval and the slash commands are live. It writes no tracked files.
See `docs/installing.md`.

## Rules every agent follows

1. Read `AGENT_RULES.md` before creating or materially revising a skill.
2. Treat `SKILL.md` frontmatter as the canonical skill metadata source.
3. Apply `standards/skill-content-contract.md` (what to say) and
   `standards/skill-authoring-style.md` (how to say it) when authoring or
   editing SKILL.md content.
4. Use `python3 scripts/search_knowledge.py` before creating a new skill or
   claiming a coverage gap.
5. Run `python3 scripts/skill_sync.py` and `python3 scripts/validate_repo.py`
   after skill changes.
6. Never hand-edit generated files.

### What "generated" means, precisely

Do not hand-edit: everything under `registry/`, `docs/SKILLS.md`,
`docs/queue-progress.md`, `standards/validation-gates.md`,
`.claude/skills/**/references/skill-index.md`, and the retrieval artifacts
`vector_index/chunks.jsonl` / `lexical.sqlite` / `*embeddings.jsonl` (all
gitignored).

`vector_index/` is **not** wholesale generated. Three files in it are tracked
and hand-maintained:

```
$ git ls-files vector_index
vector_index/manifest.json
vector_index/query-fixtures.json
vector_index/query-variants.json
```

`query-fixtures.json` is where you add the retrieval fixture every new skill
needs (see AGENT_RULES.md step 5). `manifest.json` is written by the sync
engine — leave it alone.

## Syncing: pick the right flag

| Command | When |
|---|---|
| `python3 scripts/skill_sync.py --skill skills/<domain>/<name>` | After editing one skill. Validates that skill first, then writes artifacts. |
| `python3 scripts/skill_sync.py --all --skip-embeddings` | Repo-wide rebuild during normal work. |
| `python3 scripts/skill_sync.py --all` | Only when you intend to rebuild embeddings. |

`config/retrieval-config.yaml` has `embeddings.enabled: true`, so a bare
`--all` will attempt a chunk-level encode. The config records the measured
cost: "First-time build is ~2:20 on M-series CPU", and `.githooks/pre-commit`
notes the full encode "takes ~3 hours" when the content-hash cache is cold.
That is why the pre-commit hook passes `--skip-embeddings` and why you should
too, unless rebuilding embeddings is the point. Rebuild them deliberately with
`python3 scripts/build_index.py`.

## Working on agents (not skills)

Agents live under `agents/<slug>/AGENT.md`. There are 76 of them —
48 active run-time, 14 build-time, 14 deprecated run-time stubs — plus
`agents/_shared/`, which is shared material, not an agent. Before editing or
adding one:

1. Read `agents/_shared/AGENT_CONTRACT.md` for the frontmatter spec, required
   section order, confidence rubric, and structured citation/output formats.
2. For skill-builder agents, also read `agents/_shared/SKILL_BUILDER_CORE.md`.
3. Reuse probes from `agents/_shared/probes/` (7 files) instead of hand-rolling
   MCP queries.
4. Use refusal codes from `agents/_shared/REFUSAL_CODES.md` in output
   envelopes.

After editing any `AGENT.md`:

```bash
python3 scripts/validate_repo.py --agents
```

Measured at 0.4 s across all 76 agents. `--skills-only` (the default) is the
slow half: a full skill pass is roughly 2 minutes per quarter-shard. `--all`
runs both.

### Known gap in the agent contract — do not paper over it

`AGENT_CONTRACT.md` line 132 tells every agent to resolve skills through the
MCP `search_skill` tool ("Skill-first, never freestyle"). In practice:

- Only 3 of 76 `AGENT.md` files mention `search_skill` at all
  (`audit-router`, `automation-migration-router`, `release-planner`), and none
  of the other 45 active run-time agents issues it.
- `.claude-plugin/plugin.json` ships `skills` and `commands` only. It declares
  no `mcpServers`, and there is no `.mcp.json` in the repo, so installing the
  plugin does **not** wire the MCP server. Most users do not have
  `search_skill`.
- Both routers gate a hard refusal on it: audit-router step 1 says "at runtime
  the router still verifies via `search_skill` … If any citation is
  unresolvable, STOP with `REFUSAL_NEEDS_HUMAN_REVIEW`". A caller without the
  MCP server cannot satisfy that check.

Treat the contract line as an aspiration for MCP-connected callers, not as
something the shipped path performs. When you edit a router, prefer a refusal
condition a plugin-only caller can actually evaluate — the same citation set is
already enforced statically by `_validate_citations` in
`pipelines/agent_validators.py` at PR time.

## Install the git hooks (recommended)

One-time setup per clone:

```bash
python3 scripts/install_hooks.py
```

This sets `core.hooksPath` to `.githooks/` and installs two hooks:

- **`pre-commit`** — `skill_sync --changed-only --skip-embeddings` then
  `validate_repo --changed-only`. Fast on small commits.
- **`pre-push`** — `validate_repo --skills-only --shard N/4
  --skip-fixture-retrieval` for each of 4 shards, sequentially. Catches
  cross-cutting drift (stale registries, schema-enum drift, missing query
  fixtures) that `--changed-only` cannot see.

**The pre-push hook is slow.** Its own banner says "~10–20s"; measured on this
corpus (1,027 skills) a single shard is 1 m 58 s, so the four sequential shards
are roughly 8 minutes. Budget for that, or push with `--no-verify` on WIP
branches — CI still gates merge.

`install_hooks.py` takes no arguments and performs the install when run, so
there is no `--help` to inspect; it is idempotent.

## Reading / updating the skill queue

`BACKLOG.yaml` is the authoritative machine-readable queue (646 entries), the
row data that used to live inside `MASTER_QUEUE.md` before the 2026-05-01
migration. Do not hand-edit it — use:

```bash
python3 scripts/queue_reader.py --summary
python3 scripts/queue_reader.py --next --status TODO,RESEARCHED
python3 scripts/queue_reader.py --set-status IN_PROGRESS \
  --id <entry-id> --actor "<agent-name>@<host>"
```

Recognised statuses (`scripts/queue_reader.py` `STATUSES`): `TODO`,
`RESEARCHED`, `RESEARCH`, `IN_PROGRESS`, `DONE`, `DUPLICATE`, `BLOCKED`,
`UPDATE`, `SHIPPABLE`. `DONE` is accepted for transitional updates but the
dashboard ignores it — the filesystem under `skills/` is authoritative for
"is this skill built?".

The generated dashboard at `docs/queue-progress.md` shows status counts, drift
between queue and disk, oldest TODO, and the next 10 picks. It regenerates on
every `skill_sync.py` run.

`MASTER_QUEUE.md` is now a short prose intro plus queue-specific agent
workflow. The pre-migration table is recoverable from git
(`git show 5824c4801^:MASTER_QUEUE.md`) and reproducible via
`scripts/_migrations/migrate_queue_to_yaml.py`.

**Stale pointers to be aware of:** nine build-time agents still describe
reading or writing TODO rows in `MASTER_QUEUE.md` (`grep -l MASTER_QUEUE
agents/*/AGENT.md` → the 6 skill-builders plus `orchestrator`, `task-mapper`,
`currency-monitor`), and `commands/request-skill.md` step 5 still tells the
caller to add a table row there. Those tables no longer exist. Route queue
reads and writes through `queue_reader.py`.

## Changing skill descriptions? Check the shipped roster

Only `.claude/skills/salesforce-<domain>/references/skill-index.md` ships to a
plugin install — a GitHub-sourced install has no FTS5 index and no embeddings.
A term that appears in a skill body but not in its 220-character gloss reaches
zero users, silently.

```bash
python3 scripts/check_gloss_coverage.py <term> --domain <domain>
```

Exits 1 when packages mention the term but do not route on it, so it can gate a
wave. Run it after any change to skill `description` or `triggers`.

## Running agent evals

```bash
python3 evals/agents/scripts/run_agent_evals.py --structure
python3 evals/agents/scripts/run_agent_evals.py \
  --file evals/agents/fixtures/field-impact-analyzer/case-rename-billingcity.yaml
python3 evals/agents/scripts/run_agent_evals.py \
  --file <fixture.yaml> --grade --envelope <produced-envelope.json>
```

`--structure` lints all 53 fixtures. The runner makes no network or model
calls: the agent runs in the caller's model and you hand the envelope it
produced to `--grade`. The only flags are `--structure`, `--file`, `--grade`,
`--envelope`. Fixture format lives in `evals/agents/framework.md`.

Skill-output evals are separate: `python3 evals/scripts/run_evals.py
--structure` lints the 10 flagship files under `evals/golden/`.
