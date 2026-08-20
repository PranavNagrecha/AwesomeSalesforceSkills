# Phase 1 product-owner review — remediation

Date: 2026-08-19.
Branch: `product/cursor-plugin-deployment-triage` (local only).
Baseline: `main` @ `d5f068887`.
Review file: `PHASE1_PRODUCT_OWNER_REVIEW.md` (CHANGES REQUESTED).

This is the delta against that review. The updated Phase 1 final report is `docs/product-v2/pr-1-final-report.md`.

## P0-1 — Local plugin path

Default install parent is now `~/.cursor/plugins/local` ([Cursor: Test plugins locally](https://cursor.com/docs/plugins.md#test-plugins-locally)).

`--link` / `--copy` **copy** the built plugin there. A symlink whose target is the repo `dist/` tree can be rejected (target outside `plugins/local`). `--symlink` remains an opt-in. `--uninstall` also removes a leftover `~/.cursor/plugins/awesome-salesforce-skills` if it is this plugin.

Verified on disk after install:

- `~/.cursor/plugins/local/awesome-salesforce-skills/.cursor-plugin/plugin.json` → name `awesome-salesforce-skills` version `1.0.0`
- doctor `plugin_install.user_install_layout: local`, status `ok`
- legacy `~/.cursor/plugins/awesome-salesforce-skills` removed

**Host-UI still required:** Customize list after `Developer: Reload Window`. This chat cannot reload Cursor.

## P0-2 — Org-grounder MCP

Chose option 1: `sf-org-grounder` is `readonly: false`. Mutation safety is the fail-closed MCP/shell allowlist, not Cursor Ask mode. Other subagents stay `readonly: true`.

Installed copy has `readonly: false`. After Reload Window, the parent `/triage-deployment` must delegate to this agent so it can call `get_deployment_result`.

This Composer session’s global `user-sfskills` MCP still does **not** expose `get_deployment_result` (stale pipx). Plugin MCP is `integrations/cursor/scripts/run_mcp.py` via `repo-root.json`. That is a different process than `user-sfskills`.

## P0-3 — MCP allowlist

`evaluate_mcp_call` allows only `_MCP_ALLOW_EXACT`. Unknown tools (`delete_record`, `update_user`, `change_setting`, `made_up_tool`) return **deny**. Covered by `test_unknown_mcp_denied`.

Repo authoring scripts under `scripts/*.py` are allowed in the **shell** policy so the plugin hook does not brick checkout maintenance. Salesforce mutating `sf` / MCP tools remain denied.

## P0-4 — Optional project mapping

- `pipelines/product/project_discover.py` — `explicit` | `discovered` | `standalone`
- SfSkills checkout and `empty-sfdx-project` are never treated as the user’s DX project
- `sf-repo-mapper` replaced by `sf-project-inspector`
- Flow: evidence → optional inspector → librarian → diagnosis → review

Measured: cwd = this repo → `standalone`. Explicit DevPN path → `explicit`.

## P0-5 — Cursor host E2E

Automated on this machine:

| Check | Result |
|---|---|
| Plugin files at documented local path | yes (copy, not external symlink) |
| Doctor overall | `ok` |
| `/triage-deployment` command files in plugin | yes |
| Subagent files including grounder `readonly: false` | yes |
| Fixture normalize | 2 groups |
| Live existing job retrieve (CLI report-only) | `0AfVB00000IYow50AD` Failed, 6 errors |
| Independent reviewer | `lint_diagnosis` fail on uncited HIGH; tests call it |
| Product MCP start-deploy | no product tool; CLI used `deploy report` only |

Not proven in this chat (requires Reload Window + human):

- Plugin visible in Customize
- Slash menu `/sfskills-doctor` and `/triage-deployment`
- Plugin MCP process (not pipx `user-sfskills`) listing `get_deployment_result`
- Subagent Task UI actually invoking `sf-org-grounder` with MCP

## P0-6 — Probe cleanup

Removed from `/Users/pranavnagrecha/VS Code/Excelsior/DevPN/DevPN`:

- `SfskillsTriageProbe{Alpha,Beta,Gamma}.cls` and `-meta.xml`

Tooling SOQL `ApexClass WHERE Name LIKE 'SfskillsTriageProbe%'` on `Excelsior-Dev-PN`: **0 rows**.

Historical job `0AfVB00000IYow50AD` still retrieves as Failed. Source-tracking warnings now say those classes are not in the local project (expected after delete). No new deploy was started for cleanup.

## P1-1 — Reviewer tests the lint

`pipelines/product/evidence_lint.py` `lint_diagnosis`. `ReviewerFixtureTests` calls it (unsupported fail, cited pass, unsafe remediation fail).

## P1-2 — Review bundle

`python3 scripts/pack_product_review.py` writes a ZIP with `BASELINE.txt`, full `git diff d5f068887`, reconstruct script, and product docs. Not a partial checkout.

## P1-3 — `export_skills.py --check`

| Tree | Result |
|---|---|
| Baseline `d5f068887` | **green** (`✓ export manifest matches`) |
| This branch before remediating | **red** — aider `CONVENTIONS.md` hash (new slash commands 67→70) |
| This branch after `python3 scripts/export_skills.py --all --manifest` | **green** |

Phase 1/2 added commands; the committed `registry/export_manifest.json` is updated so the gate matches.

## Automated tests (this pass)

`python3 -m unittest tests.product.test_phase1 tests.product.test_phase2 tests.product.test_project_discover` → **43 tests OK**.

`python3 scripts/validate_repo.py --agents` → 78 agents, 0 errors, 12 pre-existing warnings.

`python3 scripts/check_doc_counts.py` → 1034 skills, 50 runtime, 40 MCP tools.

`python3 scripts/export_skills.py --check` → green after manifest refresh.
