# Native Cursor plugin (local)

This is a **local** Cursor plugin. It is **not** submitted to the Cursor Marketplace. License: PolyForm Small Business 1.0.0.

## Install

From a SfSkills checkout:

```bash
python3 scripts/install_cursor_plugin.py --link
```

Then reload Cursor (`Developer: Reload Window`). Confirm `awesome-salesforce-skills` is listed under **local** plugins and that `/triage-deployment` and `/sfskills-doctor` appear.

Default install path is `~/.cursor/plugins/local/awesome-salesforce-skills` ([Cursor: Test plugins locally](https://cursor.com/docs/plugins.md#test-plugins-locally)). `--link` / `--copy` **copy** the built plugin there. A symlink to the repo `dist/` tree can be rejected because the target sits outside `~/.cursor/plugins/local`. Use `--symlink` only when you know your Cursor build accepts it. `--uninstall` removes this plugin from `plugins/local` and from the legacy `~/.cursor/plugins/` location if present.

Override the parent directory with `SFSKILLS_CURSOR_PLUGIN_DIR` if a specific Cursor version uses a different path.

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

Two evidence sources (never both guessed):

- **Fixture:** path to `sf project deploy report --json`
- **Live:** existing `0Af…` job id plus org alias from `sf org list` (hyphens, not spaces). Optional `project_dir` / DX `source_path` for local file mapping.

When `target_org` is supplied, the tool compares it to `~/.sf/deploy-cache.json`. A cache hit for a **different** org is `job_org_mismatch`, not a diagnosis of the wrong sandbox.

If the user asks for “the latest deploy” without a job id or file, refuse. Do not use `--use-most-recent`.

Telemetry (redacted) is written under `.sfskills/runs/` (gitignored). Canonical reports also go to `docs/reports/deployment-failure-triager/`.

Apex test triage is **not** part of the Phase 1 plugin.

## Safety

Product Salesforce tool: `sf project deploy report --job-id <id> --json` only.

Hooks (`beforeShellExecution`, `beforeMCPExecution`) use `failClosed: true`. Some **cloud** Cursor agents do not load MCP/shell hooks — local and cloud policy coverage is not identical.

`preCompact` only logs; it cannot stop compaction.

## Uninstall

```bash
python3 scripts/install_cursor_plugin.py --uninstall
```
