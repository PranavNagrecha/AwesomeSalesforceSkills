public with sharing class BatchCallsFuture implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Account]);
    }
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account a : scope) {
            LegacyFuture.syncAccount(a.Id);
        }
    }
    public void finish(Database.BatchableContext bc) {
    }
}
