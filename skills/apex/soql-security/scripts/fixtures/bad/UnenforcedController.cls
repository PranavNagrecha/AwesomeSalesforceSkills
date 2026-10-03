public class UnenforcedController {
    @AuraEnabled(cacheable=true)
    public static List<Account> all() {
        return [SELECT Id, Name, AnnualRevenue FROM Account];
    }
}
