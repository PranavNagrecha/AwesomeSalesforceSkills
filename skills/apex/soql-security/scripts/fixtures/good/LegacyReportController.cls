public with sharing class LegacyReportController {
    @AuraEnabled(cacheable=true)
    public static List<Contact> recent(Id accountId) {
        return Database.query(
            'SELECT Id, LastName FROM Contact WHERE AccountId = :accountId',
            AccessLevel.USER_MODE
        );
    }
}
