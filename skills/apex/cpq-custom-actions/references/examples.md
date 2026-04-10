# Examples — CPQ Custom Actions

## Example 1: Flow-Backed Validation Button That Checks Quote Eligibility

**Context:** A manufacturing company's CPQ org requires sales reps to run a product compatibility check before submitting a quote for approval. The check queries a custom object (`Compatible_Product_Matrix__c`) and returns a list of conflicts. The logic is too complex for a CPQ Product Rule.

**Problem:** Without a custom action, reps either skip the validation step or forget to run it before submission. Product Rules fire automatically but cannot be triggered on demand. Standard Lightning quick actions are not available inside the QLE.

**Solution:**

Step 1 — Create an invocable Apex method that accepts a Quote ID and returns a list of conflict messages:

```apex
public class QuoteCompatibilityChecker {
    @InvocableMethod(label='Check Quote Product Compatibility' category='CPQ')
    public static List<CheckResult> checkCompatibility(List<Id> quoteIds) {
        List<CheckResult> results = new List<CheckResult>();
        for (Id quoteId : quoteIds) {
            CheckResult result = new CheckResult();
            // Query quote lines and compatible product matrix
            List<SBQQ__QuoteLine__c> lines = [
                SELECT SBQQ__Product__c FROM SBQQ__QuoteLine__c
                WHERE SBQQ__Quote__c = :quoteId
            ];
            // ... conflict detection logic ...
            result.conflicts = 'None detected'; // or conflict list
            results.add(result);
        }
        return results;
    }

    public class CheckResult {
        @InvocableVariable(label='Conflicts Found')
        public String conflicts;
    }
}
```

Step 2 — Build an Autolaunched Flow (`Check_Quote_Compatibility`) with:
- Input variable: `quoteId` (Text, Available for Input)
- Apex Action element calling `QuoteCompatibilityChecker.checkCompatibility`, passing `{!quoteId}`
- Screen element to display the result

Step 3 — Create the `SBQQ__CustomAction__c` record:

```
Name: Check Compatibility
SBQQ__Type__c: Flow
SBQQ__FlowName__c: Check_Quote_Compatibility
SBQQ__Location__c: Global
SBQQ__DisplayOrder__c: 1
SBQQ__Active__c: true
```

Step 4 — Add a condition so the button only appears for Draft quotes:

```
SBQQ__CustomAction__c.SBQQ__ConditionsMet__c: All

SBQQ__CustomActionCondition__c:
  SBQQ__CustomAction__c: (lookup to above record)
  SBQQ__FilterField__c: SBQQ__Status__c
  SBQQ__FilterOperator__c: Equals
  SBQQ__FilterValue__c: Draft
```

**Why it works:** The Flow acts as the bridge between the CPQ button click and the Apex invocable method. Custom actions have no native Apex type, but an Autolaunched or Screen Flow can call any `@InvocableMethod`. The condition record hides the button once the quote leaves Draft status, preventing redundant validation runs.

---

## Example 2: URL Action Launching an External Pricing Reference Tool

**Context:** A technology distributor uses an external vendor pricing portal (`https://pricing.distributor.example.com`) alongside Salesforce CPQ. Sales reps need to check live distributor pricing per quote line without leaving the QLE. The portal accepts a product SKU and quote date via URL parameters.

**Problem:** Opening the portal manually requires reps to copy the product SKU from the QLE into a browser tab, which is error-prone and slow. There is no API integration in scope for this org.

**Solution:**

Step 1 — Confirm `https://pricing.distributor.example.com` is added to CSP Trusted Sites in Setup > Security > CSP Trusted Sites (required if the URL opens in a Lightning modal; for new-tab navigation it is less critical but still good practice).

Step 2 — Create the `SBQQ__CustomAction__c` record:

```
Name: Check Distributor Price
SBQQ__Type__c: URL
SBQQ__URL__c: https://pricing.distributor.example.com/lookup?sku={!SBQQ__ProductCode__c}&quoteDate={!SBQQ__Quote__r.SBQQ__StartDate__c}
SBQQ__Location__c: Line Item
SBQQ__DisplayOrder__c: 1
SBQQ__Active__c: true
```

The CPQ merge field syntax `{!SBQQ__ProductCode__c}` resolves the product code from the current line item record at click time.

**Why it works:** The `Line Item` location places the button on each individual quote line row in the QLE, giving reps a per-line lookup button. The merge field tokens are resolved by the CPQ rendering engine at click time, not at page load, so the URL always reflects the current line's product. No Apex, no Flow, and no API integration is needed for this pattern.

---

## Anti-Pattern: Using a Lightning Quick Action Instead of SBQQ__CustomAction__c

**What practitioners do:** Add a Quick Action of type `Flow` or `Screen Flow` to the `SBQQ__Quote__c` object's Lightning record page action bar, then tell reps to use that button while working in the QLE.

**What goes wrong:** The QLE is a managed Lightning component that takes over the full page layout when opened. The standard Lightning record page action bar (including Quick Actions) is not visible while the QLE is active. Reps cannot access the Quick Action from inside the QLE — they must close the QLE to return to the record page. This breaks the rep workflow and defeats the purpose of the action.

**Correct approach:** Always create an `SBQQ__CustomAction__c` record for any button that must be accessible while the QLE is open. Quick Actions on the Quote record page are appropriate only for actions that do not require QLE context.
