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

The declaration half of that contract, as it appears in `Prepare_Renewal_Context.flow-meta.xml`
— note that every variable carries all four of `dataType`, `isCollection`, `isInput` and
`isOutput`, because none of them defaults to anything useful:

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata"><!-- excerpt: variable declarations from the subflow -->
<variables>
    <name>inOpportunityId</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>true</isInput>
    <isOutput>false</isOutput>
</variables>
<variables>
    <name>outHealthScore</name>
    <dataType>Number</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
    <scale>0</scale>
</variables>
<variables>
    <name>outPrimaryContractEndDate</name>
    <dataType>Date</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
</variables>
<variables>
    <name>outRenewalRisk</name>
    <dataType>String</dataType>
    <isCollection>false</isCollection>
    <isInput>false</isInput>
    <isOutput>true</isOutput>
</variables>
<variables>
    <name>intContractRecords</name>
    <dataType>sObject</dataType>
    <objectType>Contract</objectType>
    <isCollection>true</isCollection>
    <isInput>false</isInput>
    <isOutput>false</isOutput>
</variables>
</Flow>
```

`intContractRecords` is the working collection. Both flags are `false` on purpose: it is
the child's scratch space, and leaving it exposed would put an internal query result into
the contract that a caller could then start depending on.

**Why it works:** Reuse stays centered on the shared logic rather than dragging unrelated parent behavior into the child flow.

---

## Anti-Pattern: Child Flow As A Hidden Grab Bag

**What practitioners do:** They create one subflow with many inputs, many outputs, and unrelated side effects because multiple parents "might need it."

**What goes wrong:** The child flow is no longer reusable. It is just a second parent flow with hidden coupling.

**Correct approach:** Keep reusable child flows narrow. If the logic has become broad and stateful, move it to a better boundary instead of forcing more variables into the subflow.

---

## Anti-Pattern: Putting A Fault Path On The Subflow Element

**What practitioners do:** They add `<faultConnector>` to the `<subflows>` element the way
they would to a Get or an Update, on the assumption that a call is a call.

**What goes wrong:** `faultConnector` is not a field of `FlowSubflow`. The element below is
not valid metadata, and no amount of retrying the deploy will make the branch exist:

```xml
<!-- INVALID: FlowSubflow has no faultConnector field (api_meta.txt L72628-72660) -->
<subflows>
    <name>Call_Write_Renewal_Tasks</name>
    <flowName>Write_Renewal_Tasks</flowName>
    <connector>
        <targetReference>Continue</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Handle_Subflow_Error</targetReference>
    </faultConnector>
</subflows>
```

**Correct approach:** The child returns its own failure. It catches the fault internally on
the element that can throw, sets an `isOutput` boolean, and the parent branches on that
boolean with an ordinary Decision:

```xml
<subflows>
    <name>Call_Write_Renewal_Tasks</name>
    <flowName>Write_Renewal_Tasks</flowName>
    <connector>
        <targetReference>Check_Write_Succeeded</targetReference>
    </connector>
    <outputAssignments>
        <assignToReference>varWriteSucceeded</assignToReference>
        <name>outSucceeded</name>
    </outputAssignments>
    <outputAssignments>
        <assignToReference>varWriteError</assignToReference>
        <name>outErrorMessage</name>
    </outputAssignments>
</subflows>
```

`Check_Write_Succeeded` is the fault path. The full pair, including the child side, is in
`references/metadata-examples.md`.
