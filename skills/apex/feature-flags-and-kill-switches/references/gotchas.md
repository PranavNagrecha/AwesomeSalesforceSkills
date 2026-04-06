# Gotchas — Feature Flags And Kill Switches

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CMDT Records Cannot Be Created or Modified via DML

**What happens:** Attempting `insert new FeatureFlag__mdt(DeveloperName='Test', IsEnabled__c=true)` or updating a CMDT record in Apex throws a `TypeException` or `DmlException`. Unlike Custom Objects and Custom Settings, Custom Metadata Types are metadata, not data. The only way to modify them programmatically is through the Metadata API (e.g., `Metadata.DeployContainer` and `Metadata.Operations.enqueueDeployment()`), which is asynchronous and requires a callback.

**When it occurs:** Developers who are used to Custom Settings try the same DML pattern with CMDT. This also bites teams who want a scheduled job to auto-disable a flag at a specific time — you cannot do `update flagRecord;` in a scheduled class.

**How to avoid:** If you need DML-based instant toggling (e.g., from a scheduled job or trigger), use a Hierarchical Custom Setting instead of CMDT. If you must use CMDT, use `Metadata.Operations.enqueueDeployment()` with a `DeployCallback` — but be aware this is asynchronous and the change is not immediate within the same transaction.

---

## Gotcha 2: getInstance() Returns Null for Missing Records — Not an Exception

**What happens:** `FeatureFlag__mdt.getInstance('Nonexistent_Record')` returns `null`. If the calling code does `FeatureFlag__mdt.getInstance('ERP_Sync').IsEnabled__c` without a null check, it throws a `System.NullPointerException` in production. This is especially dangerous after sandbox refreshes or partial deployments where CMDT records may not exist.

**When it occurs:** Any time the DeveloperName string is misspelled, the record was not included in a deployment, or a sandbox was refreshed from an older snapshot that predates the record. Also hits during unit tests where CMDT records from the org are visible but test-specific records are not.

**How to avoid:** Always wrap in a null-safe pattern: `FeatureFlag__mdt flag = FeatureFlag__mdt.getInstance(name); return flag != null && flag.IsEnabled__c;`. Default to `false` (feature off) when the record is missing — this is the safe direction for a kill switch. Never default to `true` on null, as that would enable a feature that was supposed to be gated.

---

## Gotcha 3: Custom Setting Data Values Do Not Deploy Across Environments

**What happens:** You define a Hierarchical Custom Setting `MyFlags__c` with a checkbox `EnableSync__c` and set the org default to `true` in your dev sandbox. You deploy the setting definition to UAT via a change set. The field definition arrives, but the org-default value is blank/false because Custom Setting **values** are data rows, not metadata. The feature appears disabled in UAT even though it works in dev.

**When it occurs:** Every environment migration — sandbox refresh, change set deployment, metadata API deployment, scratch org creation. Only the setting definition (object + fields) deploys. The data rows (org default, profile overrides, user overrides) do not.

**How to avoid:** Script Custom Setting data population in your CI/CD pipeline or use a post-deployment script. For example, include a post-install Apex script that sets `MyFlags__c orgDefault = MyFlags__c.getOrgDefaults(); orgDefault.EnableSync__c = true; upsert orgDefault;`. Alternatively, use CMDT for flags that must be consistent across environments — CMDT records are metadata and deploy.

---

## Gotcha 4: Custom Permissions Are Not Queryable in SOQL

**What happens:** A developer tries `SELECT Id FROM CustomPermission WHERE DeveloperName = 'BetaFeature'` or attempts to query which users have a Custom Permission via SOQL. While the `CustomPermission` and `SetupEntityAccess` objects exist, the check in Apex is done via `FeatureManagement.checkPermission()`, and there is no direct way to query "give me all users who have this Custom Permission" without joining through `PermissionSetAssignment` and `SetupEntityAccess`.

**When it occurs:** When building admin dashboards or reports that need to show which users have a feature enabled via Custom Permission.

**How to avoid:** To list users with a Custom Permission, query: `SELECT AssigneeId FROM PermissionSetAssignment WHERE PermissionSetId IN (SELECT ParentId FROM SetupEntityAccess WHERE SetupEntityType = 'CustomPermission' AND SetupEntityId IN (SELECT Id FROM CustomPermission WHERE DeveloperName = 'BetaFeature'))`. This is a multi-level subquery but works. For runtime checks in Apex, always use `FeatureManagement.checkPermission()` — never try to replicate the logic manually.

---

## Gotcha 5: CMDT Changes in Tests — Records Are Visible but Not Insertable

**What happens:** In `@IsTest` methods, CMDT records from the org are visible (unlike Custom Object data, which is isolated by default). However, you cannot insert new CMDT records for test purposes because DML is not supported on CMDT. This makes it hard to test the "flag disabled" path if the org always has the flag set to `true`.

**When it occurs:** Writing unit tests that need to verify both the enabled and disabled code paths. The test can see the production CMDT record but cannot change it.

**How to avoid:** Use a testable wrapper pattern. Instead of calling `FeatureFlag__mdt.getInstance()` directly in business logic, route through a utility class with a `@TestVisible` static override:

```apex
public class FeatureFlags {
    @TestVisible
    private static Map<String, Boolean> testOverrides = new Map<String, Boolean>();

    public static Boolean isEnabled(String featureName) {
        if (Test.isRunningTest() && testOverrides.containsKey(featureName)) {
            return testOverrides.get(featureName);
        }
        FeatureFlag__mdt flag = FeatureFlag__mdt.getInstance(featureName);
        return flag != null && flag.IsEnabled__c;
    }
}
```

In tests: `FeatureFlags.testOverrides.put('ERP_Sync', false);` to test the disabled path.
