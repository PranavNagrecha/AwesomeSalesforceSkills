public inherited sharing class CorrectPlain {
    public static List<Account> run() {
        // reason: the integration user lacks Account field access. Sharing follows the class,
        // which is inherited sharing, so rows stay visibility-filtered. To see all records you
        // would also need a without sharing helper class.
        return [SELECT Id FROM Account WITH SYSTEM_MODE];
    }
}
