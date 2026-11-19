# Installing SfSkills

**Who this is for:** anyone setting up a clone, the local search index or the
MCP server, and the repository owner cutting a release (§ 6).

**What works with no setup at all.** A clone carries `CLAUDE.md`, the router
skills under `.claude/skills/` (a top-level `salesforce` router plus one router
per domain, each domain router with a `references/skill-index.md` roster), and
the run-time agent loaders under `.claude/agents/`. Open the directory in Claude
Code and ask a Salesforce question: the model reads the router descriptions,
hands off to one domain router, opens that router's roster (one short gloss per
package) and opens the package it picks. No index is involved in that path.

**What bootstrap adds.** Three generated artefacts are deliberately not
committed, and one command builds them:

| Not committed | Unlocks |
|---|---|
| `vector_index/chunks.jsonl` | `scripts/search_knowledge.py`, the MCP `search_skill` tool, and the build-time agents that maintain the library |
| `vector_index/lexical.sqlite` | same — this is the FTS5 index search reads |
| `.claude/commands/` | the slash commands inside Claude Code, one per `commands/*.md` |

Bootstrap is required for the *search* and *slash-command* surfaces, not for the
library to be reachable.

**Accuracy figures for search are not accuracy figures for the library.** The
held-out retrieval number (lexical, 154 queries, 2026-10-20: Hit@1 0.41, Hit@3
0.50) measures the keyword-search path, which most users never build. The
routing path is described in
[architecture.md](architecture.md#how-this-path-is-measured-and-one-retraction).

- New user, want search and slash commands: [1. Install](#1-install).
- Wiring an AI client to the MCP server: [5. MCP install paths](#5-mcp-install-paths).
- Installing as a Claude Code plugin: [installing-the-plugin.md](./installing-the-plugin.md).
- Repository owner cutting a release: [6. Cutting a GitHub release](#6-cutting-a-github-release-maintainer-only).

---

## 1. Install

**Use a virtual environment.** A Homebrew or distro Python refuses a system-wide
`pip install` under [PEP 668](https://peps.python.org/pep-0668/) with
`error: externally-managed-environment`.

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
git check-ignore -q .venv || echo '.venv/' >> .git/info/exclude   # .venv/ is not in .gitignore
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/bootstrap.py
```

`.git/info/exclude` is per-clone and never committed. Alternatively, put the
venv outside the repository. If your Python is not externally managed (pyenv,
conda, a Docker image, most Linux user installs), plain
`python3 -m pip install -r requirements.txt` works. Everywhere below, `python3`
means "the interpreter you installed the requirements into".

Bootstrap prints one progress line per phase and finishes in seconds on a
typical laptop. Then confirm it yourself:

```bash
python3 scripts/search_knowledge.py "trigger recursion"
```

The only entry under `Top skills:` should be `apex/recursive-trigger-prevention`.
Assert the skill id, never the score; scores move when the ranker is retuned. If
the query takes tens of seconds, see
[troubleshooting.md](troubleshooting.md#search-is-slow-or-appears-to-hang).

### Flags

`scripts/bootstrap.py` uses `argparse`, so `--help` prints usage rather than
starting a build.

| Flag | Effect |
|---|---|
| *(none)* | Build the lexical index, install slash commands, verify. The normal path. |
| `--with-embeddings` | Also encode **chunk-level** embeddings into `vector_index/embeddings.jsonl`. Hours of CPU; almost certainly not what you want — read [section 4](#4-embeddings-configured-on-inert-until-you-install-fastembed) first. |
| `--skip-commands` | Do not write `.claude/commands/`. For non-Claude-Code users. |
| `--verify-only` | Build nothing; check that the index answers a known-good query and that the command count matches. |
| `--quiet` | Suppress progress lines. Failures and the final result still print. |

Exit codes: `0` success, `1` verification failed (for example, the index is
missing), `2` refused to start — wrong Python, a missing dependency, or
`--with-embeddings` against a config that disables embeddings.

---

## 2. What bootstrap does — and what it refuses to do

| Phase | Does |
|---|---|
| 1. preflight | Checks Python ≥ 3.10 and that PyYAML + jsonschema import. Prints the repo root, the interpreter, and whether `fastembed` is available. Exits 2 with the remediation command if anything is missing. |
| 2. chunks | `pipelines.sync_engine.build_state(root, skip_embeddings=True)` — scans every skill package into retrieval chunks, in-process. |
| 3. integrity | Compares the freshly computed `chunks_hash` against the committed `vector_index/manifest.json`. A mismatch prints a WARNING and continues — expected when you have local skill edits. |
| 4. write | Writes `vector_index/chunks.jsonl` and `vector_index/lexical.sqlite`. Both are gitignored. |
| 5. commands | Runs `scripts/install_local_commands.py`, copying `commands/*.md` into `.claude/commands/`. |
| 6. verify | Runs `trigger recursion` through the real search path and asserts the top skill is `apex/recursive-trigger-prevention`, and that the installed slash-command count equals the source count. Any failure exits 1. |

It never installs a package, writes to git, touches the network, writes under
`skills/`, `registry/`, `agents/`, `commands/`, `docs/` or `standards/`, or calls
`scripts/skill_sync.py` or `scripts/build_index.py`. `git status` is clean when
it finishes.

### Why bootstrap and not `scripts/build_index.py`

`build_index.py` has no argument parsing — appending `--help` starts a rebuild —
and with an embedding backend installed it encodes every chunk (hours) and
rewrites `vector_embedding` into every `registry/skills/*.json` record, leaving
roughly one modified tracked file per skill to discard. Without a backend it is
a content-identical no-op. Use `bootstrap.py`.

---

## 3. What a fresh clone contains — and what it does not

**Not in the clone (bootstrap builds the first two):**

| Path | Why not committed |
|---|---|
| `vector_index/lexical.sqlite` | Too large for GitHub's file-size limits; a binary that changes wholesale on every rebuild. |
| `vector_index/chunks.jsonl` | Same — regenerated from `skills/`. |
| `vector_index/skill_embeddings.jsonl` | One vector per skill. Built only by `scripts/build_skill_embeddings.py`; see [section 4](#4-embeddings-configured-on-inert-until-you-install-fastembed). |
| `.claude/commands/` | Copies of the tracked `commands/*.md`. Tracking both would create a drift surface. |

`vector_index/embeddings.jsonl`, the chunk-level vector file, is not built by
any default path.

**In the clone:** `vector_index/` ships three files — `manifest.json` (the
integrity hashes for bootstrap phase 3, not a statement about your working
tree), `query-fixtures.json` and `query-variants.json` (retrieval test
fixtures). Under `.claude/`, three subtrees are tracked so a clone is
plugin-usable: `.claude/agents/` (run-time agent loaders), `.claude/skills/`
(routers and rosters) and `.claude/workflows/`. Everything else under `.claude/`
is local session state and gitignored.

### The failure mode if you skip bootstrap

The router path still works without an index; `search_knowledge.py` does not,
and it does not detect a missing index. It prints `Coverage: NONE` and **exits
0**, which is indistinguishable from a library that has nothing on the topic.
Run `python3 scripts/bootstrap.py --verify-only` — it exits non-zero and names
the failed assertion.

---

## 4. Embeddings: configured on, inert until you install fastembed

1. `config/retrieval-config.yaml` sets `embeddings.enabled: true` with
   `backend: fastembed`.
2. `fastembed` is commented out of `requirements.txt`, so a plain
   `pip install -r requirements.txt` does **not** install it.
3. With no backend present, `pipelines/embedding_backends.py` prints a warning
   and falls back to lexical-only.

`scripts/bootstrap.py` also passes `skip_embeddings=True` by default, so the
standard run stays lexical-only even on a machine that has `fastembed`.

### Building the vectors that search actually uses

| File | Vectors | Built by | Read by |
|---|---|---|---|
| `vector_index/skill_embeddings.jsonl` | one per skill | `scripts/build_skill_embeddings.py` | `scripts/search_knowledge.py` and the MCP `search_skill` tool — checked first in `pipelines/ranking.rerank_results` |
| `vector_index/embeddings.jsonl` | one per chunk | `scripts/bootstrap.py --with-embeddings`, `scripts/build_index.py` | the same reranker, only as a fallback |

Almost everyone wants the first one, which takes a minute or two to build:

```bash
python3 -m pip install 'fastembed>=0.4,<1.0'
python3 scripts/build_skill_embeddings.py
```

The file is gitignored. Re-runs re-encode only skills whose summary text changed
(`--force` overrides). `fastembed` pulls in `onnxruntime`, `numpy` and
`tokenizers`, which is why it is not a default dependency. The chunk-level file
is hundreds of megabytes and hours of encode; `search_knowledge.py` loads it
into memory when present.

The skill vectors add a few points of Hit@3 on the held-out keyword-search set;
re-measure with `python3 evals/measurement/run_heldout.py --json` versus
`--no-embeddings` rather than copying a number from a doc.

`--with-embeddings` cannot turn embeddings on by itself: the encoder returns
nothing when the config says `enabled: false`, and bootstrap refuses the
combination with exit 2.

---

## 5. MCP install paths

The server exposes 50 tools over stdio (`python3 scripts/check_doc_counts.py`
prints the live count). Per-client wiring lives in
[`mcp/sfskills-mcp/docs/CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md).

**The Claude Code plugin does not wire the MCP server for you.**
`.claude-plugin/plugin.json` declares no `mcpServers` key. MCP setup is always
the manual step below.

### From a clone (recommended today)

```bash
# after section 1
./.venv/bin/python -m pip install -e mcp/sfskills-mcp
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- /absolute/path/to/AwesomeSalesforceSkills/.venv/bin/python -m sfskills_mcp
```

Register the venv's interpreter by absolute path. A bare `python3` is the system
Python, which does not have `sfskills_mcp` on its path, so the server adds
cleanly and then `claude mcp list` shows `✘ Failed to connect`.
`SFSKILLS_REPO_ROOT` must be absolute and set inside the client's own config
block — an `export` in your shell does not reach a detached subprocess.

### From PyPI

```bash
pip install sfskills-mcp
sfskills-mcp-init          # downloads the data bundle from the latest GitHub Release
```

The data bundle carries the lexical index only, so a PyPI install scores
lexical-only. It serves the corpus its release bundled; to serve your own
checkout, use the clone path above. `python3 -m pip show sfskills-mcp` shows
the installed version.

### The `mcp` SDK pin

`mcp/sfskills-mcp/pyproject.toml` declares `mcp>=1.7.0,<2.0`. Below 1.7.0,
`ToolAnnotations` is missing from `mcp.types`; mcp 2.0 removed the
`mcp.server.fastmcp` module the server imports `Context` and `FastMCP` from.
Lifting the ceiling means porting the server, not bumping a number. If you see
`ModuleNotFoundError: No module named 'mcp.server.fastmcp'`, run
`pip install 'mcp>=1.7.0,<2.0'`.

---

## 6. Cutting a GitHub release (maintainer only)

Owner authorization is a safety gate. An agent may execute this section **only
when the repository owner explicitly authorizes the active task**. This
document is the runbook; it is not standing permission.

Current in-tree versions (checked 2026-10-20; `python3 scripts/check_release_versions.py` prints them):

- Plugin/library: **1.4.0** (`PLUGIN_VERSION` in `scripts/build_plugin.py`)
- sfskills-mcp: **0.5.1** (`pyproject.toml` and `sfskills_mcp.__version__`)

Do not create a separate public GitHub Release for a `plugin-v*` tag.
`sfskills-mcp-init` downloads `/releases/latest/download/sfskills-data.tar.gz`,
so **latest must be an `mcp-v*` release that includes that asset**.

### Why one tag per push

GitHub Actions does not create events when more than three tags are pushed at
once. Push `plugin-v*` and `mcp-v*` **one tag at a time**.
`workflow_dispatch` still cannot attach `sfskills-data.tar.gz` because
`publish-data` is gated on `refs/tags/mcp-v*`.

### Lexical index in the data bundle

`publish-mcp.yml` builds the gitignored lexical index in CI with
`python3 scripts/bootstrap.py --skip-commands` and then
`git diff --exit-code` so tracked registry files are not rewritten. The
tarball includes `chunks.jsonl` and `lexical.sqlite`. Embeddings stay out.

### Steps

1. Confirm `bootstrap.py --skip-commands` is still in
   `.github/workflows/publish-mcp.yml`.
2. Confirm plugin and MCP versions agree with generated manifests and
   changelog headings (`python3 scripts/check_release_versions.py`).
3. Merge to `main` after required GitHub checks pass. Do not force-push or
   bypass protection.
4. Tag and push **one tag per push**:
   ```bash
   git tag -a plugin-v1.4.0 <final-main> -m "SfSkills plugin 1.4.0"
   git push origin plugin-v1.4.0
   git tag -a mcp-v0.5.1 <final-main> -m "sfskills-mcp 0.5.1"
   git push origin mcp-v0.5.1
   ```
5. Watch `publish-mcp.yml`: `gh run watch`.
6. Confirm assets on the MCP release include `sfskills-data.tar.gz`, the
   wheel, the sdist, and `SHA256SUMS.txt`.
7. Confirm latest-download returns HTTP 200:
   ```bash
   curl -sSIL -o /dev/null -w '%{http_code}\n' \
     https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
   ```
8. Clean-room smoke test from public PyPI:
   ```bash
   pip install "sfskills-mcp==0.5.1" && sfskills-mcp-init --force
   ```

---

## 7. Troubleshooting

| Symptom | Go to |
|---|---|
| `error: externally-managed-environment` from pip | [Section 1](#1-install) — use a venv. |
| Claude opened the wrong skill package | [`docs/troubleshooting.md`](./troubleshooting.md#claude-opened-the-wrong-skill-package) — the shipped path has no coverage gate, so this is its characteristic failure. |
| Claude says the topic is not covered | [`docs/troubleshooting.md`](./troubleshooting.md#claude-says-the-topic-is-not-covered) |
| `Coverage: NONE` on every query | [Section 3](#the-failure-mode-if-you-skip-bootstrap) — you have not built the index. |
| Slash commands missing in Claude Code | Run `python3 scripts/bootstrap.py`, then restart Claude Code. |
| Search takes tens of seconds | [`docs/troubleshooting.md`](./troubleshooting.md#search-is-slow-or-appears-to-hang) |
| `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` | [Section 5](#the-mcp-sdk-pin) — pip resolved mcp 2.0.x. |
| MCP server added but `✘ Failed to connect` | [Section 5](#from-a-clone-recommended-today) — register the venv interpreter, not bare `python3`. |
| `sfskills-mcp-init: HTTP 404` | The latest GitHub Release is missing `sfskills-data.tar.gz`; see [Section 6](#6-cutting-a-github-release-maintainer-only) step 6. |
| Client can't find the repo root | [`CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md) — set `SFSKILLS_REPO_ROOT` to an absolute path. |
| Anything else | [`docs/troubleshooting.md`](./troubleshooting.md) |

Related documents:

- [`docs/getting-started.md`](./getting-started.md) — which of the three entry
  points you want.
- [`docs/installing-the-plugin.md`](./installing-the-plugin.md) — Claude Code
  plugin install.
- [`docs/installing-single-agents.md`](./installing-single-agents.md) —
  installing one run-time agent without the whole library.
- [`mcp/sfskills-mcp/docs/CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md) —
  per-client MCP configuration.
