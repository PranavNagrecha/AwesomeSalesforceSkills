# Troubleshooting

Symptom, cause, fix. Every entry below is a failure actually hit while walking
this repository's own documented paths. Everything was re-executed on
2026-08-15 (macOS 26.5, Apple silicon, Python 3.14.4, Claude Code 2.1.209);
entries whose numbers move are dated where the measurement matters.

The first three entries are failures of the path that ships — the model-driven
roster scan, which needs no index and is what a clone or plugin install
exercises. Everything after them is either the install itself or the
keyword-search layer, which only exists after you run
`python3 scripts/bootstrap.py`.

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
the designed trade: it works with zero setup, and it has no arithmetic to refuse
with.

Two upstream causes account for most of it. Domain overlap is the first: a
callout is Apex *and* integration, a sharing question is admin *and* security,
and the pick happens at the router before any roster is opened. Near-duplicate
packages are the second: the corpus contains genuine confusable pairs, and which
of the two is "correct" is sometimes a judgement call.

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
   plain markdown at `.claude/skills/salesforce-<domain>/references/skill-index.md`,
   one per domain. Across the eleven they carry exactly 1,027 gloss entries —
   one per skill package — spread over rather more lines than that, because each
   file also has a heading and blank lines:

   ```bash
   grep -c '^- ' .claude/skills/*/references/skill-index.md | \
     awk -F: '{s+=$2} END {print s" gloss entries"}'      # 1027 gloss entries
   ```

4. **Get a second opinion from search**, if you have run bootstrap:

   ```bash
   python3 scripts/search_knowledge.py "<your question in your own words>"
   ```

   It ranks by a completely different signal, so a disagreement is informative.

**What not to do.** Do not conclude the library lacks the topic. See the next
entry.

**If it keeps happening for one package**, the fix is upstream of the router. A
skill's `description:` frontmatter becomes its gloss by way of
`registry/skills.json`, so a package that is routinely missed usually has a
description that does not carry the phrasings people type. Editing a description
is editing routing behaviour; rerun `python3 scripts/skill_sync.py --skill
skills/<domain>/<slug>` and `python3 scripts/build_plugin.py` afterwards.

---

## Claude says the topic is not covered

**Symptom.** "There is no skill for X in this library" — for an X that the corpus
plainly ought to cover.

**Cause.** Almost always the same one as above: the model scanned a roster, did
not recognise the topic under the vocabulary the glosses use, and generalised
from "I did not spot it" to "it does not exist". Occasionally the search CLI
reported `Coverage: NONE` because no index was built and the model took that at
face value.

Every domain router carries a standing rule against exactly this. Verbatim from
`.claude/skills/salesforce-apex/SKILL.md`, under `## Rules`:

> 3. Never claim a topic is uncovered without pasting lookup output.

The routers also invert the fallback direction on purpose. From the same file:

> If the command errors or reports `Coverage: NONE`, fall back to
> mechanism 1 rather than telling the user the topic is uncovered.

The roster is the floor, not the ceiling.

**Fix.** Ask for the evidence, then check it yourself:

```bash
grep -ril '<topic>' .claude/skills/*/references/skill-index.md
ls skills/*/ | grep -i '<topic>'
```

If both come back empty, it is a genuine gap — [../CONTRIBUTING.md](../CONTRIBUTING.md)
covers reporting one.

---

## `pip install -r requirements.txt` fails: externally-managed-environment

**Symptom**

```text
$ python3 -m pip install -r requirements.txt
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.
$ echo $?
1
```

**Cause.** [PEP 668](https://peps.python.org/pep-0668/). Homebrew Python on
macOS and the system Python on Debian/Ubuntu both mark themselves
externally managed and refuse system-wide `pip install`. Nothing about this
repository triggers it — it is the default state of the most common macOS
Python.

**Fix.** A virtual environment.

```bash
git check-ignore -q .venv || echo '.venv/' >> .git/info/exclude
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/bootstrap.py
```

The first line matters: `.gitignore` covers `.qa-venv/`, `.build-venv/`,
`.smoke-venv/` and `.verify-venv/` but **not** `.venv/`, so an unexcluded venv
shows up as thousands of untracked files. `.git/info/exclude` is per-clone and
never committed.

Everything else in the docs that says `python3` means "the interpreter you
installed the requirements into". Do not reach for `--break-system-packages`;
it can break the Homebrew installation, which the error message says outright.

---

## Slash commands do not exist after cloning

**Symptom.** `/consolidate-triggers` and every other command in `commands/` are
not offered by Claude Code, and `git ls-files .claude/commands` returns nothing.

**Cause.** `.gitignore:131` contains `.claude/*`, negated on lines 132–134 only
for `.claude/agents/`, `.claude/skills/` and `.claude/workflows/`. The tracked
command specs live in `commands/` at the repository root, which Claude Code does
not read. Tracking both copies would create a permanent drift surface between
two copies of the same file, which is why the generated copy is deliberately not
committed.

Note that this affects *only* the slash commands. The routers and agent loaders
under `.claude/skills/` and `.claude/agents/` **are** tracked, so a clone can
still reach every skill package without this step.

**Fix**

```bash
python3 scripts/bootstrap.py          # installs commands and builds the index
python3 scripts/install_local_commands.py   # commands only
```

```text
$ python3 scripts/install_local_commands.py
installed 67 commands to .claude/commands/  (added=67 updated=0 removed=0)
Note: Claude Code loads slash commands at session start. Restart your CLI for new commands to register.
```

The leading number is `len(src_names)` — a live count of `commands/*.md`, **67**
on this checkout — not a constant, so compare it against `ls commands/*.md | wc
-l` rather than against any number written in a doc. On a first install the
counters read `added=67 updated=0`; on a re-run they read `added=0 updated=67`,
because the installer rewrites unconditionally. Restart the CLI afterwards;
Claude Code loads slash commands at session start. Re-run the script after
pulling new commands or after one is retired — it also deletes stale entries.

`.claude/commands/` is byte-identical to `commands/` when it is current
(`cmp` clean on all 67 files), so there is nothing to reconcile by hand.

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
gitignored because it totals 310 MB after a build: `chunks.jsonl` at 134 MB and
`lexical.sqlite` at 177 MB.

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

About 9 s cold on the reference machine, 7 s warm. Then re-run the search: a
working result names at least one skill under `Top skills:` with a score.

Use `bootstrap.py` rather than `scripts/build_index.py`. Both reach a working
index; bootstrap also installs the slash commands, has a real `--help` and
`--verify-only`, and never invokes an encoder. `build_index.py` has no argument
parsing at all, and what it does to your working tree depends on whether an
embedding backend is installed:

```text
$ ./.venv/bin/python scripts/build_index.py      # no fastembed installed
[embed] WARNING: fastembed package is not installed but config has backend=fastembed. …
Index build complete. Files touched: 0
$ git status --porcelain | grep -v '^??' | wc -l
       0
```

With an encoder available it instead rewrites `vector_embedding` across all
1,027 `registry/skills/*.json` records plus `registry/skills.json` and
`vector_index/manifest.json` — **1,029 modified tracked files** — and with the
real `fastembed` backend it encodes every chunk first, which is hours rather
than seconds. Earlier revisions of this page asserted the 1,029-file outcome for
"a fresh clone with no embedding backend installed", which is exactly the case
where the count is zero.

To check the index rather than infer it, run `python3 scripts/bootstrap.py
--verify-only`. Unlike `search_knowledge.py` it exits non-zero and says which
assertion failed:

```text
$ python3 scripts/bootstrap.py --verify-only
[   0.3s] phase 6/6  verifying retrieval
[   0.3s]           FAIL  vector_index/lexical.sqlite is missing

BOOTSTRAP FAILED: index not built — run: python3 scripts/bootstrap.py
$ echo $?
1
```

**The distinction that matters here.** *Zero chunks listed* means no index.
*Chunks listed but no skills* means the index is fine and the coverage gate
suppressed the result — a different problem, covered below.

---

## `sfskills-mcp-init` fails with HTTP 404

**Symptom**

```text
$ sfskills-mcp-init --cache-dir /tmp/clean-cache
sfskills-mcp-init: downloading https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
sfskills-mcp-init: HTTP 404 fetching https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
  Verify the release tag exists: https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases
$ echo $?
1
```

**Cause.** The PyPI wheel deliberately ships without the corpus and expects to
fetch it from a GitHub Release asset named `sfskills-data.tar.gz`. No such
release has been published — re-checked 2026-08-15:

```text
$ gh api repos/PranavNagrecha/AwesomeSalesforceSkills/releases --jq 'length'
0
```

**A second failure hides behind the first.** `pip install sfskills-mcp` installs
but does not import, because the published 0.4.6 wheel declared an unbounded
`mcp>=1.4.0` floor and pip now resolves `mcp 2.0.0`:

```text
$ pip install sfskills-mcp
Successfully installed … mcp-2.0.0 … sfskills-mcp-0.4.6 …
$ python -c "import sfskills_mcp.server"
  File ".../sfskills_mcp/server.py", line 64, in <module>
    from mcp.server.fastmcp import Context, FastMCP
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
$ pip install 'mcp>=1.7.0,<2.0'
Successfully installed … mcp-1.29.0 …
$ python -c "import sfskills_mcp.server; print('import OK')"
import OK
```

That wheel is also stale: it installs as 0.4.6 and reports
`sfskills_mcp.__version__ == 0.4.4`. In-tree the package is at 0.4.7, so the fix
is published-side.

**Fix.** Use a repository checkout as the data root instead.

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/bootstrap.py
./.venv/bin/python -m pip install -e mcp/sfskills-mcp
```

Then point your MCP client at that path. Full client configuration in
[../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md); the
maintainer runbook for actually cutting the release is
[installing.md §6](installing.md#6-cutting-a-github-release-maintainer-only).

**Gotcha while diagnosing this.** If the cache directory is already populated
from an earlier successful run, the bootstrap short-circuits with `cache already
populated` and exit 0, hiding the 404. Reproduce the real first-run behaviour
with a clean cache — `--cache-dir` is a real flag, as is `--force`:

```bash
sfskills-mcp-init --cache-dir /tmp/clean-cache
```

---

## MCP server added successfully but never connects

**Symptom.** `claude mcp add` reports success, and `claude mcp list` reports
`✘ Failed to connect`.

```text
$ claude mcp add sfskills --env SFSKILLS_REPO_ROOT=/abs/path -- python3 -m sfskills_mcp
Added stdio MCP server sfskills with command: python3 -m sfskills_mcp to local config
$ claude mcp list
sfskills: python3 -m sfskills_mcp - ✘ Failed to connect
```

**Cause.** `claude mcp add` stores the command string without ever running it.
Bare `python3` resolves to your system interpreter, which does not have the
package — the repository install lives in a virtualenv, because a system-wide
`pip install` is refused under PEP 668:

```text
$ python3 -c "import sfskills_mcp"
ModuleNotFoundError: No module named 'sfskills_mcp'
```

**Fix.** Register the venv's interpreter, by absolute path.

```text
$ claude mcp add sfskills \
    --env SFSKILLS_REPO_ROOT=/abs/path/to/AwesomeSalesforceSkills \
    -- /abs/path/to/AwesomeSalesforceSkills/.venv/bin/python -m sfskills_mcp
$ claude mcp list
sfskills: /…/.venv/bin/python -m sfskills_mcp - ✔ Connected
```

`claude mcp get sfskills` prints the stored command and environment, which is the
fastest way to see which interpreter you actually registered.

---

## MCP server cannot find the data root (`RepoRootNotFoundError`)

**Symptom.** The server exits at startup, or every tool errors, with
`RepoRootNotFoundError` and a message listing the ways to set a root.

**Cause.** `mcp/sfskills-mcp/src/sfskills_mcp/paths.py` resolves the data root
from `SFSKILLS_REPO_ROOT` first, then falls back to autodetection and the
`sfskills-mcp-init` cache. Under an MCP client the server runs as a detached
subprocess that does not inherit your shell environment, so an `export` in your
terminal does not reach it. The same error appears if `SFSKILLS_REPO_ROOT` is set
but points at a path that does not exist or is not a checkout.

**Fix.** Set the variable in the client's own config block, as an absolute path,
not in your shell profile — the `--env` flag in the entry above does exactly
that.

Verify with the server's own health tool:

```bash
SFSKILLS_REPO_ROOT="$PWD" ./.venv/bin/python -c "
import sys, json
sys.path.insert(0, 'mcp/sfskills-mcp/src')
from sfskills_mcp import meta
print(json.dumps(meta.health(), indent=2))
"
```

A healthy response, measured on a clone that had been bootstrapped:

```json
{
  "server_version": "0.4.7",
  "mcp_sdk_version": "1.29.0",
  "repo_root": "/abs/path/to/AwesomeSalesforceSkills",
  "registry": { "path": "registry/skills.json", "skill_count": 1027, "built_at": "…" },
  "lexical_index": { "path": "vector_index/lexical.sqlite", "byte_size": 176865280, "built_at": "…" },
  "agents": { "runtime": 48, "build": 14, "deprecated": 14, "unknown": 0, "total": 76 }
}
```

`repo_root` must be your checkout, `registry.skill_count` must be non-zero, and
`lexical_index.byte_size` must be present. If `skill_count` is 0 or the lexical
index block is missing, the root resolved but the index was never built — go back
to `python3 scripts/bootstrap.py`.

---

## `--help` starts a rebuild instead of printing usage

**Symptom.** You append `--help` to `scripts/build_index.py` expecting usage
text. Instead a full index rebuild begins. The same happens with
`scripts/install_local_commands.py`, which performs the install:

```text
$ python3 scripts/install_local_commands.py --help
installed 67 commands to .claude/commands/  (added=0 updated=67 removed=0)
```

**Cause.** Neither script uses `argparse`; both have a bare `main()` that ignores
`sys.argv` entirely. `grep -c argparse scripts/build_index.py
scripts/install_local_commands.py` returns 0 for both. There is no flag parsing
to intercept `--help`.

**Fix.** Read the module docstring instead — both files document their usage at
the top. The normal way to build or rebuild is `python3 scripts/bootstrap.py`,
which does have full `argparse` and a real `--help`; `python3
scripts/skill_sync.py --all` also has one and is the right tool after editing a
skill. Add `--skip-embeddings` there unless you specifically want vectors
rebuilt: `--all --skip-embeddings` measured 7.8 s on a fresh clone, while the
plain form re-encodes.

If you need to interrupt a rebuild you started by accident, Ctrl-C is safe: the
sync is re-runnable and the lexical index rebuilds from scratch when its source
hash does not match.

---

## The CLI and the MCP server disagree about the same query

**Symptom.** The same question returns a good skill through one surface and
`Coverage: NONE`, or a different top skill, through the other.

**Cause.** They are separate implementations.
`mcp/sfskills-mcp/src/sfskills_mcp/skills.py` never calls
`scripts/search_knowledge.py`; it imports `aggregate_skill_scores` and
`rerank_results` from `pipelines` and runs its own shorter pipeline. The coverage
rule used to differ and no longer does — both now gate on
`max_score >= min_skill_max_score or score >= min_skill_score` from
`config/retrieval-config.yaml` (1.0 and 1.5 respectively today).

So if you see a disagreement, it is one of these:

- **You are on a PyPI install, not a checkout.** The wheel ships no
  `vector_index/skill_embeddings.jsonl`, so the MCP server cannot embed the query
  and scores lexical-only. A checkout with `fastembed` installed blends a vector
  term at weight 0.2. Different numbers, sometimes a different order.
- **The two are pointed at different data.** Check `SFSKILLS_REPO_ROOT` against
  the checkout you ran `bootstrap.py` in.
- **One of them was changed and the other was not.** The gate lives in two files
  by design. Run `python3 evals/measurement/check_cli_mcp_parity.py` — it
  compares the gated skill list from both surfaces and names any query where they
  disagree. Add `--heldout` for all 154 held-out queries; CI runs that form on
  every pull request (`.github/workflows/tests.yml:131`).

  ```text
  $ python3 evals/measurement/check_cli_mcp_parity.py
  CLI/MCP retrieval parity: 15/15 queries agree
  OK: both surfaces return the same gated skill list for every query.
  ```

**Fix.** When either surface denies coverage:

1. Look at the `Top chunks:` block anyway. If a plausible skill appears there
   with a score, the gate suppressed a real answer and you can open the skill
   directly.
2. Re-ask using the platform's own vocabulary. Symptom phrasing
   (`"three triggers on Account one fires twice"`) routes differently from jargon
   phrasing (`"trigger recursion"`), and the difference is large — it is the main
   reason mechanism-3 held-out Hit@1 sits at 40.3% while the curated fixtures,
   which paraphrase indexed `triggers:` text, sit at 98.4%. Both measured
   2026-08-15 with `evals/measurement/run_heldout.py`; the fixture run adds
   `--queries vector_index/query-fixtures.json --use-domain`.
3. Fall back to the roster. `Coverage: NONE` from mechanism 3 is not evidence of
   a gap; open `.claude/skills/salesforce-<domain>/references/skill-index.md` and
   scan.

The thresholds are tuning, not architecture: they live in
`config/retrieval-config.yaml` and are read by both surfaces. Read the code
rather than trusting a documented verdict, including this one.

---

## A query containing `+`, `%`, `*` or a quote

**Symptom.** You expect `sqlite3.OperationalError: fts5: syntax error near "+"`
from a query like `100% test coverage` or `apex *ngFor`.

**Current state: this no longer happens on either surface.** Sanitisation moved
into `pipelines/lexical_index.search_index`, which calls `tokenize_query` before
touching FTS5; that helper replaces every non-bareword character with a space
and rebuilds the query as `token* OR token*`. The CLI's own
`_sanitize_query_for_fts5` in `scripts/search_knowledge.py` is now a second layer
rather than the only one, so the MCP path is covered too. Measured 2026-08-15:

```text
$ python3 -c "…; from sfskills_mcp import skills; …"
'100% test coverage'           -> has_coverage=True n_skills=2
'salesforce + slack'           -> has_coverage=True n_skills=1
'apex *ngFor'                  -> has_coverage=True n_skills=1
'trigger recursion'            -> has_coverage=True n_skills=1

$ python3 scripts/search_knowledge.py "100% test coverage"
Query: 100% test coverage

Top skills:
- agentforce/agent-testing-and-evaluation (1.933)
- devops/continuous-integration-testing (1.033)
```

Earlier revisions of this page said the MCP path raises. If you are on an older
`sfskills-mcp` and do see an `OperationalError`, strip punctuation client-side
and upgrade.

---

## Search is slow, or appears to hang

**Symptom.** A query takes tens of seconds, or minutes.

**Cause.** This page previously documented a **13 s to 29 s** warm band as
normal, and it no longer is. Measured 2026-08-15 with `/usr/bin/time -l` on a
checkout carrying `skill_embeddings.jsonl` and `fastembed` 0.8.0:

| query | wall clock | peak RSS |
|---|---:|---:|
| `trigger recursion` | 0.62 s | 373 MB |
| `how do I stop a flow from hitting SOQL limits` | 0.84 s | 371 MB |
| `permission set groups` | 0.56 s | 377 MB |

On a plain lexical-only clone the same first query answered in 0.15 s. Commit
`d8c95d5de` removed two loads that dominated the old figure:
`build_search_context` was calling `load_embeddings()` unconditionally, ignoring
`embeddings.enabled` and pulling in roughly 2 GB that was then never read, and it
materialised all of `chunks.jsonl` so one consumer could read
`official_source_ids`, a field only 30 chunks populate.

So a multi-second query today is a real symptom, not variance. Likely causes, in
order:

- **Something else is competing for I/O.** A concurrent `scripts/skill_sync.py`
  run, an index rebuild, or a backup will multiply the cost of the SQLite reads.
- **You are on a cold page cache**, immediately after a rebuild or a reboot.
- **`fastembed` is installed and cold.** The first call in a process pays a
  one-off model load of roughly 14 s; subsequent queries add about 50 ms.
- **You built `vector_index/embeddings.jsonl`.** The chunk-level file is loaded
  in full whenever `embeddings.enabled` is true. It is not built by any default
  path; if it exists, you asked for it.

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

The file names vary with whatever is stale. That exact pair came from a run where
`agents/omnistudio-designer/` had just been added, which also named
`AGENT_RULES.md` and `mcp/sfskills-mcp/README.md` for the same reason.

**Cause.** The lint derives every corpus-scale number from `registry/skills.json`
and the `class:` / `status:` frontmatter of each `AGENT.md`, then asserts the docs
quoting those numbers still agree. Adding an agent directory changes the
canonical value immediately, while the prose in `README.md`, `CLAUDE.md`,
`AGENT_RULES.md`, `agents/_shared/RUNTIME_VS_BUILD.md` and the MCP README still
says the old one. The per-tier breakdowns are deliberately not auto-fixed,
because only their sum is machine-checkable.

**Fix.** Update every doc the error names, including the tier breakdown that must
sum to the new total, then re-run:

```bash
python3 scripts/check_doc_counts.py
```

A clean run prints one line beginning `Doc counts consistent:` and exits 0. On
2026-08-15 that line read:

```text
Doc counts consistent: 1027 skills, 48 active runtime + 14 build + 14 deprecated = 76 agents, 38 MCP tools.
```

---

Still stuck? [faq.md](faq.md) covers the "is this supposed to work this way"
questions; [architecture.md](architecture.md) documents all three mechanisms in
enough detail to debug them, mechanism 1 first. Plugin-specific failures live in
[installing-the-plugin.md](installing-the-plugin.md#known-limitations).
