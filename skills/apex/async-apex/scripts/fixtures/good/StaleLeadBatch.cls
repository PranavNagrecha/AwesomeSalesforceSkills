public with sharing class StaleLeadBatch implements Database.Batchable<SObject>, Database.Stateful {
    private Integer failed = 0;

    public Database.QueryLocator start(Database.BatchableContext context) {
        return Database.getQueryLocator([
            SELECT Id, Status
            FROM Lead
            WHERE Status = 'Open - Not Contacted'
            AND LastActivityDate < LAST_N_DAYS:90
        ]);
    }

    public void execute(Database.BatchableContext context, List<Lead> scope) {
        for (Lead leadRecord : scope) {
            leadRecord.Status = 'Closed - Not Converted';
        }
        for (Database.SaveResult result : Database.update(scope, false)) {
            if (!result.isSuccess()) {
                failed++;
            }
        }
    }

    public void finish(Database.BatchableContext context) {
        System.debug(LoggingLevel.INFO, 'StaleLeadBatch ' + context.getJobId() + ' failed rows: ' + failed);
    }
}
