# LLM Anti-Patterns — Custom Agent Actions Apex

## Anti-Pattern 1: Generating Single-Object Method Signatures Instead of List-in/List-out

**What the LLM generates wrong:**
```apex
@InvocableMethod(label='Create Case' description='...')
public static Case createCase(CreateCaseInput input) { // Wrong: single input
  return new Case(...);                                 // Wrong: single return
}
```

**Why it happens:** Single-method signatures look cleaner. The LLM optimizes for readability without knowing the platform constraint.

**Correct pattern:** The Apex Developer Guide allows at most one parameter, and that parameter must be a list (primitive, sObject, or user-defined type); a non-void return must also be a list, matched to the inputs by size and order. A method with no parameter, or a `void` method, is legal, but an agent action that takes input and returns a result uses `List<Input>` and `List<Output>`, even when only one record is ever processed:
```apex
public static List<CreateCaseOutput> createCase(List<CreateCaseInput> inputs) {
  List<CreateCaseOutput> outputs = new List<CreateCaseOutput>();
  for (CreateCaseInput inp : inputs) { outputs.add(process(inp)); }
  return outputs;
}
```

**Detection hint:** Any `@InvocableMethod` with a non-list parameter, or a non-void, non-list return type.

---

## Anti-Pattern 2: Throwing Exceptions Instead of Returning Structured Error Output

**What the LLM generates wrong:**
```apex
@InvocableMethod(label='Get Order' description='...')
public static List<OrderOutput> getOrder(List<OrderInput> inputs) {
  if (inputs[0].orderId == null) {
    throw new IllegalArgumentException('Order ID is required'); // Wrong
  }
  // ...
}
```

**Why it happens:** Exception throwing is the standard Java/Apex error handling pattern. The LLM applies it without knowing that agents cannot meaningfully process exceptions.

**Correct pattern:** Catch all exceptions and return structured error output:
```apex
try {
  // ... work
  out.success = true;
} catch (Exception e) {
  out.success = false;
  out.errorMessage = e.getMessage();
}
outputs.add(out);
```

**Detection hint:** Any `throw` statement inside an `@InvocableMethod` method body.

---

## Anti-Pattern 3: Omitting `callout=true` on Actions That Make HTTP Requests

**What the LLM generates wrong:**
```apex
@InvocableMethod(label='Get ERP Status' description='...')  // Missing callout=true
public static List<ErpOutput> getErpStatus(List<ErpInput> inputs) {
  HttpRequest req = new HttpRequest();
  req.setEndpoint('callout:ERP/status');
  new Http().send(req); // the callout itself is allowed; the modifier is missing
}
```

**Why it happens:** The LLM knows `@InvocableMethod` syntax but may not associate the `callout=true` modifier with HTTP operations specifically. The opposite error is also common: claiming the modifier is what permits the callout. The Apex Developer Guide says the modifier identifies that the method calls an external system, and screen flows use it to decide whether to run the action in a new transaction; "uncommitted work pending" errors come from DML before the callout, not from the missing modifier.

**Correct pattern:** `@InvocableMethod(label='...' description='...' callout=true)` whenever the method contains any HTTP callout, and all callouts placed before any DML in the method.

**Detection hint:** Any `new Http().send(req)` inside an `@InvocableMethod` that lacks `callout=true` in the annotation.

---

## Anti-Pattern 4: Writing Generic or Missing Descriptions on @InvocableVariable

**What the LLM generates wrong:**
```apex
public class CaseInput {
  @InvocableVariable(label='Subject')  // Missing description
  public String subject;
  @InvocableVariable(label='Account ID' description='ID')  // Too vague
  public String accountId;
}
```

**Why it happens:** The `description` field is optional at the syntax level, so the LLM omits it as "optional metadata."

**Correct pattern:** Every `@InvocableVariable` needs a description that tells the Atlas Reasoning Engine exactly what value to pass and in what format:
```apex
@InvocableVariable(
  label='Account ID'
  description='The 15 or 18-character Salesforce Account ID of the customer submitting this request. Use the account ID from the conversation context. Optional.'
)
public String accountId;
```

**Detection hint:** Any `@InvocableVariable` with a missing or single-word description.

---

## Anti-Pattern 5: Hardcoding Credentials in Callout Actions

**What the LLM generates wrong:**
```apex
req.setHeader('Authorization', 'Bearer eyJhbGci...<hardcoded token>');
req.setEndpoint('https://api.erp.com/orders');
```

**Why it happens:** The LLM generates functional code from training examples where credentials were hardcoded for demonstration.

**Correct pattern:** Always use Named Credentials for authentication. The endpoint and credentials are configured in Setup and referenced via `callout:<NamedCredentialName>`:
```apex
req.setEndpoint('callout:ERP_API/orders/' + orderId);
// Authentication is handled by the Named Credential — no header needed
```

**Detection hint:** Any hardcoded URL with a domain name (not `callout:`) or any hardcoded Authorization header in an `@InvocableMethod` callout.

---

## Anti-Pattern 6: Returning sObjects or Collections From an Agent Action

**What the LLM generates wrong:**
```apex
public class LookupOutput {
  @InvocableVariable(label='Accounts' description='Matching accounts')
  public List<Account> accounts;   // collection of sObjects
}
```

**Why it happens:** Flow accepts sObject and collection variables, so LLMs reuse Flow-style DTOs. The Generative AI guide says custom actions that reference an Apex class or flow support only primitive data types and that collections aren't supported.

**Correct pattern:**
```apex
public class LookupOutput {
  @InvocableVariable(label='Account Count' description='How many accounts matched the name.')
  public Integer accountCount;
  @InvocableVariable(label='Top Match Name' description='Name of the best-matching account, or blank if none matched.')
  public String topMatchName;
  @InvocableVariable(label='Top Match Id' description='Record ID of the best-matching account, or blank if none matched.')
  public String topMatchId;
}
```

**Detection hint:** `List<...>`, `Map<...>`, `SObject`, or a concrete sObject type as the type of an `@InvocableVariable` in a class used by an agent action.

---

## Anti-Pattern 7: Hand-Writing a GenAiFunction Schema With No Planner-Visible Output

**What the LLM generates wrong:** An output `schema.json` where every property has `"copilotAction:isDisplayable": true` and no property sets `"copilotAction:isUsedByPlanner": true`.

**Why it happens:** "Displayable" sounds like the flag that makes the agent use a value. The Metadata API Developer Guide says at least one output property must set `copilotAction:isUsedByPlanner` to true "or else the planner returns random responses".

**Correct pattern:** Set `isUsedByPlanner` true on every output the agent reasons with; set `isDisplayable` true only on outputs to show the user. See `references/metadata-examples.md` for a complete schema.

**Detection hint:** An output `schema.json` with no `"copilotAction:isUsedByPlanner": true`.
