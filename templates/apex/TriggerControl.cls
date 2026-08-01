/**
 * TriggerControl — runtime activation switch for Apex triggers.
 *
 * Reads `Trigger_Setting__mdt` records, keyed by (Object API Name, Handler Class),
 * and respects the `TriggerControl_BypassAll` Custom Permission for break-glass
 * incident response and data-load scenarios.
 *
 * The setting layer is cached in a static Map so repeated calls within a
 * transaction are free.
 *
 * DEPLOY DEPENDENCIES
 *  - `cmdt/Trigger_Setting__mdt/` — shipped with these templates. Deploy it first
 *    or this class will not compile (the SOQL below references its fields).
 *  - `TriggerControl_BypassAll` Custom Permission — NOT shipped. See
 *    `templates/apex/README.md` for the metadata to create. This class degrades
 *    safely when it is absent (see `hasBypassAllPermission` below).
 */
public with sharing class TriggerControl {

    /**
     * API name of the break-glass Custom Permission. Kept as a constant so a rename
     * is a one-line change rather than a string hunt.
     */
    @TestVisible private static final String BYPASS_ALL_PERMISSION = 'TriggerControl_BypassAll';

    @TestVisible private static Map<String, Boolean> cache;
    @TestVisible private static Boolean bypassAllOverride;
    @TestVisible private static Boolean bypassAllResolved;

    public static Boolean isActive(String sObjectName, String handlerName) {
        if (hasBypassAllPermission()) {
            return false;
        }

        String key = (sObjectName + '::' + handlerName).toLowerCase();
        Map<String, Boolean> settings = getCache();
        Boolean active = settings.get(key);
        return active == null ? true : active;
    }

    /**
     * Resolves the break-glass Custom Permission, failing CLOSED (no bypass, triggers
     * stay on) when the permission does not exist in the org.
     *
     * This try/catch is load-bearing, not defensive padding. Since Winter '20,
     * `FeatureManagement.checkPermission` throws `System.NoDataFoundException` when
     * passed an API name that is not defined in the org — it no longer returns false.
     * (Salesforce Known Issue "FeatureManagement.checkPermission() throwing exception
     * for non-existent apiName's, formerly returned false".) Because `isActive()` is
     * the first thing `TriggerHandler.run()` calls, an unguarded call would fatal
     * EVERY trigger in an org that had not yet created the permission.
     * `NoDataFoundException` is an ordinary catchable Apex exception.
     *
     * The outcome is memoised for the transaction so the throw happens at most once.
     */
    @TestVisible
    private static Boolean hasBypassAllPermission() {
        if (bypassAllOverride != null) {
            return bypassAllOverride;
        }
        if (bypassAllResolved != null) {
            return bypassAllResolved;
        }
        try {
            bypassAllResolved = FeatureManagement.checkPermission(BYPASS_ALL_PERMISSION);
        } catch (Exception e) {
            // Custom Permission not deployed to this org. Fail closed.
            // Do not log via ApplicationLogger here — that would issue DML from a
            // trigger entry point on every transaction until the permission exists.
            System.debug(
                LoggingLevel.WARN,
                'TriggerControl: Custom Permission ' + BYPASS_ALL_PERMISSION
                + ' is not deployed; bypass is unavailable. ' + e.getMessage()
            );
            bypassAllResolved = false;
        }
        return bypassAllResolved;
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
