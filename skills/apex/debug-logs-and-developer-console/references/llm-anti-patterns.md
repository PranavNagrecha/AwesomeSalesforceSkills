# LLM Anti-Patterns — Debug Logs and Developer Console

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

**Why it happens:** LLMs recommend maximum verbosity to "capture everything." But FINEST on all categories produces massive debug logs that hit the 20 MB log size limit, causing truncation. The critical information gets buried or cut off. Workflow and Validation at FINEST generate enormous output for orgs with many automation rules.

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

**Detection hint:** Advice to set all log categories to `FINEST` — should be targeted per debugging scenario.

---

## Anti-Pattern 2: Creating a trace flag on the wrong entity type

**What the LLM generates:**

```
To debug a scheduled job:
Setup > Debug Logs > New > Traced Entity Type: User > [select your user]
```

**Why it happens:** LLMs default to user-level trace flags for all scenarios. Scheduled Apex, platform event subscribers, and Batch Apex may run as the "Automated Process" user or a different context user. A trace flag on your personal user will not capture logs for those executions.

**Correct pattern:**

```
For scheduled/batch jobs running as Automated Process:
Setup > Debug Logs > New > Traced Entity Type: Automated Process

For a specific Apex class:
Setup > Debug Logs > New > Traced Entity Type: Apex Class > [select the class]

For platform event triggers:
Traced Entity Type: Automated Process (event triggers run in system context)
```

**Detection hint:** Advice to set trace flags on a specific user when debugging scheduled jobs, batch jobs, or platform event triggers.

---

## Anti-Pattern 3: Advising to use Developer Console for production debugging

**What the LLM generates:**

```
Open the Developer Console in your production org to step through the issue in real-time.
```

**Why it happens:** LLMs do not distinguish between environments. The Developer Console has known performance and reliability issues in production orgs — it can time out, lose connection, or fail to render large logs. It also adds risk by providing ad-hoc query and anonymous Apex access in production.

**Correct pattern:**

```
For production debugging:
1. Set up a trace flag via Setup > Debug Logs (targeted user/class)
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

**Why it happens:** LLMs suggest anonymous Apex as a quick data fix tool without warning that it runs in full system context, bypasses validation rules with certain configurations, has no undo mechanism, and is not auditable (no deployment record, no version history).

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

**Why it happens:** LLMs advise setting a trace flag as a one-time action. Trace flags have a maximum duration of 24 hours (and the UI defaults to shorter). If the issue does not reproduce within that window, the trace flag expires silently and no logs are captured.

**Correct pattern:**

```
1. Set the trace flag with the maximum expiration (24 hours from now)
2. Note the expiration time
3. If the issue is intermittent, set a calendar reminder to renew the trace flag
4. Alternatively, use the sf CLI to automate renewal:
   sf apex tail log --target-org myOrg
   (keeps the trace active as long as the command runs)
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
