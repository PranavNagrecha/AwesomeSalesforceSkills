# SfSkills Phase 1 — Product Owner Review

**Review status: CHANGES REQUESTED — DO NOT MERGE YET**

Reviewed against the Phase 1 product promise: a locally installable native Cursor plugin plus an evidence-grounded Deployment Failure Triager, with bounded context, focused subagents, read-only Salesforce access, safety hooks, doctor/index behavior, and reviewable QA.

## What is good and should be preserved

- Native Cursor plugin build exists; legacy `.mdc` export remains separate.
- Exactly five focused subagents were created rather than exporting the whole runtime-agent catalog.
- Deployment result normalization includes stable evidence IDs, symptom grouping, pagination/truncation, and source counts.
- Context pack implements the intended target/hard limits and avoids obvious distractors.
- Doctor exposes `index_missing` explicitly instead of treating it as zero matches.
- Deployment retrieval requires an explicit job ID and forbids `--use-most-recent`.
- The implementation discovered an important real-world Salesforce CLI hazard: locally cached deployment IDs can refer to a different org than the requested alias. Keep the `job_org_mismatch` defense.
- Telemetry and evidence handoff primitives are directionally correct.

## Merge blockers

### P0-1 — The local Cursor install path is wrong for the current documented plugin test path

`scripts/install_cursor_plugin.py` defaults to:

`~/.cursor/plugins/awesome-salesforce-skills`

Current Cursor documentation says locally tested plugins belong under:

`~/.cursor/plugins/local/<plugin-name>`

The final report therefore does not prove a valid local installation. Change the default parent to `~/.cursor/plugins/local`, retain an override for version-specific cases, and manually verify the plugin appears after `Developer: Reload Window`.

### P0-2 — `sf-org-grounder` cannot do the job assigned to it

`integrations/cursor/agents/sf-org-grounder.md` is declared `readonly: true`, while its core responsibility is to call `get_deployment_result` and other SfSkills MCP tools.

Current Cursor behavior makes readonly custom subagents equivalent to Ask/read-only mode and blocks MCP access. Therefore the evidence-gathering subagent cannot actually gather MCP evidence.

Fix the architecture rather than hiding the issue in prose. For Phase 1, preferred options are:

1. Keep `sf-org-grounder` non-readonly, rely on the plugin's fail-closed MCP/shell policy, and explicitly instruct it to use only approved read-only SfSkills tools; or
2. Have the parent call MCP and pass normalized evidence into a readonly grounding/reviewer subagent.

Pick one and verify it in actual Cursor.

### P0-3 — MCP policy is not fail-closed for unknown tools

`pipelines/product/policy.py::evaluate_mcp_call()` currently returns `allow` for any MCP tool that does not match a small deny list or deployment substring rule.

That violates the Phase 1 requirement that the MCP guard allow only approved read-only product operations. A future mutating tool named something like `delete_record`, `update_user`, or `change_setting` could be allowed because it does not match the current deny patterns.

Change MCP policy to an explicit allowlist (or derive an allowlist from verified read-only tool annotations). Unknown MCP tools must return `ask` or `deny`, not `allow`. Security-critical product calls should fail closed.

### P0-4 — Local Salesforce project mapping is still modeled as a mandatory pipeline stage

The product correction after the Phase 1 prompt was explicit: SfSkills is a skill library, not a Salesforce DX project. Local source mapping must be optional enrichment.

Current `/triage-deployment` still lists `sf-repo-mapper` as step 3 in the fixed sequence, and the subagent remains named around 'repo' rather than Salesforce project discovery.

Replace this with an optional `sf-project-inspector` (preferred name) or equivalent behavior:

- explicit `project_path` wins;
- otherwise discover a Salesforce project from the user's active workspace/current directory if `sfdx-project.json` is present;
- otherwise continue in `standalone` mode;
- never infer that the SfSkills checkout is the Salesforce project;
- never require a project path to diagnose an existing deployment;
- report local navigation/dependency mapping as unavailable, not as a product failure.

The top-level flow should be:

`deployment evidence -> optional Salesforce project discovery/mapping -> bounded context -> diagnosis -> independent review`.

### P0-5 — Phase 1 has not actually been verified end-to-end in Cursor

The final report says the current Cursor MCP session was stale, Cursor had not been reloaded, and slash commands/subagents were not verified in the host. The live retrieval was executed against the checkout Python package rather than through the installed Phase 1 Cursor plugin.

That means the implementation has not yet proven the product promise:

`/triage-deployment -> subagent delegation -> MCP evidence -> diagnosis -> independent review`.

Before merge, perform one real local Cursor smoke run after reload and capture a sanitized transcript/report showing:

- plugin is visible in Customize;
- `/sfskills-doctor` is visible and works;
- `/triage-deployment` is visible;
- custom subagents are discoverable;
- the correct checkout MCP server is active and includes `get_deployment_result`;
- a fixture-mode triage completes;
- a live existing-job triage completes if credentials/job ID remain available;
- `sf-evidence-reviewer` actually receives and reviews a draft;
- no Salesforce mutation occurs during product execution.

This manual host test is required because the implementation's own report correctly says CI cannot prove Cursor UI/plugin binding.

### P0-6 — The live QA method violated the Phase 1 safety boundary and left the external project broken

The final report says three intentionally compile-failing Apex classes were added to a private sandbox/DX tree to manufacture a failed deployment and that those probe classes remain in the DevPN tree, causing a full-project deploy to fail until cleaned up.

Even if separately authorized, this contradicts the Phase 1 instruction: when live credentials are available, retrieve an existing deployment result read-only; do not start a deployment. Seeded mutation belongs to the later disposable scratch-org QA phase.

Before merge:

- remove the probe files from the external DX project;
- restore that workspace to its pre-test state;
- verify no test metadata remains in the target org if any was successfully created;
- amend the final report to clearly record cleanup;
- do not repeat seeded mutation in Phase 1.

Keep the captured failed result as a sanitized fixture if useful.

## P1 quality gaps

### P1-1 — The reviewer unit test does not test the reviewer

`tests/product/test_phase1.py::ReviewerFixtureTests.test_unsupported_claim` uses a local list comprehension to prove an unsupported HIGH-confidence hypothesis can be found. It does not execute the reviewer prompt, a deterministic reviewer function, or actual Cursor subagent behavior.

Keep this as a low-level fixture if desired, but add one of:

- a deterministic evidence-lint function used before final output and tested directly; plus a manual Cursor reviewer smoke test, or
- a host-level test that proves the reviewer returns `fail` for a seeded unsupported claim.

The product requirement is independent verification, not merely existence of an `sf-evidence-reviewer.md` file.

### P1-2 — Review bundle is not self-contained enough to reproduce several reported checks

The architect review ZIP intentionally excludes most of the repository. In this bundle, `mcp/sfskills-mcp/src/sfskills_mcp/paths.py`, `registry/skills.json`, and other baseline dependencies are absent, so MCP tests/build checks cannot be independently reproduced from the ZIP alone.

This is not necessarily a branch defect, because these may be unchanged baseline files. But future review bundles should include either:

- a complete checkout snapshot; or
- a git patch plus exact baseline commit and a script that reconstructs the review tree.

Product-owner review should not have to trust reported test output when the supplied artifact cannot reproduce it.

### P1-3 — `export_skills.py --check` is red

The final report identifies this as unrelated aider-manifest drift. It may indeed be unrelated, but Phase 1 should not merge with an unexplained red repository check unless baseline `main` is proven red in the same way.

Record:

- result on baseline `d5f068887`;
- result on Phase 1;
- whether Phase 1 changed the affected artifact.

If baseline is already red and Phase 1 did not worsen it, document as pre-existing. Otherwise fix it.

## Required re-review evidence

Return a new review ZIP only after the P0 items are fixed. Include:

1. Updated final report.
2. Complete diff or reproducible checkout against baseline.
3. Exact automated test results.
4. Current official Cursor local-plugin path verification.
5. Sanitized manual Cursor smoke evidence.
6. Evidence that `sf-org-grounder` can actually obtain MCP evidence under the chosen subagent permissions model.
7. MCP policy tests proving unknown tools are not automatically allowed.
8. Standalone deployment triage with no Salesforce project path.
9. Optional-project triage with explicit/discovered `sfdx-project.json`.
10. Confirmation that external probe files/org artifacts were cleaned up.

## Product-owner verdict

The implementation has a strong core and is materially closer to a real product than the original platform-rewrite proposal. Keep the deployment normalizer, bounded context work, explicit job-ID behavior, org-mismatch defense, doctor/index behavior, and focused subagent concept.

Do **not** merge Phase 1 yet. The current build has three product-architecture failures (install location, MCP-incompatible readonly grounder, mandatory local-project stage), one safety-policy failure (unknown MCP tools allowed), no actual end-to-end Cursor verification, and an unacceptable live-QA cleanup/scope violation. Fix these in the same Phase 1 branch and return another architect-review ZIP.
