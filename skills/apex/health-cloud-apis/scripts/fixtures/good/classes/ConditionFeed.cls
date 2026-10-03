public with sharing class ConditionFeed {
    private static final String BASE = 'callout:Healthcare_API/clinical-summary/fhir-r4/v1';
    private static final Integer BUNDLE_MAX_ENTRIES = 30;

    public static Map<Integer, String> classify(List<Integer> entryStatuses) {
        Map<Integer, String> result = new Map<Integer, String>();
        for (Integer i = 0; i < entryStatuses.size(); i++) {
            Integer status = entryStatuses[i];
            if (status == 424) {
                result.put(i, 'DEPENDENT_CANCELLED');
            } else if (status >= 400) {
                result.put(i, 'ROOT_FAILURE');
            } else {
                result.put(i, 'OK');
            }
        }
        return result;
    }
}
