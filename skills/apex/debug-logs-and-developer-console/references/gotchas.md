# Gotchas: Debug Logs and Developer Console

Non-obvious behaviors of Salesforce debug logging that cost real debugging time. Each one names the official source it rests on.

## Gotcha 1: Class and trigger trace flags never create a log

**What happens:** A developer adds a trace flag on an Apex class, reproduces the issue, and finds no log at all.

**When it occurs:** When `CLASS_TRACING` (Traced Entity Type: Apex Class or Apex Trigger) is used on its own.

**How to avoid:** Pair it with a user or Automated Process trace flag. Use the class flag only to raise or lower levels for that class.

**Source:** Apex Developer Guide (262), "Debug Log Order of Precedence": "Setting class and trigger trace flags doesn't cause logs to be generated or saved." Tooling API Developer Guide (262), "TraceFlag," `LogType`: "CLASS_TRACING trace flags override logging levels for Apex classes and triggers, but don't generate logs."

---

## Gotcha 2: Event-driven code logs under Automated Process, outside the Developer Console

**What happens:** A platform event trigger, event process, or resumed flow interview runs, and the publishing user's log shows nothing from it. The Developer Console Logs tab shows nothing either.

**When it occurs:** When only the publishing user is traced.

**How to avoid:** Add a trace flag for Automated Process (or for the running user configured on the trigger). Read the log in Setup > Debug Logs or with `sf apex get log`.

**Source:** Platform Events Developer Guide (262), "Set Up Debug Logs for Event Subscriptions": these logs "are created by Automated Process," and "The debug logs aren't available in the Developer Console's Log tab." UNVERIFIED (2026-10-03): which user Scheduled, Batch, and Queueable Apex log under; the 262 guides do not tie them to Automated Process, so trace the submitting user and add Automated Process if no log appears.

---

## Gotcha 3: Large logs lose older lines from anywhere, not just the end

**What happens:** A log near the cap is missing early `USER_DEBUG` lines or a block in the middle, while the end of the transaction is still there.

**When it occurs:** When a log would exceed 20 MB.

**How to avoid:** Lower category levels, narrow the window, and use a class trace flag for detail on one class.

**Source:** Apex Developer Guide (262), "Debug Log Limits": "Debug logs that are larger than 20 MB are reduced in size by removing older log lines ... The log lines can be removed from any location, not just the start of the debug log."

---

## Gotcha 4: Trace flags cannot span more than 24 hours, and expire silently

**What happens:** A trace flag set for a weekend run is rejected, or a flag set an hour ago has expired before the reproduction.

**When it occurs:** When `ExpirationDate` is 24 hours or more after `StartDate`, or the window was too short.

**How to avoid:** Set a window under 24 hours that brackets the reproduction, and recreate it for each run. Only one trace flag per traced entity can be active at a time.

**Source:** Tooling API Developer Guide (262), "TraceFlag," `ExpirationDate` and `StartDate`.

---

## Gotcha 5: Retention is by log type, not by org type

**What happens:** A team expects sandbox logs to stay for a week and finds them gone the next day.

**When it occurs:** When guidance says "24 hours in production, 7 days in sandbox," which is how version 1.0.0 of this skill described it.

**How to avoid:** Download logs you need to keep. System debug logs are retained 24 hours; monitoring debug logs seven days.

**Source:** Apex Developer Guide (262), "Debug Log Limits."

---

## Gotcha 6: Too many logs turn trace flags off or block new ones

**What happens:** Trace flags stop working mid-investigation, or nobody can create a new trace flag.

**When it occurs:** More than 1,000 MB of logs in 15 minutes disables trace flags; more than 1,000 MB stored blocks adding or editing them. A trace flag on a busy class or user can also make requests fail.

**How to avoid:** Keep windows short and levels low, avoid tracing high-traffic users and classes, and delete old logs.

**Source:** Apex Developer Guide (262), "Debug Log Limits," including the warning about frequently accessed classes and users.

---

## Gotcha 7: FINEST exposes variable values and slows deployments

**What happens:** A log contains a password or token assigned to a variable. A deployment takes much longer than usual.

**When it occurs:** Apex Code at FINEST logs all variable assignments. Developer Console levels apply to all logs, including those created during deployment.

**How to avoid:** Avoid FINEST where sensitive values exist, and lower levels or close the Developer Console before deploying.

**Source:** Apex Developer Guide (262), "Debug Log" header warning and "Debug Log Levels" (Important note on deployments).

---

## Gotcha 8: Anonymous Apex runs as you, with sharing, and commits only if everything succeeds

**What happens:** A data-fix script fails to compile on a field the user cannot see, or skips records the user cannot access.

**When it occurs:** When the running user lacks object or field permissions, or sharing hides records.

**How to avoid:** Run it as a user with the right access, test it in a sandbox, and check row counts in `System.debug` before relying on it.

**Source:** Apex Developer Guide (262), "Anonymous Blocks" ("Anonymous blocks run as the current user and can fail to compile if the code violates the user's object- and field-level permissions") and sharing implementation details ("Anonymous Apex and Connect in Apex always run in with sharing mode").

---

## Gotcha 9: API requests without debugging headers leave no saved log

**What happens:** An integration call fails, and no log exists for it even though Apex ran.

**When it occurs:** When no trace flag covers the integration user and the request sends no debugging header.

**How to avoid:** Trace the integration user for the reproduction window.

**Source:** Apex Developer Guide (262), "Debug Log Order of Precedence," item 3: requests without debugging headers "generate transient logs, logs that aren't saved."
