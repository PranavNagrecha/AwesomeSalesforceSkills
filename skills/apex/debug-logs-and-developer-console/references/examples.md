# Examples: Debug Logs and Developer Console

## Example 1: Script the debug level and trace flags

**Context:** A platform event trigger fails intermittently; its logs land under Automated Process, and one handler class needs more detail.

**Approach:** Create a debug level, an Automated Process `USER_DEBUG` trace flag, and a `CLASS_TRACING` flag on the handler through the Tooling API, keeping the window under 24 hours, then pull logs with `sf apex get log`. The full script and the ID lookup queries are in `code-examples.md`.

---

## Example 2: Anonymous Apex data fix with a dry run

**Context:** A misconfigured automation set `Legacy_Code__c` on up to 200 Accounts. The value must be cleared before the corrected automation goes live.

**Solution:** Run a dry run first, then the fix, in a sandbox before production.

```apex
// Anonymous Apex runs as the current user, with sharing, and fails to compile
// if the user lacks access to the object or field.
Boolean dryRun = true;
List<Account> records = [
    SELECT Id, Name, Legacy_Code__c
    FROM Account
    WHERE Legacy_Code__c != null
    LIMIT 200
];
System.debug(LoggingLevel.INFO, 'Matched ' + records.size() + ' accounts');
for (Account a : records) {
    a.Legacy_Code__c = null;
}
if (!dryRun) {
    List<Database.SaveResult> results = Database.update(records, false);
    Integer failed = 0;
    for (Database.SaveResult r : results) {
        if (!r.isSuccess()) {
            failed++;
        }
    }
    System.debug(LoggingLevel.INFO, 'Updated ' + (records.size() - failed) + ', failed ' + failed);
}
```

Run it with `sf apex run --file fix-legacy-code.apex` or from the Developer Console Execute Anonymous window, read the `USER_DEBUG` lines, then set `dryRun = false` and run again.

**Why it works:** The dry run shows the count before anything changes. Sharing and field permissions apply because anonymous blocks run as the current user (Apex Developer Guide 262, "Anonymous Blocks"). The DML row limit is 10,000 per transaction (Per-Transaction Apex Limits, L19556), so larger fixes belong in Batch Apex.

---

## Example 3: Replaying a trigger failure in VS Code

**Context:** An Opportunity trigger throws a null pointer exception only for some Accounts.

**Solution:**

1. Set a user trace flag for the developer's user with Apex Code at a high level, plus a `CLASS_TRACING` flag on the trigger's handler if extra detail is needed.
2. Reproduce the failure, then `sf apex get log --number 1 --output-dir ./logs`.
3. In VS Code with the Salesforce Extensions, open the log and launch the Apex Replay Debugger; set breakpoints in the trigger handler and step through.

**Why it works:** The replay steps through what the log recorded, so variable values are visible without redeploying `System.debug` statements. UNVERIFIED (2026-10-03): the exact level the Replay Debugger requires and how many Developer Console checkpoints it can use; the extension documentation did not return text to a fetch.

---

## Anti-Pattern: Setting all log categories to FINEST

**What practitioners do:** Set every category to FINEST so nothing is missed.

**What goes wrong:** The log passes 20 MB and older lines are removed from anywhere in it, so early `USER_DEBUG` output can vanish. Apex Code at FINEST also records every variable assignment, including sensitive values (Apex Developer Guide 262, "Debug Log Limits" and the header warning).

**Correct approach:** Start with Apex Code DEBUG and Database INFO, and raise one category, or one class through a class trace flag, for the shortest window that reproduces the failure.
