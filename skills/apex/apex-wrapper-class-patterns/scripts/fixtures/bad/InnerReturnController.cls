public with sharing class InnerReturnController {
    public class Row {
        @AuraEnabled public String name;
    }
    @AuraEnabled(cacheable=true)
    public static List<Row> getRows() {
        return new List<Row>();
    }
}
