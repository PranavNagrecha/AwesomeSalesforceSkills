# Gotchas — Technical Debt Assessment

Non-obvious Salesforce platform behaviors that affect how technical debt is identified, measured, and reported.
Each gotcha names the official source it rests on. Claims that no fetched source confirms carry an inline `UNVERIFIED (date):` marker.

---

## Gotcha 1: Inactive Flow Versions Are Not Harmless

**What happens:** Inactive Flow versions stay in the org after they stop executing. An org with a long history of iterative Flow development accumulates them silently, because each save of a Flow creates a new version and older versions are rarely deleted. UNVERIFIED (2026-10-03): the earlier text of this skill said inactive versions count against a "2,000 Flow version limit per org". The only 2,000 figure in the Metadata API Developer Guide is the `triggerOrder` range for record-triggered flows (1 to 2,000). The sibling skill `flow/flow-deployment-and-packaging` states a 50-versions-per-flow cap instead. The flow limits page lives only in Salesforce Help, which this pass could not fetch, so confirm the current per-flow and per-org caps there before quoting either number.

**When it occurs:** Any org where Flows have been edited many times without periodic version cleanup.

**Why it matters for debt assessment:** Version sprawl makes the version picker unusable and hides which version is the rollback candidate. It is a housekeeping finding even before any cap is reached.

**How to avoid:** Count versions per flow with the Tooling API `Flow` object (`Status` values are `Active`, `Draft`, `Obsolete`, `InvalidDraft`). Delete obsolete versions of retired flows, keeping the most recent inactive version as a rollback reference. The Tooling API Developer Guide (Flow object) says a flow version can be deleted only if it is not active and has no paused interviews, so clear or wait out paused interviews first.

---

## Gotcha 2: Process Builder and Workflow Rules Execute Even When They "Look Inactive"

**What happens:** A Process Builder process or Workflow Rule whose status is `Active` keeps executing regardless of whether the team considers it "legacy" or "replaced." Deactivation is an explicit action. It does not happen when a replacement Flow is created.

**When it occurs:** Teams build a new Record-Triggered Flow to replace an old process but never deactivate the process. Both execute. The process may carry stale logic, send duplicate emails, or write fields the new Flow also writes.

**Why it matters for debt assessment:** Correction (2026-10-03): an earlier version of this gotcha said processes and Workflow Rules run after after-save Record-Triggered Flows. The Apex Developer Guide, "Triggers and Order of Execution", says the opposite. Workflow Rules run at step 11, processes built with Process Builder run at step 13, and after-save record-triggered flows run at step 14. So the new after-save Flow runs last and overwrites what the legacy process wrote, while a before-save Flow (step 3) runs first and can be overwritten by a Workflow field update. Either way the final field value depends on which layer wrote last, and a test with one record rarely exposes it.

**How to avoid:** Inventory status directly, never from team memory. Query the Tooling API `Flow` object for `ProcessType = 'Workflow'` with `Status = 'Active'` (the Tooling API Developer Guide defines `Workflow` as the record change process built in Process Builder), and retrieve `Workflow` metadata per object for active rules. Treat every active legacy automation on an object that also has a Record-Triggered Flow as an overlap finding until proven otherwise.

**Common trap:** Process Builder processes in `Draft` status were never activated. They do not execute, but they create maintenance noise. Include them in the inventory as Low-severity hygiene findings.

---

## Gotcha 3: Dead Apex Classes Consume the Org Code Allowance and Can Block Deployments

**What happens:** Apex classes that nothing calls still exist in the org's codebase. They contribute to:
- **The org Apex code-size limit.** Correction (2026-10-03): this gotcha previously said there is no hard per-org limit. The Apex Developer Guide, "Execution Governors and Limits", sets a maximum of 6 MB for all Apex code in an org (10 MB in scratch orgs). The limit excludes 1GP and 2GP managed package code and classes annotated `@isTest`, and support can raise it. Dead classes spend that allowance. UNVERIFIED (2026-10-03): the earlier claim that large class counts slow Salesforce internal processing has no source in the fetched guides.
- **Test coverage calculations.** The Apex Developer Guide, "Code Coverage Best Practices", says coverage is based on the total number of code lines in the org, so uncovered dead lines pull the org-wide percentage down. A deployment fails if the average coverage of new and existing code is below 75%.
- **Deployment validation.** The Apex Developer Guide ("Writing Tests", in Apex Development Process) requires that all classes and triggers compile before a deploy. A dead class with a broken reference can fail a deployment that never touched it.

**When it occurs:** Classes accumulate as features are retired, integrations are replaced, or package dependencies change.

**How to avoid:** Pull aggregate coverage from the Tooling API `ApexCodeCoverageAggregate` object (`NumLinesCovered`, `NumLinesUncovered`). Cross-reference inbound references with `MetadataComponentDependency` (see Gotcha 6 for its limits). Before deleting, check for dynamic invocation that no dependency scan sees: `Type.forName()`, scheduled job class names, and class names stored as configuration values in Custom Metadata or Custom Settings.

---

## Gotcha 4: Managed Package Components Create Debt You Cannot Modify — Report Separately

**What happens:** Managed packages install Apex classes, Flows, triggers, and permission sets that the org team cannot edit or delete. They can carry debt (deprecated package Flows, broad package permission sets, legacy package Apex) that the org team cannot remediate.

**When it occurs:** Any org with AppExchange packages installed. Each package's namespace-prefixed metadata appears in Setup views and Metadata API retrieves.

**Why it matters for debt assessment:** Correction (2026-10-03): this gotcha previously said a package's Apex counts against the org's overall coverage. The Apex Developer Guide ("@IsTest(OnInstall=true) Annotation") says Apex installed from a managed package is excluded from org-level coverage requirements, and "Code Coverage Best Practices" says the org percentage excludes package-related tests. The exception is a deployment run with the `RunAllTestsInOrg` test level, which does include package code in the computed coverage. Counting package classes as the org's own dead code inflates the remediation backlog with items nobody can fix.

**How to avoid:**
- Filter every finding by namespace (`NamespacePrefix` on `ApexClass`, `MetadataComponentNamespace` on dependency rows). Record namespaced findings as **Vendor Debt: Informational Only**, outside the severity-rated backlog.
- An installed package that nobody uses is still a finding. Its triggers fire on its objects and its permission sets may grant excess access. Record it as "Unused Managed Package" and recommend a business review of whether to uninstall.
- If validation deployments use `RunAllTestsInOrg`, expect a coverage figure that differs from the Developer Console figure, and run that deployment in a sandbox first, as the guide recommends.

---

## Gotcha 5: Coverage Numbers Are Stale Until Tests Are Rerun

**What happens:** A class that shows 0% coverage may simply not have been tested since its last change. The Apex Developer Guide, "Code Coverage Best Practices", says coverage numbers are not refreshed when Apex is updated unless tests are rerun, and the estimate can be incorrect if the org changed since the last run.

**When it occurs:** Assessments that read coverage from the Developer Console or Tooling API without first running the full local test suite. It is worst after a large deployment: the same guide notes that a single deployment of more than 2,000 Apex classes deletes the per-method `ApexCodeCoverage` rows (the aggregate rows survive).

**How to avoid:** Run `sf apex run test --test-level RunLocalTests --code-coverage --result-format json` (Salesforce CLI Command Reference, "apex run test") immediately before collecting coverage evidence. Record the test-run ID and timestamp in the findings report so a reviewer can tell how fresh the coverage figure was.

---

## Gotcha 6: The Dependency API Truncates and Omits Silently

**What happens:** `MetadataComponentDependency` is the obvious source for "who references this class or field". The Tooling API Developer Guide marks it Beta and lists limits that make naive scans incomplete. A Tooling API query returns no more than 2,000 records. Reports are not included in Tooling API dependency queries (Bulk API 2.0 includes them, up to 100,000 records). `count()`, `ORDER BY`, `OFFSET`, `queryMore()` and filters on `MetadataComponentName` or `RefMetadataComponentName` are not supported.

**When it occurs:** An assessor runs one Tooling query for "everything that references X", gets 2,000 rows back, and reports the rest of the org as unreferenced. Or the assessor concludes a field is unused because no report shows up in the Tooling results.

**How to avoid:** Query by component ID (`RefMetadataComponentId = '<18-char id>'`) rather than by name, which the API does not allow anyway. Use Bulk API 2.0 when reports matter or when the result could exceed 2,000 rows. State in the report that the Dependency API is Beta and does not see dynamic references, so "no inbound references" is evidence, not proof.

---

## Gotcha 7: Retired API Versions Fail Hard, Not Gradually

**What happens:** Integration debt on old API versions is not a slow decline. The REST API Developer Guide, "API End-of-Life Policy", says versions 7.0 through 20.0 were retired in Summer '22 and versions 21.0 through 30.0 were retired in Summer '25. A request to a retired version returns `410 GONE`. Salesforce supports each version for at least 3 years from first release and gives at least 1 year of notice before support ends.

**When it occurs:** Middleware, ETL jobs, or Apex callouts to Salesforce endpoints hardcoded to `/services/data/v29.0/` or similar. They work until the retirement release and then fail on every call.

**How to avoid:** Treat any client on version 30.0 or below as a Critical finding (it is already broken or about to be). The same guide recommends the API Total Usage event type to identify requests from old versions. The Object Reference ("EventLogFile Supported Event Types") lists API Total Usage among the event types available in supported editions at no additional cost, and its log rows carry `API_VERSION`, `CLIENT_NAME` and `CONNECTED_APP_NAME`, so every org can run this check. The skill's v50.0 threshold for "upgrade soon" is a planning heuristic, not a platform boundary.

---

## Gotcha 8: A Workflow Field Update Fires Update Triggers a Second Time

**What happens:** The Apex Developer Guide, "Triggers and Order of Execution", step 11, says that when a Workflow Rule performs a field update, the record is updated again and the before update and after update triggers execute one more time, regardless of whether the original operation was an insert or an update. In that second run, `Trigger.old` holds the record as it was before the original update, not the value the user saved.

**When it occurs:** Overlap analysis that lists "one Apex trigger and one Workflow Rule" on an object and rates it Medium. In practice the trigger runs twice per save, and any non-idempotent logic in it (counters, task creation, callout enqueueing) doubles.

**How to avoid:** For every object with an active Workflow field update, record the trigger re-fire in the overlap matrix and check the trigger handler for a recursion guard. Rate non-idempotent trigger logic paired with a Workflow field update as High. Migrating the field update into a before-save flow removes the re-fire.

---

## Gotcha 9: Legacy Automation Runs in No Guaranteed Order

**What happens:** Step 13 of the order of execution in the Apex Developer Guide runs processes built with Process Builder and flows launched by workflow rules "not in a guaranteed order." The guide's own advice is to use record-triggered flows to control order. Record-triggered flows on the same object can be sequenced with the `triggerOrder` field (1 to 2,000, Metadata API Developer Guide, Flow, API 54.0 and later).

**When it occurs:** An org with several active processes on one object. A finding that says "process A runs before process B" is not something the platform promises.

**How to avoid:** Do not write findings or remediation steps that depend on the relative order of two processes. Recommend consolidating them into record-triggered flows with explicit `triggerOrder` values, or into one flow per object and timing. The migration skills `flow/process-builder-to-flow-migration` and `flow/workflow-rule-to-flow-migration` own the cut-over.

---

## Gotcha 10: "Last Fired" Evidence for Triggers Needs Event Monitoring

**What happens:** An earlier version of this skill pointed at an "Apex Trigger Manager in Setup" for a trigger's last execution time. UNVERIFIED (2026-10-03): no Salesforce guide fetched in this pass (Apex Developer Guide, Object Reference, Tooling API, Metadata API, Security Guide) mentions such a page. The documented source of trigger execution evidence is the `EventLogFile` Apex Trigger event type (Object Reference, "EventLogFile Supported Event Types"), which records `TRIGGER_NAME`, `TRIGGER_TYPE`, `ENTITY_NAME` and timing per execution.

**When it occurs:** An assessor wants to prove a trigger is dead before recommending deletion and has no log data.

**How to avoid:** Check whether the org has Event Monitoring. The Object Reference lists only Apex Unexpected Exception, API Total Usage, CORS Violation Record, CSP Violation, Hostname Redirects, Insecure External Assets, Login and Logout as no-cost event types, so Apex Trigger events need the purchased product. It also says querying `EventLogFile` requires the View Event Log Files and API Enabled permissions, and that Shield and Event Monitoring customers get 1 year of log storage by default. Without it, fall back to record-level evidence (the object's `LastModifiedDate` distribution) and mark the "dead trigger" finding as inferred rather than observed.
