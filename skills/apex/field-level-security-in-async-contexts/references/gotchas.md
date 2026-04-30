# Gotchas — FLS in Async Contexts

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Platform Event subscribers run as Automated Process

**What happens:** An `after insert` trigger on `Account_Sync__e` does `[SELECT ... WITH USER_MODE]` and the query returns every field. There's no FLS, no error, no log entry — the trigger runs as the Automated Process user, which has system-level access.

**When it occurs:** Any Apex trigger on a Platform Event object. The subscriber's running user is fixed by the platform.

**How to avoid:** Treat PE-subscribed Apex as system mode regardless of what the SOQL says. Filter fields at publish time so the event payload only contains safe data.

---

## Gotcha 2: Scheduled Apex inherits the scheduler's user identity forever

**What happens:** A scheduled job runs nightly for two years as the user who originally scheduled it. That user leaves the company, gets deactivated — and the job halts (sometimes catching the team off guard) or, before deactivation, continues to run as a sysadmin who no longer represents the org's data access policy.

**When it occurs:** Any `System.schedule(...)` job, including those auto-scheduled by managed packages.

**How to avoid:** Document the scheduler-user identity in the class header. For long-running schedules, re-schedule them as a dedicated integration user whose permissions are reviewed annually. For FLS, explicitly run in declared system mode or apply target-user FLS manually (Pattern 2).

---

## Gotcha 3: `Test.startTest` / `Test.stopTest` runs Queueables synchronously, masking cross-user bugs

**What happens:** A test enqueues a Queueable inside `Test.startTest()`. The Queueable's `execute()` runs as part of the test transaction, with the same `runAs` user. The test passes. In production, the same Queueable enqueued from a Platform Event handler runs as Automated Process and FLS-bypasses.

**When it occurs:** Any test that exercises an async path triggered by a different entry point in production.

**How to avoid:** Test each entry point separately under `runAs` blocks for both a sysadmin and a permission-restricted user. For PE-triggered paths, simulate the Automated Process behavior by calling the subscriber method directly without `runAs`, or by mocking `UserInfo.getUserId()`.

---

## Gotcha 4: `@future(callout=true)` cannot accept sObjects, forcing a re-query

**What happens:** A trigger calls `@future` with a list of IDs. The future method re-queries the records inside. Practitioners assume the re-query inherits the trigger's user context — which it does — but they often skip `WITH USER_MODE` on the re-query, accidentally elevating to system mode.

**When it occurs:** Any `@future` method that re-queries by ID and forgets the FLS clause.

**How to avoid:** Always include `WITH USER_MODE` on re-queries inside `@future`. The future method does run as the calling user, so the clause is meaningful — but you have to write it.

---

## Gotcha 5: `Database.Stateful` does not preserve FLS context — only member fields

**What happens:** A Batch Apex job declares `Database.Stateful` and stores accumulator state across batches. A team assumes "Stateful means context is preserved" and concludes that FLS evaluates as a captured user.

**When it occurs:** Misunderstanding of what `Database.Stateful` covers. It preserves member-field values, not security context.

**How to avoid:** Document explicitly: every `execute(...)` runs as the user who called `Database.executeBatch(...)`. There is no per-slice user switch. If you need a specific user's FLS, re-apply it manually (Pattern 2).

---

## Gotcha 6: `Approval.process` callbacks run as the approver, not the submitter

**What happens:** A custom Apex callback on an Approval Process step refetches the original record `WITH USER_MODE` and gets back data filtered by the approver's FLS — not the submitter's. The approver may not see fields the submitter populated, leading to `NullPointerException` in the callback or, worse, silent data loss when the callback "blanks out" fields it can't read.

**When it occurs:** Any custom callback on `Approval.LockResult` or related approval-process logic that refetches records.

**How to avoid:** Capture the submitter's user ID into the record (via a custom field or custom setting) at submission time. In the callback, use the submitter ID to apply target-user FLS via the cross-user helper, not the approver's `UserInfo.getUserId()`.
