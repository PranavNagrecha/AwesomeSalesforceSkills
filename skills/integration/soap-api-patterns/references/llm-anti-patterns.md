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

## Anti-Pattern 3: Using login() with Username/Password Instead of OAuth Session ID

**What the LLM generates:** SOAP API authentication via the `login()` call with hardcoded username, password, and security token, instead of using an OAuth access token injected into the SOAP session header.

**Why it happens:** The `login()` call is the traditional SOAP API authentication method and appears in most legacy examples. OAuth-based SOAP authentication is less documented.

**Correct pattern:**

```text
SOAP API authentication options:

DEPRECATED — login() with username/password:
  <login>
    <username>user@org.com</username>
    <password>passwordSECURITY_TOKEN</password>
  </login>
  Problems: password in config, breaks on password change, no MFA support

RECOMMENDED — OAuth token in SOAP header:
  1. Obtain access_token via OAuth (JWT Bearer, Client Credentials, etc.)
  2. Set the SessionHeader in SOAP requests:
     <SessionHeader>
       <sessionId>{access_token}</sessionId>
     </SessionHeader>
  3. Set the endpoint to the instance URL from the OAuth response

  The OAuth access_token IS a valid Salesforce session ID for SOAP API.

This separates authentication (OAuth) from API usage (SOAP),
enabling MFA support and credential rotation.
```

**Detection hint:** Flag SOAP API code that calls `login()` with username/password parameters. Look for hardcoded passwords or security tokens in SOAP configuration.

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
