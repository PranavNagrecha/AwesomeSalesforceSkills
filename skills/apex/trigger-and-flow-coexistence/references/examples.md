# Examples — Trigger And Flow Coexistence

## Example 1: Silent Field Overwrite Between Before Trigger and Before-Save Flow

**Context:** A financial services org has a before-insert trigger on Opportunity that sets `Risk_Rating__c` based on Amount and Account industry. Six months later, an admin creates a before-save Flow on Opportunity that also sets `Risk_Rating__c` using a different formula that includes the opportunity's product family.

**Problem:** After the Flow is activated, some Opportunities have incorrect `Risk_Rating__c` values. The bug is intermittent -- sometimes the trigger's value wins, sometimes the Flow's value wins. No error is thrown. Debug logs show both automations executing but the final field value depends on which ran second.

**Solution:**

```text
Automation Inventory — Opportunity (Before-Save timing)

| Automation          | Type              | Fields Written    |
|---------------------|-------------------|-------------------|
| OpportunityTrigger  | Before Trigger    | Risk_Rating__c    |
| Set Risk Rating     | Before-Save Flow  | Risk_Rating__c    |

CONFLICT: Risk_Rating__c is written by two automations at Before-Save timing.

Resolution: Remove the Risk_Rating__c assignment from the before trigger.
Consolidate all Risk_Rating__c logic into the before-save Flow, which the
admin team can maintain without deployments. Update the trigger handler to
skip Risk_Rating__c and document the ownership in the automation inventory.
```

**Why it works:** The conflict is resolved by assigning a single owner to the field at the before-save timing. The choice of Flow over trigger is a governance decision based on who maintains the logic. The critical step was building the inventory that revealed the collision.

---

## Example 2: Cross-Automation Recursion Between After Trigger and After-Save Flow

**Context:** A Case object has an after-update trigger that creates a child CaseComment when the Status changes to "Escalated." The same object has an after-save Flow that updates a parent Account field `Open_Escalations__c` by incrementing a counter. The Flow's DML on Account fires an Account after trigger that updates all related Cases with a flag, which re-enters the Case save cycle.

**Problem:** The transaction hits the CPU time limit and fails. Debug logs show the Case after trigger and after-save Flow cycling repeatedly: Case trigger -> Case Flow -> Account trigger -> Case trigger -> Case Flow -> ...

**Solution:**

```apex
public class AutomationControl {
    public static Boolean caseEscalationProcessed = false;

    @InvocableMethod(label='Is Escalation Already Processed')
    public static List<Boolean> isEscalationProcessed(List<String> unused) {
        return new List<Boolean>{ caseEscalationProcessed };
    }
}

// In CaseTriggerHandler.afterUpdate():
if (!AutomationControl.caseEscalationProcessed) {
    AutomationControl.caseEscalationProcessed = true;
    // Create CaseComment and perform escalation logic
}
```

In the after-save Flow, add a Decision element at the top that calls the `Is Escalation Already Processed` Invocable method. If it returns `true`, the Flow skips to the end. This breaks the recursion cycle because the second time through, both the trigger and the Flow see the guard flag and exit.

**Why it works:** The InvocableMethod bridges the static-variable gap between Apex and Flow. A static Boolean alone would guard the trigger but not the Flow. The Invocable call gives the Flow visibility into the Apex transaction state, allowing both automation types to participate in the same guard pattern.

---

## Example 3: Adding a Flow to a Legacy Trigger-Heavy Object

**Context:** A manufacturing org's `Work_Order__c` object has a mature single-trigger handler with 12 methods covering validation, field defaulting, rollups, and integrations. An admin needs to add a simple before-save Flow that sets a `Region__c` field based on the related Site's address.

**Problem:** The admin activates the Flow without consulting the development team. The `Region__c` field was already being set by one of the 12 trigger handler methods using a different region-mapping table. Records now have inconsistent `Region__c` values.

**Solution:**

```text
Step 1: Before activating ANY new automation, run the automation inventory check.
Step 2: Search the trigger handler for references to Region__c.
        Found: WorkOrderTriggerHandler.setRegion() — writes Region__c on before insert/update.
Step 3: Decision — who should own Region__c?
        Admin team prefers Flow for region mapping (no deployment needed for mapping changes).
Step 4: Remove setRegion() call from trigger handler. Deploy to sandbox.
Step 5: Activate before-save Flow in sandbox. Test with 200 Work Orders.
Step 6: Update automation inventory:
        Region__c — owned by Flow "Set Work Order Region" at Before-Save timing.
Step 7: Deploy trigger handler change and activate Flow in production together.
```

**Why it works:** The ownership transfer was coordinated: the trigger handler method was removed before the Flow was activated. The automation inventory was updated to prevent future developers from re-adding the logic to the trigger.

---

## Anti-Pattern: Relying on Deployment Order to Control Execution Sequence

**What practitioners do:** A developer deploys the trigger first and the Flow second, assuming the trigger will always run before the Flow at the before-save timing because it was "registered first."

**What goes wrong:** Salesforce does not use deployment order, creation date, or alphabetical order to determine the relative execution of a before trigger and a before-save Flow. The order is indeterminate and can change across releases, sandboxes, or even between transactions. The assumption silently breaks.

**Correct approach:** Never rely on relative ordering between a trigger and a Flow at the same timing slot. Instead, ensure they write to disjoint fields or consolidate the logic into a single automation. If they must coexist, use a field-value guard: the second automation checks the field value before writing and only writes if the value does not match expectations.
