# LLM Anti-Patterns — Apex JSON Serialization

Common mistakes AI coding assistants make when generating or advising on Apex JSON serialization.

## Anti-Pattern 1: Omitting suppressApexObjectNulls

**What the LLM generates:**
```apex
String body = JSON.serialize(payload);
```

**Why it happens:** LLMs trained on Java/JavaScript patterns default to the single-argument `serialize` form. The Salesforce-specific second argument for null suppression is underrepresented in general training data.

**Correct pattern:**
```apex
String body = JSON.serialize(payload, true); // suppress null fields
```

**Detection hint:** Look for `JSON.serialize(` with no second argument in callout payload construction. If the downstream API uses strict schema validation, this will fail at runtime.

---

## Anti-Pattern 2: Calling JSON.deserialize without catching TypeException

**What the LLM generates:**
```apex
MyClass result = (MyClass) JSON.deserialize(response.getBody(), MyClass.class);
```

**Why it happens:** LLMs follow the happy path and assume the JSON shape matches the Apex class. External APIs that change their schema cause uncaught runtime exceptions.

**Correct pattern:**
```apex
MyClass result;
try {
    result = (MyClass) JSON.deserialize(response.getBody(), MyClass.class);
} catch (JSONException e) {
    // malformed JSON
} catch (System.TypeException e) {
    // type mismatch — log and handle
}
```

**Detection hint:** Search for `JSON.deserialize` calls outside a try/catch block in callout handlers or webhook receivers.

---

## Anti-Pattern 3: Casting deserializeUntyped result without checking type

**What the LLM generates:**
```apex
Map<String, Object> root = (Map<String, Object>) JSON.deserializeUntyped(body);
// Then directly: List<Object> items = (List<Object>) root.get('items');
// Without null check
String name = (String) ((Map<String,Object>) root.get('customer')).get('name');
```

**Why it happens:** LLMs chain casts without null guards, assuming the JSON always contains the expected keys and types.

**Correct pattern:**
```apex
Map<String, Object> root = (Map<String, Object>) JSON.deserializeUntyped(body);
if (root.containsKey('customer') && root.get('customer') != null) {
    Map<String, Object> customer = (Map<String, Object>) root.get('customer');
    String name = (String) customer.get('name');
}
```

**Detection hint:** Chained casts on `deserializeUntyped` results without null/key checks. Search for `(Map<String,Object>) ... .get(` patterns without preceding `containsKey` guards.

---

## Anti-Pattern 4: Expecting static fields in JSON.serialize output

**What the LLM generates:**
```apex
public class Config {
    public static String version = '2.0';
    public String data;
}
// Then: JSON.serialize(new Config()) and expecting "version" in output
```

**Why it happens:** Java and other languages serialize static fields in some frameworks. LLMs apply this pattern to Apex where it silently fails — static fields are excluded.

**Correct pattern:**
```apex
public class Config {
    public String version = '2.0'; // instance field, not static
    public String data;
}
```

**Detection hint:** `static` fields in Apex classes that are then passed to `JSON.serialize`. The serialization will silently omit the static field with no error.

---

## Anti-Pattern 5: Using JSON.deserialize when JSON.deserializeStrict is needed

**What the LLM generates:**
```apex
// Receiving webhook — want to reject unknown fields for security
WebhookPayload p = (WebhookPayload) JSON.deserialize(body, WebhookPayload.class);
```

**Why it happens:** LLMs default to `JSON.deserialize` as the "standard" deserialization method. When strict schema enforcement is required (e.g., security-sensitive webhooks where extra fields could indicate injection or schema drift), the strict variant is the correct choice.

**Correct pattern:**
```apex
// Rejects JSON with extra fields not in WebhookPayload
WebhookPayload p = (WebhookPayload) JSON.deserializeStrict(body, WebhookPayload.class);
```

**Detection hint:** Security-sensitive deserialization contexts (webhook handlers, inbound REST endpoints) using `JSON.deserialize` where schema adherence should be enforced.
