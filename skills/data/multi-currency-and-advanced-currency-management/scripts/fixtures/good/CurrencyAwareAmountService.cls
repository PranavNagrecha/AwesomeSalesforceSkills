public with sharing class CurrencyAwareAmountService {
    public static List<SObject> amounts(Set<Id> ids) {
        Boolean multi = UserInfo.isMultiCurrencyOrganization();
        String soql = 'SELECT Id, Amount' + (multi ? ', CurrencyIsoCode' : '') + ' FROM Opportunity WHERE Id IN :ids';
        return Database.queryWithBinds(soql, new Map<String, Object>{ 'ids' => ids }, AccessLevel.USER_MODE);
    }
    public static List<Opportunity> bigDeals() {
        return [SELECT Id, Name, convertCurrency(Amount) FROM Opportunity WHERE Amount > USD1000000 ORDER BY Amount DESC LIMIT 50];
    }
}
