# LLM Anti-Patterns — Trigger And Flow Coexistence

Common mistakes AI coding assistants make when generating or advising on trigger and Flow coexistence.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming before triggers always run before before-save Flows

**What the LLM generates:** "The before trigger fires first, then the before-save Flow runs, so you can set default values in the trigger and override them in the Flow."

**Why it happens:** Many older blog posts and StackExchange answers state that triggers run before Flows. This was partially true before Spring '22 when before-save Flows were introduced. LLMs trained on this data repeat the claim as fact.

**Correct pattern:**

```text
Before-save Flows and before triggers both execute at step 3 of the order of
execution. Salesforce does not guarantee their relative order. Do not rely on
one running before the other. Assign each field to a single automation owner.
```

**Detection hint:** Look for phrases like "trigger runs first," "trigger fires before the Flow," or "Flow runs after the trigger" when discussing before-save timing.

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

## Anti-Pattern 5: Generating trigger code that validates fields a Flow might overwrite

**What the LLM generates:** "In the before trigger, validate that Priority__c is not blank and add an error if it is. This ensures data quality."

**Why it happens:** LLMs generate trigger validation code without considering that a before-save Flow running after the trigger could set the field to null, bypassing the trigger's check. The LLM does not model the full order of execution.

**Correct pattern:**

```text
Use declarative validation rules for field-level validation. Validation rules
execute at step 4, after both before triggers and before-save Flows complete.
This ensures the validation sees the final field state regardless of which
automation wrote last.
```

**Detection hint:** Field validation logic inside a before trigger's `Trigger.new` loop on an object that also has before-save Flows. Look for `addError()` calls that check field values a Flow might subsequently change.

---

## Anti-Pattern 6: Assuming after-save Flows run before after triggers

**What the LLM generates:** "The after-save Flow runs at step 8, before the after trigger at step 10, so you can use the Flow to set up data that the trigger will process."

**Why it happens:** LLMs hallucinate step numbers or confuse different versions of the order-of-execution documentation. The actual step numbers vary by documentation version, but after-save Flows consistently run after workflow field updates, not before after triggers in the initial pass.

**Correct pattern:**

```text
After-save Flows run at step 15, which is after workflow field updates (step 9)
and after the re-evaluation of triggers caused by those field updates. After
triggers in the initial save cycle run at step 4. Do not assume a specific
relative order without consulting the current order-of-execution documentation.
```

**Detection hint:** Specific step numbers cited without a documentation link, or claims about after-save Flow timing that contradict the Apex Developer Guide's Triggers and Order of Execution page.
