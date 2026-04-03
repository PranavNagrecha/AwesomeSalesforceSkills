public with sharing class BulkSafeService {

    public static void process(List<Account> records) {
        // Collect IDs first so the query happens once per transaction.
        Set<Id> accountIds = new Set<Id>();
        for (Account recordItem : records) {
            if (recordItem.Id != null) {
                accountIds.add(recordItem.Id);
            }
        }

        if (accountIds.isEmpty()) {
            return;
        }

        // Query once outside loops. Add only the fields the business rule needs.
        Map<Id, Account> existingById = new Map<Id, Account>([
            SELECT Id, Name
            FROM Account
            WHERE Id IN :accountIds
        ]);

        List<Account> toUpdate = new List<Account>();
        for (Account recordItem : records) {
            Account existing = existingById.get(recordItem.Id);
            if (existing == null) {
                continue;
            }

            // TODO: Replace this example update with real business logic.
            existing.Name = existing.Name;
            toUpdate.add(existing);
        }

        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }
}
