public class StaticIsoQuery {
    public static List<Account> run() {
        return [SELECT Id, AnnualRevenue, CurrencyIsoCode FROM Account LIMIT 10];
    }
}
