@IsTest
private class FhirConditionNormalizerTest {

    static String conditionWithCodings(Integer count, Boolean withPeriod) {
        List<Object> codings = new List<Object>();
        for (Integer i = 0; i < count; i++) {
            codings.add(new Map<String, Object>{
                'system' => 'http://snomed.info/sct',
                'code' => String.valueOf(1000 + i),
                'display' => 'Concept ' + i
            });
        }
        Map<String, Object> resource = new Map<String, Object>{
            'resourceType' => 'Condition',
            'code' => new Map<String, Object>{ 'coding' => codings, 'text' => 'Test condition' }
        };
        if (withPeriod) {
            resource.put('onsetPeriod', new Map<String, Object>{ 'start' => '2026-01-10', 'end' => '2026-02-01T08:30:00Z' });
        }
        return JSON.serialize(resource);
    }

    @IsTest
    static void keepsFifteenCodingsAndFlattensPeriod() {
        Account patient = new Account(Name = 'FHIR Test Patient');
        insert patient;
        Test.startTest();
        FhirConditionNormalizer.Result r = FhirConditionNormalizer.ingest(conditionWithCodings(16, true), patient.Id);
        Test.stopTest();

        System.assertEquals(1, r.droppedCodings, 'sixteenth coding is reported, not stored');
        CodeSetBundle b = [SELECT Name, CodeSet1Id, CodeSet15Id FROM CodeSetBundle WHERE Id = :r.codeSetBundleId];
        System.assertEquals('Test condition', b.Name);
        System.assertNotEquals(null, b.CodeSet15Id);
        HealthCondition hc = [SELECT OnsetStartDateTime, OnsetEndDateTime FROM HealthCondition WHERE Id = :r.healthConditionId];
        System.assertNotEquals(null, hc.OnsetStartDateTime);
        System.assertNotEquals(null, hc.OnsetEndDateTime);
    }

    @IsTest
    static void reusesExistingCodeSets() {
        Account patient = new Account(Name = 'FHIR Test Patient 2');
        insert patient;
        FhirConditionNormalizer.ingest(conditionWithCodings(2, false), patient.Id);
        FhirConditionNormalizer.ingest(conditionWithCodings(2, false), patient.Id);
        System.assertEquals(2, [SELECT COUNT() FROM CodeSet WHERE SourceSystem = 'http://snomed.info/sct']);
    }

    @IsTest
    static void rejectsConditionWithoutCode() {
        Account patient = new Account(Name = 'FHIR Test Patient 3');
        insert patient;
        try {
            FhirConditionNormalizer.ingest('{"resourceType":"Condition"}', patient.Id);
            System.assert(false, 'expected an exception');
        } catch (FhirConditionNormalizer.FhirMappingException e) {
            System.assert(e.getMessage().contains('required'));
        }
    }
}
