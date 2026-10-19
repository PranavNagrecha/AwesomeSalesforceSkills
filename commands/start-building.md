# /start-building — run the release loop

```
/start-building [--release 1.4.0] [--once]
```

Starts the orchestrator ([`agents/orchestrator/AGENT.md`](../agents/orchestrator/AGENT.md)). It reads the release plan in `RELEASES.yaml`, dispatches the next item's work, merges and verifies each writer's output one at a time, commits, records the evidence, and picks again. It stops at the release: it prints the merge, push, and tag commands for you and runs none of them.

| arg | default | effect |
|---|---|---|
| `--release <version>` | the current release | which release's items to work |
| `--once` | off | advance one item, then stop instead of looping |

## What you need

A clean working tree (the loop's own files, `RELEASES.yaml` and generated artifacts, are fine) and a passing `python3 -m pytest tests/test_releases.py -q`. The loop refuses to start otherwise and says which file or test.

To see where the plan stands without starting anything:

```bash
python3 scripts/release_plan.py status
```

## Resuming

A run lives as long as its Claude Code session. All state is in `RELEASES.yaml` and git, so running `/start-building` again resumes exactly where the last run stopped: finished-but-unmerged writer worktrees are merged and verified, abandoned `running` items go back to `todo`, and nothing is re-planned.

## What it never does

Push, tag, deploy, edit `RELEASES.yaml` by hand, or run more than one subagent at a time.

## Related

- `/add-to-backlog` — add an ask to the plan
- `agents/orchestrator/AGENT.md` — the playbook
