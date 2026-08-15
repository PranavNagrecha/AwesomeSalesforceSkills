# Installing SfSkills

Canonical setup reference for a fresh clone.

**What works with no setup at all.** A clone carries `CLAUDE.md`, the 12 router
skills under `.claude/skills/` (a top-level `salesforce` router plus 11 domain
routers), their 11 rosters, and the 48 run-time agent loaders under
`.claude/agents/`. Open the directory in Claude Code and ask a Salesforce
question: the model reads the router descriptions, hands off to one domain
router, opens that router's `references/skill-index.md` — the roster of that
domain's packages, one 220-character gloss each — and opens the one it picks.

There are **eleven** rosters, not one, and Claude reads **one** of them: an Apex
question costs the apex roster's 158 glosses, never the corpus's 1,027. No index
is involved anywhere in that path, which is why every router says the shipped
rosters work with no setup.

**What bootstrap adds.** Three generated artefacts are deliberately not
committed, and one command builds them:

| Not committed | Unlocks |
|---|---|
| `vector_index/chunks.jsonl` | `scripts/search_knowledge.py`, the MCP `search_skill` tool, and the build-time agents that maintain the library |
| `vector_index/lexical.sqlite` | same — this is the FTS5 index search reads |
| `.claude/commands/` | the 67 slash commands inside Claude Code |

So bootstrap is required for the *search* and *slash-command* surfaces, not for
the library to be reachable. Skipping it degrades library maintenance work and
the CLI; it does not stop Claude from finding and reading a skill package.

One consequence worth stating up front, because two of this repo's own docs got
it wrong: **accuracy figures for search are not accuracy figures for the
library.** Every number on this page that carries a Hit@1 or Hit@3 measures the
keyword-search path, which most users never build. The routing path is measured
separately and is documented in
[architecture.md](architecture.md#how-this-path-is-measured-and-one-retraction).

- New user, want search and slash commands: [1. One command](#1-one-command).
- Wiring an AI client to the MCP server: [5. MCP install paths](#5-mcp-install-paths).
- Repository owner cutting a release: [6. Cutting a GitHub release](#6-cutting-a-github-release-maintainer-only).

---

## 1. One command

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap.py
```

Real transcript of the first run on a `git clone --depth 1`, captured
2026-08-01:

```text
$ python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
$ python3 scripts/bootstrap.py
[   0.0s] phase 1/6  preflight
[   0.0s]           repo root       /.../qa/fresh
[   0.0s]           interpreter     /.../qa/fresh/.venv/bin/python
[   0.0s]           python          3.14.4
[   0.3s]           fastembed       not installed (lexical-only retrieval — this is the default)
[   0.3s]           OK  required dependencies present (PyYAML, jsonschema)
[   0.3s] phase 2/6  scanning skill packages -> retrieval chunks (~5-35 s)
[   3.3s]           ... still scanning skills/ and knowledge/  [chunks.jsonl not yet written, lexical.sqlite not yet written]
[   5.9s]           130151 chunks built from 1027 skill packages
[   5.9s] phase 3/6  verifying chunk hash against the committed manifest
[   5.9s]           OK  chunks_hash=511de071cf01... matches the committed manifest
[   5.9s] phase 4/6  writing vector_index/ (chunks.jsonl + lexical.sqlite) — all gitignored
[   8.0s]           chunks.jsonl   126 MB
[   8.0s]           lexical.sqlite 166 MB
[   8.0s] phase 5/6  installing slash commands -> .claude/commands/
[   8.0s]           installed 66 commands to .claude/commands/  (added=66 updated=0 removed=0)
[   8.0s]           Note: Claude Code loads slash commands at session start. Restart your CLI for new commands to register.
[   8.0s] phase 6/6  verifying retrieval
[   8.6s]           OK  'trigger recursion' -> apex/recursive-trigger-prevention
[   8.6s]           OK  66 slash commands installed in .claude/commands/

Bootstrap complete in 9s.
```

That transcript is verbatim from 2026-08-01 and two of its counts have since
moved. `commands/` holds **67** specs today (`commands/add-skill.md` was added),
so phases 5 and 6 print 67; and the corpus now chunks to **132,743** rather than
130,151 (`vector_index/manifest.json`, key `chunk_count`). Both numbers are live
counts, never constants — compare them against `ls commands/*.md | wc -l` and
against the manifest rather than against any figure written into a doc.

**Those timings are one machine's, not a guarantee.** Measured on macOS 26.5,
Apple silicon (arm64): **9 s** for a cold run with both artefacts deleted
(3 runs, all 9 s) and **7-8 s** for a re-run (10 runs) — a re-run is faster
because `build_lexical_index` short-circuits when the chunk hash is unchanged.
Python 3.12 completed the same cold build in 9 s; both 3.12 and 3.14 are
verified working. A slower disk will be longer, and the phase-2 banner quotes a
deliberately conservative `~5-35 s`. The progress lines exist so that a longer
run is still obviously working rather than hung — nothing is silent for more
than 3 seconds (except under `--quiet`, which suppresses them by request).

Then confirm it yourself:

```bash
python3 scripts/search_knowledge.py "trigger recursion"
```

The only entry under `Top skills:` should be `apex/recursive-trigger-prevention`.
The number beside it is a ranking output and moves whenever the ranker is
retuned — assert the skill id, never the score. Measured on this checkout on
2026-08-14, that query answers in **0.49 s**; five runs across three queries
landed between 0.49 s and 0.72 s. If yours takes tens of seconds, see
[troubleshooting.md](troubleshooting.md#search-is-slow-or-appears-to-hang).

### Flags

| Flag | Effect |
|---|---|
| *(none)* | Build the lexical index, install slash commands, verify. The normal path. |
| `--with-embeddings` | Also encode semantic embeddings. Requires `fastembed` to be installed and `embeddings.enabled: true` in `config/retrieval-config.yaml` — see [section 4](#4-embeddings-configured-on-inert-until-you-install-fastembed). |
| `--skip-commands` | Do not write `.claude/commands/`. For non-Claude-Code users. |
| `--verify-only` | Build nothing; just check that the index answers a known-good query. Exits 1 if the index is missing. |
| `--quiet` | Suppress progress lines. Failures and the final result still print. |

Exit codes: `0` success, `1` verification failed, `2` refused to start — wrong
Python, a missing dependency, or `--with-embeddings` against a config that
disables embeddings ([section 4](#--with-embeddings-cannot-turn-embeddings-on-by-itself)).

---

## 2. What bootstrap does — and what it refuses to do

| Phase | Does |
|---|---|
| 1. preflight | Checks Python ≥ 3.10 and that PyYAML + jsonschema import. Prints the resolved repo root, the interpreter path, and whether `fastembed` is available. Exits 2 with the exact remediation command if anything is missing. |
| 2. chunks | `pipelines.sync_engine.build_state(root, skip_embeddings=True)` — scans 1,027 skill packages into ~133k retrieval chunks, in-process. |
| 3. integrity | Compares the freshly computed `chunks_hash` against the committed `vector_index/manifest.json`. A mismatch prints a WARNING naming both hashes and continues — it is the expected result when you have local skill edits. |
| 4. write | Writes `vector_index/chunks.jsonl` and `vector_index/lexical.sqlite`. Both are gitignored. Nothing else is written. |
| 5. commands | Runs `scripts/install_local_commands.py`, copying `commands/*.md` into `.claude/commands/`. |
| 6. verify | Runs `trigger recursion` through the real search path and asserts `has_coverage` is true and the top skill is `apex/recursive-trigger-prevention`. Also asserts the installed slash-command count equals the source count. Any failure exits 1 naming the assertion. |

It never:

- installs a package (it prints the command and exits 2 instead);
- writes to git — no staging, no commits, no index or branch mutation;
- touches the network;
- writes under `skills/`, `registry/`, `agents/`, `commands/`, `docs/`, or
  `standards/`;
- calls `scripts/skill_sync.py` or `scripts/build_index.py`.

**`git status` is clean when it finishes.** That is a deliberate design
constraint, not a nicety. `scripts/build_index.py` reaches the same retrieval
outcome by calling `pipelines.sync_engine.write_state`, which rewrites every
registry record — on a fresh clone with no embedding backend installed it nulls
`vector_embedding` across all 1,027 records and zeroes `embedding_count` in
`vector_index/manifest.json`, leaving **1,029 modified tracked files** that a
new contributor then has to recognise as noise and discard. Bootstrap sidesteps
that by never calling `write_state`; it writes only the two gitignored
artefacts. Verified after a bootstrap run on a fresh clone:

```text
$ git status --porcelain | grep -v '^?? .venv' | wc -l
       0
```

---

## 3. What a fresh clone contains — and what it does not

Measured on `git clone --depth 1` (2026-08-01): **130 MB** working tree,
of which **29 MB** is `.git`.

**Not in the clone (bootstrap builds these):**

| Path | Size | Why not committed |
|---|---:|---|
| `vector_index/lexical.sqlite` | 165 MB | Past GitHub's file-size limits; a binary that changes wholesale on every rebuild. |
| `vector_index/chunks.jsonl` | 124 MB | Same — 132,743 lines regenerated from `skills/`. |
| `vector_index/skill_embeddings.jsonl` | 5 MB | 1,027 vectors, one per skill. Written only when `fastembed` is installed; see [section 4](#4-embeddings-configured-on-inert-until-you-install-fastembed). |
| `.claude/commands/` | 67 files | Byte-for-byte copies of the tracked `commands/*.md`. Tracking both would create a permanent drift surface between two copies of the same file. |

`vector_index/embeddings.jsonl`, the chunk-level vector file that earlier
versions of this page listed at 535 MB, is **not built by the current
pipeline**. It is absent from this checkout and nothing loads it. Any cost
figure quoting it describes a configuration nobody is running.

Total on this checkout: **295 MB** (`du -sh vector_index/`).

**In the clone:**

`vector_index/` ships only `manifest.json` (the integrity hashes),
`query-fixtures.json` and `query-variants.json` (the retrieval test fixtures).
Note that the committed `manifest.json` describes artefacts that are *not* in
the clone — it reports a chunk count and an embedding count for an index you
have not built yet. It is an integrity baseline for bootstrap phase 3, not a
statement about your working tree.

Under `.claude/`, three subtrees are tracked so a clone is plugin-usable:
`.claude/agents/` (48 run-time agent loaders), `.claude/skills/` (23 files —
12 router `SKILL.md` plus 11 `references/skill-index.md` rosters; the top-level
`salesforce` router has no roster because it hands off to the domain routers)
and `.claude/workflows/` (1). Everything else under `.claude/` is local session
state.

### The failure mode if you skip bootstrap

This is confined to the search surface. The router path in the header above
still works without an index; `search_knowledge.py` does not.

`search_knowledge.py` does not detect a missing index. It reports no coverage
and **exits 0**, which is indistinguishable from a library that has nothing on
the topic:

```text
$ python3 scripts/search_knowledge.py "trigger recursion"
Query: trigger recursion

Coverage: NONE — no skill meets the confidence threshold. Use official sources below.
Top skills:

Top chunks:
$ echo $?
0
```

If you see that for a query the library plainly ought to cover, you have not
built the index. Run `python3 scripts/bootstrap.py --verify-only` — unlike
`search_knowledge.py`, it exits non-zero and says so.

---

## 4. Embeddings: configured on, inert until you install fastembed

Three facts only make sense together, and this page has previously stated one
of them without the others:

1. `config/retrieval-config.yaml` sets `embeddings.enabled: true`. The config
   turns them **on**.
2. `fastembed` is commented out of `requirements.txt` (line 12). A plain
   `pip install -r requirements.txt` does **not** install it.
3. With no backend present, `pipelines/embedding_backends.py` logs a warning
   and falls back to lexical-only without crashing.

So the accurate statement is that embeddings are **configured on and inert
until you install `fastembed` yourself**. They are not "opt-in behind a flag" —
the config already enables them — and they are not "on by default" — the
dependency is not installed. Both earlier phrasings, including this section's
old title, were wrong.

`scripts/bootstrap.py` additionally passes `skip_embeddings=True` by default, so
the standard run stays deterministic and takes seconds even on a machine that
happens to have `fastembed` installed globally.

To use them:

```bash
python3 -m pip install 'fastembed>=0.4,<1.0'
python3 scripts/bootstrap.py --with-embeddings
```

### What you get, and what it costs

Skill-level vectors are what both search surfaces actually load:
`vector_index/skill_embeddings.jsonl`, 1,027 vectors at **about 5 MB**, built by
`python3 scripts/build_skill_embeddings.py`. Per-query overhead is roughly 50 ms
once the model is warm, after a one-off cold start of about 14 s.

The **535 MB and several hours** this section used to quote describes
`vector_index/embeddings.jsonl`, the chunk-level file. The current pipeline does
not build it, it is absent from this checkout, and `scripts/search_knowledge.py`
loads an empty mapping when it asks for it. Those figures are kept here only
because they are still accurate about a configuration you could construct:

| Source | Full chunk-level encode |
|---|---|
| `config/retrieval-config.yaml` (comment) | ~2 h 20 m on M-series CPU |
| `requirements.txt` (comment) | ~2-3 h on CPU |
| Measured 2026-08-01 | ~3 h 50 m (9.4 chunks/sec, strided 521-chunk sample through `BAAI/bge-small-en-v1.5`, machine already busy) |

If you build it, budget hours and run it overnight. Re-runs are far cheaper —
the content-hash cache in `pipelines/embedding_backends.py` re-encodes only
chunks whose text changed.

### Retrieval benefit — measured 2026-08-14

Over the 154 hand-written held-out queries, with
`python3 evals/measurement/run_heldout.py --json` versus `--no-embeddings`, on a
machine carrying `fastembed` 0.8.0:

| retrieval config | Hit@1 | Hit@3 | Coverage: NONE |
|---|---:|---:|---:|
| lexical-only | 39.6% | 48.1% | 0.0% |
| + `fastembed` skill vectors | **40.9%** | **53.9%** | 0.0% |

**+1.3pp Hit@1 and +5.8pp Hit@3.** Both rows measure the keyword-search path
only, not the routing path a clone or plugin user exercises.

This replaces the table that stood here before, which quoted 34.4%/42.2% →
35.7%/46.8% on the same held-out set and 95.5%/99.8% with "identical — 0.0pp"
on 400 curated fixtures, then concluded *"enable this only if you are actively
evaluating semantic retrieval"*. Two corrections. The held-out absolutes moved
because the index moved underneath them — note that
`config/retrieval-config.yaml` itself quotes a third pair, 36.4/44.2 → 37.0/48.7,
from the 2026-08-13 re-enable. Re-run `run_heldout.py` rather than copying any
of the three. And the 400 fixtures are close paraphrases of the `triggers:`
frontmatter that is itself indexed, so they measure the easy case and saturate
near the ceiling; a saturated benchmark cannot show a difference in either
direction, which is why "no difference at all" was the wrong conclusion to draw
from it.

The 0% `Coverage: NONE` rate is itself worth noting: a 2026-07-31 measurement
on realistic phrasings recorded 23.3%.

### `--with-embeddings` cannot turn embeddings on by itself

Whether embeddings are encoded at all is decided repository-wide by
`embeddings.enabled` in `config/retrieval-config.yaml`. Bootstrap never edits
that key. The flag only stops bootstrap from forcing `skip_embeddings=True`;
the encoder itself returns zero vectors whenever the config says
`enabled: false` (`pipelines/embedding_backends.py:103-104`). So the flag can
suppress the encode but never enable it, and `scripts/build_index.py` reads the
same key — check its current value rather than assuming either way.

So that the combination is not a silent no-op, bootstrap reads the config before
phase 2 and refuses when the key is `false` (an unreadable or absent config is
treated as unknown and the build proceeds):

```text
$ python3 scripts/bootstrap.py --with-embeddings
[   0.0s] phase 1/6  preflight
...
[   0.3s]           FAIL  --with-embeddings requested but config/retrieval-config.yaml has embeddings.enabled: false

BOOTSTRAP FAILED: embeddings are disabled repository-wide, so --with-embeddings would encode nothing.
Set embeddings.enabled: true in config/retrieval-config.yaml, or drop the flag.
```

**You will not see that failure on the current config**, which has
`embeddings.enabled: true` and has since 2026-05-09 (re-enabled 2026-08-13). The
transcript above is what the guard prints if someone flips the key back. The
condition you *are* likely to hit is the other one: the flag runs, the config
agrees, and `fastembed` is not installed — in which case phase 1 prints
`fastembed  not installed (lexical-only retrieval — this is the default)` and
the encode produces nothing. Install the package first.

---

## 5. MCP install paths

Full per-client wiring for 18 clients lives in
[`mcp/sfskills-mcp/docs/CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md). The
install decision is here.

### From a clone (recommended today)

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap.py
python3 -m pip install -e mcp/sfskills-mcp
```

Then set `SFSKILLS_REPO_ROOT` to the absolute path of that checkout in your
client's MCP config.

### From PyPI

```bash
pip install sfskills-mcp
sfskills-mcp-init          # currently exits 1 — see below
```

`pip install sfskills-mcp` works. `sfskills-mcp-init` does not: it fetches
`https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz`,
which returns HTTP 404 because no GitHub release has been published. Until one
is cut ([section 6](#6-cutting-a-github-release-maintainer-only)), use the
clone path above.

### The `mcp` SDK pin

`mcp/sfskills-mcp/pyproject.toml` declares `mcp>=1.7.0,<2.0`. Both bounds were
measured against published wheels on 2026-08-01:

| mcp version | `import sfskills_mcp.server` |
|---|---|
| 1.4.0, 1.5.0, 1.6.0 | `ImportError: cannot import name 'ToolAnnotations' from 'mcp.types'` |
| 1.7.0, 1.7.1, 1.8.0, 1.10.0, 1.29.0 | OK |
| 2.0.0 | `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` |

mcp 2.0.0 removed the `mcp.server.fastmcp` module that `server.py:64` imports
`Context` and `FastMCP` from. Lifting the ceiling means porting the server to
`mcp.server.mcpserver`, not bumping a number.

Releases up to and including `sfskills-mcp` 0.4.6 shipped an unbounded floor of
1.4.0, so any PyPI install made after mcp 2.0.0 shipped resolves to the broken
version and dies at import. Those installs need
`pip install 'mcp>=1.7.0,<2.0'` by hand.

---

## 6. Cutting a GitHub release (maintainer only)

**No agent may execute this section.** Publishing a release is outward-facing
and is the repository owner's decision. What follows is the diagnosis and the
runbook.

### Diagnosis

The repository has **zero** published releases:

```text
$ gh api repos/PranavNagrecha/AwesomeSalesforceSkills/releases --jq 'length'
0
$ curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -L \
    'https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz'
HTTP 404
```

`sfskills-mcp-init` builds that exact URL (`init.py:_release_url` plus
`ASSET_NAME = "sfskills-data.tar.gz"`) and exits 1 on the 404.
`/releases/latest/download/` only resolves against a **published,
non-draft, non-prerelease** release.

The workflow that would create one exists and is correct — it has just never
run:

```text
$ gh run list --workflow=publish-mcp.yml --limit 5
(no output — zero runs, ever)
$ git ls-remote --tags origin | grep 'refs/tags/mcp-v'
mcp-v0.4.0  mcp-v0.4.1  mcp-v0.4.4  mcp-v0.4.6
```

All four tags are on origin and all four carry `publish-mcp.yml`. They date
2026-05-08 … 2026-06-17 and the GitHub repository was created 2026-06-17, so
all four arrived in the single initial import push. GitHub Actions documents
this exact behaviour: *"Events will not be created for tags when more than
three tags are pushed at once."*
([Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows))
Four tags in one push therefore produced **no `push` event at all**, and
`publish-mcp.yml` never fired. This is also why step 4 below insists on one
tag per push.

`workflow_dispatch` cannot rescue it. The `publish-data` job that attaches the
tarball is gated on `if: startsWith(github.ref, 'refs/tags/mcp-v')`, so a
manual dispatch from a branch builds the bundle and then skips the upload. Only
a fresh tag push cuts a release.

### Blocker to fix first

`.github/workflows/publish-mcp.yml` builds the data bundle with:

```yaml
cp -r vector_index _bundle/sfskills-data/
```

against a bare CI checkout, where `vector_index/` holds only `manifest.json`
and the two fixture files — `lexical.sqlite` and `chunks.jsonl` are gitignored
and the workflow never builds them (`grep -n 'build_index\|skill_sync'
.github/workflows/publish-mcp.yml` returns nothing). A release cut today would
publish a tarball with **no retrieval index**, and `sfskills-mcp-init` would
succeed into a cache that answers nothing — a worse failure than the current
honest 404.

Add a step before `Build data bundle`:

```yaml
      - name: Build retrieval index
        run: |
          python -m pip install -r requirements.txt
          python scripts/build_index.py
```

(`scripts/bootstrap.py --skip-commands` also works and is faster, since it
skips the embedding encode and writes nothing tracked.)

### Steps

1. **Fix the blocker above** in `.github/workflows/publish-mcp.yml`. Without it
   the release ships an unusable bundle.
2. Align the versions. `mcp/sfskills-mcp/pyproject.toml` `version` and
   `src/sfskills_mcp/__init__.py` `__version__` must match. Both read `0.4.6`
   in-tree today, but the wheel published to PyPI as 0.4.6 reports
   `__version__ = 0.4.4` — it was built from stale source. Bump both together.
3. Commit and push to `main`.
4. Tag and push — **one tag per push**, which is what the >3-tags rule above
   requires:
   ```bash
   git tag mcp-v0.4.7
   git push origin mcp-v0.4.7
   ```
5. Watch it: `gh run watch`.
6. Confirm the asset attached:
   ```bash
   gh release view mcp-v0.4.7 --json assets --jq '.assets[].name'
   ```
   `sfskills-data.tar.gz` must be listed.
7. Confirm the URL the client actually requests now resolves:
   ```bash
   curl -sSIL -o /dev/null -w '%{http_code}\n' \
     https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
   ```
   must print `200`.
8. End-to-end, in a clean virtualenv:
   ```bash
   pip install sfskills-mcp && sfskills-mcp-init
   ```
   must exit 0, and the extracted cache must contain a non-trivial
   `vector_index/lexical.sqlite`.

---

## 7. Troubleshooting

| Symptom | Go to |
|---|---|
| Claude opened the wrong skill package | [`docs/troubleshooting.md`](./troubleshooting.md#claude-opened-the-wrong-skill-package) — the shipped path has no coverage gate, so this is its characteristic failure. Nothing to install. |
| Claude says the topic is not covered | [`docs/troubleshooting.md`](./troubleshooting.md#claude-says-the-topic-is-not-covered) — almost always the same cause; every router forbids the claim without pasted lookup output. |
| `Coverage: NONE` on every query | [Section 3](#the-failure-mode-if-you-skip-bootstrap) — you have not built the index. This means "nothing built", never "empty library". |
| Slash commands missing in Claude Code | Run `python3 scripts/bootstrap.py`, then restart Claude Code. It loads commands at session start. |
| Search takes tens of seconds | [`docs/troubleshooting.md`](./troubleshooting.md#search-is-slow-or-appears-to-hang) — no longer normal; expect 0.5–0.7 s. |
| `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` | [Section 5](#the-mcp-sdk-pin) — pip resolved mcp 2.0.x. |
| `sfskills-mcp-init: HTTP 404` | [Section 6](#6-cutting-a-github-release-maintainer-only) — expected; use the clone path. |
| Client can't find the repo root | [`CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md) — set `SFSKILLS_REPO_ROOT` to an absolute path. |
| Anything else | [`docs/troubleshooting.md`](./troubleshooting.md) |

Related documents:

- [`docs/getting-started.md`](./getting-started.md) — remains authoritative for
  the three-entry-point framing (Claude Code checkout / MCP server / plain
  export to Cursor, Windsurf and other tools), including the split inside the
  Claude Code entry point between the no-build router path and the optional
  search build. This page covers setup mechanics; that one covers which entry
  point you want.
- [`docs/installing-the-plugin.md`](./installing-the-plugin.md) — Claude Code
  plugin packaging.
- [`docs/installing-single-agents.md`](./installing-single-agents.md) —
  installing one run-time agent without the whole library.
- [`mcp/sfskills-mcp/docs/CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md) —
  per-client MCP configuration.
