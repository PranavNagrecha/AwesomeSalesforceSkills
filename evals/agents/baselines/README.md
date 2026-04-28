# Agent Envelope Baselines

This directory holds **structural fingerprints** of past agent runs. Each baseline is the load-bearing shape of an envelope produced by [`scripts/execute_agent_fixture.py`](../../../scripts/execute_agent_fixture.py) for a given fixture. Future runs of the same fixture compare against the baseline; structural changes raise drift alerts.

A baseline is **not** the full envelope. Model output prose (summary, observation text, deliverable bodies) varies run-to-run and would create noise diffs. The baseline distills only what should be stable: the agent's confidence, refusal code (if any), citations (`type` + `id`), follow-up agent recommendations, the multiset of process-observation categories, finding ids and severities, deliverable kinds, and dimension coverage.

## Layout

```
evals/agents/baselines/
└── <agent-slug>/
    └── <case-stem>.baseline.json
```

Where `<case-stem>` is the fixture filename without `.yaml`. One baseline per fixture.

## Workflow

Seed a baseline (typically once, after a human-reviewed clean run):

```bash
python3 scripts/baseline_agent_envelope.py create \
  --fixture evals/agents/fixtures/<agent>/<case>.yaml \
  --envelope docs/validation/agent_executions_<date>/<agent>__<case>.envelope.json \
  --model claude-sonnet-4-5
```

Check a fresh run for drift:

```bash
python3 scripts/baseline_agent_envelope.py check \
  --fixture evals/agents/fixtures/<agent>/<case>.yaml \
  --envelope docs/validation/agent_executions_<date>/<agent>__<case>.envelope.json
```

Or let `execute_agent_fixture.py` do it inline (default `--baseline=auto`):

```bash
python3 scripts/execute_agent_fixture.py \
  --fixture evals/agents/fixtures/<agent>/<case>.yaml
```

`--baseline=auto` checks if a baseline exists and silently skips if not. `--baseline=check` fails if no baseline exists. `--baseline=create` seeds one. `--baseline=create-force` overwrites.

## Reading drift output

Drift output is per-field. Example:

```
DRIFT vs evals/agents/baselines/apex-refactorer/happy-path.baseline.json:
  citations: added=[['skill', 'apex/new-skill']]
  confidence: 'MEDIUM' -> 'LOW'
  followup_agents: removed=['detect-drift']
```

Each baseline file also stores SHA-256 of the fixture YAML and the agent's `AGENT.md` at capture time. When drift is reported, the checker also flags whether either of those changed since the baseline — which often explains the drift.

## When to regenerate a baseline

- The fixture inputs intentionally changed (rerun + `create --force`).
- The agent's plan or output contract intentionally changed (rerun + `create --force`).
- A new template / decision tree / skill landed and the agent is expected to cite it.
- The model used for the harness was upgraded and the new envelope is reviewed and accepted.

Never regenerate a baseline to "make CI pass" without reviewing the diff. The whole point of baselines is to catch silent regressions; auto-accepting drift defeats them.

## What the baseline does NOT cover

- Wording / phrasing of `summary` or `process_observations[].observation`.
- Full content of `deliverables[].content` (Apex bodies, etc.).
- `confidence_rationale` text.
- Order of items inside arrays (everything is sorted before comparison).
- `inputs_received` echo (varies with default application).

If you need correctness-of-content checks — e.g. "the refactored Apex still compiles" — those belong in a separate harness (deploy-to-scratch-org or `scripts/smoke_test_agents.py`), not in the baseline layer.
