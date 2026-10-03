public with sharing class LegacyEhrWriter {
    public static void write(Id patientId, String code) {
        insert new HC24__EhrCondition__c(HC24__Patient__c = patientId, HC24__Code__c = code);
    }
}
