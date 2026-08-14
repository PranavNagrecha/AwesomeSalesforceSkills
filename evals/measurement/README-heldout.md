# Held-out retrieval benchmark

`evals/measurement/heldout-queries.json` holds 154 queries and
`evals/measurement/run_heldout.py` scores retrieval against them. Every query was
written by hand, none of them appears anywhere in the index, and the set is
deliberately harder than the generated fixtures. It is the honest counterpart to
`vector_index/query-fixtures.json`, which measures the same retrieval stack
against vocabulary that stack already contains.

## Why it exists

The fixture sweep grades retrieval on text that is in the index by construction.

`scripts/build_index.py` builds the index through `pipelines/sync_engine.py`,
which appends each skill's `triggers:` frontmatter to that skill's document as a
`## Trigger Scenarios` section. `pipelines/lexical_index.py` then indexes
`title`, `tags` and `text` into FTS5. So a skill's own trigger strings become
searchable chunk text, and a fixture that paraphrases those triggers is querying
material the skill put into the index itself.

The concrete case: `admin/validation-rules` owns a chunk titled
`Trigger Scenarios` whose text is literally its six trigger strings —
"validation rule is blocking an API integration", "how do I bypass a validation
rule for admins", and four more. Its fixture is the keyword bag
`validation rule bypass formula data quality`, assembled from the same skill's
tags and description.

The consequence, in one line: the fixture sweep measures recall of indexed
vocabulary, not recall of a practitioner's phrasing.

Historical motivation, **no longer reproducible** — measured 2026-07-31 before
the retrieval fixes landed: a 400-fixture sample reported a 0.8% "Coverage:
NONE" rate against 23.3% on hand-written realistic phrasings, a 29x gap, and
hand-labelled Hit@1 was 95% on fixtures against 50% on a 20-query held-out set.
Those exact figures cannot be reproduced today because the coverage gate is now
`max_score >= 1.0 OR score >= 1.5` and the ranker now adds a name/description
centrality bonus (`config/retrieval-config.yaml`, `pipelines/ranking.py`). The
gap they describe did not close — see below — but re-measure rather than quoting
them.

## What it measures

Three aggregate numbers, per `evaluate()` in `evals/measurement/run_heldout.py`:

| Metric | Definition |
|---|---|
| **Hit@1** | `payload['skills'][0]['id'] == expected_skill` |
| **Hit@k** | `expected_skill in [s['id'] for s in payload['skills'][:k]]`, k = `--top-k` (default 3) |
| **NONE rate** | share of queries where `payload['has_coverage']` is false |

All three read the **gated** skills list — the one `run_search` actually returns
after filtering on `max_score >= min_skill_max_score or score >= min_skill_score`
(`scripts/search_knowledge.py`, thresholds in `config/retrieval-config.yaml`).
That is what a caller sees. Scoring the raw pre-gate aggregate would flatter the
numbers, because it counts skills the caller is never shown.

Three honesty caveats:

- **One label per query.** Each entry names exactly one `expected_skill`, so a
  defensible alternative answer scores as a miss. Treat the absolute values as a
  floor and the run-to-run delta as the signal.
- **`misses` lists Hit@k misses only.** A query whose expected skill sits at
  rank 2 is a Hit@1 miss but never appears in the `misses` list.
- **The JSON key stays `hit_at_3`** even when `--top-k` is not 3; the text
  output relabels it, the JSON does not.

## Current numbers

Measured **2026-08-01** on commit `38aea1e34`, against an index rebuilt that
morning (`vector_index/chunks.jsonl` 126 MB, `vector_index/embeddings.jsonl`
535 MB). Same binary, same index, for every row.

| Run | n | Hit@1 | Hit@3 | NONE |
|---|---:|---:|---:|---:|
| Held-out, default | 154 | **35.7%** | 46.8% | 4.5% |
| Held-out, `--no-embeddings` | 154 | 34.4% | 42.2% | 5.2% |
| Held-out, `--tag evidence-20` | 20 | 60.0% | 65.0% | 5.0% |
| Held-out, `--tag evidence-60` | 60 | 20.0% | 28.3% | 6.7% |
| Fixtures, domain-free | 1356 | 95.5% | 98.7% | 0.07% |
| Fixtures, `--use-domain` | 1356 | **98.2%** | 99.9% | 0.0% |

```bash
python3 evals/measurement/run_heldout.py
python3 evals/measurement/run_heldout.py --no-embeddings
python3 evals/measurement/run_heldout.py --tag evidence-20
python3 evals/measurement/run_heldout.py --tag evidence-60
python3 evals/measurement/run_heldout.py --queries vector_index/query-fixtures.json
python3 evals/measurement/run_heldout.py --queries vector_index/query-fixtures.json --use-domain
```

The headline gap is **98.2% vs 35.7% Hit@1 and 0.0% vs 4.5% NONE** — the fixture
set with its domain hint, which is the configuration `scripts/validate_repo.py`
step 5 runs, against the same stack asked a question nobody indexed. Embeddings
are worth about 1.3pp Hit@1 and 4.6pp Hit@3 on the held-out set, for 535 MB and
the fastembed dependency. The gap is *wider* than it was on 2026-07-31,
because the retrieval fixes lifted the fixture side further than the held-out
side. That is the finding this benchmark exists to publish, not a defect in the
benchmark.

## Running

```bash
--queries PATH      Benchmark file. Defaults to heldout-queries.json; accepts
                    vector_index/query-fixtures.json unchanged.
--tag TAG           Only entries carrying TAG. Repeatable, OR semantics.
                    `evidence-20` / `evidence-60` mark the queries carried over
                    from the 2026-07-31 evidence brief (20 and 60 entries;
                    6 carry both, 80 carry neither).
--use-domain        Pass each entry's `domain` into run_search. Off by default
                    because a real caller supplies none. On, it reproduces the
                    configuration validate_repo.py step 5 uses.
--top-k N           Hit@k depth, default 3. A per-entry `top_k` overrides it,
                    which the fixture file supplies and the held-out set does not.
--no-embeddings     Stub the embedding loaders rather than read 535 MB off disk
                    and discard it. Reproduces the lexical-only configuration.
--json              Machine-readable result, including the full misses list.
--check             Validate the benchmark file only; run no queries.
--min-hit1 F        Fail when Hit@1 falls below F.
--min-hit3 F        Fail when Hit@3 falls below F.
--max-none F        Fail when the NONE rate rises above F.
```

Exit codes:

| Code | Meaning |
|---|---|
| 0 | Pass |
| 1 | A threshold floor was breached, or `--check` found a problem |
| 2 | A label points at a skill that is not on disk. Reported before any metric runs |

Measured runtimes on an Apple M3 laptop with a warm cache, 2026-08-01: `--check`
0.14s; a held-out run about half a minute (25s lexical-only, 38s with
embeddings); a full 1,356-fixture sweep two and a half to three and a half
minutes per configuration. Most of a short run is the one-off
`build_search_context` load, roughly ten seconds, not the queries.

## Adding queries

1. **Hand-write the query the way a practitioner types it.** Lowercase, partial,
   symptom-first — "my batch job keeps timing out", not "batch apex governor
   limits".
2. **Never copy or paraphrase a skill's `triggers:`, `tags:` or `description:`.**
   Doing so silently re-creates the exact overfitting this benchmark exists to
   detect: the query stops testing retrieval and starts testing string match
   against text the skill put in the index. `--check` rejects only *verbatim*
   overlap with the fixture set; it cannot detect paraphrase, so this one is on
   the contributor.
3. **Verify every `expected_skill` resolves** to a real
   `skills/<domain>/<slug>/SKILL.md`. A phantom label makes every number in the
   report a lie, which is why the tool exits 2 on one before running a single
   query.
4. **Keep all 11 registry categories represented**, so no domain rots unmeasured.
5. **Bump `updated`** in `evals/measurement/heldout-queries.json`.
6. **Run `--check` before opening the PR.**

What `--check` enforces today: at least 120 queries, at least 6 per category, no
duplicate `query` strings, no category outside the registry list, and zero
verbatim overlap with `vector_index/query-fixtures.json`. Current headroom: 154
queries against the floor of 120, and omnistudio at 8 entries is the category
nearest the per-category floor of 6.

## The four harnesses

| Harness | Question it answers | Shape |
|---|---|---|
| `vector_index/query-fixtures.json`, run by `scripts/validate_repo.py` step 5 | Does each skill still retrieve for its own indexed vocabulary? | 1,356 generated queries, per-fixture pass/fail, domain hint supplied |
| `evals/measurement/run_heldout.py` | Does the right skill retrieve for a phrasing nobody indexed? | 154 hand-written queries, aggregate metrics, no domain hint |
| `evals/measurement/run_model_routing.py` | Does Claude pick the right skill from router + roster glosses (the shipped path)? | 154 held-out queries, agent-simulated routing, see `README-model-routing.md` |
| `evals/golden/` | Once the skill is activated, is the output correct? | 30 P0 cases across 10 flagship skills, graded against a rubric |

They are complementary, not redundant: the fixture sweep is a regression
tripwire (one skill stopped retrieving), this benchmark is a quality measurement
(retrieval is worse than the tripwire suggests), model routing measures what
actually ships on a fresh install, and the golden evals start where all three stop. Note that `evals/framework.md` says "Evals are NOT retrieval
tests. `query-fixtures.json` owns that." — written 2026-04-16, before this
benchmark existed. This file is the retrieval-quality harness that sentence
points away from; the disclaimer is still right about `evals/golden/`.

Where the fixture gate runs, as of 2026-08-01: `.github/workflows/validate.yml`
runs `scripts/validate_repo.py --skills-only --shard N/4` with the fixture step
live, while `.githooks/pre-push` still passes `--skip-fixture-retrieval` to keep
push latency down. Re-check with
`grep -rn skip-fixture-retrieval .github/workflows/ .githooks/` — this has moved
before.

## CI status

Not wired, as of 2026-08-01. `grep -rn run_heldout .github/workflows/ .githooks/`
returns nothing — this benchmark runs only when someone runs it.

The intended shape when it is wired: `--check` on every PR (sub-second, no
index needed beyond the fixture file), and the `--min-hit1` / `--min-hit3` /
`--max-none` floors on a slower job that has the index available. Set the floors
from a measured baseline, not from an aspiration.
