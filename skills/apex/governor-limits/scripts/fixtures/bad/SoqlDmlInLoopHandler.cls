public class SoqlDmlInLoopHandler {
public void onAfterInsert(List<Opportunity> newRecords) {
    for (Opportunity opp : newRecords) {
        // ❌ 1 SOQL per record; 200 opportunities = 200 SOQL
        Account acc = [SELECT Id, Name FROM Account WHERE Id = :opp.AccountId];
        acc.Last_Won_Date__c = (opp.StageName == 'Closed Won') ? opp.CloseDate : acc.Last_Won_Date__c;
        update acc; // ❌ 1 DML per record
    }
}

}
