# Examples — Managed Package Installation And Upgrade

## Example 1: Sandbox-first install of a new revenue-recognition package

**Context:** Finance has signed contracts with a vendor whose AppExchange package promises automated revenue recognition. The package is 1GP, has passed Security Review, is version 4.2.1, and adds two Custom Objects, six Custom Fields on `Opportunity`, and an `InstallHandler` that seeds default Custom Settings. The team has 450 users in production. Vendor docs say "Install for All Users."

**Problem:** Installing directly in production using the vendor's recommendation grants every user CRUD on the two new objects via the bundled profile updates. The finance team wants only 12 users to use the feature initially, and Security has standing guidance to avoid profile-based grants for managed packages. The org also runs an existing `Opportunity` trigger framework that handles 100k records on close-date updates — vendor docs do not mention how their managed code interacts with subscriber triggers.

**Solution:**

1. Resolve version ID from the vendor: `04t8b000001abcdAAB`. Confirm it appears as "Released" (not "Beta") in their packaging documentation.
2. Install in a Developer Sandbox first using `https://test.salesforce.com/packaging/installPackage.apexp?p0=04t8b000001abcdAAB`. Audience choice: Install for Admins Only.
3. Time the install (records ~6 minutes), capture the components added screen as a PDF, run existing Apex test suite — two tests fail because the package added a required field to `Opportunity` without a default value. Open vendor support ticket; vendor confirms a documented post-install step is missing from their checklist.
4. After resolution, install in a Full Sandbox refreshed from production. The 100k existing `Opportunity` records load the upgrade-time field-backfill DML — note the duration (28 minutes) so production can be scheduled.
5. Sequence production install for Saturday 02:00 site-local time. Execute. Run the post-install checklist: create Permission Set Group `Revenue_Rec_Power_Users` combining the package's `Revenue_Rec_User` permission set and the org's `Finance_Read_All` set; assign to the 12 pilot users.

**Why it works:** Each sandbox catches a different class of issue. Developer Sandbox surfaced the test failure (code-level integration); Full Sandbox surfaced the backfill duration (data-volume planning). Production was the third execution of the same runbook, not the first.

---

## Example 2: Patch upgrade rolled out via push, breaking subscriber-written Apex

**Context:** A logistics package (1GP, 2.4.x line) pushed a patch upgrade from 2.4.7 to 2.4.8 in the most recent Salesforce maintenance window. The patch renamed an internal Apex method on `LogisticsService.calculateRate(String)` to `calculateRouteRate(String, String)`. The subscriber org has custom Apex calling `LogisticsService.calculateRate(...)` from a trigger.

**Problem:** The next deployment to the subscriber org fails because `calculateRate(...)` no longer exists. Salesforce maintenance ran overnight; the admin learns of the breakage from a deployment failure on Monday morning. Multiple users report a workflow blocking error during the same window.

**Solution:**

1. Confirm the cause by checking Setup → Installed Packages → version is 2.4.8. The publisher's release notes (now visible) document the rename.
2. Patch the subscriber Apex: replace `LogisticsService.calculateRate(rate)` with `LogisticsService.calculateRouteRate(rate, originAddress)`. Run unit tests, deploy to sandbox, validate end-to-end.
3. Push the subscriber-org fix to production through the normal change pipeline.
4. Add a check to the org's release-monitoring practice: subscribe to the publisher's release-notes mailing list AND check Setup → Installed Packages monthly to surface patch versions before they break code.

**Why it works:** Push patches can rename Apex method signatures that subscribers have called. The only durable defense is monitoring publisher release notes and treating any rename in the patch notes as a subscriber-side refactor task scheduled before the maintenance window.

---

## Example 3: Uninstall of a deprecated marketing package

**Context:** A marketing automation package installed in 2020 is being retired in favor of Marketing Cloud. The package added one Custom Object (`Email_Campaign__c`) with 480,000 records, two Custom Fields on `Lead`, three Flow versions, and a Permission Set. Two subscriber-written Apex classes reference the package namespace.

**Problem:** "Just click Uninstall" deletes 480,000 records permanently after 48 hours, plus the uninstall will fail today because subscriber Apex still references the package.

**Solution:**

1. Export `Email_Campaign__c` data via Bulk API to S3. Verify row count: 480,142 records, matching the production count.
2. Find the two subscriber Apex classes referencing the package namespace (`mkt_pkg__`). One is dead code (no test references, no Flow callers); delete it. The other is a `LeadAssignmentService` that reads `Lead.mkt_pkg__Last_Touch__c`; refactor to read from a new subscriber field `Last_Marketing_Touch__c` and backfill the value before the uninstall.
3. Run uninstall in a Full Sandbox first. Email arrives with the data export CSV (validates Salesforce's 48-hour-retention path is functional). Org spot-checks: page layouts render, Flows do not show "missing component" warnings, scheduled jobs do not fail.
4. Schedule production uninstall in a low-traffic window. Execute. Download and archive the data export CSV within the 48-hour window — server-side retention is the only undo button.
5. Remove the now-unused subscriber Permission Set assignments and field references from documentation.

**Why it works:** The data export precedes the uninstall, not follows it. Subscriber-code references are pre-audited and removed before uninstall, so the operation succeeds without the "component is referenced" error. The 48-hour Salesforce-side retention is treated as a safety net, not a primary recovery mechanism.

---

## Anti-Pattern: Production-first install on a Friday

**What practitioners do:** "It's just a managed package, the vendor said it's safe. Install directly in production at end of day Friday."

**What goes wrong:** The vendor's "safe" was based on their internal test orgs, not the subscriber's specific automation, license posture, or data volumes. Friday-evening installs that fail have a 60+ hour resolution window where no engineering is on call, and the install audit trail captures choices the admin would have made differently with one more iteration. Subscribers cannot uninstall after 48 hours without irrecoverable data loss in package objects.

**Correct approach:** Sandbox-first runbook in three stages (Developer → Full → Production), Monday-through-Wednesday installation windows so a failed Friday install is never the rollback path, and the post-install checklist authored before the production install begins.
