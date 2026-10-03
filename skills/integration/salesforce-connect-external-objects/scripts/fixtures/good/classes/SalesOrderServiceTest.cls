@IsTest
private class SalesOrderServiceTest {
    private class OpenOrderStub extends SoqlStubProvider {
        public override List<SObject> handleSoqlQuery(
            SObjectType sobjectType, String rawQuery, Map<String, Object> binds
        ) {
            Assert.areEqual('C-1001', binds.get('customer'), 'The bind value reaches the stub');
            return new List<SObject>{
                Test.createStubQueryRow(sobjectType, new Map<String, Object>{
                    'Status__c' => 'Open',
                    'Amount__c' => 250.00
                })
            };
        }
    }

    @IsTest
    static void returnsOpenOrdersFromTheStub() {
        Test.createSoqlStub(SalesOrder__x.SObjectType, new OpenOrderStub());
        Test.startTest();
        List<SalesOrder__x> rows = SalesOrderService.openOrdersFor('C-1001');
        Test.stopTest();
        Assert.areEqual(1, rows.size(), 'One stubbed order');
        Assert.areEqual('Open', rows[0].Status__c, 'Stubbed field value');
    }
}
