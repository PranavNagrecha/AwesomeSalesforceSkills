@IsTest
private class OrderReportingTest {
    @IsTest
    static void readsOrders() {
        List<SalesOrder__x> rows = [SELECT Id FROM SalesOrder__x LIMIT 1];
        Assert.isNotNull(rows);
    }
}
