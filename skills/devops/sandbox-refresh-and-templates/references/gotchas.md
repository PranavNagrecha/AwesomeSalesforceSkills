# Gotchas — Sandbox Refresh and Templates

Non-obvious Salesforce platform behaviors that cause real problems during or after sandbox refresh.

---

## Gotcha 1: Org IDs and URLs Copied from Production Are Wrong in the Sandbox

**What happens:** A custom setting, custom metadata record, or Apex constant holds production's org ID or My Domain URL. After refresh the sandbox carries those values, so environment checks and callbacks point at production.

**When it occurs:** Any code or configuration that stores the org ID or an org URL as a literal. The sandbox is a separate org; the `SandboxContext` passed to the post-copy class carries the sandbox's own org ID.

**How to avoid:** Read the org ID at runtime with `UserInfo.getOrganizationId()`; set environment-specific values in the post-copy class from `context.organizationId()` and `context.sandboxName()`. The checker flags literal `00D` IDs in Apex.

---

## Gotcha 2: Scheduled Jobs Are Not Copied

**What happens:** Nightly batch jobs that ran in production simply never run in the refreshed sandbox, and test cycles that depend on them stall.

**When it occurs:** The Apex Developer Guide states that when you refresh a sandbox, scheduled jobs from the source org aren't copied and you must reschedule the jobs you need. A post-copy class that loops over `CronTrigger` calling `System.abortJob` is aborting nothing that came from production.

**How to avoid:** Keep a list of the jobs each sandbox needs and schedule them with `System.schedule` in the post-copy class or in the runbook. The checker warns on `System.abortJob` inside a `SandboxPostCopy` class.

---

## Gotcha 3: Integrations Still Point at Production Systems

**What happens:** Configuration copied from production (custom settings, custom metadata, Named Credential endpoints) sends sandbox traffic to production endpoints, or sandbox callouts fail on credentials that belong to production.

**When it occurs:** On any refresh of a sandbox whose integrations are configured by data or metadata copied from production.

**How to avoid:** Change endpoints in the post-copy class and use sandbox-specific Named Credentials and External Credentials. `ConnectApi.NamedCredentials.createCredential` (API 56.0) creates credentials from Apex, but the post-copy user may not have access to every feature, so keep a runbook line to verify each credential after refresh.

---

## Gotcha 4: The Post-Copy User Can't Do Everything

**What happens:** The post-copy class throws on DML against an object the Automated Process user can't access, and the remaining setup never happens.

**When it occurs:** `runApexClass` runs at the end of the copy as a special Automated Process user that isn't visible in the org and doesn't have access to all objects and features.

**How to avoid:** Keep the class to operations that user can perform, test with `Test.testSandboxPostCopyScript(script, orgId, sandboxId, sandboxName, true)` so the test runs with the same permissions, and keep the documented fallback: if the script fails, run it after activation as a user with the right permissions.

---

## Gotcha 5: Templates Depend on the Sandbox Type

**What happens:** A CLI create or refresh fails, or a Full sandbox copies far more than the team wanted, because the template rule was misremembered.

**When it occurs:** In a sandbox definition file, `templateId` is required for Partial sandboxes, optional for Full sandboxes, and not available for Developer and Developer Pro sandboxes. A template selects which objects to copy.

**How to avoid:** Put `templateId` in every Partial definition file, consider one for Full sandboxes when not every object is needed, and never add one for Developer types. The checker enforces all three.

---

## Gotcha 6: Production Personal Data Arrives Unmasked

**What happens:** Developers and testers see real customer emails and phone numbers, and sandbox automation emails real people.

**When it occurs:** Partial Copy and Full sandboxes receive production data along with metadata.

**How to avoid:** Mask personal fields in the post-copy class (a Queueable for volume) before access is granted, or use a dedicated masking product; review which objects the template brings in.

---

## Gotcha 7: Refresh Options Are Set per Refresh

**What happens:** A refresh runs without the post-copy class or with the wrong template, because the person refreshing from Setup forgot a field.

**When it occurs:** The Apex class and template are chosen when the sandbox is created or refreshed. From the CLI, `sf org refresh sandbox --definition-file` takes a definition file with the options you want to change, such as `licenseType`, `templateId`, or `copyArchivedActivities`, but can't change the sandbox name; changing the name means delete and recreate.

**How to avoid:** Keep one definition file per sandbox in source control and refresh from it, so the template and post-copy class are never retyped.
