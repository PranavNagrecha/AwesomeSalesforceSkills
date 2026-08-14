# Examples — Flow Orchestration Admin

## Example 1: Making Orchestrations Visible to a Flow Inventory

**Scenario:** A release checklist counts active flows and flags any that changed since the last deploy. Orchestrations were added last quarter. The checklist has never once mentioned one.

**Problem:** Orchestrations are not `AutoLaunchedFlow`. Metadata API gives them their own process type — `Orchestrator`, "An orchestration that organizes flows into groups of steps contained in a series of stages" (API 53.0+) — with a second type, `ApprovalWorkflow`, "An orchestration that's used for an approval process" (API 63.0+). Any filter written as an allow-list of the older types excludes both.

**Solution:** The discriminating line is in the flow metadata itself. Retrieving an orchestration gives a `Flow` component whose `processType` is what tells the tooling what it is:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <label>Vendor Onboarding Orchestration</label>
    <!-- THIS is the line inventories miss. Not AutoLaunchedFlow. -->
    <processType>Orchestrator</processType>
    <status>Active</status>
    <!-- stage and step nodes omitted -->
</Flow>
```

Retrieve them with the ordinary `Flow` metadata type and filter on process type downstream, rather than trying to name orchestrations in `package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>Flow</name>
    </types>
    <version>63.0</version>
</Package>
```

**Why it works:** Orchestrations ship inside the `Flow` metadata type, so nothing special is needed to retrieve them — the gap is entirely in how downstream tooling classifies what came back. Enumerate `Orchestrator` and `ApprovalWorkflow` explicitly in every inventory, report, and regression-scope rule.

---

## Example 2: Reading In-Flight Orchestration State from Apex

**Scenario:** A record page should show whether the record has an orchestration running against it, so a case owner does not open a duplicate request.

**Problem:** The three `ConnectApi.Orchestration` methods arrived in three different API versions, and the controlling value is the `apiVersion` in the class's own `.cls-meta.xml`. Writing against the newest overload in an old utility class fails to compile with no hint that a version is the cause.

**Solution:**

```apex
public with sharing class OrchestrationStatusController {

    @AuraEnabled(cacheable=true)
    public static ConnectApi.OrchestrationInstanceCollection
            getRunningOrchestrations(Id recordId) {
        // getOrchestrationInstanceCollection(String relatedRecordId) -- API 54.0.
        // Safe on any class pinned to 54.0 or later. The documented return
        // type is ConnectApi.OrchestrationInstanceCollection; the single-id
        // lookup ConnectApi.Orchestration.getOrchestrationInstance(instanceId)
        // returns ConnectApi.OrchestrationInstance and needs 63.0.
        return ConnectApi.Orchestration.getOrchestrationInstanceCollection(recordId);
    }
}
```

Hand the collection straight to the component rather than unpacking it in Apex. Before reading any property off `ConnectApi.OrchestrationInstanceCollection` or `ConnectApi.OrchestrationInstance`, copy the property names from the ConnectApi output-class reference for the API version the class is pinned to — a plausible-looking property name on a ConnectApi output class fails at compile time, and the failure reads as an orchestration problem rather than a typo.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- The gate. 54.0 is the floor for the single-argument overload;
         the two-argument form needs 66.0 and getOrchestrationInstance
         needs 63.0. Raise this deliberately, never silently. -->
    <apiVersion>63.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

**Why it works:** The single-argument overload is the oldest and therefore the most portable, so a component meant to be copied between orgs should prefer it. If the two-argument form is genuinely needed, raise `apiVersion` to 66.0 and honour its rule — "You must specify either relatedRecordId or relatedOrchestrationId" — because passing neither fails at run time, not at deploy time.

---

## Anti-Pattern: Hardening the Apex a Background Step Calls with the Removed Clause

**What practitioners do:** An invocable behind a Background Step needs to read records the step will act on. A security review asks for enforcement, and the fix applied is the idiom everyone learned in 2023:

```apex
// WRONG on any class pinned to API 67.0 or later.
public with sharing class VendorLookupAction {
    @InvocableMethod(label='Load Vendor Contacts')
    public static List<List<Contact>> run(List<Id> accountIds) {
        return new List<List<Contact>>{
            [SELECT Id, Email FROM Contact
             WHERE AccountId IN :accountIds
             WITH SECURITY_ENFORCED]
        };
    }
}
```

**What goes wrong:** `WITH SECURITY_ENFORCED` was removed in API 67.0. The deploy fails outright with `WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`, and because the failure is in a class three layers below the orchestration, it gets reported as an orchestration deployment problem.

**Correct approach:**

```apex
public with sharing class VendorLookupAction {
    @InvocableMethod(label='Load Vendor Contacts')
    public static List<List<Contact>> run(List<Id> accountIds) {
        // WITH USER_MODE is the read idiom from API 57.0 upward, and from
        // 67.0 user mode is the default -- the clause states the intent.
        return new List<List<Contact>>{
            [SELECT Id, Email FROM Contact
             WHERE AccountId IN :accountIds
             WITH USER_MODE]
        };
    }
}
```

For a step that writes records assembled from step inputs, decide deliberately between letting user mode throw — which stalls the orchestration instance — and stripping inaccessible fields so the step completes:

```apex
SObjectAccessDecision decision =
    Security.stripInaccessible(AccessType.CREATABLE, newRecords);
insert decision.getRecords();   // DML on the original list is unenforced
```

The trade-off is whether a silent partial save is acceptable for this step. For an orchestration it usually is not — a half-written record advancing the stage is worse than a visible stall — so user mode's throw is often the right default here. Cite the version table in `agents/_shared/AGENT_CONTRACT.md` § "Apex security idiom by API version" when recording the decision.
