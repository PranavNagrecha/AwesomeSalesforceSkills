# LLM Anti-Patterns — Experience Cloud Multi-IdP SSO

Common mistakes AI coding assistants make when generating or advising on Experience Cloud multi-IdP SSO configurations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending One Portal Per IdP Instead of Multiple Providers on a Single Login Page

**What the LLM generates:** "Create a separate Experience Cloud site for your Okta users and another for your Google users. Each site connects to its own auth provider."

**Why it happens:** LLMs associate "different IdPs" with "different systems" and pattern-match to physical separation. Training data contains many multi-site architectures that were built before multi-provider login pages were well-documented.

**Correct pattern:**

```
Register each IdP as a separate Auth Provider record in one org.
Add multiple Social Login components to the same Experience Cloud site login page,
each pointing to its respective Start SSO URL with the same community parameter.
```

**Detection hint:** Look for "create another site" or "separate community per provider" language in SSO advice. This is almost always wrong when the underlying data model is shared.

---

## Anti-Pattern 2: Omitting the `community` Parameter from the Start SSO URL

**What the LLM generates:**

```
Start SSO URL:
https://myorg.my.salesforce.com/services/auth/sso/MyOIDCProvider
```

**Why it happens:** The Start SSO URL as displayed in Salesforce Setup does not include the `community` parameter. LLMs reproduce what they see in documentation screenshots and examples without noting the parameter must be added manually.

**Correct pattern:**

```
Start SSO URL:
https://myorg.my.salesforce.com/services/auth/sso/MyOIDCProvider?community=https://myorg.my.site.com/portal
```

**Detection hint:** Any Start SSO URL for an Experience Cloud context that does not contain `?community=` is incorrect. Flag it.

---

## Anti-Pattern 3: Not Populating Federation ID on User Records Before Activating SAML SSO

**What the LLM generates:** "Configure the SAML Auth Provider, assign it to the login page, and activate SSO. Users will be matched automatically."

**Why it happens:** LLMs conflate SAML attribute mapping (which is configurable) with the matching field population (which requires a data operation). The auto-match language in some Salesforce documentation is about the matching key selection, not about the field being populated.

**Correct pattern:**

```
1. Export users from the IdP to get their NameID values.
2. Bulk-update FederationIdentifier on User records via Data Loader before activating SSO.
3. Validate with Setup > SAML Assertion Validator using a test assertion.
4. Only then activate SSO for the profile or permission set.
```

**Detection hint:** Any SAML SSO activation advice that does not mention `FederationIdentifier` or Federation ID population as a pre-activation step is incomplete.

---

## Anti-Pattern 4: Missing or Incomplete RegistrationHandler for OIDC Auth Providers

**What the LLM generates:** An OIDC Auth Provider configuration with no RegistrationHandler assigned, or a RegistrationHandler whose `createUser` method returns `null` for unrecognized users.

**Why it happens:** LLMs sometimes treat RegistrationHandler as optional, confusing it with the optional JIT provisioning feature available for SAML. For OIDC, it is mandatory. Additionally, LLMs frequently generate RegistrationHandler implementations that return `null` when a user is not found, intending to block the login but actually producing an undifferentiated error.

**Correct pattern:**

```apex
global User createUser(Id portalId, Auth.UserData data) {
    // Always return a User or throw Auth.RegistrationHandlerException
    // Never return null
    List<User> matches = [SELECT Id FROM User WHERE Email = :data.email LIMIT 1];
    if (!matches.isEmpty()) {
        return matches[0];
    }
    // Create new user — or throw to block unauthorized access
    throw new Auth.RegistrationHandlerException('User not provisioned: ' + data.email);
}
```

**Detection hint:** Check that the Auth Provider record has a Registration Handler class assigned. Check that `createUser` never contains a bare `return null` statement.

---

## Anti-Pattern 5: Forgetting to Register the Salesforce Callback URL in the External IdP Application

**What the LLM generates:** A complete Salesforce Auth Provider setup walkthrough that ends at saving the record, without mentioning that the Salesforce callback URL must be registered in the IdP application (Azure, Google, Okta, etc.).

**Why it happens:** The step is on the IdP side, not the Salesforce side, so LLMs focused on Salesforce configuration omit it. The error manifests as a `redirect_uri_mismatch` on the IdP's side, which is often misdiagnosed as a Salesforce misconfiguration.

**Correct pattern:**

```
After saving the Auth Provider record in Salesforce Setup:
1. Copy the Callback URL from the Auth Provider detail page.
   Format: https://<my-domain>.my.salesforce.com/services/authcallback/<ProviderName>
2. Register this URL as an allowed redirect URI in the IdP application:
   - Azure: App Registration > Authentication > Redirect URIs
   - Google: OAuth 2.0 Client > Authorized redirect URIs
   - Okta: Application > Sign-in redirect URIs
3. Only then test the SSO flow.
```

**Detection hint:** Any OIDC or SAML setup guide that does not mention registering the callback/redirect URI in the external IdP application is missing this step.

---

## Anti-Pattern 6: Assuming Salesforce Cannot Act as Both SP and IdP Simultaneously

**What the LLM generates:** "You cannot configure Salesforce as both a Service Provider (for Experience Cloud) and an Identity Provider (for a connected app) at the same time. You need a separate org for the IdP role."

**Why it happens:** LLMs conflate the SP and IdP roles as mutually exclusive because many enterprise SSO diagrams show a single direction of trust flow. Salesforce supports both roles simultaneously.

**Correct pattern:**

```
Salesforce can be:
- SP: receiving SAML assertions from an external IdP for Experience Cloud login
- IdP: issuing SAML assertions to a connected app via Identity Provider settings
Both configurations are active in the same org simultaneously.
Key risk: test for redirect loops when both are active.
```

**Detection hint:** Any advice recommending separate orgs to separate the SP and IdP roles should be flagged for review.
