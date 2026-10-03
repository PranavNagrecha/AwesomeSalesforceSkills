public class AggregateConvert {
    public static List<AggregateResult> totals() {
        return [SELECT OwnerId, convertCurrency(SUM(Amount)) total FROM Opportunity GROUP BY OwnerId];
    }
}
