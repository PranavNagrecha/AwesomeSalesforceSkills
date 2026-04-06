# Examples — OmniStudio Remote Actions

## Example 1: IP Action with Scoped JSON Paths for a Quote Request

**Context:** An OmniScript collects customer and product selections across multiple steps. Step 4 calls an Integration Procedure to generate a quote from an external pricing engine. The OmniScript JSON contains PII from earlier steps (SSN, date of birth) that the pricing engine must not receive.

**Problem:** Without scoping the Send JSON Path, the entire OmniScript JSON — including PII — is sent to the Integration Procedure. The IP then forwards it to the external system, creating a data-leakage risk. Additionally, the pricing response overwrites the step node, destroying data from other elements in the same step.

**Solution:**

```
Action Element Configuration:
  Type:               Integration Procedure
  Integration Procedure Name: GenerateQuote_IP
  Send JSON Path:     ProductSelections
  Response JSON Path: QuoteResult
  Invoke Mode:        Promise
```

The IP receives only the `ProductSelections` node. The response lands at `QuoteResult`, leaving all other step data untouched. Promise mode ensures the quote data is available before the user sees Step 5.

**Why it works:** Scoped JSON Paths enforce the principle of least privilege on data flow. The OmniScript JSON acts as a shared state bus — every action should read and write only its own slice.

---

## Example 2: Apex Remote Action for Complex Eligibility Calculation

**Context:** A health insurance enrollment OmniScript needs to run a multi-factor eligibility check that involves 15+ business rules, lookups against custom metadata, and date arithmetic. An Integration Procedure would require 10+ steps with complex conditional logic that is hard to maintain declaratively.

**Problem:** Building this logic as an IP creates a deeply nested, hard-to-test procedure. Each conditional branch adds maintenance cost, and the IP debugger does not support breakpoints within conditional nodes.

**Solution:**

```apex
global class EligibilityCheck implements omnistudio.VlocityOpenInterface2 {

    global Object invokeMethod(String methodName, Map<String, Object> inputMap,
                               Map<String, Object> outputMap, Map<String, Object> options) {
        if (methodName == 'checkEligibility') {
            String memberId = (String) inputMap.get('MemberId');
            Date effectiveDate = Date.valueOf((String) inputMap.get('EffectiveDate'));

            EligibilityResult result = EligibilityEngine.evaluate(memberId, effectiveDate);

            outputMap.put('IsEligible', result.isEligible);
            outputMap.put('DenialReasons', result.denialReasons);
            outputMap.put('EffectiveCoverage', result.coverageMap);
        }
        return null;
    }
}
```

```
Action Element Configuration:
  Type:               Apex Remote Action
  Apex Class:         EligibilityCheck
  Method Name:        checkEligibility
  Send JSON Path:     MemberInfo
  Response JSON Path: EligibilityResult
  Invoke Mode:        Promise
```

**Why it works:** Complex business logic belongs in testable Apex, not in deeply nested IP steps. The Apex class is unit-testable with standard Apex test methods. The OmniScript only needs to know the input/output contract.

---

## Example 3: Handling the Continuation Pattern for Slow External APIs

**Context:** A FlexCard needs to display real-time inventory data from a warehouse management system. The warehouse API takes 30-90 seconds to respond during peak hours. A standard synchronous callout fails with a timeout after the configured limit.

**Problem:** The synchronous Remote Action throws an Apex timeout exception, and the FlexCard shows a generic error. Increasing the timeout is not viable because it blocks the user thread and risks hitting the 120-second absolute limit.

**Solution:**

```apex
global class InventoryCheckContinuation implements omnistudio.VlocityOpenInterface2 {

    global Object invokeMethod(String methodName, Map<String, Object> inputMap,
                               Map<String, Object> outputMap, Map<String, Object> options) {
        if (methodName == 'getInventory') {
            Continuation cont = new Continuation(120);
            cont.continuationMethod = 'processResponse';

            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:Warehouse_API/inventory');
            req.setMethod('POST');
            req.setBody(JSON.serialize(inputMap.get('WarehouseRequest')));

            cont.addHttpRequest(req);
            return cont;
        }
        return null;
    }

    global Object processResponse(Map<String, Object> outputMap) {
        HttpResponse resp = Continuation.getResponse(this.requestLabel);
        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(resp.getBody());
        outputMap.put('InventoryData', body);
        return null;
    }
}
```

**Why it works:** The Continuation pattern releases the Apex thread while waiting for the external response. The OmniStudio framework resumes the action when the callback fires, keeping the user session alive without blocking server resources.

---

## Anti-Pattern: Using Fire and Forget for Data the Next Step Needs

**What practitioners do:** Set invoke mode to Fire and Forget on an action whose output is displayed or validated on the next OmniScript step. The intent is to make the current step load faster.

**What goes wrong:** The user clicks Next before the action response arrives. The response writes to a step node that is no longer active. The next step renders with null data. No error is logged because the action itself succeeded — the data simply had nowhere to land.

**Correct approach:** Use Promise invoke mode for any action whose output is consumed by the current step or any subsequent step. Reserve Fire and Forget exclusively for side effects that do not affect the OmniScript's visible state (e.g., logging, analytics tracking, or audit record creation).
