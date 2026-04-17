# Agent Evals

Golden evals for SfSkills **agents** (as opposed to skills). Where `evals/golden/` grades what an AI produces once a single skill is activated, `evals/agents/` grades what an AI produces once a multi-step agent is activated.

## What an agent eval tests

Two things, in this order:

1. **Output-envelope well-formedness** — the structured JSON the agent emits validates against `agents/_shared/schemas/output-envelope.schema.json` for the declared `mode`. This is the agent's contract with its callers.
2. **Rubric correctness** — for a given fixture (inputs + org metadata stub), the agent's deliverable includes the required findings, cites the required skills/templates/probes, hits the right confidence score, and doesn't produce forbidden findings.

An agent eval is a *fixture + expected envelope shape + rubric*. The runner compares the envelope the model produces to the fixture's expectations; structural lint runs without any model invocation.

## Layout

```
evals/agents/
├── README.md                                   ← this file
├── framework.md                                ← eval schema + scoring rubric
├── fixtures/
│   └── field-impact-analyzer/
│       ├── case-rename-billingcity.yaml        ← one fixture = one case
│       └── case-delete-never-populated.yaml
└── (add more <agent-slug>/ directories per agent)
```

Each fixture is a YAML file with this shape:

```yaml
eval:
  id: field-impact-analyzer__case-rename-billingcity
  agent: field-impact-analyzer
  mode: single
  priority: P0
  last_verified: 2026-04-16

inputs:
  object: Account
  field: BillingCity
  target_org_alias: uat-fixture

org_stub:
  apex_hits:
    - {kind: ApexClass, name: AccountService, access: read}
    - {kind: ApexTrigger, name: AccountTrigger, access: write}
  flow_hits: []
  matching_rule_hits: []

expect:
  confidence: HIGH
  must_include_findings_with_any_of_ids:
    - "apex.read"
    - "apex.write"
  must_cite_any_of:
    - skill: admin/field-impact-analysis
  must_not_cite_probes:
    - flow-references-to-field    # fixture says no flow hits — probe shouldn't be claimed
  process_observations:
    min_count: 1
    categories_present_any_of: [healthy, concerning]
```

## Running

```bash
# Structural lint only — no grader, no model calls. Fast.
python3 evals/agents/scripts/run_agent_evals.py --structure

# Lint one fixture.
python3 evals/agents/scripts/run_agent_evals.py --file evals/agents/fixtures/field-impact-analyzer/case-rename-billingcity.yaml

# Grade an agent run (an envelope JSON produced by a model) against its fixture.
python3 evals/agents/scripts/run_agent_evals.py --grade \
  --file evals/agents/fixtures/field-impact-analyzer/case-rename-billingcity.yaml \
  --envelope /tmp/run-42-envelope.json
```

The grader is deterministic — it does not invoke an LLM. The way to wire this into a full pipeline is:

1. Build the fixture's input packet + org stub.
2. Invoke the agent (any LLM following `agents/<slug>/AGENT.md`).
3. Capture the structured `envelope.json` the agent emits.
4. Run the grader against the envelope.

Step 2 is intentionally out of scope for this runner — like the skill-eval runner, we stay pluggable with whatever model provider the team already uses.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All checks pass |
| 1 | Structural lint failure |
| 2 | P0 rubric failure |
| 3 | Invalid CLI usage |

## Expansion roadmap

Start with the highest-blast-radius agents:

- `field-impact-analyzer` (first — shipped with the initial framework)
- `permission-set-architect`
- `duplicate-rule-designer`
- `security-scanner`
- `soql-optimizer`

Each agent's first fixture should cover the canonical happy path. The second fixture should cover the refusal path (missing org, ambiguous input, etc.).
