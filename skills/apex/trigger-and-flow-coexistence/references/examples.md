# Examples — Trigger And Flow Coexistence

## Example 1: Silent Field Overwrite Between Before Trigger and Before-Save Flow

**Context:** A financial services org has a before-insert trigger on Opportunity that sets `Risk_Rating__c` based on Amount and Account industry. Six months later, an admin creates a before-save Flow on Opportunity that also sets `Risk_Rating__c` using a different formula that includes the opportunity's product family.

**Problem:** After the Flow is activated, the admin's new `Risk_Rating__c` values never appear -- the trigger's value is saved on every record. No error is thrown, and debug logs show the Flow executing successfully, which sends the admin looking for a Flow bug that does not exist. The Flow runs at step 3; the trigger runs at step 4 and unconditionally overwrites the field one step later.

**Solution:**

```text
Automation Inventory — Opportunity (Before-Save timing)

| Automation          | Type              | Fields Written    |
|---------------------|-------------------|-------------------|
| OpportunityTrigger  | Before Trigger    | Risk_Rating__c    |
| Set Risk Rating     | Before-Save Flow  | Risk_Rating__c    |

CONFLICT: Risk_Rating__c is written by the Flow at step 3 and by the trigger
at step 4. The trigger runs later, so the trigger's value always wins.

Resolution: Remove the Risk_Rating__c assignment from the before trigger.
Consolidate all Risk_Rating__c logic into the before-save Flow, which the
admin team can maintain without deployments. Update the trigger handler to
skip Risk_Rating__c and document the ownership in the automation inventory.
```

**Why it works:** The conflict is resolved by assigning a single owner to the field. Removing the *trigger's* write is what actually changes the outcome, because the trigger is the later writer (step 4) -- had the team instead added a condition to the Flow, nothing would have changed. The choice of Flow over trigger as the surviving owner is a governance decision based on who maintains the logic. The critical step was building the inventory that revealed the collision, since the platform reports nothing.

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

## Anti-Pattern: Believing Deployment Order Controls Execution Sequence

**What practitioners do:** A developer deploys the trigger first and the Flow second, assuming the trigger will run before the Flow at before-save timing because it was "registered first."

**What goes wrong:** Deployment order, creation date, and alphabetical order have no bearing on this. The platform fixes the sequence by step number: before-save Flows at step 3, before triggers at step 4. The developer's assumption happens to land on the right answer for the wrong reason -- the trigger does run second, but the Flow-then-trigger order would be identical if the Flow had been deployed first. Reasoning that produces a right answer by accident produces a wrong one as soon as the situation shifts.

**Correct approach:** Read the ordering off the documented step list, not off deployment history. The Flow runs first, the trigger runs second, always. Then ensure the two write disjoint fields or consolidate into one automation. If they must both write a field, put the guard in the **trigger** -- the later writer -- so it checks the current value and defers when the Flow has already set it.

Note also what deployment order *does* control, so the correction is not over-applied: nothing here. The one ordering that *is* configurable is among multiple record-triggered Flows of the same type on the same object, via the Flow `triggerOrder` field (Metadata API 54.0+, surfaced as Flow Trigger Explorer).
