# LLM Anti-Patterns — Custom Agent Actions Apex

## 1. Generating Single-Object Method Signatures Instead of List-in/List-out

**What the LLM generates wrong:**
```apex
@InvocableMethod(label='Create Case' description='...')
public static Case createCase(CreateCaseInput input) { // Wrong: single input
  return new Case(...);                                 // Wrong: single return
}
```

**Why it happens:** Single-method signatures look cleaner. The LLM optimizes for readability without knowing the platform constraint.

**Correct pattern:** All `@InvocableMethod` methods must use `List<Input>` parameter and `List<Output>` return type, even when only one record is ever processed:
```apex
public static List<CreateCaseOutput> createCase(List<CreateCaseInput> inputs) {
  List<CreateCaseOutput> outputs = new List<CreateCaseOutput>();
  for (CreateCaseInput inp : inputs) { outputs.add(process(inp)); }
  return outputs;
}
```

**Detection hint:** Any `@InvocableMethod` method signature that does not use `List<>` for both parameter and return type.

---

## 2. Throwing Exceptions Instead of Returning Structured Error Output

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

## 3. Omitting `callout=true` on Actions That Make HTTP Requests

**What the LLM generates wrong:**
```apex
@InvocableMethod(label='Get ERP Status' description='...')  // Missing callout=true
public static List<ErpOutput> getErpStatus(List<ErpInput> inputs) {
  HttpRequest req = new HttpRequest();
  req.setEndpoint('callout:ERP/status');
  new Http().send(req); // Will throw at runtime
}
```

**Why it happens:** The LLM knows `@InvocableMethod` syntax but may not associate the `callout=true` modifier with HTTP operations specifically.

**Correct pattern:** `@InvocableMethod(label='...' description='...' callout=true)` whenever the method contains any HTTP callout.

**Detection hint:** Any `new Http().send(req)` inside an `@InvocableMethod` that lacks `callout=true` in the annotation.

---

## 4. Writing Generic or Missing Descriptions on @InvocableVariable

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

## 5. Hardcoding Credentials in Callout Actions

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
