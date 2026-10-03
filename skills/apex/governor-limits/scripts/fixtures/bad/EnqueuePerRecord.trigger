trigger EnqueuePerRecord on Account (after insert) {
    for (Account a : Trigger.new) { System.enqueueJob(new AccountSyncJob(a.Id)); }
}
