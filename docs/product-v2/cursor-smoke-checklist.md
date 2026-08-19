# Manual Cursor smoke (not automated)

Run after `python3 scripts/install_cursor_plugin.py --link` and a Cursor reload.

- [ ] Plugin `awesome-salesforce-skills` is visible
- [ ] `/sfskills-doctor` runs and JSON/human output is coherent
- [ ] `/triage-deployment` on `mcp/sfskills-mcp/tests/fixtures/deploy/component_failures.json` produces grouped failures and citations
- [ ] Evidence reviewer flags a draft that claims a root cause with no evidence IDs
- [ ] Asking for “the latest deploy” without a job id refuses
- [ ] Agent cannot run `sf project deploy start` (hook deny)
- [ ] Cloud-agent hook limitation is understood if you use cloud agents

Live retrieve (optional, user-supplied alias + existing `0Af` job + DX path):

- [ ] `get_deployment_result` returns the real job
- [ ] No deploy is started
