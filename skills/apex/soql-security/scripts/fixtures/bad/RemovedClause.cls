public with sharing class RemovedClause {
    @AuraEnabled(cacheable=true)
    public static List<Account> top() {
        return [SELECT Id, Name FROM Account WITH SECURITY_ENFORCED LIMIT 10];
    }
}
