# AGENTS.md

Repo-local agent instructions live in [AGENT_RULES.md](./AGENT_RULES.md).

Any coding agent working in this repository must:

1. Read `AGENT_RULES.md` before creating or materially revising a skill.
2. Treat `SKILL.md` frontmatter as the canonical skill metadata source.
3. Use `python3 scripts/search_knowledge.py` before creating a new skill or claiming a coverage gap.
4. Run `python3 scripts/skill_sync.py` and `python3 scripts/validate_repo.py` after skill changes.
5. Never hand-edit generated files in `registry/`, `vector_index/`, or `docs/SKILLS.md`.

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

## Reading / updating the skill queue

`MASTER_QUEUE.md` is the authoritative queue. Do not `grep`/`sed` it — use:

```bash
python3 scripts/queue_reader.py --summary
python3 scripts/queue_reader.py --next --status TODO,RESEARCHED
python3 scripts/queue_reader.py --set-status IN_PROGRESS \
  --id <skill-name-or-row-id> --actor "<agent-name>@<host>"
```

See `docs/QUEUE_FORMAT_PROPOSAL.md` for the reader contract and the deferred
YAML migration plan.

## Running agent evals

```bash
python3 evals/agents/scripts/run_agent_evals.py --structure   # lint fixtures
python3 evals/agents/scripts/run_agent_evals.py --agent field-impact-analyzer --output path/to/output.json
```

Fixture format lives in `evals/agents/framework.md`.
