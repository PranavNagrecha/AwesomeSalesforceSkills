# Installing SfSkills as a Claude Code plugin

The generated artifacts come from
[`scripts/build_plugin.py`](../scripts/build_plugin.py); the drift gate is
`python3 scripts/build_plugin.py --check`. The shipped version is whatever
`.claude-plugin/plugin.json` says — read it there rather than from this page.

**Verified against:** Claude Code 2.1.209 (`claude --version`). Every install
figure on this page was re-measured on **2026-08-15** by a real
`marketplace add` → `install` → `details` cycle run from **outside** this
repository against a throwaway `CLAUDE_CONFIG_DIR`, using a **local-path**
marketplace source. The GitHub source resolves the default branch and is
documented but untested here. Every probe plugin is named `sfskills`, matching
the real plugin — [a name mismatch is what corrupted an earlier
calibration](#what-the-previous-constants-got-wrong-and-why-it-is-instructive).

**Read [Verify the plugin path](#verify-the-plugin-path) before trusting any
check** — "it works when I'm in the repo" proves nothing about the plugin.

One branch note. This working tree carries **67** commands; `origin/main` still
carries 66, because `commands/add-skill.md` has not been pushed yet. Every
figure below is the working tree's. Confirm which you are looking at:

```bash
ls commands/*.md | wc -l                              # 67  (this tree)
git ls-tree -r --name-only origin/main commands/ | wc -l   # 66  (default branch)
```

Schema sources, researched before anything was written and re-fetched
2026-08-15:

- <https://code.claude.com/docs/en/plugins-reference> — `plugin.json` fields,
  `${CLAUDE_PLUGIN_ROOT}`, and the component-path table. Verbatim: `skills` is
  *"Custom skill directories containing `<name>/SKILL.md`. Adds to the default
  `skills/` scan."*; `commands` is *"Custom flat `.md` skill files or
  directories (replaces default `commands/`)"*; `agents` is *"Custom agent files
  (replaces default `agents/`)"*. And: *"All paths must be relative to the
  plugin root and start with `./`, except that the `skills` field also accepts
  `"."`"*. Nothing here depends on that exception; both declared paths use `./`.
- <https://code.claude.com/docs/en/plugin-marketplaces> — `marketplace.json`
  fields and the marketplace-root exception under "Advanced plugin entries",
  verbatim: *"With a marketplace-root `source`, the listed paths are the
  complete set for that entry, and other directories in the shared `skills/`
  folder don't load. Listing `./skills/` itself, or the plugin root, keeps the
  full scan. If none of the listed paths exist, the default scan runs instead."*
- <https://code.claude.com/docs/en/sub-agents> — the `.claude/agents/*.md`
  project-scope subagent format (`name` + `description` frontmatter). **Project
  scope is not plugin scope**, which is why the same 48 loaders are generated
  twice, to two different paths — see
  [Known limitation 1](#1-the-agents-manifest-key-does-not-work-in-any-form).
- <https://code.claude.com/docs/en/plugins> — namespacing and precedence,
  verbatim: *"Plugin skills are always namespaced (like `/my-first-plugin:hello`)
  to prevent conflicts when multiple plugins have skills with the same name. To
  change the namespace prefix, update the `name` field in `plugin.json`."* and
  *"Project and user `.claude/agents/` definitions override same-named plugin
  agents, so the plugin version only takes effect once the originals are
  removed. Plugin skills are namespaced as `/plugin-name:skill-name`, so the
  original `/skill-name` and the plugin copy both remain available rather than
  one overriding the other."*

---

## Install

> **The GitHub install path works.** An earlier revision of this page said the
> manifests were not yet on the default branch and that both recipes were
> blocked. That has not been true for some time — every payload the plugin
> declares is on `main`. Check it yourself:
>
> ```bash
> git ls-tree origin/main .claude-plugin/                     # 2 manifests
> git ls-tree -r --name-only origin/main .claude/skills/ | wc -l   # 23 files = 12 routers + 11 rosters
> git ls-tree -r --name-only origin/main commands/ | wc -l        # 66 on main, 67 here
> git ls-tree -r --name-only origin/main .claude/agents/ | wc -l  # 48 loaders
> ```

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
extra setup. `.claude-plugin/` is on the default branch, so a plain clone is
enough — no branch switch. A local path is the source type every measurement on
this page used:

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
claude plugin marketplace add ./AwesomeSalesforceSkills
claude plugin install sfskills@sfskills
```

Use this form when you want to install a working tree you are editing, so
`build_plugin.py` output is picked up without pushing first.

Inside Claude Code the same pair is:

```
/plugin marketplace add ./AwesomeSalesforceSkills
/plugin install sfskills@sfskills
```

Run these from a directory that is **not** the clone. Installing from inside the
repository works, but it makes the result impossible to read: project-local
loading supplies the same routers, so you cannot tell which mechanism you are
seeing. The next section is how to tell.

### The plugin does not ship an MCP server

`.claude-plugin/plugin.json` declares no `mcpServers` key, and a clean install
reports `MCP servers (0)`. Search through the `sfskills-mcp` `search_skill` tool
is a separate, manual setup — see
[installing.md §5](./installing.md#5-mcp-install-paths). Nothing on this page
depends on it: the zero-setup lookup path is the shipped roster.

---

## Verify the plugin path

This is the section that matters. Claude Code loads `.claude/skills/` and
`.claude/agents/` **from your current working directory** whenever you are
sitting in a trusted project, plugin or no plugin. So if you check the install
from inside a clone of this repository, you will see routers and subagents appear
whether or not the plugin manifest works at all. An earlier "verified working"
claim on this repository was exactly that mistake: what had been observed was
project-local loading, and the plugin was shipping zero agents.

The trap did not go away when the agents started shipping — it got quieter. Both
copies now exist and are byte-identical, and the project-local one takes
precedence inside a clone, so a broken plugin copy would look exactly like a
working one from in here. Only `plugin details`, from outside, can tell.

Two mechanisms, two different pieces of evidence:

| | Project-local loading | Plugin loading |
|---|---|---|
| Trigger | your cwd is a trusted dir containing `.claude/` | `claude plugin install` |
| Reads | `<cwd>/.claude/skills/`, `<cwd>/.claude/agents/` | the plugin cache copy: `.claude/skills/` per the manifest, `agents/*.md` by default scan |
| Survives `cd` to an unrelated directory | no | yes |
| Shows in `claude plugin details` | no | yes |
| Invocation name in a session | bare (`/salesforce`) | namespaced (`/sfskills:salesforce`) |
| Wins when both are present | **yes**, for same-named agents | no |

The last two rows come from the plugins doc quoted above. Note that
`claude plugin details` prints the **bare** names in its inventory; the namespace
shows up where you invoke them.

### The check that cannot be faked

Run it from a directory that is **not** this repository and has no `.claude/` of
its own. The `CLAUDE_CONFIG_DIR` override keeps the whole exercise out of your
real configuration, so a failed experiment cannot leave a half-installed plugin
behind.

```bash
export CLAUDE_CONFIG_DIR="$(mktemp -d)"      # throwaway config
cd "$(mktemp -d)"                            # NOT the repo, no .claude/ here

claude plugin marketplace add /absolute/path/to/AwesomeSalesforceSkills   # the working tree
claude plugin install sfskills@sfskills --scope user
claude plugin details sfskills
```

What proves the plugin path worked, measured 2026-08-15 on 2.1.209 (abridged —
`details` also prints a per-component table):

```text
SfSkills — Salesforce AI Skill Library (sfskills) 1.0.0
  1,027 grounded Salesforce skill packages, 48 run-time agents and 67 slash commands, reached through 12 lightweight router skills instead of a flat index.
  Source: sfskills@sfskills

Component inventory
  Skills (79)  add-skill, analyze-field-impact, analyze-flow, … salesforce, salesforce-admin, … sync-upstream-skills
  Agents (48)  lwc-debugger, flow-builder, email-template-modernizer, … changeset-builder
  Hooks (0)
  MCP servers (0)
  LSP servers (0)

Projected token cost
  Always-on:   ~5,490 tok   added to every session
```

Read it like this:

- **`Source: sfskills@sfskills`** — `plugin details` only knows about installed
  plugins. Project-local `.claude/` never appears here, so any output at all is
  already plugin-path evidence.
- **`Skills (79)`** — 12 routers from `.claude/skills/` plus 67 from
  `commands/`. Both arrive through manifest keys; see
  [What the manifests do](#what-the-manifests-do-and-why). This reads 78 against
  `origin/main`, which has 66 commands.
- **`Agents (48)`** — the flat `agents/<id>.md` loaders, through Claude Code's
  default scan. No manifest key is involved, and none would help; see
  [Known limitation 1](#1-the-agents-manifest-key-does-not-work-in-any-form).
  This number was `0` until 2026-08-07.
- **`MCP servers (0)`** — expected. The plugin declares none.
- **`Always-on: ~5,490 tok`** — Claude Code's own accounting for what the install
  adds to every session. [Measured cost](#measured-cost) carries the breakdown.

`claude plugin list` should report `Status: ✔ enabled` alongside this:

```text
$ claude plugin list
Installed plugins:

  ❯ sfskills@sfskills
    Version: 1.0.0
    Scope: user
    Status: ✔ enabled
```

A plugin whose manifest is malformed reports `✘ failed to load` here while its
components may still appear to work in a session — because project-local loading
picked them up. Treat `plugin list` and `plugin details` as the source of truth,
never the presence of a skill in a session.

Tear the experiment down:

```bash
claude plugin uninstall sfskills
claude plugin marketplace remove sfskills
rm -rf "$CLAUDE_CONFIG_DIR"; unset CLAUDE_CONFIG_DIR
```

### The repo-side gate

The same expectation is encoded so it cannot drift:

```text
$ python3 scripts/build_plugin.py --audit-install
Projected inventory of an INSTALLED sfskills plugin
  Skills     79   (12 router(s) from ./.claude/skills/ + 67 command(s) from ./commands/)
  Agents     48   (flat *.md under agents/, the only form that loads)

Repo inventory
  skill packages     1027   reached on demand by path, not loaded up front
  run-time agents      48
  slash commands       67

OK: every component this repo defines is reachable through the plugin.
$ echo $?
0
```

It projects the installed inventory from the repo's own files, prints it beside
the repo inventory, and exits 1 for every component the repo defines that the
plugin cannot deliver. Its `Skills 79 / Agents 48` projection matches what
`claude plugin details` reports. It also compares the two loader sets
byte-for-byte and fails if they diverge, because that divergence is invisible
from inside a clone.

The projection is a model of the loader, not a reading of it. It agreeing with
the CLI is evidence, not proof — when in doubt, run the install.

---

## Why the plugin is tiered

A flat export is not an option. Claude Code loads every skill's `name` and
`description` into the system prompt at session start, before the user types
anything.

```text
$ python3 -c "import json,math; d=json.load(open('registry/skills.json')); \
    c=sum(len(s['name'])+len(s['description']) for s in d['skills']); \
    print(d['skill_count'],'skills;',c,'chars;',math.ceil(c/4),'tokens')"
1027 skills; 544507 chars; 136127 tokens
```

136k tokens of index before the first question — and that raw figure ignores the
`sfskills:` namespace prefix each name would carry, which is why `--measure`
reports the like-for-like flat export slightly higher at **138,694**.

So the library ships in three tiers, and only the frontmatter of Tier 1 is
always-on. An agent's `name` + `description` is always-on too; only its *body* is
deferred, the same as a skill's. Calling Tier 3 "0 tok until invoked" was wrong,
and it stopped being harmless the moment the 48 loaders started shipping.

```
Tier 1  ALWAYS ON      12 router skills           1,921 tok
        (5,490 tok)    67 slash commands          1,412 tok
                       48 agent loaders           2,157 tok  ← frontmatter only
                              │
                              │  router teaches the model to look up,
                              │  then read by path
                              ▼
Tier 2  ON DEMAND      1,027 skill packages      0 tok until opened
                       ${CLAUDE_PLUGIN_ROOT}/skills/<domain>/<slug>/SKILL.md
                       11 domain rosters         0 tok until read
                       (largest is admin, 253 entries, 68 KB ≈ 17k tok)
                              │
                              ▼
Tier 3  ON INVOCATION  48 agent playbooks        0 tok until invoked
                       agents/<id>.md → agents/<id>/AGENT.md
                       (the loader is Tier 1; the playbook it points at
                        is Tier 3 — ~370 tok each, on invoke)
```

The three tiers sum to 5,490.2 and the whole plugin reports 5,490 — additive to
within the single rounding step. An earlier version of this document reported
the tiers as **sub-additive by 75 tokens** and called that "unexplained". It was
not a property of Claude Code; it was a defect in the measurement. See
[Re-calibrating the token model](#re-calibrating-the-token-model).

### Measured cost

| | Skills loaded | Always-on tokens | Share of a flat export |
|---|---:|---:|---:|
| Flat export of all 1,027 packages | 1,027 | 138,694 | 100% |
| **This plugin (Claude Code's own accounting, 2026-08-15)** | **79 + 48 agents** | **5,490** | **3.96%** — a 25x reduction |
| This plugin (`--measure`, closed-form prediction) | 79 + 48 agents | 5,490 | 3.96% |
| Same plugin before the 2026-08-07 rework | 78 + 48 agents | 6,118 | 4.4% |
| Same plugin before the agents shipped | 78 | ~2,889 | 2.1% |

Prediction and measurement agree exactly on the current files. Reproduce the
first two rows with:

```bash
claude plugin details sfskills          # reads "Always-on:  ~5,490 tok"
python3 scripts/build_plugin.py --measure
```

#### The budget, and why it is not raised

`--measure` exits 1 if Tier 1 crosses 6,000 tokens or 5% of the flat-export
cost. It exits **0** today, at 5,490 predicted / 5,546 after the safety margin,
with **454 tokens of headroom**.

It did not always. On 2026-08-07 the plugin measured 6,118 — 118 over the cap —
and the fix was the cost, not the ceiling. Do not reach for
`BUDGET_TIER1_TOKENS`: the budget is the only thing standing between this plugin
and the flat export it exists to avoid, and a ceiling raised to meet the cost
measures nothing. What was actually cut:

1. **The 48 generated agent descriptions: 3,229 → 2,157 tok.** All 48 shared a
   **188-character longest common suffix** ("reads its full AGENT.md playbook,
   cites every skill consulted, returns a confidence score, and never deploys to
   an org. Invoke for the whole workflow, not a single lookup."). That is
   188 × 48 = 9,024 characters ≈ 2,256 tok — over a third of the entire
   always-on bill, spent on text identical across every loader and therefore
   discriminating between none of them. (An earlier revision said 203 chars /
   9,744 / 2,436 tok. Those figures were never measured.) The shared suffix is
   now **64 characters**, and part of the saving was spent back on
   discrimination — each description names its slash command, because
   `/refactor-apex` and the agent id `apex-refactorer` are different strings and
   the command is what a user types. Median description length went 247 → **158.5**
   characters. Both current figures are re-derivable from `agents/*.md`
   frontmatter:

   ```text
   n = 48
   median len = 158.5
   longest common suffix len = 64
   suffix = ': reads its AGENT.md playbook, cites its sources, never deploys.'
   ```

2. **The correction to the command model.** Not a saving — the old figure was
   simply wrong. See below.

The 67 commands remain the obvious next lever if one is ever needed: an
allowlist in `PLUGIN_COMMANDS_PATH` would drop the 9 deprecated aliases and the
build-time commands that mean nothing to someone who installed the library to
*use* it. That is optional rather than urgent.

#### The token model

`--measure` no longer estimates. It computes:

```
always_on(component) = 0.25 × (len(qualified_name) + len(description)) + 0.25
```

summed over every component, rounded **once** at the end. Where:

- `qualified_name` is `"<plugin>:<name>"` for **skills and commands**, and the
  bare `"<name>"` for **agents** — agents are not namespaced.
- `description` is the frontmatter `description` for skills and agents; for a
  command it is the **full H1 text** (everything after `# `), hard-truncated at
  **100 characters**.

Nine probe plugins, Claude Code 2.1.209, 2026-08-07, each installed from a
local-path marketplace into a throwaway `CLAUDE_CONFIG_DIR` from outside this
repository. Every prediction was written down before the probe ran. The table is
kept in sync inside the `AGENT_LOADING_MATRIX` / token-model comment block at
the top of `scripts/build_plugin.py`:

| Probe | Predicted | Measured | What it establishes |
|---|---:|---:|---|
| A1 · 10 skills, plugin `sfskills` (8 ch), desc 100 | 280 | **280** | baseline |
| A2 · 10 skills, plugin `sfskillsabcd` (12 ch), desc 100 | 290 | **290** | skills **are** namespaced (+4 name chars × 10 × 0.25) |
| A3 · 10 skills, plugin `sfskills`, desc 300 | 780 | **780** | slope is exactly 0.25 tok/char |
| B1 · 10 agents, plugin `sfskills`, desc 100 | 258 | **258** | bare name (namespaced would be 280) |
| B2 · 10 agents, plugin `sfskillsabcd`, desc 100 | 258 | **258** | agents are **not** namespaced — unchanged by plugin name |
| C1 · 10 commands, H1 = `/cN — ` + 50 chars | 170 | **170** | the **full H1** is billed (stripped subtitle would be 155) |
| C2 · 10 commands, H1 length 146 | 280 | **280** | truncated |
| C3 · 10 commands, H1 length 100 | 280 | **280** | cap is exactly |
| C4 · 10 commands, H1 length 101 | 280 | **280** | 100 characters |
| **R · replica of the Tier-1 files as they stood on 2026-08-07** | **6117.8** | **6,118** | 126 real components, variable-length |

Row R is the acid test: real, variable-length descriptions predicted to a tenth
of a token. It replicated the **pre-rework** files, which is why its figure is
6,118 rather than today's 5,490 — a previous revision of this page mislabelled R
as `5386.8 / 5,387`, conflating the probe with a later whole-plugin reading. The
model's current validation is simpler and stronger: `--measure` predicts 5,490
and `claude plugin details` reports 5,490 on the same files.

#### What the previous constants got wrong, and why it is instructive

The superseded model hard-coded `SKILL_OVERHEAD_TOKENS = 3`,
`AGENT_OVERHEAD_TOKENS = 1`, `COMMAND_OVERHEAD_TOKENS = 9` as "measured per-tier
intercepts", and this document presented a per-tier table built from them. Both
were wrong, in a way worth recording:

- **Each tier was probed under a different plugin name.** The router probe was
  called `tierrouters` (11 chars) and the command probe `tiercommands` (12),
  while the real plugin is `sfskills` (8). Since skills and commands are billed
  as `<plugin>:<name>`, those extra name characters were absorbed into what
  looked like per-component structural overhead. It is exactly why the "agent
  overhead" came out near zero — agents are not namespaced, so their probe had no
  qualifier to misattribute.
- **The same artifact produced the "unexplained 75-token sub-additivity."**
  12 skills × 3 extra name chars × 0.25 = 9, plus 66 commands × 4 × 0.25 = 66,
  plus 0 for agents = **75 exactly**. Re-measured with all three tiers under the
  name `sfskills`, they are additive. There is no sub-additivity.
- **The command cap was reported as "~90 characters."** It is exactly 100 — the
  earlier probe only swept 100/120/160/200/400, which cannot distinguish 90 from
  100. And commands are billed against the **whole H1**, not the
  `/slug — `-stripped subtitle; charging the subtitle under-reads by ~1.5 tok per
  command.

The lesson is not "those numbers were off." It is that a probe whose *name*
differs from the subject measures the name.

#### Re-calibrating the token model

The model lives at the top of `scripts/build_plugin.py` (`TOKENS_PER_CHAR = 0.25`,
`COMPONENT_INTERCEPT_TOKENS = 0.25`, `COMMAND_DESCRIPTION_CHARS = 100`,
`SAFETY_MARGIN_RATIO = 0.01`, `BUDGET_TIER1_TOKENS = 6000`, `MEASURED_REFERENCE`).
If a Claude Code upgrade changes the accounting, **re-derive it, do not nudge
it**:

```bash
# STEP 1, AND DO NOT SKIP IT: name the probe plugin exactly "sfskills".
# Skills and commands are billed as "<plugin>:<name>", so a probe under any
# other name measures the name difference and reports it as per-component
# overhead. This is the specific mistake that produced the constants this
# section replaced.
export CLAUDE_CONFIG_DIR="$(mktemp -d)"
cd /somewhere/outside/the/repo
claude plugin marketplace add /absolute/path/to/probe-plugin
claude plugin install sfskills@sfskills --scope user
claude plugin details sfskills        # the "Always-on:" line is the answer
rm -rf "$CLAUDE_CONFIG_DIR"; unset CLAUDE_CONFIG_DIR
```

Sweep one variable at a time, holding the others fixed, and read the slope off
two points rather than fitting an intercept to one. Then build a **replica**
probe from the real Tier-1 files and confirm the model predicts the whole
install — a model that fits every synthetic sweep and misses the replica is still
wrong. The per-component table `plugin details` prints is rounded (to the nearest
10, and to `< 20` below that) and cannot be used for any of this; it was tried,
and the rounding bands are wide enough to admit both a correct and an incorrect
model.

`SAFETY_MARGIN_RATIO` is the **one** explicit margin, applied once to the total.
It replaced three fitted per-tier intercepts. It is headroom against a future
accounting change, not a correction for a model that does not fit — `--measure`
reports the exact prediction and the padded figure separately, and gates on the
padded one.

---

## What the manifests do, and why

Both manifests are valid JSON. Validate them, and treat `--strict` as the real
gate, because that is what the community-marketplace review pipeline runs:

```bash
claude plugin validate .            # exit 1 on rejection, 0 on pass-with-warnings
claude plugin validate . --strict   # exit 1 on warnings too
```

A clean tree prints `✔ Validation passed` for both. Measured exit codes on
2.1.209: `1` when a manifest is rejected (for example `agents: Invalid input`),
`0` when it passes with warnings, `1` for those same warnings under `--strict`.
Pointed at this repository the validator resolves
`.claude-plugin/marketplace.json` and reports problems inside the referenced
`plugin.json` prefixed with the entry index (`plugins[0] plugin.json → …`).

**The version in `plugin.json` and the version in the marketplace entry must
agree.** They are written by the same build, so the only way they diverge is a
hand-edit — and the failure is quiet, because a plain `validate` still passes:

```text
$ claude plugin validate . --strict
⚠ Found 1 warning:

  ❯ plugins[0].version: Entry declares version "1.0.0" but .claude-plugin/plugin.json says "1.0.1".
    At install time, plugin.json wins (calculatePluginVersion precedence) — the entry version is
    silently ignored. Update this entry to "1.0.1" to match.

✘ Validation failed (--strict treats warnings as errors)
```

`python3 scripts/build_plugin.py --check` catches the same thing as
`differs: .claude-plugin/plugin.json`, and `claude plugin tag` refuses outright.
The fix is always `python3 scripts/build_plugin.py`, never editing one file to
match the other.

### `.claude-plugin/marketplace.json`

The entry's `source: "./"` and `skills: ["./.claude/skills/"]` are a pair, and
both halves are load-bearing.

- **`source: "./"`** puts the whole repository into the plugin cache, so
  `${CLAUDE_PLUGIN_ROOT}/skills/`, `/scripts/`, `/standards/` and `/templates/`
  all resolve. A narrower source would leave the routers pointing at nothing.
- **`skills: ["./.claude/skills/"]`** triggers the marketplace-root exception
  quoted at the top of this page: with a marketplace-root `source`, the listed
  paths are the complete set. This is the only mechanism that keeps the 1,027
  Tier-2 packages out of the always-on index. Without it, `skills` merely **adds**
  to the default scan.

The doc adds a trap worth knowing: *"If none of the listed paths exist, the
default scan runs instead."* That is why the router files must be tracked in git
— see [Known limitation 2](#2-claudecommands-is-not-tracked-and-does-not-need-to-be).

### `.claude-plugin/plugin.json`

Carries the metadata plus exactly two component paths:

- **`skills: ["./.claude/skills/"]`** — the 12 routers, as above.
- **`commands: ["./commands/"]`** — the 67 slash commands, loaded from the
  tracked repo-root `commands/`, which is where the canonical files already live.
  `commands` *replaces* its default scan, but naming the default folder
  explicitly is the documented way to declare it without losing it. Measured:
  `Skills (79)`. The key is there so the manifest states what it ships rather
  than relying on an implicit default.

It deliberately omits **`agents`**, and declares no `mcpServers`, `hooks` or
`.lsp.json`. Measured on 2.1.209, every custom-path form of the `agents` key
loads zero agents, and because it *replaces* the default scan, declaring it also
disables the one path that does work. The 48 agents ship through that default
scan instead — flat `agents/<id>.md` at the plugin root, generated by the same
build. The probe matrix is in
[Known limitation 1](#1-the-agents-manifest-key-does-not-work-in-any-form).

### The description string is derived, not typed

Both manifests build their description from `_inventory_phrase()` in
`scripts/build_plugin.py`, and every number in it comes from what an install
actually exposes — `registry/skills.json` for the package count, the `commands/`
file count for the command count, and the flat `agents/*.md` set the build emits
for the agent count. The agent clause is **omitted while that set is empty**, so
before 2026-08-07 the description made no agent claim at all. It started saying
"48 run-time agents" on its own the moment the loaders were emitted — nobody
typed the number. Likewise, the command count moved from 66 to 67 by itself when
`commands/add-skill.md` landed.

The agent count comes from the build's **output map**, not from a filesystem scan
and not from the agent roster. That matters for two reasons: a manifest rendered
from pre-build disk state would describe the *previous* build and `--check` would
report drift on the next run; and deriving it from the roster would let the
manifest claim 48 agents even if the loader emit were deleted.

---

## Regenerating the artifacts

Everything under `.claude-plugin/`, `.claude/skills/` and `.claude/agents/` is
generated, and so are the flat `agents/*.md` loaders at the repository root. Do
not hand-edit any of it.

Note the split inside `agents/`: the build owns the flat `agents/<id>.md` loaders
**that it wrote**, and nothing else there. The `agents/<id>/AGENT.md` packages
and `agents/_shared/` are hand-authored and are never touched — the stale-file
sweep over that directory is deliberately non-recursive and `*.md`-only, since a
recursive prune would delete the agent library.

The sweep is narrower than that glob, because the glob alone would make the build
own every top-level `agents/*.md` — a hand-authored `agents/README.md` would then
be silently unlinked by the next build. So a candidate is pruned only if it
carries the marker line `render_subagent()` stamps into every loader
(`GENERATED_MARKER` in `scripts/build_plugin.py`, the literal string
``**Generated by `scripts/build_plugin.py`. Do not hand-edit.**``). A
hand-authored file dropped into `agents/` survives, and is not reported as drift
by `--check`.

```bash
python3 scripts/build_plugin.py                 # build in place
python3 scripts/build_plugin.py --check         # drift gate; exit 1 on any diff
python3 scripts/build_plugin.py --measure       # token budget; exit 1 if over
python3 scripts/build_plugin.py --verify-seeds  # resolve the curated seed table
python3 scripts/build_plugin.py --audit-install # installed inventory; exit 1 on a gap
```

What a clean tree looks like:

```text
$ python3 scripts/build_plugin.py --check
OK: 121 plugin artifact(s) match a fresh build — no drift
$ python3 scripts/build_plugin.py --verify-seeds
OK: 102 curated seed(s) resolved, 0 unresolved
```

`--check` names each artifact that diverges and exits 1. Any hand-edit under
`.claude-plugin/`, `.claude/skills/`, `.claude/agents/` or the flat
`agents/*.md` will show up here:

```text
$ python3 scripts/build_plugin.py --check
DRIFT: the committed plugin artifacts do not match a fresh build:
  - differs: .claude-plugin/plugin.json

To fix: python3 scripts/build_plugin.py
```

The single hand-authored input is the seed table at the top of
`scripts/build_plugin.py`: featured skills per domain, the per-domain
decision-tree pointers, and the trigger vocabulary — 102 seeds today. Each of
the 11 domain routers ends up with exactly 8 featured entry points; the
top-level `salesforce` router has none, because it only hands off. Every seed is
resolved against `registry/skills.json` **and**
the filesystem at build time, so a renamed or deleted skill fails the build
instead of shipping a dead path. The domain list, skill counts, rosters, agent
set and both manifests are derived.

If you add a router, re-run the build **and** re-add the new files with
`git add -f` (`.claude/` is ignored by default; see the note below). A new
run-time agent needs no `-f`: `agents/` is not ignored, so its flat loader shows
up in `git status` normally, but its `.claude/agents/` twin does need the
negation that is already in place.

---

## Known limitations

Each of these was measured on Claude Code 2.1.209; none is a guess.

### 1. The `agents` manifest key does not work in any form

The agents ship — `claude plugin details sfskills` reports `Agents (48)` — but
not through anything you can declare. The `agents` manifest key is inert at
2.1.209, so the loaders have to sit exactly where the default scan looks and the
manifest has to stay silent about them.

**Probe procedure**, if you want to re-derive the table on a newer Claude Code.
Build a throwaway plugin directory with its own `.claude-plugin/marketplace.json`
and `plugin.json`, one flat `agents/foo.md` with `name` + `description`
frontmatter, and whichever `agents` key the row under test declares. Then, for
each row: `export CLAUDE_CONFIG_DIR="$(mktemp -d)"`, `cd "$(mktemp -d)"`,
`claude plugin validate <probe dir>`, `claude plugin marketplace add <probe dir>`,
`claude plugin install <name>@<name> --scope user`, `claude plugin details <name>`,
then `rm -rf "$CLAUDE_CONFIG_DIR"`. A fresh config directory per row is what stops
one row's install from colouring the next.

| Where declared | Value | `validate` | `plugin details` | Re-verified |
|---|---|---|---|---|
| — (omitted) | flat `agents/foo.md` at plugin root | pass | `Agents (1)  foo` | **2026-08-15** |
| — (omitted) | only `agents/x/AGENT.md`, no flat file | pass | `Agents (0)` | 2026-08-07 |
| `plugin.json` | `["./custom-agents/"]` (directory) | **`agents: Invalid input`**, exit 1 | install refused | **2026-08-15** |
| `plugin.json` | `["./custom-agents/a.md"]` | pass | `Agents (0)` | 2026-08-07 |
| `plugin.json` | `["./.claude/agents/a.md"]` | pass | `Agents (0)` | 2026-08-07 |
| `plugin.json` | `["./agents/foo.md"]` — the file the default scan just loaded | pass | `Agents (0)` | **2026-08-15** |
| marketplace entry | `["./.claude/agents/a.md"]` | pass | `Agents (0)` from the key (the 1 seen was still the default scan) | 2026-08-07 |
| marketplace entry | `["./.claude/agents/"]` (directory) | **`plugins.0.agents: Invalid input`** | — | 2026-08-07 |
| marketplace entry | any of the above with `strict: false` | pass | plugin **fails to load**: *"conflicting manifests: both plugin.json and marketplace entry specify components"* | 2026-08-07 |

The row that most needs re-checking on an upgrade is row 6, and it is
counter-intuitive enough to be worth pasting. Declaring the key at the exact
path the default scan had just loaded from turns the agent off:

```text
# probeA — no `agents` key, flat agents/foo.md
Component inventory
  Skills (0)
  Agents (1)  foo

# probeC — identical tree, plus "agents": ["./agents/foo.md"] in plugin.json
Component inventory
  Skills (0)
  Agents (0)
```

Two conclusions. The only mechanism that ships a subagent is a flat `*.md`
**directly inside `<plugin root>/agents/`**; and declaring the key suppresses even
that, so omitting it is strictly better.

That collided with this repository's layout. `agents/` holds 76 `<id>/AGENT.md`
*packages* — row 2 shows the flat scan skips those — and until 2026-08-07 the 48
generated loaders lived only at `.claude/agents/`, the **project-scope** location.
Claude Code reads that path for anyone whose cwd is this repo, plugin or not.
That is precisely why the plugin once looked like it shipped agents when it
measured `Agents (0)`.

**What ships now.** `scripts/build_plugin.py` writes each loader twice, from a
single `render_subagent()` call:

| Path | Mechanism | Who sees it |
|---|---|---|
| `agents/<id>.md` | plugin default scan | anyone who installs the plugin |
| `.claude/agents/<id>.md` | project scope | anyone whose cwd is a clone |

Both sets are 48 files with byte-identical contents, sitting beside — never
instead of — the `agents/<id>/AGENT.md` playbooks they load. Verified directly:

```bash
for f in agents/*.md; do cmp -s "$f" ".claude/agents/$(basename $f)" || echo "DIFF $f"; done
# compared=48 differing=0
```

**Why two copies, and why generated.** Per the plugins doc quoted at the top,
project and user `.claude/agents/` definitions override same-named plugin agents.
Inside a clone the project copy therefore always wins, and the plugin copy is
never exercised — so if the two ever diverged, no amount of testing from inside
the repo would reveal it. Generating both from one call is what makes divergence
impossible; `--check` and `--audit-install` are what prove it stayed that way.

The duplication is deliberate, not redundancy to clean up. Deleting
`.claude/agents/` would break the clone workflow; deleting `agents/*.md` would
put `Agents (0)` back.

**What this still costs.** The 48 loaders add 2,157 always-on tokens, 39% of the
Tier-1 bill — see [Measured cost](#measured-cost). And the manifest can never
advertise them: the `agents` key stays absent, so anyone reading `plugin.json`
alone sees no agent declaration at all. The `description` string names them; the
component list does not.

### 2. `.claude/commands/` is not tracked, and does not need to be

The plugin's slash commands ship from the tracked repo-root `commands/`, which
`.claude-plugin/plugin.json` declares as `"commands": ["./commands/"]`. When
`.claude/commands/` is current, its files are byte-for-byte identical to
`commands/` (`cmp` clean on all 67), so tracking the second copy would add a
permanent drift surface and buy nothing. `.claude/commands/` stays gitignored as
a local editor convenience, regenerated by `python3 scripts/bootstrap.py`.

The evidence is `Skills (79)` on a clean install from outside the repo: 12
routers plus all 67 commands, including `review`, `new-skill`, `refactor-apex`
and the rest.

`.claude/skills/` and `.claude/agents/` **are** tracked, and their `.gitignore`
negations are in place (`.gitignore:131` is `.claude/*`; lines 132–134 negate
`agents/`, `skills/` and `workflows/`), so a new file written by a later build
shows up normally rather than being silently dropped:

```text
$ touch .claude/skills/__probe.md .claude/agents/__probe.md
$ git status --short .claude/
?? .claude/agents/__probe.md
?? .claude/skills/__probe.md
$ rm .claude/skills/__probe.md .claude/agents/__probe.md
```

`??` means untracked **and addable** — an ignored path would not be listed at
all. This matters more than it looks: if none of a marketplace entry's declared
skill paths exist in the fetched source, Claude Code falls back to the default
scan, which would silently ship a plugin with the wrong skill set.

The flat `agents/*.md` loaders need no negation. `agents/` was never ignored, so
they behave like any other tracked file. They do, however, need to be
*committed*: a GitHub install fetches only tracked files, so an uncommitted
loader means `Agents (0)` for everyone installing that way.

### 3. `vector_index/` is not shipped, so `search_knowledge.py` needs a one-time build

`vector_index/chunks.jsonl` and `vector_index/lexical.sqlite` are gitignored
(134 MB / 177 MB after a build, 310 MB for the whole directory), so a **GitHub**
install has no retrieval index and `scripts/search_knowledge.py` cannot answer.
Only `vector_index/manifest.json` and the two query-fixture files are tracked.
The chunk-level `vector_index/embeddings.jsonl` that older revisions of this page
costed at 535 MB is not built by any default path and does not exist on disk;
`fastembed` plus `scripts/build_skill_embeddings.py` adds `skill_embeddings.jsonl`
at 5.3 MB instead.

Build it once per clone, from the repository root — or from the plugin's cache
directory, whose path `claude plugin details sfskills` prints:

```bash
git check-ignore -q .venv || echo '.venv/' >> .git/info/exclude   # .venv/ is NOT in .gitignore
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/bootstrap.py
```

Use `bootstrap.py`, not `scripts/build_index.py`: it also installs the slash
commands, has a real `--help`, and never invokes an encoder. A plain
`python3 -m pip install -r requirements.txt` fails under PEP 668 on Homebrew and
distro Pythons — see
[troubleshooting.md](./troubleshooting.md#pip-install--r-requirementstxt-fails-externally-managed-environment).

Until then — and this is the normal case for anyone installing from GitHub — the
**zero-setup path is the shipped roster**. Every domain router ships
`references/skill-index.md`, a complete list of that domain's packages with a
one-line gloss each, generated from `registry/skills.json` (which *is* tracked).
The routers list it first for exactly this reason, ahead of the `sfskills-mcp`
`search_skill` tool and the search CLI.

Because the roster is the primary lookup path rather than a fallback, the gloss is
generated to discriminate rather than to summarise. The package id is already on
the line, so a gloss that restates the name is dead weight; instead each gloss
carries, in priority order, the package's own **trigger vocabulary**, its
**`NOT for X - use Y` redirect**, and a scope phrase if there is room. The
previous rule — "first sentence, truncated to 120 characters" — kept the least
useful third: measured over all 1,027 packages it cut 923 (89.9%) of them
**mid-word** and opened 673 (65.5%) with "Use when" boilerplate. It also dropped
the literal trigger `'why can user see too much'` from
`admin/sharing-and-visibility` and the `(use admin/duplicate-management)`
redirect from `data/large-scale-deduplication` — both of which had been observed
causing a wrong pick in a fresh-clone routing test.

The current budget is `MAX_GLOSS_CHARS = 220`, with mid-word truncation
eliminated and every cut placed on a word, keyword or whole-clause boundary and
marked with `…`. Rosters are Tier 2, so this costs nothing always-on; it costs
more to *read* one. The worst case is `admin` at 253 packages. The sweep that
chose 220, quoted from the `MAX_GLOSS_CHARS` block in `scripts/build_plugin.py`:

| `MAX_GLOSS_CHARS` | admin roster | ~tok to read it | full triggers kept | cross-reference kept |
|---|---:|---:|---:|---:|
| 120 (the old rule) | 43.8 KB | 11.2k | n/a | n/a |
| 180 | 57.0 KB | 14.6k | 54% | 55% |
| **220 (chosen)** | 67.3 KB | 17.2k | 54% | 67% |
| 240 | 71.8 KB | 18.4k | 54% | 79% |

220 is where both measured routing failures resolve, and past it the curve is
still rising but no longer buys a known failure. Those roster sizes are from
that sweep and grow with the corpus; the live figures today are **70,112 bytes**
for `admin` and **304 KB** across all eleven, carrying 1,027 gloss entries
between them — only one of which is ever read for a given question:

```bash
ls -l .claude/skills/salesforce-admin/references/skill-index.md   # 70112 bytes
du -ch .claude/skills/*/references/skill-index.md | tail -1       # 304K total
grep -c '^- ' .claude/skills/*/references/skill-index.md | awk -F: '{s+=$2} END {print s}'   # 1027
```

`MAX_ROSTER_BYTES` caps a roster at 80 KiB, so `admin` has room but not room for
another doubling.

### 4. The clone is heavy, and a local install is heavier

Re-measured 2026-08-15. These drift with every commit — re-run the commands
below rather than trusting the table.

| What | Size |
|---|---|
| Tracked working tree | 87.00 MB across 9,324 files |
| `.git` | 489 MB (`size-pack` 406.68 MiB) |
| Plugin cache after a **local** install | 1.2 GB |

```bash
git ls-files | wc -l                                    # 9324
git ls-files -z | xargs -0 stat -f '%z' | awk '{s+=$1} END {print s/1048576" MB"}'
                                                        # 87.0045 MB
git count-objects -vH | grep size-pack                  # size-pack: 406.68 MiB
du -sh .git                                             # 489M
du -sh "$CLAUDE_CONFIG_DIR/plugins/cache"               # 1.2G, after a local install
```

A **local-path** install copies the entire working tree, gitignored files
included, into `<CLAUDE_CONFIG_DIR>/plugins/cache/<marketplace>/<plugin>/<version>/`.
Measured contents of that cache, largest first:

```text
301M  vector_index      gitignored, copied anyway
253M  exports           gitignored, copied anyway
 81M  skills
 19M  knowledge
 15M  registry
```

`.git` is **not** copied. A **GitHub** install never sees the gitignored
directories either, because untracked files are not cloned; it pays the
~407 MiB pack fetch instead. If you install locally and the 1.2 GB matters,
clear `exports/` and `vector_index/` first — neither is needed by the plugin
itself, only by the search CLI.

### 5. All 67 commands ship, including deprecated aliases

`"commands": ["./commands/"]` names the whole directory, and the `commands/`
files are not owned by this change. So the plugin ships all 67, including the 9 files
marked `LEGACY ALIAS` and the build-time commands (`/new-skill`, `/new-agent`,
`/build-skills`, `/onboard-source`, `/sync-upstream-skills`, `/add-skill`, …)
that are meaningless to someone who installed the plugin to *use* the library.

```bash
grep -l 'LEGACY ALIAS' commands/*.md | wc -l    # 9
```

Collectively the commands cost 1,412 of the 5,490 always-on tokens Claude Code
bills for this plugin — 26%, behind the 48 agent loaders at 2,157 (39%) and
ahead of the routers at 1,921 (35%).

Trimming them is follow-up work rather than urgent: Tier 1 is **under** its 6,000
cap with 454 tokens of headroom (see
[The budget, and why it is not raised](#the-budget-and-why-it-is-not-raised)).
The commands remain the largest block that could be cut without losing a
component anyone installed the plugin for. The mechanism is known rather than
untested: the field accepts a mixed array of directories and individual files —
the plugin-marketplaces "Advanced plugin entries" example is literally
`["./commands/core/", "./commands/enterprise/", "./commands/experimental/preview.md"]`
— so an allowlist is a matter of listing the keepers in `PLUGIN_COMMANDS_PATH`.
Re-measure with `claude plugin details` afterwards; the `Skills (n)` count is the
check.

---

## What you get

| Tier | Component | Count | Where |
|---|---|---:|---|
| 1 | Top-level router skill | 1 | `.claude/skills/salesforce/` |
| 1 | Domain router skills | 11 | `.claude/skills/salesforce-<domain>/` |
| 1 | Slash commands | 67 | `commands/` (declared) |
| 1 | Run-time subagent loaders | 48 | `agents/<id>.md` (plugin scope) + `.claude/agents/<id>.md` (project scope) — [why both](#1-the-agents-manifest-key-does-not-work-in-any-form) |
| 2 | Skill packages | 1,027 | `skills/<domain>/<slug>/` |
| 2 | Domain rosters (on-invoke) | 11 | `.claude/skills/salesforce-*/references/skill-index.md` |
| 3 | Run-time agent playbooks | 48 | `agents/<id>/AGENT.md` — read on invocation by the loader |

The 11 domains and their skill counts: admin 253, apex 158, architect 104,
data 101, lwc 82, devops 70, flow 63, integration 61, agentforce 53,
security 48, omnistudio 34 — 1,027 total. (`registry/skills.json` is the source;
`python3 scripts/check_doc_counts.py` fails the build if this line drifts.)

Each router carries, for its domain: the three lookup mechanisms in reliability
order, 8 curated featured skills with a reason each, the relevant decision trees
from `standards/decision-trees/` (seven trees plus a README), the canonical
templates from `templates/<domain>/` where one exists (admin, agentforce, apex,
flow, lwc), and the run-time agents that cover it. A router is a map, not the
territory — it never answers a Salesforce question itself, and each one says so
in its own `## Rules` block.

### A router's keyword list is a promise about its roster

A router's `description` is always-on, and it is the only thing Claude reads
before choosing which of the 11 rosters to open. So a router that advertises a
keyword whose packages live in a *different* domain sends the reader to a roster
that cannot answer them — and the reader has no way to know, because they scan
the wrong file and conclude the library has no coverage. Three such mis-routes
were measured on 2026-08-07 and are fixed in the shipped descriptions:

| Keyword | Was advertised by | Where the packages actually concentrate | Fixed by |
|---|---|---|---|
| sharing / record access | `salesforce-security` only | admin, comfortably ahead of security — `admin/sharing-and-visibility` is the anchor package | admin now claims the *design* of the access model; security keeps *troubleshooting a live denial* |
| REST API | `salesforce-integration` only | apex, roughly 2:1 over integration — `apex/callouts-and-http-integrations` is the anchor | integration = **inbound**; apex = **outbound**, both stated in both descriptions |
| duplicate | `salesforce-data` only | data leads on volume, but `admin/duplicate-management` owns *prevention* | admin = matching + duplicate rules; data = cleanup at volume |

(The exact package tallies behind those three rows were taken on 2026-08-07 with
a keyword count over `registry/skills.json`; the direction of each still holds,
but re-count rather than quoting a number, because the corpus moves.)

Two more concepts genuinely span two domains and are now named as split in both,
rather than silently claimed by one: **Bulk API** (data owns the load/extract,
integration owns the job API) and **governor limits** (apex owns Apex limits,
flow owns Flow limits and "my flow is hitting SOQL limits").

The rule when editing `DOMAIN_META` in `scripts/build_plugin.py`: count where the
packages actually are first, in `registry/skills.json`, and make the keyword list
match. Do not move skills between domains to resolve an overlap — that churns
paths for no retrieval gain. Name the split in both descriptions instead.

## Uninstall

```bash
claude plugin uninstall sfskills
claude plugin marketplace remove sfskills
```

Both were run as written and reported
`✔ Successfully uninstalled plugin: sfskills (scope: user)` and
`✔ Successfully removed marketplace: sfskills`. Removing the marketplace does not
delete the cache directory; `rm -rf` it yourself if you want the 1.2 GB back.
