# LLM Anti-Patterns — NPSP Trigger Framework Extension (TDTM)

Common mistakes AI coding assistants make when generating or advising on NPSP TDTM custom handlers. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Issuing Direct DML Inside run() Instead of Returning DmlWrapper

**What the LLM generates:**

```apex
public override npsp.TDTM_Runnable.DmlWrapper run(
    List<SObject> newlist, List<SObject> oldlist,
    npsp.TDTM_Runnable.Action triggerAction,
    Schema.DescribeSObjectResult objResult
) {
    List<Related_Record__c> toInsert = new List<Related_Record__c>();
    for (SObject rec : newlist) {
        toInsert.add(new Related_Record__c(Parent__c = rec.Id));
    }
    insert toInsert; // WRONG — direct DML
    return null;
}
```

**Why it happens:** LLMs are trained on standard Apex trigger handler patterns where direct DML is normal. The TDTM DmlWrapper contract is NPSP-specific and rarely appears in general Apex training data.

**Correct pattern:**

```apex
public override npsp.TDTM_Runnable.DmlWrapper run(
    List<SObject> newlist, List<SObject> oldlist,
    npsp.TDTM_Runnable.Action triggerAction,
    Schema.DescribeSObjectResult objResult
) {
    npsp.TDTM_Runnable.DmlWrapper wrapper = new npsp.TDTM_Runnable.DmlWrapper();
    for (SObject rec : newlist) {
        wrapper.objectsToInsert.add(new Related_Record__c(Parent__c = rec.Id));
    }
    return wrapper;
}
```

**Detection hint:** Search generated code for `insert `, `update `, or `delete ` statements inside a method whose class extends `npsp.TDTM_Runnable`. Any direct DML statement inside `run()` is the anti-pattern.

---

## Anti-Pattern 2: Omitting npsp__Owned_by_Namespace__c on the Handler Registration Record

**What the LLM generates:**

```apex
npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    Name = 'MyHandler',
    npsp__Class__c = 'MyHandler',
    npsp__Object__c = 'Contact',
    npsp__Trigger_Action__c = 'AfterInsert',
    npsp__Load_Order__c = 10,
    npsp__Active__c = true
    // npsp__Owned_by_Namespace__c is absent
);
```

**Why it happens:** LLMs copy NPSP documentation examples that show only the minimum required fields. The `npsp__Owned_by_Namespace__c` field is a non-obvious protective field that is easy to omit when focusing only on functional requirements.

**Correct pattern:**

```apex
npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    Name = 'MyHandler',
    npsp__Class__c = 'MyHandler',
    npsp__Object__c = 'Contact',
    npsp__Trigger_Action__c = 'AfterInsert',
    npsp__Load_Order__c = 100,
    npsp__Active__c = true,
    npsp__Owned_by_Namespace__c = 'myorg' // protects from NPSP upgrade deletion
);
```

**Detection hint:** Check any generated `npsp__Trigger_Handler__c` record for the presence of `npsp__Owned_by_Namespace__c`. If absent, flag it. Also check that the value is not `npsp` — setting it to `npsp` has the same effect as omitting it.

---

## Anti-Pattern 3: Calling getTdtmConfig() Before setTdtmConfig() in Tests

**What the LLM generates:**

```apex
@testSetup
static void setupHandlers() {
    List<npsp__Trigger_Handler__c> handlers = npsp.TDTM_Global_API.getTdtmConfig(); // WRONG
    handlers.add(new npsp__Trigger_Handler__c(
        npsp__Class__c = 'MyHandler',
        npsp__Object__c = 'Contact',
        npsp__Trigger_Action__c = 'AfterInsert',
        npsp__Load_Order__c = 100,
        npsp__Active__c = true
    ));
    npsp.TDTM_Global_API.setTdtmConfig(handlers);
}
```

**Why it happens:** LLMs infer from "get then set" patterns common in configuration APIs that you should retrieve the existing list before modifying it. The static cache bug is an NPSP implementation detail not documented in general resources.

**Correct pattern:**

```apex
@testSetup
static void setupHandlers() {
    // Build the list from scratch — do NOT call getTdtmConfig() first
    List<npsp__Trigger_Handler__c> handlers = new List<npsp__Trigger_Handler__c>{
        new npsp__Trigger_Handler__c(
            npsp__Class__c = 'MyHandler',
            npsp__Object__c = 'Contact',
            npsp__Trigger_Action__c = 'AfterInsert',
            npsp__Load_Order__c = 100,
            npsp__Active__c = true
        )
    };
    npsp.TDTM_Global_API.setTdtmConfig(handlers);
}
```

**Detection hint:** Search test class code for `getTdtmConfig()` followed by `setTdtmConfig()` within the same method or setup block. This sequence is always wrong.

---

## Anti-Pattern 4: Adding the npsp. Namespace Prefix to the Class Name in npsp__Class__c

**What the LLM generates:**

```apex
npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    npsp__Class__c = 'npsp.MyCustomHandler', // WRONG — namespace prefix included
    ...
);
```

**Why it happens:** LLMs see the `npsp.TDTM_Runnable` reference in the class definition and assume the handler's own class name needs the `npsp.` prefix when registered. In a subscriber org context, `MyCustomHandler` is in the default namespace (no prefix) even though it extends an `npsp`-namespaced class.

**Correct pattern:**

```apex
npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    npsp__Class__c = 'MyCustomHandler', // just the class name, no namespace prefix
    ...
);
```

If the handler class itself is in a managed package namespace (e.g. `myns`), then the value should be `myns.MyCustomHandler` — not `npsp.MyCustomHandler`.

**Detection hint:** Check `npsp__Class__c` values for `npsp.` as a prefix. If present and the class is a custom class (not a packaged NPSP class), the prefix is wrong.

---

## Anti-Pattern 5: Using a Load Order That Collides With Packaged NPSP Handlers

**What the LLM generates:**

```apex
npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    npsp__Load_Order__c = 1, // WRONG — likely collides with NPSP packaged handlers
    ...
);
```

**Why it happens:** LLMs use low numbers like 1, 2, or 10 as defaults without awareness that NPSP packaged handlers occupy the 1–50 range on common objects. The collision causes undefined execution order relative to packaged logic.

**Correct pattern:**

```apex
// Query existing handlers first to find safe load order
// SELECT MAX(npsp__Load_Order__c) FROM npsp__Trigger_Handler__c
//   WHERE npsp__Object__c = 'Opportunity'
// Start at 100 for the first custom handler, increment by 10 for each additional one

npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    npsp__Load_Order__c = 100, // well above packaged handler range
    ...
);
```

**Detection hint:** Check generated `npsp__Load_Order__c` values. Any value below 100 on a standard NPSP-managed object (Account, Contact, Opportunity, npe01__OppPayment__c, etc.) should be flagged as potentially conflicting with packaged handlers.

---

## Anti-Pattern 6: Returning null Instead of an Empty DmlWrapper

**What the LLM generates:**

```apex
public override npsp.TDTM_Runnable.DmlWrapper run(...) {
    if (triggerAction != npsp.TDTM_Runnable.Action.AfterInsert) {
        return null; // WRONG
    }
    // ... handler logic
}
```

**Why it happens:** LLMs pattern-match to methods that return null as a "no-op" shortcut. In TDTM, the dispatcher expects a non-null `DmlWrapper` from every handler. Returning null causes a NullPointerException in the dispatcher when it tries to merge wrapper results.

**Correct pattern:**

```apex
public override npsp.TDTM_Runnable.DmlWrapper run(...) {
    npsp.TDTM_Runnable.DmlWrapper wrapper = new npsp.TDTM_Runnable.DmlWrapper();
    if (triggerAction != npsp.TDTM_Runnable.Action.AfterInsert) {
        return wrapper; // return empty wrapper, never null
    }
    // ... handler logic
    return wrapper;
}
```

**Detection hint:** Search for `return null;` inside any method body within a class that extends `npsp.TDTM_Runnable`. Every return path must return a `DmlWrapper` instance.
