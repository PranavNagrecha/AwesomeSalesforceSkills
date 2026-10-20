public inherited sharing class StaleShared {
    public static List<Account> run() {
        // reason: FLS only. SYSTEM_MODE does not change the class sharing keyword. System mode bypasses sharing for batch jobs.
        return [SELECT Id FROM Account WITH SYSTEM_MODE];
    }
}
