# Installing SfSkills as a Claude Code plugin

**Status:** 1.0.0. Generated artifacts are produced by
[`scripts/build_plugin.py`](../scripts/build_plugin.py); the drift gate is
`python3 scripts/build_plugin.py --check`.
**Verified against:** Claude Code 2.1.209 (`claude --version`), re-measured
2026-08-07, by a real `marketplace add` → `install` → `details` cycle run from
**outside** this repository against an isolated `CLAUDE_CONFIG_DIR`. **The
marketplace source in every measured run was a local path; the GitHub source is
documented but untested.** Read
[Verify the plugin path](#verify-the-plugin-path) before trusting any check —
"it works when I'm in the repo" proves nothing about the plugin.

Schema sources, researched before anything was written:

- <https://code.claude.com/docs/en/plugins-reference> — `plugin.json` fields,
  the `${CLAUDE_PLUGIN_ROOT}` substitution, and the "Path behavior rules"
  section that says `skills` **adds to** the default scan while `commands`,
  `agents`, `workflows` and `outputStyles` **replace** it. Quoting the
  component-path table: `commands` is *"Custom flat `.md` skill files or
  directories (replaces default `commands/`)"*; `agents` is *"Custom agent
  files (replaces default `agents/`)"*; and *"All paths must be relative to
  the plugin root and start with `./` …"* — the sentence continues with an
  exception for `skills`, which also accepts `"."`. Nothing here depends on
  the exception; both declared paths use `./`.
- <https://code.claude.com/docs/en/plugin-marketplaces> — `marketplace.json`
  fields, reserved marketplace names, and the marketplace-root exception under
  "Advanced plugin entries".
- <https://code.claude.com/docs/en/sub-agents> — the `.claude/agents/*.md`
  project-scope subagent format (`name` + `description` frontmatter), which
  the docs say to check into version control. **Project scope is not plugin
  scope**, which is why the same 48 loaders are generated twice, to two
  different paths — see
  [Known limitation 1](#1-the-agents-manifest-key-does-not-work-in-any-form).
- <https://code.claude.com/docs/en/plugins> — plugin skill namespacing, and
  the precedence rule that decides which of the two loader copies wins:
  *"Project and user `.claude/agents/` definitions override same-named plugin
  agents, so the plugin version only takes effect once the originals are
  removed. Plugin skills are namespaced as `/plugin-name:skill-name`, so the
  original `/skill-name` and the plugin copy both remain available rather than
  one overriding the other."*

---

## Install

> **Prerequisite:** the plugin manifests live on `overhaul/2026-08-01-checkpoint`
> and are not yet on the default branch, so neither recipe below works until
> that branch merges to `main`. Verify for yourself with
> `git ls-tree origin/main .claude-plugin/` — it returns nothing today, which
> means `marketplace add PranavNagrecha/AwesomeSalesforceSkills` resolves a
> branch with no `marketplace.json` and no `plugin.json` on it. Until that
> changes, install from a **local path** pointed at a working tree that
> contains `.claude-plugin/`, as in
> [The check that cannot be faked](#the-check-that-cannot-be-faked).

### From GitHub (normal path — blocked by the prerequisite above)

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
extra setup — but the clone has to be on a branch that carries
`.claude-plugin/`, which the default branch is not (see the prerequisite
above). A local path is the source type every measurement in this document
used; a fresh clone is not, for the reason immediately below the block:

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
git -C AwesomeSalesforceSkills switch overhaul/2026-08-01-checkpoint
claude plugin marketplace add ./AwesomeSalesforceSkills
claude plugin install sfskills@sfskills
```

That `switch` needs the branch to exist on the remote. It does not yet
(`git ls-remote --heads origin overhaul/2026-08-01-checkpoint` returns
nothing), so for now the only source that works is a **path to an existing
working tree** on that branch — for example the checkout you are reading this
file in.

Inside Claude Code the same pair is:

```
/plugin marketplace add ./AwesomeSalesforceSkills
/plugin install sfskills@sfskills
```

Run these from a directory that is **not** the clone. Installing from inside
the repository works, but it makes the result impossible to read: project-local
loading supplies the same routers, so you cannot tell which mechanism you are
seeing. The next section is how to tell.

---

## Verify the plugin path

This is the section that matters. Claude Code loads `.claude/skills/` and
`.claude/agents/` **from your current working directory** whenever you are
sitting in a trusted project, plugin or no plugin. So if you check the install
from inside a clone of this repository, you will see routers and subagents
appear whether or not the plugin manifest works at all. An earlier "verified
working" claim on this repository was exactly that mistake: what had been
observed was project-local loading, and the plugin was shipping zero agents.

The trap did not go away when the agents started shipping — it got quieter.
Both copies now exist and are identical, and the project-local one takes
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

The last row comes from <https://code.claude.com/docs/en/plugins> — *"Plugin
skills are always namespaced (like `/my-first-plugin:hello`) to prevent
conflicts … To change the namespace prefix, update the `name` field in
`plugin.json`."* Note that `claude plugin details` prints the **bare** names
in its inventory; the namespace shows up where you invoke them.

### The check that cannot be faked

Run it from a directory that is **not** this repository and has no `.claude/`
of its own. The `CLAUDE_CONFIG_DIR` override keeps the whole exercise out of
your real configuration, so a failed experiment cannot leave a half-installed
plugin behind.

```bash
export CLAUDE_CONFIG_DIR="$(mktemp -d)"      # throwaway config
cd "$(mktemp -d)"                            # NOT the repo, no .claude/ here

claude plugin marketplace add /absolute/path/to/AwesomeSalesforceSkills   # the working tree
claude plugin install sfskills@sfskills --scope user
claude plugin details sfskills
```

What proves the plugin path worked. Measured on 2.1.209 with a **local path**
marketplace source; the GitHub source resolves the default branch and is
untested here:

```text
SfSkills — Salesforce AI Skill Library (sfskills) 1.0.0
  1,027 grounded Salesforce skill packages, 48 run-time agents and 66 slash commands, …
  Source: sfskills@sfskills

Component inventory
  Skills (78)  analyze-field-impact, analyze-flow, … salesforce, salesforce-admin, …
  Agents (48)  lwc-debugger, flow-builder, email-template-modernizer, …
  Hooks (0)
  MCP servers (0)
  LSP servers (0)

Projected token cost
  Always-on:   ~6,118 tok   added to every session
```

Read it like this:

- **`Source: sfskills@sfskills`** — `plugin details` only knows about
  installed plugins. Project-local `.claude/` never appears here, so any
  output at all is already plugin-path evidence.
- **`Skills (78)`** — 12 routers from `.claude/skills/` plus 66 from
  `commands/`. Both arrive through manifest keys; see
  [What the manifests do](#what-the-manifests-do-and-why).
- **`Agents (48)`** — the flat `agents/<id>.md` loaders, through Claude Code's
  default scan. No manifest key is involved, and none would help; see
  [Known limitation 1](#1-the-agents-manifest-key-does-not-work-in-any-form).
  This number was `0` until 2026-08-07.
- **`Always-on: ~6,118 tok`** — Claude Code's own accounting for what the
  install adds to every session. It was `~2,889` before the agents shipped:
  each loader's `name` + `description` costs ~60-70 always-on tokens, so the
  48 agents more than doubled the bill. That is the price of the fix, and
  [Measured cost](#measured-cost) carries it.

`claude plugin list` should report `Status: ✔ enabled` alongside this. Tear the
experiment down when you are finished — the last block in this section.

One more cross-check, and it is the one that catches the specific mistake this
document exists to prevent. `claude plugin list` reports load status:

```bash
claude plugin list      # sfskills@sfskills  Status: ✔ enabled
```

A plugin whose manifest is malformed reports `✘ failed to load` here while its
components may still appear to work in a session — because project-local
loading picked them up. Treat `plugin list` and `plugin details` as the source
of truth, never the presence of a skill in a session.

Tear the experiment down:

```bash
claude plugin uninstall sfskills
claude plugin marketplace remove sfskills
rm -rf "$CLAUDE_CONFIG_DIR"; unset CLAUDE_CONFIG_DIR
```

### The repo-side gate

The same expectation is encoded so it cannot drift:

```bash
python3 scripts/build_plugin.py --audit-install
```

It projects the installed inventory from the repo's own files, prints it
beside the repo inventory, and exits 1 for every component the repo defines
that the plugin cannot deliver. Today it exits **0**: its
`Skills 78 / Agents 48` projection matches what `claude plugin details`
reports. It also compares the two loader sets byte-for-byte and fails if they
diverge, because that divergence is invisible from inside a clone (the
project-scope copy overrides the plugin-scope one).

The projection is a model of the loader, not a reading of it. It agreeing with
the CLI is evidence, not proof — when in doubt, run the install.

---

## Why the plugin is tiered

A flat export is not an option. Claude Code loads every skill's `name` and
`description` into the system prompt at session start, before the user types
anything.

```bash
python3 -c "import json,math; d=json.load(open('registry/skills.json')); \
  c=sum(len(s['name'])+len(s['description']) for s in d['skills']); \
  print(d['skill_count'],'skills;',c,'chars;',math.ceil(c/4),'tokens')"
# 1027 skills; 536653 chars; 134164 tokens
```

134k tokens of index before the first question. So the library ships in three
tiers, and only the frontmatter of Tier 1 is always-on. The per-tier figures
below come from `--measure`; Claude Code's own accounting reports a slightly
higher 6,118 (both are in the [table](#measured-cost) that follows).

An agent's `name` + `description` is always-on too. Only its *body* is
deferred, the same as a skill's. Calling Tier 3 "0 tok until invoked" was
wrong, and it stopped being harmless the moment the 48 loaders started
shipping: measured always-on went from ~2,889 to ~6,118.

```
Tier 1  ALWAYS ON      12 router skills           1,470 tok
        (5,956 tok)    66 slash commands          1,253 tok
                       48 agent loaders           3,233 tok  ← frontmatter only
                              │
                              │  router teaches the model to look up,
                              │  then read by path
                              ▼
Tier 2  ON DEMAND      1,027 skill packages      0 tok until opened
                       ${CLAUDE_PLUGIN_ROOT}/skills/<domain>/<slug>/SKILL.md
                              │
                              ▼
Tier 3  ON INVOCATION  48 agent playbooks        0 tok until invoked
                       agents/<id>.md → agents/<id>/AGENT.md
                       (the loader is Tier 1; the playbook it points at
                        is Tier 3 — ~370 tok each, on invoke)
```

### Measured cost

| | Skills loaded | Always-on tokens | Share of a flat export |
|---|---:|---:|---:|
| Flat export of all 1,027 packages | 1,027 | 134,164 | 100% |
| **This plugin (Claude Code's own accounting)** | **78 + 48 agents** | **~6,118** | **4.56%** — a 22x reduction |
| This plugin (`--measure`, `ceil(chars/4)` model) | 78 + 48 agents | 5,956 | 4.44% — a 22x reduction |
| Same plugin before the agents shipped | 78 | ~2,889 | 2.15% |

Reproduce the first two rows with:

```bash
claude plugin details sfskills          # reads "Always-on:  ~6,118 tok"
python3 scripts/build_plugin.py --measure
```

`--measure` exits 1 if Tier 1 crosses 6,000 tokens or 5% of the flat-export
cost, so a router that grows a paragraph fails the build rather than quietly
taxing every session. **Headroom is now 44 tokens**, and the agent loaders are
54% of the budget. Adding a 49th run-time agent will fail the gate. When that
happens, shorten the generated loader `description` in `render_subagent()` —
do not raise `BUDGET_TIER1_TOKENS`, because the budget is the only thing
standing between this plugin and the flat export it exists to avoid.

The two rows disagree by 2.6% (5,956 modelled vs ~6,118 measured), the same
order as the 8% gap the pre-agent build showed. `ceil(chars/4)` is a model,
not the tokenizer; treat `plugin details` as the number of record.

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

Carries the metadata plus two component paths:

- **`skills: ["./.claude/skills/"]`** — the 12 routers, as above.
- **`commands: ["./commands/"]`** — the 66 slash commands, loaded from the
  tracked repo-root `commands/`, which is where the canonical files already
  live. `commands` *replaces* its default scan, but naming the default folder
  explicitly is the documented way to declare it without losing it:
  plugins-reference says Claude Code *"doesn't warn when the manifest key
  points into the default folder … because that path names the folder
  explicitly."* Measured: still `Skills (78)`. The key is there so the
  manifest states what it ships rather than relying on an implicit default.

It deliberately omits **`agents`**. Measured on 2.1.209, every custom-path
form of that key loads zero agents, and because it *replaces* the default
scan, declaring it also disables the one path that does work. The 48 agents
ship through that default scan instead — flat `agents/<id>.md` at the plugin
root, generated by the same build. The full probe matrix is in
[Known limitation 1](#1-the-agents-manifest-key-does-not-work-in-any-form)
and in the `AGENT_LOADING_MATRIX` comment at the top of
`scripts/build_plugin.py`.

### The description string is derived, not typed

Both manifests build their description from
`_inventory_phrase()` in `scripts/build_plugin.py`, and every number in it
comes from what an install actually exposes — `registry/skills.json` for the
package count, the `commands/` file count for the command count, and the flat
`agents/*.md` set the build emits for the agent count. The agent clause is
**omitted while that set is empty**, so before 2026-08-07 the description read
"1,027 grounded Salesforce skill packages and 66 slash commands" with no agent
claim. It started saying "48 run-time agents" on its own the moment the
loaders were emitted — nobody typed the number. Nothing about the count is
hand-maintained, so the manifest cannot drift back into promising components
it does not ship.

The agent count comes from the build's **output map**, not from a filesystem
scan and not from the agent roster. That matters for two reasons: a manifest
rendered from pre-build disk state would describe the *previous* build and
`--check` would report drift on the next run; and deriving it from the roster
would let the manifest claim 48 agents even if the loader emit were deleted.

### Validation

```bash
claude plugin validate .          # exits 1 on failure, 0 on pass-with-warnings
claude plugin validate . --strict # exits 1 on warnings too
```

Measured exit codes on 2.1.209: `1` when the manifest is rejected (for example
`agents: Invalid input`), `0` when it passes with warnings, `1` for the same
warnings under `--strict`. Pointed at this repository the validator resolves
`.claude-plugin/marketplace.json`, and reports problems inside the referenced
`plugin.json` prefixed with the entry index (`plugins[0] plugin.json → …`).

---

## Regenerating the artifacts

Everything under `.claude-plugin/`, `.claude/skills/` and `.claude/agents/` is
generated, and so are the flat `agents/*.md` loaders at the repository root.
Do not hand-edit any of it.

Note the split inside `agents/`: the build owns the flat `agents/<id>.md`
files and nothing else there. The `agents/<id>/AGENT.md` packages and
`agents/_shared/` are hand-authored and are never touched — the stale-file
sweep over that directory is deliberately non-recursive and `*.md`-only, since
a recursive prune would delete the agent library.

```bash
python3 scripts/build_plugin.py                 # build in place
python3 scripts/build_plugin.py --check         # drift gate; exit 1 on any diff
python3 scripts/build_plugin.py --measure       # token budget; exit 1 if over
python3 scripts/build_plugin.py --verify-seeds  # resolve the curated seed table
python3 scripts/build_plugin.py --audit-install # installed inventory; exit 1 on a gap
```

The single hand-authored input is the seed table at the top of
`scripts/build_plugin.py`: 5–10 featured skills per domain, the per-domain
decision-tree pointers, and the trigger vocabulary. Every seed is resolved
against `registry/skills.json` **and** the filesystem at build time, so a
renamed or deleted skill fails the build instead of shipping a dead path.
The domain list, skill counts, rosters, agent set and both manifests are
derived.

If you add a router, re-run the build **and** re-add the new files with
`git add -f` (see the `.gitignore` note below — `.claude/` is ignored by
default). A new run-time agent needs no `-f`: `agents/` is not ignored, so its
flat loader shows up in `git status` normally, but its `.claude/agents/` twin
does need the negation that is already in place.

---

## Known limitations

Each of these was measured on Claude Code 2.1.209; none is a guess.

### 1. The `agents` manifest key does not work in any form

The agents ship — `claude plugin details sfskills` reports `Agents (48)` — but
not through anything you can declare. The `agents` manifest key is inert at
2.1.209, so the loaders have to sit exactly where the default scan looks and
the manifest has to stay silent about them.

**Probe procedure**, if you want to re-derive the table below on a newer
Claude Code. Build a throwaway plugin directory with its own
`.claude-plugin/marketplace.json` and `plugin.json`, one flat `agents/foo.md`
with `name` + `description` frontmatter, and whichever `agents` key the row
under test declares. Then, for each row: `export CLAUDE_CONFIG_DIR="$(mktemp
-d)"`, `cd "$(mktemp -d)"`, `claude plugin validate <probe dir>`,
`claude plugin marketplace add <probe dir>`,
`claude plugin install <name>@<name> --scope user`,
`claude plugin details <name>`, then `rm -rf "$CLAUDE_CONFIG_DIR"`. A fresh
config directory per row is what stops one row's install from colouring the
next. Results at 2.1.209:

| Where declared | Value | `validate` | `plugin details` |
|---|---|---|---|
| — (omitted) | flat `agents/foo.md` at plugin root | pass | `Agents (1)  foo` |
| — (omitted) | only `agents/x/AGENT.md`, no flat file | pass | `Agents (0)` |
| `plugin.json` | `["./custom-agents/"]` (directory) | **`agents: Invalid input`** | — |
| `plugin.json` | `["./custom-agents/a.md"]` | pass | `Agents (0)` |
| `plugin.json` | `["./.claude/agents/a.md"]` | pass | `Agents (0)` |
| `plugin.json` | `["./agents/foo.md"]` — the file the default scan just loaded | pass | `Agents (0)` |
| marketplace entry | `["./.claude/agents/a.md"]` | pass | `Agents (0)` from the key (the 1 seen was still the default scan) |
| marketplace entry | `["./.claude/agents/"]` (directory) | **`plugins.0.agents: Invalid input`** | — |
| marketplace entry | any of the above with `strict: false` | pass | plugin **fails to load**: *"conflicting manifests: both plugin.json and marketplace entry specify components"* |

Two conclusions. The only mechanism that ships a subagent is a flat `*.md`
**directly inside `<plugin root>/agents/`**; and declaring the key suppresses
even that, so omitting it is strictly better.

That collided with this repository's layout. `agents/` holds 76
`<id>/AGENT.md` *packages* — row 2 shows the flat scan skips those — and until
2026-08-07 the 48 generated loaders lived only at `.claude/agents/`, which is
the **project-scope** location from
<https://code.claude.com/docs/en/sub-agents>. Claude Code reads that path for
anyone whose cwd is this repo, plugin or not. That is precisely why the plugin
once looked like it shipped agents when it measured `Agents (0)`.

**What ships now.** `scripts/build_plugin.py` writes each loader twice, from a
single `render_subagent()` call:

| Path | Mechanism | Who sees it |
|---|---|---|
| `agents/<id>.md` | plugin default scan (variant A) | anyone who installs the plugin |
| `.claude/agents/<id>.md` | project scope | anyone whose cwd is a clone |

Both sets are 48 files with byte-identical contents, sitting beside — never
instead of — the `agents/<id>/AGENT.md` playbooks they load. Measured from
outside the repo, isolated `CLAUDE_CONFIG_DIR`, local-path marketplace source:

```text
Skills (78)  analyze-field-impact, analyze-flow, … salesforce-security, …
Agents (48)  lwc-debugger, flow-builder, email-template-modernizer, …
```

**Why two copies, and why generated.** Per
<https://code.claude.com/docs/en/plugins>, *"Project and user `.claude/agents/`
definitions override same-named plugin agents, so the plugin version only
takes effect once the originals are removed."* Inside a clone the project copy
therefore always wins, and the plugin copy is never exercised — so if the two
ever diverged, no amount of testing from inside the repo would reveal it.
Generating both from one call is what makes divergence impossible;
`--check` and `--audit-install` are what prove it stayed that way.
`--audit-install` compares them byte-for-byte and fails if they differ.

The duplication is deliberate, not redundancy to clean up. Deleting
`.claude/agents/` would break the clone workflow; deleting `agents/*.md` would
put `Agents (0)` back.

**What this still costs.** The 48 loaders add ~3,200 always-on tokens, 54% of
the Tier-1 budget — see [Measured cost](#measured-cost). And the manifest can
never advertise them: the `agents` key stays absent, so anyone reading
`plugin.json` alone sees no agent declaration at all. The `description` string
names them; the component list does not.

### 2. `.claude/commands/` is not tracked, and does not need to be

The plugin's slash commands ship from the tracked repo-root `commands/`, which
`.claude-plugin/plugin.json` declares as `"commands": ["./commands/"]`. The 66
files there are byte-for-byte identical to `.claude/commands/` (`cmp` clean on
all 66), so tracking the second copy would add a permanent drift surface and
buy nothing. `.claude/commands/` stays gitignored as a local editor
convenience, regenerated by `python3 scripts/bootstrap.py`.

The evidence is `Skills (78)` on a clean install from outside the repo: 12
routers plus all 66 commands, including `review`, `new-skill`, `refactor-apex`
and the rest.

`.claude/skills/` and `.claude/agents/` **are** tracked, and their `.gitignore`
negations are in place, so a new file written by a later build shows up
normally rather than being silently dropped:

```bash
touch .claude/skills/__probe.md .claude/agents/__probe.md
git status --short .claude/     # ?? both — untracked and addable, not ignored
rm .claude/skills/__probe.md .claude/agents/__probe.md
```

This matters more than it looks: if none of a marketplace entry's declared
skill paths exist in the fetched source, Claude Code falls back to the default
scan — which would silently ship a plugin with the wrong skill set.

The flat `agents/*.md` loaders need no negation. `agents/` was never ignored,
so they behave like any other tracked file. They do, however, need to be
*committed*: a GitHub install fetches only tracked files, so an uncommitted
loader means `Agents (0)` for everyone installing that way.

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

`"commands": ["./commands/"]` names the whole directory, and the `commands/`
files are not owned by this change. So 1.0.0 ships all 66, including the 9
files marked `LEGACY ALIAS` (`grep -lc 'LEGACY ALIAS' commands/*.md`) and the
build-time commands (`/new-skill`, `/new-agent`, `/build-skills`,
`/onboard-source`, `/sync-upstream-skills`, …) that are meaningless to someone
who installed the plugin to *use* the library. Collectively the commands are
1,253 of the 5,956 tokens `--measure` attributes to Tier 1 — 21% of the
budget, behind the 48 agent loaders at 54%.

Trimming them is follow-up work, and it got more urgent once the agents
started shipping: Tier 1 now sits 44 tokens under its 6,000 cap, and the
commands are the largest block that can be cut without losing a component.
The mechanism is known rather than untested: the field accepts a mixed array
of directories and individual files
(`["./commands/core/", "./commands/enterprise/", "./commands/experimental/preview.md"]`
in the plugin-marketplaces "Advanced plugin entries" example), so an allowlist
is a matter of listing the keepers in `PLUGIN_COMMANDS_PATH`. Re-measure with
`claude plugin details` afterwards — the `Skills (n)` count is the check.

---

## What you get

| Tier | Component | Count | Where |
|---|---|---:|---|
| 1 | Top-level router skill | 1 | `.claude/skills/salesforce/` |
| 1 | Domain router skills | 11 | `.claude/skills/salesforce-<domain>/` |
| 1 | Slash commands | 66 | `commands/` (declared) |
| 1 | Run-time subagent loaders | 48 | `agents/<id>.md` (plugin scope) + `.claude/agents/<id>.md` (project scope) — [why both](#1-the-agents-manifest-key-does-not-work-in-any-form) |
| 2 | Skill packages | 1,027 | `skills/<domain>/<slug>/` |
| 2 | Domain rosters (on-invoke) | 11 | `.claude/skills/salesforce-*/references/skill-index.md` |
| 3 | Run-time agent playbooks | 48 | `agents/<id>/AGENT.md` — read on invocation by the loader |

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
