public class ConvertInWhere {
    public static List<Opportunity> run() {
        return [SELECT Id, convertCurrency(Amount) FROM Opportunity WHERE convertCurrency(Amount) > 1000000];
    }
}
