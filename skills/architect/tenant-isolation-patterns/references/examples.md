# Examples — Tenant Isolation Patterns

## Example 1: A durable tenant grant on a custom object, via a named Apex sharing reason

**Context:** A franchise network runs in one org. `Service_Job__c` records belong to a franchise, and the franchise's
regional coordinators — who sit outside the record owner's role branch — need access. OWD on `Service_Job__c` is
Private.

**Problem:** The common implementation inserts a `Service_Job__Share` row and leaves `RowCause` at its default. That
produces a *user managed* share: "Manual shares written using Apex contains `RowCause="Manual"` by default. Only shares
with this condition are removed when ownership changes." The grant works, tests pass, and it vanishes the first time a
job is reassigned — which in a franchise network is routine.

**Solution:** Define an Apex sharing reason on the object and write the share against it. Apex managed sharing "is
maintained when the record owner changes or is deactivated".

```apex
public with sharing class TenantShareService {

    /**
     * Grants the franchise's coordinator group access to newly-created jobs.
     * Called from an after-insert trigger.
     *
     * Prerequisite: an Apex sharing reason named Franchise_Coordinator on
     * Service_Job__c. It is a deployable component — Metadata API type
     * SharingReason, under the custom object — so create it in source, not by
     * clicking, and check your org's Setup path for it before assuming one.
     */
    public static List<Database.SaveResult> grantCoordinatorAccess(List<Service_Job__c> jobs) {
        List<Service_Job__Share> shares = new List<Service_Job__Share>();

        for (Service_Job__c job : jobs) {
            if (job.Coordinator_Group__c == null) {
                continue;
            }
            Service_Job__Share share = new Service_Job__Share();
            share.ParentId        = job.Id;
            share.UserOrGroupId   = job.Coordinator_Group__c;

            // Must be HIGHER than the object's org-wide default, or the insert errors.
            share.AccessLevel     = 'Edit';

            // The named reason is what makes this Apex MANAGED sharing: it survives
            // owner changes, and it can be removed independently of other grants.
            share.RowCause        = Schema.Service_Job__Share.RowCause.Franchise_Coordinator__c;

            shares.add(share);
        }

        // allOrNone = false: one bad row must not discard the whole tenant's grants.
        return Database.insert(shares, false);
    }
}
```

**Why it works:** The named reason turns an ephemeral manual share into a durable, attributable one. It also makes
revocation surgical — deleting shares `WHERE RowCause = 'Franchise_Coordinator__c'` removes exactly this program's
grants and leaves manual shares and other reasons alone, which is what offboarding a franchise requires.

**The constraint to check first:** "Apex sharing reasons and Apex managed sharing recalculation are only available for
custom objects." If the object in your design is `Account` or `Case`, this pattern is unavailable and the isolation has
to come from ownership, criteria-based sharing, and hierarchy placement instead. Also note that "Only users with
'Modify All Data' permission can add or change Apex managed sharing on a record", so the calling context matters as
much as the code.

---

## Example 2: Per-tenant feature gating that fails closed

**Context:** One codebase serves several tenants at different feature tiers. A premium routing engine should run for
some tenants and not others, with no per-tenant code branch.

**Problem:** Feature flags read from a Custom Permission are the right shape, but the naive call is a live grenade in a
multi-tenant org. Since Winter '20, `FeatureManagement.checkPermission` throws `System.NoDataFoundException` when
passed an API name that is not defined in the org — it no longer returns `false`. In a multi-tenant deployment where
tenants are onboarded incrementally, "the permission has not been created yet" is the normal state for a new tenant,
and an unguarded call fatals every transaction that touches the gate.

**Solution:** Resolve the permission once per transaction, catch the missing-permission case, and default to the
restrictive answer.

```apex
public with sharing class TenantFeatureService {

    // Memoised per transaction: the throw happens at most once, not per call.
    private static Map<String, Boolean> resolved = new Map<String, Boolean>();

    public static Boolean isEnabled(String customPermissionApiName) {
        if (resolved.containsKey(customPermissionApiName)) {
            return resolved.get(customPermissionApiName);
        }

        Boolean enabled;
        try {
            enabled = FeatureManagement.checkPermission(customPermissionApiName);
        } catch (Exception e) {
            // Custom Permission is not deployed in this org / for this tenant yet.
            // Fail CLOSED: an unknown flag is an OFF flag, never an ON one.
            System.debug(
                LoggingLevel.WARN,
                'TenantFeatureService: Custom Permission ' + customPermissionApiName
                + ' is not deployed; feature treated as disabled. ' + e.getMessage()
            );
            enabled = false;
        }

        resolved.put(customPermissionApiName, enabled);
        return enabled;
    }
}
```

**Why it works:** The gate is a capability assigned through a Permission Set, so tenant tiering is governed the same
way every other permission is — through Permission Set Groups, with an assignment history — rather than through a
checkbox somebody can edit. Failing closed is the load-bearing decision: in a shared org, an exception that defaults a
premium feature *on* has exposed one tenant's capability to another, whereas defaulting off is a support ticket. The
same try/catch discipline appears in `templates/apex/TriggerControl.cls`; reuse that class rather than reimplementing
the memoisation.

---

## Anti-Pattern: Filtering by tenant in the query and calling it isolation

**What practitioners do:** Stamp `Tenant__c` on every record, declare services `with sharing`, and filter each query by
the running user's tenant.

```apex
public with sharing class JobService {
    public List<Service_Job__c> getJobs() {
        Id tenantId = [SELECT Tenant__c FROM User WHERE Id = :UserInfo.getUserId()].Tenant__c;
        return [SELECT Id, Name, Margin__c, Internal_Notes__c
                FROM Service_Job__c
                WHERE Tenant__c = :tenantId];       // "isolated"
    }
}
```

**What goes wrong:** The filter is application logic, so it holds exactly as long as every future query remembers it —
report builder, list views, the REST API, and a Flow do not. Worse, `with sharing` was never doing the second half of
the job: "Sharing declarations don't enforce object-level access or field-level security." Every
field on the returned record is exposed, including ones the tenant's users are not granted, and serialising the sObject
to a frontend publishes them.

**Correct approach:** Make the platform enforce isolation, and state the access mode explicitly so field-level
isolation is enforced too.

```apex
public with sharing class JobService {
    public List<Service_Job__c> getJobs() {
        // OWD Private + tenant-scoped sharing (criteria-based rules, or Apex managed
        // sharing with a named reason) means the platform filters by access, not the
        // WHERE clause. WITH USER_MODE adds the field-level half that `with sharing`
        // never covered.
        return [SELECT Id, Name, Margin__c, Internal_Notes__c
                FROM Service_Job__c
                WITH USER_MODE];
    }
}
```

Then verify with a two-tenant fixture that includes a user at *every* level of the role hierarchy. Peer-to-peer
isolation is the case that always passes; the case that fails is the manager role somebody placed above two tenant
branches to satisfy a reporting requirement.
