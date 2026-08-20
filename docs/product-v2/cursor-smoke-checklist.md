# Manual Cursor smoke (not fully automatable)

Verified **2026-08-19** after product-owner P0 remediations. Official path: [Test plugins locally](https://cursor.com/docs/plugins.md#test-plugins-locally) → `~/.cursor/plugins/local/<name>`.

## On disk (this machine)

- [x] Plugin **copied** to `~/.cursor/plugins/local/awesome-salesforce-skills` (not an external symlink)
- [x] `.cursor-plugin/plugin.json` name `awesome-salesforce-skills` version `1.0.0`
- [x] Legacy `~/.cursor/plugins/awesome-salesforce-skills` removed
- [x] Doctor `plugin_install.user_install_layout: local`, `overall: ok`
- [x] Commands present: `triage-deployment.md`, `sfskills-doctor.md` (and Phase 2 `triage-apex-tests.md`)
- [x] Subagents present: `sf-org-grounder` (`readonly: false`), `sf-project-inspector`, librarian, triager(s), reviewer
- [x] Fixture `component_failures.json` → 2 groups
- [x] `lint_diagnosis` fails uncited HIGH claims (`ReviewerFixtureTests`)
- [x] Latest-deploy without job id refused by input validation
- [x] Policy denies `sf project deploy start` and unknown MCP tools
- [x] Standalone discovery from SfSkills cwd; explicit DevPN path is `explicit`
- [x] Live **report-only** retrieve of `0AfVB00000IYow50AD` (Failed, 6 errors). No deploy start in this remediation pass
- [x] Probe classes deleted from DevPN tree; org ApexClass query empty

## Host UI after you run Developer: Reload Window

- [ ] Customize lists `awesome-salesforce-skills` as a **local** plugin
- [ ] Slash menu shows `/sfskills-doctor` and `/triage-deployment`
- [ ] Plugin MCP (not global pipx `user-sfskills`) lists `get_deployment_result`
- [ ] `/triage-deployment` on the fixture completes through subagents
- [ ] `sf-org-grounder` actually calls MCP (or reads the fixture) and returns evidence IDs
- [ ] `sf-evidence-reviewer` reviews a draft
- [ ] No Salesforce mutation during that run
