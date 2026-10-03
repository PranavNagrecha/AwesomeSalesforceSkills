trigger InsertUpdateOnlyRollup on Service_Ticket__c (after insert, after update) {
    TicketRollupService.collectAndRecalculate(Trigger.new, Trigger.oldMap);
}
