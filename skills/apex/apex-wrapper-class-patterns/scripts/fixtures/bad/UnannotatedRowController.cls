public with sharing class UnannotatedRowController {
    @AuraEnabled
    public static UnannotatedRow save(UnannotatedRow input) {
        return input;
    }
}
