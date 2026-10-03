trigger ServiceTicketRollup on Service_Ticket__c (after insert, after update, after delete, after undelete) {
    TicketRollupService.collectAndRecalculate(
        Trigger.isDelete ? null : Trigger.new,
        Trigger.isInsert || Trigger.isUndelete ? null : Trigger.oldMap
    );
}
