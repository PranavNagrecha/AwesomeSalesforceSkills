# Gotchas — Flow Deployment And Packaging

Non-obvious Salesforce platform behaviors that cause real production problems when deploying or packaging Flows.

---

## Gotcha 1: Change Sets ship only the *active* version of a flow

**What happens:** You add `Lead_Routing` to a Change Set in your sandbox. Sandbox has versions 1 through 7, with version 5 currently active. The Change Set carries only version 5. Versions 1–4, 6, and 7 do not migrate.

**When it occurs:** every Change Set deploy for a flow with multiple versions. The behavior is silent — there's no warning that other versions are being dropped.

**How to avoid:** if you need version history in the target org, do not use Change Sets. Use SFDX source deploy for each version sequentially (each as `<status>Active</status>` to bump the active pointer, then `<status>Obsolete</status>` for the final state of older ones), OR accept that the target will only have the single active version, OR migrate via Unlocked Package which preserves version lineage at the package level.

---

## Gotcha 2: FlowAccessPermission does NOT auto-deploy with the flow

**What happens:** Deploy succeeds. Admin tests in their own context — works. End-user opens the related record next morning — "Flow execution failed: Insufficient privileges".

**When it occurs:** any deploy that introduces a flow that requires explicit run access (which is most flows in orgs with restrictive default permissions). FlowAccessPermission lives inside Profile and PermissionSet metadata, not inside the Flow metadata.

**How to avoid:** include the relevant Profile or PermissionSet metadata files in the deploy bundle. Better — deliver flow access via Permission Sets (not Profiles) because Permission Sets are easier to source-control granularly. Smoke-test by impersonating a representative non-admin user before closing the deploy ticket.

---

## Gotcha 3: Obsolete versions accumulate forever — no auto-cleanup

**What happens:** After 100 deploys of the same flow, `FlowDefinition` shows 100 historical versions in Setup → Flows. The Flow Builder version dropdown becomes a wall of "Version 47 (Obsolete) — 2024-08-12T14:22Z".

**When it occurs:** any flow that gets deployed many times over months / years.

**How to avoid:** schedule a quarterly cleanup. Use a Tooling API DELETE on `Flow` rows where `Status = Obsolete` AND the version is older than N. Be careful: deleting an Obsolete version is permanent — there's no recovery. Keep at least the last 5 obsolete versions for forensic / rollback purposes.

```bash
# Inventory obsolete versions older than 6 months.
sf data query \
  --query "SELECT Id, VersionNumber, LastModifiedDate FROM Flow WHERE DeveloperName = 'Lead_Routing' AND Status = 'Obsolete' AND LastModifiedDate < LAST_N_MONTHS:6" \
  --use-tooling-api
```

---

## Gotcha 4: Re-deploying the same flow XML creates redundant version rows

**What happens:** CI flakes. Your deploy pipeline retries `sf project deploy start` against the same source. Salesforce creates a *new* Flow version row for each successful deploy, even if the XML is byte-identical to the previous one.

**When it occurs:** any retry, any re-run of a deploy job, any test of "did the deploy actually go through" by re-running.

**How to avoid:** for legitimate retries within a cutover window, prefer `sf project deploy quick --job-id <validationId>` against the original validation Id rather than re-running `validate`. For accidental double-deploys, accept the redundant version (they're harmless beyond clutter) and clean up later.

---

## Gotcha 5: Flow referencing a missing custom field — deploy succeeds, runtime fails

**What happens:** Your flow includes a Decision element comparing `Account.Region__c = "EMEA"`. The target org doesn't have `Region__c`. The deploy succeeds (the XML is syntactically valid; Salesforce checks the field reference exists by name in the bundle but cannot fully validate at deploy time without strict mode). At runtime, the flow fails on the Decision element with a vague "field not found" error.

**When it occurs:** mostly when the flow source XML predates a refactor that removed the field, OR the field genuinely doesn't exist in the target org because it was never deployed.

**How to avoid:** include the field in the deploy bundle. Run a pre-deploy check via a script that greps the flow XML for `<field>` and `<elementReference>` references and validates each against the target org's schema. Or use a tool like `sfdx-hardis` that does dependency validation pre-deploy.

---

## Gotcha 6: Picklist value reference in flow — silent runtime mismatch

**What happens:** Flow Decision: `Opportunity.StageName = "Closed Lost - Competitor"`. Target org's StageName picklist has only "Closed Lost". Deploy succeeds, flow runs, the Decision branch never matches, every record routes to default — and nobody notices because no error is thrown.

**When it occurs:** any environment where picklist values diverge between source and target. Common when picklists are managed by admins via UI rather than source-controlled.

**How to avoid:** source-control picklist value sets. Validate the target's actual picklist values against the values your flow references *before* deploy. Add a smoke test that exercises every Decision branch with representative data.

---

## Gotcha 7: "Flow Version Conflict" error on deploy

**What happens:** Deploy fails with `cannot deploy a Flow that has been edited in the Flow Builder UI since the source was last retrieved`.

**When it occurs:** an admin clicked "Save As New Version" on the same flow in the target org *after* you extracted the source. Salesforce refuses to deploy because it would silently overwrite the admin's changes.

**How to avoid:** always re-retrieve target state before deploying high-traffic flows. Establish a policy: production flows are not edited in Flow Builder UI in production; all changes go through source-control. For sandboxes, accept that this conflict will happen periodically and have a documented merge workflow.

---

## Gotcha 8: `<status>Active</status>` deploy auto-deactivates without warning

**What happens:** You deploy version 8 with `<status>Active</status>`. Salesforce silently deactivates version 7 (which was active). Live traffic starts running version 8 the moment the deploy succeeds.

**When it occurs:** every Active deploy. There is no "are you sure" prompt, no maintenance-window warning, no opt-in confirmation.

**How to avoid:** for high-stakes changes, deploy with `<status>Draft</status>` and activate manually in a maintenance window. Document this requirement in your deploy runbook. Use peer-review of the source XML to catch unintended `Active` declarations.

---

## Gotcha 9: `--test-level` doesn't run Flow Tests

**What happens:** You wrote a Flow Test (Flow Builder → Tests tab) for `Lead_Routing`. You assume `--test-level RunLocalTests` runs it during deploy. It doesn't.

**When it occurs:** any deploy expecting Flow Tests to gate the deploy. They don't — Flow Tests are a Flow Builder–internal authoring aid, not a deploy gate.

**How to avoid:** write Apex tests that invoke the flow (via `Flow.Interview.<FlowName>` instantiation) for any logic that must be deploy-gated. Apex tests run during `RunLocalTests`. Flow Tests are a developer convenience, not a CI gate.

---

## Gotcha 10: Running user lacks "Manage Flow" → activation fails silently

**What happens:** The deploying user has "Customize Application" but not "Manage Flow". The flow definition deploys, but the activation step fails with `INSUFFICIENT_ACCESS`. Sometimes the deploy reports success overall (flow XML committed) but the active version pointer didn't move.

**When it occurs:** CI service users with narrowly-scoped permissions, or admins recently demoted from a higher-privilege profile.

**How to avoid:** the deploying user must have both "Customize Application" AND "Manage Flow" AND "View All Data" (for Tooling API queries). For CI service users, create a dedicated profile with these permissions documented.

---

## Gotcha 11: API version mismatch between source and org

**What happens:** Flow source has `<apiVersion>62.0</apiVersion>`. Target org is running a release where API 62.0 doesn't exist yet (you're deploying ahead of a release upgrade, or to an org pinned to an older release). Deploy fails with `INVALID_TYPE` or `Invalid API version`.

**When it occurs:** mixed-release environments — sandbox refreshed from a preview-release prod, or scratch org with a different API version than its source-control project.

**How to avoid:** keep `sourceApiVersion` in `sfdx-project.json` aligned with the *lowest* org you deploy to. The flow's `<apiVersion>` should match. When orgs upgrade, bump the source.

---

## Gotcha 12: Deploying with `<status>Obsolete</status>` deactivates without superseding

**What happens:** You deploy a flow with `<status>Obsolete</status>` thinking it's a no-op cleanup. The currently-active version goes Obsolete. The flow stops running entirely (no active version exists).

**When it occurs:** misuse of `Obsolete` status — practitioners assume it means "delete this old version" when it actually means "deactivate the active one without replacing it".

**How to avoid:** use `Obsolete` only when you genuinely want the flow turned off. To deactivate without intent to re-activate, prefer this. To replace with a new version, use `Active` on the new version (which auto-deactivates the old).

---

## Gotcha 13: Subflow deploy ordering when activated separately

**What happens:** You deploy parent `Lead_Routing` as Active and subflow `Sub_Score_Lead` as Draft (forgot to set Active). Parent runs, calls subflow, subflow has no active version → runtime error: `Subflow Sub_Score_Lead has no active version`.

**When it occurs:** mixed-status deploys where the parent is active but a subflow is left in draft state.

**How to avoid:** every subflow that a parent calls must have an active version. Audit the deploy bundle for `<status>` consistency. If a subflow must be in draft (e.g. mid-development), the parent should also be inactive.

---

## Gotcha 14: Change Set "Add Dependent Components" misses FlowAccessPermission

**What happens:** You build a Change Set, click "Add Dependent Components", and assume everything required has been added. Deploy succeeds. End-users can't run the flow.

**When it occurs:** every Change Set with a flow that requires explicit run access. "Add Dependent Components" picks up subflows, custom fields, Apex classes — but not FlowAccessPermission entries on Profiles / PermissionSets.

**How to avoid:** manually add the Profile and PermissionSet metadata to the Change Set. Or stop using Change Sets and migrate to SFDX source.

---

## Gotcha 15: Quick-deploy expires after 10 days

**What happens:** You ran `sf project deploy validate` 12 days ago. You try `sf project deploy quick --job-id <id>`. Fails: `validation has expired`.

**When it occurs:** any quick-deploy attempted more than 10 days after the validation. Salesforce caches test results for 10 days.

**How to avoid:** for slow-moving change requests, re-run validate close to the cutover window. Plan the cutover within 10 days of validation. If a deploy slips, re-validate.

---

## Gotcha 16: Unlocked Package install fails when an org-default flow exists

**What happens:** You install Unlocked Package "ACME Flow Library v1.4" containing flow `Sub_Score_Lead`. Target org already has an unmanaged flow named `Sub_Score_Lead` (e.g. previously created by an admin). Install fails: `name conflict`.

**When it occurs:** any Unlocked Package install where a same-named flow already exists in the target org, especially when the package is using the org's default namespace (no namespace prefix).

**How to avoid:** rename or delete the conflicting org-default flow before installing, OR use a real namespace for the package so flows are prefixed (e.g. `acme__Sub_Score_Lead`).

---

## Gotcha 17: Managed Package upgrade can lock you out of editing

**What happens:** A managed package ships flows. Recipients install. Recipients try to edit the flow in Flow Builder — read-only.

**When it occurs:** any Managed Package install. Managed Packages lock metadata to protect the ISV's IP.

**How to avoid:** if recipients need to customize, ship as Unlocked Package instead. Or expose extension points (subflows, invocable Apex parameters) that let recipients build adjacent flows that call the managed flow.

---

## Gotcha 18: `sf project deploy start` doesn't deploy `Flow` test data

**What happens:** Your sandbox flow has Flow Tests authored in Flow Builder. You deploy the flow. The Flow Tests don't travel.

**When it occurs:** every flow deploy. Flow Tests are stored separately from the flow definition and are not part of the standard `Flow` metadata type.

**How to avoid:** treat Flow Tests as authoring aids that live only in the org where they were created. Don't rely on Flow Tests for cross-org test coverage. Use Apex tests instead.

---

## Gotcha 19: Active version count exceeds 50 limit

**What happens:** Salesforce limits each FlowDefinition to 50 versions total (active + obsolete + draft). When you try to save the 51st, the deploy fails: `flow limit exceeded`.

**When it occurs:** flows that have been iterated weekly for over a year without obsolete-version cleanup.

**How to avoid:** the quarterly cleanup mentioned in Gotcha 3 is not optional for high-iteration flows — it's required to stay under the 50-version limit. Delete obsolete versions before they pile up.

---

## Gotcha 20: Two-step deploy creates window where neither version is active

**What happens:** You deploy old version with `<status>Obsolete</status>` first (to "clean up"), then plan to deploy new version with `<status>Active</status>` next. Between the two deploys, there is a window — sometimes seconds, sometimes minutes — where no version of the flow is active. Live traffic during this window silently misses automation.

**When it occurs:** any cutover that splits deactivation and activation into two separate deploy transactions.

**How to avoid:** deploy the new Active version directly. Salesforce auto-deactivates the prior. The transition is atomic from the user's perspective. Don't pre-deactivate.
