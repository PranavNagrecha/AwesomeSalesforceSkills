public with sharing class CommentOnlySecurityEnforced {
    public static List<Account> queryAccounts() {
        // WITH SECURITY_ENFORCED is not used: it was removed at 67.0 and does not compile.
        return [SELECT Id FROM Account];
    }
}
