/**
 * Template: Apex-Defined Type for Flow.
 *
 * Rules:
 *  - Every exposed field annotated with @AuraEnabled.
 *  - No Map<> — use List<KeyValue> pattern.
 *  - No required-arg constructors.
 *  - Data only. Put behaviour in a service class.
 */
public class ExampleResponse {
    @AuraEnabled public String id;
    @AuraEnabled public String status;
    @AuraEnabled public Datetime retrievedAt;
    @AuraEnabled public List<Item> items;
    @AuraEnabled public List<KeyValue> metadata;

    public class Item {
        @AuraEnabled public String code;
        @AuraEnabled public Decimal amount;
        @AuraEnabled public List<String> tags;
    }

    public class KeyValue {
        @AuraEnabled public String key;
        @AuraEnabled public String value;
    }
}
