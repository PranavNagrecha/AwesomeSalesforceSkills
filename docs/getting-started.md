# Getting started

Three genuinely different ways to use this library. Pick one; you do not need
all three.

Every command on this page was executed on 2026-07-31 on an Apple-silicon
macOS machine with Python 3.14.4, and the output shown is the output that came
back. Where a command could not be run in that session it carries an explicit
`> Not measured in this session:` marker naming where the figure came from.

---

## Prerequisites

| Requirement | Why | Check |
|---|---|---|
| `python3` 3.10 or newer | All repo tooling is Python. | `python3 --version` returned `Python 3.14.4` |
| `git` | The library is distributed as a repository. | `git --version` |
| ~2.5 GB free disk | `.git` alone is 524 MB (`du -sh .git`); the generated retrieval index adds ~830 MB more. | `df -h .` |
| Salesforce CLI (`sf`) | Optional. Only the org-reading MCP tools need it. Nothing else does. | `sf --version` |

Python dependencies are small — `requirements.txt` is PyYAML and jsonschema
only. Installing them into a clean virtualenv took **1.60 s**:

```
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
| C — plain export | A tool-native skill tree on disk | **1.2 s** after clone + deps |
| B — MCP server, repo checkout | `search_skill` answering a question | **0.01–0.28 s** per query once warm, once configured |
| A — Claude Code / CLI search | `search_knowledge.py` answering a question | **13–29 s** per query, **after** a one-time index build |

Read that table before choosing. Entry point A is the one most people expect
to be fastest and is in fact the slowest to reach, because local CLI search
needs an index that is not in the repository.

### The two things a fresh clone does not give you

**1. There is no search index.** `.gitignore` excludes
`vector_index/lexical.sqlite`, `vector_index/chunks.jsonl`,
`vector_index/embeddings.jsonl` and `vector_index/skill_embeddings.jsonl`
— together about 832 MB, past GitHub's file-size limits. Until you build
them, retrieval finds nothing. The `search_index` helper in
`pipelines/lexical_index.py` returns an empty list when the SQLite file is
absent (verified directly:
`search_index(Path('/tmp/no-such-index.sqlite'), 'trigger recursion', None, 30)`
returned `[]`), so `scripts/search_knowledge.py` prints
`Coverage: NONE` with no chunks and still exits 0. It looks like an empty
library. It is not.

**2. There are no slash commands.** `.gitignore` contains `.claude/*`
(negated only for `.claude/workflows/`), and `git ls-files .claude/commands`
returns 0 files. The tracked command specs live in `commands/`, one file per
command — 66 of them when this page was written, and
`ls commands/*.md | wc -l` is the live count.
`python3 scripts/install_local_commands.py` is what puts them where Claude
Code looks.

Both are fixed below.

---

## Entry point A — Claude Code (repo checkout)

Time budget: minutes for the clone and deps, then a one-time index build that
dominates everything else.

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m pip install -r requirements.txt
python3 scripts/skill_sync.py --all
python3 scripts/install_local_commands.py
```

`skill_sync.py --all` is the step the repository's own quick-start omits. It
rebuilds `registry/`, `vector_index/` and `docs/SKILLS.md` from the skill
packages.

> Not measured in this session: the wall-clock of `python3 scripts/skill_sync.py --all`.
> House rules for this session forbade running it, because it rewrites shared
> generated artifacts. The figures published in-repo are:
> `config/retrieval-config.yaml` records **2:20** for a full chunk-level
> encode of 126,618 chunks on an M-series CPU, with subsequent builds
> re-encoding only changed chunks via a content hash;
> `requirements.txt` notes the fastembed cold start is **~14 s**, per-query
> overhead **~50 ms** once warm, and a full corpus encode **2–3 h on CPU**
> for machines without that acceleration.

What the build leaves on disk, measured in this checkout:

| File | Size | Notes |
|---|---:|---|
| `vector_index/embeddings.jsonl` | 535.0 MB | 384-dim vector per chunk |
| `vector_index/lexical.sqlite` | 166.1 MB | FTS5 index, 130,062 chunks |
| `vector_index/chunks.jsonl` | 126.2 MB | chunk text |
| `vector_index/skill_embeddings.jsonl` | 5.1 MB | one vector per skill |

`install_local_commands.py` copies `commands/` into `.claude/commands/`. The
first number it prints is `len(src_names)` — the count of `commands/*.md`, not
a constant — and the counters read `updated` when the files are already there,
`added` on a fresh clone:

```
$ python3 scripts/install_local_commands.py
installed 66 commands to .claude/commands/  (added=0 updated=66 removed=0)
Note: Claude Code loads slash commands at session start. Restart your CLI for new commands to register.
```

> Not re-run in this session: house rules for this session forbade writing
> outside `docs/`. The line above is what
> `scripts/install_local_commands.py:63-66` prints for the state verified on
> this checkout — `ls commands/*.md | wc -l` is 66 and `.claude/commands/`
> already holds the same 66 filenames, so every file is an update. On a fresh
> clone the same run reads `(added=66 updated=0 removed=0)`.

Restart the CLI afterwards, as the note says.

Claude Code then picks the repository up through `CLAUDE.md` automatically.
The slash commands become available — one per file in `commands/`;
`/consolidate-triggers` is walked end to end in
[worked-example-trigger-consolidation.md](worked-example-trigger-consolidation.md).

### Verify it worked

```bash
python3 scripts/search_knowledge.py "trigger recursion"
```

Expect `apex/recursive-trigger-prevention` as the only entry under
`Top skills:`, and `skills/apex/recursive-trigger-prevention/SKILL.md` as the
first line under `Top chunks:`:

```
Query: trigger recursion

Top skills:
- apex/recursive-trigger-prevention (2.505)
```

Assert the skill id, not the number. Scores are a tuning output: that same
line printed `6.901` earlier on 2026-07-31, and moved to `2.505` when the
displayed figure became `rank_score` the same afternoon. A different number
with the right skill id means the ranker changed, not that your install is
broken. No skills listed at all, or no chunks, is the real failure — see
below.

Wall-clock for that query on a warm page cache measured 13.14 s, 15.34 s and
17.37 s across three runs on 2026-07-31. Other queries the same day:
`"why is my LWC slow"` 17.73 s and 18.77 s,
`"permission sets" --domain admin` 19.32 s and 29.25 s,
`python3 scripts/search_skills.py "trigger firing twice"` 14.80 s. Plan for
**13–29 s** warm. On a cold page cache earlier the same day the same commands
measured 52 s to 90 s, and one run competing with an index rebuild took
83.08 s. The cost is process startup reading a 535 MB
`vector_index/embeddings.jsonl` and a 126 MB `vector_index/chunks.jsonl` on
every invocation; see [faq.md](faq.md).

If you get `Coverage: NONE` and no chunks at all, the index was never built —
go back to `python3 scripts/skill_sync.py --all`. See
[troubleshooting.md](troubleshooting.md).

---

## Entry point B — MCP server

Time budget: a couple of minutes once you have a checkout. This is the fastest
surface at query time by two orders of magnitude, and the one to use for real
work.

The package is on PyPI and installs cleanly:

```
$ python3 -m pip install sfskills-mcp
$ python3 -m pip show sfskills-mcp
Name: sfskills-mcp
Version: 0.4.6
```

The wheel ships small on purpose and does not bundle the corpus. Its
documented bootstrap, `sfskills-mcp-init`, is supposed to download a data
bundle from a GitHub Release. **That path does not work today** — the project
has published no GitHub release carrying `sfskills-data.tar.gz`:

```
$ sfskills-mcp-init --cache-dir /tmp/clean-cache
sfskills-mcp-init: downloading https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
sfskills-mcp-init: HTTP 404 fetching https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
  Verify the release tag exists: https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases
$ echo $?
1
```

So configure the server against a repository checkout and point
`SFSKILLS_REPO_ROOT` at it. Follow Entry point A first (the MCP server reads
`registry/skills.json` and `vector_index/lexical.sqlite`, so it needs the same
index build).

Claude Code:

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- python3 -m sfskills_mcp
```

Every other client — Claude Desktop, Cursor, Windsurf, Zed, VS Code, Cline,
Continue, Codex CLI, Gemini CLI, Goose, generic stdio — is covered in
[../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md).
Tool schemas are in [../mcp/sfskills-mcp/README.md](../mcp/sfskills-mcp/README.md).

Only the org-reading tools need Salesforce credentials, and they borrow the
`sf` CLI's existing session — nothing is stored by this project:

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
  "lexical_index": { "path": "vector_index/lexical.sqlite", "byte_size": 166060032 },
  "sf_cli": { "present": true }
}
```

`skill_count` must be non-zero and `lexical_index.byte_size` must be present.
If `repo_root` resolution fails with `RepoRootNotFoundError`, the environment
variable is not reaching the server process — see
[troubleshooting.md](troubleshooting.md).

One honest caveat before you rely on it: the MCP retrieval path and the CLI
retrieval path are still different code.
`mcp/sfskills-mcp/src/sfskills_mcp/skills.py` never calls
`scripts/search_knowledge.py` — it imports the same ranking helpers from
`pipelines` and runs its own shorter pipeline. They agreed on every query
tried on 2026-07-31, because both now apply the identical
`max_score >= min_skill_max_score or score >= min_skill_score` gate from
`config/retrieval-config.yaml`, and both embed the query when
`vector_index/skill_embeddings.jsonl` is present (it is, on a checkout — 994
vectors):

```
CLI  "why is my LWC slow" -> lwc/lwc-performance (2.507), coverage granted, 18.77 s
MCP  "why is my LWC slow" -> lwc/lwc-performance (2.507), has_coverage true,  0.18 s

CLI  "trigger recursion"  -> apex/recursive-trigger-prevention (2.505), 17.37 s
MCP  "trigger recursion"  -> apex/recursive-trigger-prevention (2.505),  0.14 s

MCP  "xylophone"          -> has_coverage false, 0 skills
```

Two differences survive and can bite you. A PyPI-only install has no vector
files at all, so it scores lexical-only and *will* diverge from a checkout.
And the MCP path does not sanitise the query — `search_skill("100% test
coverage")` raises `sqlite3.OperationalError: fts5: syntax error near "%"`
where the CLI answers. Treat scoring numbers on this page as dated
measurements, not as guarantees. The mechanism is explained in
[architecture.md](architecture.md).

---

## Entry point C — Plain export to another tool

Time budget: about a second. No index build, no MCP client, no Salesforce
org. This is the genuinely fastest route to something useful on disk, and the
right one for Cursor, Windsurf, Aider, Augment, Codex CLI and Gemini CLI.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/export_skills.py --target cursor
```

Measured 1.21 s on the first run and 1.51 s on a second, clean run. The tail
of the output:

```
  + 66 slash command(s) → .cursor/commands/
  1027 skills exported → .../cursor

==================================================
EXPORT COMPLETE
==================================================
  cursor       1027 skills → exports/cursor/
```

The tree it writes for this target is `exports/cursor/.cursor/` containing
`rules/` (1,027 `.mdc` files plus an `INDEX.md`) and `commands/` (one per file
in `commands/`, 66 at the time of writing): **1,094 files, 23.3 MB**. Copy
`exports/cursor/.cursor/` to the root of your project.

Other targets — `claude`, `windsurf`, `aider`, `augment`, `codex`, `agents`,
`mcp` — take the same `--target` flag, and `--all` writes every one. What each
target gains and loses is tabulated in [multi-ai-parity.md](multi-ai-parity.md).

`--domain` and `--skill` narrow the export if 1,027 skills is more than your
tool's context can carry, which it usually is.

### Verify it worked

Compare the export against its own sources rather than against a frozen
integer — both counts move whenever a skill or a command is added:

```bash
# rules should be one per skill, plus INDEX.md
echo "$(ls exports/cursor/.cursor/rules | wc -l) rules vs $(( $(ls skills/*/*/SKILL.md | wc -l) + 1 )) expected"

# commands should be one per spec in commands/
echo "$(ls exports/cursor/.cursor/commands | wc -l) commands vs $(ls commands/*.md | wc -l) expected"
```

Both lines must report two equal numbers. On this checkout on 2026-07-31 that
was `1028 rules vs 1028 expected` and `66 commands vs 66 expected`.

---

## Where to go next

- One complete Salesforce task, end to end, with real output:
  [worked-example-trigger-consolidation.md](worked-example-trigger-consolidation.md)
- What all the pieces are and how they connect: [architecture.md](architecture.md)
- Vocabulary this repository assumes you know: [glossary.md](glossary.md)
- Something is wrong: [troubleshooting.md](troubleshooting.md)
