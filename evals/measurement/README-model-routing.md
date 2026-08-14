# Model-routing benchmark — measuring the path that actually ships

`run_heldout.py` measures `search_knowledge.py`. **Most users never run that
code.** `vector_index/` is gitignored — `git ls-files vector_index` returns only
`manifest.json`, `query-fixtures.json` and `query-variants.json` — so on a fresh
install there is no FTS5 index and no embeddings.

What ships is a roster. Claude reads the 11 router `description:` values, opens
one `.claude/skills/salesforce-<domain>/references/skill-index.md`, scans ~1,027
one-line glosses, and picks. Lexical search is mechanism 3 of 3, behind a local
`build_index.py` run; the MCP server is mechanism 2 and is not auto-wired.

**This benchmark measures mechanism 1.** It is the honest counterpart to
`run_heldout.py`, in the same way `run_heldout.py` is the honest counterpart to
`query-fixtures.json`.

## Running it

```
Workflow { scriptPath: ".claude/workflows/model-routing-benchmark.js" }
```

Twenty agents. Ten route a tenth of `heldout-queries.json` each; ten then
re-adjudicate every miss by reading both packages. Roughly 10 minutes.

The routing agents are **forbidden** from running `search_knowledge.py`,
querying `lexical.sqlite`, grepping `skills/`, or opening any
`skills/**/SKILL.md`. They may read only the router descriptions and the roster
files. That restriction is the measurement — lift it and the number silently
becomes mechanism 3 again, which is how the previous attempt to measure this
path was lost.

They are also told to route BEFORE looking at `expected_skill`. A router that
peeks produces a meaningless number.

## Results, 2026-08-14

Raw result sets are in `model-routing/`, one per run.

| | baseline | after the routing wave |
|---|---:|---:|
| Hit@1 | 79.2% | **92.2%** |
| expected in top 3 | 90.9% | **99.4%** |
| correct router / domain | 88.3% | **96.1%** |
| misses | 43 | 12 |
| — genuine corpus defects | 22 | 8 |
| — benchmark mislabels | 21 | 4 |

For scale, `run_heldout.py` over the same 154 queries moved 37.0% → 40.9% Hit@1
across the same change. Both paths improved; only one of them ships.

What moved it: `NOT for X — use Y` clauses naming a package that exists went
from 181 to 1,011 of 1,027 descriptions, and the share of shipped glosses where
that destination survives the 220-character budget went from 9% to 97%.

## Read the mislabels before trusting a miss

**Half the baseline's misses were wrong LABELS, not wrong routing.** The
adjudication phase exists to separate them, and it changes what you should fix.

The clearest example: `"the org is a mess where do I start"` is labelled
`admin/org-cleanup-and-technical-debt`. But that package's own description says
*"NOT for assessing or reporting on technical debt (use
architect/technical-debt-assessment)"*, and its declared inputs presuppose you
already hold a list of metadata to clean. The router obeyed the corpus's
explicit redirect and picked the triage package. The corpus was right and the
label was wrong.

So a falling Hit@1 is not automatically a regression, and a rising one is not
automatically an improvement. Read `defects[].label_is_wrong` first.

## Defect classes the analysis emits

| class | fix it by |
|---|---|
| `WRONG_ROUTER` | the 11 router descriptions, not the 1,027 glosses |
| `GLOSS_TOO_VAGUE` | put the query's own vocabulary in the expected package's description |
| `NO_REDIRECT` | add `NOT for <topic> — use <slug>` to the package that WAS picked |
| `GLOSS_TRUNCATED` | shorten the description; the budget is 220 characters |
| `GENUINE_OVERLAP` | two packages both fairly cover it — a merge candidate |
| `LABEL_ARBITRARY` | fix the benchmark, not the corpus |

Note where the leverage sits: a `WRONG_ROUTER` miss is fixed in one of eleven
files, not one of a thousand.

## Related

- `README-heldout.md` — the same argument one layer down, for mechanism 3
- `scripts/build_plugin.py` — `build_gloss()` and the `MAX_GLOSS_CHARS` block
- `scripts/skill_doctor.py` — its `routing` check is this benchmark's lever,
  evaluated per skill
