trigger OrderTrigger on Order__c (after insert, after update) {
    Set<Id> changedOrderIds = new Set<Id>();
    for (Order__c record : Trigger.new) {
        Order__c previous = Trigger.isUpdate ? Trigger.oldMap.get(record.Id) : null;
        if (previous == null || previous.Status__c != record.Status__c) {
            changedOrderIds.add(record.Id);
        }
    }
    if (!changedOrderIds.isEmpty()) {
        System.enqueueJob(new OrderDispatchQueueable(changedOrderIds)); // one job per chunk
    }
}
