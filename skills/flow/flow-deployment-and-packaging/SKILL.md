---
name: flow-deployment-and-packaging
description: "Move a Flow from sandbox to production reliably — source format, version-on-deploy semantics, deploy vs activate, dependency bundling, Change Set vs SFDX vs Unlocked vs Managed, validate-then-quick-deploy, and rollback by activating a prior version. NOT for source-driven setup or branching strategy — see devops/salesforce-dx-project-structure and devops/source-tracking-and-conflict-resolution."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "deploy a flow from sandbox to prod"
  - "flow version conflict on deploy"
  - "change set vs unlocked package for flows"
  - "sf project deploy validate flow"
  - "flow active version not deploying"
  - "flow deploy succeeded but FlowAccessPermission missing"
  - "rollback a flow after a bad release"
tags:
  - flow-deployment-and-packaging
  - devops
  - flow
  - packaging
  - sfdx
  - unlocked-package
  - change-set
  - rollback
inputs:
  - The Flow source file(s) — `force-app/main/default/flows/<FlowName>.flow-meta.xml`
  - Target org alias and API version
  - Deployment package shape (Change Set / SFDX source / Unlocked Package / Managed Package)
  - List of dependent metadata (subflows, Apex invocables, custom fields, picklist values)
  - Deploying user's profile and permission sets
outputs:
  - Deployment plan (validate → quick-deploy sequence)
  - Dependency bundle list
  - Activation order for multi-flow / flow + Apex deploys
  - Rollback steps (prior `<status>Active</status>` redeploy or manual reactivation)
  - Permission delivery checklist (FlowAccessPermission, RunFlow system permission)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-27
---

# Flow Deployment And Packaging

Activate when a Flow needs to move between orgs (sandbox → UAT → prod, scratch org → packaging org, ISV release) and the question is *which* deployment shape, *what* must travel with it, and *how* to roll it back without breaking the active version chain.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Target org API version.** The `sourceApiVersion` in `sfdx-project.json` and the `<apiVersion>` inside the `.flow-meta.xml` must be ≤ the target org's release. A flow saved at API 62.0 will not deploy to a Spring '25 org running API 63.0+ if the org is on a lower release.
- **Deploying user's profile and permission sets.** The user must hold "Modify Metadata Through Metadata API Functions" or "Customize Application", AND "Manage Flow" for activating. If the user lacks Manage Flow, an `<status>Active</status>` deploy fails with `INSUFFICIENT_ACCESS`.
- **Dependent metadata already in the target org.** A flow referencing `Account.Custom_Field__c`, an invocable Apex class `MyInvocable`, a subflow `Sub_Validate_Lead`, or a picklist value `Stage = "Closed Lost"` must have those dependencies present *before or alongside* the flow deploy. Missing dependencies either fail the deploy (subflow, Apex, custom field) or — silently — pass deploy and fail at runtime (picklist values, formula references, RecordType DeveloperName lookups).
- **Existing active version in target.** Run `sf data query --query "SELECT Id, VersionNumber, Status FROM Flow WHERE DeveloperName = '<FlowName>'" --use-tooling-api` to see what's already there. Knowing the current active version is a precondition for a safe rollback plan.
- **Most common wrong assumption:** "Deploy = activate." Deploying a flow with `<status>Draft</status>` puts it in the org but does NOT make it run. Practitioners forget this and wonder why their automation didn't fire after a successful deploy.

---

## Core Concepts

### Concept 1 — Flow source XML and the `<status>` field

In source format, a flow lives at `force-app/main/default/flows/<FlowName>.flow-meta.xml`. The metadata API name keeps the `.flow` extension; SFDX source format adds `-meta.xml`. A single file represents one *definition*; the org tracks *versions* of that definition separately in `Flow` and `FlowDefinition` Tooling API objects.

The `<status>` element is the activation control:

| Status value | Meaning on deploy |
|---|---|
| `Active` | Deploys as a new version AND makes it the active version. Auto-deactivates the previously active version. |
| `Draft` | Deploys as a new version in Draft state. Does not change which version is active. |
| `Obsolete` | Deactivates whatever version is currently active. Does not create a new version. |
| `InvalidDraft` | Reserved — a draft that failed validation. You generally do not deploy this status. |

The `<processType>` element is mandatory and not inferred. Common values: `AutoLaunchedFlow`, `Flow` (screen), `RecordBeforeSave`, `RecordAfterSave`, `InvocableProcess` (legacy Process Builder), `CustomEvent` (platform event triggered). Missing `<processType>` causes a deploy error: `Required field is missing: processType`.

### Concept 2 — Versioning on deploy: every Active deploy creates a new Flow Version

Salesforce never overwrites a Flow version in place. Every `<status>Active</status>` deploy creates a brand-new version row, increments `VersionNumber`, and deactivates the prior active version (which stays in the org as `Status = Obsolete`). Over a year of weekly deploys, a single flow can accumulate 50+ obsolete versions. There is no automatic cleanup — you must delete obsolete versions explicitly via the UI or a Tooling API call.

Implications:

- **Storage / clutter, not breakage.** Old versions don't run; they just sit in the FlowDefinition history. But the Flow Builder version dropdown becomes unwieldy.
- **Rollback is "activate prior version", not "delete current".** You cannot un-deploy a version. You activate an older one to supersede it (which itself creates… another version row, or just flips the active pointer if you do it via UI / Tooling API).
- **Re-deploying the same XML twice creates two identical versions.** If your CI runs the same SFDX deploy twice (e.g. a re-run after a flake), you get two identical version rows.

### Concept 3 — Deploy vs Activate (they are NOT the same step)

Two distinct operations:

1. **Deploy** — Move the source XML into the target org. After this, the flow definition exists, but its activation state depends on the `<status>` field in the XML you deployed.
2. **Activate** — Flip the active-version pointer in `FlowDefinition` to point at a specific Flow version. Done automatically by `<status>Active</status>` in source XML, OR manually via the UI ("Activate" button on the version row), OR programmatically via Tooling API `PATCH /tooling/sobjects/FlowDefinition/<Id>` with `ActiveVersionNumber`.

The "deploy with Draft, activate later via UI" pattern is common when ops wants a controlled cutover window separate from the deploy window. Useful for high-stakes changes where the deploy can run during business hours but the activation must happen during a maintenance window.

### Concept 4 — `--test-level` and Flow deploys

`sf project deploy start` `--test-level` flag controls Apex test execution. It does NOT run Flow Tests (Flow Tests are a separate Flow Builder–internal framework). Behavior:

| Flag | What runs | Flow impact |
|---|---|---|
| `NoTestRun` | No Apex tests | Allowed only in sandboxes. Flow deploys without test validation. |
| `RunSpecifiedTests` | Only the named test classes | If your flow calls invocable Apex, the invocable's test must be named explicitly or it won't run. |
| `RunLocalTests` | All non-namespaced tests | Production default. If the flow calls invocable Apex `X`, then `X`'s test class must exist and pass — and Apex 75% coverage rule still applies to the org as a whole, including the invocable class. |
| `RunAllTestsInOrg` | All tests including managed | Slowest. Use when an upgrade might affect managed-package tests. |

Flow has no coverage requirement of its own. The 75% rule applies only to Apex.

---

## Common Patterns

### Pattern 1 — Validate-Then-Quick-Deploy (the canonical CI/CD shape)

**When to use:** every production deploy. Splits the slow part (compile + tests) from the fast part (apply changes), so the cutover window is minutes, not hours.

**How it works:**

```bash
# Step 1 — Validate (runs all tests, takes 30–90 min in a real org).
sf project deploy validate \
  --source-dir force-app \
  --target-org prod \
  --test-level RunLocalTests \
  --wait 90

# Capture the validation Id from the output, e.g. 0Af5g00000xxxxxxx.

# Step 2 — Quick deploy (within 10 days of the validation; reuses test results).
sf project deploy quick \
  --job-id 0Af5g00000xxxxxxx \
  --target-org prod \
  --wait 30
```

**Why not the alternative:** running `sf project deploy start --test-level RunLocalTests` directly during the cutover means tests run *during* the maintenance window. A 60-minute test run plus a failure means another 60 minutes after the fix. Validate-then-quick-deploy keeps the actual production change to under 5 minutes for most flow-only deploys.

### Pattern 2 — Bundle Flow + Subflow + Apex Together

**When to use:** the flow being deployed references a subflow, an invocable Apex class, or a custom field that is not yet in the target org.

**How it works:** include all dependencies in a single SFDX deploy package or single Change Set:

```bash
sf project deploy start \
  --source-dir force-app/main/default/flows/Lead_Routing.flow-meta.xml \
  --source-dir force-app/main/default/flows/Sub_Score_Lead.flow-meta.xml \
  --source-dir force-app/main/default/classes/LeadRouter.cls \
  --source-dir force-app/main/default/classes/LeadRouter.cls-meta.xml \
  --source-dir force-app/main/default/objects/Lead/fields/Routing_Score__c.field-meta.xml \
  --target-org prod
```

Or use a `package.xml` manifest. Salesforce computes the dependency graph and deploys in the correct order — subflows before parents, fields before flows that reference them, Apex classes before flows that call them.

**Why not the alternative:** deploying the parent flow alone gives `Subflow Sub_Score_Lead does not exist`. Deploying the subflow first as a separate transaction works but doubles the deploy windows and makes rollback harder (which deploy do you reverse?).

### Pattern 3 — Deactivate-Activate Sequence for Cutover

**When to use:** swapping a complex flow during a maintenance window where you need to verify the new version with smoke tests *before* it starts handling live traffic.

**How it works:**

1. Deploy new flow with `<status>Draft</status>`. The new version exists in the org but isn't active.
2. (Optional) Deploy the prior active flow with `<status>Obsolete</status>`. This deactivates the current active version. The flow stops running — useful if you want a "frozen" window during cutover.
3. In the maintenance window, navigate to Setup → Flows → click the new draft version → Activate.
4. Smoke-test by triggering a known input.
5. If smoke fails, click Activate on the prior version to revert.

**Why not the alternative:** deploying directly with `<status>Active</status>` means the new version starts handling live traffic the moment the deploy finishes — no smoke-test window, no controlled flip.

---

## Decision Guidance

| Deployment Shape | Best Use Case | Trade-offs |
|---|---|---|
| **Change Set** | One-off admin-led migration sandbox → prod for a single flow + 1–2 dependencies. No CI/CD. | Manual UI clicks. Carries only the *active* version. Does not carry FlowAccessPermission. No version history. Cannot validate-then-quick-deploy. |
| **SFDX source deploy** | Standard developer / DevOps workflow. Source-controlled in Git, deployed via CLI from CI. | Requires `sfdx-project.json` setup. Best balance of automation + flexibility. Supports validate-then-quick-deploy. |
| **Unmanaged Package** | One-time distribution to many orgs (training orgs, demo orgs). | Cannot upgrade in place. Recipients can edit (which breaks future re-installs). Largely deprecated for new work. |
| **Unlocked Package (2GP)** | Internal teams shipping reusable flows / subflows across many internal orgs. Or open-source distribution. | Best long-term answer for shared subflow libraries. Versioned, upgradable in place, no namespace required (org-default namespace OK). Steeper learning curve than SFDX source. |
| **Managed Package (2GP)** | ISV distribution on AppExchange. Locked metadata, namespace-prefixed. | IP-protected (recipients cannot edit). Strict upgrade rules (no breaking changes to public API). Requires a packaging org and security review. |

Rule of thumb: **default to SFDX source.** Only graduate to Unlocked Package when the *same* flow / subflow library needs to ship to multiple orgs. Only graduate to Managed when you're an ISV.

---

## Recommended Workflow

1. **Inventory the flow + its dependencies.** Run `sf project retrieve start --metadata Flow:<FlowName>` to pull current state. Open the `.flow-meta.xml` and grep for: `<flowName>` (subflow refs), `<actionName>` with `<actionType>apex</actionType>` (Apex refs), `<object>` and `<field>` (custom field refs), `<value>` inside picklist filters (picklist value refs).
2. **Verify dependencies in the target org.** For each dependency, run a tooling-API query or use `sf project retrieve start --metadata <Type>:<Name> --target-org prod`. If anything is missing, add it to the deploy bundle.
3. **Validate the deploy.** `sf project deploy validate --source-dir <bundle> --target-org prod --test-level RunLocalTests --wait 90`. Capture the validation Id. Treat any test failure as a hard stop.
4. **Plan activation strategy.** If high-risk, deploy with `<status>Draft</status>` and activate manually in the maintenance window. If low-risk, deploy with `<status>Active</status>` directly via quick-deploy.
5. **Quick-deploy in the cutover window.** `sf project deploy quick --job-id <validationId> --target-org prod --wait 30`. Confirm the new active version number with a Tooling API query.
6. **Verify FlowAccessPermission and RunFlow system permission.** Profiles / permission sets controlling who can run the flow must be deployed separately if changed. Spot-check by impersonating a typical end-user.
7. **Document rollback steps.** Record the prior active `VersionNumber` in the deployment ticket so an oncall engineer can re-activate it without spelunking through Flow Builder history.

---

## Review Checklist

- [ ] All dependent metadata (subflows, invocable Apex, custom fields, RecordTypes, picklist values) is included in the deploy bundle OR confirmed already present in target.
- [ ] `<processType>` is set in the `.flow-meta.xml`. (Missing → deploy fails.)
- [ ] `<status>` is set deliberately — `Active` for direct cutover, `Draft` for staged activation.
- [ ] Validation ran with `--test-level RunLocalTests` (or `RunAllTestsInOrg` if managed-package interaction expected) and passed within the 10-day quick-deploy window.
- [ ] Rollback plan documents the prior `VersionNumber` and the activation command (UI click or Tooling API PATCH).
- [ ] FlowAccessPermission and RunFlow system permission delivered to required profiles / permission sets.
- [ ] Obsolete-version cleanup considered if the org has > 30 historical versions of this flow.
- [ ] Post-deploy smoke test plan (record a known-good input, verify flow ran via Flow Interview log).

---

## Salesforce-Specific Gotchas

1. **`<status>Active</status>` deploy auto-deactivates the prior active version** — there is no warning, no confirmation step, no "are you sure". The moment the deploy succeeds, live traffic flips to the new version. If you wanted a staged cutover, you needed to deploy as `Draft` first.
2. **FlowAccessPermission does NOT auto-deploy with the flow.** A flow that requires explicit access via `FlowAccessPermission` on a profile or permission set needs that permission deployed separately. Symptom: end-users hit "Flow execution failed: Insufficient privileges" after an apparently-successful deploy.
3. **Change Sets carry only the *active* version of a flow.** If your sandbox has versions 1–7 with version 5 active, the Change Set ships only version 5. Versions 1–4, 6, and 7 stay behind. No way to migrate a non-active version via Change Set — must use SFDX or recreate manually.
4. **Obsolete versions accumulate forever.** Every Active deploy adds a row. After 50–100 deploys, the FlowDefinition version dropdown becomes hard to navigate. There's no built-in archival; you must delete obsolete versions via UI (Setup → Flows → version row → Delete) or via Tooling API DML on the `Flow` sObject.
5. **Flow referencing a not-yet-deployed custom field deploys successfully but fails at runtime.** Picklist *values* especially: if your flow's Decision element checks `Stage = "Closed Lost - Competitor"` but the target org's picklist has only `Stage = "Closed Lost"`, the deploy passes (the flow XML is syntactically valid) and the flow runs — but the Decision branch never matches, silently routing every record to the default path.
6. **"Flow Version Conflict" on deploy.** Happens when the active version in the target org has been edited via Flow Builder *after* the source you're deploying was extracted. Salesforce refuses to deploy because applying your version would silently overwrite an admin's in-org changes. Resolution: re-retrieve the target's current active version, manually merge into source, re-deploy.
7. **`--ignore-errors` on a flow deploy is dangerous.** It allows partial deploys where some flows succeed and others fail. You can end up with a parent flow active in the org while its dependent subflow failed to deploy — a runtime error waiting to happen. Use only for non-flow components and never for prod.
8. **Re-running the same deploy creates redundant version rows.** If your CI flakes and you re-trigger, you'll get two identical Flow versions. Not breaking, but pollutes the version history. Prefer re-running `sf project deploy quick` against the original validation Id rather than re-running `validate`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Deployment plan | Step-by-step: validate command, quick-deploy command, activation strategy (Active vs Draft + manual), maintenance window if any. |
| Dependency bundle list | Explicit list of every metadata file included in the deploy package — flows, subflows, Apex classes + meta, custom fields, RecordTypes, picklist value sets. |
| Activation order document | For multi-flow deploys, the sequence of activations and any required deactivations. |
| Rollback plan | Prior `VersionNumber` for each deployed flow, the Tooling API PATCH command or UI step to re-activate it, and the smoke-test that confirms rollback success. |
| Permission delivery checklist | FlowAccessPermission and RunFlow system permission entries that must travel with the flow on any profile or permission set change. |
| Post-deploy verification log | Tooling API query results confirming new active VersionNumber, plus smoke-test interview logs. |

---

## Related Skills

- `devops/salesforce-dx-project-structure` — how the `force-app/main/default/flows/` directory and `sfdx-project.json` integrate with broader source control. Use first if the org is migrating off Change Sets.
- `devops/source-tracking-and-conflict-resolution` — handling source-tracking conflicts that surface as Flow Version Conflict errors during scratch-org and sandbox deploys.
- `devops/unlocked-package-development` — when a Flow + subflow library needs to ship to multiple internal orgs, graduate from SFDX source deploy to 2GP.
- `flow/flow-versioning-strategy` — naming conventions, version hygiene, and obsolete-version cleanup policy.
- `flow/flow-rollback-patterns` — detailed rollback playbooks beyond the basic "activate prior version" mechanic.
- `flow/flow-deployment-activation-ordering` — multi-flow deploys where activation order matters (e.g., a parent flow that depends on a newly-activated subflow).
- `devops/change-set-deployment` — when you must use Change Sets despite their limitations.

---

## Official Sources Used

- Salesforce DX Developer Guide — Deploy and Retrieve: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_deploy_and_retrieve.htm
- Salesforce DX Developer Guide — Second-Generation Managed and Unlocked Packages: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- Metadata API Developer Guide — Flow type: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flow.htm
- Metadata API Developer Guide — FlowDefinition type: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flowdefinition.htm
- Salesforce Help — Activate or Deactivate a Flow Version: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_activate.htm
- Salesforce Help — Deploy Flows in Change Sets: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_change_set.htm
- Salesforce CLI Command Reference — `sf project deploy validate` / `quick`: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm
- Salesforce Architects — Application Lifecycle Management: https://architect.salesforce.com/decision-guides/alm/
