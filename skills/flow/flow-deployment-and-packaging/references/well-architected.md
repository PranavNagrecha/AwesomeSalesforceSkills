# Well-Architected Notes — Flow Deployment And Packaging

## Relevant Pillars

This skill's primary pillars are **Operational Excellence** and **Reliability**. Performance and Scalability are not directly impacted (deployment is a control-plane operation, not a runtime one). Security touches the edges (deploying-user permissions, FlowAccessPermission delivery) but isn't the central concern.

### Operational Excellence

The single biggest operational-excellence move in flow deployment is **validate-then-quick-deploy**. Without it, every production deploy is a coin flip: test failures surface inside the maintenance window, turning a 5-minute change into a 65-minute outage risk. With it, the actual production change is sub-minute and predictable, because all the heavy lifting (compile + test) happens hours earlier in a non-blocking validation run.

Additional operational moves:

- **Source of truth is Git, not Flow Builder.** Every flow change starts in source-control. Flow Builder UI edits in production are emergency-only, with a documented back-port rule (any in-prod edit must be merged into source within 24 hours). Without this rule, source drifts from reality and every future deploy hits Flow Version Conflict.
- **Deployment runbooks per flow type.** Record-triggered flows have different cutover requirements (low/zero downtime windows) than scheduled flows (run during off-hours regardless of when deployed). The runbook captures the right window per flow.
- **Post-deploy verification is mandatory.** A deploy isn't done until a Tooling API query confirms the new active VersionNumber AND a smoke test executes a known-good input through the new version. Without this gate, "deploy succeeded" is just an Apex Manager green checkmark, not actual evidence the flow runs.
- **Quarterly obsolete-version cleanup.** Beyond ~50 versions, the FlowDefinition hits a hard limit. Before that, the version dropdown becomes unusable. Schedule the cleanup; don't wait for a deploy to fail.

### Reliability

Flow deployment reliability hinges on two things: **dependency completeness** and **rollback availability**.

**Dependency completeness:** A flow that references a missing subflow fails to deploy (loud). A flow that references a missing custom field can either fail to deploy (loud) or pass deploy and fail at runtime (silent). Picklist values, RecordType DeveloperNames, and formula references especially fall into the silent category. Reliable deploys validate dependencies *before* the deploy command runs — via a pre-deploy script that greps the source XML and queries the target org's schema.

**Rollback availability:** every Active deploy preserves the prior version as Obsolete in the org. Rollback is a metadata-only operation (re-activate via Tooling API PATCH on FlowDefinition.ActiveVersionNumber), not a redeploy. This is the fastest possible recovery path — sub-minute. Reliable orgs:

- Document the prior `VersionNumber` in every deploy ticket.
- Smoke-test the rollback path itself in non-prod (proving the prior version still works against current data).
- Keep at least the last 5 obsolete versions un-deleted in production at all times.
- Treat "Active deploy auto-deactivates prior" as a guaranteed-recoverable operation, but `<status>Obsolete</status>` deploys (which deactivate without superseding) as semi-irreversible — once you Obsolete the active version, recovery requires either re-deploying Active or manually re-activating in the UI.

### Performance

Deployment is a control-plane activity. It does not affect runtime flow performance. Performance considerations are limited to deployment *time* itself:

- `validate` + `quick` keeps cutover-window performance crisp.
- Deploying small bundles (single flow + immediate deps) is faster than full-org redeploys.
- Test-level choice dominates deploy duration — `RunLocalTests` is typically 30–90 minutes; `RunAllTestsInOrg` can be 2–6 hours in mature orgs.

Runtime performance of the deployed flow itself is governed by `flow/flow-performance-optimization` and `flow/flow-governor-limits-deep-dive`, not by anything in this deployment skill.

### Scalability

Not a primary pillar concern. Deployment volume scales linearly with team activity (more developers → more deploys), but Salesforce's deployment API handles enterprise-scale orgs without issue. The scalability limit that does matter is the **50-version-per-FlowDefinition** cap, addressed by quarterly obsolete cleanup.

### Security

Edge concerns:

- **Deploying user's permissions.** A CI service user with overly-broad permissions (e.g. "Modify All Data") is a security risk. Scope to "Customize Application" + "Manage Flow" + "View All Data" (for Tooling API queries) and nothing more.
- **FlowAccessPermission delivery.** Forgetting to deploy permission entries means flows fail open (admin can run, end-users can't) — annoying, not security-critical. Forgetting in the *other* direction (granting access too broadly) is the security risk. Audit FlowAccessPermission grants in the deploy bundle.
- **Managed-package flow secrets.** If a flow contains hard-coded credentials (anti-pattern), packaging exposes them. Use Named Credentials and Custom Metadata Type pointers instead.

---

## Architectural Tradeoffs

### Tradeoff 1 — Change Set vs SFDX vs Unlocked Package

| Dimension | Change Set | SFDX Source | Unlocked Package |
|---|---|---|---|
| Setup cost | Zero (UI-driven) | Medium (sfdx-project.json, branch strategy) | High (package definition, version pinning, scratch-org config) |
| Per-deploy cost | High (manual UI work) | Low (CLI command) | Medium (CLI + version-build step) |
| Auditability | Poor (Change Set log only) | Excellent (Git commit history) | Excellent (Git + package version lineage) |
| Rollback | Re-deploy prior Change Set (slow, manual) | Re-deploy prior commit / re-activate prior version | Install prior package version (clean) |
| Multi-org distribution | Painful (one CS per target) | Manageable (one source, N deploys) | Designed for it (one package, N installs) |
| Best for | One-off admin-driven migration | Standard developer flow | Reusable libraries shipped to many orgs |

**Default to SFDX source.** Graduate to Unlocked Package when a flow library starts shipping to 3+ orgs. Use Change Set only when blocked by tooling constraints (no Git access, admin without CLI familiarity, sandbox-to-prod for a single trivial change).

### Tradeoff 2 — Active deploy vs Draft + manual activation

| Dimension | Active deploy | Draft + manual activation |
|---|---|---|
| Cutover atomicity | High (deploy = cutover) | Lower (two operations, with a window between) |
| Smoke-test window | None — live traffic immediately | Yes — test against the deployed-but-inactive version |
| Operational complexity | Lower (one CLI command) | Higher (deploy + deferred Tooling API PATCH) |
| Risk profile | Higher (no test gate after deploy) | Lower (chance to abort before activation) |
| Best for | Routine, low-risk changes | High-stakes, business-critical changes |

Choose based on blast radius. A label-only change in a screen flow → Active. A complete restructure of an Opportunity stage automation → Draft + manual activation in maintenance window.

### Tradeoff 3 — Bundle dependencies together vs deploy in sequence

| Dimension | Bundle together | Deploy in sequence |
|---|---|---|
| Atomicity | Yes (all-or-nothing transaction) | No (each step commits independently) |
| Rollback complexity | Single-step rollback (re-activate priors) | Multi-step rollback (reverse each deploy in order) |
| Deploy time | Single longer deploy | Multiple shorter deploys |
| Diagnosis on failure | Clearer (one bundle, one error report) | Murkier (which step's deploy left the org in this state?) |

Default to bundle-together. Sequence deploys only when bundle size exceeds practical limits (10K+ files, very rare).

---

## Anti-Patterns

1. **Deploying without validation.** Running `sf project deploy start` directly to prod with `--test-level RunLocalTests` means tests run *during* the cutover window. A test failure turns a 5-minute change into a 65-minute risk. Always validate-then-quick-deploy for prod.

2. **Editing production flows in Flow Builder UI.** Drift between Git source and prod active version. Future deploys hit Flow Version Conflict, OR worse, silently overwrite the in-prod edit. Production flows are read-only outside the deploy pipeline. Emergency-edits get back-ported to source within 24 hours, no exceptions.

3. **Forgetting FlowAccessPermission in the deploy bundle.** End-users get "Insufficient privileges" the morning after deploy. Not a security risk per se, but a reliability and customer-experience hit. Always include Profile / PermissionSet metadata when flow access requirements change.

4. **Using Change Sets when Unlocked Package is the right answer.** Teams shipping the same flow library to 5+ internal orgs via Change Sets are paying a per-org migration tax indefinitely. Pay the one-time setup cost of Unlocked Package, then ship a single package version to all orgs.

5. **Skipping rollback documentation.** Deploy ticket says "deployed v12, looks good." When v12 corrupts data at 3am, the on-call engineer has to spelunk through Flow Builder history to find v11. Document the prior `VersionNumber` and rollback Tooling API command in the deploy ticket *before* clicking deploy.

6. **`--ignore-errors` on prod deploys.** Partial-success deploys leave the org in a half-migrated state — parent flow active, dependent subflow missing. Hard to diagnose, harder to roll back. Never use `--ignore-errors` against production.

---

## Official Sources Used

- Salesforce DX Developer Guide — Deploy and Retrieve: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_deploy_and_retrieve.htm
- Salesforce DX Developer Guide — Quick Deploy: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_deploy_quick.htm
- Salesforce DX Developer Guide — Second-Generation Managed and Unlocked Packages: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- Metadata API Developer Guide — Flow / FlowDefinition: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flow.htm
- Salesforce Architects — Application Lifecycle Management: https://architect.salesforce.com/decision-guides/alm/
- Salesforce Help — Activate or Deactivate a Flow Version: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_activate.htm
- Salesforce Help — Considerations for Deploying Flows: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_considerations.htm
