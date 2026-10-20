public inherited sharing class StaleSingle {
    public static List<Account> run() {
        // reason: needs Account fields the user cannot read. WITH SYSTEM_MODE bypasses sharing, so this returns every account.
        return [SELECT Id FROM Account WITH SYSTEM_MODE];
    }
}
