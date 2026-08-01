# LLM Anti-Patterns — Webhook Inbound Patterns

Common mistakes AI coding assistants make when generating or advising on inbound webhook patterns in Salesforce.

## Anti-Pattern 1: Parsing Body Before HMAC Verification

**What the LLM generates:** Apex code that calls `JSON.deserializeUntyped(req.requestBody.toString())` before computing the HMAC signature.

**Why it happens:** LLMs naturally want to extract the payload data early. They do not know that HMAC verification requires the raw bytes.

**Correct pattern:**
```apex
// WRONG: parse before HMAC
Map<String,Object> payload = (Map<String,Object>) JSON.deserializeUntyped(rawBody);
String computed = computeHmac(JSON.serialize(payload), secret); // WRONG hash

// CORRECT: HMAC over raw body string, parse after
String rawBody = req.requestBody.toString();
if (!verifyHmac(rawBody, signature, secret)) { return; }
Map<String,Object> payload = (Map<String,Object>) JSON.deserializeUntyped(rawBody);
```

**Detection hint:** Any HMAC computation that is not directly called on `req.requestBody.toString()` as the first step after getting the body.

---

## Anti-Pattern 2: Hardcoding the Shared Secret in Apex

**What the LLM generates:** Apex code with the shared secret as a string literal: `private static final String SECRET = 'abc123secret';`

**Why it happens:** LLMs generate the simplest working code and do not consider secret rotation requirements.

**Correct pattern:**
```apex
// WRONG
private static final String SECRET = 'hardcoded-secret';

// CORRECT: stored in Custom Metadata
String secret = [SELECT Value__c FROM Webhook_Config__mdt
                 WHERE DeveloperName = 'StripeSigningSecret' LIMIT 1].Value__c;
```

**Detection hint:** Any string literal in Apex that looks like a secret, API key, or HMAC key.

---

## Anti-Pattern 3: Not Implementing Idempotency

**What the LLM generates:** A webhook handler that directly processes the payload and creates/updates records without checking if the event was already processed.

**Why it happens:** LLMs generate the happy-path implementation. Retry handling is a non-obvious operational concern.

**Correct pattern:**
```apex
// WRONG: no idempotency check
Database.insert(new Order__c(ExternalId__c = eventId, /* ... */));

// CORRECT: upsert on External ID = idempotent
Webhook_Event__c eventRecord = new Webhook_Event__c(
    Event_Id__c = eventId,
    Status__c = 'Processing'
);
Database.UpsertResult result = Database.upsert(eventRecord, Webhook_Event__c.Event_Id__c);
if (!result.isCreated()) {
    return; // Already processed — skip
}
```

**Detection hint:** Any webhook handler that uses `Database.insert()` with a unique event ID without checking for duplicates first.

---

## Anti-Pattern 4: Missing Salesforce Site Guest User Apex Access

**What the LLM generates:** Instructions to create a Salesforce Site and configure the URL, without mentioning that the Apex class must be added to the Guest User Profile's Apex Class Access.

**Why it happens:** LLMs generate the Site creation steps from documentation but miss the Guest User Profile access step which is a separate Setup screen.

**Correct pattern:** After creating the @RestResource class:
1. Go to Setup > Sites > [Your Site] > Public Access Settings (Guest User Profile)
2. Go to Apex Class Access section
3. Add the @RestResource class

Without this step, all requests to the Site endpoint return 403 Forbidden.

**Detection hint:** Any Salesforce Site webhook setup guide that does not mention "Guest User Profile" or "Apex Class Access."

---

## Anti-Pattern 5: Synchronous Processing for Time-Consuming Events

**What the LLM generates:** A webhook handler that performs all processing (multiple SOQL queries, DML, external callouts) synchronously before returning the HTTP response.

**Why it happens:** Synchronous is the simplest pattern. LLMs do not model the sender's timeout window.

**Correct pattern:**
```apex
// WRONG: all processing synchronous
@HttpPost
global static void handle() {
    // Multiple SOQLs, DML, and callouts here... may exceed 5-10 second timeout
    processEvent(req.requestBody.toString());
    res.statusCode = 200;
}

// CORRECT: enqueue async, respond immediately
@HttpPost
global static void handle() {
    String body = RestContext.request.requestBody.toString();
    if (!verifyHmac(body)) { RestContext.response.statusCode = 401; return; }
    System.enqueueJob(new EventProcessor(body));
    RestContext.response.statusCode = 200;
}
```

**Detection hint:** Any @HttpPost handler that performs more than a simple HMAC check and upsert before returning the response.

---

## Anti-Pattern 6: Comparing HMAC Signatures with `String.equals()` and Labelling It Constant-Time

**What the LLM generates:** a signature check that recomputes the MAC, hex-encodes it, and compares with `==` or `String.equals()` — very often with a comment claiming the comparison is constant-time:

```apex
String expected = 'sha256=' + EncodingUtil.convertToHex(
    Crypto.generateMac('hmacSHA256', Blob.valueOf(body), Blob.valueOf(secret))
);
// Constant-time comparison to prevent timing attacks   <-- the comment is false
return expected.equals(signature);
```

**Why it happens:** the model has learned the *phrase* "use a constant-time comparison to verify HMACs" alongside the *shape* of an equality check, and emits both together. Nothing in Apex flags it: `String.equals()` compiles, passes every functional test, and returns the right boolean. The defect is invisible except under timing measurement, so the comment survives code review. This is the worst class of generated security bug — correct-looking, self-certifying, and wrong.

**Correct pattern:**

```apex
// WRONG: String.equals short-circuits on the first differing character.
// Response latency reveals how many leading chars of a forged signature
// were correct, so an attacker recovers the signature one char per retry.
return expected.equals(signature);

// CORRECT: platform-side verification, no Apex-level comparison at all.
Blob macToVerify = EncodingUtil.convertFromHex(signature.substring(7)); // strip 'sha256='
return Crypto.verifyHMac('hmacSHA256', Blob.valueOf(body), Blob.valueOf(secret), macToVerify);

// CORRECT (only when verifyHMac does not fit the sender's scheme):
// accumulate over every character, test the accumulator once at the end.
Integer diff = expected.length() ^ actual.length();
Integer n = Math.min(expected.length(), actual.length());
for (Integer i = 0; i < n; i++) { diff |= expected.charAt(i) ^ actual.charAt(i); }
return diff == 0;
```

`Crypto.verifyHMac(algorithmName, data, privateKey, macToVerify)` is the documented Apex method for this — valid `algorithmName` values are `hmacMD5`, `hmacSHA1`, `hmacSHA256`, `hmacSHA512`. There is **no** `Crypto.areEqualConstantTime()` on the platform; helpers with that name come from sample blog code, and generating a call to it is a compile error (`Method does not exist or incorrect signature: void areEqualConstantTime(Blob, Blob) from the type Crypto`).

**Detection hint:** grep the diff for `.equals(` or `==` on the same line or within three lines of any of `signature`, `hmac`, `mac`, `digest`, `token`, or `secret`. Independently, grep for the string `constant-time` / `constant time` in a comment and confirm the very next comparison is a fixed-iteration accumulator or a `Crypto.verifyHMac` call — a constant-time *claim* sitting above an `equals()` is the signature of this anti-pattern. Also flag any call to `Crypto.areEqualConstantTime`.
