# Gotchas — Debug And Logging

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `System.debug` Is Not Retention Strategy

**What happens:** A critical incident occurs and the needed debug lines are gone or were never collected at the right level.

**When it occurs:** Teams assume the existence of a debug statement means production observability exists.

**How to avoid:** Use durable log storage for production-critical diagnostics.

---

## Sensitive Payload Logging Creates Security Debt

**What happens:** Tokens, bearer headers, or full request bodies end up in logs.

**When it occurs:** Teams log entire callout payloads or auth objects during troubleshooting.

**How to avoid:** Log identifiers and error classification, not secrets or unnecessary personal data.

---

## Async Failures Need More Than Stack Traces

**What happens:** Support knows a Queueable or Batch failed but cannot trace which business operation triggered it.

**When it occurs:** Logging ignores correlation IDs or async job IDs.

**How to avoid:** Capture the initiating record context and job ID together.

---

## Excessive Debug Noise Can Obscure Root Cause

**What happens:** The exact failure is present in the logs but buried under hundreds of low-value debug statements.

**When it occurs:** Teams use debug output as a permanent narrative of every method entry and variable value.

**How to avoid:** Use deliberate log levels and remove temporary debug statements after diagnosis.

---

## A Debug Log Over 20 MB Loses Lines From The Middle, Not The End

**What happens:** The log you open is complete-looking but the `USER_DEBUG` line you added is gone,
and so is the `LIMIT_USAGE_FOR_NS` block you wanted. Nothing marks the hole.

**When it occurs:** Any transaction verbose enough to push one log past 20 MB — typically `APEX_CODE`
at `FINEST` over a bulk operation, or a loop that logs per record. "Each debug log must be 20 MB or
smaller. Debug logs that are larger than 20 MB are reduced in size by removing older log lines, such
as log lines for earlier `System.debug` statements. The log lines can be removed from any location,
not just the start of the debug log." (Apex Developer Guide L38115–38117)

**How to avoid:** Narrow the trace before you reproduce, not after. Raise `APEX_CODE` for one class
with a class-level trace flag instead of raising it for the user, and drop `DB`/`WORKFLOW` to `NONE`
when the question is pure Apex. If the answer must survive, it belongs in `Application_Log__c` or a
`Log_Event__e`, not in a debug line.

---

## Debug Logs Expire On Two Different Clocks, And Trace Flags Switch Themselves Off

**What happens:** The log from this morning's incident is gone by the afternoon, or trace flags stop
producing logs entirely and nobody changed anything.

**When it occurs:** "System debug logs are retained for 24 hours. Monitoring debug logs are retained
for seven days." (Apex Developer Guide L38118; the same split appears on `ApexLog.Location` —
`SystemLog` = Developer Console, 24 hours; `Monitoring` = debug log monitoring, seven days — Object
Reference, ApexLog.) Separately: "If you generate more than 1,000 MB of debug logs in a 15-minute
window, your trace flags are disabled" (L38119–38120), and "When your org accumulates more than
1,000 MB of debug logs, we prevent users in the org from adding or editing trace flags" (L38125–38126).

**How to avoid:** Treat a debug log as evidence you have hours to collect, not a record. Download the
log during triage. Budget log volume: a trace flag left on a frequently executed class is the usual
cause of the 1,000 MB wall, and the guide warns that in that situation "the request can result in
failure, regardless of the time window and the size of the debug logs" (L38122–38123). Clearing the
wall means deleting `ApexLog` rows, which is why `ApexLog` supports `delete()`.

---

## `LoggingLevel` Filters The Write, Not The Call

**What happens:** Setting `APEX_CODE` to `ERROR` hides the output but the transaction is no faster,
and a heap-heavy string concatenation still runs.

**When it occurs:** Every `System.debug(LoggingLevel.FINEST, 'x=' + JSON.serialize(bigList))` in code
that ships. Apex evaluates the argument expression and passes the result into `System.debug` before
the platform decides whether to write it: "if the log level is set to ERROR, the string MsgTxt isn't
written to the debug log because the debug method has a level of INFO" (Apex Reference Guide,
LoggingLevel Enum, L222112–222114) — *written*, not *evaluated*. UNVERIFIED (2026-09-05): the corpus
states the filtering-at-write behaviour but does not quantify the residual CPU or heap cost of the
call itself; the argument-evaluation cost follows from Apex's call semantics, not from a documented
measurement.

**How to avoid:** Never build an expensive string inline. Guard it (`if (Limits.getHeapSize() < X)`),
or pass the object and let `System.debug` call `String.valueOf` on it — "If the msg argument is not a
string, the debug method calls `String.valueOf` to convert it into a string" (Apex Reference Guide
L238869–238871). Routing production diagnostics through `LogService` moves the decision to
`Logger_Setting__mdt` where it can be changed without a deploy.

---

## Logs From A Publish-After-Commit Event Vanish With The Rollback That Caused Them

**What happens:** A trigger throws, the transaction rolls back, and the log record explaining why is
rolled back with it. The incident leaves no trace anywhere except a debug log that has since expired.

**When it occurs:** Any logging built on `insert new Log__c(...)` or on a platform event left at
`PublishAfterCommit`: "The event message is published only after a transaction commits successfully.
If the transaction fails, the event message isn't published." (Metadata API Developer Guide,
`CustomObject.publishBehavior`, api_meta L42222–42224)

**How to avoid:** Route ERROR and FATAL through an event whose `publishBehavior` is
`PublishImmediately` — "published when the publish call executes, regardless of whether the
transaction succeeds" (api_meta L42225–42227). See `references/code-examples.md`. The two behaviours
also charge different meters: publish-after-commit "is counted as one DML statement against the Apex
DML statement limit", publish-immediately against "a separate event publishing limit of 150
`EventBus.publish()` calls" (Apex Reference Guide L214524–214528; Apex Developer Guide L19598–19599).

---

## `EventBus.publish` Never Throws — A Failed Publish Is A Return Value

**What happens:** Logging code that looks correct silently stops recording. There is no exception, no
retry, and no clue in the debug log.

**When it occurs:** Whenever `EventBus.publish` is called without inspecting the result. "The
`EventBus.publish()` method doesn't throw exceptions caused by an unsuccessful publish operation.
It's similar in behavior to the Apex `Database.insert` method when called with the partial success
option." (Apex Reference Guide L214563–214565) A `true` from `isSuccess()` only means the request was
queued — "the publish request is queued in Salesforce and the event message is published
asynchronously" (L214511–214513).

**How to avoid:** Iterate `Database.SaveResult` and read `getErrors()`, as `LogService.flush()` does.
For failures that happen after the queue accepts the request, attach an Apex publish callback — the
system "invokes this method when the final result of `EventBus.publish` is available" (Apex Reference
Guide L157483–157488) — and test the failure branch with `Test.getEventBus().fail()` (L157744).

---

## A Platform Event Trigger's Debug Log Belongs To The Automated Process Entity

**What happens:** You set a trace flag on yourself, publish a log event, and get no log for the
subscriber trigger at all. The event was delivered; the log is filed under a user you cannot select.

**When it occurs:** Every platform event trigger deployed without a `PlatformEventSubscriberConfig`.
"By default, the platform event trigger runs as the Automated Process entity. Setting the running
user to a specific user has these benefits: Records are created or modified as this user … Debug logs
for the trigger execution are created by this user. You can send email from the trigger, which isn't
supported with the default Automated Process user." (Metadata API Developer Guide,
`PlatformEventSubscriberConfig.user`, api_meta L96454–96462) The same entity is limited elsewhere:
"Automated Process users can't perform Object and FLS checks in custom code unless appropriate
permission sets are explicitly applied to those users." (Apex Developer Guide L11921–11922)

**How to avoid:** Deploy the `PlatformEventSubscriberConfig` with an explicit `user` alongside the
trigger, and grant that user create access to the log object. This is not optional for a logging
subscriber: without it the log row's owner, the debug log's owner, and any alert email all fail or
land on the wrong identity.

---

## `APEX_CODE` At `FINEST` Logs Variable Assignments — Including The Password Ones

**What happens:** A log gathered to diagnose a self-registration bug contains the passwords that were
assigned to Apex string variables, and it is readable for the retention window.

**When it occurs:** Any `FINEST` trace over code that touches credentials or personal data.
"If the Apex Code log level is set to FINEST, the debug log includes details of all Apex variable
assignments. Ensure that the Apex Code being traced doesn't handle sensitive data. Before enabling
FINEST log level, be sure to understand the level of sensitive data your organization's Apex handles.
Be careful with processes such as community users self-registration where user passwords can be
assigned to an Apex string variable." (Apex Developer Guide L38171–38175) The platform scrubs exactly
one thing for you: "Session IDs are replaced with `SESSION_ID_REMOVED` in Apex debug logs" (L38133) —
nothing else.

**How to avoid:** Use `FINE` or `FINER` on paths that handle secrets and reserve `FINEST` for code you
have read. The same paragraph is why `FINEST` is also a deployment hazard: "Before running a
deployment, verify that the Apex Code log level isn't set to FINEST. Otherwise, the deployment is
likely to take longer than expected." (L38405–38407)

---

## `System.debug` Calls Are Invisible To Code Coverage, So Debug-Only Branches Look Covered

**What happens:** A method whose only body is `System.debug(...)` reports coverage that does not
reflect any tested behaviour, and a `catch` block that only debugs passes the 75% gate while
swallowing the failure it was supposed to surface.

**When it occurs:** Any class where debug lines pad the executable-statement count.
"Calls to `System.debug` are not counted as part of Apex code coverage." (Apex Reference Guide,
`System.debug`, L238877 and L238914)

**How to avoid:** Judge a catch block by what it does, not by its coverage. The checker in this skill
flags `catch` blocks whose only statement is a `System.debug` — that pattern converts an exception
into an expired log line. Rethrow, or call `LogService.error(...)` and then rethrow.

---

## Unhandled-Exception Emails Are Throttled Per App Server And Suppressed Per Duplicate

**What happens:** A production defect fires thousands of times and one email arrives, or none does.
The team concludes the problem stopped.

**When it occurs:** "If duplicate exceptions occur in Apex code that runs synchronously or
asynchronously, subsequent exception emails are suppressed and only the first email is sent." Also
"Apex exception emails are limited to 10 emails per hour, per application server. Because this limit
isn't on a per-org basis, email delivery to a particular org can be unreliable." And critically for
modern UIs: "Emails aren't sent for exceptions encountered with anonymous Apex executions or with
Apex methods accessed by Aura components and Lightning web components via the `@AuraEnabled`
annotation." (Apex Developer Guide L39604–39612)

**How to avoid:** Never use exception email as the alerting channel — use it as a fallback and point
it at a monitored distribution list via the `ApexEmailNotifications` metadata type (see
`references/code-examples.md`). Note that deploying that type "deletes all previous notifications in
the org" that are not in the deployed file (Metadata API Developer Guide, api_meta L22458–22461), so
retrieve before you deploy. Real alerting comes from `Application_Log__c` rows plus the Apex
Unexpected Exception event type in Event Monitoring, which the guide recommends over relying on the
emails (Apex Developer Guide L39594–39596).

---

## A Finalizer Is The Only Place A Queueable's Log Survives An Unhandled Exception

**What happens:** A Queueable dies on a limit exception. Everything it buffered — including the log
rows explaining the failure — is rolled back, and `AsyncApexJob` records only that the job failed.

**When it occurs:** Any Queueable that buffers log rows and inserts them at the end of `execute()`.
The guide's own logging example builds the buffer in the finalizer instead, because the finalizer runs
"regardless of success or failure" and commits the buffered log there (Apex Developer Guide
L16416–16437). `FinalizerContext.getRequestId()` "returns the request ID, a string that uniquely
identifies the request, and can be correlated with Event Monitoring logs … The Queueable job and the
Finalizer execution both share the (same) request ID" (L16322–16330), and `getResult()` returns
`SUCCESS` or `UNHANDLED_EXCEPTION` (L16337–16340).

**How to avoid:** Attach a finalizer to any Queueable whose failure matters, stamp
`ctx.getAsyncApexJobId()` and `ctx.getRequestId()` onto the rows, and call `LogService.flush()` from
it. To join a log row back to the job use `getAsyncApexJobId()`, not `getRequestId()` — the guide is
explicit that the request ID correlates to Event Monitoring while the job ID correlates to
`AsyncApexJob` (L16327–16329).

---

## A Captured Stack Trace Can Come Back Empty

**What happens:** `Stack_Trace__c` on the log row is blank or a bare `()`, so the record names the
exception type and message but not where it came from.

**When it occurs:** Two situations are worth guarding against. First, an exception object that was
constructed but never thrown has no trace to report — `LogService.buildEvent` calls
`getStackTraceString()` on whatever it is handed, and construction alone does not populate one.
Second: UNVERIFIED (2026-09-05) — practitioners report `getStackTraceString()` returning `()` for
exceptions that cross a managed-package boundary. The Apex guides document only that the method
"Returns the stack trace of a thrown exception as a string" (Apex Developer Guide L39979; Apex
Reference Guide L215105) and say nothing about managed-package behaviour, so treat the managed-package
half of this as unverified until you reproduce it. The debug log's own convention is related and *is*
documented: "If a line number can't be located, `[EXTERNAL]` is logged instead. For example,
`[EXTERNAL]` is logged for built-in Apex classes or code that's in a managed package"
(Apex Developer Guide L38224–38226).

**How to avoid:** Log from a `catch` on a thrown exception, never from a constructed one, and treat a
blank trace as a normal case rather than a bug — `LogService.safeTrace` returns `null` instead of
writing an empty string, so a blank column reads as "no trace available" rather than "trace of length
zero". Always carry `getTypeName()` and the correlation id alongside the trace; those two are enough
to locate the code unit in `ApexLog` even when the trace is useless.
