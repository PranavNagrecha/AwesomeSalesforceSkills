# LLM Anti-Patterns — Experience Cloud Authentication

Common mistakes AI coding assistants make when generating or advising on Experience Cloud Authentication.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `Auth.RegistrationHandler` for Headless Flows

**What the LLM generates:** An Apex class implementing `Auth.RegistrationHandler` assigned as the headless self-registration handler, or advice to "implement RegistrationHandler for passwordless login."

**Why it happens:** `Auth.RegistrationHandler` is the most commonly documented handler interface in Salesforce training data. LLMs conflate "authentication handler" broadly and apply the familiar interface to all flow types including headless.

**Correct pattern:**

```apex
// For headless passwordless or headless self-registration flows, implement:
global class MyHandler implements Auth.HeadlessSelfRegistrationHandler {
    global User createUser(Map<String, String> userAttributes,
                           Map<String, String> requestAttributes,
                           Id networkId) { ... }
    global Boolean autoConfirm() { return true; }
}

// Auth.RegistrationHandler is ONLY for standard (non-headless) social login via auth provider:
global class MySocialHandler implements Auth.RegistrationHandler {
    global User createUser(Id portalId, Auth.UserData data) { ... }
    global void updateUser(Id userId, Id portalId, Auth.UserData data) { ... }
}
```

**Detection hint:** If the generated code uses `Auth.RegistrationHandler` but the context mentions "headless", "passwordless", or "mobile app login", flag it for review.

---

## Anti-Pattern 2: Building a VF Login Page for an LWR Site

**What the LLM generates:** A Visualforce page for a custom login experience, or instructions like "create a VF page and assign it under Administration > Login & Registration."

**Why it happens:** VF login pages are the established pattern for Aura-based communities and are heavily represented in older Salesforce documentation. LLMs frequently apply this pattern without checking the site engine type.

**Correct pattern:**

```xml
<!-- For LWR sites, the login page must be an LWC with the correct target -->
<!-- In the LWC's .js-meta.xml: -->
<targets>
    <target>lightningCommunity__Page</target>
</targets>

<!-- For Aura sites only, a VF page is valid:
     Setup > Administration > Login & Registration > Login Page Type = Visualforce Page -->
```

**Detection hint:** If the generated output contains a `<apex:page>` component or references a Visualforce page for a login use case, verify the site type. Check whether the word "LWR", "Microsite", or a modern template name (Build Your Own LWR) is present.

---

## Anti-Pattern 3: Missing `HeadlessUserDiscoveryHandler` for Headless Flows

**What the LLM generates:** Code that implements only `HeadlessSelfRegistrationHandler` and omits `HeadlessUserDiscoveryHandler`, or advice to "implement the registration handler and you're done."

**Why it happens:** LLMs focus on the user creation path. The discovery handler — which determines whether to challenge an existing user or route to registration — is a less-documented requirement that LLMs often overlook.

**Correct pattern:**

```
For any headless passwordless or headless self-registration flow, BOTH handlers are required:
1. Auth.HeadlessUserDiscoveryHandler — discover() method, determines CHALLENGE vs REGISTER
2. Auth.HeadlessSelfRegistrationHandler — createUser() method, provisions new users

Both must be assigned in the Experience Cloud site's Headless Identity settings.
Assigning only one causes the flow to fail at the unhandled step.
```

**Detection hint:** If the output mentions headless identity but only one handler class is present (not both), or if `HeadlessUserDiscoveryHandler` is absent from any headless flow implementation, flag it.

---

## Anti-Pattern 4: Not Including the `community` Parameter in the Start SSO URL

**What the LLM generates:** A social login redirect to `/services/auth/sso/<ProviderName>` without the `community` query parameter, or a button that constructs the URL without it.

**Why it happens:** The `community` parameter is an Experience Cloud-specific addition to the standard auth provider Start SSO URL. LLMs trained on general Salesforce auth provider docs produce the base URL pattern without the site-routing parameter.

**Correct pattern:**

```javascript
// Wrong — user ends up on internal org login after IdP handshake
const startUrl = '/services/auth/sso/GoogleProvider';

// Correct — community parameter routes the user back to the site
const siteBase = encodeURIComponent('https://mysite.my.site.com/portal');
const startUrl = `/services/auth/sso/GoogleProvider?community=${siteBase}`;
window.location.href = startUrl;
```

**Detection hint:** Look for any URL containing `/services/auth/sso/` in generated code or advice. Verify it includes `?community=` or `&community=`. If absent, flag it.

---

## Anti-Pattern 5: Testing Auth Provider Only in Production Without Sandbox Validation

**What the LLM generates:** Advice like "configure the auth provider in production and test there" or setup instructions that skip sandbox, especially for time-sensitive implementations.

**Why it happens:** LLMs default to the most direct path. Sandbox-first validation is a process discipline, not a code requirement, so LLMs frequently omit it from generated instructions.

**Correct pattern:**

```
Auth provider callback URL setup process:
1. Create auth provider in sandbox first
2. Register the SANDBOX callback URL with the IdP:
   https://mysite--sandbox-name.sandbox.my.site.com/services/authcallback/ProviderName
3. Test the full login round-trip (initiation → IdP → callback → community landing)
4. Only after sandbox passes, configure production:
   https://mysite.my.site.com/services/authcallback/ProviderName
5. Register the PRODUCTION callback URL with the IdP (separate from sandbox)

Skipping sandbox means the first login failure is in production with real users.
```

**Detection hint:** If a response about auth provider setup does not mention sandbox or does not mention registering the callback URL in the IdP, it is likely missing this step.

---

## Anti-Pattern 6: Using Email as the Sole Match Key in `createUser()`

**What the LLM generates:** A `createUser()` implementation that queries `User` by email address only, with no use of `FederationIdentifier`.

**Why it happens:** Email is intuitive and prominently available in `Auth.UserData`. `FederationIdentifier` is a less familiar field, and LLMs producing "quick" implementations default to the familiar approach.

**Correct pattern:**

```apex
// Wrong — email can change in the IdP, causing duplicate users
List<User> existing = [SELECT Id FROM User WHERE Email = :data.email LIMIT 1];

// Correct — FederationIdentifier stores the IdP's immutable subject identifier
User u = new User();
u.FederationIdentifier = data.identifier; // data.identifier is the IdP subject

List<User> existing = [
    SELECT Id FROM User
    WHERE FederationIdentifier = :data.identifier
    AND IsActive = true
    LIMIT 1
];
```

**Detection hint:** If `createUser()` queries by email only and does not set or query `FederationIdentifier`, flag it as likely to produce duplicate users on email change.
