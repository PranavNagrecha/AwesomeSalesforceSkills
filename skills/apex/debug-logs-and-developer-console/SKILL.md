---
name: debug-logs-and-developer-console
description: "Use when setting up debug logs and trace flags, reading Apex log output and log levels, running queries in the Developer Console, executing anonymous Apex, or using the Apex Replay Debugger in VS Code. Triggers: 'set up debug log', 'Developer Console', 'anonymous Apex', 'trace flag', 'Apex Replay Debugger'. NOT for production logging strategy or custom structured logging frameworks (use debug-and-logging), and NOT for writing test classes (use apex-test-class-standards)."
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
inputs:
  - "Which user or automated process needs logging (user, scheduled job, Automated Process, platform event subscriber)"
  - "Which log categories matter (Apex, Database, Callout, Workflow, etc.)"
  - "Environment type (sandbox, scratch org, or production)"
outputs:
  - "Step-by-step trace flag setup with correct log levels"
  - "Guidance on reading and interpreting debug log output"
  - "Developer Console usage guidance for queries and anonymous Apex"
  - "Apex Replay Debugger setup and checkpoint instructions"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when a developer needs to capture runtime Apex behavior using debug logs, navigate the Developer Console, execute ad-hoc Apex anonymously, or step through code with the Apex Replay Debugger. This skill covers the mechanics of Salesforce's native debugging toolchain — not logging architecture or production observability strategy.

---

## Before Starting

- **Who or what needs to be traced?** Debug logs require a trace flag tied to a Traced Entity Type: User, Apex class, Apex trigger, Visualforce page, or Automated Process.
- **What environment are you in?** Production limits log retention. Sandboxes allow broader experimentation.
- **What log size risk exists?** A single debug log is capped at 20 MB. Logs beyond that are truncated without error. Set log categories to the minimum needed.

---

## Core Concepts

### Trace Flags and Debug Levels

A **trace flag** is a Setup record that tells Salesforce to capture a debug log for a specific entity during a defined time window. Without a trace flag, no debug log is generated for that entity — even if the code runs.

Every trace flag references a **Debug Level**, a named configuration that sets the verbosity for each of the nine log categories:

| Category | What it captures |
|---|---|
| ApexCode | `System.debug` calls, Apex entry/exit, exceptions |
| ApexProfiling | Limits consumption, method timing |
| Callout | HTTP request/response headers and bodies |
| Database | SOQL queries, DML statements, query rows |
| NBA | Next Best Action strategy execution |
| System | System method calls |
| Validation | Validation rule evaluation details |
| Visualforce | Visualforce page execution |
| Workflow | Flow and workflow rule evaluation |

For each category the valid log levels in ascending verbosity order are:
`NONE < ERROR < WARN < INFO < DEBUG < FINE < FINER < FINEST`

For most Apex debugging, set **ApexCode to DEBUG** and **Database to INFO**. Avoid FINEST on ApexCode unless diagnosing the heaviest executions — it generates enormous output and may cause the 20 MB cap to truncate the useful end of the log.

### Debug Log Lifecycle

- **Setup path:** Setup → Debug Logs → New (choose Traced Entity Type → select entity → set start/end time → assign or create a Debug Level).
- **Expiration:** Trace flags expire automatically at the configured end time. Expired flags produce no new logs. Always check whether the flag is still active.
- **Retention:** The platform retains the most recent **20 logs per user**. Older logs are purged automatically. Logs in production are retained for **24 hours**; sandbox logs are retained for **7 days**. The org has an overall cap of **1,000 MB** of total debug log storage — when that cap is hit, Salesforce blocks adding new trace flags until old logs are deleted.
- **Log size cap:** Each log file is capped at **20 MB**. Truncated logs display a message at the point of truncation. If the log is truncated, reduce verbosity or narrow the trace to a smaller time window.

Trace flag **Traced Entity Types** and when to use each:

| Entity Type | When to use |
|---|---|
| User | Trace all Apex triggered by a specific user's session |
| Apex Class | Trace invocations of a single Apex class regardless of which user triggers it |
| Apex Trigger | Trace a specific trigger |
| Visualforce Page | Trace a specific Visualforce page |
| Automated Process | Trace background jobs (Scheduled Apex, Queueable, Batch, Platform Event triggers) |

**Important:** When debugging scheduled jobs or batch Apex, set the Traced Entity Type to **Automated Process**, not the user who created the job.

### Developer Console

The Developer Console is a browser-based IDE accessible from the gear icon or from **Setup → Developer Console**. Its key panels for debugging are:

**Logs tab:**
- Displays captured debug logs for the current user.
- Filter by request type or search within a log.
- Click **Open** on a log to view raw text, or switch to the **Execution Overview** panel for a structured tree view of code execution.
- Use **Debug → Open Execute Anonymous Window** (Ctrl+E) to run ad-hoc Apex.

**Query Editor:**
- Supports SOQL and SOSL queries against the org.
- Results display in a data grid. Relationships (child-to-parent, parent-to-child) work in the same syntax as production SOQL.
- Useful for verifying data state without a separate tool.

**Source and Tests tabs:**
- Open, create, and save Apex classes, triggers, and Visualforce pages.
- Run individual test methods directly.

**Checkpoints:**
- Set up to five checkpoints in Apex code via the Developer Console to capture a heap dump at that line. These are required for the Apex Replay Debugger.

### Anonymous Apex Execution

Anonymous Apex lets developers run ad-hoc Apex in the current org without deploying a class. Common uses:

- Quickly fix or correct data records.
- Invoke a method under test to reproduce a bug.
- Test a single method before deploying.
- Batch jobs or Queueable invocation for immediate execution.

**Developer Console path:** Debug → Open Execute Anonymous Window → paste code → Execute.

**sf CLI path:** `sf apex run --file path/to/script.apex` or `sf apex run` (interactive).

Anonymous Apex runs with the **permissions of the current user**. It is not a public-facing API and does not require a class definition, but it does consume governor limits. Each execution is a fresh transaction.

### Apex Replay Debugger

The **Apex Replay Debugger** is a VS Code extension (part of the Salesforce Extensions for VS Code) that replays a debug log as if stepping through code in a traditional debugger. It supports:

- Step-over, step-into, step-out controls.
- Variable inspection at each point in the log.
- Heap dump inspection when checkpoints are set in the Developer Console.

**Setup steps:**
1. In VS Code, install the Salesforce Extension Pack.
2. Capture a debug log with **ApexCode set to FINEST** and checkpoints enabled for the code path you need.
3. Download the log to your local project directory.
4. In VS Code, right-click the log file → **Launch Apex Replay Debugger**.
5. Set breakpoints in your Apex source and start the replay.

**Key limitation:** The Replay Debugger replays what the log captured — it cannot re-execute code live. If the log is truncated before the error point, replay stops at the truncation. For this reason, keep the traced scope narrow and log level targeted.

---

## Mode 1: Set Up a Debug Log (Build from Scratch)

1. Go to **Setup → Debug Logs**.
2. Click **New**.
3. Set **Traced Entity Type** (User for interactive debugging, Automated Process for background jobs).
4. Select or search for the entity.
5. Set **Start Date** to now and **End Date** to 15–30 minutes from now (avoid long windows that generate excess logs).
6. Select or create a **Debug Level**. Recommended starting point: ApexCode = DEBUG, Database = INFO, all others = NONE.
7. Click **Save**.
8. Reproduce the operation that triggers the code you want to trace.
9. Return to **Setup → Debug Logs** and refresh. Click the log to open it.

---

## Mode 2: Read an Existing Debug Log

Debug logs use a structured format. Key events to look for:

- `EXECUTION_STARTED` / `EXECUTION_FINISHED` — marks the transaction boundary.
- `CODE_UNIT_STARTED` / `CODE_UNIT_FINISHED` — marks class/trigger/method boundaries.
- `SOQL_EXECUTE_BEGIN` / `SOQL_EXECUTE_END` — shows SOQL statements and row counts.
- `DML_BEGIN` / `DML_END` — shows DML operations and record counts.
- `FATAL_ERROR` — unhandled exception with stack trace.
- `LIMIT_USAGE_FOR_NS` — governor limit consumption at point of reporting.
- `USER_DEBUG` — output from `System.debug()` calls.

If the log ends with `*** Skipped N bytes of log` it was truncated. Reduce verbosity and re-capture.

---

## Mode 3: Troubleshoot Missing or Truncated Logs

| Symptom | Likely cause | Fix |
|---|---|---|
| No log appears after operation | Trace flag is expired or missing | Check expiry; create a new trace flag |
| Log exists but code section is absent | Wrong Traced Entity Type (e.g., User instead of Automated Process) | Add a trace flag for Automated Process |
| Log is cut off mid-execution | 20 MB cap reached | Reduce category verbosity; narrow trace window |
| Log shows but is empty | Code did not execute in the trace window | Verify the timestamp of the operation vs the trace flag window |
| Replay Debugger stops early | Log truncated before error point | Use FINEST ApexCode only for the method under test; set checkpoints |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Trace flag created for the correct entity type (User vs Automated Process)
- [ ] Trace flag is not expired; end time is in the future
- [ ] Log level is set appropriately (DEBUG for ApexCode, INFO or NONE for noisy categories)
- [ ] Log was captured after reproducing the operation (not before)
- [ ] Log size is under 20 MB (no truncation message at end)
- [ ] For Replay Debugger: log file is downloaded locally and ApexCode is set to FINEST

---

## Related Skills

- `apex/debug-and-logging` — logging strategy, custom logging frameworks, production observability (use when the question is about *how* to log, not *how to set up the tooling*)
- `apex/apex-test-class-standards` — writing and running Apex test classes
- `apex/soql-fundamentals` — writing the SOQL queries you run in the Query Editor
