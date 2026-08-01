# Installing SfSkills as a Claude Code plugin

**Status:** 1.0.0. Generated artifacts are produced by
[`scripts/build_plugin.py`](../scripts/build_plugin.py); the drift gate is
`python3 scripts/build_plugin.py --check`.
**Verified against:** Claude Code v2.1.209 (`claude --version`), by a real
`marketplace add` → `install` → `details` cycle against an isolated
`CLAUDE_CONFIG_DIR` / `CLAUDE_CODE_PLUGIN_CACHE_DIR`.

Schema sources, researched before anything was written:

- <https://code.claude.com/docs/en/plugins-reference> — `plugin.json` fields,
  the `${CLAUDE_PLUGIN_ROOT}` substitution, and the "Path behavior rules"
  section that says `skills` **adds to** the default scan while `commands`,
  `agents`, `workflows` and `outputStyles` **replace** it.
- <https://code.claude.com/docs/en/plugin-marketplaces> — `marketplace.json`
  fields, reserved marketplace names, and the marketplace-root exception under
  "Advanced plugin entries".
- <https://code.claude.com/docs/en/sub-agents> — the `.claude/agents/*.md`
  project-scope subagent format (`name` + `description` frontmatter), which
  the docs say to check into version control.

---

## Install

### From GitHub (normal path)

Inside Claude Code:

```
/plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills
/plugin install sfskills@sfskills
```

Non-interactively, from a shell:

```bash
claude plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills
claude plugin install sfskills@sfskills
```

### From a local clone

The repository is its own marketplace, so a clone works as a source with no
extra setup:

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
claude plugin marketplace add ./AwesomeSalesforceSkills
claude plugin install sfskills@sfskills
```

Inside Claude Code the same pair is:

```
/plugin marketplace add ./AwesomeSalesforceSkills
/plugin install sfskills@sfskills
```

### Verify

```bash
claude plugin details sfskills
```

Expected on v2.1.209: `Skills (78)`, `Agents (0)`, and an always-on cost of
about 2,889 tokens. `Agents (0)` is expected — see
[Known limitations](#known-limitations).

---

## Why the plugin is tiered

A flat export is not an option. Claude Code loads every skill's `name` and
`description` into the system prompt at session start, before the user types
anything.

```bash
python3 -c "import json,math; d=json.load(open('registry/skills.json')); \
  c=sum(len(s['name'])+len(s['description']) for s in d['skills']); \
  print(d['skill_count'],'skills;',c,'chars;',math.ceil(c/4),'tokens')"
# 1027 skills; 535737 chars; 133935 tokens
```

134k tokens of index before the first question. So the library ships in three
tiers, and only Tier 1 is always-on. The per-tier figures below come from
`--measure`; Claude Code's own accounting reports a slightly higher 2,889
(both are in the [table](#measured-cost) that follows).

```
Tier 1  ALWAYS ON      12 router skills           1,470 tok
        (2,723 tok)    66 slash commands          1,253 tok
                              │
                              │  router teaches the model to look up,
                              │  then read by path
                              ▼
Tier 2  ON DEMAND      1,027 skill packages      0 tok until opened
                       ${CLAUDE_PLUGIN_ROOT}/skills/<domain>/<slug>/SKILL.md
                              │
                              ▼
Tier 3  ON INVOCATION  48 run-time agents        0 tok until invoked
                       .claude/agents/<id>.md → agents/<id>/AGENT.md
```

### Measured cost

| | Skills loaded | Always-on tokens | Share of a flat export |
|---|---:|---:|---:|
| Flat export of all 1,027 packages | 1,027 | 133,935 | 100% |
| **This plugin (Claude Code's own accounting)** | **78** | **~2,889** | **2.16%** — a 46x reduction |
| This plugin (`--measure`, `ceil(chars/4)` model) | 78 | 2,723 | 2.03% — a 49x reduction |

Reproduce the first two rows with:

```bash
claude plugin details sfskills          # reads "Always-on:  ~2,889 tok"
python3 scripts/build_plugin.py --measure
```

`--measure` exits 1 if Tier 1 crosses 6,000 tokens or 5% of the flat-export
cost, so a router that grows a paragraph fails the build rather than quietly
taxing every session.

For reference, the requirements pass measured **2,671** always-on tokens on a
synthetic probe (12 routers with 450-character descriptions plus the 65
commands that existed at the time). The shipped artifacts measure higher
because the real router descriptions are longer and a 66th command has since
landed. Both numbers agree to within 8%, and both are ~2% of a flat export.

---

## What the manifests do, and why

### `.claude-plugin/marketplace.json`

The entry's `source: "./"` and `skills: ["./.claude/skills/"]` are a pair, and
both halves are load-bearing.

- **`source: "./"`** puts the whole repository into the plugin cache, so
  `${CLAUDE_PLUGIN_ROOT}/skills/`, `/scripts/`, `/standards/` and `/templates/`
  all resolve. A narrower source would leave the routers pointing at nothing.
- **`skills: ["./.claude/skills/"]`** triggers the marketplace-root exception.
  Per plugin-marketplaces, "Advanced plugin entries": *"With a marketplace-root
  `source`, the listed paths are the complete set for that entry, and other
  directories in the shared `skills/` folder don't load."* This is the only
  mechanism that keeps the 1,027 Tier-2 packages out of the always-on index.
  Without it, `skills` merely **adds** to the default scan.

The doc adds a trap worth knowing: *"If none of the listed paths exist, the
default scan runs instead."* That is why the router files must be tracked in
git — see [Known limitations](#known-limitations).

### `.claude-plugin/plugin.json`

Carries the metadata and the same `skills` path. It deliberately omits two
keys:

- **No `agents`.** Measured on v2.1.209: a custom `agents` file path loads
  zero agents, a directory value is rejected with `agents: Invalid input`,
  and because `agents` *replaces* the default scan, declaring it at all
  disables the plugin-root `agents/*.md` path that does work. The full probe
  table is in [Known limitations](#1-the-agents-load-as-project-scope-subagents-not-as-plugin-agents).
- **No `commands`.** `commands` also replaces its default scan. Omitting it
  lets the default `commands/` scan load all 66 existing command files
  unchanged.

### Validation

```bash
claude plugin validate .
```

`claude plugin validate` **exits 0 even when it prints `Validation failed`**,
so gate on its output, not its exit code:

```bash
claude plugin validate . 2>&1 | grep -c 'Validation failed'   # must be 0
```

---

## Regenerating the artifacts

Everything under `.claude-plugin/`, `.claude/skills/` and `.claude/agents/` is
generated. Do not hand-edit it.

```bash
python3 scripts/build_plugin.py                 # build in place
python3 scripts/build_plugin.py --check         # drift gate; exit 1 on any diff
python3 scripts/build_plugin.py --measure       # token budget; exit 1 if over
python3 scripts/build_plugin.py --verify-seeds  # resolve the curated seed table
```

The single hand-authored input is the seed table at the top of
`scripts/build_plugin.py`: 5–10 featured skills per domain, the per-domain
decision-tree pointers, and the trigger vocabulary. Every seed is resolved
against `registry/skills.json` **and** the filesystem at build time, so a
renamed or deleted skill fails the build instead of shipping a dead path.
The domain list, skill counts, rosters, agent set and both manifests are
derived.

If you add a router or a run-time agent, re-run the build **and** re-add the
new files with `git add -f` (see the `.gitignore` note below).

---

## Known limitations

Each of these was measured on Claude Code v2.1.209; none is a guess.

### 1. The agents load as project-scope subagents, not as plugin agents

`claude plugin details sfskills` reports `Agents (0)`. The plugin `agents`
field is defective at v2.1.209, measured on a four-case throwaway probe
(a minimal plugin, its own marketplace, an isolated config each time):

| `plugin.json` `agents` value | Result |
|---|---|
| omitted — default `agents/*.md` scan | `Agents (1)  flat-agent` |
| `["./custom-agents/custom-agent.md"]` | `Agents (0)` |
| `["./custom-agents/"]` (a directory) | `claude plugin validate` → `agents: Invalid input`, `Validation failed` |
| `["./agents/flat-agent.md"]` — the file the default scan just loaded | `Agents (0)` |

So the only working plugin path is a flat `agents/*.md` directory at the
plugin root with **no** `agents` key, and declaring the key breaks even that.
This repository's `agents/` holds 76 `AGENT.md` *packages*, not flat files, so
that path is unavailable without restructuring a directory this change does
not own.

The wrappers therefore ship to `.claude/agents/`, the documented project-scope
location per <https://code.claude.com/docs/en/sub-agents>. Practical effect:

- **Clone the repo and work inside it** → all 48 subagents are available.
- **Install the plugin from a remote marketplace** → the 12 routers and 66
  slash commands work; the subagents do not appear in the subagent picker.
  The agent playbooks are still reachable by path at
  `${CLAUDE_PLUGIN_ROOT}/agents/<id>/AGENT.md`, and every domain router names
  the agents for its domain.

Revisit when the plugin `agents` field works.

### 2. `.gitignore` excludes `.claude/*`, so the generated files need `git add -f`

`.gitignore` ignores `.claude/*` and negates only `.claude/workflows/`, so any
*new* file under `.claude/skills/` or `.claude/agents/` is ignored the moment
it is written. The 71 current files are tracked only because they were
force-added:

```bash
git add -f .claude/skills .claude/agents
```

Ignore rules never apply to tracked paths, so `git check-ignore` now reports
them as not ignored — but a brand-new sibling still is:

```bash
git check-ignore -q .claude/skills/salesforce/SKILL.md; echo $?   # 1 = tracked, not ignored
touch .claude/skills/probe.md
git check-ignore -q .claude/skills/probe.md; echo $?              # 0 = ignored
```

**So any new router or subagent added by a later build is silently dropped
unless it is force-added too.** The durable fix is a two-line `.gitignore`
amendment, which was outside this change's file ownership:

```gitignore
!.claude/skills/
!.claude/agents/
```

This matters more than it looks: if none of a marketplace entry's declared
skill paths exist in the fetched source, Claude Code falls back to the default
scan — which would silently ship a plugin with the wrong skill set.

### 3. `vector_index/` is not shipped, so `search_knowledge.py` needs a one-time build

`vector_index/chunks.jsonl`, `vector_index/lexical.sqlite` and
`vector_index/embeddings.jsonl` are gitignored (126 MB / 166 MB / 535 MB on
disk here), so an installed copy has no retrieval index and
`scripts/search_knowledge.py` cannot run. Only `vector_index/manifest.json`
and the query fixtures are tracked.

Build it once per clone, from the repository root (a clone, or the plugin's
cache directory — `claude plugin details sfskills` prints its path):

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build_index.py
```

Until then — and this is the normal case for anyone installing from GitHub —
the **zero-setup path is the shipped roster**. Every domain router ships
`references/skill-index.md`, a complete list of that domain's packages with a
one-line gloss each, generated from `registry/skills.json` (which *is*
tracked). The routers list it first for exactly this reason, ahead of the
`sfskills-mcp` `search_skill` tool and the search CLI.

### 4. The clone is heavy

| What | Size |
|---|---|
| Tracked working tree | 80.7 MB across 9,229 files |
| `.git` | 524 MB (`size-pack` 389.86 MiB) |
| Plugin cache after a **local** install | 1.7 GB |

A **local-path** install copies the entire working tree — including gitignored
`vector_index/` (805 MB) and `exports/` (252 MB) — into the plugin cache,
which is where the 1.7 GB comes from. A **GitHub** install never sees those,
because untracked files are not cloned; it pays the ~390 MiB pack fetch
instead. Neither number is small, but GitHub is the cheaper of the two.

Reproduce:

```bash
git ls-files -z | xargs -0 stat -f '%z' | awk '{s+=$1} END {print s/1048576" MB"}'
git count-objects -vH | grep size-pack
```

### 5. All 66 commands ship, including deprecated aliases

The default `commands/` scan is all-or-nothing without a `commands` allowlist,
and the `commands/` files are not owned by this change. So 1.0.0 ships all 66,
including the 9 files marked `LEGACY ALIAS` (`grep -lc 'LEGACY ALIAS'
commands/*.md`) and the build-time commands (`/new-skill`, `/new-agent`,
`/build-skills`, `/onboard-source`, `/sync-upstream-skills`, …) that are
meaningless to someone who installed the plugin to *use* the library.
Collectively the commands are 1,253 of the 2,723 tokens `--measure`
attributes to Tier 1 — 46% of the budget. Trimming them is follow-up work,
and needs the same empirical check the `agents` field got, because a
`commands` allowlist is untested here.

---

## What you get

| Tier | Component | Count | Where |
|---|---|---:|---|
| 1 | Top-level router skill | 1 | `.claude/skills/salesforce/` |
| 1 | Domain router skills | 11 | `.claude/skills/salesforce-<domain>/` |
| 1 | Slash commands | 66 | `commands/` (default scan) |
| 2 | Skill packages | 1,027 | `skills/<domain>/<slug>/` |
| 2 | Domain rosters (on-invoke) | 11 | `.claude/skills/salesforce-*/references/skill-index.md` |
| 3 | Run-time subagents | 48 | `.claude/agents/` |

The 11 domains and their skill counts: admin 253, apex 158, architect 104,
data 101, lwc 82, devops 70, flow 63, integration 61, agentforce 53,
security 48, omnistudio 34 — 1,027 total.

Each router carries, for its domain: the three lookup mechanisms in
reliability order, 8 curated featured skills with a reason each, the relevant
decision trees from `standards/decision-trees/`, the canonical templates from
`templates/<domain>/` where one exists (admin, agentforce, apex, flow, lwc),
and the run-time agents that cover it. A router is a map, not the territory —
it never answers a Salesforce question itself.

## Uninstall

```bash
claude plugin uninstall sfskills
claude plugin marketplace remove sfskills
```
