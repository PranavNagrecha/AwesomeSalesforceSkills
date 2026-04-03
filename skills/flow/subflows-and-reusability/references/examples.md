# Examples - Subflows And Reusability

## Example 1: Shared Case Routing Decision

**Context:** Three separate case-related flows all decide queue assignment from region and priority.

**Problem:** Each parent flow contains its own routing decision tree, and one team updates only two of the three copies.

**Solution:**

Extract an autolaunched child flow with a narrow contract.

```text
Flow API Name: Resolve_Case_Routing
Input variables:
- inRegion (Text, Available for input)
- inPriority (Text, Available for input)

Output variables:
- outQueueDeveloperName (Text, Available for output)

Parent call:
- Case_AfterSave_Route
- Escalation_Request_Submit
- Portal_Case_Submit
```

**Why it works:** The routing rule becomes one contract that every caller can share without copying the decision tree.

---

## Example 2: Shared Data Enrichment Before Parent-Specific Actions

**Context:** Several renewal flows need the same account health score and contract summary before continuing to their own branching logic.

**Problem:** Each flow repeats the same lookups and formulas, then mixes them with parent-specific side effects.

**Solution:**

Create a child flow that only gathers and returns the reusable context.

```text
Flow API Name: Prepare_Renewal_Context
Input variables:
- inOpportunityId (Text)

Output variables:
- outHealthScore (Number)
- outPrimaryContractEndDate (Date)
- outRenewalRisk (Text)
```

Parent flows keep their own task creation, notifications, and approval routing after the shared preparation step returns.

**Why it works:** Reuse stays centered on the shared logic rather than dragging unrelated parent behavior into the child flow.

---

## Anti-Pattern: Child Flow As A Hidden Grab Bag

**What practitioners do:** They create one subflow with many inputs, many outputs, and unrelated side effects because multiple parents "might need it."

**What goes wrong:** The child flow is no longer reusable. It is just a second parent flow with hidden coupling.

**Correct approach:** Keep reusable child flows narrow. If the logic has become broad and stateful, move it to a better boundary instead of forcing more variables into the subflow.
