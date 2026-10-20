public inherited sharing class CorrectNegated {
    public static List<Account> run() {
        // reason: SYSTEM_MODE does not bypass sharing; it lifts object and field checks only.
        return [SELECT Id FROM Account WITH SYSTEM_MODE];
    }
}
