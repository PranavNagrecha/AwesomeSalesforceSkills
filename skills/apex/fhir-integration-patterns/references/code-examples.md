# Code Examples: FHIR Integration Patterns

Deployable Apex, tests, and manifest for the FHIR normalization pattern in `SKILL.md`. Narrative and API examples are in `examples.md`.

## Example 1: Normalize a FHIR R4 Condition into HealthCondition, CodeSetBundle, and CodeSet (Apex)

**Context:** A middleware flow delivers FHIR R4 Condition resources and the patient's Account Id to an Apex service. The EHR sends SNOMED and ICD-10 codings and sometimes many local codes.

**Rules applied (Health Cloud developer guide 262, "Mapping FHIR v4.0 to Salesforce Standard Objects"):** Coding maps to CodeSet (`SourceSystem`, `SystemVersion`, `Code`, `Name`, `IsPrimary`); CodeableConcept maps to CodeSetBundle with `CodeSet1Id` to `CodeSet15Id` and `Name` for `text`; Condition maps to HealthCondition with `ConditionCodeId` required and `PatientId` as the master-detail to Account; `onsetPeriod` flattens to `OnsetStartDateTime` and `OnsetEndDateTime`.

`force-app/main/default/classes/FhirConditionNormalizer.cls`

```apex
public with sharing class FhirConditionNormalizer {

    public class FhirMappingException extends Exception {}

    public class Result {
        public Id healthConditionId;
        public Id codeSetBundleId;
        public Integer droppedCodings = 0;
    }

    public static final Integer MAX_CODINGS = 15; // CodeSetBundle.CodeSet1Id .. CodeSet15Id

    public static Result ingest(String conditionJson, Id patientAccountId) {
        Map<String, Object> condition = (Map<String, Object>) JSON.deserializeUntyped(conditionJson);
        if ((String) condition.get('resourceType') != 'Condition') {
            throw new FhirMappingException('Expected a FHIR Condition resource');
        }
        Map<String, Object> code = (Map<String, Object>) condition.get('code');
        if (code == null) {
            // HealthCondition.ConditionCodeId is 1..1 in Salesforce even though FHIR allows 0..1.
            throw new FhirMappingException('Condition.code is required for HealthCondition');
        }
        List<Object> codings = code.get('coding') == null ? new List<Object>() : (List<Object>) code.get('coding');

        Result result = new Result();
        List<Map<String, Object>> kept = new List<Map<String, Object>>();
        for (Object o : codings) {
            if (kept.size() == MAX_CODINGS) {
                result.droppedCodings++;
                continue;
            }
            kept.add((Map<String, Object>) o);
        }

        Map<String, Id> codeSetIdByKey = upsertCodeSets(kept);

        String bundleName = (String) code.get('text');
        if (String.isBlank(bundleName) && !kept.isEmpty()) {
            bundleName = (String) (kept[0].get('display') != null ? kept[0].get('display') : kept[0].get('code'));
        }
        CodeSetBundle bundle = new CodeSetBundle(Name = bundleName);
        for (Integer i = 0; i < kept.size(); i++) {
            bundle.put('CodeSet' + (i + 1) + 'Id', codeSetIdByKey.get(key(kept[i])));
        }
        insert bundle;
        result.codeSetBundleId = bundle.Id;

        HealthCondition hc = new HealthCondition(PatientId = patientAccountId, ConditionCodeId = bundle.Id);
        if (condition.get('onsetDateTime') != null) {
            hc.OnsetStartDateTime = toDatetime((String) condition.get('onsetDateTime'));
        } else if (condition.get('onsetPeriod') != null) {
            Map<String, Object> period = (Map<String, Object>) condition.get('onsetPeriod');
            hc.OnsetStartDateTime = toDatetime((String) period.get('start'));
            hc.OnsetEndDateTime = toDatetime((String) period.get('end'));
        }
        // onsetAge, onsetRange, and onsetString have no Salesforce field; they are not mapped.
        insert hc;
        result.healthConditionId = hc.Id;
        return result;
    }

    private static Map<String, Id> upsertCodeSets(List<Map<String, Object>> codings) {
        Set<String> codes = new Set<String>();
        for (Map<String, Object> c : codings) {
            codes.add((String) c.get('code'));
        }
        Map<String, Id> idByKey = new Map<String, Id>();
        for (CodeSet existing : [SELECT Id, Code, SourceSystem FROM CodeSet WHERE Code IN :codes WITH USER_MODE]) {
            idByKey.put(existing.SourceSystem + '|' + existing.Code, existing.Id);
        }
        List<CodeSet> toInsert = new List<CodeSet>();
        for (Map<String, Object> c : codings) {
            if (!idByKey.containsKey(key(c))) {
                String display = (String) c.get('display');
                toInsert.add(new CodeSet(
                    Code = (String) c.get('code'),
                    SourceSystem = (String) c.get('system'),
                    SystemVersion = (String) c.get('version'),
                    Name = String.isBlank(display) ? (String) c.get('code') : display,
                    IsPrimary = c.get('userSelected') == true
                ));
            }
        }
        insert toInsert;
        for (CodeSet cs : toInsert) {
            idByKey.put(cs.SourceSystem + '|' + cs.Code, cs.Id);
        }
        return idByKey;
    }

    private static String key(Map<String, Object> coding) {
        return (String) coding.get('system') + '|' + (String) coding.get('code');
    }

    private static Datetime toDatetime(String value) {
        if (String.isBlank(value)) {
            return null;
        }
        if (value.length() == 10) {
            return Datetime.newInstanceGmt(Date.valueOf(value), Time.newInstance(0, 0, 0, 0));
        }
        return (Datetime) JSON.deserialize('"' + value + '"', Datetime.class);
    }
}
```

`force-app/main/default/classes/FhirConditionNormalizerTest.cls`

```apex
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
```

package.xml members: `FhirConditionNormalizer`, `FhirConditionNormalizerTest` under `<name>ApexClass</name>`; each class needs a `-meta.xml` with `<apiVersion>67.0</apiVersion>`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>FhirConditionNormalizer</members>
        <members>FhirConditionNormalizerTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

**Prerequisites and limits:** compiles only in an org where the FHIR-Aligned Clinical Data Model org preference is enabled (HealthCondition needs it) and the running user can create CodeSet, CodeSetBundle, and HealthCondition. UNVERIFIED (2026-10-03): other required fields on CodeSet, CodeSetBundle, or HealthCondition in your org, whether `PatientId` must reference a Person Account, and picklist API values for `ConditionStatus` (not set here). Codes are not validated by Salesforce, so validate them upstream.

**Why it works:** Each rule in the class traces to a row in the Health Cloud mapping tables, the 15-coding limit is enforced and reported rather than silently applied, and CodeSet records are reused by system and code.
