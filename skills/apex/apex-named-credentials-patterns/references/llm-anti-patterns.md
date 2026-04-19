# LLM Anti-Patterns — Apex Named Credentials Patterns

Common mistakes AI coding assistants make when generating or advising on Apex Named Credentials patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using a Hardcoded Endpoint Instead of the `callout:` Prefix

**What the LLM generates:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.acme-corp.com/v2/customers/' + customerId);
req.setHeader('Authorization', 'Bearer ' + System.Label.Acme_Token);
```

**Why it happens:** LLMs trained on general Java/HTTP examples default to constructing full URLs with manually injected auth headers, because that is the most common pattern in general web programming. The Salesforce-specific `callout:` convention is not represented in general training data.

**Correct pattern:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:AcmeCorpNC/v2/customers/' + customerId);
req.setMethod('GET');
req.setTimeout(30000);
// Auth injected via Named Credential custom header formula — no setHeader() for auth
```

**Detection hint:** Look for `req.setEndpoint('https://` — any full HTTPS URL in `setEndpoint()` is a red flag. Also look for `req.setHeader('Authorization'` combined with a credential source.

---

## Anti-Pattern 2: Using Legacy Model Syntax Assumptions in an Enhanced-Model Org

**What the LLM generates:**

```apex
// LLM advises configuring "Authentication Protocol" on the Named Credential
// and expects all auth config to be on the Named Credential record itself.
// In enhanced orgs the Named Credential has no auth protocol field.
```

The LLM might also suggest querying `NamedCredential` SObject fields that don't exist in the enhanced model, or give setup instructions that only apply to legacy Named Credentials (pre-Spring '22).

**Why it happens:** Training data about Named Credentials is predominantly legacy-model documentation and blog posts written before Spring '22. Enhanced model documentation is newer and less represented.

**Correct pattern:** Distinguish the two models explicitly. In the enhanced model:
- Auth config lives on the External Credential record, not the Named Credential.
- Named Credential holds only the endpoint URL and optional custom headers.
- `UserExternalCredential` SObject is available for per-user token inspection.
- `callout:` Apex syntax is identical in both models.

**Detection hint:** If generated setup instructions say "set Authentication Protocol on the Named Credential" — this is legacy-model guidance. Enhanced orgs use External Credentials for this.

---

## Anti-Pattern 3: Not Handling the Expired Token Case via UserExternalCredential

**What the LLM generates:**

```apex
// LLM checks UserExternalCredential and treats existence as "token is valid"
if (!userExternalCredentials.isEmpty()) {
    // Token is valid — proceed with callout
    makeCallout();
}
// No handling for HTTP 401 from the callout itself
```

**Why it happens:** LLMs correctly identify the `UserExternalCredential` check as a pre-callout auth gate but conflate "user has authenticated at some point" with "user's token is currently valid." Token expiry is a runtime concern that `UserExternalCredential` does not surface.

**Correct pattern:**

```apex
// UserExternalCredential check = "has the user ever authenticated" (UX gate)
if (!isUserAuthenticated(externalCredDevName)) {
    throw new AuraHandledException('Please connect your account first.');
}
// Still handle 401 from the callout — token may have expired
HttpResponse res = new Http().send(req);
if (res.getStatusCode() == 401) {
    throw new AuraHandledException('Session expired. Please reconnect your account.');
}
```

**Detection hint:** Look for code that checks `UserExternalCredential` but has no `401` handling in the callout response logic.

---

## Anti-Pattern 4: Confusing Named Credential API Name With External Credential API Name in `callout:` Syntax

**What the LLM generates:**

```apex
// LLM uses the External Credential developer name in the callout: prefix
req.setEndpoint('callout:MyExternalCredential_EC/api/v1/data');
```

**Why it happens:** In the enhanced model there are two related records — the External Credential and the Named Credential. LLMs sometimes confuse the two names, especially when the developer's question is about auth configuration (External Credential), and then generate a `callout:` prefix using the External Credential name.

**Correct pattern:**

```apex
// callout: ALWAYS references the Named Credential API name, never the External Credential
req.setEndpoint('callout:MyServiceNC/api/v1/data');
```

The Named Credential API name is what appears in the Setup > Named Credentials list. The External Credential name is in Setup > External Credentials. They are typically different values.

**Detection hint:** Ask the developer to confirm the named credential API name explicitly from Setup > Named Credentials. If the `callout:` value ends in `_EC` or `EC`, that is a red flag — External Credential naming conventions typically include `EC`.

---

## Anti-Pattern 5: Using Named Credentials With the Continuation Framework

**What the LLM generates:**

```apex
// Visualforce controller — WRONG
Continuation con = new Continuation(40);
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:ExternalServiceNC/api/data'); // Will NOT work
req.setMethod('GET');
con.addHttpRequest(req);
return con;
```

**Why it happens:** LLMs know that Named Credentials are the recommended callout pattern and also know that Continuation is the recommended async callout pattern for Visualforce/Aura. They combine the two recommendations without checking whether `callout:` syntax is supported by the Continuation framework. It is not — the Continuation framework requires a fully qualified HTTPS URL.

**Correct pattern:**

```apex
// For async callouts from UI: use Queueable instead of Continuation
// The Queueable runs asynchronously and uses the Named Credential normally
public class AsyncDataFetchJob implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ExternalServiceNC/api/data'); // Works in Queueable
        req.setMethod('GET');
        req.setTimeout(30000);
        HttpResponse res = new Http().send(req);
        // process and store result
    }
}
```

**Detection hint:** Any code that constructs a `Continuation` object and uses `callout:` in `setEndpoint()` is wrong. Also watch for code that suggests "use full HTTPS URL in Continuation and handle auth manually" — that is the wrong architectural response to this constraint.

---

## Anti-Pattern 6: Placing `{!$Credential.OAuthToken}` in Apex String Literals or Request Body

**What the LLM generates:**

```apex
// WRONG: formula token in Apex string — sent as literal text to the API
String body = 'grant_type=client_credentials&token=' + '{!$Credential.OAuthToken}';
req.setBody(body);
```

**Why it happens:** LLMs familiar with Salesforce formula fields and merge fields in other contexts (Flow, email templates, SOQL) assume `{!$Credential.*}` works as a general Apex merge field. It does not. These tokens are evaluated only in Named Credential custom header field values in the Setup UI.

**Correct pattern:** If the API requires the token in the body rather than a header, reconsider the integration design. If a header-only approach cannot work, the token must be obtained through an explicit OAuth callout first, then passed into the request body. Named Credentials with formula tokens cannot satisfy body-injection requirements.

**Detection hint:** Look for `{!$Credential.` in any Apex string literal, `setBody()` call, or `setEndpoint()` call. These will always be sent as literal text and never resolved.
