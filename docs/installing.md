# Installing SfSkills

Canonical setup reference for a fresh clone. Every command on this page was
executed as written on 2026-08-15 (macOS 26.5, Apple silicon, Python 3.14.4,
Claude Code 2.1.209). Counts and timings are live values — the verification
command is given beside each one so you can re-derive it rather than trust it.

**What works with no setup at all.** A clone carries `CLAUDE.md`, the 12 router
skills under `.claude/skills/` (a top-level `salesforce` router plus 11 domain
routers), their 11 rosters, and the 48 run-time agent loaders under
`.claude/agents/`. Open the directory in Claude Code and ask a Salesforce
question: the model reads the router descriptions, hands off to one domain
router, opens that router's `references/skill-index.md` — the roster of that
domain's packages, one ≤220-character gloss each — and opens the one it picks.

There are **eleven** rosters, not one, and Claude reads **one** of them: an Apex
question costs the apex roster's 158 glosses, never the corpus's 1,027. No index
is involved anywhere in that path, which is why every router says the shipped
rosters work with no setup.

```bash
git ls-files .claude/skills | wc -l          # 23 = 12 SKILL.md + 11 rosters
grep -c '^- ' .claude/skills/salesforce-apex/references/skill-index.md   # 158
```

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

- New user, want search and slash commands: [1. Install](#1-install).
- Wiring an AI client to the MCP server: [5. MCP install paths](#5-mcp-install-paths).
- Installing as a Claude Code plugin: [installing-the-plugin.md](./installing-the-plugin.md).
- Repository owner cutting a release: [6. Cutting a GitHub release](#6-cutting-a-github-release-maintainer-only).

---

<a id="1-one-command"></a>

## 1. Install

**Use a virtual environment.** This is not a style preference. A Homebrew or
distro Python refuses a system-wide `pip install` under
[PEP 668](https://peps.python.org/pep-0668/), and earlier revisions of this page
opened with the command that fails:

```text
$ python3 -m pip install -r requirements.txt
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.

    If you wish to install a Python library that isn't in Homebrew,
    use a virtual environment:

    python3 -m venv path/to/venv
$ echo $?
1
```

The recipe that works:

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/bootstrap.py
```

**`.venv/` is not in `.gitignore`** — the file ignores `.qa-venv/`,
`.build-venv/`, `.smoke-venv/` and `.verify-venv/`, but not `.venv/`. Verify and
exclude it locally before you create it, or thousands of untracked files land in
`git status`:

```bash
git check-ignore -q .venv || echo '.venv/' >> .git/info/exclude
```

`.git/info/exclude` is per-clone and never committed, so this needs no change to
a tracked file. Alternatively, put the venv outside the repository.

If your Python is not externally managed — pyenv, conda, a Docker image, most
Linux user installs — plain `python3 -m pip install -r requirements.txt` works
and you can drop the `./.venv/bin/` prefix throughout. Everywhere below,
`python3` means "the interpreter you installed the requirements into".

Real transcript of a cold first run, captured 2026-08-15 on a
`git clone --depth 1`:

```text
$ ./.venv/bin/python scripts/bootstrap.py
[   0.0s] phase 1/6  preflight
[   0.0s]           repo root       /.../freshclone
[   0.0s]           interpreter     /opt/homebrew/opt/python@3.14/bin/python3.14
[   0.0s]           python          3.14.4
[   0.6s]           fastembed       installed (semantic embeddings available)
[   0.6s]           OK  required dependencies present (PyYAML, jsonschema)
[   0.6s] phase 2/6  scanning skill packages -> retrieval chunks (~5-35 s)
[   3.6s]           ... still scanning skills/ and knowledge/  [chunks.jsonl not yet written, lexical.sqlite not yet written]
[   6.5s]           135409 chunks built from 1027 skill packages
[   6.5s] phase 3/6  verifying chunk hash against the committed manifest
[   6.5s]           OK  chunks_hash=779839f875b7... matches the committed manifest
[   6.5s] phase 4/6  writing vector_index/ (chunks.jsonl + lexical.sqlite) — all gitignored
[   8.8s]           chunks.jsonl   134 MB
[   8.8s]           lexical.sqlite 177 MB
[   8.8s] phase 5/6  installing slash commands -> .claude/commands/
[   8.9s]           installed 67 commands to .claude/commands/  (added=67 updated=0 removed=0)
[   8.9s]           Note: Claude Code loads slash commands at session start. Restart your CLI for new commands to register.
[   8.9s] phase 6/6  verifying retrieval
[   9.0s]           OK  'trigger recursion' -> apex/recursive-trigger-prevention
[   9.0s]           OK  67 slash commands installed in .claude/commands/

Bootstrap complete in 9s.
```

The `fastembed` line reads `not installed (lexical-only retrieval — this is the
default)` on a machine that does not happen to carry the package. Either way the
default build is lexical-only; see [section 4](#4-embeddings-configured-on-inert-until-you-install-fastembed).

**Every count in that transcript is live, never a constant.** The command count
is `len(commands/*.md)` and the chunk count is whatever your working tree
produces. Compare them against the repository, not against this page:

```bash
ls commands/*.md | wc -l                                              # 67
python3 -c "import json;print(json.load(open('vector_index/manifest.json'))['chunk_count'])"
```

**Those timings are one machine's, not a guarantee.** Measured on macOS 26.5,
Apple silicon (arm64), Python 3.14.4: **9 s** cold with both artefacts absent and
**7 s** on a re-run, because `build_lexical_index` short-circuits when the chunk
hash is unchanged. A slower disk will be longer, and the phase-2 banner quotes a
deliberately conservative `~5-35 s`. The progress lines exist so a longer run is
still obviously working rather than hung — nothing is silent for more than three
seconds (except under `--quiet`, which suppresses them by request).

Then confirm it yourself:

```bash
python3 scripts/search_knowledge.py "trigger recursion"
```

The only entry under `Top skills:` should be `apex/recursive-trigger-prevention`.
The number beside it is a ranking output and moves whenever the ranker is
retuned — assert the skill id, never the score. On a fresh clone with no
embeddings that query answered in **0.15 s**; on a checkout that also carries
`vector_index/skill_embeddings.jsonl` and has `fastembed` installed, three
queries measured **0.56–0.84 s** with a peak resident set of 371–377 MB. If
yours takes tens of seconds, see
[troubleshooting.md](troubleshooting.md#search-is-slow-or-appears-to-hang).

### Flags

`scripts/bootstrap.py` uses `argparse`, so `--help` prints usage rather than
starting a build.

| Flag | Effect |
|---|---|
| *(none)* | Build the lexical index, install slash commands, verify. The normal path. |
| `--with-embeddings` | Also encode **chunk-level** semantic embeddings into `vector_index/embeddings.jsonl`. Hours of CPU. This is almost certainly not what you want — read [section 4](#4-embeddings-configured-on-inert-until-you-install-fastembed) first. |
| `--skip-commands` | Do not write `.claude/commands/`. For non-Claude-Code users. |
| `--verify-only` | Build nothing; just check that the index answers a known-good query and that the command count matches. |
| `--quiet` | Suppress progress lines. Failures and the final result still print. |

Exit codes, all observed: `0` success, `1` verification failed, `2` refused to
start — wrong Python, a missing dependency, or `--with-embeddings` against a
config that disables embeddings
([section 4](#--with-embeddings-cannot-turn-embeddings-on-by-itself)).

```text
$ ./.venv/bin/python scripts/bootstrap.py --verify-only     # before any build
[   0.3s] phase 6/6  verifying retrieval
[   0.3s]           FAIL  vector_index/lexical.sqlite is missing

BOOTSTRAP FAILED: index not built — run: python3 scripts/bootstrap.py
$ echo $?
1
```

---

## 2. What bootstrap does — and what it refuses to do

| Phase | Does |
|---|---|
| 1. preflight | Checks Python ≥ 3.10 and that PyYAML + jsonschema import. Prints the resolved repo root, the interpreter path, and whether `fastembed` is available. Exits 2 with the exact remediation command if anything is missing. |
| 2. chunks | `pipelines.sync_engine.build_state(root, skip_embeddings=True)` — scans 1,027 skill packages into ~135k retrieval chunks, in-process. |
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

**`git status` is clean when it finishes**, verified on the clone the transcript
above came from:

```text
$ git status --porcelain | grep -v '^??' | wc -l
       0
```

### Why bootstrap and not `scripts/build_index.py`

Both reach a working lexical index. Prefer `bootstrap.py` because it also
installs the slash commands, has a real `--help` and `--verify-only`, and never
runs an encoder. `build_index.py` has no argument parsing at all — appending
`--help` starts a rebuild.

The difference that matters is what `build_index.py` does to your working tree,
and it depends entirely on whether an embedding backend is installed. Both
outcomes were measured on the same fresh clone:

| `build_index.py` run | Script output | Modified tracked files | Wall clock |
|---|---|---:|---:|
| no encoder available (plain `pip install -r requirements.txt`) | `Index build complete. Files touched: 0` | **0** | 7 s |
| an encoder available | `Index build complete. Files touched: 1030` | **1,029** | see below |

```text
$ ./.venv/bin/python scripts/build_index.py          # no fastembed installed
[embed] WARNING: fastembed package is not installed but config has backend=fastembed. …
Index build complete. Files touched: 0
$ git status --porcelain | grep -v '^??' | wc -l
       0
```

With an encoder present it rewrites `vector_embedding` into all 1,027
`registry/skills/*.json` records plus `registry/skills.json` and
`vector_index/manifest.json` — 1,029 modified tracked files you then have to
recognise as noise and discard. Measured by temporarily setting
`embeddings.backend: hash` (a cheap stand-in for a working encoder) on that same
clone:

```text
$ ./.venv/bin/python scripts/build_index.py
Index build complete. Files touched: 1030
$ git status --porcelain | grep -v '^??' | awk '{print $2}' | sed 's|/[^/]*$||' | sort | uniq -c
    1 registry
 1027 registry/skills
    1 vector_index
```

With the real `fastembed` backend that same run first encodes every chunk, which
is hours rather than seconds. Earlier revisions of this page asserted the
1,029-file outcome unconditionally, including for "a fresh clone with no
embedding backend installed" — which is precisely the case where the count is
zero. The committed registry already carries `vector_embedding: null` for all
1,027 records and `embedding_count: 0` in the manifest, so without an encoder the
run is a content-identical no-op.

---

## 3. What a fresh clone contains — and what it does not

Measured on `git clone --depth 1` (2026-08-15): **138 MB** working tree, of which
**32 MB** is `.git`. These grow with every commit; re-run `du -sh . .git`.

**Not in the clone (bootstrap builds these):**

| Path | Size on this checkout | Why not committed |
|---|---:|---|
| `vector_index/lexical.sqlite` | 177 MB | Past GitHub's file-size limits; a binary that changes wholesale on every rebuild. |
| `vector_index/chunks.jsonl` | 134 MB | Same — 135,409 lines regenerated from `skills/`. |
| `vector_index/skill_embeddings.jsonl` | 5.3 MB | 1,027 vectors, one per skill. Built only by `scripts/build_skill_embeddings.py`; see [section 4](#4-embeddings-configured-on-inert-until-you-install-fastembed). |
| `.claude/commands/` | 67 files | Byte-for-byte copies of the tracked `commands/*.md` (`cmp` clean on all 67). Tracking both would create a permanent drift surface between two copies of the same file. |

`vector_index/embeddings.jsonl`, the chunk-level vector file, is **not built by
any default path**. It is absent from this checkout; only
`scripts/bootstrap.py --with-embeddings` and `scripts/build_index.py` with an
encoder installed produce it.

Total after a default bootstrap: **310 MB** (`du -sh vector_index/`).

**In the clone:**

`vector_index/` ships exactly three files — `manifest.json` (the integrity
hashes), `query-fixtures.json` and `query-variants.json` (the retrieval test
fixtures). Note that the committed `manifest.json` describes artefacts that are
*not* in the clone: it reports a chunk count for an index you have not built yet.
It is an integrity baseline for bootstrap phase 3, not a statement about your
working tree.

```bash
git ls-files vector_index          # 3 files, none of them an index
```

Under `.claude/`, three subtrees are tracked so a clone is plugin-usable:

```text
$ git ls-files .claude/ | cut -d/ -f1-2 | sort | uniq -c
  48 .claude/agents            run-time agent loaders
  23 .claude/skills            12 router SKILL.md + 11 references/skill-index.md
   3 .claude/workflows         add-skill.js, model-routing-benchmark.js, source-onboarding.js
```

The top-level `salesforce` router has no roster because it hands off to the
domain routers, which is why 12 routers carry 11 rosters. Everything else under
`.claude/` is local session state, ignored by `.gitignore:131` (`.claude/*`) and
re-admitted by the three negations on lines 132–134.

### The failure mode if you skip bootstrap

This is confined to the search surface. The router path in the header above
still works without an index; `search_knowledge.py` does not.

`search_knowledge.py` does not detect a missing index. It reports no coverage and
**exits 0**, which is indistinguishable from a library that has nothing on the
topic. Reproduced on a fresh clone before bootstrap:

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
`search_knowledge.py`, it exits non-zero and names the failed assertion.

---

## 4. Embeddings: configured on, inert until you install fastembed

Three facts only make sense together, and this page has previously stated one of
them without the others:

1. `config/retrieval-config.yaml` sets `embeddings.enabled: true` (line 84) with
   `backend: fastembed`. The config turns them **on**.
2. `fastembed` is commented out of `requirements.txt` (line 12,
   `# fastembed>=0.4,<1.0`). A plain `pip install -r requirements.txt` does
   **not** install it.
3. With no backend present, `pipelines/embedding_backends.py` prints a warning
   and falls back to lexical-only without crashing.

So the accurate statement is that embeddings are **configured on and inert until
you install `fastembed` yourself**. They are not "opt-in behind a flag" — the
config already enables them — and they are not "on by default" — the dependency
is not installed.

`scripts/bootstrap.py` additionally passes `skip_embeddings=True` by default, so
the standard run stays deterministic and takes seconds even on a machine that
happens to have `fastembed` installed globally.

### Building the vectors that search actually uses

There are two embedding files and they are not interchangeable:

| File | Vectors | Built by | Read by |
|---|---:|---|---|
| `vector_index/skill_embeddings.jsonl` | 1,027 (one per skill) | `scripts/build_skill_embeddings.py` | `scripts/search_knowledge.py` and the MCP `search_skill` tool — checked **first** in `pipelines/ranking.rerank_results` |
| `vector_index/embeddings.jsonl` | ~135,409 (one per chunk) | `scripts/bootstrap.py --with-embeddings`, `scripts/build_index.py` | the same reranker, only as a fallback when a chunk's skill has no skill-level vector |

Almost everyone wants the first one. The chunk-level file is hundreds of
megabytes and hours; the skill-level one is 5.3 MB and, measured cold on a fresh
clone, **86 seconds**:

```text
$ ./.venv/bin/python -m pip install 'fastembed>=0.4,<1.0'
Successfully installed … fastembed-0.8.0 numpy-2.5.2 onnxruntime-1.28.0 …

$ ./.venv/bin/python scripts/build_skill_embeddings.py
discovered 1027 skills
  cached: 0, to encode: 1027
  encoded 1027 in 84.6s (12/sec)
wrote 1027 embeddings to /…/vector_index/skill_embeddings.jsonl
```

That file is gitignored, so `git status` stays clean. Re-runs are near-free —
the content-hash cache re-encodes only skills whose summary text changed
(`--force` overrides it). Note that `fastembed` pulls in `onnxruntime`, `numpy`
and `tokenizers`, which is why it is not a default dependency.

Earlier revisions of this page pointed here at `bootstrap.py --with-embeddings`,
which builds the *other* file. That is why `--with-embeddings` is described in
the flag table as almost certainly not what you want; its own `--help` text says
`+535 MB, HOURS of encode time`.

Per-query overhead from skill vectors is roughly 50 ms once the model is warm,
after a one-off cold start of about 14 s.

If you do build the chunk-level file, budget hours and run it overnight. Re-runs
are far cheaper — the content-hash cache in `pipelines/embedding_backends.py`
re-encodes only chunks whose text changed. Note also that
`scripts/search_knowledge.py` loads the whole of `embeddings.jsonl` into memory
when `embeddings.enabled` is true, so building it raises the resident set of
every search process. On a checkout without it, `load_embeddings` returns an
empty mapping and costs nothing.

### Retrieval benefit — measured 2026-08-15

Over the 154 hand-written held-out queries, `python3
evals/measurement/run_heldout.py --json` versus `--no-embeddings`, on a machine
carrying `fastembed` 0.8.0 and `vector_index/skill_embeddings.jsonl`:

| retrieval config | Hit@1 | Hit@3 | Coverage: NONE |
|---|---:|---:|---:|
| lexical-only | 39.0% | 48.7% | 0.0% |
| + `fastembed` skill vectors | **40.3%** | **53.9%** | 0.0% |

**+1.3pp Hit@1 and +5.2pp Hit@3.** Both rows measure the keyword-search path
only, not the routing path a clone or plugin user exercises.

**Do not copy those absolutes into another document.** They move whenever the
corpus moves, and at least three different pairs are quoted around this
repository — `config/retrieval-config.yaml` still carries 36.4/44.2 → 37.0/48.7
from the 2026-08-13 re-enable. Re-run `run_heldout.py` instead.

The 400-fixture comparison that a previous revision of this page used to conclude
*"enable this only if you are actively evaluating semantic retrieval"* should not
be used for this question at all. The fixtures are close paraphrases of the
`triggers:` frontmatter that is itself indexed, so they measure the easy case and
saturate: measured 2026-08-15 over all 1,356 of them with `--use-domain`, Hit@1
is 98.4% and Hit@3 is 100.0%. A saturated benchmark cannot show a difference in
either direction.

The 0% `Coverage: NONE` rate on the held-out set is itself worth noting: a
2026-07-31 measurement on realistic phrasings recorded 23.3%.

### `--with-embeddings` cannot turn embeddings on by itself

Whether embeddings are encoded at all is decided repository-wide by
`embeddings.enabled` in `config/retrieval-config.yaml`. Bootstrap never edits
that key. The flag only stops bootstrap from forcing `skip_embeddings=True`; the
encoder itself returns zero vectors whenever the config says `enabled: false`
(`pipelines/embedding_backends.py:103-104` is literally `if not config.enabled: /
return []`). So the flag can suppress the encode but never enable it.

So that the combination is not a silent no-op, bootstrap reads the config before
phase 2 and refuses when the key is `false`. An unreadable or absent config is
treated as unknown and the build proceeds. Reproduced by flipping the key on a
scratch clone:

```text
$ ./.venv/bin/python scripts/bootstrap.py --with-embeddings
[   0.3s]           FAIL  --with-embeddings requested but config/retrieval-config.yaml has embeddings.enabled: false

BOOTSTRAP FAILED: embeddings are disabled repository-wide, so --with-embeddings would encode nothing.
Set embeddings.enabled: true in config/retrieval-config.yaml, or drop the flag.
$ echo $?
2
```

**You will not see that failure on the current config**, which has
`embeddings.enabled: true`. The transcript above is what the guard prints if
someone flips the key back. The condition you *are* likely to hit is the other
one: the flag runs, the config agrees, and `fastembed` is not installed — in
which case phase 1 prints `fastembed  not installed (lexical-only retrieval —
this is the default)` and the encode produces nothing.

---

## 5. MCP install paths

The server exposes 38 tools over stdio. Full per-client wiring for 18 clients
lives in [`mcp/sfskills-mcp/docs/CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md).
The install decision is here.

**The Claude Code plugin does not wire the MCP server for you.**
`.claude-plugin/plugin.json` declares no `mcpServers` key, and a fresh install
reports `MCP servers (0)` in `claude plugin details sfskills`. MCP setup is
always the manual step below.

### From a clone (recommended today)

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/bootstrap.py
./.venv/bin/python -m pip install -e mcp/sfskills-mcp
```

Then register the server **with the venv's interpreter, by absolute path**:

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- /absolute/path/to/AwesomeSalesforceSkills/.venv/bin/python -m sfskills_mcp
```

Registering bare `python3` instead is the most common way to get a server that
adds cleanly and then never connects — that interpreter is the system Python,
which does not have `sfskills_mcp` on its path:

```text
$ claude mcp add sfskills --env SFSKILLS_REPO_ROOT=… -- python3 -m sfskills_mcp
Added stdio MCP server sfskills with command: python3 -m sfskills_mcp to local config
$ claude mcp list
sfskills: python3 -m sfskills_mcp - ✘ Failed to connect

$ claude mcp add sfskills --env SFSKILLS_REPO_ROOT=… -- /…/.venv/bin/python -m sfskills_mcp
$ claude mcp list
sfskills: /…/.venv/bin/python -m sfskills_mcp - ✔ Connected
```

`SFSKILLS_REPO_ROOT` must be absolute, and must be set inside the client's own
config block — an `export` in your shell does not reach a detached subprocess.

### From PyPI

```bash
pip install sfskills-mcp
sfskills-mcp-init          # currently exits 1 — see below
```

Both halves of this path are currently broken, verified in a clean virtualenv on
2026-08-15:

1. **The wheel resolves an incompatible SDK.** `pip install sfskills-mcp` pulls
   `sfskills-mcp 0.4.6`, which declared an unbounded `mcp>=1.4.0` floor, so pip
   now picks `mcp 2.0.0` and the server cannot import:

   ```text
   $ pip install sfskills-mcp
   Successfully installed … mcp-2.0.0 … sfskills-mcp-0.4.6 …
   $ python -c "import sfskills_mcp.server"
     File ".../sfskills_mcp/server.py", line 64, in <module>
       from mcp.server.fastmcp import Context, FastMCP
   ModuleNotFoundError: No module named 'mcp.server.fastmcp'
   ```

   Fix an existing install by hand — this works:

   ```text
   $ pip install 'mcp>=1.7.0,<2.0'
   Successfully installed … mcp-1.29.0 …
   $ python -c "import sfskills_mcp.server; print('import OK')"
   import OK
   ```

2. **The published wheel is stale.** It installs as version 0.4.6 but reports
   `__version__ = 0.4.4`, so it was built from older source:

   ```text
   $ pip show sfskills-mcp | head -2
   Name: sfskills-mcp
   Version: 0.4.6
   $ python -c "import sfskills_mcp; print(sfskills_mcp.__version__)"
   0.4.4
   ```

3. **`sfskills-mcp-init` has nothing to download.** It fetches
   `https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz`,
   which returns HTTP 404 because no GitHub release has been published:

   ```text
   $ sfskills-mcp-init --cache-dir /tmp/clean-cache
   sfskills-mcp-init: downloading https://github.com/…/sfskills-data.tar.gz
   sfskills-mcp-init: HTTP 404 fetching https://github.com/…/sfskills-data.tar.gz
     Verify the release tag exists: https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases
   $ echo $?
   1
   ```

Until a release is cut ([section 6](#6-cutting-a-github-release-maintainer-only)),
use the clone path above. In-tree the package is already at **0.4.8**
(`mcp/sfskills-mcp/pyproject.toml` and `src/sfskills_mcp/__init__.py` agree), so
the version skew is fixed at source and waiting on a publish.

### The `mcp` SDK pin

`mcp/sfskills-mcp/pyproject.toml` declares `mcp>=1.7.0,<2.0`. Both bounds were
re-measured against published wheels on 2026-08-15:

| mcp version | `import sfskills_mcp.server` | evidence |
|---|---|---|
| 1.6.0 | fails | `ImportError: cannot import name 'ToolAnnotations' from 'mcp.types'` |
| 1.7.0 | OK | verified |
| 1.29.0 | OK | verified |
| 2.0.0 | fails | `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` |

mcp 2.0.0 removed the `mcp.server.fastmcp` module that `server.py:64` imports
`Context` and `FastMCP` from. Lifting the ceiling means porting the server, not
bumping a number.

---

## 6. Cutting a GitHub release (maintainer only)

**No agent may execute this section.** Publishing a release is outward-facing and
is the repository owner's decision. What follows is the diagnosis and the
runbook.

### Diagnosis

The repository has **zero** published releases, re-checked 2026-08-15:

```text
$ gh api repos/PranavNagrecha/AwesomeSalesforceSkills/releases --jq 'length'
0
$ curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -L \
    'https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz'
HTTP 404
```

`sfskills-mcp-init` builds that exact URL (`init.py:_release_url` plus
`ASSET_NAME = "sfskills-data.tar.gz"`) and exits 1 on the 404.
`/releases/latest/download/` only resolves against a **published, non-draft,
non-prerelease** release.

The workflow that would create one exists and is correct — it has just never run:

```text
$ git ls-remote --tags origin | grep 'refs/tags/mcp-v'
mcp-v0.4.0  mcp-v0.4.1  mcp-v0.4.4  mcp-v0.4.6
```

All four tags are on origin and all four carry `publish-mcp.yml`. They date
2026-05-08 … 2026-06-17 and the GitHub repository was created 2026-06-17, so all
four arrived in the single initial import push. GitHub Actions documents this
exact behaviour: *"Events will not be created for tags when more than three tags
are pushed at once."*
([Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
quote re-verified 2026-08-15.) Four tags in one push therefore produced **no
`push` event at all**, and `publish-mcp.yml` never fired. This is also why step 4
below insists on one tag per push.

`workflow_dispatch` cannot rescue it. The `publish-data` job that attaches the
tarball is gated on `if: startsWith(github.ref, 'refs/tags/mcp-v')`
(`publish-mcp.yml:80`), so a manual dispatch from a branch builds the bundle and
then skips the upload. Only a fresh tag push cuts a release.

### The bundle-without-an-index blocker — fixed

`publish-mcp.yml` used to build the data bundle with `cp -r vector_index
_bundle/sfskills-data/` against a bare CI checkout, where `vector_index/` holds
only `manifest.json` and the two fixture files — `lexical.sqlite` and
`chunks.jsonl` are gitignored. A release cut that way published a tarball with
**no retrieval index**, and `sfskills-mcp-init` succeeded into a cache that
answered nothing.

Fixed before the `mcp-v0.4.7` release: the workflow now runs
`python -m pip install -r requirements.txt` and `python3 scripts/build_index.py`
before the bundle step (`publish-mcp.yml`, *Build lexical retrieval index*).
That adds ~300 MB to the release asset — `chunks.jsonl` ~127 MB plus
`lexical.sqlite` ~169 MB. Embeddings are deliberately not built and stay
excluded.

Verify it stayed fixed before any release:

```bash
grep -n 'build_index' .github/workflows/publish-mcp.yml   # must match
```

### Steps

1. Confirm the index step is still present (see above) — without it the release
   ships an unusable bundle.
2. Confirm the versions still agree. `mcp/sfskills-mcp/pyproject.toml` `version`
   and `src/sfskills_mcp/__init__.py` `__version__` must match; both read
   **0.4.8** in-tree today, which is the bump that carries the record-access
   corpus and the first PolyForm-licensed wheel.
3. Commit and push to `main`.
4. Tag and push — **one tag per push**, which is what the >3-tags rule above
   requires:
   ```bash
   git tag mcp-v0.4.8
   git push origin mcp-v0.4.8
   ```
5. Watch it: `gh run watch`.
6. Confirm the asset attached:
   ```bash
   gh release view mcp-v0.4.8 --json assets --jq '.assets[].name'
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
   must exit 0, `python -c "import sfskills_mcp.server"` must succeed, and the
   extracted cache must contain a non-trivial `vector_index/lexical.sqlite`.

---

## 7. Troubleshooting

| Symptom | Go to |
|---|---|
| `error: externally-managed-environment` from pip | [Section 1](#1-install) — use a venv. |
| Claude opened the wrong skill package | [`docs/troubleshooting.md`](./troubleshooting.md#claude-opened-the-wrong-skill-package) — the shipped path has no coverage gate, so this is its characteristic failure. Nothing to install. |
| Claude says the topic is not covered | [`docs/troubleshooting.md`](./troubleshooting.md#claude-says-the-topic-is-not-covered) — almost always the same cause; every router forbids the claim without pasted lookup output. |
| `Coverage: NONE` on every query | [Section 3](#the-failure-mode-if-you-skip-bootstrap) — you have not built the index. This means "nothing built", never "empty library". |
| Slash commands missing in Claude Code | Run `python3 scripts/bootstrap.py`, then restart Claude Code. It loads commands at session start. |
| Search takes tens of seconds | [`docs/troubleshooting.md`](./troubleshooting.md#search-is-slow-or-appears-to-hang) — no longer normal; expect well under a second. |
| `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` | [Section 5](#the-mcp-sdk-pin) — pip resolved mcp 2.0.x. |
| MCP server added but `✘ Failed to connect` | [Section 5](#from-a-clone-recommended-today) — register the venv interpreter, not bare `python3`. |
| `sfskills-mcp-init: HTTP 404` | [Section 6](#6-cutting-a-github-release-maintainer-only) — expected; use the clone path. |
| Client can't find the repo root | [`CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md) — set `SFSKILLS_REPO_ROOT` to an absolute path. |
| Anything else | [`docs/troubleshooting.md`](./troubleshooting.md) |

Related documents:

- [`docs/getting-started.md`](./getting-started.md) — remains authoritative for
  the three-entry-point framing (Claude Code checkout / MCP server / plain export
  to Cursor, Windsurf and other tools), including the split inside the Claude
  Code entry point between the no-build router path and the optional search
  build. This page covers setup mechanics; that one covers which entry point you
  want.
- [`docs/installing-the-plugin.md`](./installing-the-plugin.md) — Claude Code
  plugin packaging.
- [`docs/installing-single-agents.md`](./installing-single-agents.md) —
  installing one run-time agent without the whole library.
- [`mcp/sfskills-mcp/docs/CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md) —
  per-client MCP configuration.
