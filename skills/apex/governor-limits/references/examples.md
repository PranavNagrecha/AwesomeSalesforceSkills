# Governor Limits — Examples

## Example 1: Refactoring SOQL-in-Loop in a Trigger Handler

### Before

```apex
public void onAfterInsert(List<Opportunity> newRecords) {
    for (Opportunity opp : newRecords) {
        // ❌ 1 SOQL per record — 200 opportunities = 200 SOQL
        Account acc = [SELECT Id, Name FROM Account WHERE Id = :opp.AccountId];
        acc.Last_Won_Date__c = (opp.StageName == 'Closed Won') ? opp.CloseDate : acc.Last_Won_Date__c;
        update acc; // ❌ 1 DML per record
    }
}
```

### After

```apex
public void onAfterInsert(List<Opportunity> newRecords) {
    // 1. Collect IDs
    Set<Id> accountIds = new Set<Id>();
    for (Opportunity opp : newRecords) {
        if (opp.StageName == 'Closed Won') {
            accountIds.add(opp.AccountId);
        }
    }
    if (accountIds.isEmpty()) return;

    // 2. Query once
    Map<Id, Account> accountMap = new Map<Id, Account>(
        [SELECT Id, Last_Won_Date__c FROM Account WHERE Id IN :accountIds]
    );

    // 3. Process in memory
    for (Opportunity opp : newRecords) {
        if (opp.StageName == 'Closed Won' && accountMap.containsKey(opp.AccountId)) {
            Account acc = accountMap.get(opp.AccountId);
            if (acc.Last_Won_Date__c == null || opp.CloseDate > acc.Last_Won_Date__c) {
                acc.Last_Won_Date__c = opp.CloseDate;
            }
        }
    }

    // 4. DML once
    update accountMap.values();
}
```

Result: 2 statements (1 SOQL + 1 DML) regardless of number of Opportunities.

---

## Example 2: Queueable for Post-DML Callout

### Trigger Handler (after DML complete)

```apex
public void onAfterInsert(List<Contact> newRecords) {
    // Don't make callout here — DML has occurred in this transaction
    Set<Id> ids = new Map<Id, Contact>(newRecords).keySet();
    System.enqueueJob(new ContactSyncQueueable(ids));
}
```

### Queueable Implementation

```apex
public class ContactSyncQueueable implements Queueable, Database.AllowsCallouts {

    private Set<Id> contactIds;

    public ContactSyncQueueable(Set<Id> contactIds) {
        this.contactIds = contactIds;
    }

    public void execute(QueueableContext ctx) {
        List<Contact> contacts = [
            SELECT Id, FirstName, LastName, Email
            FROM Contact
            WHERE Id IN :contactIds
        ];

        // Fresh governor context: 200 SOQL, 60s CPU
        for (Contact c : contacts) {
            try {
                ExternalCRMClient.syncContact(c);
            } catch (Exception e) {
                // Log per contact — don't fail entire job on one bad record
                Error_Log__c log = new Error_Log__c(
                    Contact__c = c.Id,
                    Error_Message__c = e.getMessage()
                );
                insert log;
            }
        }
    }
}
```

---

## Example 3: Batch Apex for Nightly Cleanup

```apex
public class StaleLeadCleanupBatch implements Database.Batchable<SObject>, Database.Stateful {

    // Database.Stateful allows instance vars to persist across execute() calls
    private Integer totalProcessed = 0;
    private Integer totalErrors = 0;

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        // QueryLocator handles up to 50M rows via cursor pagination
        return Database.getQueryLocator(
            'SELECT Id, Status, LastActivityDate FROM Lead ' +
            'WHERE Status != \'Closed\' AND LastActivityDate < LAST_N_YEARS:1'
        );
    }

    public void execute(Database.BatchableContext ctx, List<SObject> scope) {
        // Each execute() = fresh governor limits
        List<Lead> leads = (List<Lead>) scope;
        List<Lead> toUpdate = new List<Lead>();

        for (Lead l : leads) {
            l.Status = 'Closed - No Response';
            toUpdate.add(l);
        }

        Database.SaveResult[] results = Database.update(toUpdate, false); // allOrNone = false
        totalProcessed += results.size();
        for (Database.SaveResult sr : results) {
            if (!sr.isSuccess()) totalErrors++;
        }
    }

    public void finish(Database.BatchableContext ctx) {
        // Send completion email
        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new List<String>{'ops-team@company.com'});
        email.setSubject('Stale Lead Cleanup Complete');
        email.setPlainTextBody(
            'Processed: ' + totalProcessed + '\nErrors: ' + totalErrors
        );
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{email});
    }
}

// Schedule it:
// Database.executeBatch(new StaleLeadCleanupBatch(), 200);
```

---

## Example 4: Monitoring Limits During Development

```apex
public class LimitMonitor {

    public static void checkpoint(String label) {
        System.debug('=== LIMIT CHECK: ' + label + ' ===');
        System.debug('SOQL: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
        System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
        System.debug('DML Rows: ' + Limits.getDmlRows() + '/' + Limits.getLimitDmlRows());
        System.debug('CPU (ms): ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
        System.debug('Heap (bytes): ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
    }
}

// Usage in service class during development:
LimitMonitor.checkpoint('before bulk query');
List<Account> accounts = [SELECT Id FROM Account WHERE ...];
LimitMonitor.checkpoint('after bulk query, before processing');
// ... processing
LimitMonitor.checkpoint('after processing, before DML');
update accountsToUpdate;
LimitMonitor.checkpoint('after DML');
```
