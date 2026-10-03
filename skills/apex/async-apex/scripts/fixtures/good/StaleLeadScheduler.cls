public with sharing class StaleLeadScheduler implements Schedulable {
    public void execute(SchedulableContext context) {
        // Synchronous limits apply to scheduled Apex, so dispatch and return.
        Database.executeBatch(new StaleLeadBatch(), 200);
    }
}
