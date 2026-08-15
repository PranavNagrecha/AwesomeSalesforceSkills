# Model-routing benchmark — measuring the path that actually ships

`run_heldout.py` measures `search_knowledge.py`. **Most users never run that
code.** `vector_index/` is gitignored — `git ls-files vector_index` returns only
`manifest.json`, `query-fixtures.json` and `query-variants.json` — so on a fresh
install there is no FTS5 index and no embeddings.

What ships is a roster. Claude reads the router `description:` values under
`.claude/skills/` (a top-level `salesforce` router plus 11 domain routers),
opens one `salesforce-<domain>/references/skill-index.md`, scans its slice of
the 1,027 one-line glosses, and picks. Lexical search is mechanism 3 of 3,
behind a local `build_index.py` run; the MCP server is mechanism 2 and is not
auto-wired.

**This benchmark measures mechanism 1.** It is the honest counterpart to
`run_heldout.py`, in the same way `run_heldout.py` is the honest counterpart to
`query-fixtures.json`.

## Running it

```
Workflow { scriptPath: ".claude/workflows/model-routing-benchmark.js" }
```

Twenty agents. Ten route a tenth of `heldout-queries.json` each; ten then
re-adjudicate every miss by reading both packages. Roughly 10 minutes.

Scoring a saved run needs no agents:

```
python3 evals/measurement/run_model_routing.py --check
python3 evals/measurement/run_model_routing.py \
    --results evals/measurement/model-routing/baseline-2026-08-14.json --json
```

The routing agents are **forbidden** from running `search_knowledge.py`,
querying `lexical.sqlite`, grepping `skills/`, or opening any
`skills/**/SKILL.md`. They may read only the router descriptions and the roster
files. That restriction is the measurement — lift it and the number silently
becomes mechanism 3 again, which is how the previous attempt to measure this
path was lost.

They are also told to route BEFORE looking at `expected_skill`. A router that
peeks produces a meaningless number.

## ⚠ The 2026-08-14 result set is confounded — read this before citing it

The first use of this harness produced a headline of "79.2% → 92.2% Hit@1"
across the routing wave. **That comparison does not survive re-scoring and
should not be repeated.** Both runs are still in `model-routing/` because the
raw picks are useful; the *derived improvement* is what was wrong.

Score both saved runs against one label set and the direction inverts:

| scoring basis | baseline | after |
|---|---:|---:|
| labels as they stood before the wave | 85.7% | 80.5% |
| labels as they stand now | 98.7% | 92.2% |
| now, **excluding the 20 relabelled queries** | **98.5%** | **92.5%** |

Query-level diff: **10 regressions, 0 improvements.**

Two independent defects produced the phantom gain.

**1. The comparison was circular.** During adjudication, 41 of the baseline
run's 43 miss rows had their `expected` label rewritten to whatever the
*baseline run itself* had picked. Twenty of those were then written back into
`heldout-queries.json` via `RELABEL_MAP`. Scoring the after run against labels
derived from the baseline's own behaviour structurally favours the baseline —
and scoring the baseline against them is close to tautological. The third row
above excludes those 20 queries and the gap persists, so circularity is not the
whole story, but neither published number was ever a clean read.

**2. Exact-match scoring cannot see near-duplicates.** Eight of the ten
regressions are near-duplicate pairs where the "wrong" pick is defensible:

| query | label | after-run pick |
|---|---|---|
| force everyone onto mfa without locking out integrations | `security/mfa-enforcement-strategy` | `security/mfa-enforcement-patterns` |
| we need to keep 7 years of cases but not in the main object | `data/data-archival-strategies` | `data/service-data-archival` |
| how do I stop my flow from hitting SOQL limits | `flow/flow-bulkification` | `flow/flow-get-records-optimization` |
| hardcoded record type ids everywhere | `apex/apex-hardcoded-id-elimination` | `admin/record-type-id-management` |

A corpus with 1,027 packages has many such pairs. Exact-match Hit@1 charges
the router for the corpus's own redundancy.

**The one robust, label-independent improvement is router accuracy: 88.3% →
96.1%** — which of the 12 routers gets opened. That metric does not depend on
the relabelled skill labels, and the wave did rewrite router descriptions, so
the causal story holds for this number and only this number.

### The rule this establishes

**Never score a corpus change against labels derived from a run of that same
corpus.** Freeze the labels before the change lands, or stop scoring exact
match and have an independent adjudicator rule each pick *acceptable* or
*not* — which is the only scoring that survives near-duplicate pairs.

## Read the mislabels before trusting a miss

Even setting the confound aside, a large share of misses are wrong LABELS
rather than wrong routing, and that changes what you should fix.

The clearest example: `"the org is a mess where do I start"` was labelled
`admin/org-cleanup-and-technical-debt`. But that package's own description says
*"NOT for assessing or reporting on technical debt (use
architect/technical-debt-assessment)"*, and its declared inputs presuppose you
already hold a list of metadata to clean. The router obeyed the corpus's
explicit redirect and picked the triage package. The corpus was right and the
label was wrong.

So a falling Hit@1 is not automatically a regression, and a rising one is not
automatically an improvement. Read `defects[].label_is_wrong` first — then
check whether the label was rewritten from a run you are now comparing against.

## Defect classes the analysis emits

| class | fix it by |
|---|---|
| `WRONG_ROUTER` | the router descriptions, not the 1,027 glosses |
| `GLOSS_TOO_VAGUE` | put the query's own vocabulary in the expected package's description |
| `NO_REDIRECT` | add `NOT for <topic> — use <slug>` to the package that WAS picked |
| `GLOSS_TRUNCATED` | shorten the description; the budget is 220 characters |
| `GENUINE_OVERLAP` | two packages both fairly cover it — a merge candidate, and a scoring hazard |
| `LABEL_ARBITRARY` | fix the benchmark, not the corpus |

Note where the leverage sits: a `WRONG_ROUTER` miss is fixed in one of twelve
files, not one of a thousand.

## Related

- `README-heldout.md` — the same argument one layer down, for mechanism 3
- `scripts/build_plugin.py` — `build_gloss()` and the `MAX_GLOSS_CHARS` block
- `scripts/skill_doctor.py` — its `routing` check is this benchmark's lever,
  evaluated per skill
