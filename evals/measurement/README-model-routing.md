# Model-driven routing benchmark

Measures the **shipped** skill-selection path — the one a fresh Claude install
actually uses. This is distinct from `run_heldout.py`, which scores FTS5 /
embedding retrieval over `vector_index/` (gitignored, does not ship).

## What it measures

| Step | Source |
|---|---|
| Router pick | `description:` on `.claude/skills/salesforce-*/SKILL.md` |
| Skill pick | One-line gloss in the router's `references/skill-index.md` |

| Metric | Definition |
|---|---|
| **Hit@1** | `skill_picked == expected_skill` |
| **Hit@3** | Expected skill was among the agent's top-3 candidates |
| **Router correct** | Chosen router domain matches expected skill domain |

## Current numbers

Measured **2026-08-14** on branch `overhaul/2026-08-01-checkpoint`, 154 held-out
queries, agent-simulated routing (no search index). Gold labels include the
documented relabels (now 20).

| Run | Hit@1 | Hit@3 | Router |
|---|---:|---:|---:|
| Live re-route + three post-fix edits (CI relabel; 100-callout and hallucination glosses) | **98.7%** | **100%** | 88.3% |
| Live re-route (post-fix glosses + 19 relabels, before the three edits) | 96.8% | 99.4% | 88.3% |
| Prior snapshot (pre-relabel gold, pre-fix glosses) | 79.2% | 90.9% | — |

Two remaining Hit@1 misses are both SSO **setup** queries labelled
`security/sso-saml-troubleshooting`, which NOT-fors initial setup. That package
points at `admin/connected-apps-and-auth` (OAuth/connected apps) and at a
nonexistent `security/sso-saml-setup`. Relabelling would hide a coverage gap.
Router-correct is lower than Hit@1 because several correct picks follow a
NOT-for into another domain.

For comparison, the same queries through FTS5 retrieval (`run_heldout.py`):
Hit@1 **37.0%**, Hit@3 **48.7%**, NONE **0.0%**.

## Running

Score a saved routing run (produced by the workflow):

```bash
python3 evals/measurement/run_model_routing.py \
  --results .overhaul-2026-08/research/routing-benchmark-routed.json
```

Validate benchmark health and relabel status:

```bash
python3 evals/measurement/run_model_routing.py --check
```

Apply documented benchmark relabels (21 mislabels where the router pick was
defensible):

```bash
python3 evals/measurement/run_model_routing.py --apply-relabels --dry-run
python3 evals/measurement/run_model_routing.py --apply-relabels
```

Estimate post-relabel score without re-running agents:

```bash
python3 evals/measurement/run_model_routing.py --rescore-relabels
```

## Re-running live routing

Live routing requires an LLM to read glosses and pick — it is not fully
automatable. Re-run via the `sfskills-model-routing-benchmark` workflow script
under `.claude/workflows/` (10 batches × route + analyse phases).

Save output to `.overhaul-2026-08/research/routing-benchmark-routed.json` and
defect analysis to `routing-benchmark-defects.json`.

## The four harnesses

| Harness | Question | Mechanism |
|---|---|---|
| `query-fixtures.json` + validate_repo step 5 | Does each skill retrieve for its indexed vocabulary? | FTS5 + optional embeddings |
| `run_heldout.py` | Does retrieval work for practitioner phrasing? | FTS5 + optional embeddings |
| **`run_model_routing.py`** | **Does Claude pick the right skill from glosses?** | **Router + roster (shipped)** |
| `evals/golden/` | Is the activated skill's output correct? | Rubric grading |

## CI status

Not wired as of 2026-08-14. Intended shape: `--check` on every PR (fast),
`--min-hit1` / `--min-hit3` floors on a slower agent-routing job after corpus
changes that touch `description:` or rosters.
