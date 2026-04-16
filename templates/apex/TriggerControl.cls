/**
 * TriggerControl — runtime activation switch for Apex triggers.
 *
 * Reads `Trigger_Setting__mdt` records, keyed by (Object API Name, Handler Class),
 * and respects the `TriggerControl_BypassAll` Custom Permission for break-glass
 * incident response and data-load scenarios.
 *
 * The setting layer is cached in a static Map so repeated calls within a
 * transaction are free.
 */
public with sharing class TriggerControl {

    @TestVisible private static Map<String, Boolean> cache;
    @TestVisible private static Boolean bypassAllOverride;

    public static Boolean isActive(String sObjectName, String handlerName) {
        if (hasBypassAllPermission()) {
            return false;
        }

        String key = (sObjectName + '::' + handlerName).toLowerCase();
        Map<String, Boolean> settings = getCache();
        Boolean active = settings.get(key);
        return active == null ? true : active;
    }

    @TestVisible
    private static Boolean hasBypassAllPermission() {
        if (bypassAllOverride != null) {
            return bypassAllOverride;
        }
        return FeatureManagement.checkPermission('TriggerControl_BypassAll');
    }

    @TestVisible
    private static Map<String, Boolean> getCache() {
        if (cache != null) {
            return cache;
        }
        cache = new Map<String, Boolean>();
        for (Trigger_Setting__mdt setting : [
            SELECT Object_API_Name__c, Handler_Class__c, Is_Active__c
            FROM Trigger_Setting__mdt
            WITH SYSTEM_MODE
        ]) {
            if (setting.Object_API_Name__c == null || setting.Handler_Class__c == null) {
                continue;
            }
            String key = (setting.Object_API_Name__c + '::' + setting.Handler_Class__c).toLowerCase();
            cache.put(key, setting.Is_Active__c);
        }
        return cache;
    }

    @TestVisible
    public static void overrideForTest(String sObjectName, String handlerName, Boolean active) {
        if (cache == null) { cache = new Map<String, Boolean>(); }
        cache.put((sObjectName + '::' + handlerName).toLowerCase(), active);
    }
}
