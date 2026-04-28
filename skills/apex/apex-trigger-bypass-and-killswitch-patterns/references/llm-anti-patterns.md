# LLM Anti-Patterns — Apex Trigger Bypass And Killswitch Patterns

Common mistakes AI coding assistants make when generating bypass and kill-switch
code. Use these to self-check your output before returning it.

## Anti-Pattern 1: Hardcoded UserInfo.getUserId() equality check

**What the LLM generates:**

```apex
public override void run() {
    if (UserInfo.getUserId() == '0051x000005ABCDQAW') return; // skip for integration user
    super.run();
}
```

**Why it happens:** LLMs see "skip for integration user" in the prompt and
reach for the most direct expression. The result hardcodes a Production-only
ID, breaks across sandboxes, and is invisible to admins.

**Correct pattern:**

```apex
if (FeatureManagement.checkPermission('Bypass_Triggers')) return;
```

**Detection hint:** regex `UserInfo\.getUserId\(\)\s*==\s*['"]005` — flag
any equality check between `UserInfo.getUserId()` and a literal Id.

---

## Anti-Pattern 2: Bypass checkbox on the User SObject

**What the LLM generates:** A suggestion to "add a custom field
`Bypass_Triggers__c` to the User object and check it in the trigger."

**Why it happens:** LLMs reach for the most discoverable place to put a flag.
User-object fields are easy to query but conflate identity with capability,
allow self-grant, and bypass Permission Set Groups governance.

**Correct pattern:** Custom Permission assigned via Permission Set, gated
through `FeatureManagement.checkPermission('Bypass_Triggers')`.

**Detection hint:** any `User.Bypass_Triggers__c` or `Bypass__c` field
reference on `User` in trigger or handler code.

---

## Anti-Pattern 3: Commenting out trigger logic to "temporarily disable"

**What the LLM generates:**

```apex
trigger AccountTrigger on Account (before insert, before update) {
    // TEMPORARILY DISABLED FOR DATA LOAD - re-enable before EOD
    // new AccountTriggerHandler().run();
}
```

**Why it happens:** LLMs treat a temporary disable as a code change because
that's the most direct interpretation of "turn it off".

**Correct pattern:** Toggle `Trigger_Setting__mdt.Is_Active__c = false` for
that handler, or assign the `Bypass_Triggers` Custom Permission to the
loader user. No code change.

**Detection hint:** commented-out `new .*TriggerHandler\(\)\.run\(\)` or
`//.*TODO.*re-enable` patterns in trigger files.

---

## Anti-Pattern 4: Forgetting the Custom Metadata cache lag

**What the LLM generates:** "Deploy the CMDT change and the trigger is
disabled immediately." No mention of cache propagation.

**Why it happens:** LLMs treat CMDT like config — instant.

**Correct pattern:** Document that CMDT changes can take seconds to
propagate, and that ops should verify by issuing a test DML and reading the
`Application_Log__c` entry before declaring the kill switch effective.

**Detection hint:** any rollout/runbook section that promises "immediate"
effect for a CMDT-based kill switch.

---

## Anti-Pattern 5: Combining recursion prevention and bypass in one flag

**What the LLM generates:**

```apex
public class TriggerControl {
    public static Boolean disabled = false; // both recursion guard and kill switch
}
```

**Why it happens:** LLMs see "static boolean to control trigger" twice in
training and conflate recursion guards with bypass switches.

**Correct pattern:** Separate concerns. Recursion guard lives in the handler
(per-handler `private static Set<Id> processedIds`). Bypass lives in
`TriggerControl` keyed by (object, handler) and respects CMDT + Custom
Permission. Flipping the kill switch must not change recursion behaviour
and vice versa.

**Detection hint:** a single boolean field whose name contains both "bypass"
and "recursion", or any handler that uses `TriggerControl.bypass(...)` to
prevent re-entry within the same transaction.

---

## Anti-Pattern 6: Static-state bypass without try/finally

**What the LLM generates:**

```apex
TriggerControl.bypass('Account', 'AccountTriggerHandler');
update accounts;
TriggerControl.restore('Account', 'AccountTriggerHandler');
```

**Why it happens:** Linear code reads cleanly; LLMs don't always reach for
exception-safe scaffolding.

**Correct pattern:**

```apex
try {
    TriggerControl.bypass('Account', 'AccountTriggerHandler');
    update accounts;
} finally {
    TriggerControl.restore('Account', 'AccountTriggerHandler');
}
```

**Detection hint:** any `TriggerControl.bypass(...)` call NOT inside a
`try` block whose `finally` clause calls `restore(...)`.
