# Troubleshooting

Symptom, cause, fix. Every entry below is a failure actually hit while walking
this repository's own documented paths on 2026-07-31 — not a list of things
that could theoretically go wrong.

---

## Search returns nothing, or prints `Coverage: NONE` with zero chunks

**Symptom**

```
$ python3 scripts/search_knowledge.py "trigger recursion"
Query: trigger recursion

Coverage: NONE — no skill meets the confidence threshold. Use official sources below.
Top skills:

Top chunks:
```

No chunks listed at all, and the exit code is 0.

**Cause.** There is no search index. `.gitignore` excludes
`vector_index/lexical.sqlite`, `vector_index/chunks.jsonl`,
`vector_index/embeddings.jsonl` and `vector_index/skill_embeddings.jsonl`
because they total about 832 MB, past GitHub's file-size limits. The lexical
helper returns an empty list rather than raising when the SQLite file is
absent — verified directly:

```
$ python3 -c "
from pipelines.lexical_index import search_index
from pathlib import Path
print(search_index(Path('/tmp/no-such-index.sqlite'), 'trigger recursion', None, 30))"
[]
```

So the whole pipeline runs, finds nothing, gates on nothing, and exits
successfully. It looks like an empty library.

**Fix**

```bash
python3 scripts/skill_sync.py --all
```

Then re-run the search. A working result names at least one skill under
`Top skills:` with a score.

Note the distinction: *zero chunks listed* means no index. *Chunks listed but
no skills* means the index is fine and the coverage gate suppressed the
result — a different problem, covered below.

---

## Slash commands do not exist after cloning

**Symptom.** `/consolidate-triggers` and every other command in `commands/`
are not offered by Claude Code, and `git ls-files .claude/commands` returns
nothing.

**Cause.** `.gitignore` contains `.claude/*`, negated only for
`.claude/workflows/`. The tracked command specs live in `commands/` at the
repository root, which Claude Code does not read. Nothing in the repository's
own quick-start mentions the copy step.

**Fix**

```bash
python3 scripts/install_local_commands.py
```

Expected output:

```
installed 66 commands to .claude/commands/  (added=0 updated=66 removed=0)
Note: Claude Code loads slash commands at session start. Restart your CLI for new commands to register.
```

The leading number is `len(src_names)` — a live count of `commands/*.md`, 66
on this checkout — not a constant, so compare it against
`ls commands/*.md | wc -l` rather than against the line above. On a first
install the counters read `added=66 updated=0`. Restart the CLI afterwards, as
the note says. Re-run the script after pulling new commands or after a command
is retired — it also deletes stale entries.

---

## `sfskills-mcp-init` fails with HTTP 404

**Symptom**

```
$ sfskills-mcp-init
sfskills-mcp-init: downloading https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
sfskills-mcp-init: HTTP 404 fetching https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
  Verify the release tag exists: https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases
```

Exit code 1.

**Cause.** The PyPI wheel deliberately ships without the corpus and expects to
fetch it from a GitHub Release asset named `sfskills-data.tar.gz`. No such
release has been published, so the documented PyPI-only bootstrap cannot
complete today. `pip install sfskills-mcp` itself works fine — version 0.4.6
installed cleanly into a scratch virtualenv.

**Fix.** Use a repository checkout as the data root instead.

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m pip install -r requirements.txt
python3 scripts/skill_sync.py --all
export SFSKILLS_REPO_ROOT="$PWD"
```

Then point your MCP client at that path. Full client configuration in
[../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md).

**Gotcha while diagnosing this.** If the cache directory is already populated
from an earlier successful run, the bootstrap short-circuits and prints
`cache already populated` with exit 0, hiding the 404. Reproduce the real
first-run behaviour with a clean cache:

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
subprocess that does not inherit your shell environment, so an `export` in
your terminal does not reach it. The same error appears if
`SFSKILLS_REPO_ROOT` is set but points at a path that does not exist or is not
a checkout.

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

`repo_root` must be your checkout, `registry.skill_count` must be non-zero,
and `lexical_index.byte_size` must be present. If `skill_count` is 0 or the
lexical index block is missing, the root resolved but the index was never
built — go back to `python3 scripts/skill_sync.py --all`.

---

## `--help` starts a rebuild instead of printing usage

**Symptom.** You append `--help` to `scripts/build_index.py` expecting usage
text. Instead a full index rebuild begins. The same happens with
`scripts/install_local_commands.py`, which performs the install.

**Cause.** Neither script uses `argparse`; both have a bare `main()` that
ignores `sys.argv` entirely. Grepping either file for `argparse` or
`add_argument` returns 0 hits. There is no flag parsing to intercept `--help`.

**Fix.** Read the module docstring instead — both files document their usage
at the top. Do not invoke `scripts/build_index.py` casually: it is the
expensive path, and the normal way to rebuild is
`python3 scripts/skill_sync.py --all`, which does have full `argparse` and a
real `--help`. If you need to interrupt a rebuild you started by accident,
Ctrl-C is safe; the sync is re-runnable and the lexical index rebuilds from
scratch when its source hash does not match.

---

## The CLI and the MCP server disagree about the same query

**Symptom.** The same question returns a good skill through one surface and
`Coverage: NONE` — or a different top skill — through the other.

**Cause.** They are separate implementations.
`mcp/sfskills-mcp/src/sfskills_mcp/skills.py` never calls
`scripts/search_knowledge.py`; it imports `aggregate_skill_scores` and
`rerank_results` from `pipelines` and runs its own shorter pipeline. The
coverage rule used to differ and no longer does — both now gate on
`max_score >= min_skill_max_score or score >= min_skill_score` from
`config/retrieval-config.yaml`. On a repository checkout they agreed on every
query tried on 2026-07-31, including the negative case
(`search_skill("xylophone")` → `has_coverage: false`, zero skills).

So if you see a disagreement today, it is one of these:

- **You are on a PyPI install, not a checkout.** The wheel ships no
  `vector_index/skill_embeddings.jsonl`, so the MCP server cannot embed the
  query and scores lexical-only. A checkout blends a vector term at weight
  0.2. Different numbers, sometimes a different order.
- **The two are pointed at different data.** Check `SFSKILLS_REPO_ROOT`
  against the checkout you ran `skill_sync.py` in.
- **Your query has punctuation.** See the next entry — the MCP path does not
  sanitise, and raises rather than disagreeing.
- **One of them was changed and the other was not.** The gate lives in two
  files by design and nothing in CI compares them; the MCP module's docstring
  names `evals/measurement/check_cli_mcp_parity.py` as the regression test and
  that file does not exist.

**Fix.** When either surface denies coverage:

1. Look at the `Top chunks:` block anyway. If a plausible skill appears there
   with a score, the gate suppressed a real answer and you can open the skill
   directly.
2. Re-ask using the platform's own vocabulary. Symptom phrasing
   (`"three triggers on Account one fires twice"`) routes differently from
   jargon phrasing (`"trigger recursion"`), and the difference is large.
3. Prefer the MCP server for iteration — same gate, two to three orders of
   magnitude faster.

The thresholds are tuning, not architecture: they live in
`config/retrieval-config.yaml` and are read by both surfaces. Both the gate
and the displayed score changed during 2026-07-31. Read the code rather than
trusting a documented verdict, including this one.

---

## A query containing `+`, `%`, `*` or a quote

**Symptom.** You expect `sqlite3.OperationalError: fts5: syntax error near "+"`
from a query like `100% test coverage` or `apex *ngFor`.

**Cause and current state.** FTS5 treats those characters as query operators.
This is already handled: `_sanitize_query_for_fts5` in
`scripts/search_knowledge.py` strips the query down to alphanumerics and
hyphens before searching, which is a superset of what the tokeniser indexes
anyway, so retrieval quality on safe queries is unchanged.

**Fix.** None needed for the CLI. The MCP path does *not* sanitise — it passes
the query straight to `search_index` — and it does raise. Verified on
2026-07-31:

```
skills.search_skill("100% test coverage")  -> OperationalError: fts5: syntax error near "%"
skills.search_skill("salesforce + slack")  -> OperationalError: fts5: syntax error near "+"
skills.search_skill("apex *ngFor")         -> has_coverage true (a trailing * is a valid prefix operator)
```

Strip punctuation client-side if you are building an integration against
`search_skill`.

---

## Search worked yesterday and is slow or hanging today

**Symptom.** A query that took about 13 s now takes half a minute, minutes, or
appears to hang.

**Cause.** Each invocation loads `vector_index/embeddings.jsonl` (535.0 MB)
and `vector_index/chunks.jsonl` (126.2 MB) from disk. Anything else competing
for I/O — a concurrent `scripts/skill_sync.py` run, a rebuild of the index, a
backup — multiplies that cost. On this machine on 2026-07-31 the same three
queries measured anywhere in a **13 s to 29 s** band warm, 52 s to 90 s on a
cold page cache, and 83.08 s for one run alongside an index rebuild. Treat
anything inside the warm band as normal variance, not a fault.

**Fix.** Wait for the competing job, or use the MCP server, which reads only
`vector_index/lexical.sqlite` and `registry/skills.json` and measured 0.01 s
to 0.79 s per query in a warm process (the high end is the first call, which
also loads the skill vectors).

---

## `check_doc_counts.py` fails after someone adds an agent or a skill

**Symptom**

```
ERROR CLAUDE.md: active_runtime is 47 in doc but canonical is 48 (pattern /Run-time agents \((\d+)\)/)
ERROR CLAUDE.md: runtime tiers sum to 47 (16+14+7+10) but active-runtime total is 48
```

The file names vary with whatever is stale. That exact pair came from a run on
2026-07-31, which also named `AGENT_RULES.md` and `mcp/sfskills-mcp/README.md`
for the same reason: `agents/omnistudio-designer/` had just been added.

**Cause.** The lint derives every corpus-scale number from
`registry/skills.json` and the `class:` / `status:` frontmatter of each
`AGENT.md`, then asserts the docs quoting those numbers still agree. Adding an
agent directory changes the canonical value immediately, while the prose in
`README.md`, `CLAUDE.md`, `AGENT_RULES.md`, `agents/_shared/RUNTIME_VS_BUILD.md`
and the MCP README still says the old one. The per-tier breakdowns are
deliberately not auto-fixed, because only their sum is machine-checkable.

**Fix.** Update every doc the error names, including the tier breakdown that
must sum to the new total, then re-run:

```bash
python3 scripts/check_doc_counts.py
```

A clean run prints one line beginning `Doc counts consistent:` and exits 0.

---

Still stuck? [faq.md](faq.md) covers the "is this supposed to work this way"
questions; [architecture.md](architecture.md) explains the retrieval pipeline
in enough detail to debug it.
