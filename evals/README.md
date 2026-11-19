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
├── measurement/            ← retrieval, routing and knowledge-lift results
└── scripts/
    ├── run_evals.py        ← CLI that loads an eval file and grades output
    └── run_lift.py         ← knowledge-lift test: each case with and without the skill loaded
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

## Why these ten

They were picked by judgement as common Apex, integration, LWC and Flow
builder topics where a wrong answer is costly (governor limits, credentials,
bulkification, FLS). Neither retrieval frequency nor bug cost was measured.
There is no expansion plan; `framework.md` § "Adding a new eval" describes how
to add one.

## Knowledge lift on these 30 cases

`evals/scripts/run_lift.py` answers every case twice with the same model, once
with the skill package in the prompt and once without, and a separate grader
model scores both blind against the rubric (R1-12 in `RELEASES.yaml`, run
2026-10-19; Sonnet answers, Opus grader; baseline
`evals/measurement/lift-baseline-2026-10-19.json`):

| Result | Value |
|---|---|
| Skill-loaded answer scored higher | 22 of 30 |
| Skill-loaded answer scored lower | 6 of 30 |
| Tie | 2 of 30 |
| Mean rubric delta (1–5 scale) | +0.253 |
| MUST-assertion violations | 107 without the skill, 91 with it |

Limits: one run of 30 cases over 10 skills in 4 domains; one grader model;
`async-apex` scored lower with its skill loaded (−0.27). It shows that a skill's
text reaches the answer, not that the other packages would help. The same
harness with `--probes` measured fact probes on audited skills (20 Winter '27
probes: 0% → 100% correct; 10 more: 50% → 100%), recorded in the 1.5.0
`decision_memo` in `RELEASES.yaml`.

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
3. A full grader run is optional: `scripts/release_gate.sh` grades the golden
   evals only when `RELEASE_GRADER=1` is set. Nothing in CI scores answers
   against the rubric. See `framework.md` "When an eval fails".

## Relationship to other repo concepts

| Concept | Scope | Owns |
|---|---|---|
| `vector_index/query-fixtures.json` | Retrieval | "Does the right skill get picked?" |
| `evals/golden/` | Output | "Does the right code get produced?" |
| `standards/skill-content-contract.md` | Authoring | "Is the skill well-written?" |
| `scripts/validate_repo.py` | Structure | "Is the repo well-formed?" |
| `standards/decision-trees/` | Routing | "Did we pick the right tool?" |
| `templates/` | Idioms | "Is the implementation canonical?" |

Evals check output for 10 skills only; they do not answer whether the
system works end to end.
