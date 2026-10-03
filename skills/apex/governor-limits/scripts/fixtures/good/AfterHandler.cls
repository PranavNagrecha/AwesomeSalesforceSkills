public class AfterHandler {
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

}
