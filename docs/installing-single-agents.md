# Installing a Single Agent

**Status:** Wave 8 feature. Added in response to the Excelsior incident where hand-copying a single `AGENT.md` into another project dropped its probe + skill dependencies, causing the consuming AI to improvise (and hallucinate) SOQL.

---

## Why this exists

An `AGENT.md` file by itself is 8 sections of instructions. But those instructions reference:

- **Probes** under `agents/_shared/probes/` (the canonical SOQL)
- **Skills** under `skills/<domain>/<slug>/` (the background knowledge)
- **Shared docs** under `agents/_shared/` (`AGENT_CONTRACT.md`, `REFUSAL_CODES.md`, schemas)
- **Templates** under `templates/` (Apex base classes, LWC skeletons)
- **Decision trees** under `standards/decision-trees/` (routing logic)

Without those files, any AI executing the agent fills gaps with plausible-looking output — which in one documented incident produced `PermissionSetGroupAssignment` as an sObject name (it doesn't exist). See `skills/admin/salesforce-object-queryability` for the failure-mode taxonomy.

**The fix is to ship the agent and its dependencies together, as a self-contained bundle.**

---

## Three supported install paths

### Option A — MCP server (recommended for live use)

Run the SfSkills MCP server in your project. The server holds the full library, and any MCP-capable client (Claude Code, Cursor with MCP, Claude Desktop, Cline, Continue) can call `get_agent("user-access-diff")` without copying any files.

Setup:
```bash
# In the SfSkills repo
cd mcp/sfskills-mcp
pip install -e .
```

In your project's MCP config (`.mcp.json` or equivalent), point at the local server.

**Pros:** Always up-to-date. One install serves every agent in the library. Integrates with `sf` CLI automatically.

**Cons:** Requires an MCP-capable client and a running server process.

---

### Option B — Bundle export (recommended for drop-in install)

Export a single agent with all its dependencies as a self-contained tree. Copy into your project. Done.

Setup:
```bash
# In the SfSkills repo
python3 scripts/export_agent_bundle.py --agent user-access-diff --rewrite-paths --out ./my-export
```

Produces:
```
my-export/user-access-diff/
├── AGENT.md                              ← the agent (bundle-relative paths)
├── probes/
│   └── user-access-comparison.md         ← the 9 SOQL queries
├── skills/
│   ├── admin/user-management/SKILL.md
│   ├── admin/permission-set-architecture/SKILL.md
│   └── ...
├── shared/
│   ├── AGENT_CONTRACT.md
│   ├── AGENT_RULES.md
│   ├── DELIVERABLE_CONTRACT.md          ← Wave 10 output contract
│   ├── lib/emit_deliverable.md
│   └── schemas/
│       ├── output-envelope.schema.json
│       └── ...
├── .cursor/commands/diff-users.md       ← Wave 11: slash command, per-target
├── .claude/commands/diff-users.md
├── .windsurf/workflows/diff-users.md
├── .augment/commands/diff-users.md
├── codex-prompts/diff-users.md
└── INSTALL.md
```

Drop the folder into your project:

| Tool | Location | Slash-command visibility |
|---|---|---|
| Claude Code | `.claude/agents/user-access-diff/` | `/diff-users` appears in `/` menu (Wave 11) |
| Cursor | `.cursor/agents/user-access-diff/` | `/diff-users` appears in `/` menu (Wave 11) |
| Windsurf | copy contents of `.windsurf/workflows/` into project root | `/diff-users` runs as a Cascade workflow |
| Augment | copy `.augment/commands/` into project root | `/diff-users` appears in `/` menu |
| Codex | `cp codex-prompts/*.md ~/.codex/prompts/` (user-scope) | `/prompts:diff-users` appears in `/` menu after restart |
| Aider | copy `AGENT.md` + dependencies into project | No slash support; reference in prose |
| Anywhere else | Any folder; reference `AGENT.md` directly | — |

The bundle ships the slash-command file for ALL five slash-supporting targets. Whichever tool your project uses, the command is already there.

**Pros:** Works offline. No MCP server needed. Single self-contained folder. Slash commands appear natively in all five supporting tools.

**Cons:** Manual update when the source agent changes. Regenerate the bundle on a schedule.

---

### Option C — Git subtree / submodule

Vendor the relevant paths from SfSkills into your project as a subtree. Pull updates with `git subtree pull`.

Example:
```bash
git subtree add --prefix=vendor/sfskills \
  https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git \
  main --squash
```

Then reference `vendor/sfskills/agents/user-access-diff/AGENT.md` from your project's agent config. The full repo travels with your project.

**Pros:** Git-tracked updates. Full library always available.

**Cons:** Ships ~100+ MB of unused content. Updates require conflict resolution.

---

## Which should I pick?

| Your situation | Option |
|---|---|
| Building on Claude Code / Cursor with MCP support | **A** |
| One specific agent, one specific project, no MCP | **B** |
| Multiple projects want consistent library updates | **A** (run one central MCP server) or **C** |
| Airgapped / offline / locked-down environment | **B** |
| You want agents auto-updated when the library releases | **A** |

---

## When a bundle drift happens

If the agent's dependencies change upstream (new probe added to Mandatory Reads, new skill cited), your installed bundle is stale. Two signs:

1. The agent's `AGENT.md` in your project references a file that doesn't exist in your bundle.
2. Output envelopes start showing `dimensions_skipped` entries with `reason: 'dependency missing'`.

Remediation: re-run `scripts/export_agent_bundle.py --agent <name>` in the source repo and replace your bundled copy.

---

## Agent dependencies block (what controls what gets bundled)

Every `AGENT.md` declares its dependencies explicitly in frontmatter:

```yaml
dependencies:
  probes:
    - user-access-comparison.md
  skills:
    - admin/user-management
    - admin/permission-set-architecture
    - security/permission-set-groups-and-muting
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
  templates: []
  decision_trees: []
```

The bundle exporter reads this block to decide what to copy. Adding an item to an agent's Mandatory Reads is a two-step operation: update the prose AND update this frontmatter block. CI enforces parity.

If you're authoring a new agent, run `python3 scripts/migrate_agent_dependencies.py --agent <your-id>` after drafting Mandatory Reads — it auto-populates the block from the prose citations.

---

## Validating an installed bundle

A quick check that your bundle is complete:

```bash
# From the bundle root
ls AGENT.md probes/ skills/ shared/
```

If any of those are missing, the bundle is incomplete. Regenerate.

More thorough check (from the source repo):

```bash
python3 scripts/export_agent_bundle.py --agent <your-id> --out /tmp/check
diff -r /tmp/check/<your-id>/ /your-project/.cursor/agents/<your-id>/
```

No diff output = your bundle matches the source.

---

## Security note

An agent bundle is **read-only static content**. No credentials. No executable code beyond the probe recipes (which are SOQL snippets, not scripts). Safe to check into your project repo. Safe to distribute.

**NEVER** include your `sf` CLI auth tokens, API keys, or connected-app secrets anywhere in an agent bundle. Those belong in your project's secrets management, not in markdown files.

---

## See also

- `docs/multi-ai-parity.md` — the parity contract that agent bundles ultimately express.
- `scripts/export_agent_bundle.py` — the bundler.
- `scripts/migrate_agent_dependencies.py` — backfills the `dependencies` frontmatter block.
- `skills/admin/salesforce-object-queryability` — why bundles matter (the Excelsior incident).
