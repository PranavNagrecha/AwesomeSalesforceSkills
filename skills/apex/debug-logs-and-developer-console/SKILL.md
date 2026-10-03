---
name: debug-logs-and-developer-console
description: "Use when setting up debug logs and trace flags, reading Apex log output and log levels, running queries in the Developer Console, executing anonymous Apex, or using the Apex Replay Debugger in VS Code. Triggers: 'set up debug log', 'Developer Console', 'anonymous Apex', 'trace flag', 'Apex Replay Debugger', 'tail Apex logs from the CLI', 'capture logs for a platform event trigger'. NOT for production logging strategy or custom structured logging frameworks — use apex/debug-and-logging. NOT for writing test classes — use apex/test-class-standards."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - debug-logs
  - developer-console
  - trace-flags
  - anonymous-apex
  - apex-replay-debugger
triggers:
  - "how do I set up a debug log for a user in Salesforce"
  - "I cannot see my debug log in the Developer Console"
  - "how do I run anonymous Apex to execute a quick fix"
  - "what are the Apex log levels and what do they log"
  - "how do I use the Apex Replay Debugger in VS Code"
  - "my debug log is truncated or missing output"
  - "how do I query data from the Developer Console"
  - "capture debug logs for a platform event trigger that runs as Automated Process"
  - "create a trace flag from the command line and tail the logs"
inputs:
  - "Which user or automated process needs logging (user, scheduled job, Automated Process, platform event subscriber)"
  - "Whether an Apex class or trigger needs its own log levels (class tracing) on top of a user trace flag"
  - "Which log categories matter (Apex, Database, Callout, Workflow, etc.)"
  - "Environment type (sandbox, scratch org, or production)"
outputs:
  - "Step-by-step trace flag setup with correct log levels"
  - "Guidance on reading and interpreting debug log output"
  - "Developer Console usage guidance for queries and anonymous Apex"
  - "Apex Replay Debugger setup and checkpoint instructions"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

Use this skill when a developer needs to capture runtime Apex behavior with debug logs, use the Developer Console or the sf CLI to read them, run anonymous Apex, or step through a log with the Apex Replay Debugger. It covers the native debugging toolchain, not logging architecture or production observability.

---

## Before Starting

- **Whose execution produces the log?** A user trace flag logs that user's requests. Platform event triggers, event processes, resumed flow interviews, and publish callbacks log under **Automated Process**. Class and trigger trace flags only change levels; they never create a log on their own.
- **How long must the trace stay on?** A trace flag's expiration must be less than 24 hours after its start, and only one trace flag per traced entity can be active at a time.
- **How big will the log get?** Each log is capped at 20 MB. Above that, older lines are removed from anywhere in the log, not just the start.
- **Is anything sensitive in scope?** FINEST on Apex Code logs every variable assignment.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which user, or which background process, runs the code we need to see?" | Event triggers and resumed flows log under Automated Process, and those logs don't show in the Developer Console Logs tab | The right traced entity: the user, Automated Process, or the overridden trigger user | A log that actually appears after the reproduction |
| "Do we need more detail for one class or trigger without flooding the whole log?" | `CLASS_TRACING` trace flags override levels for that class or trigger but don't generate logs | A user (or Automated Process) trace flag plus a class trace flag with higher levels | A focused log that stays under 20 MB |
| "When will the problem be reproduced, and for how long must logging run?" | Expiration must be under 24 hours from start, and trace flags expire without warning | A window that brackets the reproduction | No empty searches after a flag quietly expired |
| "Could the code under trace touch passwords, tokens, or personal data?" | FINEST on Apex Code logs all variable assignments | Lower Apex Code levels, or a sandbox with masked data | No secrets sitting in a downloadable log |
| "Is a deployment running while the Developer Console is open?" | Developer Console log levels affect all logs, including deployment logs, and FINEST slows deployments | Close the Console or lower levels before deploying | Deployments that are not slowed by logging |
| "How many logs will this generate?" | More than 1,000 MB in 15 minutes disables trace flags; more than 1,000 MB stored blocks new trace flags | A narrow window and a cleanup step | Logging that keeps working for the rest of the team |

What a proper setup adds over clicking "New" in Debug Logs: the log lands under the right entity, contains the detail you need, stays under the size cap, and does not leak sensitive values or block other people's trace flags.

---

## Core Concepts

### Trace flags and debug levels

A trace flag (Tooling API `TraceFlag`) ties a traced entity (`TracedEntityId`: a user, an Apex class, or an Apex trigger) to a debug level for a time window. `LogType` is one of:

| LogType | What it does |
|---|---|
| `USER_DEBUG` | Logs an individual user's activities |
| `DEVELOPER_LOG` | Set by the Developer Console when it opens, and by `sf apex tail log`, to log your own activity |
| `CLASS_TRACING` | Overrides levels for an Apex class or trigger; doesn't generate logs |

A debug level (Tooling API `DebugLevel`) holds one level per category. The Apex Developer Guide lists these categories: Database, Database Access, Workflow, NBA, Validation, Callout, Apex Code, Apex Profiling, Visualforce, System. Levels run `NONE`, `ERROR`, `WARN`, `INFO`, `DEBUG`, `FINE`, `FINER`, `FINEST`, and are cumulative. Not every category offers every level.

### Order of precedence

1. Trace flags override all other logging logic.
2. With no active trace flags, Apex tests run with default levels (DB INFO, APEX_CODE DEBUG, APEX_PROFILING INFO, WORKFLOW INFO, VALIDATION INFO, CALLOUT INFO, VISUALFORCE INFO, SYSTEM DEBUG).
3. Otherwise the API header sets levels; API requests without debugging headers produce transient logs that aren't saved.
4. Otherwise an entry point's own level applies. If none apply, no log is generated.

### Limits and retention

| Limit | Value |
|---|---|
| Size per log | 20 MB; larger logs lose older lines from any location |
| Retention | System debug logs 24 hours; monitoring debug logs seven days |
| Burst | More than 1,000 MB of logs in 15 minutes disables trace flags (re-enable after 15 minutes) |
| Storage | More than 1,000 MB of stored logs blocks adding or editing trace flags until logs are deleted |
| Trace window | `ExpirationDate` less than 24 hours after `StartDate` |

UNVERIFIED (2026-10-03): a per-user cap on the number of stored logs; version 1.0.0 of this skill said 20, and the 262 Apex guide does not state one.

### Reading a log

The header lists the API version and category levels. `EXECUTION_STARTED` and `EXECUTION_FINISHED` delimit a transaction; `CODE_UNIT_STARTED` and `CODE_UNIT_FINISHED` delimit triggers, validation rules, future calls, batch `start`, `execute`, and `finish`, scheduled `execute`, and anonymous blocks. Each line is `timestamp (nanoseconds since request start)|EVENT|details`. `USER_DEBUG` carries `System.debug` output, `DML_BEGIN` shows `Op`, `Type`, and `Rows`, and `CUMULATIVE_LIMIT_USAGE` with `LIMIT_USAGE_FOR_NS` shows limit consumption. Session IDs appear as `SESSION_ID_REMOVED`.

### Anonymous Apex

Anonymous blocks need "API Enabled" and "Author Apex" (execution through the API allows restricted access without Author Apex). They run as the current user, can fail to compile if the code violates the user's object or field permissions, and run with sharing. Changes commit only if the whole block succeeds. Run them from the Developer Console, VS Code, or `sf apex run --file script.apex`.

### Apex Replay Debugger

The Replay Debugger in the Salesforce Extensions for VS Code replays a downloaded log with breakpoints and variable inspection; it cannot re-run code. UNVERIFIED (2026-10-03): the exact log levels and checkpoint counts it requires; the extension documentation page did not return its text to a fetch. Capture with high Apex Code detail on a narrow scope so the log stays under 20 MB.

---

## Mode 1: Set Up a Debug Log

1. Setup > Debug Logs > New, or `sf apex tail log` for your own user (it sets a `DEVELOPER_LOG` trace flag).
2. Traced Entity Type: User for interactive work; Automated Process for platform event triggers, event processes, and resumed flows; the configured user if an event trigger's running user is overridden.
3. Window: start now, end before the 24-hour limit; 30 minutes is usually enough.
4. Debug level: Apex Code DEBUG, Database INFO, others NONE or INFO as needed.
5. Optional: add a `CLASS_TRACING` trace flag on the one class or trigger that needs FINE or FINEST.
6. Reproduce, then open the log in Setup, the Developer Console, or `sf apex get log --number 1`.

## Mode 2: Read an Existing Log

Search for `FATAL_ERROR`, `EXCEPTION_THROWN`, and `USER_DEBUG`, then read the last `LIMIT_USAGE_FOR_NS` block before the failure. If lines you expect are missing in a large log, assume the 20 MB reduction removed older lines and re-capture with lower levels.

## Mode 3: Troubleshoot Missing or Incomplete Logs

| Symptom | Likely cause | Fix |
|---|---|---|
| No log after the operation | Trace flag expired or not yet started | Check `StartDate` and `ExpirationDate`; create a new flag |
| Event trigger or resumed flow never logs | Traced the publishing user only | Add an Automated Process trace flag (or the overridden user) |
| Class trace flag set, still no log | `CLASS_TRACING` doesn't generate logs | Add a user or Automated Process trace flag too |
| Cannot add a trace flag | Org holds more than 1,000 MB of logs | Delete old logs |
| Trace flags turned off by themselves | More than 1,000 MB generated in 15 minutes | Lower levels, narrow scope, re-enable after 15 minutes |
| Expected lines missing in a big log | 20 MB reduction removed older lines | Lower verbosity; use class tracing for detail |
| Log not in Developer Console Logs tab | Logs created by Automated Process aren't shown there | View in Setup > Debug Logs or with `sf apex get log` |

---

## Recommended Workflow

1. **Identify the running entity.** User, Automated Process, or an overridden trigger user; note whether a class needs extra detail.
2. **Create the debug level and trace flag.** Setup, the Tooling API, or `sf data create record --use-tooling-api --sobject TraceFlag` (see `references/code-examples.md`).
3. **Reproduce inside the window** and keep it under the 24-hour limit.
4. **Retrieve and read.** `sf apex get log`, Setup, or the Developer Console; search for `FATAL_ERROR` and `LIMIT_USAGE_FOR_NS`.
5. **Clean up.** Delete or let the trace flag expire, delete large logs, and lower Developer Console levels before deployments.
6. **Lint the setup.** Run `python3 scripts/check_debug_logs_and_developer_console.py --manifest-dir <folder>` over saved trace flag JSON and anonymous Apex scripts.

---

## Review Checklist

- [ ] Traced entity matches who runs the code (user, Automated Process, overridden user)
- [ ] Class or trigger trace flags are paired with a user or Automated Process trace flag
- [ ] Expiration is less than 24 hours after start and covers the reproduction
- [ ] Apex Code is not FINEST where sensitive data is handled
- [ ] Log size stays under 20 MB; levels lowered if lines are missing
- [ ] Anonymous Apex was run in a sandbox first and its user has the needed object and field access
- [ ] Trace flags and large logs cleaned up afterwards

---

## Related Skills

- `apex/debug-and-logging`: logging strategy, custom logging frameworks, production observability
- `apex/salesforce-debug-log-analysis`: forensic reading of large logs
- `apex/test-class-standards`: writing and running Apex test classes
- `apex/soql-fundamentals`: writing the SOQL you run in the Query Editor
