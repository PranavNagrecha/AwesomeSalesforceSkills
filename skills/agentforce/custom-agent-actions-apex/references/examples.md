# Examples — Custom Agent Actions Apex

## Example 1: Create Support Case Action for a Service Agent

**Scenario:** A service company builds an Agentforce Service Agent that handles inbound customer inquiries. The agent needs to create a Case when a customer describes a product problem.

**Problem:** The default Agentforce standard actions do not create Cases automatically. A custom Apex action is needed so the agent can create a Case with the correct record type, subject, and account linkage.

**Solution:**

```apex
public class CreateCaseInput {
  @InvocableVariable(
    label='Subject'
    description='One-sentence summary of the customer problem. Required.'
    required=true
  )
  public String subject;

  @InvocableVariable(
    label='Account ID'
    description='The Salesforce ID of the account submitting the case. Optional.'
  )
  public String accountId;

  @InvocableVariable(
    label='Description'
    description='Detailed description of the problem. Optional but improves routing accuracy.'
  )
  public String description;
}

public class CreateCaseOutput {
  @InvocableVariable(label='Success' description='True if case was created.')
  public Boolean success;
  @InvocableVariable(label='Case ID' description='ID of the created case. Null if failed.')
  public String caseId;
  @InvocableVariable(label='Case Number' description='Human-readable case number.')
  public String caseNumber;
  @InvocableVariable(label='Error Message' description='Error detail if success is false.')
  public String errorMessage;
}

@InvocableMethod(
  label='Create Support Case'
  description='Creates a new Salesforce Case for a customer product problem or service request. Invoke when the customer has described a specific issue that needs to be tracked and assigned to support.'
  callout=false
)
public static List<CreateCaseOutput> createCase(List<CreateCaseInput> inputs) {
  List<CreateCaseOutput> outputs = new List<CreateCaseOutput>();
  for (CreateCaseInput inp : inputs) {
    CreateCaseOutput out = new CreateCaseOutput();
    try {
      Case c = new Case(
        Subject = inp.subject,
        Description = inp.description,
        AccountId = String.isNotBlank(inp.accountId) ? (Id) inp.accountId : null,
        Origin = 'AI Agent'
      );
      insert c;
      Case inserted = [SELECT Id, CaseNumber FROM Case WHERE Id = :c.Id WITH USER_MODE LIMIT 1];
      out.success = true;
      out.caseId = inserted.Id;
      out.caseNumber = inserted.CaseNumber;
      out.errorMessage = '';
    } catch (Exception e) {
      out.success = false;
      out.caseId = null;
      out.caseNumber = null;
      out.errorMessage = e.getMessage();
    }
    outputs.add(out);
  }
  return outputs;
}
```

**Why it works:** The `@InvocableMethod` description tells the Atlas Reasoning Engine exactly when to invoke this action. The structured output lets the agent surface the case number to the customer or handle the failure gracefully. The `Origin = 'AI Agent'` field tags agent-created cases for routing and reporting.

---

## Example 2: Order Status Lookup Action with External Callout

**Scenario:** An Employee Agent for an internal sales team needs to look up order status from an ERP system when a sales rep asks "What's the status of order #12345?"

**Problem:** The order data lives in the ERP, not Salesforce. The agent needs to call an external REST API.

**Solution:** The action uses a Named Credential to authenticate to the ERP and returns a structured order status response.

```apex
@InvocableMethod(
  label='Get Order Status from ERP'
  description='Retrieves the current shipment and fulfillment status of a customer order from the ERP system. Use when a sales representative asks about order status, delivery date, or shipment tracking.'
  callout=true
)
public static List<OrderStatusOutput> getOrderStatus(List<OrderStatusInput> inputs) {
  List<OrderStatusOutput> outputs = new List<OrderStatusOutput>();
  for (OrderStatusInput inp : inputs) {
    OrderStatusOutput out = new OrderStatusOutput();
    try {
      HttpRequest req = new HttpRequest();
      req.setEndpoint('callout:ERP_API/orders/' + EncodingUtil.urlEncode(inp.orderNumber, 'UTF-8'));
      req.setMethod('GET');
      req.setTimeout(10000);
      HttpResponse resp = new Http().send(req);
      if (resp.getStatusCode() == 200) {
        Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(resp.getBody());
        out.success = true;
        out.status = (String) body.get('status');
        out.estimatedDelivery = (String) body.get('estimated_delivery');
        out.errorMessage = '';
      } else {
        out.success = false;
        out.errorMessage = 'ERP returned HTTP ' + resp.getStatusCode();
      }
    } catch (Exception e) {
      out.success = false;
      out.errorMessage = e.getMessage();
    }
    outputs.add(out);
  }
  return outputs;
}
```

**Why it works:** `callout=true` marks the method as calling an external system, so screen flows can run it in a fresh transaction; the callout happens before any DML, so there is no uncommitted work to block it. Named Credential `ERP_API` handles authentication without hardcoded credentials. The 10-second timeout prevents the agent turn from hanging on a slow ERP response.

---

## Example 3: Apex Action Deployed With Its GenAiFunction Metadata

**Context:** A Service Agent needs a read-only "case status" action that the planner can reason with and that never returns raw records.

**Solution:** The complete Apex class, its test, the `GenAiFunction` component with input and output `schema.json` files, and the `package.xml` member form are in `references/metadata-examples.md`. The design choices it encodes:

```text
inputs   case_number  String   isUserInput=true
outputs  success      Boolean  isUsedByPlanner=true  isDisplayable=false
         status       String   isUsedByPlanner=true  isDisplayable=true
         subject      String   isUsedByPlanner=true  isDisplayable=true
         error_message String  isUsedByPlanner=true  isDisplayable=false
confirmation  not required (read-only)
sharing       with sharing + WITH USER_MODE (runs as the agent user)
```

**Why it works:** Every field is primitive, at least one output is visible to the planner, and the action reads only what the agent user may see.
