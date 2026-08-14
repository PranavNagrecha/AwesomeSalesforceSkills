# LLM Anti-Patterns — SOAP API Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce SOAP API integration patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending SOAP API for New Integrations Without Evaluating REST

**What the LLM generates:** "Use the SOAP API to query and update Salesforce records" for new integration projects without noting that REST API is generally preferred for new development due to simpler payload format, better tooling support, and wider adoption.

**Why it happens:** SOAP API has decades of training data from enterprise integration scenarios. LLMs recommend it without evaluating whether REST would be simpler and more maintainable.

**Correct pattern:**

```text
SOAP vs REST API decision:

Use REST API when:
- Building a new integration from scratch
- Consumer is a modern web/mobile/cloud application
- JSON payload format is preferred
- Team has REST API experience

Use SOAP API when:
- Integrating with a .NET or Java system that prefers WSDL-generated stubs
- Using Metadata API for deployment (Metadata API is SOAP-only)
- Working with legacy middleware that only supports SOAP
- Need the describe() call for metadata introspection
- Existing integration already uses SOAP (avoid unnecessary rewrite)

Both APIs have the same governor limits (daily API request allocation).
Both support OAuth authentication.
```

**Detection hint:** Flag SOAP API recommendations for new integrations without a REST API comparison. Look for missing justification for choosing SOAP over REST.

---

## Anti-Pattern 2: Confusing Enterprise WSDL with Partner WSDL

**What the LLM generates:** "Download the Enterprise WSDL and use it for your cross-org integration" when the Partner WSDL would be more appropriate for integrations that must work across multiple orgs with different schemas.

**Why it happens:** Enterprise WSDL is mentioned first in most documentation. LLMs do not consistently distinguish between the two WSDLs and their appropriate use cases.

**Correct pattern:**

```text
Enterprise WSDL vs Partner WSDL:

Enterprise WSDL:
- Strongly typed: generated specifically for YOUR org's schema
- Contains concrete sObject types (Account, Contact, Custom__c)
- Must be regenerated when custom objects/fields change
- Best for: single-org integrations with stable schema
- Simpler to code against (IDE auto-completion, compile-time checks)

Partner WSDL:
- Loosely typed: generic sObject structure
- Works with any org without regeneration
- Uses generic field access: sObject.getField("Name")
- Best for: ISV products, cross-org integrations, dynamic schema access
- More code required (runtime field access instead of typed properties)

Common mistake: using Enterprise WSDL for an AppExchange product
that must install in customer orgs with different schemas.
```

**Detection hint:** Flag Enterprise WSDL recommendations for multi-org, ISV, or AppExchange integration contexts. Check whether Partner WSDL is more appropriate.

---

## Anti-Pattern 3: Handing the User a `login()` Snippet That Is Already Dead at v65.0+

**What the LLM generates:** The classic SOAP login envelope as *the* way to authenticate a middleware or ETL job — typically pointed at the newest API version it knows, e.g. `https://login.salesforce.com/services/Soap/u/65.0` with `<username>` and `<password+token>` — then tells the user to reuse the returned `sessionId` and `serverUrl`.

**Why it happens:** `login()` is the canonical "get a session id" snippet across decades of training data. Two changes post-date most corpora: the call was removed in API 65.0, and newly created orgs gate it behind a permission the model has never heard of. So the model confidently emits a snippet that cannot work, and — worse — cannot explain why a brand-new scratch org rejects a `login()` that succeeds against an older production org.

**Why it matters:** At v65.0+ that call never succeeds. On 31.0–64.0 it works but is on a fixed countdown to Summer '27. The model also reaches for *connected apps* as the replacement when the prescribed replacement is an **external client app**.

**Correct pattern:**

```text
SOAP API authentication options:

REMOVED at API 65.0+ / RETIRES Summer '27 — login() with username/password:
  <login>
    <username>user@org.com</username>
    <password>passwordSECURITY_TOKEN</password>
  </login>
  v65.0+          : HTTP 500, exception code UNSUPPORTED_API_VERSION
  v31.0-64.0      : works only until Summer '27 is released
  new orgs        : running user needs the "Any API Auth" permission
  Other problems  : password in config, breaks on password change, no MFA support

REQUIRED — OAuth token in SOAP header:
  1. Register an EXTERNAL CLIENT APP (not a legacy connected app)
  2. Obtain access_token via OAuth (JWT Bearer, Client Credentials,
     or Web Server flow for browser-based integrations)
  3. Set the SessionHeader in SOAP requests:
     <SessionHeader>
       <sessionId>{access_token}</sessionId>
     </SessionHeader>
  4. Set the endpoint to the instance URL from the OAuth response

  The OAuth access_token IS a valid Salesforce session ID for SOAP API,
  and SOAP API now accepts JWT-based access tokens in that same
  sessionId header element.

Only the auth step changes: query(), create(), upsert(), queryMore()
are all unaffected. This also enables MFA support and credential rotation.
```

**Detection hint:** Flag any SOAP code calling `login()` with username/password. Two extra checks the model routinely misses: (a) if the endpoint URL is v65.0 or later, the snippet is broken *right now*, not merely dated; (b) if the replacement it proposes is a "connected app", correct it to an external client app. Do not let "it still works on 64.0" stand as a recommendation — say the deadline out loud.

---

## Anti-Pattern 4: Not Handling SOAP API Session Expiration

**What the LLM generates:** SOAP client code that obtains a session ID once and reuses it indefinitely without handling `INVALID_SESSION_ID` faults that occur when the session expires.

**Why it happens:** Session management is an operational concern that tutorials skip. LLMs generate authentication code without the error handling and token refresh logic needed for long-running integrations.

**Correct pattern:**

```text
SOAP API session lifecycle:

Default session timeout: 2 hours (configurable via Session Settings)
Session can expire due to:
- Timeout (no activity for the configured period)
- Admin session revocation
- Password change
- Security policy enforcement

Error handling:
  try {
      // SOAP API call
      QueryResult result = binding.query("SELECT Id FROM Account");
  } catch (InvalidSessionIdFault e) {
      // Session expired — re-authenticate
      loginResult = binding.login(username, password);
      binding.setSessionId(loginResult.getSessionId());
      binding.setEndpoint(loginResult.getServerUrl());
      // Retry the original call
      result = binding.query("SELECT Id FROM Account");
  }

For OAuth-based sessions:
  - Check for INVALID_SESSION_ID fault
  - Use refresh_token to obtain a new access_token
  - Update the SessionHeader and retry
```

**Detection hint:** Flag SOAP API client code that does not handle `INVALID_SESSION_ID` or `InvalidSessionIdFault`. Look for missing session renewal logic.

---

## Anti-Pattern 5: Ignoring SOAP API Batch Size Limits

**What the LLM generates:** "Call create() with all 5,000 records at once" without noting that SOAP API operations are limited to 200 records per call for create/update/upsert/delete.

**Why it happens:** LLMs do not consistently apply Salesforce-specific batch size limits to SOAP API operations. General SOAP training data does not include these constraints.

**Correct pattern:**

```text
SOAP API operation limits:

create(), update(), upsert(), delete():
  Maximum 200 records per call

query():
  Returns up to 2,000 records per response (use queryMore() for pagination)
  Maximum 50,000 records total via queryMore() loop

retrieve():
  Maximum 2,000 IDs per call

For operations over 200 records:
  1. Chunk the data into batches of 200
  2. Call create/update/delete for each batch
  3. Check SaveResult[] for per-record success/failure
  4. Implement retry logic for transient failures

For large volumes (>10,000 records):
  Use Bulk API instead of SOAP API for better throughput.
```

**Detection hint:** Flag SOAP API create/update/delete calls with more than 200 records per invocation. Check for missing batch chunking logic.
