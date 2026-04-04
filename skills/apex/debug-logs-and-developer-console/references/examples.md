# Examples — Debug Logs And Developer Console

## Example 1: Debugging a Scheduled Apex Job That Silently Fails

**Context:** A nightly scheduled Apex job is supposed to send reminder emails, but some users report not receiving them. There is no error in the org's standard email logs, and the developer cannot reproduce it interactively.

**Problem:** The developer sets up a debug log for their own user account and runs the scheduler manually, but the log shows nothing useful. The scheduler runs as an automated process, not as the developer's user context, so the developer's trace flag captures nothing from the actual job execution.

**Solution:**

1. Go to **Setup → Debug Logs → New**.
2. Set **Traced Entity Type** to **Automated Process**.
3. Set the trace window to cover the next scheduled run (e.g., 11:45 PM to 12:15 AM).
4. Set Debug Level: ApexCode = DEBUG, Database = INFO.
5. Allow the scheduler to run.
6. Retrieve the resulting log from **Setup → Debug Logs** after the run completes.
7. Search the log for `FATAL_ERROR` or `USER_DEBUG` to locate the failure.

```apex
// The scheduler class being debugged
global class NightlyReminderScheduler implements Schedulable {
    global void execute(SchedulableContext ctx) {
        // This runs as Automated Process, not as any named user
        List<Contact> contacts = [SELECT Id, Email FROM Contact WHERE ReminderDue__c = TODAY];
        System.debug(LoggingLevel.DEBUG, 'Contacts to remind: ' + contacts.size());
        for (Contact c : contacts) {
            // ... send logic
        }
    }
}
```

**Why it works:** Scheduled Apex, Batch Apex, and Queueable jobs run under the Automated Process system user. A User-scoped trace flag does not intercept their execution. Using the Automated Process entity type ensures the platform captures log output from background job transactions.

---

## Example 2: Using Anonymous Apex to Fix a Data Issue in Sandbox

**Context:** A validation rule was misconfigured and set a required field to an invalid value on 200 records. The developer needs to clear the field on all affected records before enabling the corrected validation rule.

**Problem:** There is no existing UI or admin tool to bulk-clear this field. Building and deploying a batch class just for a one-time fix would take too long. Manually editing 200 records is error-prone.

**Solution:**

1. In VS Code, open a terminal and run: `sf apex run`
2. Or in the Developer Console: **Debug → Open Execute Anonymous Window**.
3. Paste and execute the following:

```apex
// Fix: clear InvalidField__c on all records where it is set incorrectly
List<Account> records = [
    SELECT Id, InvalidField__c
    FROM Account
    WHERE InvalidField__c != null
    LIMIT 200
];
for (Account a : records) {
    a.InvalidField__c = null;
}
update records;
System.debug('Updated ' + records.size() + ' records');
```

4. After execution, check the debug log output to confirm the count matches expectations.
5. Re-run if more than 200 records need fixing (anonymous Apex shares the 10,000-row DML limit per transaction).

**Why it works:** Anonymous Apex runs in the current user's context with their permissions. It executes immediately without deployment, making it ideal for one-time data corrections in sandbox. The `System.debug` call after the DML lets the developer verify the record count in the log.

---

## Example 3: Using Apex Replay Debugger to Trace a Trigger Failure

**Context:** A trigger on the Opportunity object throws an unexpected `NullPointerException` in sandbox, but only when a specific condition in a related Account field is true. The stack trace alone does not pinpoint which variable is null.

**Problem:** Adding more `System.debug` calls and redeploying every time a variable is suspected is slow. The developer needs to inspect the runtime state of multiple variables simultaneously.

**Solution:**

1. In the Developer Console, open the Apex trigger source.
2. Set a **checkpoint** on the suspect line (click the margin next to the line number → **Set Checkpoint**). Checkpoints capture a heap dump at that execution point.
3. Go to **Setup → Debug Logs → New**. Set: User = developer's user, ApexCode = FINEST, end time = 30 minutes from now.
4. Reproduce the operation (create or edit an Opportunity with the triggering condition).
5. Download the resulting log file from **Setup → Debug Logs**.
6. In VS Code, right-click the log file → **Launch Apex Replay Debugger**.
7. Step through execution. When the replay reaches the checkpoint, inspect the **Variables** panel to see the heap snapshot — all local variables and their values at that point.

**Why it works:** The Apex Replay Debugger reads the log file sequentially, recreating execution state. Heap dumps captured by checkpoints allow variable inspection without needing to modify and redeploy the code. This is significantly faster than iterative debug-statement insertion when the exact null source is unknown.

---

## Anti-Pattern: Setting All Log Categories to FINEST

**What practitioners do:** When unsure what to capture, developers set every log category to FINEST to ensure nothing is missed.

**What goes wrong:** FINEST on all categories produces enormous logs that frequently hit the 20 MB cap and truncate before reaching the error point. The log is then useless — the most important output (the exception and stack trace near the end of the transaction) is cut off. Additionally, the sheer volume of data makes the log nearly impossible to read manually.

**Correct approach:** Start with ApexCode = DEBUG and Database = INFO. Only elevate categories (to FINE or FINEST) for the specific category you are investigating, and only for the shortest window needed to reproduce the failure. For Apex Replay Debugger use, set ApexCode to FINEST but keep all other categories at NONE or INFO to stay within the 20 MB limit.
