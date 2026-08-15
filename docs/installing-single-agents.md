# Installing a Single Agent

How to take one run-time agent into another project without carrying the whole
library. Every command below was executed as written on 2026-08-15 against a
fresh `git clone --depth 1` of this repository.

---

## Why this exists

An `AGENT.md` file by itself is instructions. Those instructions reference:

- **Probes** under `agents/_shared/probes/` (the canonical SOQL)
- **Skills** under `skills/<domain>/<slug>/` (the background knowledge)
- **Shared docs** under `agents/_shared/` (`AGENT_CONTRACT.md`,
  `DELIVERABLE_CONTRACT.md`, `REFUSAL_CODES.md`, the JSON schemas)
- **Templates** under `templates/` (Apex base classes, LWC skeletons)
- **Decision trees** under `standards/decision-trees/` (routing logic)

Without those files, an AI executing the agent fills the gaps with
plausible-looking output. The documented case is in
`skills/admin/salesforce-object-queryability`, which records an agent running
`user-access-diff` against a sandbox and querying `PermissionSetGroupAssignment`
— an sObject that does not exist in any Salesforce edition:

> "sObject type 'PermissionSetGroupAssignment' is not supported."

The agent collapsed the 400 into "PSG not queryable in this org" and silently
dropped the permission-set-group dimension. The report was incomplete and looked
complete. (`PermissionSetAssignment` with `PermissionSetGroupId != null` is the
real query; the substitution table is in that skill.)

**So ship the agent and its dependencies together, as a self-contained bundle.**

---

## Three supported install paths

### Option A — MCP server (recommended for live use)

Run the SfSkills MCP server. It holds the whole library, and any MCP-capable
client can call `get_agent("user-access-diff")` — one of its 38 tools — without
copying any files.

```bash
# In an SfSkills checkout
git check-ignore -q .venv || echo '.venv/' >> .git/info/exclude   # .venv/ is NOT in .gitignore
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/bootstrap.py
./.venv/bin/python -m pip install -e mcp/sfskills-mcp
```

Then register it in your client, pointing at the **venv's** interpreter by
absolute path and setting `SFSKILLS_REPO_ROOT` inside the client's own config
block:

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- /absolute/path/to/AwesomeSalesforceSkills/.venv/bin/python -m sfskills_mcp
```

`claude mcp list` must report `✔ Connected`. Registering bare `python3` adds
cleanly and then fails to connect — see
[troubleshooting.md](./troubleshooting.md#mcp-server-added-successfully-but-never-connects).
Full per-client wiring for 18 clients is in
[`mcp/sfskills-mcp/docs/CONNECT.md`](../mcp/sfskills-mcp/docs/CONNECT.md).

`get_agent` returns `{name, kind, path, summary, markdown, slash_command_hint}` —
the playbook text, not a file copy.

**Pros:** always up to date; one install serves every agent in the library; the
server detects a local `sf` CLI and reports it in `meta.health()`.

**Cons:** requires an MCP-capable client and a server process.

---

### Option B — Bundle export (recommended for drop-in install)

Export one agent with its declared dependencies as a self-contained tree, then
copy that tree into your project.

```bash
# In the SfSkills repo
python3 scripts/export_agent_bundle.py --agent user-access-diff --rewrite-paths --out ./my-export
```

```text
✓ user-access-diff: 73 file(s) bundled → my-export/user-access-diff
  paths rewritten bundle-relative
```

The exporter is stdlib-only and needs no bootstrap. Flags:

| Flag | Effect |
|---|---|
| `--agent <id>` | Bundle one agent. Mutually exclusive with `--all-runtime`. |
| `--all-runtime` | Bundle every non-deprecated run-time agent. **Currently broken — see the known failure below.** |
| `--out <dir>` | Output directory. Default `exports/agent-bundles`. |
| `--rewrite-paths` | Rewrite `AGENT.md` citations to bundle-relative form and set `dependency_path_mode: bundle-relative`. Recommended for drop-in installs; skip it if the consumer already knows how to resolve `agents/_shared/*` paths. |

The `user-access-diff` bundle, verbatim from `find`:

```text
my-export/user-access-diff/
├── AGENT.md                                 the agent, paths bundle-relative
├── INSTALL.md
├── probes/
│   ├── user-access-comparison.md            9 numbered SOQL sections
│   └── permission-set-assignment-shape.md
├── skills/                                  8 complete packages, not just SKILL.md
│   ├── admin/agent-output-formats/
│   ├── admin/custom-permissions/
│   ├── admin/mass-transfer-ownership/
│   ├── admin/permission-set-architecture/
│   ├── admin/permission-sets-vs-profiles/
│   ├── admin/user-access-policies/
│   ├── admin/user-management/
│   └── security/permission-set-groups-and-muting/
├── shared/
│   ├── AGENT_CONTRACT.md
│   ├── AGENT_RULES.md
│   ├── DELIVERABLE_CONTRACT.md
│   ├── lib/emit_deliverable.md
│   └── schemas/{agent-frontmatter,citation,observation,output-envelope}.schema.json
├── .claude/commands/diff-users.md
├── .cursor/commands/diff-users.md
├── .windsurf/workflows/diff-users.md
├── .augment/commands/diff-users.md
└── codex-prompts/diff-users.md
```

73 files, 560 KB. Each cited skill arrives as the whole package — `SKILL.md`
plus `references/`, `scripts/` and `templates/` — not just the entry file. Bundle
size scales with the agent: `flow-builder` exports 342 files.

Drop the folder into your project:

| Tool | Location | Slash-command visibility |
|---|---|---|
| Claude Code | `.claude/agents/user-access-diff/` | `/diff-users` from the bundled `.claude/commands/` |
| Cursor | `.cursor/agents/user-access-diff/` | `/diff-users` from the bundled `.cursor/commands/` |
| Windsurf | copy the contents of `.windsurf/workflows/` into the project root | `/diff-users` runs as a Cascade workflow |
| Augment | copy `.augment/commands/` into the project root | `/diff-users` in the `/` menu |
| Codex | `cp codex-prompts/*.md ~/.codex/prompts/` (user scope) | `/prompts:diff-users` after restart |
| Aider | copy `AGENT.md` + dependencies into the project | no slash support; reference in prose |
| Anywhere else | any folder; reference `AGENT.md` directly | — |

The bundle ships the slash-command file for all five slash-supporting targets, so
whichever tool your project uses, the command is already there.

**Pros:** works offline; no MCP server; one self-contained folder.

**Cons:** manual update when the source agent changes; regenerate on a schedule.

#### Known failure: 9 of 76 agents cannot be exported today

`export_agent_bundle.py` copies each `dependencies.templates` entry with
`shutil.copyfile`, which cannot copy a directory. Nine agents declare a template
*directory* rather than a file and therefore crash with exit 1:

```text
$ python3 scripts/export_agent_bundle.py --agent apex-builder --out ./x
IsADirectoryError: [Errno 21] Is a directory: '/…/templates/apex'
$ echo $?
1
```

Measured by exporting every agent one at a time: **67 succeed, 9 fail.** The
nine are `apex-builder`, `apex-refactorer`,
`custom-metadata-and-settings-designer`, `lwc-auditor`, `lwc-builder`,
`lwc-debugger`, `sandbox-strategy-designer`, `test-class-generator` and
`trigger-consolidator` — every agent whose frontmatter lists a directory such as
`apex/`, `apex/tests/`, `apex/cmdt/` or `lwc/patterns/`.

`--all-runtime` hits the first of them and aborts the whole run, leaving a
partial output directory. Until the exporter learns `copytree`, use Option A or
Option C for those nine, or hand-copy the named template directories into a
bundle produced for a different agent.

---

### Option C — Git subtree

Vendor the repository into your project as a subtree and pull updates with
`git subtree pull`.

```bash
git subtree add --prefix=vendor/sfskills \
  https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git \
  main --squash
```

Then reference `vendor/sfskills/agents/user-access-diff/AGENT.md` from your
project's agent config.

**Pros:** git-tracked updates; the full library is always available; unaffected
by the exporter bug above.

**Cons:** the tracked tree is 87 MB across 9,324 files, almost all of it unused
by any single agent, and the fetch pays a ~407 MiB pack. Updates need conflict
resolution.

```bash
git ls-files | wc -l                        # 9324
git count-objects -vH | grep size-pack      # size-pack: 406.68 MiB
```

---

## Which should I pick?

| Your situation | Option |
|---|---|
| Building on a client with MCP support | **A** |
| One specific agent, one project, no MCP | **B** |
| One of the 9 agents the exporter cannot bundle | **A** or **C** |
| Multiple projects want consistent library updates | **A** (one central server) or **C** |
| Airgapped / offline / locked-down | **B**, or **C** if the agent is one of the 9 |

---

## When a bundle drifts

If the agent's dependencies change upstream — a new probe in Mandatory Reads, a
newly cited skill — your installed bundle is stale. Two signs:

1. The bundled `AGENT.md` references a file that is not in your bundle.
2. Output envelopes carry `dimensions_skipped` entries whose `reason` names a
   missing dependency. That array is part of the contract:
   `agents/_shared/schemas/output-envelope.schema.json` requires
   `{dimension, reason, state}` per entry and forces confidence to MEDIUM or LOW
   whenever it is non-empty, precisely to stop the "silently complete report"
   failure mode.

Remediation: re-run `scripts/export_agent_bundle.py --agent <name>` in the source
repo and replace your bundled copy.

---

## The dependencies block controls what gets bundled

Every `AGENT.md` declares its dependencies in frontmatter. This is the real block
from `agents/user-access-diff/AGENT.md`, not an illustration:

```yaml
dependencies:
  probes:
    - permission-set-assignment-shape.md
    - user-access-comparison.md
  skills:
    - admin/agent-output-formats
    - admin/custom-permissions
    - admin/mass-transfer-ownership
    - admin/permission-set-architecture
    - admin/permission-sets-vs-profiles
    - admin/user-access-policies
    - admin/user-management
    - security/permission-set-groups-and-muting
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
```

`templates:` and `decision_trees:` are optional and absent when empty.

Adding an item to an agent's Mandatory Reads is a two-step operation: update the
prose **and** this block. Parity is enforced —
`scripts/check_agent_citation_parity.py` runs standalone and is also called from
`scripts/validate_repo.py`:

```text
$ python3 scripts/check_agent_citation_parity.py
Checked 76 agent(s); 0 error(s).
```

If you are authoring a new agent, run
`python3 scripts/migrate_agent_dependencies.py --agent <your-id>` after drafting
Mandatory Reads — it populates the block from the prose citations. It also takes
`--dry-run` and `--force`.

---

## Validating an installed bundle

A quick completeness check from the bundle root:

```bash
ls AGENT.md probes/ skills/ shared/
```

If any of those are missing, the bundle is incomplete — regenerate. (`templates/`
and `standards/decision-trees/` appear only when the agent declares them, so
their absence is not a fault.)

A thorough check, from the source repo:

```bash
python3 scripts/export_agent_bundle.py --agent <your-id> --out /tmp/check
diff -r /tmp/check/<your-id>/ /your-project/.cursor/agents/<your-id>/
```

No diff output means your bundle matches the source. Note that a bundle produced
with `--rewrite-paths` will not match one produced without it — the frontmatter
`dependency_path_mode` and the in-body citations both differ — so compare like
with like.

---

## Security note

An agent bundle is **read-only static content**: markdown, JSON schemas, and
skill-local stdlib-only checker scripts. No credentials. Safe to check into your
project repo and safe to distribute.

**Never** put `sf` CLI auth tokens, API keys, or connected-app secrets in a
bundle. Those belong in your project's secrets management. Every run-time agent
is under standing instructions to redact secrets as `[REDACTED]` and never to
deploy to an org.

---

## See also

- [`docs/multi-ai-parity.md`](./multi-ai-parity.md) — the parity contract agent
  bundles express.
- [`docs/installing.md`](./installing.md) — full setup, including the MCP server.
- [`docs/troubleshooting.md`](./troubleshooting.md) — install and connection
  failures.
- `scripts/export_agent_bundle.py` — the bundler.
- `scripts/migrate_agent_dependencies.py` — backfills the `dependencies` block.
- `skills/admin/salesforce-object-queryability` — why bundles matter.
