public with sharing class AccountService {
    public static List<Account> load() {
        return [SELECT Id FROM Account];
    }
}
