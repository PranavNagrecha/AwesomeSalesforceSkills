# Gotchas — Webhook Inbound Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: HMAC Must Be Computed Over Raw Bytes, Not Parsed JSON

**What happens:** Developers parse the JSON body first, then re-serialize it and compute HMAC over the serialized string. The result never matches the sender's signature because JSON serialization changes key ordering, whitespace, or encoding.

**When it occurs:** Any Apex webhook handler that calls `JSON.deserializeUntyped(rawBody)` before computing the HMAC signature.

**How to avoid:** Always compute the HMAC over `req.requestBody.toString()` — the original raw string exactly as received — before any parsing. The signature is computed over the exact bytes the sender transmitted.

---

## Gotcha 2: Salesforce Site Guest User Needs Explicit Apex Class Access

**What happens:** The Apex class is created, the Salesforce Site is activated, but the endpoint returns 403 Forbidden for all requests.

**When it occurs:** The guest user profile for the Salesforce Site does not have the Apex class explicitly listed in its Apex Class Access section, even if the class is visible from the org perspective.

**How to avoid:** After creating the Apex class, navigate to Setup > Sites > [Your Site] > Guest User Profile > Apex Class Access. Add the @RestResource class explicitly. Without this, the guest user cannot execute the class.

---

## Gotcha 3: The 5-Second Response Window Is Not Always Enforced But Should Be Treated as Absolute

**What happens:** A synchronous webhook handler works in testing but randomly fails in production because the sender's timeout is shorter than expected, or Salesforce processing varies under load.

**When it occurs:** Any webhook handler that performs complex SOQL, DML, or external callouts synchronously before returning the HTTP response.

**How to avoid:** Treat 5 seconds as the absolute maximum for the synchronous response. For any processing that involves non-trivial SOQL (more than 1-2 queries), DML, or external callouts, enqueue a Queueable immediately and return 200. Never perform the business logic synchronously.

---

## Gotcha 4: DML-Before-Callout Restriction in Queueable

**What happens:** The Queueable processing a webhook attempts to call an external system (callout) but has already executed DML to save the event. The transaction fails with `System.CalloutException: You have uncommitted work pending.`

**When it occurs:** Any Queueable that performs DML (saving the event record) before making a callout.

**How to avoid:** Reorder operations: perform callouts first, then DML. Or split into two Queueables: first Queueable does the callout, chains a second Queueable to do DML after the callout result is known.
