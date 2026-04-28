# LLM Anti-Patterns — Apex Secrets and Protected CMDT

Common mistakes AI coding assistants make when generating or advising on Apex secret storage. These help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting `private static final String API_KEY = '...'` "for now"

**What the LLM generates:**

```apex
public class StripeClient {
    private static final String API_KEY = 'sk_live_REPLACE_ME';
    // ... rest of class
}
```

**Why it happens:** Java/Python training data is full of "constants at the top of the file" patterns. The LLM treats secrets as configuration constants. The placeholder lulls reviewers into thinking the value will be replaced before commit — it rarely is.

**Correct pattern:**

```apex
public class StripeClient {
    private static String apiKey() {
        return SecretsProvider.getSecret('Stripe_Api_Key');  // backed by Protected CMDT
    }
}
```

**Detection hint:** Regex `(api_?key|secret|token|password)\s*=\s*'[^']{8,}'` against `.cls` files. The checker script in this skill implements exactly this.

---

## Anti-Pattern 2: "Store it in a Custom Setting" without specifying Protected + managed package

**What the LLM generates:** "You can store the API key in a Custom Setting so you don't have to redeploy when it rotates."

**Why it happens:** Custom Settings appear in Salesforce documentation as the canonical "configuration storage" mechanism. The LLM omits the two crucial qualifiers — **Protected** visibility AND **managed-package** packaging — because they're a paragraph deeper in the docs and absent from most blog tutorials.

**Correct pattern:**

> Store the API key in a **Hierarchy Custom Setting marked Protected**, packaged inside a managed package with a namespace. In the subscriber org, the value is readable only by Apex inside the namespace. Without managed packaging the Protected designation provides no protection — any System Admin in the source org can read it.

**Detection hint:** Search assistant output for "custom setting" near "API key" or "secret" without the words "Protected" and "managed package" within the same paragraph.

---

## Anti-Pattern 3: Recommending Protected CMDT in an unmanaged DX project as if subscriber protection applies

**What the LLM generates:** "Use Protected Custom Metadata. Mark the type Protected and the values will be hidden from admins."

**Why it happens:** The LLM has read the Salesforce help article snippet "Protected components are hidden from subscribers" and internalized it as a general property of "Protected", missing the managed-package precondition.

**Correct pattern:**

> Protected CMDT hides values **only from subscribers of a managed package**. In an unmanaged DX project, in the packaging org, or in any org where the user has Customize Application + View All Data, the values are fully visible. If your project is unmanaged, Protected CMDT is **not** a secret-storage mechanism — use an off-platform vault accessed via Named Credential.

**Detection hint:** Look for assistant output that recommends Protected CMDT without first asking or asserting that the code lives in a managed (namespaced) package.

---

## Anti-Pattern 4: Adding `System.debug` of the secret during troubleshooting

**What the LLM generates:**

```apex
String key = SecretsProvider.getSecret('Stripe_Api_Key');
System.debug('Retrieved key: ' + key);  // for debugging
HttpRequest req = new HttpRequest();
req.setHeader('Authorization', 'Bearer ' + key);
```

**Why it happens:** Generic debugging guidance — "log the value to verify it's set correctly" — applied without secret-awareness.

**Correct pattern:**

```apex
String key = SecretsProvider.getSecret('Stripe_Api_Key');
System.debug('Stripe key length=' + (key == null ? 0 : key.length()));
// or, if comparing across environments:
System.debug('Stripe key sha256=' + EncodingUtil.convertToHex(
    Crypto.generateDigest('SHA-256', Blob.valueOf(key))
));
```

**Detection hint:** Regex `System\.debug\([^)]*\b(key|secret|token|password|credential)\b[^)]*\)` against `.cls`. Whitelist `.length()` and `Crypto.generateDigest`.

---

## Anti-Pattern 5: Generating a `customMetadata/*.md-meta.xml` record with the secret value populated

**What the LLM generates:**

```xml
<!-- force-app/main/default/customMetadata/Webhook_Signing_Key.Outbound.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <values>
        <field>Value__c</field>
        <value xsi:type="xsd:string">sk_live_a1b2c3d4e5f6...</value>
    </values>
</CustomMetadata>
```

**Why it happens:** The LLM treats CMDT records as "data" to be deployed alongside code, and helpfully fills in the Value__c field with the placeholder it was given. It does not realize this file is committed to source control by default.

**Correct pattern:** Do not generate the record file at all. Generate the type definition, the Apex retrieval class, and a `.forceignore` entry that excludes records of this type. Document that the record must be created post-deploy via a controlled admin procedure.

```
# .forceignore
**/customMetadata/Webhook_Signing_Key.*.md-meta.xml
```

**Detection hint:** Scan generated `customMetadata/*.md-meta.xml` for fields named `Api_Key__c`, `Secret__c`, `Token__c`, `Password__c`, `Signing_Key__c` with non-placeholder values. The checker script in this skill flags this as P0.

---

## Anti-Pattern 6: Using `Crypto.encrypt`/`decrypt` with a hardcoded key parameter

**What the LLM generates:**

```apex
Blob key = Blob.valueOf('mysecretkey12345');
Blob iv  = Blob.valueOf('1234567890123456');
Blob enc = Crypto.encryptWithManagedIV('AES256', key, Blob.valueOf(plain));
```

**Why it happens:** Tutorials often show `Blob.valueOf('...')` as the simplest way to construct a key Blob. The LLM does not flag that this defeats the purpose of encryption.

**Correct pattern:** Use `Crypto.generateAesKey(256)` once at install time, store the resulting Blob via Protected CMDT (base64-encoded in the Long Text Area) or, preferably, in an off-platform KMS. Never construct the key from a string literal.

**Detection hint:** Regex `Blob\.valueOf\s*\(\s*'[^']*'\s*\)\s*[,)].*Crypto\.(encrypt|decrypt)` against `.cls`.
