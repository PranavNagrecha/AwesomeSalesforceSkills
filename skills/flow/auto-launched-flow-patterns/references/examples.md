# Examples — Auto-Launched Flow Patterns

---

## Example 1: Apex-Invoked Flow for Configurable Approval Routing

**Context:** A financial services org has complex loan approval routing rules that change quarterly. Rather than deploying new Apex every quarter, the team encodes the routing logic in an auto-launched Flow so a business analyst can update rules in Flow Builder.

**Problem:** Without this pattern, routing logic is hard-coded in Apex. Every rule change requires a developer, a sandbox cycle, and a deployment window. When the Apex trigger calls the Flow in a loop (once per loan record in a bulk save), the Flow's internal SOQL queries multiply and the transaction hits the 100-query governor limit during end-of-month batch loads.

**Solution:**

*Flow variables:*
- `inputLoanRecords` — Collection (Record / Loan__c), Input Only
- `outputRoutedRecords` — Collection (Record / Loan__c), Output Only

*Apex invocation (trigger handler):*

```apex
public static void routeLoans(List<Loan__c> loans) {
    Map<String, Object> inputs = new Map<String, Object>{
        'inputLoanRecords' => loans
    };

    Flow.Interview routingFlow = Flow.Interview.createInterview(
        'Loan_Approval_Router',  // exact API name from Setup > Flows
        inputs
    );

    try {
        routingFlow.start();
    } catch (System.FlowException fe) {
        // Log and rethrow so the trigger transaction rolls back cleanly
        System.debug(LoggingLevel.ERROR,
            'Loan_Approval_Router failed: ' + fe.getMessage());
        throw fe;
    }

    List<SObject> routedLoans =
        (List<SObject>) routingFlow.getVariableValue('outputRoutedRecords');

    if (routedLoans != null) {
        update routedLoans;
    }
}
```

*Flow internal structure (high-level):*

```
[START: Auto-launched, no trigger]
        ↓
[LOOP: over inputLoanRecords]
   ↓
  [DECISION: Loan Amount > 500,000?]
    ├── Yes → [ASSIGNMENT: set ApprovalQueue = "Senior Underwriting"]
    └── No  → [ASSIGNMENT: set ApprovalQueue = "Standard Underwriting"]
   ↓
  [ASSIGNMENT: add updated loan record to outputRoutedRecords collection]
        ↓
[END LOOP]
        ↓
[END]
```

**Why it works:** One `start()` call processes the entire collection in one Flow transaction. No SOQL multiplication occurs because the Flow reads from the input collection rather than querying Salesforce for each record. The fault path is on every DML element to capture `{!$Flow.FaultMessage}` before the exception reaches the Apex caller.

---

## Example 2: External System Triggering a Case-Creation Flow via REST API

**Context:** A legacy customer portal (non-Salesforce) needs to create Cases and assign them to the correct queue based on product and region. The team wants to manage the assignment logic in Salesforce Flow without giving the portal direct object permissions.

**Problem:** Direct REST API record creation (POST to `/sobjects/Case`) requires the integration user to have object-level create permission and hard-codes assignment logic in the portal. When assignment rules change, the portal must be redeployed.

**Solution:**

*Flow API name:* `Create_Support_Case`

*Flow variables:*
- `inputAccountId` — Text, Input Only
- `inputSubject` — Text, Input Only
- `inputProductFamily` — Text, Input Only
- `inputRegion` — Text, Input Only
- `outputCaseId` — Text, Output Only
- `outputAssignedQueue` — Text, Output Only

*HTTP request from portal:*

```http
POST /services/data/v62.0/actions/custom/flow/Create_Support_Case
Authorization: Bearer <oauth_access_token>
Content-Type: application/json

{
  "inputs": [
    {
      "inputAccountId": "001xx000003GybAAA",
      "inputSubject": "Login page returns 500 error",
      "inputProductFamily": "Platform",
      "inputRegion": "EMEA"
    }
  ]
}
```

*Successful response:*

```json
[
  {
    "actionName": "Create_Support_Case",
    "errors": null,
    "isSuccess": true,
    "outputValues": {
      "outputCaseId": "500xx000001XyzABC",
      "outputAssignedQueue": "EMEA Platform Support"
    }
  }
]
```

*Error response (Flow fault or input mismatch):*

```json
[
  {
    "actionName": "Create_Support_Case",
    "errors": [
      {
        "message": "An error occurred while executing the flow",
        "statusCode": "FLOW_EXCEPTION"
      }
    ],
    "isSuccess": false,
    "outputValues": null
  }
]
```

**Why it works:** The integration user needs only the "Run Flows" permission and object-level Create on Case. All routing logic lives in Flow Builder. When EMEA routing rules change, the Flow is updated in Salesforce — no portal redeployment required. The portal checks `isSuccess` before reading `outputValues` to handle faults gracefully.

---

## Example 3: Platform Event Triggers an Auto-Launched Flow for Async Post-Processing

**Context:** An order management system publishes an `Order_Fulfillment__e` Platform Event after an order ships. A Flow subscribes to this event to update related records and notify the customer — without blocking the order management transaction.

**Problem:** Placing all post-fulfillment logic in the order Apex trigger makes the trigger long and adds SOQL/DML load to the order save transaction. If the notification logic fails, it rolls back the order save.

**Solution:**

*Platform Event object:* `Order_Fulfillment__e`
- Fields: `Order_Id__c` (Text), `Carrier__c` (Text), `Tracking_Number__c` (Text)

*Flow Start element configuration:*
- Flow type: Auto-launched Flow
- Start trigger: Platform Event — `Order_Fulfillment__e`
- Entry conditions: none (process all events)

*Inside the Flow:*

```
[START: Platform Event — Order_Fulfillment__e]
         ↓
[GET RECORDS: Order__c where Id = {!$Record.Order_Id__c}]
  ├── fault → [CREATE RECORDS: Error_Log__c — {!$Flow.FaultMessage}] → [END]
  └── success ↓
[UPDATE RECORDS: Order__c.Status = "Shipped", Tracking_Number__c = {!$Record.Tracking_Number__c}]
  ├── fault → [CREATE RECORDS: Error_Log__c — {!$Flow.FaultMessage}] → [END]
  └── success ↓
[SEND EMAIL: Customer shipment confirmation]
         ↓
[END]
```

**Why it works:** The Flow runs in a new, separate transaction from the order management system. Its governor limits are fully reset — the order save is not delayed or blocked. The fault path logs `{!$Flow.FaultMessage}` to `Error_Log__c` so failures are visible without requiring the publisher to track them. Platform Event delivery is at-least-once, so the Flow should be idempotent (safe to run more than once for the same event).

---

## Anti-Pattern: Calling `start()` Inside a Loop

**What practitioners do:** They write a for-loop in Apex that calls `Flow.Interview.createInterview()` and `start()` once per record, thinking it mirrors how the Flow builder's loop element works.

```apex
// WRONG — called inside a loop
for (Opportunity opp : opps) {
    Map<String, Object> inputs = new Map<String, Object>{
        'inputOppId' => opp.Id
    };
    Flow.Interview f = Flow.Interview.createInterview('Process_Opp', inputs);
    f.start();  // Each call fires the Flow's SOQL and DML
}
```

**What goes wrong:** If `Process_Opp` contains one SOQL query and one DML statement, and the trigger fires on 150 Opportunities in a data load, the transaction issues 150 SOQL queries (blowing the 100-query limit) and 150 DML statements (exceeding the 150-DML limit). The transaction fails with a `System.LimitException` and all 150 records roll back.

**Correct approach:** Redesign the Flow to accept a collection input variable. Collect all records in Apex, then call `start()` once with the entire collection. Inside the Flow, use a Loop element to process the collection and accumulate updated records in an output collection for the Apex caller to DML once.
