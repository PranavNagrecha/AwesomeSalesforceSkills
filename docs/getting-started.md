# Getting started

Three genuinely different ways to use this library. Pick one; you do not need
all three.

Before you pick, one fact that reorders the whole page: **the main path needs no
build step.** A clone carries `CLAUDE.md`, the 12 router skills under
`.claude/skills/`, their 11 rosters and the 48 run-time agent loaders under
`.claude/agents/` — all tracked in git. Open the directory in Claude Code and
ask a Salesforce question and it works immediately. What a build adds is the
keyword-search layer and the slash commands, and both are optional.

Commands and outputs on this page were executed on an Apple-silicon macOS
machine with Python 3.14.4, dated where the figure matters. Where a command
could not be run in the session it carries an explicit
`> Not measured in this session:` marker naming where the figure came from.

---

## Prerequisites

| Requirement | Why | Check |
|---|---|---|
| `python3` 3.10 or newer | All repo tooling is Python. Not needed at all if you only use the router path. | `python3 --version` returned `Python 3.14.4` |
| `git` | The library is distributed as a repository. | `git --version` |
| ~1 GB free disk | A `git clone --depth 1` is about 130 MB of working tree. The optional retrieval index adds **295 MB** on top (`du -sh vector_index/`). A full-history clone carries a larger `.git` — 479 MB on this checkout. | `df -h .` |
| Salesforce CLI (`sf`) | Optional. Only the org-reading MCP tools need it. Nothing else does. | `sf --version` |

Python dependencies are small — `requirements.txt` is PyYAML and jsonschema
only. Installing them into a clean virtualenv took **1.60 s**:

```text
$ python3 -m pip install -r requirements.txt
$ python3 -m pip list
Package                   Version
------------------------- --------
attrs                     26.1.0
jsonschema                4.26.0
PyYAML                    6.0.3
referencing               0.37.0
rpds-py                   2026.6.3
```

### Time to first useful output

| Entry point | First useful output | Measured |
|---|---|---|
| A — Claude Code, no build | Claude opens the right skill package | **immediate** after clone; nothing to build |
| C — plain export | A tool-native skill tree on disk | **1.2 s** after clone + deps |
| B — MCP server, repo checkout | `search_skill` answering a question | **0.01–0.28 s** per query once warm, once configured |
| A — Claude Code, with local search | `search_knowledge.py` answering a question | **0.5–0.7 s** per query, after a one-time **9 s** index build |

That last row used to read **13–29 s per query**, and this page used to warn
that entry point A was the slowest to reach. Both are obsolete. Commit
`d8c95d5de` removed two loads that dominated the old figure — an unconditional
`load_embeddings()` call worth roughly 2 GB that was never read, and a full
materialisation of `chunks.jsonl` to serve about 30 rows. Re-measured on
2026-08-14:

```text
$ /usr/bin/time -p python3 scripts/search_knowledge.py "trigger recursion"
real 0.49
```

Five runs across three queries landed between **0.49 s and 0.72 s**, at a peak
resident set of 392 MB.

### The two things a fresh clone does not give you

Neither of them stops Claude from finding and reading a skill package.

**1. There is no search index.** `git ls-files vector_index` returns exactly
three files — `manifest.json`, `query-fixtures.json` and `query-variants.json`.
Everything else is gitignored because it totals 295 MB: `chunks.jsonl` at
~124 MB and `lexical.sqlite` at ~165 MB. Until you build them, `scripts/
search_knowledge.py` finds nothing, and it fails *silently*: `search_index` in
`pipelines/lexical_index.py` returns an empty list when the SQLite file is
absent (verified directly —
`search_index(Path('/tmp/no-such-index.sqlite'), 'trigger recursion', None, 30)`
returns `[]`), so the CLI prints `Coverage: NONE` with no chunks and still exits
0. It looks like an empty library. It is not, and mechanism 1 is unaffected.

**2. There are no slash commands.** `.gitignore:131` contains `.claude/*`,
negated for `.claude/agents/`, `.claude/skills/` and `.claude/workflows/` but
not `.claude/commands/`. The tracked command specs live in `commands/`, one file
per command — **67** on this checkout, and `ls commands/*.md | wc -l` is the
live count. Tracking a second copy would create a permanent drift surface
between two copies of the same file, which is why the generated copy is not
committed. `python3 scripts/bootstrap.py` puts them where Claude Code looks.

Both are fixed below.

---

## Entry point A — Claude Code (repo checkout)

### A1. No build step

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
```

Open that directory in Claude Code and ask a Salesforce question. That is the
whole setup.

What happens next is a model-driven roster scan, not a search. Claude reads the
`description:` frontmatter of the 12 routers under `.claude/skills/`, hands off
to one domain router, opens that router's `references/skill-index.md` — a roster
of that domain's packages with one 220-character gloss each — and opens the
package it picks. Eleven rosters carry 1,027 glosses between them; Claude reads
one. No index is consulted and nothing is built.

That indirection is the design, not a workaround. A flat export of all 1,027
skill descriptions would cost **138,334 tokens** at session start before you
type anything. Everything loaded up front here — 12 routers, 67 commands and 48
agent loaders — costs **5,490**, or **4.0%** of that
(`python3 scripts/build_plugin.py --measure`). The token model is an estimate
calibrated against a real Claude Code install; the method and its caveat are in
[architecture.md](architecture.md#why-the-library-is-tiered).

**Verify it worked.** Ask something with an unambiguous home — "how do I stop a
trigger firing twice on the same record?" — and check that Claude opens
`skills/apex/recursive-trigger-prevention/`. If it opens a neighbour instead,
that is mechanism 1's characteristic failure and
[troubleshooting.md](troubleshooting.md) opens with it: this path has no
coverage gate, so it never returns nothing, it returns the wrong package
confidently.

### A2. Add local search and the slash commands

```bash
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap.py
```

About **9 s** on the reference machine. It builds `vector_index/chunks.jsonl`
and `vector_index/lexical.sqlite`, installs the 67 slash commands into
`.claude/commands/`, and writes nothing tracked — `git status` is clean when it
finishes. The full transcript, every flag, and the phase-by-phase breakdown are
in [installing.md §1](installing.md#1-one-command).

> Use `scripts/bootstrap.py`, not `scripts/skill_sync.py --all` or
> `scripts/build_index.py`. The other two rewrite generated artifacts —
> `build_index.py` nulls `vector_embedding` across all 1,027 registry records on
> a fresh clone with no embedding backend, leaving about **1,029 modified
> tracked files** you then have to recognise as noise. `skill_sync.py` is the
> contributor's command, run after editing a skill; `bootstrap.py` is the
> consumer's.

Restart the CLI afterwards. Claude Code loads slash commands at session start,
so `/consolidate-triggers` and the other 66 will not appear until you do.
`/consolidate-triggers` is walked end to end in
[worked-example-trigger-consolidation.md](worked-example-trigger-consolidation.md).

What the build leaves on disk, measured on this checkout with
`ls -la vector_index/`:

| File | Size | Notes |
|---|---:|---|
| `vector_index/lexical.sqlite` | 165 MB | FTS5 index over 132,743 chunks |
| `vector_index/chunks.jsonl` | 124 MB | chunk text |
| `vector_index/skill_embeddings.jsonl` | 5 MB | one vector per skill, 1,027 of them — only present if `fastembed` is installed |

`vector_index/embeddings.jsonl`, the chunk-level vector file that older versions
of this page listed at 535 MB, is **not built by the current pipeline** and is
absent here. See [installing.md §4](installing.md#4-embeddings-configured-on-inert-until-you-install-fastembed).

**Verify it worked.**

```bash
python3 scripts/search_knowledge.py "trigger recursion"
```

Expect `apex/recursive-trigger-prevention` as the only entry under `Top skills:`
and `skills/apex/recursive-trigger-prevention/SKILL.md` as the first line under
`Top chunks:`:

```text
Query: trigger recursion

Top skills:
- apex/recursive-trigger-prevention (2.505)
```

Assert the skill id, not the number. Scores are a tuning output: that same line
printed `6.901` earlier on 2026-07-31 and moved to `2.505` when the displayed
figure became `rank_score` the same afternoon. A different number with the right
skill id means the ranker changed, not that your install is broken. No skills
listed at all, or no chunks, is the real failure — see
[troubleshooting.md](troubleshooting.md), or run `python3 scripts/bootstrap.py
--verify-only`, which unlike `search_knowledge.py` exits non-zero when the index
is missing.

---

## Entry point B — MCP server

Time budget: a couple of minutes once you have a checkout. This is the fastest
search surface at query time and the only way to ask questions about your actual
org.

The package is on PyPI and installs cleanly:

```text
$ python3 -m pip install sfskills-mcp
$ python3 -m pip show sfskills-mcp
Name: sfskills-mcp
Version: 0.4.6
```

The wheel ships small on purpose and does not bundle the corpus. Its documented
bootstrap, `sfskills-mcp-init`, is supposed to download a data bundle from a
GitHub Release. **That path does not work today** — the project has published no
GitHub release carrying `sfskills-data.tar.gz`, re-checked 2026-08-14:

```text
$ gh api repos/PranavNagrecha/AwesomeSalesforceSkills/releases --jq 'length'
0
$ sfskills-mcp-init --cache-dir /tmp/clean-cache
sfskills-mcp-init: HTTP 404 fetching https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
$ echo $?
1
```

So configure the server against a repository checkout and point
`SFSKILLS_REPO_ROOT` at it. Follow entry point A2 first — the MCP server reads
`registry/skills.json` and `vector_index/lexical.sqlite`, so it needs the same
index build.

Claude Code:

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- python3 -m sfskills_mcp
```

Every other client — Claude Desktop, Cursor, Windsurf, Zed, VS Code, Cline,
Continue, Codex CLI, Gemini CLI, Goose, generic stdio — is covered in
[../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md). Tool
schemas are in [../mcp/sfskills-mcp/README.md](../mcp/sfskills-mcp/README.md).

Only the org-reading tools need Salesforce credentials, and they borrow the `sf`
CLI's existing session — nothing is stored by this project:

```bash
sf org login web --alias my-dev
```

### Verify it worked

Call the server's own `health` tool. Run from the checkout:

```bash
SFSKILLS_REPO_ROOT="$PWD" python3 -c "
import sys, json
sys.path.insert(0, 'mcp/sfskills-mcp/src')
from sfskills_mcp import meta
print(json.dumps(meta.health(), indent=2))
"
```

Expected shape, with the values this checkout returned:

```json
{
  "server_version": "0.4.6",
  "mcp_sdk_version": "1.27.0",
  "repo_root": "/Users/.../AwesomeSalesforceSkills",
  "registry": { "path": "registry/skills.json", "skill_count": 1027 },
  "lexical_index": { "path": "vector_index/lexical.sqlite", "byte_size": 173297664 },
  "sf_cli": { "present": true }
}
```

`skill_count` must be non-zero and `lexical_index.byte_size` must be present. If
`repo_root` resolution fails with `RepoRootNotFoundError`, the environment
variable is not reaching the server process — see
[troubleshooting.md](troubleshooting.md).

One honest caveat before you rely on it: the MCP retrieval path and the CLI
retrieval path are still different code.
`mcp/sfskills-mcp/src/sfskills_mcp/skills.py` never calls
`scripts/search_knowledge.py` — it imports the same ranking helpers from
`pipelines` and runs its own shorter pipeline. They agreed on every query tried
on 2026-07-31, because both apply the identical
`max_score >= min_skill_max_score or score >= min_skill_score` gate from
`config/retrieval-config.yaml`, and both embed the query when
`vector_index/skill_embeddings.jsonl` is present (it is on a checkout with
`fastembed` installed — **1,027 vectors**, one per skill):

```text
CLI  "why is my LWC slow" -> lwc/lwc-performance (2.507), coverage granted
MCP  "why is my LWC slow" -> lwc/lwc-performance (2.507), has_coverage true, 0.18 s

CLI  "trigger recursion"  -> apex/recursive-trigger-prevention (2.505)
MCP  "trigger recursion"  -> apex/recursive-trigger-prevention (2.505), 0.14 s

MCP  "xylophone"          -> has_coverage false, 0 skills
```

That agreement is now gated rather than assumed:
`evals/measurement/check_cli_mcp_parity.py --heldout` runs both surfaces over
all 154 held-out queries in CI and fails on any difference.

Two differences survive and can bite you. A PyPI-only install has no vector
files at all, so it scores lexical-only and *will* diverge from a checkout. And
the MCP path does not sanitise the query — `search_skill("100% test coverage")`
raises `sqlite3.OperationalError: fts5: syntax error near "%"` where the CLI
answers. Treat scoring numbers on this page as dated measurements, not as
guarantees. The mechanism is explained in [architecture.md](architecture.md).

---

## Entry point C — Plain export to another tool

Time budget: about a second. No index build, no MCP client, no Salesforce org.
This is the right route for Cursor, Windsurf, Aider, Augment, Codex CLI and
Gemini CLI.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/export_skills.py --target cursor
```

Measured 1.21 s on the first run and 1.51 s on a second, clean run. The tail of
the output:

```text
  + 67 slash command(s) → .cursor/commands/
  1027 skills exported → .../cursor

==================================================
EXPORT COMPLETE
==================================================
  cursor       1027 skills → exports/cursor/
```

The tree it writes for this target is `exports/cursor/.cursor/` containing
`rules/` (1,027 `.mdc` files plus an `INDEX.md`) and `commands/` (one per file
in `commands/`). Copy `exports/cursor/.cursor/` to the root of your project —
copying `exports/` wholesale puts the rules in the wrong place, because the
export writes one subdirectory per target.

Other targets — `claude`, `windsurf`, `aider`, `augment`, `codex`, `agents`,
`mcp` — take the same `--target` flag, and `--all` writes every one. What each
target gains and loses is tabulated in [multi-ai-parity.md](multi-ai-parity.md).

`--domain` and `--skill` narrow the export if 1,027 skills is more than your
tool's context can carry, which it usually is.

### Verify it worked

Compare the export against its own sources rather than against a frozen integer
— both counts move whenever a skill or a command is added:

```bash
# rules should be one per skill, plus INDEX.md
echo "$(ls exports/cursor/.cursor/rules | wc -l) rules vs $(( $(ls skills/*/*/SKILL.md | wc -l) + 1 )) expected"

# commands should be one per spec in commands/
echo "$(ls exports/cursor/.cursor/commands | wc -l) commands vs $(ls commands/*.md | wc -l) expected"
```

Both lines must report two equal numbers. On this checkout the rules line reads
`1028 rules vs 1028 expected`. The commands line reads `66 vs 67` against a
stale export directory and becomes `67 vs 67` after a re-run — which is exactly
the drift this check exists to catch.

---

## Where to go next

- Canonical setup reference, every flag and the maintainer runbook:
  [installing.md](installing.md)
- One complete Salesforce task, end to end, with real output:
  [worked-example-trigger-consolidation.md](worked-example-trigger-consolidation.md)
- What all the pieces are and how they connect, mechanism 1 first:
  [architecture.md](architecture.md)
- Vocabulary this repository assumes you know: [glossary.md](glossary.md)
- Something is wrong: [troubleshooting.md](troubleshooting.md)
