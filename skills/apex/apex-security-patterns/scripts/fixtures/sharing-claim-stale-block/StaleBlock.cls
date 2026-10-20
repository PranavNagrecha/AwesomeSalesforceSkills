public inherited sharing class StaleBlock {
    public static List<Account> run() {
        /*
         * Returns accounts for the batch job.
         * AccessLevel.SYSTEM_MODE is used here and
         * ignores record sharing, giving the job access to all records.
         */
        // reason: batch job reads fields the running user cannot see
        return Database.query('SELECT Id FROM Account', AccessLevel.SYSTEM_MODE);
    }
}
