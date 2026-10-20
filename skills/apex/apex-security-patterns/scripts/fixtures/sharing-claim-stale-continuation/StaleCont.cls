public inherited sharing class StaleCont {
    public static List<Account> run() {
        // reason: needs the field values the user cannot read. Under
        // system mode the query runs for the
        // whole org and bypasses sharing entirely.
        return [SELECT Id FROM Account WITH SYSTEM_MODE];
    }
}
