# PR 1 plan — Native Cursor plugin and Deployment Failure Triager

Status: implementing on branch `product/cursor-plugin-deployment-triage`.
Date: 2026-08-19.

This plan is specific to Phase 1. Apex test triage, scratch-org QA lab, and
repository-wide hardening are out of scope.

## User-visible outcome

After install + Cursor reload, a user can:

1. Run `/sfskills-doctor` and get a structured health report (including
   explicit `index_missing`).
2. Run `/triage-deployment` with either a local Salesforce CLI deploy-report
   JSON file or an existing job ID + org alias.
3. Receive an evidence-grounded diagnosis plus an independent evidence-review
   pass. No deploy is started, cancelled, retried, or modified.

## Baseline (this clone, 2026-08-19)

Recorded before product code:

- Git: `main` at `d5f068887`, new branch `product/cursor-plugin-deployment-triage`.
- Existing Cursor path: `scripts/export_skills.py --target cursor` flattens
  skills to `.mdc` rules. That remains **legacy**.
- Existing Claude plugin: `.claude-plugin/plugin.json` name `sfskills`,
  generated routers under `.claude/skills/`. Left intact except count pins
  required by `scripts/check_doc_counts.py` when the new runtime agent is added.
- MCP: FastMCP server, 38 tools, `sf_cli.run_sf_json` already redacts and
  times out. No deployment-report tool.
- `pipelines/lexical_index.search_index` returns `[]` when
  `vector_index/lexical.sqlite` is absent — CLI/MCP look like “no hits”.
- Live-org QA today is probe/factuality/structure, not seeded end-to-end
  reasoning. This PR adds fixture-backed product tests plus optional live
  **read-only** retrieve of an existing job ID (credentials supplied later).
- Envelope schema has no `completed|partial|refused|failed` outcome field.
  Smallest extension: optional `outcome` plus product report paths under
  `.sfskills/runs/`.

## Artifact ownership

| Artifact | Owner | Generated? |
|---|---|---|
| `integrations/cursor/**` | human / this PR | no (canonical adapter sources) |
| `scripts/build_cursor_plugin.py` | this PR | no |
| `scripts/install_cursor_plugin.py` | this PR | no |
| `scripts/sfskills_doctor.py` | this PR | no |
| `dist/cursor/awesome-salesforce-skills/` | builder | yes; gitignored; `--check` gates drift via committed manifest |
| `pipelines/product/**` | this PR | no |
| `mcp/sfskills-mcp/src/sfskills_mcp/deploy.py` | this PR | no |
| `agents/deployment-failure-triager/` | this PR | no |
| `agents/deployment-failure-triager.md` + `.claude/agents/` loader | `build_plugin.py` | yes (existing Claude machinery) |
| `commands/triage-deployment.md`, `commands/sfskills-doctor.md` | this PR | no |
| `.sfskills/runs/` | runtime telemetry | gitignored |
| Claude plugin routers | unchanged | — |

## Planned files (high level)

- Product libraries: deploy-result normalizer, context pack, handoff schema,
  shell/MCP policy, telemetry writer, doctor.
- MCP: `get_deployment_result` + captured CLI fixtures.
- Cursor plugin: bounded routers (12), five subagents, two commands, hooks,
  `mcp.json` wrapper, install helper.
- Canonical runtime agent + typed `inputs.schema.json`.
- Tests under `tests/product/` and `mcp/sfskills-mcp/tests/`.
- Docs under `docs/product-v2/` plus a short install page. No Marketplace claim.

## Context budget

Pilot pack (`integrations/cursor/context-packs/deployment-failure.yaml`):

- Core skill/reference files: 5 (contracts + three devops skills).
- Conditional packs by failure class (compile, tests, coverage, missing
  metadata, API version, permissions).
- Target domain skill/reference files: ≤ 8.
- Hard limit: 12 with explicit `overflow: true`.
- Single MCP payload injected into model context: ≤ 32 KiB; otherwise
  paginated / aggregated with `truncated` and `next_cursor`.

## Subagents (Cursor plugin only; max 5)

| Subagent | Role |
|---|---|
| `sf-context-librarian` | Select files; no diagnosis |
| `sf-repo-mapper` | Map failures to local DX paths (user-supplied project) |
| `sf-org-grounder` | Call approved read-only MCP tools; bound output |
| `deployment-failure-triager` | Diagnose from compact handoffs |
| `sf-evidence-reviewer` | Reject unsupported / unsafe claims |

`/triage-deployment` coordinates these directly. No extra orchestrator.

## Safety

- Product Salesforce path: `sf project deploy report --job-id <id> --json` only.
- No `--use-most-recent`.
- Hooks: `beforeShellExecution` and `beforeMCPExecution` with `failClosed: true`.
- `preCompact`: observe/log only.
- Cloud agents: MCP/shell hooks may not load; docs must say so.
- License: PolyForm Small Business 1.0.0 — local install only, no Marketplace.

## Acceptance mapping

The 21 criteria in the Phase 1 prompt are the exit gate. Live-org retrieve
runs only after the user provides: authenticated `sf` alias, existing `0Af`
job ID, and DX project path. Until then: `Live-org verification not run`.

## Risks

1. Cursor local plugin directory layout can differ by app version; installer
   detects known paths and refuses to guess.
2. Adding one runtime agent forces gated count updates (48 → 49) in
   `check_doc_counts.py` files. That is required, not doc sprawl.
3. Envelope `report_path` pattern currently requires `docs/reports/`. Product
   runs also write `.sfskills/runs/` — schema extended.
4. Full Cursor agent execution is not CI-automatable; hermetic tests + a
   manual smoke checklist.
