# Examples — Apex Flow Invocation From Apex

## Example 1: Invoke An Autolaunched Flow From A Queueable

**Context:** A nightly Queueable reconciles Opportunity data and needs to apply an admin-owned tier calculation that lives in a Flow.

**Problem:** Developers instinctively call `Flow.Interview.createInterview` inside the record loop, creating one interview per record (200+ interviews). Each interview runs separately, sharing governor limits, multiplying CPU cost by 200x.

**Solution:**

```apex
public class OppTierReconQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        List<Opportunity> opps = [SELECT Id, Amount, CloseDate FROM Opportunity
                                  WHERE StageName = 'Closed Won' LIMIT 200];
        Map<String, Object> params = new Map<String, Object>{
            'inputOpps' => opps
        };
        try {
            Flow.Interview i = Flow.Interview.createInterview('Recon_Opp_Tiers', params);
            i.start();
            List<Opportunity> updated = (List<Opportunity>) i.getVariableValue('outputOpps');
            if (updated != null && !updated.isEmpty()) update updated;
        } catch (Flow.FlowException e) {
            System.debug(LoggingLevel.ERROR, 'Flow failed: ' + e.getMessage());
            throw e;
        }
    }
}
```

**Why it works:** The Flow receives a collection input and iterates internally. One interview, one governor budget, and output comes back as a mutated collection.

---

## Example 2: Guarding Against Screen Flow Invocation

**Context:** An admin accidentally changes a Flow from "Autolaunched" to "Screen" without notifying the Apex team. Next deployment the Apex wrapper throws a runtime error.

**Problem:** Practitioners have no way to detect at compile time that the Flow is of the wrong type. Users see "An unexpected error occurred" when the triggering action fires.

**Solution:**

```apex
public with sharing class FlowRunner {
    public static Map<String, Object> run(String flowName, Map<String, Object> params) {
        try {
            Flow.Interview i = Flow.Interview.createInterview(flowName, params);
            i.start();
            return new Map<String, Object>{ 'success' => true, 'interview' => i };
        } catch (Flow.FlowException fe) {
            return new Map<String, Object>{
                'success' => false,
                'error'   => 'Flow ' + flowName + ' failed: ' + fe.getMessage(),
                'type'    => 'FLOW_EXCEPTION'
            };
        } catch (Exception e) {
            return new Map<String, Object>{
                'success' => false,
                'error'   => e.getMessage(),
                'type'    => e.getTypeName()
            };
        }
    }
}
```

**Why it works:** Callers get a structured result; the enclosing transaction can continue, log, alert, or fall back to Apex-native logic.

---

## Example 3: Reading Multiple Output Variables Safely

**Context:** A pricing Flow returns `finalPrice`, `discountApplied`, `tier`, and a list of `warnings`.

**Problem:** Developers cast each output without null-checks and NPE on missing variables (typos) or empty collections.

**Solution:**

```apex
Flow.Interview i = Flow.Interview.createInterview('Pricing_Engine', params);
i.start();

Object priceObj = i.getVariableValue('finalPrice');
Decimal finalPrice = priceObj == null ? null : (Decimal) priceObj;

Object tierObj = i.getVariableValue('tier');
String tier = tierObj == null ? 'STANDARD' : (String) tierObj;

Object warnObj = i.getVariableValue('warnings');
List<String> warnings = warnObj == null
    ? new List<String>()
    : (List<String>) warnObj;
```

**Why it works:** Every output is null-checked before cast. Missing outputs fall through to safe defaults rather than NPEs.

---

## Anti-Pattern: Per-Record Flow Invocation In A Trigger

**What practitioners do:**

```apex
for (Account a : Trigger.new) {
    Flow.Interview i = Flow.Interview.createInterview('Assign_Tier',
        new Map<String, Object>{ 'account' => a });
    i.start();
}
```

**What goes wrong:** On a 200-record bulk DML, the trigger creates and runs 200 interviews. CPU consumption explodes. SOQL and DML inside the Flow count 200x. Governor limits exhaust before completion.

**Correct approach:** Design the Flow to accept a `List<Account>` input and loop internally. Call once.

---

## Anti-Pattern: Hardcoded Flow API Name String With No Fallback

**What practitioners do:**

```apex
Flow.Interview i = Flow.Interview.createInterview('Assin_Tier', params);  // typo
```

**What goes wrong:** `SObjectException: There was an error while retrieving the Interview` at runtime. The Flow was never found. The typo might survive testing if the test class also uses the same constant.

**Correct approach:** Store Flow names in a Custom Metadata Type or a single `FlowNames` constants class with integration tests that assert each Flow exists via `Metadata` namespace or an actual invocation in the test setup.
