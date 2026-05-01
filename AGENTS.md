# AGENTS.md

Repo-local agent instructions live in [AGENT_RULES.md](./AGENT_RULES.md).

Any coding agent working in this repository must:

1. Read `AGENT_RULES.md` before creating or materially revising a skill.
2. Treat `SKILL.md` frontmatter as the canonical skill metadata source.
3. Apply `standards/skill-content-contract.md` (what to say) and `standards/skill-authoring-style.md` (how to say it) when authoring or editing SKILL.md content.
4. Use `python3 scripts/search_knowledge.py` before creating a new skill or claiming a coverage gap.
5. Run `python3 scripts/skill_sync.py` and `python3 scripts/validate_repo.py` after skill changes.
6. Never hand-edit generated files in `registry/`, `vector_index/`, or `docs/SKILLS.md`.

## Working on agents (not skills)

Agents live under `agents/<slug>/AGENT.md`. Before editing or adding one:

1. Read `agents/_shared/AGENT_CONTRACT.md` for the frontmatter spec, required
   section order, confidence rubric, and structured citation/output formats.
2. For skill-builder agents, also read `agents/_shared/SKILL_BUILDER_CORE.md`.
3. Reuse probes from `agents/_shared/probes/` instead of hand-rolling MCP
   queries.
4. Use refusal codes from `agents/_shared/REFUSAL_CODES.md` in output envelopes.

After editing any `AGENT.md` run:

```bash
python3 scripts/validate_repo.py --agents
```

`validate_repo.py --all` runs both skill and agent validation (slow; skill
compilation + query fixtures). Use `--agents` or `--skills-only` for fast
iteration.

## Install the git hooks (strongly recommended)

One-time setup per clone:

```bash
python3 scripts/install_hooks.py
```

This configures `core.hooksPath` to `.githooks/` and installs two hooks:

- **`pre-commit`** — runs `skill_sync --changed-only` and `validate_repo --changed-only`. Fast (<5s).
- **`pre-push`** — runs the full 4-shard validation CI runs. Catches cross-cutting drift (stale registries, schema-enum drift, missing query fixtures) that `--changed-only` can't see. 10–20s.

Bypass for WIP: `git commit --no-verify` / `git push --no-verify`. CI still gates merge.

## Reading / updating the skill queue

`BACKLOG.yaml` is the authoritative machine-readable queue (the row data formerly
inside `MASTER_QUEUE.md`, migrated 2026-05-01). Do not hand-edit it — use:

```bash
python3 scripts/queue_reader.py --summary
python3 scripts/queue_reader.py --next --status TODO,RESEARCHED
python3 scripts/queue_reader.py --set-status IN_PROGRESS \
  --id <entry-id> --actor "<agent-name>@<host>"
```

The generated dashboard at `docs/queue-progress.md` shows status counts, drift
between queue and disk, oldest TODO, and the next 10 picks. It regenerates on
every `skill_sync.py` run.

`MASTER_QUEUE.md` is now a short prose intro + agent workflow doc. The
historical row data is preserved in git history and reproducible from a
pre-migration `MASTER_QUEUE.md` via `scripts/_migrations/migrate_queue_to_yaml.py`.

## Running agent evals

```bash
python3 evals/agents/scripts/run_agent_evals.py --structure   # lint fixtures
python3 evals/agents/scripts/run_agent_evals.py --agent field-impact-analyzer --output path/to/output.json
```

Fixture format lives in `evals/agents/framework.md`.
