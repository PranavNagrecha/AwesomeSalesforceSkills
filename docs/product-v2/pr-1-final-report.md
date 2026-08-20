# Phase 1 final report — Native Cursor plugin and Deployment Failure Triager

Branch: `product/cursor-plugin-deployment-triage` (local commits only; **not pushed**).
Date: 2026-08-19.
Baseline: `main` @ `d5f068887`.

This document is the Phase 1 exit report, **updated after the product-owner CHANGES REQUESTED review**. See `docs/product-v2/pr-1-po-review-response.md`. Scratch-org QA lab is still later.

---

## 1. What changed

A native **local** Cursor plugin (`awesome-salesforce-skills`) plus a read-only **Deployment Failure Triager**. Product libraries normalize `sf project deploy report --json`, bound context, fail-closed shell/MCP policy, and doctor. MCP gained `get_deployment_result` (39 tools). Roster: 49 runtime agents.

Live retrieve against Excelsior Dev PN required two product fixes: refuse CLI cache jobs for the wrong org; run `sf project deploy report` from a DX project cwd (this repo is not one).

## 2. User-visible workflow

1. `python3 scripts/install_cursor_plugin.py --link` then **Reload Window**.
2. `/sfskills-doctor` or `python3 scripts/sfskills_doctor.py --json`.
3. `/triage-deployment` with **either** a deploy-report JSON fixture **or** `job_id` + org alias (`sf org list`) + optional DX `source_path`.
4. Diagnosis + evidence review. No deploy start/cancel/retry/quick.

Doctor on this machine 2026-08-19 (post-review): `overall: ok`. Plugin **copied** to `~/.cursor/plugins/local/awesome-salesforce-skills`.

## 3. Files added, changed, generated, and deleted

`git diff main --stat`: **70 files, +3774 / −40** before this report commit (plus this docs/agent polish).

Canonical sources: `integrations/cursor/**`, `pipelines/product/**`, `mcp/sfskills-mcp/src/sfskills_mcp/deploy.py`, `agents/deployment-failure-triager/`, `commands/triage-deployment.md`, `commands/sfskills-doctor.md`, `scripts/build_cursor_plugin.py`, `scripts/install_cursor_plugin.py`, `scripts/sfskills_doctor.py`, `docs/product-v2/**`, `tests/product/test_phase1.py`.

Generated / gitignored: `dist/cursor/awesome-salesforce-skills/`, `.sfskills/runs/`.

Deleted: none on `main`. Probe Apex files were added under the **separate** Excelsior DevPN DX tree (not this git repo).

## 4. Architecture decisions

- Cursor path is a **bounded plugin**, not 1,034 `.mdc` rules. Flat export remains legacy.
- Focused Cursor subagents; `/triage-deployment` coordinates them. Mapping is optional (`sf-project-inspector`). `sf-org-grounder` is `readonly: false` so it can call MCP.
- Salesforce product path is **report-only**. Job id is mandatory. `--use-most-recent` is forbidden.
- CLI deploy-cache can return another org’s job; product returns `job_org_mismatch`.
- `sf project deploy report` requires a DX cwd; optional `project_dir` or bundled empty project.
- Source-tracking “returned from org, but not found in the local project” is not a deploy failure group.
- Envelope `outcome` plus `.sfskills/runs/` paths; `docs/reports/deployment-failure-triager/` remains the Wave 10 pair.
- License PolyForm Small Business 1.0.0 — **no Marketplace**.

## 5. Subagents and responsibilities

| Subagent | Role |
|---|---|
| `sf-org-grounder` | Fixture or `get_deployment_result`; bounded facts |
| `sf-context-librarian` | File selection; no diagnosis |
| `sf-project-inspector` | Optional: map `full_name` to local path / `line` / `column` when a DX project is found |
| `deployment-failure-triager` | Grouped diagnosis and remediation **shown not run** |
| `sf-evidence-reviewer` | Reject unsupported / unsafe claims |

## 6. Context-budget measurements

Live job `0AfVB00000IYow50AD`: domain skill/reference files **4**, files_loaded **6**, estimated tokens **21847**, overflow **false**, inject bytes **4177**, truncated **false**.

Fixture `component_failures.json`: domain files **5**, files_loaded **7**, estimated tokens **24809**, overflow **false**, bytes **2727**.

Hard limit 12 never silently exceeded in these runs.

## 7. MCP read-only and safety analysis

Checkout MCP: **39** tools (`check_doc_counts.py`). `get_deployment_result` runs `sf project deploy report --job-id … --json` only.

Policy (this run):

- `sf project deploy start` → deny
- compound `report && start` → deny
- `bash -c 'sf project deploy start'` → deny
- `--use-most-recent` → deny
- MCP `deploy_metadata` → deny
- unknown MCP (`delete_record`, …) → **deny** (explicit allowlist)
- `get_deployment_result` without `job_id` → deny
- report with explicit job id + `--json` → allow

Hooks: `beforeShellExecution` + `beforeMCPExecution`, `failClosed: true`. Cloud Cursor agents may not load those hooks.

**This Composer session’s `user-sfskills` MCP is stale:** `health` reported version **0.4.4**, repo `~/.cache/sfskills-mcp/latest`, 997 skills, 47 runtime agents, **no** `get_deployment_result`. Live retrieve was executed via the **checkout** Python package, not that cached MCP process.

## 8. Tests run with exact results

| Command | Result |
|---|---|
| `python3 -m unittest tests.product.test_phase1 tests.product.test_phase2 tests.product.test_project_discover` | **43 tests OK** (post-review) |
| `cd mcp/sfskills-mcp && python3 -m unittest tests.test_deliverable_contract tests.test_deploy_result` | **21 tests OK** after Output Contract persistence/guardrails added |
| `cd mcp/sfskills-mcp && python3 -m unittest discover -s tests -p 'test_*.py'` | **First run: 263 tests, 2 FAIL** (`deployment-failure-triager` missing persistence + Scope Guardrails). **Fixed in AGENT.md.** Those two classes now OK; full MCP discover not re-run after the fix (~75s plus ONNX fetch in unrelated tests). |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | **272 tests OK in 0.38s** — too fast to have executed `tests.product` (that file alone is 2.8s). Treat as a **shallow/other suite**, not as a substitute for `tests.product.test_phase1`. |
| `python3 scripts/validate_repo.py --agents` | **77 agents, 0 errors, 12 warnings** (pre-existing reading-list + unreachable-question WARNs) |
| `python3 scripts/build_plugin.py --check` | OK (123 artifacts) |
| `python3 scripts/build_cursor_plugin.py --check` | OK (37 files) |
| `python3 scripts/check_doc_counts.py` | OK: 1034 skills, 49 runtime, 39 MCP tools |
| `python3 scripts/export_skills.py --check` | Baseline `d5f068887` **green**. This branch was red until new slash commands were hashed into `registry/export_manifest.json`; **green** after `--all --manifest`. |
| `python3 scripts/sfskills_doctor.py --json` | `overall: ok` |

## 9. Live-org verification run

**Ran.** Org alias `Excelsior-Dev-PN` (`pnagrecha@excelsior.edu.devpn`). DX project `/Users/pranavnagrecha/VS Code/Excelsior/DevPN/DevPN`.

User authorized mutation of that private sandbox and DX tree. To produce a real failed job of metadata that exists in that tree, three compile-fail probe classes were added and deployed with `sf project deploy start` **from the shell** (not via product MCP). Product then retrieved:

- Job **`0AfVB00000IYow50AD`**
- Status **Failed**, 6 component errors, 0 components deployed, 0 Apex classes remaining (`SfskillsTriageProbe%`)
- Groups: 3× `Invalid type: SfskillsTriageProbeGhost`; 3× `Variable does not exist: ghost`
- Local map: `force-app/main/default/classes/SfskillsTriageProbe{Alpha,Beta,Gamma}.cls` lines 3–4
- Cache username matched requested username

Earlier job `0AfVB00000IYjjW0AT` was planted from `.sfskills/qa-excelsior-devpn` and did **not** map into DevPN.

`job_org_mismatch` was proven with cache id `0AfVB00000IYiyj0AD` belonging to `pnagrecha@excelsior.edu.full`.

MyServDevPN was not written.

Probe `.cls` files were **deleted** from the DevPN tree (PO P0-6). Tooling query for `SfskillsTriageProbe%` returned **0** Apex classes. Historical job `0AfVB00000IYow50AD` remains retrievable read-only. Do not seed compile-fail classes again for Phase 1.

## 10. Manual Cursor verification still required

On disk (post-review): plugin **copied** under `~/.cursor/plugins/local/`, commands and subagents present, grounder `readonly: false`.

This **chat cannot Reload Window**. Global `user-sfskills` in this session still lacks `get_deployment_result`. After reload, confirm Customize, slash menu, and that the **plugin** MCP (not pipx cache) exposes `get_deployment_result`. Checklist: `docs/product-v2/cursor-smoke-checklist.md`.

## 11. Known limitations

- Cursor cloud agents may skip MCP/shell hooks.
- Aliases with spaces (`Excelsior Dev PN`) fail CLI parse; use `Excelsior-Dev-PN`.
- Bundled empty DX cwd retrieves jobs but source-tracking warnings are stripped from groups.
- In-session MCP can stay on a cached wheel until Cursor reloads.
- Host-UI plugin binding still needs Reload Window.

## 12. Risks and migration notes

- Do not treat CLI deploy-cache as proof the job belongs to `--target-org`.
- Doctor lists `Broadtree-Full-RO` as default org; live tests used an explicit alias.
- Claude plugin left intact except count pins. Legacy Cursor `.mdc` export unchanged in purpose.
- PolyForm: local install only.

## 13. Review checklist

- [x] Deterministic Cursor plugin + `--check`
- [x] Install helper `--link` / `--dry-run` (no unsafe overwrite)
- [x] Bounded routers, not 1,034 rules
- [x] Legacy export still exists (`export_skills.py --target cursor`); `--check` currently red on aider hash
- [x] MCP config, doctor, triage, five subagents
- [x] Fixture path works
- [x] Live retrieve works when job + alias + DX path exist
- [x] MCP cannot start a deploy
- [x] 32 KiB bound / pagination tested
- [x] Evidence IDs + grouping
- [x] Context ≤8 target / 12 hard
- [x] Structured handoff (no transcripts)
- [x] Unsupported-claim reviewer fixture
- [x] Explicit missing job / malformed / auth-shaped / mismatch errors
- [x] Policy bypass tests
- [x] No org-mutation **product** tools
- [x] Docs: install, doctor, uninstall, smoke
- [x] This report records live tests and unrun host-UI reload

## 14. Items explicitly deferred

- Host-UI Reload Window confirmation (Customize, slash menu, plugin MCP)
- Scratch-org QA lab / general workflow engine / capability graph
- Backlog v2, decision-tree compiler, migrating all agents to context packs
- Claude plugin modernization
- Cursor Marketplace
- Automated remediation
