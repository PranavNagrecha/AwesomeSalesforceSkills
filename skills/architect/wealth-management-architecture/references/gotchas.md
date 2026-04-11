# Gotchas — Wealth Management Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Scoring Framework Objects Are Invisible Without CRM Plus License

**What happens:** Flows, Apex classes, or page layout components that reference FSC Scoring Framework objects (such as `FinServ__ScoringRecord__c` or the scoring configuration objects) do not fail at deployment. The deployment succeeds, but at runtime the components return no data or render blank. Setup does not surface the Scoring configuration UI. There is no error message pointing to the license gap.

**When it occurs:** Any FSC org that purchased base FSC without the CRM Plus add-on license. This is common for smaller wealth management clients who purchased FSC Starter or FSC Growth before understanding the analytics feature dependency. It also occurs when a sandbox is provisioned with different license allocations than production.

**How to avoid:** Before scoping any advisor analytics feature that involves scoring, run a license verification step. In Setup > Company Information > User Licenses, confirm `CRM Plus` is listed. Alternatively, run `SELECT Name FROM UserLicense WHERE Name LIKE '%CRM Plus%'` in the Developer Console. If not present, escalate to Salesforce account team before proceeding with scoring architecture.

---

## Gotcha 2: Compliant Data Sharing Activation Removes Record Visibility for All Existing Records

**What happens:** When CDS is enabled on an object type that already contains records, every existing record immediately loses its sharing entries. The records exist in the database but become invisible to all advisors until the sharing recalculation batch runs and completes. The effect is total — it is not partial or gradual. Advisors log in after the activation window and see zero records for the enrolled object type.

**When it occurs:** Any org that activates CDS on an object type that was previously using standard Salesforce sharing (org-wide defaults, role hierarchy, or sharing rules). Orgs that run the CDS activation during business hours while advisors are active cause immediate and visible disruption.

**How to avoid:** Always activate CDS in a maintenance window. Immediately after activation, queue the FSC sharing recalculation batch for the enrolled object type. Do not close the maintenance window until the batch completes and a spot-check query confirms `Share` records exist for the object. Test the full activation-plus-recalculation sequence in a full-copy sandbox with production data volume before production activation.

---

## Gotcha 3: `enableWealthManagementAIPref` Silently Fails on API Versions Below v63.0

**What happens:** When a team retrieves or deploys `IndustriesSettings` metadata using an API version earlier than 63.0 (Spring '25), the `enableWealthManagementAIPref` field is not recognized. On retrieve, the field is omitted from the retrieved XML — giving a false impression that it is not set. On deploy, the field is silently ignored — the flag is never enabled even though the deployment reports success.

**When it occurs:** Projects where `sfdx-project.json` has `sourceApiVersion` set to `62.0` or earlier (Winter '25 or prior). CI/CD pipelines that pin the API version for stability also hit this. The field was introduced in API v63.0.

**How to avoid:** Confirm `sourceApiVersion` in `sfdx-project.json` is `63.0` or higher before working with this flag. Run `sf org display --target-org <alias>` to confirm the target org supports API v63.0. If the org is on a pre-Spring '25 release, the feature is not available — no workaround exists.

---

## Gotcha 4: Bulk API 2.0 Job Completion Does Not Trigger FSC Rollup Recalculation

**What happens:** After a Bulk API 2.0 ingest job completes loading `FinServ__FinancialAccountTransaction__c` records, FSC rollup fields (Net Worth, Total Assets, Total Liabilities on `FinServ__FinancialAccount__c`) do not automatically update. The transaction records are present in the database but the advisor dashboard still shows stale portfolio totals from the previous run.

**When it occurs:** Bulk API ingest bypasses standard Apex triggers and before/after DML trigger contexts. The FSC rollup engine is trigger-driven; when triggers do not fire, rollup jobs are never queued.

**How to avoid:** After each successful Bulk API 2.0 ingest job, explicitly enqueue the FSC rollup recalculation. This can be done by firing a Platform Event that a trigger subscribes to, by scheduling a batch Apex job that touches the parent `FinServ__FinancialAccount__c` records (forcing a rollup recalculation), or by using the FSC-provided rollup recalculation invocable action from a scheduled Flow. Document this as an explicit post-load step in the custodian integration runbook.

---

## Gotcha 5: Financial Deal Management Junction Objects Are Not Queryable Without `enableDealManagement`

**What happens:** SOQL queries against Interaction-to-Deal junction objects fail with an "object not found" error in orgs where Deal Management is not enabled. This is an expected behavior but catches teams who assume the objects are always present in FSC orgs. It also blocks sandbox refreshes where the IndustriesSettings flag was deployed in production but the sandbox metadata was created before the deployment.

**When it occurs:** Any org or sandbox where `enableDealManagement` was not explicitly deployed via IndustriesSettings. Also occurs when using Scratch Orgs built from feature definitions that do not include the Deal Management feature.

**How to avoid:** Include `enableDealManagement` in the `IndustriesSettings` metadata deployed to all environments (sandbox, scratch org, production). In scratch org feature definitions, add `FinancialDealManagement` to the `features` array. Do not assume that FSC product license automatically activates Deal Management.
