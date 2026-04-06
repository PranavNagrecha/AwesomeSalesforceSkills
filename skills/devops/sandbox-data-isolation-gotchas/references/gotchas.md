# Gotchas — Sandbox Data Isolation Gotchas

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Contact and Lead Email Addresses Are NOT Changed to `.invalid` on Refresh

**What happens:** Only the `Email` field on the **User** object is appended with `.invalid` during sandbox creation and refresh. The `Email` field on Contact, Lead, Person Account, and any other object is copied verbatim from production. Any workflow email alert, Apex `Messaging.sendEmail()` call, case auto-response, or Process Builder/Flow email action that targets a Contact or Lead email address will deliver real email to real addresses if sandbox deliverability is `All Email`.

**When it occurs:** On every Full sandbox refresh and every Partial Copy sandbox refresh where the sandbox template includes Contact or Lead records. Developer sandboxes do not copy data records so this does not apply.

**How to avoid:** After each refresh, run:
```sql
SELECT COUNT() FROM Contact WHERE Email != null AND Email NOT LIKE '%.invalid'
SELECT COUNT() FROM Lead WHERE Email != null AND Email NOT LIKE '%.invalid'
```
If either count is non-zero and deliverability is not `No Access`, scrub those fields with a Queueable Apex job that appends `.invalid`. Automate this by chaining the Queueable from your SandboxPostCopy class.

---

## Gotcha 2: Email Deliverability Setting Is NOT Automatically Reset on Refresh

**What happens:** New sandboxes created from scratch default to `System Email Only`. However, when a sandbox is refreshed, Salesforce preserves the deliverability setting that was active on the sandbox at the time of refresh — it does NOT reset to a safe default. A sandbox that previously had `All Email` enabled (perhaps for a specific testing scenario) will still have `All Email` after a refresh.

**When it occurs:** Every sandbox refresh where the previous deliverability setting was `All Email` or where the setting was changed from the default at any point in the sandbox's history. This is especially likely for long-lived sandboxes that have been used for multiple purposes over time.

**How to avoid:** Add "verify deliverability setting" as the first item in every post-refresh runbook. Navigate to Setup > Deliverability in the sandbox and confirm the setting matches the intended level. This cannot be automated via SandboxPostCopy — the deliverability setting is not exposed as a writable property through Apex or Metadata API.

---

## Gotcha 3: CronTrigger Records Are Copied in WAITING State and Will Fire

**What happens:** When a Full or Partial Copy sandbox is refreshed, all CronTrigger records (scheduled Apex jobs) from production are copied to the sandbox with their `State` preserved as `WAITING`. These jobs begin evaluating their next fire time the moment the sandbox refresh completes. A job scheduled to run at 2:00 AM will run at 2:00 AM in the sandbox — potentially against production endpoints or sending emails — before any post-refresh runbook is executed.

**When it occurs:** Every Full sandbox refresh and any Partial Copy sandbox refresh that copies the CronTrigger records (they are part of the org metadata layer and are included by default). Developer sandboxes do not copy scheduled jobs.

**How to avoid:** Abort all CronTrigger records in the SandboxPostCopy class:
```apex
for (CronTrigger ct : [SELECT Id FROM CronTrigger WHERE State IN ('WAITING','ACQUIRED','EXECUTING')]) {
    System.abortJob(ct.Id);
}
```
Note: the Automated Process user running SandboxPostCopy must have sufficient permissions to call `System.abortJob()`. Pre-grant the required system permission via a permission set on the Automated Process user in production before the refresh.

---

## Gotcha 4: SandboxPostCopy Exceptions Do Not Surface Visibly — The Sandbox Still Opens

**What happens:** If the SandboxPostCopy class throws an unhandled exception, Salesforce marks the post-copy script run as failed but still makes the sandbox available for login. The sandbox Setup > Sandboxes page may show a success status or a generic message rather than surfacing the exception. The isolation steps that were supposed to run (aborting jobs, scrubbing emails) simply did not happen, with no visible indication to the team that logged in.

**When it occurs:** Any time the SandboxPostCopy class encounters a runtime error — most commonly a `System.NoAccessException` because the Automated Process user lacks permission to access a custom object, or a `QueryException` because a Custom Setting or Custom Metadata record does not exist in the sandbox yet.

**How to avoid:** Enable debug logging for the Automated Process user in production before initiating the refresh. After the sandbox becomes available, immediately check the debug log for `SandboxIsolation` (or whatever class name you registered) and look for `FATAL_ERROR` or `EXCEPTION_THROWN` events. Write the SandboxPostCopy class defensively using try/catch blocks so partial failures are logged without aborting the entire isolation routine:
```apex
try {
    // abort scheduled jobs
} catch (Exception e) {
    System.debug(LoggingLevel.ERROR, 'Failed to abort jobs: ' + e.getMessage());
}
```

---

## Gotcha 5: Named Credential Endpoint URLs Are Copied Unchanged — Secrets Are Blanked, Not URLs

**What happens:** When a sandbox is refreshed, Named Credentials are copied from production. The **endpoint URL** is preserved exactly as it was in production. The **secrets** (passwords, OAuth access and refresh tokens) are blanked. Practitioners often test the Named Credential after refresh, get an authentication error, and conclude the Named Credential is "broken" and harmless. In reality, the credential is pointing at the production endpoint and will become fully functional again the moment a secret is re-entered — without any warning that it targets a live system.

**When it occurs:** Every Full and Partial Copy sandbox refresh. Named Credentials are org metadata and are always included.

**How to avoid:** Before re-entering any Named Credential secret in a sandbox, review the endpoint URL field and confirm it targets a sandbox or test endpoint. If the org uses a single Named Credential with an environment-specific URL, update the URL in the sandbox immediately after refresh (this is a manual Setup step — Named Credential URL cannot be changed via Apex in most API versions). Document this step in the post-refresh runbook as a mandatory gate before any integration testing begins.

---

## Gotcha 6: Partial Copy Sandbox Templates Pull in Parent Records Beyond the Cap

**What happens:** Sandbox templates for Partial Copy sandboxes specify a maximum record count per object. However, Salesforce follows parent lookup relationships to maintain referential integrity. If a template caps Opportunities at 5,000 records, but those Opportunities have parent Account records that were not in the template, Salesforce pulls in those Account records automatically. This can result in the sandbox containing significantly more records than the template specified — including Account and Contact records with real production email addresses.

**When it occurs:** Any time a Partial Copy sandbox template references child objects whose parent records are not explicitly included in the template with adequate caps. Common relationship chains: Case → Account → Contact, Opportunity → Account → Contact.

**How to avoid:** When designing sandbox templates, always include the full parent chain with generous caps. After a refresh, audit the Contact and Lead email counts as described in Gotcha 1 regardless of whether the template was expected to pull in those objects.
