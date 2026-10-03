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
