# Examples — Apex Enum Patterns

## Example 1: Enum-based dispatch in a trigger handler

Replace string switching with an enum. Compiler catches typos; runtime
catches new values.

```apex
public enum RenewalAction { NOTIFY_OWNER, ESCALATE, AUTO_CLOSE }

public class RenewalDispatcher {
    public static void handle(RenewalAction action, Opportunity opp) {
        switch on action {
            when NOTIFY_OWNER { notifyOwner(opp); }
            when ESCALATE     { escalate(opp); }
            when AUTO_CLOSE   { autoClose(opp); }
            when else {
                throw new IllegalArgumentException(
                    'Unhandled RenewalAction: ' + action
                );
            }
        }
    }
}
```

The `when else` is mandatory — Apex doesn't enforce exhaustive switch.
When someone adds `RENEW_AT_DISCOUNT`, the throw surfaces it in tests.

---

## Example 2: Safe `valueOf` from a Custom Metadata string

`Enum.valueOf` throws `System.NoSuchElementException` for unknown values.
Wrap it.

```apex
public class RenewalActionParser {
    public static RenewalAction parse(String raw, RenewalAction fallback) {
        if (String.isBlank(raw)) return fallback;
        try {
            return RenewalAction.valueOf(raw.trim());
        } catch (System.NoSuchElementException e) {
            System.debug(LoggingLevel.WARN,
                'Unknown RenewalAction `' + raw + '`; using ' + fallback);
            return fallback;
        }
    }
}
```

When the source is configuration (Custom Metadata, a field), this is the
only safe pattern. Bare `valueOf` will fail an entire transaction the
moment someone misconfigures the metadata.

---

## Example 3: Mapping an enum to/from a picklist value

If the picklist label changes, the API name doesn't. Map by API name, not
label.

```apex
public enum CaseStage {
    NEW_INTAKE, IN_PROGRESS, ESCALATED, CLOSED
}

public class CaseStageMapper {
    private static final Map<String, CaseStage> BY_API = new Map<String, CaseStage>{
        'New_Intake'   => CaseStage.NEW_INTAKE,
        'In_Progress'  => CaseStage.IN_PROGRESS,
        'Escalated'    => CaseStage.ESCALATED,
        'Closed'       => CaseStage.CLOSED
    };

    public static CaseStage fromPicklistApiName(String apiName) {
        CaseStage v = BY_API.get(apiName);
        if (v == null) {
            throw new IllegalArgumentException(
                'No CaseStage mapping for picklist API name: ' + apiName);
        }
        return v;
    }

    public static String toPicklistApiName(CaseStage s) {
        for (String key : BY_API.keySet()) {
            if (BY_API.get(key) == s) return key;
        }
        throw new IllegalStateException('No mapping for ' + s);
    }
}
```

---

## Example 4: Asserting `values()` in a unit test

A 2-line test that catches the "someone added a value but didn't update
the dispatcher" mistake.

```apex
@isTest
static void renewal_action_values_are_complete() {
    Set<RenewalAction> expected = new Set<RenewalAction>{
        RenewalAction.NOTIFY_OWNER,
        RenewalAction.ESCALATE,
        RenewalAction.AUTO_CLOSE
    };
    Set<RenewalAction> actual = new Set<RenewalAction>(RenewalAction.values());
    System.assertEquals(expected, actual,
        'Enum gained a value — update RenewalDispatcher.handle()');
}
```

Cheap, fast, and the assertion message points the next engineer at the
right file.

---

## Example 5: Global enum in a managed package

```apex
global enum LicenseTier { FREE, PRO, ENTERPRISE }
```

Once a `global` enum ships, the values become a stable contract. Removing
`PRO` is a breaking change for every subscriber. Add new values at the
end of the list — never reorder; ordinals are positional.

For internal-only enums, use `public`. The compiler will let you change
public enum values freely between package versions.
