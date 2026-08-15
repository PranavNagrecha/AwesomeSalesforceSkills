# LLM Anti-Patterns — Webhook Signature Verification

Mistakes AI assistants reliably make when asked to "receive a Stripe/GitHub/Twilio
webhook in Salesforce."

## Anti-Pattern 1: Hand-Rolling the Digest Comparison

**What the LLM generates:**

```apex
Blob computed = Crypto.generateMac('hmacSHA256', body, key);
if (EncodingUtil.convertToHex(computed) == providedSignature) {
    // process
}
```

**Why it happens:** `Crypto.generateMac` is the method that appears in almost every
Apex crypto example, including the payment-gateway sample in the Apex Developer
Guide. `verifyHMac` is a sibling method that appears far less often in training
data.

**Correct pattern:**

```
Salesforce ships a verifier. Use it:

  Boolean ok = Crypto.verifyHMac('hmacSHA256', rawBody, secret, providedMac);

Signature (Apex Reference Guide):
  public static Boolean verifyHMac(String algorithmName, Blob data,
                                   Blob privateKey, Blob macToVerify)

Valid algorithmName: hmacMD5, hmacSHA1, hmacSHA256, hmacSHA512.
Choose hmacSHA256 or hmacSHA512 for anything new.

generateMac remains correct for PRODUCING a signature - for example in a test
that builds a valid request. It is the wrong tool for checking one.
```

**Detection hint:** any `==`, `.equals(`, or `String.isNotBlank` comparison
applied to the output of `generateMac`. If `generateMac` appears in a method whose
name contains "verify," "validate," or "check," it is the wrong call.

---

## Anti-Pattern 2: Parsing Before Verifying

**What the LLM generates:**

```apex
Map<String, Object> payload =
    (Map<String, Object>) JSON.deserializeUntyped(RestContext.request.requestBody.toString());
String eventType = (String) payload.get('type');
if (eventType == 'invoice.payment_succeeded') {
    if (isSignatureValid()) { ... }
}
```

**Why it happens:** The prompt is about handling an event, so the model organises
the handler around event type. Verification becomes a step inside the branch rather
than the gate in front of it.

**Correct pattern:**

```
Order of operations is fixed:

  1. read raw body (Blob)
  2. read signature header (case-insensitively)
  3. reject if header absent or malformed
  4. reject if timestamp outside tolerance
  5. verify HMAC over the raw bytes
  6. ONLY NOW deserialise
  7. record idempotently
  8. return 2xx
  9. process asynchronously

Deserialising untrusted input before verification hands an attacker your JSON
parser and any code path the payload can steer.
```

**Detection hint:** a `JSON.deserialize` call that appears textually before the
verification call, or inside a branch whose condition depends on payload content.

---

## Anti-Pattern 3: Re-Serialising the Body to "Canonicalise" It

**What the LLM generates:**

```apex
Object parsed = JSON.deserializeUntyped(req.requestBody.toString());
String canonical = JSON.serialize(parsed);
Blob mac = Crypto.generateMac('hmacSHA256', Blob.valueOf(canonical), key);
```

**Why it happens:** "Canonicalisation" is a real concept in XML signatures and in
some API-signing schemes (AWS SigV4 canonical requests), so the model transfers it
to HMAC-over-body schemes where it is actively harmful.

**Correct pattern:**

```
HMAC-over-body schemes sign EXACT BYTES. There is nothing to canonicalise.

  Blob rawBody = RestContext.request.requestBody;   // sign this, unchanged

JSON.serialize reorders keys, strips whitespace, and normalises numbers. The
regenerated MAC will never match the sender's, so EVERY request fails - which
usually gets "fixed" by deleting the check.

Where a provider signs a derived payload, build the derivation from the raw
body string:
  Stripe:  Blob.valueOf(timestamp + '.' + rawBody.toString())
```

**Detection hint:** `JSON.serialize` anywhere between reading `requestBody` and
calling a Crypto method.

---

## Anti-Pattern 4: Direct Map Lookup on the Header Name

**What the LLM generates:**

```apex
String sig = RestContext.request.headers.get('Stripe-Signature');
```

**Why it happens:** `headers` is a `Map<String, String>` and `get()` is the obvious
accessor. Nothing in the type signals that HTTP header names are case-insensitive
while Apex map keys are not.

**Correct pattern:**

```
Always look headers up case-insensitively. Proxies, load balancers, and the
provider's own client all normalise casing differently, and the failure is
intermittent - which is worse than consistent.

  private static String headerIgnoreCase(Map<String,String> h, String name) {
      if (h == null) { return null; }
      String target = name.toLowerCase();
      for (String k : h.keySet()) {
          if (k.toLowerCase() == target) { return h.get(k); }
      }
      return null;
  }

And write a test that supplies the header in different casing from the handler.
A test using req.addHeader with the handler's own spelling proves nothing.
```

**Detection hint:** `.headers.get('` anywhere in the generated class.

---

## Anti-Pattern 5: Stopping at the Signature (No Replay Protection, No Idempotency)

**What the LLM generates:** a correct verifier followed immediately by
`insert record;` and a `200`.

**Why it happens:** The prompt asked for signature verification, and the model
delivers exactly that. Replay and idempotency are adjacent concerns the user did
not name.

**Correct pattern:**

```
A valid signature proves authenticity and integrity. It does NOT prove freshness
or uniqueness. Add both:

  Replay window - if the provider signs a timestamp, reject outside tolerance
                  (Stripe's documented default is 300 seconds). Check the
                  timestamp BEFORE the HMAC so replay floods are cheap.

  Idempotency   - upsert on the provider's event id against an External Id,
                  Unique field:

      Database.UpsertResult ur = Database.upsert(
          evt, Webhook_Event__c.External_Id__c, false);
      if (ur.isSuccess()) { Processor.enqueue(evt); }

Providers retry on any non-2xx and can redeliver on success. Without
idempotency, one timeout becomes duplicate records.
```

**Detection hint:** a handler with no External Id upsert, or with no timestamp
tolerance check when the provider's header carries a timestamp.

---

## Anti-Pattern 6: Hardcoding the Secret, or Putting It in a Custom Setting

**What the LLM generates:**

```apex
private static final String SECRET = 'whsec_abc123...';
// or
String secret = Webhook_Config__c.getOrgDefaults().Secret__c;
```

**Why it happens:** A constant is the shortest path to working code, and List/
Hierarchy Custom Settings are the pattern models associate with "configuration."

**Correct pattern:**

```
Protected Custom Metadata, retrieved through a small accessor:

  Webhook_Secret__mdt with Secret__c marked Protected
  read via Webhook_Secret__mdt.getAll() - costs no SOQL query

Why not each alternative:
  - String literal: the secret is in source control, in every clone of the
    repo, in every sandbox, and in the deployment log.
  - Custom Setting: readable by any user with access to the setting; appears
    in describe calls and can surface in reports and the API.
  - Named Credential: the right home for OUTBOUND credentials. An inbound
    webhook secret is not a callout credential.

Never echo the secret, the computed MAC, or the raw body in an error response
or a log. A verbose rejection is a forging oracle.
```

**Detection hint:** a string literal beginning `whsec_`, `sk_`, `ghp_`, or similar;
any `__c.getOrgDefaults()` in a security path; any `System.debug` of the body or a
signature header.

---

## Anti-Pattern 7: Assuming `/services/apexrest/` Is Publicly Reachable

**What the LLM generates:** a complete `@RestResource` class with the instruction
"point the provider's webhook at
`https://yourorg.my.salesforce.com/services/apexrest/stripe/v1/`" and nothing about
authentication.

**Why it happens:** From the Apex side the endpoint looks like an ordinary public
REST resource. The session requirement is a platform fact that lives in a different
part of the documentation from `@RestResource`.

**Correct pattern:**

```
Apex REST requires an authenticated session. Webhooks have none. Pick one:

  A) Provider authenticates - Connected App / External Client App, OAuth 2.0
     client credentials flow bound to a dedicated integration user. Preferred
     when the provider supports custom auth headers on outbound webhooks.
     Keep the HMAC check anyway.

  B) Public Salesforce Site - Setup -> Sites -> [site] -> Public Access
     Settings -> Enabled Apex Class Access. The endpoint is then reachable by
     anyone and the HMAC check is the ONLY authentication. Give the guest user
     minimum object access; the handler should write only to a staging object.

Always state which shape the answer assumes, and what the guest user needs.
```

**Detection hint:** an answer containing a `/services/apexrest/` URL with no
mention of a Connected App, a Site, or guest-user Apex class access.

---

## Anti-Pattern 8: Doing the Work Inline and Returning Late

**What the LLM generates:** verify → create records → update related records →
send an email → make a callout → `res.statusCode = 200`.

**Why it happens:** The prompt describes what should happen when the event arrives,
so the model writes it all in the handler.

**Correct pattern:**

```
The handler does two things: verify, and durably record. Then it returns 200.

  Blob raw = req.requestBody;
  ... verify ...
  upsert staging record on External Id
  enqueue Queueable / publish platform event
  res.statusCode = 200;

Providers time out in single-digit seconds and retry on timeout. An eight-second
handler turns one event into repeated deliveries of the same event, each of
which takes eight seconds. Callouts from the handler make this worse: a
synchronous webhook handler that calls out is one slow dependency away from
being permanently unhealthy.

Payload ceiling: "the maximum request or response size is 6 MB for synchronous
Apex or 12 MB for asynchronous Apex."
```

**Detection hint:** a `Http.send`, `Messaging.sendEmail`, or more than one DML
statement between the verification call and the status assignment.
