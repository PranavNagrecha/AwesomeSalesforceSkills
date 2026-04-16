# Evals

Golden evaluations for flagship skills. These test **output quality** — the
correctness of code and guidance an AI produces once a skill is activated —
not retrieval (which is handled by `vector_index/query-fixtures.json`).

## Layout

```
evals/
├── README.md               ← this file
├── framework.md            ← schema, priority levels, scoring rubric
├── golden/
│   ├── apex__trigger-framework.md
│   ├── apex__async-apex.md
│   ├── apex__batch-apex-patterns.md
│   ├── apex__apex-security-patterns.md
│   ├── integration__bulk-api-2-patterns.md
│   ├── integration__named-credentials-setup.md
│   ├── integration__callouts-and-http-integrations.md
│   ├── lwc__wire-service-patterns.md
│   ├── lwc__lwc-imperative-apex.md
│   └── flow__flow-bulkification.md
└── scripts/
    └── run_evals.py        ← CLI that loads an eval file and grades output
```

## What's covered today

| Category | Skill | Priority | Cases |
|---|---|---|---|
| Apex | `trigger-framework` | P0 | 3 |
| Apex | `async-apex` | P0 | 3 |
| Apex | `batch-apex-patterns` | P0 | 3 |
| Apex | `apex-security-patterns` | P0 | 3 |
| Integration | `bulk-api-2-patterns` | P0 | 3 |
| Integration | `named-credentials-setup` | P0 | 3 |
| Integration | `callouts-and-http-integrations` | P0 | 3 |
| LWC | `wire-service-patterns` | P0 | 3 |
| LWC | `lwc-imperative-apex` | P0 | 3 |
| Flow | `flow-bulkification` | P0 | 3 |

10 flagship skills, 30 P0 cases. Every case comes with a reference answer.

## Why these ten first

They are the **10 skills most likely to be retrieved** for Apex-heavy,
integration-heavy, and LWC-heavy builder queries, and the 10 whose
wrong answers cause the most expensive production bugs (governor-limit
blowups, credential leaks, unbulked automation, missing FLS).

The roadmap for expanding to the rest of the repo is in `framework.md`.

## Running an eval

The `run_evals.py` CLI supports three modes:

```bash
# Structural lint only — no model invocation. Fast.
python3 evals/scripts/run_evals.py --structure

# Dry run a single eval file (structural checks for one file).
python3 evals/scripts/run_evals.py --file evals/golden/apex__trigger-framework.md --dry-run

# Full grade — invokes a grader model for each case. Requires a grader.
python3 evals/scripts/run_evals.py --file evals/golden/apex__trigger-framework.md --grader <model-id>
```

The grader contract is defined in `framework.md` — any LLM that can follow
the rubric scoring guide can act as grader.

## Workflow for contributors

1. When you create or materially change a skill, add/update its eval.
2. Before merge, `--structure` must pass.
3. Before a release, the full grader run must pass P0 gates.
4. Failing evals block release — see `framework.md` "When an eval fails".

## Relationship to other repo concepts

| Concept | Scope | Owns |
|---|---|---|
| `vector_index/query-fixtures.json` | Retrieval | "Does the right skill get picked?" |
| `evals/golden/` | Output | "Does the right code get produced?" |
| `standards/skill-content-contract.md` | Authoring | "Is the skill well-written?" |
| `scripts/validate_repo.py` | Structure | "Is the repo well-formed?" |
| `standards/decision-trees/` | Routing | "Did we pick the right tool?" |
| `templates/` | Idioms | "Is the implementation canonical?" |

Evals sit at the intersection of all of these — they are where "did the
system work end-to-end?" is answered.
