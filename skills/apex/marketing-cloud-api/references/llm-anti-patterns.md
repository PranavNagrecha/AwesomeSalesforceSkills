# LLM Anti-Patterns — Marketing Cloud API

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud API integrations.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using a Generic or Legacy Base URL Instead of the Tenant-Specific Subdomain

**What the LLM generates:** Code or instructions that use `https://www.exacttargetapis.com`, `https://api.exacttarget.com`, or a shared endpoint without a tenant-specific subdomain prefix.

**Why it happens:** LLMs are trained on older Marketing Cloud documentation and blog posts from the ExactTarget era, where generic endpoints were common. The current tenant-specific subdomain requirement is a more recent change that is underrepresented in training data.

**Correct pattern:**

```
POST https://{{subdomain}}.auth.marketingcloudapis.com/v2/token
POST https://{{subdomain}}.rest.marketingcloudapis.com/interaction/v1/events
```

Where `{{subdomain}}` is the unique MID-based subdomain from the Installed Package API Integration component in Marketing Cloud Setup.

**Detection hint:** Flag any endpoint URL in generated code that does not contain a tenant-specific subdomain (i.e., does not follow the pattern `{something}.auth.marketingcloudapis.com` or `{something}.rest.marketingcloudapis.com`). Also flag `exacttarget.com` domain references.

---

## Anti-Pattern 2: Using Legacy Fuel Authentication Instead of OAuth 2.0 Client Credentials

**What the LLM generates:** Code that sends a `clientId` and `clientSecret` to a legacy AppCenter Fuel endpoint (e.g., `https://auth.exacttargetapis.com/v1/requestToken`) or references legacy `AppID`/`AppSecret` style credentials.

**Why it happens:** Legacy Fuel authentication was the standard for years and dominates older Marketing Cloud integration tutorials. LLMs surface this pattern frequently because it appears in a large volume of training documentation.

**Correct pattern:**

```json
POST https://{{subdomain}}.auth.marketingcloudapis.com/v2/token
{
  "grant_type": "client_credentials",
  "client_id": "{{clientId}}",
  "client_secret": "{{clientSecret}}"
}
```

Credentials come from an Installed Package → API Integration component, not from AppCenter or a legacy application entry.

**Detection hint:** Flag any reference to `/v1/requestToken`, `auth.exacttargetapis.com`, `AppID`, `AppSecret`, or Fuel SDK patterns in generated integration code.

---

## Anti-Pattern 3: Using the Journey Key as EventDefinitionKey for Journey Injection

**What the LLM generates:** Code that retrieves the journey's ID or key from the Journey Builder URL or journey metadata and uses it as the `EventDefinitionKey` in the `/interaction/v1/events` payload.

**Why it happens:** The journey key is the most visible identifier in Journey Builder's UI and URL. LLMs conflate "journey identifier" with "entry event identifier" because the distinction is not obvious from the API name alone.

**Correct pattern:**

```json
{
  "ContactKey": "subscriber@example.com",
  "EventDefinitionKey": "APIEvent-a1b2c3d4-...",
  "Data": { ... }
}
```

The `EventDefinitionKey` must come from the entry source settings within the specific journey — it follows the `APIEvent-{{GUID}}` format and is found by clicking the API entry event block in Journey Builder, not from the journey's own properties.

**Detection hint:** Flag any `EventDefinitionKey` value in generated code that does not follow the `APIEvent-` prefix pattern, or any code that derives the EventDefinitionKey from a journey URL parameter or Journey metadata API response.

---

## Anti-Pattern 4: Treating HTTP 201 from Journey Injection as Confirmed Contact Entry

**What the LLM generates:** Code or guidance stating that a 201 response from `/interaction/v1/events` means the contact successfully entered the journey, with no further verification recommended.

**Why it happens:** The standard HTTP semantics of 201 (Created) imply resource creation was successful. LLMs apply standard REST semantics here, unaware that Marketing Cloud's journey injection is asynchronous and the 201 only means the request was queued — not that the contact entered the journey.

**Correct pattern:**

```
// HTTP 201 = request accepted (queued), NOT confirmed journey entry
// Field name mismatches, inactive journeys, and schema validation errors
// cause silent contact drops AFTER a 201 response.
//
// Verify contact entry in Journey Builder → [Journey] → Contact History
// after testing in a non-production environment.
```

Always include a verification step against Journey Builder's contact history, and document in code comments that 201 is acceptance, not confirmation.

**Detection hint:** Flag any code or prose that equates a 201 response from the journey injection endpoint with successful or confirmed contact entry. Look for comments like "201 means success" or "contact entered the journey" adjacent to response code checks.

---

## Anti-Pattern 5: Firing a Triggered Send Without Verifying or Starting the TriggeredSendDefinition

**What the LLM generates:** Code that jumps directly to `POST /messaging/v1/messageDefinitionSends/key:{ExternalKey}/send` without any mention of the TriggeredSendDefinition lifecycle (create → start → send), or that assumes the definition is already started.

**Why it happens:** The triggered send API documentation focuses heavily on the send endpoint itself, and LLMs compress the three-step lifecycle into a one-step assumption. The definition management step is often in a different documentation section and is underrepresented in code examples.

**Correct pattern:**

```
Step 1: Create TriggeredSendDefinition (via SOAP API or MC Setup UI)
        — set ExternalKey, associated email, and subscriber list

Step 2: Start the definition
        — status must be 'Running' (Active) before any sends
        — verify in Email Studio → Triggered Sends or via SOAP TriggeredSendStatus

Step 3: Fire the send via REST
POST https://{{subdomain}}.rest.marketingcloudapis.com/messaging/v1/messageDefinitionSends/key:{ExternalKey}/send
{
  "To": {
    "Address": "recipient@example.com",
    "SubscriberKey": "recipient@example.com",
    "ContactAttributes": { "SubscriberAttributes": { "FirstName": "Jane" } }
  }
}
```

**Detection hint:** Flag any triggered send implementation that does not mention or include a step for verifying or starting the TriggeredSendDefinition before the first send. Also flag code where the ExternalKey is assumed to be valid without a status check.

---

## Anti-Pattern 6: Requesting a New Token on Every API Call

**What the LLM generates:** Code that calls the token endpoint inside a loop, inside a trigger handler per-record, or at the top of every individual API method without caching — acquiring a new `access_token` for every single request.

**Why it happens:** LLMs generate straightforward "authenticate then call" code patterns because they are simpler to write. Token caching requires state management that LLMs often omit for brevity, especially when generating short code snippets.

**Correct pattern:**

```apex
// Cache token in a static variable or Custom Setting with expiry tracking
// Re-acquire only when token is expired or about to expire
private static String cachedToken;
private static DateTime tokenExpiry;

public static String getToken() {
    if (cachedToken != null && DateTime.now() < tokenExpiry.addMinutes(-2)) {
        return cachedToken;
    }
    // ... acquire new token, set cachedToken and tokenExpiry
    return cachedToken;
}
```

Tokens are valid for approximately 20 minutes (`expires_in` seconds in the response). Cache and reuse within the validity window. In Apex, use a static variable for within-transaction caching or a Custom Setting for cross-transaction caching.

**Detection hint:** Flag any code where a token acquisition call appears inside a loop, inside a trigger context without caching logic, or where there is no reference to `expires_in` or token expiry management.
