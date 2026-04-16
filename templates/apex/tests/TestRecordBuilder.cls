/**
 * TestRecordBuilder — fluent builder for arbitrary SObjects in tests.
 *
 * Use when TestDataFactory doesn't cover the shape you need, or when you
 * want one-off records with specific field values without bloating the
 * factory with dozens of overloads.
 *
 *     Account a = (Account) new TestRecordBuilder(Account.SObjectType)
 *         .set('Name', 'Edge case')
 *         .set('Industry', 'Technology')
 *         .build();
 *     insert a;
 */
@IsTest
public class TestRecordBuilder {

    private Schema.SObjectType token;
    private Map<String, Object> fields = new Map<String, Object>();

    public TestRecordBuilder(Schema.SObjectType token) {
        if (token == null) {
            throw new TestRecordBuilderException('SObjectType is required');
        }
        this.token = token;
    }

    public TestRecordBuilder set(String fieldApiName, Object value) {
        fields.put(fieldApiName, value);
        return this;
    }

    public TestRecordBuilder setAll(Map<String, Object> values) {
        if (values != null) { fields.putAll(values); }
        return this;
    }

    public SObject build() {
        SObject record = token.newSObject();
        for (String key : fields.keySet()) {
            record.put(key, fields.get(key));
        }
        return record;
    }

    public SObject buildAndInsert() {
        SObject record = build();
        insert record;
        return record;
    }

    public List<SObject> buildMany(Integer count) {
        List<SObject> out = new List<SObject>();
        for (Integer i = 0; i < count; i++) {
            out.add(build());
        }
        return out;
    }

    public class TestRecordBuilderException extends Exception {}
}
