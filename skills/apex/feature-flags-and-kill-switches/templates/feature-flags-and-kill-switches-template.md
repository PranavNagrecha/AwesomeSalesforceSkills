# Feature Flags And Kill Switches — Work Template

Use this template when implementing feature flags or kill switches in a Salesforce org.

## Scope

**Skill:** `feature-flags-and-kill-switches`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Toggle scope:** (org-wide / profile-level / user-level)
- **Mechanism selected:** (CMDT / Custom Permission / Hierarchical Custom Setting)
- **Reason for selection:** (reference Decision Guidance table in SKILL.md)
- **Flag lifecycle:** (permanent kill switch / temporary rollout gate — expected removal date: ___)
- **Environments affected:** (production, sandboxes, scratch orgs)
- **Deployment constraints:** (change set / metadata API / CI/CD pipeline)

## Feature Flag Inventory

| Flag Name (DeveloperName) | Mechanism | Scope | Purpose | Owner | Removal Date |
|---|---|---|---|---|---|
| | | | | | |

## Implementation Checklist

### Metadata Setup

- [ ] CMDT object `FeatureFlag__mdt` exists with `IsEnabled__c` (checkbox) and `Description__c` (text)
- [ ] OR Custom Permission created with DeveloperName: ___
- [ ] OR Hierarchical Custom Setting created with boolean field: ___
- [ ] CMDT record(s) created for each feature flag
- [ ] Permission Set created for Custom Permission (if applicable)

### Apex Implementation

- [ ] Centralized `FeatureFlags` utility class created or updated
- [ ] Null-safe pattern used: `flag != null && flag.IsEnabled__c`
- [ ] `@TestVisible` test override map included in utility class
- [ ] All flag checks route through utility class — no raw `getInstance()` in business logic
- [ ] Kill switch "off" path fully implemented (no partial execution or NPEs)

### Testing

- [ ] Unit test covers "flag enabled" path
- [ ] Unit test covers "flag disabled" path using `testOverrides`
- [ ] Unit test covers "flag record missing" (null) path
- [ ] All tests pass with `--test-level RunLocalTests`

### Deployment

- [ ] CMDT records included in deployment package or change set
- [ ] Custom Setting data values scripted for target environment (if using Custom Settings)
- [ ] Post-deployment verification: flag check returns expected value in target org

## Apex Utility Class Skeleton

```apex
public class FeatureFlags {

    @TestVisible
    private static Map<String, Boolean> testOverrides = new Map<String, Boolean>();

    /**
     * Check an org-wide feature flag stored in FeatureFlag__mdt.
     * Returns false if the record does not exist (safe default).
     */
    public static Boolean isEnabled(String featureName) {
        if (Test.isRunningTest() && testOverrides.containsKey(featureName)) {
            return testOverrides.get(featureName);
        }
        FeatureFlag__mdt flag = FeatureFlag__mdt.getInstance(featureName);
        return flag != null && flag.IsEnabled__c;
    }

    /**
     * Check a user-scoped feature flag via Custom Permission.
     * Returns true only if the running user has the permission assigned.
     */
    public static Boolean isPermitted(String permissionName) {
        return FeatureManagement.checkPermission(permissionName);
    }
}
```

## Test Class Skeleton

```apex
@IsTest
private class FeatureFlags_Test {

    @IsTest
    static void testFlagEnabled() {
        FeatureFlags.testOverrides.put('My_Feature', true);

        Test.startTest();
        Boolean result = FeatureFlags.isEnabled('My_Feature');
        Test.stopTest();

        System.assert(result, 'Expected feature to be enabled');
    }

    @IsTest
    static void testFlagDisabled() {
        FeatureFlags.testOverrides.put('My_Feature', false);

        Test.startTest();
        Boolean result = FeatureFlags.isEnabled('My_Feature');
        Test.stopTest();

        System.assert(!result, 'Expected feature to be disabled');
    }

    @IsTest
    static void testFlagMissing() {
        // No override set and no CMDT record — should default to false
        Test.startTest();
        Boolean result = FeatureFlags.isEnabled('Nonexistent_Flag');
        Test.stopTest();

        System.assert(!result, 'Expected missing flag to default to disabled');
    }
}
```

## Notes

Record any deviations from the standard pattern and why:

-
