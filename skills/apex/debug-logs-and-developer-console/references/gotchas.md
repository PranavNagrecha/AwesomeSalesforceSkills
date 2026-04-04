# Gotchas — Debug Logs And Developer Console

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Scheduled and Batch Jobs Run as Automated Process, Not the Submitting User

**What happens:** A developer creates a trace flag for their own user account expecting to see debug output from a scheduled job or batch class. The job runs and completes, but no debug log appears for the developer's user.

**When it occurs:** Whenever code runs asynchronously as a background process — Scheduled Apex, Batch Apex, Queueable (when enqueued by a scheduled job), and Platform Event trigger handlers all execute under the **Automated Process** system user, not the user who submitted the job.

**How to avoid:** Always check what user context the code runs in before creating the trace flag. For background jobs, set **Traced Entity Type = Automated Process** rather than User. You can also set a trace flag on the specific Apex class to capture it regardless of which user or system entity triggers it.

---

## Gotcha 2: Trace Flags Silently Expire — No Alert Is Issued

**What happens:** A developer sets up a trace flag, takes a break, and then reproduces the scenario — only to find no log was captured. The trace flag had an end time of 30 minutes and expired during the break.

**When it occurs:** Trace flags have a required expiry time. Once expired, the flag still appears in the Debug Logs list but is greyed out. The platform generates no notification, no error, and no empty log to indicate the flag was inactive.

**How to avoid:** Always check the trace flag expiry before reproducing a scenario. When setting up a flag, choose a window that exceeds the time you expect to spend debugging, then delete the flag manually when done. If a log is missing, check the flag's expiry first — it is the most common cause of missing logs.

---

## Gotcha 3: The 20 MB Log Cap Truncates from the End — Silently Cutting Off the Error

**What happens:** The debug log exists and is readable, but the `FATAL_ERROR` or the `USER_DEBUG` statements at the end of the transaction are absent. The log shows a message like `*** Skipped 3145728 bytes of log ***` near the end or does not include `EXECUTION_FINISHED`.

**When it occurs:** When a single transaction generates more than 20 MB of log output, the platform silently drops the tail of the log. Ironically, the most important information — exceptions, final state — is typically at the end and is the first thing truncated.

**How to avoid:**
- Set ApexProfiling, NBA, System, Validation, Visualforce, and Workflow to NONE unless specifically needed.
- Start with ApexCode = DEBUG and Database = INFO rather than FINEST.
- For Apex Replay Debugger scenarios, set all non-Apex categories to NONE and ApexCode to FINEST — this targets the verbosity to only what the debugger needs.
- Narrow the trace window and scope to a single operation rather than a broad user session.

---

## Gotcha 4: Developer Console Debug Logs Only Show the Current User's Logs

**What happens:** A developer opens the Developer Console and clicks on the Logs tab expecting to see logs for all users or for a specific integration user. Only their own logs appear.

**When it occurs:** The Developer Console's Logs tab filters debug logs to the current authenticated user by default. Logs captured for other users via trace flags are stored in the org but not surfaced in the Developer Console's Logs panel for other users.

**How to avoid:** To view logs for another user (or for Automated Process), go to **Setup → Debug Logs**, find the log entry (sorted by timestamp), and open it from Setup. Alternatively, use the sf CLI: `sf apex log list` to list all available logs, then `sf apex log get --log-id <id>` to download a specific log. For Automated Process logs, you can also query them via the Tooling API: `SELECT Id, Body FROM ApexLog WHERE LogUser.Name = 'Automated Process'`.

---

## Gotcha 5: Anonymous Apex Runs With the Current User's Permissions — Not System Permissions

**What happens:** A developer runs anonymous Apex to update records and receives an unexpected `System.DmlException: FIELD_CUSTOM_VALIDATION_EXCEPTION` or is unable to query certain fields. The same query works fine in a unit test written with `@isTest`.

**When it occurs:** Anonymous Apex executes in the current user's security context and enforces field-level security (FLS), sharing rules, and validation rules. It does not run in a system context like `@isTest` methods. If the developer's profile lacks access to a field or record, the anonymous Apex reflects those restrictions.

**How to avoid:** Run anonymous Apex as a System Administrator when elevated access is needed. If the intent is to test code logic that bypasses sharing, run the code inside a class declared `without sharing` and invoke it from the anonymous script — but be explicit about this choice. Do not assume anonymous Apex equals unrestricted access.
