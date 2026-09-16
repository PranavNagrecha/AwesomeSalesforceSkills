public with sharing class RealSecurityEnforced {
    public static List<Account> queryAccounts() {
        return [SELECT Id FROM Account WITH SECURITY_ENFORCED];
    }
}
