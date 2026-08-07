# LLM Anti-Patterns — Trigger And Flow Coexistence

Common mistakes AI coding assistants make when generating or advising on trigger and Flow coexistence.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Getting before-save Flow vs. before trigger order wrong (either direction)

Two variants, both wrong, both common:

**Variant A — reversed order.** "The before trigger fires first, then the before-save Flow runs, so you can set default values in the trigger and override them in the Flow."

**Variant B — the indeterminacy claim.** "Before-save Flows and before triggers both run at step 3, and Salesforce doesn't guarantee which goes first, so the outcome is indeterminate — never rely on their relative order."

**Why it happens:** Before-save updates in record-triggered Flows arrived in **Spring '20**; before that, only triggers existed at before-save timing, and a large body of blog and StackExchange content states flatly that "triggers run first." Variant B has a different origin: for a period the Apex Developer Guide's order-of-execution list did not enumerate before-save Flows as their own numbered step, and writers filled the gap by declaring the order unspecified. The current list resolves it explicitly. Models trained on either era repeat the stale claim as fact.

**Correct pattern:**

```text
Step 3: Execute record-triggered flows configured to run BEFORE the record is saved
Step 4: Execute all before triggers

Separate, consecutive, documented steps. The order is DETERMINATE:
  the before-save Flow always runs first; the before trigger always runs second.

If both write the same field, the BEFORE TRIGGER wins -- every transaction,
every org, regardless of deployment order or which was created first.

Fix by field ownership. If both must write, make the TRIGGER conditional
(it is the later writer). Making the FLOW conditional does nothing.
```

**Detection hint:** Flag "trigger runs first," "trigger fires before the Flow," or "Flow runs after the trigger" (Variant A). Flag "indeterminate," "no guaranteed order," "unpredictable," "whichever runs second," or "race" alongside before-save Flow and before trigger (Variant B). Flag any claim that both occupy step 3, any total step count other than 20, and any claim that before-save Flows postdate Spring '20.

---

## Anti-Pattern 2: Using only a static Boolean as a cross-automation recursion guard

**What the LLM generates:** "Add a static Boolean `hasRun` to your trigger handler. Set it to true on the first execution. This prevents recursion from Flows too."

**Why it happens:** Static variable recursion guards are the standard pattern for trigger-to-trigger recursion. LLMs generalize this to all automation types without recognizing that Flows cannot read Apex static variables.

**Correct pattern:**

```apex
// Static variable PLUS InvocableMethod bridge
public class AutomationControl {
    public static Boolean hasProcessed = false;

    @InvocableMethod(label='Check Has Processed')
    public static List<Boolean> checkHasProcessed(List<String> unused) {
        return new List<Boolean>{ hasProcessed };
    }
}
// Flow must call this Invocable in a Decision element to participate in the guard.
```

**Detection hint:** Look for static Boolean guards without an accompanying `@InvocableMethod`. If the org has Flows on the same object, the guard is incomplete.

---

## Anti-Pattern 3: Recommending Process Builder as a coexistence solution

**What the LLM generates:** "Use Process Builder to coordinate between the trigger and the Flow. Process Builder can call an Apex action that sets the static variable before the Flow runs."

**Why it happens:** LLMs trained on pre-2023 content recommend Process Builder as a bridge layer. Process Builder is deprecated and adds a third automation type to an already complex stack.

**Correct pattern:**

```text
Do not introduce Process Builder into a trigger-Flow coexistence scenario. Process
Builder is deprecated (Winter '23 announcement). If coordination is needed, use an
InvocableMethod called from the Flow or consolidate logic into the trigger handler.
```

**Detection hint:** Any mention of "Process Builder" as a solution (rather than a legacy system to migrate away from) in a coexistence context.

---

## Anti-Pattern 4: Suggesting Flow Trigger Explorer shows trigger execution order

**What the LLM generates:** "Open Flow Trigger Explorer in Setup to see the exact order your triggers and Flows will execute."

**Why it happens:** LLMs conflate Flow Trigger Explorer's purpose (ordering multiple Flows) with a broader automation sequencing tool. The name "Trigger Explorer" reinforces the confusion.

**Correct pattern:**

```text
Flow Trigger Explorer shows the execution order of record-triggered Flows only.
It does not display Apex triggers, workflow rules, or Process Builder. To see
trigger-Flow interleaving, enable debug logs and look for CODE_UNIT_STARTED
and FLOW_START_INTERVIEWS events in the execution log.
```

**Detection hint:** Recommendations to use Flow Trigger Explorer to debug trigger-Flow ordering or claims that it shows "all automation" on an object.

---

## Anti-Pattern 5: Generating trigger validation code, then justifying it with a backwards ordering claim

**What the LLM generates:** "In the before trigger, validate that Priority__c is not blank and add an error if it is." Often paired with the reasoning "a before-save Flow could run after the trigger and null the field."

**Why it happens:** LLMs generate trigger validation code without modelling the full order of execution, and then reach for the stale ordering claim to explain the risk. The reasoning is backwards: a before-save Flow runs at step 3, one step **before** the trigger at step 4, so it cannot undo a check the trigger performed. The real exposure is later-step automation -- most commonly a workflow field update at step 11.

**Correct pattern:**

```text
Use declarative validation rules for field-level validation. Custom validation
rules execute at step 5, after the before-save Flow (step 3) and the before
trigger (step 4) have both finished writing. They see the final pre-save state
regardless of which automation wrote it.

An addError() check in a before trigger cannot be undone by a before-save Flow
(the Flow already ran). It CAN be undone by a workflow field update at step 11.
```

**Detection hint:** Field validation logic inside a before trigger's `Trigger.new` loop, especially when the surrounding rationale claims a before-save Flow runs "after" the trigger or could overwrite the validated value.

---

## Anti-Pattern 6: Assuming after-save Flows run before after triggers

**What the LLM generates:** "The after-save Flow runs at step 8, before the after trigger at step 10, so you can use the Flow to set up data that the trigger will process."

**Why it happens:** LLMs mix step numbers drawn from different generations of the order-of-execution page. Several superseded numberings are in circulation (18-step and 19-step variants), so a model can produce internally consistent nonsense.

**Correct pattern:**

```text
After Apex triggers      step 8
Assignment rules         step 9
Auto-response rules      step 10
Workflow rules           step 11   (field updates re-fire before/after
                                    update triggers once, and only once)
Escalation rules         step 12
Process Builder etc.     step 13   (not in a guaranteed order)
After-save Flows         step 14

After triggers run SIX steps before after-save Flows. A record created by an
after trigger IS visible to the after-save Flow; the reverse is not true.
```

**Detection hint:** Any after-save Flow step number other than 14 (15 is the most common stale value; 15 is now entitlement rules), any after-trigger step number other than 8, or any total step count other than 20. Also flag step numbers cited without a documentation link.
