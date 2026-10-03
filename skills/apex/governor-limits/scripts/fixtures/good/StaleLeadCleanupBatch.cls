public class StaleLeadCleanupBatch implements Database.Batchable<SObject>, Database.Stateful {

    // Database.Stateful allows instance vars to persist across execute() calls
    private Integer totalProcessed = 0;
    private Integer totalErrors = 0;

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        // A Batch QueryLocator returns up to 50 million rows (limits table L19856)
        return Database.getQueryLocator(
            'SELECT Id, Status, LastActivityDate FROM Lead ' +
            'WHERE Status != \'Closed\' AND LastActivityDate < LAST_N_YEARS:1'
        );
    }

    public void execute(Database.BatchableContext ctx, List<SObject> scope) {
        // Limits reset for each execute() (limits table L19530 to L19531)
        List<Lead> leads = (List<Lead>) scope;
        List<Lead> toUpdate = new List<Lead>();

        for (Lead l : leads) {
            l.Status = 'Closed - No Response';
            toUpdate.add(l);
        }

        Database.SaveResult[] results = Database.update(toUpdate, false); // allOrNone = false
        totalProcessed += results.size();
        for (Database.SaveResult sr : results) {
            if (!sr.isSuccess()) totalErrors++;
        }
    }

    public void finish(Database.BatchableContext ctx) {
        // Send completion email
        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new List<String>{'ops-team@company.com'});
        email.setSubject('Stale Lead Cleanup Complete');
        email.setPlainTextBody(
            'Processed: ' + totalProcessed + '\nErrors: ' + totalErrors
        );
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{email});
    }
}

