# Troubleshooting

Symptom, cause, fix. Every entry below is a failure actually hit while walking
this repository's own documented paths, dated where the measurement matters.

The first three entries are failures of the path that ships — the model-driven
roster scan, which needs no index and is what a clone or plugin install
exercises. Everything after them is the keyword-search layer, which only exists
after you run `python3 scripts/bootstrap.py`. Earlier versions of this page
covered only the second group, which meant the two most likely real symptoms
were missing.

---

## Claude opened the wrong skill package

**Symptom.** You asked about record visibility and Claude opened an Apex
package. Or it opened a plausible neighbour — `security/mfa-enforcement-patterns`
when you wanted `security/mfa-enforcement-strategy`. The answer is confident and
grounded in a real package; it is just the wrong one.

**Cause.** The shipped path has **no coverage gate**. Mechanisms 2 and 3 score
candidates against a threshold and can print `Coverage: NONE`. A model scanning
a roster of one-line glosses always finds something plausible, so this path
cannot fail by returning nothing — it fails by being confidently wrong. That is
the designed trade: it works with zero setup, and it has no arithmetic to
refuse with.

Two upstream causes account for most of it. Domain overlap is the first: a
callout is Apex *and* integration, a sharing question is admin *and* security,
and the pick happens at the router before any roster is opened. Near-duplicate
packages are the second: the corpus contains genuine confusable pairs, and
which of the two is "correct" is sometimes a judgement call.

**Fix**, cheapest first:

1. **Name the domain.** "This is a sharing question, not an Apex one." The
   router pick is where routing goes wrong first, and it is the cheapest thing
   to override.
2. **Read the gloss it picked.** Glosses that have a confusable neighbour carry
   a `NOT for X - use Y` clause naming the package to open instead. Grep the
   roster for the topic:

   ```bash
   grep -i 'sharing' .claude/skills/salesforce-admin/references/skill-index.md
   ```

3. **Open the roster yourself** and paste the right skill id back. Rosters are
   plain markdown at
   `.claude/skills/salesforce-<domain>/references/skill-index.md`, one per
   domain, and they sum to exactly 1,027 lines across the eleven.
4. **Get a second opinion from search**, if you have run bootstrap:

   ```bash
   python3 scripts/search_knowledge.py "<your question in your own words>"
   ```

   It ranks by a completely different signal, so a disagreement is
   informative.

**What not to do.** Do not conclude the library lacks the topic. See the next
entry.

**If it keeps happening for one package**, the fix is upstream of the router. A
skill's `description:` frontmatter becomes its gloss by way of
`registry/skills.json`, so a package that is routinely missed usually has a
description that does not carry the phrasings people type. Editing a
description is editing routing behaviour; rerun `python3
scripts/skill_sync.py --skill skills/<domain>/<slug>` and `python3
scripts/build_plugin.py` afterwards.

---

## Claude says the topic is not covered

**Symptom.** "There is no skill for X in this library" — for an X that the
corpus plainly ought to cover.

**Cause.** Almost always the same one as above: the model scanned a roster,
did not recognise the topic under the vocabulary the glosses use, and
generalised from "I did not spot it" to "it does not exist". Occasionally the
search CLI reported `Coverage: NONE` because no index was built and the model
took that at face value.

Every domain router carries a standing rule against exactly this. From
`.claude/skills/salesforce-apex/SKILL.md`:

> 3. Never claim a topic is uncovered without pasting lookup output.

The routers also invert the fallback direction on purpose: if
`search_knowledge.py` errors or reports `Coverage: NONE`, the router tells the
model to fall back to the roster scan rather than tell you the topic is
uncovered. The roster is the floor, not the ceiling.

**Fix.** Ask for the evidence, then check it yourself:

```bash
grep -ril '<topic>' .claude/skills/*/references/skill-index.md
ls skills/*/ | grep -i '<topic>'
```

If both come back empty, it is a genuine gap — [../CONTRIBUTING.md](../CONTRIBUTING.md)
covers reporting one.

---

## Slash commands do not exist after cloning

**Symptom.** `/consolidate-triggers` and every other command in `commands/` are
not offered by Claude Code, and `git ls-files .claude/commands` returns
nothing.

**Cause.** `.gitignore:131` contains `.claude/*`, negated only for
`.claude/agents/`, `.claude/skills/` and `.claude/workflows/`. The tracked
command specs live in `commands/` at the repository root, which Claude Code
does not read. Tracking both copies would create a permanent drift surface
between two copies of the same file, which is why the generated copy is
deliberately not committed.

Note that this affects *only* the slash commands. The routers and agent loaders
under `.claude/skills/` and `.claude/agents/` **are** tracked, so a clone can
still reach every skill package without this step.

**Fix**

```bash
python3 scripts/bootstrap.py          # installs commands and builds the index
python3 scripts/install_local_commands.py   # commands only
```

The leading number in the output is `len(src_names)` — a live count of
`commands/*.md`, **67** on this checkout — not a constant, so compare it against
`ls commands/*.md | wc -l` rather than against any number written in a doc. On
a first install the counters read `added=67 updated=0`. Restart the CLI
afterwards; Claude Code loads slash commands at session start. Re-run the
script after pulling new commands or after one is retired — it also deletes
stale entries.

---

## `Coverage: NONE` on every query, with zero chunks listed

**Symptom**

```text
$ python3 scripts/search_knowledge.py "trigger recursion"
Query: trigger recursion

Coverage: NONE — no skill meets the confidence threshold. Use official sources below.
Top skills:

Top chunks:
$ echo $?
0
```

No chunks listed at all, and the exit code is 0.

**Cause.** There is no search index, and this means *"nothing built"*, not
*"empty library"*. `git ls-files vector_index` returns exactly three files —
`manifest.json`, `query-fixtures.json` and `query-variants.json`. The rest is
gitignored because it totals 295 MB on this checkout: `chunks.jsonl` at ~124 MB
and `lexical.sqlite` at ~165 MB.

The failure is silent because the lexical helper returns an empty list rather
than raising when the SQLite file is absent — verified directly:

```text
$ python3 -c "
from pipelines.lexical_index import search_index
from pathlib import Path
print(search_index(Path('/tmp/no-such-index.sqlite'), 'trigger recursion', None, 30))"
[]
```

So the whole pipeline runs, finds nothing, gates on nothing, and exits
successfully.

**Fix**

```bash
python3 scripts/bootstrap.py
```

About 9 s on the reference machine. Then re-run the search: a working result
names at least one skill under `Top skills:` with a score.

Use `bootstrap.py`, not `scripts/build_index.py`. The latter reaches the same
retrieval outcome through `pipelines.sync_engine.write_state`, which rewrites
every registry record — on a fresh clone with no embedding backend installed it
nulls `vector_embedding` across all 1,027 records, leaving about **1,029
modified tracked files** you then have to recognise as noise and discard.
Bootstrap never calls `write_state` and leaves `git status` clean.

To check the index rather than infer it, run `python3 scripts/bootstrap.py
--verify-only`. Unlike `search_knowledge.py` it exits non-zero and says which
assertion failed.

**The distinction that matters here.** *Zero chunks listed* means no index.
*Chunks listed but no skills* means the index is fine and the coverage gate
suppressed the result — a different problem, covered below.

---

## `sfskills-mcp-init` fails with HTTP 404

**Symptom**

```text
$ sfskills-mcp-init
sfskills-mcp-init: downloading https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
sfskills-mcp-init: HTTP 404 fetching https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
  Verify the release tag exists: https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases
```

Exit code 1.

**Cause.** The PyPI wheel deliberately ships without the corpus and expects to
fetch it from a GitHub Release asset named `sfskills-data.tar.gz`. No such
release has been published — re-checked 2026-08-14:

```text
$ gh api repos/PranavNagrecha/AwesomeSalesforceSkills/releases --jq 'length'
0
```

So the documented PyPI-only bootstrap cannot complete today. `pip install
sfskills-mcp` itself works fine — version 0.4.6 installs cleanly.

**Fix.** Use a repository checkout as the data root instead.

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap.py
export SFSKILLS_REPO_ROOT="$PWD"
```

Then point your MCP client at that path. Full client configuration in
[../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md); the
maintainer runbook for actually cutting the release is
[installing.md §6](installing.md#6-cutting-a-github-release-maintainer-only).

**Gotcha while diagnosing this.** If the cache directory is already populated
from an earlier successful run, the bootstrap short-circuits and prints `cache
already populated` with exit 0, hiding the 404. Reproduce the real first-run
behaviour with a clean cache:

```bash
sfskills-mcp-init --cache-dir /tmp/clean-cache
```

---

## MCP server cannot find the data root (`RepoRootNotFoundError`)

**Symptom.** The server exits at startup, or every tool errors, with
`RepoRootNotFoundError` and a message listing the ways to set a root.

**Cause.** `mcp/sfskills-mcp/src/sfskills_mcp/paths.py` resolves the data root
from `SFSKILLS_REPO_ROOT` first, then falls back to autodetection and the
`sfskills-mcp-init` cache. Under an MCP client the server runs as a detached
subprocess that does not inherit your shell environment, so an `export` in your
terminal does not reach it. The same error appears if `SFSKILLS_REPO_ROOT` is
set but points at a path that does not exist or is not a checkout.

**Fix.** Set the variable in the client's own config block, as an absolute
path, not in your shell profile:

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- python3 -m sfskills_mcp
```

Verify with the server's own health tool:

```bash
SFSKILLS_REPO_ROOT="$PWD" python3 -c "
import sys, json
sys.path.insert(0, 'mcp/sfskills-mcp/src')
from sfskills_mcp import meta
print(json.dumps(meta.health(), indent=2))
"
```

`repo_root` must be your checkout, `registry.skill_count` must be non-zero, and
`lexical_index.byte_size` must be present. If `skill_count` is 0 or the lexical
index block is missing, the root resolved but the index was never built — go
back to `python3 scripts/bootstrap.py`.

---

## `--help` starts a rebuild instead of printing usage

**Symptom.** You append `--help` to `scripts/build_index.py` expecting usage
text. Instead a full index rebuild begins. The same happens with
`scripts/install_local_commands.py`, which performs the install.

**Cause.** Neither script uses `argparse`; both have a bare `main()` that
ignores `sys.argv` entirely. Grepping either file for `argparse` returns 0
hits. There is no flag parsing to intercept `--help`.

**Fix.** Read the module docstring instead — both files document their usage at
the top. Do not invoke `scripts/build_index.py` casually: it is the expensive
path and it dirties the working tree. The normal way to build or rebuild is
`python3 scripts/bootstrap.py`, which does have full `argparse` and a real
`--help`; `python3 scripts/skill_sync.py --all` also has one and is the right
tool after editing a skill. If you need to interrupt a rebuild you started by
accident, Ctrl-C is safe: the sync is re-runnable and the lexical index
rebuilds from scratch when its source hash does not match.

---

## The CLI and the MCP server disagree about the same query

**Symptom.** The same question returns a good skill through one surface and
`Coverage: NONE`, or a different top skill, through the other.

**Cause.** They are separate implementations.
`mcp/sfskills-mcp/src/sfskills_mcp/skills.py` never calls
`scripts/search_knowledge.py`; it imports `aggregate_skill_scores` and
`rerank_results` from `pipelines` and runs its own shorter pipeline. The
coverage rule used to differ and no longer does — both now gate on
`max_score >= min_skill_max_score or score >= min_skill_score` from
`config/retrieval-config.yaml`.

So if you see a disagreement today, it is one of these:

- **You are on a PyPI install, not a checkout.** The wheel ships no
  `vector_index/skill_embeddings.jsonl`, so the MCP server cannot embed the
  query and scores lexical-only. A checkout with `fastembed` installed blends a
  vector term at weight 0.2. Different numbers, sometimes a different order.
- **The two are pointed at different data.** Check `SFSKILLS_REPO_ROOT` against
  the checkout you ran `bootstrap.py` in.
- **Your query has punctuation.** See the next entry — the MCP path does not
  sanitise, and raises rather than disagreeing.
- **One of them was changed and the other was not.** The gate lives in two
  files by design. Run `python3 evals/measurement/check_cli_mcp_parity.py` (add
  `--heldout` for all 154 held-out queries) — it compares the gated skill list
  from both surfaces and names any query where they disagree. CI runs the
  `--heldout` form on every pull request.

**Fix.** When either surface denies coverage:

1. Look at the `Top chunks:` block anyway. If a plausible skill appears there
   with a score, the gate suppressed a real answer and you can open the skill
   directly.
2. Re-ask using the platform's own vocabulary. Symptom phrasing
   (`"three triggers on Account one fires twice"`) routes differently from
   jargon phrasing (`"trigger recursion"`), and the difference is large — it is
   the main reason mechanism-3 held-out Hit@1 sits at 40.9% while the curated
   fixtures, which paraphrase indexed `triggers:` text, sit at 98.4%
   (both measured 2026-08-14 with `evals/measurement/run_heldout.py`).
3. Fall back to the roster. `Coverage: NONE` from mechanism 3 is not evidence of
   a gap; open
   `.claude/skills/salesforce-<domain>/references/skill-index.md` and scan.

The thresholds are tuning, not architecture: they live in
`config/retrieval-config.yaml` and are read by both surfaces. Read the code
rather than trusting a documented verdict, including this one.

---

## A query containing `+`, `%`, `*` or a quote

**Symptom.** You expect `sqlite3.OperationalError: fts5: syntax error near "+"`
from a query like `100% test coverage` or `apex *ngFor`.

**Cause and current state.** FTS5 treats those characters as query operators.
This is already handled on the CLI: `_sanitize_query_for_fts5` in
`scripts/search_knowledge.py` strips the query down to alphanumerics and
hyphens before searching, which is a superset of what the tokeniser indexes
anyway, so retrieval quality on safe queries is unchanged.

**Fix.** None needed for the CLI. The MCP path does *not* sanitise — it passes
the query straight to `search_index` — and it does raise:

```text
skills.search_skill("100% test coverage")  -> OperationalError: fts5: syntax error near "%"
skills.search_skill("salesforce + slack")  -> OperationalError: fts5: syntax error near "+"
skills.search_skill("apex *ngFor")         -> has_coverage true (a trailing * is a valid prefix operator)
```

Strip punctuation client-side if you are building an integration against
`search_skill`.

---

## Search is slow, or appears to hang

**Symptom.** A query takes tens of seconds, or minutes.

**Cause.** This page previously documented a **13 s to 29 s** warm band as
normal, and it no longer is. Measured on this checkout on 2026-08-14, three
queries across five runs landed between **0.49 s and 0.72 s** with a peak
resident set of 392 MB. Commit `d8c95d5de` removed two loads that dominated the
old figure: `build_search_context` was calling `load_embeddings()`
unconditionally, ignoring `embeddings.enabled` and pulling in roughly 2 GB that
was then never read, and it materialised all of `chunks.jsonl` — about 856 MB
of dicts — so one consumer could read `official_source_ids`, a field only 30
chunks populate.

So a multi-second query today is a real symptom, not variance. Likely causes,
in order:

- **Something else is competing for I/O.** A concurrent
  `scripts/skill_sync.py` run, an index rebuild, or a backup will multiply the
  cost of the SQLite reads.
- **You are on a cold page cache**, immediately after a rebuild or a reboot.
- **`fastembed` is installed and cold.** The first call in a process pays a
  one-off model load of roughly 14 s; subsequent queries add about 50 ms.

**Fix.** Wait for the competing job, or use the MCP server, which reads only
`vector_index/lexical.sqlite` and `registry/skills.json` and answers in
milliseconds once the process is warm.

---

## `check_doc_counts.py` fails after someone adds an agent or a skill

**Symptom**

```text
ERROR CLAUDE.md: active_runtime is 47 in doc but canonical is 48 (pattern /Run-time agents \((\d+)\)/)
ERROR CLAUDE.md: runtime tiers sum to 47 (16+14+7+10) but active-runtime total is 48
```

The file names vary with whatever is stale. That exact pair came from a run
where `agents/omnistudio-designer/` had just been added, which also named
`AGENT_RULES.md` and `mcp/sfskills-mcp/README.md` for the same reason.

**Cause.** The lint derives every corpus-scale number from
`registry/skills.json` and the `class:` / `status:` frontmatter of each
`AGENT.md`, then asserts the docs quoting those numbers still agree. Adding an
agent directory changes the canonical value immediately, while the prose in
`README.md`, `CLAUDE.md`, `AGENT_RULES.md`,
`agents/_shared/RUNTIME_VS_BUILD.md` and the MCP README still says the old one.
The per-tier breakdowns are deliberately not auto-fixed, because only their sum
is machine-checkable.

**Fix.** Update every doc the error names, including the tier breakdown that
must sum to the new total, then re-run:

```bash
python3 scripts/check_doc_counts.py
```

A clean run prints one line beginning `Doc counts consistent:` and exits 0. On
2026-08-14 that line read `1027 skills, 48 active runtime + 14 build + 14
deprecated = 76 agents, 38 MCP tools`.

---

Still stuck? [faq.md](faq.md) covers the "is this supposed to work this way"
questions; [architecture.md](architecture.md) documents all three mechanisms in
enough detail to debug them, mechanism 1 first.
