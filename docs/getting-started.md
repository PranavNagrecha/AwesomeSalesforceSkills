# Getting started

**Who this is for:** a first-time user going from install to a first useful
answer, on whichever of the three entry points fits their tool.

Three different ways to use this library. Pick one; you do not need all three.

**The main path needs no build step.** A clone carries `CLAUDE.md`, the router
skills under `.claude/skills/` with their per-domain rosters, and the run-time
agent loaders under `.claude/agents/`, all tracked in git. Open the directory in
Claude Code, ask a Salesforce question, and it works. A build adds the
keyword-search layer and the slash commands; both are optional.

Before you rely on the output: most skill packages have not been claims-audited
against official Salesforce guides yet, and 55 of the 70 run-time agents are
`experimental` (ungraded). [architecture.md](architecture.md) and
[`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md)
say what is checked and what is not.

---

## Prerequisites

| Requirement | Why | Check |
|---|---|---|
| `python3` 3.10 or newer | All repo tooling is Python. Not needed if you only use the router path. | `python3 --version` |
| `git` | The library is distributed as a repository. | `git --version` |
| Free disk | The checkout, plus the optional local search index (the larger of the two). | `df -h .` |
| Salesforce CLI (`sf`) | Optional. Only the org-reading MCP tools need it. | `sf --version` |

Python dependencies are small: `requirements.txt` is PyYAML and jsonschema plus
their transitive dependencies.

### What a fresh clone does not give you

Neither gap stops Claude from finding and reading a skill package.

1. **No search index.** `vector_index/chunks.jsonl` and
   `vector_index/lexical.sqlite` are gitignored. Until you build them,
   `scripts/search_knowledge.py` finds nothing *and still exits 0*, printing
   `Coverage: NONE`. It looks like an empty library; it is a missing index.
2. **No slash commands.** The command specs live in `commands/`, one file per
   command. `.claude/commands/` is not committed;
   `python3 scripts/bootstrap.py` installs the commands there.

---

## Entry point A — Claude Code (repo checkout)

### A1. No build step

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
```

Open that directory in Claude Code and ask a Salesforce question.

What happens next is a model-driven roster scan, not a search. Claude reads the
`description:` frontmatter of the routers under `.claude/skills/`, hands off to
one domain router, opens that router's `references/skill-index.md` (one short
gloss per package) and opens the package it picks. No index is consulted. The
token model behind this layout is in
[architecture.md](architecture.md#why-the-library-is-tiered-at-all).

**Verify it worked.** Ask something with an unambiguous home — "how do I stop a
trigger firing twice on the same record?" — and check that Claude opens
`skills/apex/recursive-trigger-prevention/`. If it opens a neighbour instead,
that is this path's characteristic failure: it has no coverage gate, so it never
returns nothing, it returns the wrong package confidently. See
[troubleshooting.md](troubleshooting.md).

### A2. Add local search and the slash commands

```bash
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap.py
```

It builds `vector_index/chunks.jsonl` and `vector_index/lexical.sqlite`,
installs the slash commands into `.claude/commands/`, and writes nothing
tracked. Every flag is in [installing.md §1](installing.md#1-install).

> Use `scripts/bootstrap.py`, not `scripts/skill_sync.py --all` or
> `scripts/build_index.py`. Those rewrite generated artifacts, and
> `build_index.py` starts the multi-hour embedding pass. `skill_sync.py` is the
> contributor's command, run after editing a skill; `bootstrap.py` is the
> consumer's.

Restart Claude Code afterwards; it loads slash commands at session start.

**Verify it worked.**

```bash
python3 scripts/search_knowledge.py "trigger recursion"
python3 scripts/bootstrap.py --verify-only
```

The first should list `apex/recursive-trigger-prevention` under `Top skills:`.
Assert the skill id, not the score; scores move when the ranker is tuned. The
second exits 1 when the index is missing, unlike `search_knowledge.py`.

---

## Entry point B — MCP server

The MCP server adds read-only tools against your own org on top of skill
search. The Claude Code plugin does not connect it; you register it yourself.

From PyPI:

```bash
pip install sfskills-mcp
sfskills-mcp-init
```

The wheel does not bundle the corpus. `sfskills-mcp-init` downloads the data
bundle `sfskills-data.tar.gz` from the latest GitHub Release. That bundle holds
the lexical index only, so a PyPI install scores lexical-only. Check the
installed version with `python3 -m pip show sfskills-mcp`.

To serve the corpus in your own checkout instead, run entry point A2 first (the
server reads `registry/skills.json` and `vector_index/lexical.sqlite`), install
the package from `mcp/sfskills-mcp`, and point `SFSKILLS_REPO_ROOT` at the
checkout. Claude Code:

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- /absolute/path/to/python -m sfskills_mcp
```

Use the absolute path of the interpreter that has the package installed; a bare
`python3` often adds cleanly and then never connects. Other clients are covered
in [../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md);
tool schemas are in [../mcp/sfskills-mcp/README.md](../mcp/sfskills-mcp/README.md).

The org-reading tools borrow the `sf` CLI's existing session; nothing is stored
by this project:

```bash
sf org login web --alias my-dev
```

**Verify it worked.** Call the server's `health` tool. It returns
`server_version`, `mcp_sdk_version`, `repo_root`, `registry` (with
`skill_count`), `lexical_index` (with `byte_size`), `agents` (counts by class)
and `sf_cli`. `skill_count` must be non-zero and `lexical_index.byte_size` must
be present. A `RepoRootNotFoundError` means `SFSKILLS_REPO_ROOT` is not reaching
the server process — see [troubleshooting.md](troubleshooting.md).

---

## Entry point C — Plain export to another tool

No index build, no MCP client, no Salesforce org. This is the route for Cursor,
Windsurf, Aider, Augment, Codex CLI and Gemini CLI.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/export_skills.py --target cursor
```

For this target it writes `exports/cursor/.cursor/` containing `rules/` (one
`.mdc` file per skill plus an `INDEX.md`) and `commands/` (one per file in
`commands/`). Copy `exports/cursor/.cursor/` to the root of your project;
copying `exports/` wholesale puts the rules in the wrong place.

Other targets — `claude`, `windsurf`, `aider`, `augment`, `codex`, `agents`,
`mcp` — take the same `--target` flag, and `--all` writes every one. What each
target gains and loses is in [multi-ai-parity.md](multi-ai-parity.md).
`--domain` and `--skill` narrow the export when the full corpus is more than your
tool's context can carry, which it usually is.

**Verify it worked.** Compare the export against its own sources:

```bash
# rules: one per skill, plus INDEX.md
echo "$(ls exports/cursor/.cursor/rules | wc -l) rules vs $(( $(ls skills/*/*/SKILL.md | wc -l) + 1 )) expected"
# commands: one per spec in commands/
echo "$(ls exports/cursor/.cursor/commands | wc -l) commands vs $(ls commands/*.md | wc -l) expected"
```

Both lines must report two equal numbers. A stale export directory shows up as a
mismatch.

---

## Where to go next

- Asked to make a Salesforce change rather than answer a question? The
  requirement-to-build loop, told through the example builds:
  [build-loop.md](build-loop.md)
- Every setup flag and the maintainer runbook: [installing.md](installing.md)
- What the pieces are and how they connect: [architecture.md](architecture.md)
- Vocabulary this repository assumes you know: [glossary.md](glossary.md)
- Something is wrong: [troubleshooting.md](troubleshooting.md)
