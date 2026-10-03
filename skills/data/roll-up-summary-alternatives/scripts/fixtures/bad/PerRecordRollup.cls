public class PerRecordRollup {
    public static void run(List<Service_Ticket__c> tickets) {
        for (Service_Ticket__c t : tickets) {
            AggregateResult ar = [SELECT COUNT(Id) n FROM Service_Ticket__c WHERE Account__c = :t.Account__c];
            update new Account(Id = t.Account__c, Open_Ticket_Count__c = (Integer) ar.get('n'));
        }
    }
}
