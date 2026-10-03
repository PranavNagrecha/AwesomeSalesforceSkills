/**
 * Bulk-safe service skeleton: collect keys, query once, map, process in memory, DML once.
 * Example rule: stamp each Account's Description with its number of related Contacts.
 * Safe for a 200-record trigger chunk; for platform event or CDC triggers, design for 2,000.
 * Limits referenced: 100 SOQL / 150 DML statements / 10,000 DML rows per synchronous
 * transaction (Apex Developer Guide 262, Per-Transaction Apex Limits; see references/limits-table.md).
 */
public with sharing class BulkSafeService {

    public static void process(List<Account> records) {
        // 1. Collect IDs first so the query happens once per transaction.
        Set<Id> accountIds = new Set<Id>();
        for (Account recordItem : records) {
            if (recordItem.Id != null) {
                accountIds.add(recordItem.Id);
            }
        }
        if (accountIds.isEmpty()) {
            return;
        }

        // 2. Query once outside loops. COUNT with GROUP BY costs one query row per group.
        Map<Id, Integer> contactCountByAccount = new Map<Id, Integer>();
        for (AggregateResult ar : [
            SELECT AccountId accountId, COUNT(Id) contactCount
            FROM Contact
            WHERE AccountId IN :accountIds
            WITH USER_MODE
            GROUP BY AccountId
        ]) {
            contactCountByAccount.put((Id) ar.get('accountId'), (Integer) ar.get('contactCount'));
        }

        // 3. Process in memory; build only the rows that change.
        List<Account> toUpdate = new List<Account>();
        for (Id accountId : accountIds) {
            Integer contacts = contactCountByAccount.containsKey(accountId) ? contactCountByAccount.get(accountId) : 0;
            toUpdate.add(new Account(Id = accountId, Description = 'Contacts: ' + contacts));
        }

        // 4. DML once.
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }
}
