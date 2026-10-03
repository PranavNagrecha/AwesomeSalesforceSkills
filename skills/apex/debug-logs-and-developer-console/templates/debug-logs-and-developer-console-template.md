# Debug Logs and Developer Console - Work Template

Use this template when helping a developer set up debug logs, read Apex log output, or use the Developer Console and Apex Replay Debugger.

---

## Scope

**Skill:** `debug-logs-and-developer-console`

**Request summary:** (fill in what the developer is trying to diagnose or accomplish)

---

## Context Gathered

- **Code or feature under investigation:** (Apex class name, trigger, scheduler, etc.)
- **Execution context:** [ ] Interactive (user-triggered) [ ] Scheduled Apex [ ] Batch [ ] Queueable [ ] Platform Event trigger
- **Environment:** [ ] Sandbox [ ] Scratch Org [ ] Production
- **Failure symptom:** (exception message, wrong data, no output, etc.)

---

## Trace Flag Setup

| Setting | Value |
|---|---|
| Traced Entity Type | [ ] User [ ] Automated Process (event triggers, event processes, resumed flows) [ ] Apex Class or Trigger (levels only; pair with a User or Automated Process flag) |
| Entity | (name or username) |
| Start Date/Time | (set to now or slightly before reproduction) |
| End Date/Time | (15 to 30 minutes from now; must be under 24 hours after start) |
| Debug Level: ApexCode | [ ] DEBUG [ ] FINE [ ] FINEST (not where sensitive values are handled) |
| Debug Level: Database | [ ] NONE [ ] INFO [ ] DEBUG |
| All other categories | NONE (unless specifically needed) |

**Setup path:** Setup > Debug Logs > New, or `sf data create record --use-tooling-api --sobject TraceFlag` (see references/code-examples.md)

---

## Reproduction Steps

1. Create the trace flag above.
2. (Describe the steps to trigger the code being debugged)
3. Return to Setup to Debug Logs and refresh.
4. Open the resulting log.

---

## Log Analysis Findings

| Event | Location in log | Observation |
|---|---|---|
| EXECUTION_STARTED | | |
| SOQL_EXECUTE_BEGIN | | |
| USER_DEBUG | | |
| FATAL_ERROR | | |
| LIMIT_USAGE_FOR_NS | | |
| EXECUTION_FINISHED | | |

**Is the log truncated?** [ ] Yes - reduce verbosity and re-capture [ ] No

---

## Anonymous Apex Script (if applicable)

```apex
// Paste the anonymous Apex script here
// Remember: runs as the current user - permissions apply
```

**Tested in sandbox first?** [ ] Yes [ ] No - do not run in production without sandbox validation

---

## Apex Replay Debugger Setup (if applicable)

- [ ] VS Code Salesforce Extension Pack installed
- [ ] Checkpoints set in Developer Console on suspect lines (checkpoint limit UNVERIFIED 2026-10-03)
- [ ] Debug log captured with high Apex Code detail on a narrow scope (required level UNVERIFIED 2026-10-03)
- [ ] Log file downloaded to local project directory
- [ ] Replay Debugger launched from the log file in VS Code

**Variables to inspect at checkpoint:** (list variables suspected of being null or wrong)

---

## Resolution

**Root cause identified:** (describe what was found)

**Fix applied:** (describe what was changed)

**Verified in log:** [ ] Yes - FATAL_ERROR no longer present [ ] Yes - USER_DEBUG shows expected values
