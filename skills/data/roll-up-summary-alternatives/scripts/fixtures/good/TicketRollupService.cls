public without sharing class TicketRollupService {
    // without sharing: the total must count every ticket, not only those the editing user can see.

    public static void collectAndRecalculate(List<Service_Ticket__c> newRows, Map<Id, Service_Ticket__c> oldMap) {
        Set<Id> accountIds = new Set<Id>();
        if (newRows != null) {
            for (Service_Ticket__c t : newRows) {
                if (t.Account__c != null) {
                    accountIds.add(t.Account__c);
                }
            }
        }
        if (oldMap != null) {
            for (Service_Ticket__c t : oldMap.values()) {
                if (t.Account__c != null) {
                    accountIds.add(t.Account__c); // old parent on reparent or delete
                }
            }
        }
        recalculate(accountIds);
    }

    public static void recalculate(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return;
        }
        Map<Id, Integer> counts = new Map<Id, Integer>();
        for (Id accountId : accountIds) {
            counts.put(accountId, 0);
        }
        // One aggregate per transaction. COUNT with GROUP BY uses one query row per group.
        for (AggregateResult ar : [
            SELECT Account__c accountId, COUNT(Id) openCount
            FROM Service_Ticket__c
            WHERE Account__c IN :accountIds AND Is_Closed__c = false
            GROUP BY Account__c
        ]) {
            counts.put((Id) ar.get('accountId'), (Integer) ar.get('openCount'));
        }
        List<Account> changed = new List<Account>();
        for (Account a : [SELECT Id, Open_Ticket_Count__c FROM Account WHERE Id IN :accountIds]) {
            Integer fresh = counts.get(a.Id);
            if (a.Open_Ticket_Count__c == null || a.Open_Ticket_Count__c.intValue() != fresh) {
                changed.add(new Account(Id = a.Id, Open_Ticket_Count__c = fresh));
            }
        }
        // Writing only changed parents keeps parent locks and parent save procedures to a minimum.
        update changed;
    }
}
