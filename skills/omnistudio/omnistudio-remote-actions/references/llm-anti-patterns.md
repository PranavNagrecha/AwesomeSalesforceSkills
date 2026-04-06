# LLM Anti-Patterns — OmniStudio Remote Actions

Common mistakes AI coding assistants make when generating or advising on OmniStudio Remote Actions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the Wrong VlocityOpenInterface Namespace

**What the LLM generates:**

```apex
global class MyAction implements VlocityOpenInterface2 {
```

**Why it happens:** Training data contains both `vlocity_cmt.VlocityOpenInterface2` and `omnistudio.VlocityOpenInterface2`. LLMs frequently omit the namespace entirely or use the managed-package namespace in a native OmniStudio org. Without the namespace prefix, the class does not compile. With the wrong namespace, it compiles but fails at runtime.

**Correct pattern:**

```apex
// For native OmniStudio orgs:
global class MyAction implements omnistudio.VlocityOpenInterface2 {

// For managed-package (Vlocity CMT) orgs:
global class MyAction implements vlocity_cmt.VlocityOpenInterface2 {
```

**Detection hint:** Check for `implements VlocityOpenInterface2` without a namespace prefix, or confirm the namespace matches the org's installed package.

---

## Anti-Pattern 2: Returning Data Instead of Populating outputMap

**What the LLM generates:**

```apex
global Object invokeMethod(String methodName, Map<String, Object> inputMap,
                           Map<String, Object> outputMap, Map<String, Object> options) {
    Map<String, Object> result = new Map<String, Object>();
    result.put('Status', 'Success');
    result.put('Data', queryResults);
    return result;  // Wrong — framework ignores this
}
```

**Why it happens:** Standard Apex patterns and Aura controller methods return data as the method return value. LLMs default to this familiar pattern. The `VlocityOpenInterface2` contract is unusual in that data must go into the `outputMap` parameter.

**Correct pattern:**

```apex
global Object invokeMethod(String methodName, Map<String, Object> inputMap,
                           Map<String, Object> outputMap, Map<String, Object> options) {
    outputMap.put('Status', 'Success');
    outputMap.put('Data', queryResults);
    return null;
}
```

**Detection hint:** Look for `return` statements that return a Map or Object containing business data instead of `return null`.

---

## Anti-Pattern 3: Recommending Fire and Forget Without Checking Data Dependencies

**What the LLM generates:**

```
Set invoke mode to "Fire and Forget" for better performance.
```

**Why it happens:** LLMs optimize for user-perceived speed and recommend async patterns by default. They do not trace the data dependency graph of the OmniScript to determine whether downstream steps read the action's output. "Fire and Forget" sounds like a performance best practice.

**Correct pattern:**

```
Use Promise invoke mode. The action's output (QuoteResult) is read by Step 5's
display elements. Fire and Forget would risk the data not being available when
Step 5 renders.

Use Fire and Forget ONLY when the action is a side effect (logging, audit write)
and no downstream step reads its output.
```

**Detection hint:** If the recommendation includes "Fire and Forget," verify that no subsequent step references the action's Response JSON Path node.

---

## Anti-Pattern 4: Omitting Send JSON Path (Sending Full OmniScript JSON)

**What the LLM generates:**

```
Configure the Integration Procedure Action:
  IP Name: CalculatePrice_IP
  Response JSON Path: PriceResult
  (Send JSON Path not mentioned)
```

**Why it happens:** LLMs often skip optional configuration fields. Send JSON Path defaults to blank, which sends the entire step node — including framework-internal keys and unrelated user data. Training examples frequently show minimal configuration.

**Correct pattern:**

```
Configure the Integration Procedure Action:
  IP Name: CalculatePrice_IP
  Send JSON Path: PricingInput
  Response JSON Path: PriceResult
```

**Detection hint:** Check for Remote Action configurations where Send JSON Path is missing or explicitly blank. Flag it as a potential data-leakage and payload-bloat issue.

---

## Anti-Pattern 5: Using Public Instead of Global Access Modifier

**What the LLM generates:**

```apex
public class MyAction implements omnistudio.VlocityOpenInterface2 {
    public Object invokeMethod(String methodName, Map<String, Object> inputMap,
                               Map<String, Object> outputMap, Map<String, Object> options) {
```

**Why it happens:** Apex best practices discourage `global` access unless building managed packages. LLMs follow this general guidance without recognizing that `VlocityOpenInterface2` requires `global` on both the class and the method for the OmniStudio framework to bind at runtime.

**Correct pattern:**

```apex
global class MyAction implements omnistudio.VlocityOpenInterface2 {
    global Object invokeMethod(String methodName, Map<String, Object> inputMap,
                               Map<String, Object> outputMap, Map<String, Object> options) {
```

**Detection hint:** Search for `public class` or `public Object invokeMethod` in VlocityOpenInterface2 implementations. Both the class and method must be `global`.

---

## Anti-Pattern 6: Hardcoding External Endpoints in Apex Remote Action

**What the LLM generates:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.example.com/v2/pricing');
req.setHeader('Authorization', 'Bearer ' + apiKey);
```

**Why it happens:** LLMs generate working code with the simplest approach. Named Credentials require org-level configuration that the LLM cannot verify, so it defaults to hardcoded values that "work" in the current context.

**Correct pattern:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Pricing_API/v2/pricing');
// Named Credential handles authentication automatically
```

**Detection hint:** Look for `setEndpoint` calls with full URLs (starting with `https://`) or `setHeader('Authorization', ...)` in Apex Remote Action classes. Both indicate missing Named Credential usage.

---

## Anti-Pattern 7: Generating Aura-Style Remote Action Configuration

**What the LLM generates:**

```javascript
// In the OmniScript, call the Apex method:
var action = component.get("c.getQuote");
action.setParams({ accountId: this.accountId });
$A.enqueueAction(action);
```

**Why it happens:** Training data contains far more Aura controller action patterns than OmniStudio Remote Action configurations. LLMs confuse the two patterns, especially when the prompt says "remote action" — a term also used in Visualforce and Aura contexts.

**Correct pattern:**

OmniStudio Remote Actions are configured declaratively in the OmniScript designer, not through JavaScript or Aura controller syntax. The configuration is set in the action element's properties panel (type, class name, method name, JSON paths, invoke mode).

**Detection hint:** Look for `$A.enqueueAction`, `component.get("c.`)`, or `@AuraEnabled` in code generated for an OmniStudio Remote Action context. These are Aura patterns, not OmniStudio patterns.
