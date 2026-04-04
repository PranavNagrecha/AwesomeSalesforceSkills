# Gotchas — Sandbox Refresh and Templates

Non-obvious Salesforce platform behaviors that cause real problems during or after sandbox refresh.

---

## Gotcha 1: Org ID Changes on Every Refresh

**What happens:** Each sandbox refresh assigns the sandbox a new organization ID. Any code, custom setting value, custom metadata record, Remote Site Setting, or external system configuration that stores the org ID as a literal string is immediately stale after the refresh completes.

**When it occurs:** Every refresh of every sandbox type. It is not specific to Full or Partial Copy — Developer sandboxes also receive a new org ID after refresh.

**How to avoid:** Never hardcode the org ID. Instead, use a SandboxPostCopy class to read `context.organizationId()` and write the new value into a custom setting or custom metadata record on every refresh. All consumer code reads the org ID from that record. External systems that need the org ID for webhook validation must be updated as part of the post-refresh runbook.

---

## Gotcha 2: Scheduled Jobs Are Copied in Active State

**What happens:** All CronTrigger records from production are copied into the sandbox with their `State` preserved as `WAITING` or `ACQUIRED`. They begin executing on schedule in the sandbox immediately after refresh. If those jobs make callouts to production APIs, send emails, or insert records into shared external systems, they will do so from the sandbox.

**When it occurs:** Any time a Full or Partial Copy sandbox (which receives production data including CronTrigger records) is refreshed. Developer and Developer Pro sandboxes are metadata-only and do not copy CronTrigger records.

**How to avoid:** Abort all CronTrigger records in the SandboxPostCopy class using `System.abortJob(ct.Id)` in a loop. Do this as the first action in `runApexClass` before any other DML, to ensure no jobs fire during the post-copy window. For jobs that must run in the sandbox, reschedule them with sandbox-safe parameters after aborting the production copies.

---

## Gotcha 3: Named Credentials Lose Their Secrets After Refresh

**What happens:** Named Credentials are copied to the sandbox, but their secrets (passwords, OAuth access tokens, OAuth refresh tokens) are blanked. Any callout that uses a Named Credential will receive a 401 or connection error in the sandbox until the credential is reconfigured. The Named Credential record itself is present and appears configured, which makes this easy to miss.

**When it occurs:** Every refresh, for all sandbox types. Named Credential metadata is copied; secrets are not.

**How to avoid:** Document every Named Credential that requires post-refresh secret entry in the manual runbook. There is no Apex API to set Named Credential secrets programmatically, so this step is always manual. Consider using a sandbox-specific Named Credential that points at a sandbox endpoint with a stable credential, and swap which Named Credential is used at the custom setting level via SandboxPostCopy.

---

## Gotcha 4: SandboxPostCopy Runs as Automated Process User, Not a System Admin

**What happens:** The `runApexClass` method executes in the context of the Automated Process user, which has limited object and field access. DML against objects where this user lacks permission will throw a `System.NoAccessException` or `DmlException`. The exception is recorded in sandbox status details, and the sandbox itself is still usable — but the post-copy script has silently failed.

**When it occurs:** Any time the SandboxPostCopy class attempts DML on an object the Automated Process user cannot access — common with custom objects, permission-gated standard objects, or objects controlled by package namespaces.

**How to avoid:** Before deploying a SandboxPostCopy class, identify every object and field it writes to. Assign the Automated Process user a permission set that grants the required access. Alternatively, delegate heavy DML work to a Queueable or @future method that runs as a different user, or use `Database.insert(records, false)` to allow partial success and log failures rather than failing the entire script.

---

## Gotcha 5: Partial Copy Template Record Counts Are Caps, Not Guarantees

**What happens:** A sandbox template specifies 500 Accounts. After refresh, the sandbox contains 700 Accounts. This is because Salesforce follows parent-lookup relationships to preserve referential integrity — when a Contact or Opportunity's parent Account was not in the initial sample, Salesforce pulls in the parent. The template cap is a ceiling on the primary random sample, not on the final record count after relationship traversal.

**When it occurs:** Any Partial Copy sandbox where the sampled child records reference parent records not in the initial sample. Complex data models with deep lookup chains amplify the effect.

**How to avoid:** Treat template caps as approximations. Design sandbox templates to over-specify caps on parent objects so the relationship traversal does not add unexpected volume. Do not write tests that assert exact record counts in a Partial Copy sandbox — the count is non-deterministic across refreshes.

---

## Gotcha 6: Refresh Interval Countdown Starts at Completion, Not Initiation

**What happens:** A Full sandbox refresh is initiated on Day 0 and completes on Day 2 due to data volume. The team assumes they can refresh again on Day 29 from initiation. The actual next-available refresh date is Day 31 (Day 2 + 29 days from completion).

**When it occurs:** For Full (29-day) and Partial Copy (5-day) sandboxes where the refresh itself takes significant time. Less impactful for Developer sandboxes (1-day interval, minutes to complete).

**How to avoid:** When planning refresh windows on a release calendar, calculate the next-available date from the expected completion date, not the initiation date. For Full sandboxes, add buffer for refresh duration when the release schedule is tight.
