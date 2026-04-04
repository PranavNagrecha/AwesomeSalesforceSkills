# Examples — Business Rules Engine

## Example 1: Broadband Product Eligibility Decision Table

**Context:** A telecommunications company needs to determine which broadband products a customer is eligible for based on service area, credit score tier, and account type. The eligibility matrix has approximately 30 rows and changes quarterly when new service areas are added.

**Problem:** The first implementation hard-codes eligibility logic in an Apex trigger using nested `if/else` blocks. Every time a new service area is added, a developer must update the Apex class, write tests, and deploy through the full release process — taking three weeks and blocking marketing from launching new territories on their desired dates.

**Solution:**

Define a Decision Table named `BroadbandProductEligibility` with the following columns:

| Column | Type | Role | Operator |
|--------|------|------|----------|
| `ServiceAreaCode` | Text | Input | In |
| `CreditTier` | Text | Input | Equals |
| `AccountType` | Text | Input | In |
| `EligibleProductCode` | Text | Output | — |
| `IsEligible` | Boolean | Output | — |

Add a default row (all input conditions blank) returning `IsEligible = false` and `EligibleProductCode = null` to handle any unmatched combination without returning null at the IP layer.

In the Integration Procedure that drives the OmniScript enrollment journey, add a `BusinessRules` action element:

```json
// IP Action element: type = BusinessRules, subtype = DecisionTable
// Input mapping (from IP context variables):
{
  "ServiceAreaCode": "%serviceArea%",
  "CreditTier": "%creditTier%",
  "AccountType": "%accountType%"
}

// Output mapping (to IP variables):
// isEligible    <-- output attribute "IsEligible"
// productCode   <-- output attribute "EligibleProductCode"
```

Then add a Condition step in the IP: if `isEligible == true`, proceed to product display; otherwise, route to an ineligibility message.

**Why it works:** Business analysts can add new service area codes or product mappings directly in the BRE UI. The rule change takes effect immediately on activation — no deployment, no Apex test authoring, no release calendar dependency. The Integration Procedure wiring remains static.

---

## Example 2: Insurance Quote Eligibility with Expression Set Nested Logic

**Context:** An insurance platform must determine whether a customer is eligible for a specific policy product. Eligibility requires either (a) the applicant is 18+ AND their state is in an approved list, OR (b) the applicant is 21+ AND they already hold an existing policy with the carrier.

**Problem:** The product team initially modeled this in a Decision Table. The combinatorial explosion of age ranges, states, and existing-policy flags required 200+ rows and was prone to authoring errors when new states were added. The flat-table model also made it impossible to verify the logical intent by reading the table.

**Solution:**

Create an Expression Set named `PolicyEligibility`. In version 1, configure two top-level condition groups joined by OR:

```
(Group 1 — AND)
  Condition: applicantAge >= 18
  Condition: applicantState IN ['CA', 'TX', 'NY', 'FL', 'WA']

(Group 2 — AND)
  Condition: applicantAge >= 21
  Condition: hasExistingPolicy = true
```

Set the output to a boolean attribute `IsEligible`.

Invoke from Apex in a pre-opportunity-creation trigger:

```apex
// Apex call pattern — stdlib only, no external dependency
Map<String, Object> inputs = new Map<String, Object>{
    'applicantAge'      => (Integer) applicantAge,
    'applicantState'    => applicantState,
    'hasExistingPolicy' => hasExistingPolicy
};

Map<String, Object> result = BusinessRules.ExpressionSetService.evaluate(
    'PolicyEligibility',
    inputs
);

Boolean isEligible = (Boolean) result.get('IsEligible');

if (isEligible == null) {
    // Expression set returned no result — handle gracefully
    throw new AuraHandledException('Eligibility check returned no result. Contact support.');
}
```

**Why it works:** The Expression Set directly represents the logical intent `(A AND B) OR (C AND D)` without combinatorial row explosion. Product managers can read the condition groups in the BRE designer and verify the logic without parsing a table. When a new approved state is added, only one condition's value list changes.

---

## Anti-Pattern: Using Flow Decision Elements for Multi-Attribute Eligibility

**What practitioners do:** Build a Screen Flow or Auto-launched Flow with a Decision element containing resource formulas like `{!applicantAge} >= 18 && {!applicantState} == 'CA'`. For each new product or territory, they clone the flow and update the formula.

**What goes wrong:**
- Every eligibility rule change requires a developer to modify, test, and deploy a Flow.
- Formula-based conditions in Flow Decision elements have no built-in test harness for business analysts; testing requires a full flow execution.
- Multi-attribute conditions across 10+ inputs result in deeply nested Decision elements that are hard to audit.
- When the same rule needs to be evaluated in both a Flow context and an Apex trigger context, the logic must be duplicated — Flows are not callable from Apex synchronously in the same way BRE is.

**Correct approach:** Model the multi-attribute rule in a BRE Decision Table or Expression Set. Call it from Integration Procedures (for OmniScript journeys) or directly from Apex (`ExpressionSetService.evaluate()`). Reserve Flow Decision elements for workflow-level branching — e.g., "if eligibility is confirmed, move to the next screen" — not for computing whether eligibility holds.
