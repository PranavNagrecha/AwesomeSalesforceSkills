# LLM Anti-Patterns: Debug Logs and Developer Console

Common mistakes AI coding assistants make when advising on debug log setup, trace flags, and Developer Console usage.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Setting all log categories to FINEST level

**What the LLM generates:**

```
Set all categories to FINEST:
- Apex Code: FINEST
- Database: FINEST
- Callout: FINEST
- Workflow: FINEST
- Validation: FINEST
- System: FINEST
```

**Why it happens:** LLMs recommend maximum verbosity to "capture everything." FINEST everywhere produces logs that pass 20 MB, and the platform then removes older lines from anywhere in the log (Apex Developer Guide 262, "Debug Log Limits"). Apex Code at FINEST also logs every variable assignment, including sensitive values.

**Correct pattern:**

```
Targeted log levels for Apex debugging:
- Apex Code: FINE or DEBUG (shows System.debug output)
- Database: FINE (shows SOQL/DML)
- Callout: FINE (shows HTTP requests/responses)
- Workflow: ERROR (unless debugging automation)
- Validation: ERROR (unless debugging validation rules)
- System: WARN
```

**Detection hint:** Advice to set all log categories to `FINEST`; levels should be targeted per debugging scenario.

---

## Anti-Pattern 2: Creating a trace flag on the wrong entity type

**What the LLM generates:**

```
To debug a scheduled job:
Setup > Debug Logs > New > Traced Entity Type: User > [select your user]
```

**Why it happens:** LLMs default to one user-level trace flag for every scenario, or the opposite: they suggest a class trace flag as a way to capture a class. Neither matches how logging works.

**Correct pattern:**

```
Platform event triggers, event processes, resumed flow interviews, publish callbacks:
  Traced Entity Type: Automated Process (or the running user configured on the trigger)
  (Platform Events Developer Guide 262, "Set Up Debug Logs for Event Subscriptions")

More detail for one Apex class or trigger:
  Keep a User or Automated Process trace flag, AND add Traced Entity Type: Apex Class
  with higher levels. A class trace flag (CLASS_TRACING) overrides levels but never
  generates a log on its own (Apex Developer Guide 262, "Debug Log Order of Precedence").

Scheduled, Batch, Queueable Apex:
  Trace the user who scheduled or submitted the job; add Automated Process if no log
  appears. UNVERIFIED (2026-10-03): the 262 guides do not state which user these log under.
```

**Detection hint:** Only the publishing user traced for platform event triggers, or a class trace flag offered as the only trace flag.

---

## Anti-Pattern 3: Advising to use Developer Console for production debugging

**What the LLM generates:**

```
Open the Developer Console in your production org to step through the issue in real-time.
```

**Why it happens:** LLMs do not distinguish between environments. Opening the Developer Console sets a `DEVELOPER_LOG` trace flag, its log levels apply to all logs including deployment logs, and it offers ad-hoc anonymous Apex against production data (Apex Developer Guide 262, "Debug Log Order of Precedence" and "Debug Log Levels"). UNVERIFIED (2026-10-03): claims that the Console is less reliable in production than in sandboxes.

**Correct pattern:**

```
For production debugging:
1. Set up a trace flag via Setup > Debug Logs (the user or Automated Process; add a class trace flag only for extra detail)
2. Reproduce the issue
3. Download the debug log file
4. Analyze locally using VS Code with the Apex Replay Debugger
   - sf apex get log --log-id <logId> --target-org prod
   - Set checkpoints and replay offline

For sandbox: Developer Console is acceptable for interactive debugging.
```

**Detection hint:** Recommending Developer Console usage specifically for production orgs.

---

## Anti-Pattern 4: Running anonymous Apex in production without warning about side effects

**What the LLM generates:**

```apex
// "Quick fix" via Execute Anonymous:
List<Account> accounts = [SELECT Id FROM Account WHERE Status__c = 'Bad'];
delete accounts;
```

**Why it happens:** LLMs suggest anonymous Apex as a quick data fix without saying how it runs. It runs as the current user, with sharing, and fails to compile if it violates that user's object or field permissions (Apex Developer Guide 262, "Anonymous Blocks"). It has no undo once it commits, and it leaves no deployment record or version history. Version 1.0.0 of this file said it runs in full system context; that was wrong.

**Correct pattern:**

```apex
// If anonymous Apex is truly needed:
// 1. Run in a SANDBOX first
// 2. Add explicit safety checks
// 3. Use Database.delete with allOrNone=false
// 4. Log what was modified

List<Account> accounts = [SELECT Id, Name FROM Account WHERE Status__c = 'Bad' LIMIT 10];
System.debug('About to delete ' + accounts.size() + ' accounts:');
for (Account a : accounts) {
    System.debug('  - ' + a.Id + ': ' + a.Name);
}
// Comment out the delete until you verify the debug output
// Database.delete(accounts, false);
```

**Detection hint:** Anonymous Apex snippets containing `delete ` or `update ` on production data without `LIMIT`, safety checks, or dry-run logging.

---

## Anti-Pattern 5: Forgetting that trace flags expire and must be renewed

**What the LLM generates:**

```
Set up the trace flag and then reproduce the issue whenever it happens next.
```

**Why it happens:** LLMs advise setting a trace flag as a one-time action. `ExpirationDate` must be less than 24 hours after `StartDate` (Tooling API Developer Guide 262, "TraceFlag"). If the issue does not reproduce within that window, the trace flag expires silently and no logs are captured.

**Correct pattern:**

```
1. Set the trace flag with an expiration just under 24 hours from the start
2. Note the expiration time
3. If the issue is intermittent, set a calendar reminder to renew the trace flag
4. Alternatively, use the sf CLI to automate renewal:
   sf apex tail log --target-org myOrg
   (sets a DEVELOPER_LOG trace flag for your own user and streams logs;
    UNVERIFIED 2026-10-03: whether it renews the flag past 24 hours)
5. For persistent monitoring beyond 24 hours, use a custom logging
   framework that writes to a custom object or platform event
```

**Detection hint:** Trace flag setup instructions with no mention of expiration time or renewal.

---

## Anti-Pattern 6: Suggesting SOQL queries in Developer Console without mentioning the tooling API context

**What the LLM generates:**

```
In the Developer Console Query Editor, run:
SELECT Id, Name FROM Account WHERE CreatedDate = TODAY
```

**Why it happens:** The advice is correct for the Query Editor tab, but LLMs do not mention that the Developer Console also has a Tooling API query option. If a user is trying to query `ApexClass`, `ApexTrigger`, or `TraceFlag` records and is in the wrong query mode (regular SOQL vs Tooling API), the query returns zero results with no error.

**Correct pattern:**

```
Developer Console Query Editor has two modes:
- "Use Tooling API" checkbox UNCHECKED: queries standard SObjects (Account, Contact, etc.)
- "Use Tooling API" checkbox CHECKED: queries Tooling objects (ApexClass, ApexLog, TraceFlag, etc.)

To query debug logs:
1. Check "Use Tooling API"
2. Run: SELECT Id, Operation, Status, LogLength FROM ApexLog ORDER BY StartTime DESC LIMIT 20

To query data:
1. Uncheck "Use Tooling API"
2. Run: SELECT Id, Name FROM Account WHERE CreatedDate = TODAY
```

**Detection hint:** Advice to query `ApexLog`, `ApexClass`, or `TraceFlag` without mentioning Tooling API mode.
