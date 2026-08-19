# Native Cursor plugin (local)

This is a **local** Cursor plugin. It is **not** submitted to the Cursor Marketplace. License: PolyForm Small Business 1.0.0.

## Install

From a SfSkills checkout:

```bash
python3 scripts/install_cursor_plugin.py --link
```

Then reload Cursor. Confirm `awesome-salesforce-skills` is listed and that `/triage-deployment` and `/sfskills-doctor` appear.

`--dry-run` prints paths without writing. `--copy` copies instead of symlink (writes `repo-root.json`). `--uninstall` removes only this plugin’s install.

Override the Cursor plugins directory with `SFSKILLS_CURSOR_PLUGIN_DIR` if your app version uses a different path.

## What is in the plugin

Bounded routers (`salesforce` + 11 domains with rosters), five subagents, two commands, MCP via `scripts/run_mcp.py`, and fail-closed shell/MCP hooks.

Detailed skill bodies are **not** packaged. Use MCP `get_skill` / `search_skill` against the checkout.

The flattened `.mdc` export (`python3 scripts/export_skills.py --target cursor`) is **legacy**.

## Doctor

```bash
python3 scripts/sfskills_doctor.py --json
```

`index_missing` means `vector_index/lexical.sqlite` is absent (`python3 scripts/bootstrap.py`). It is not “zero matches”.

## /triage-deployment

- **Fixture:** path to `sf project deploy report --json`
When `target_org` is supplied, the tool compares it to the local `~/.sf/deploy-cache.json` entry for that job id. The Salesforce CLI can return a cached job from a **different** org; the product refuses that as `job_org_mismatch` rather than diagnosing the wrong sandbox.


Local mapping needs a Salesforce DX project path.

Telemetry (redacted) is written under `.sfskills/runs/` (gitignored).

## Safety

Product Salesforce tool: `sf project deploy report --job-id <id> --json` only.

Hooks (`beforeShellExecution`, `beforeMCPExecution`) use `failClosed: true`. Some **cloud** Cursor agents do not load MCP/shell hooks — local and cloud policy coverage is not identical.

`preCompact` only logs; it cannot stop compaction.

## Uninstall

```bash
python3 scripts/install_cursor_plugin.py --uninstall
```
