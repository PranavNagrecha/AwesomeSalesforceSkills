# Manual Cursor smoke (not automated)

Verified 2026-08-19 on this machine unless marked **host-UI**.

- [x] Plugin `awesome-salesforce-skills` is linked at `~/.cursor/plugins/awesome-salesforce-skills` → `dist/cursor/awesome-salesforce-skills` (doctor `plugin_install: ok`)
- [x] `/sfskills-doctor` equivalent: `python3 scripts/sfskills_doctor.py --json` → `overall: ok` (index present, sf CLI 2.144.6)
- [x] Fixture triage on `mcp/sfskills-mcp/tests/fixtures/deploy/component_failures.json`: 2 groups, citations/evidence IDs, domain files 5, overflow false
- [x] Evidence reviewer flags a draft that claims a root cause with no evidence IDs (`tests.product.test_phase1.ReviewerFixtureTests`)
- [x] Asking for “the latest deploy” without a job id refuses (`malformed_job_id` / `use_most_recent_forbidden`)
- [x] Agent policy cannot allow `sf project deploy start` (deny, including compound/nested wrappers)
- [x] Cloud-agent hook limitation is documented in `docs/product-v2/cursor-plugin.md`

Live retrieve:

- [x] `get_deployment_result` returns the real job `0AfVB00000IYow50AD` on `Excelsior-Dev-PN` (Failed, 6 errors, 2 groups)
- [x] No product tool started that retrieve (report-only). QA setup used an explicit deploy start **outside** the product MCP, with user authorization, to create the job.

Host-UI still true after **Reload Window**:

- [ ] Slash menu shows `/triage-deployment` and `/sfskills-doctor` in the Composer UI
- [ ] This chat’s `user-sfskills` MCP process is the **checkout** server (39 tools including `get_deployment_result`), not `~/.cache/sfskills-mcp/latest` (measured 2026-08-19: version 0.4.4, 997 skills, 47 runtime, **no** `get_deployment_result`)
