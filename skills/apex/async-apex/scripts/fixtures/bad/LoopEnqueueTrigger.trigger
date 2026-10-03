trigger LoopEnqueueTrigger on Order__c (after insert) {
    for (Order__c o : Trigger.new) {
        System.enqueueJob(new OrderDispatchQueueable(new Set<Id>{ o.Id }));
    }
}
