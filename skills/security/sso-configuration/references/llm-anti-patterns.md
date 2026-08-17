# LLM Anti-Patterns — SSO Configuration

Common mistakes AI coding assistants make when generating or advising on Salesforce single sign-on configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Emitting Setup Labels as Metadata API Field Names

**What the LLM generates:**

```xml
<SamlSsoConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <entityId>https://acme.my.salesforce.com</entityId>
    <identityProviderLoginUrl>https://idp.example.com/sso</identityProviderLoginUrl>
    <identityProviderCertificate>MIIC...</identityProviderCertificate>
    <samlIdentityType>Federation ID</samlIdentityType>
</SamlSsoConfig>
```

**Why it happens:** the Setup UI labels — "Entity Id", "Identity Provider Login URL", "Identity Provider Certificate", "SAML Identity Type" — dominate blogs, screenshots and Trailhead content, while the Metadata API field names appear almost exclusively in reference documentation. The model reaches for the label it has seen most. The output looks plausible, deploys nowhere, and the resulting error message names the element rather than explaining the mapping.

**Correct pattern:**

```xml
<SamlSsoConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <samlEntityId>https://acme.my.salesforce.com</samlEntityId>
    <loginUrl>https://idp.example.com/sso</loginUrl>
    <validationCert>Corporate_IdP_Signing_2026</validationCert>
    <identityMapping>FederationId</identityMapping>
    <identityLocation>SubjectNameId</identityLocation>
</SamlSsoConfig>
```

Note that `validationCert` names a certificate already uploaded to Certificate and Key Management — it is not the PEM body — and `identityMapping` takes the enum token `FederationId`, not the UI string "Federation ID".

**Detection hint:** grep generated `SamlSsoConfig` XML for `<entityId>`, `<identityProviderLoginUrl>`, `<identityProviderCertificate>`, `<samlIdentityType>` or `<samlIdentityLocation>`. None of those are `SamlSsoConfig` fields. Also flag any `identityMapping` value containing a space.

---

## Anti-Pattern 2: Claiming SSO Is Enforced Because a SAML Configuration Exists

**What the LLM generates:** "Once you save the SAML Single Sign-On Setting and assign it, users will be redirected to your identity provider and can no longer log in with their Salesforce password." Or a completion checklist whose final item is "enable SSO" with nothing after it.

**Why it happens:** in most SaaS products, configuring an IdP replaces the local login. The model transfers that expectation. Salesforce splits the two: the SAML setting adds a route, and a separate login-policy control decides whether the generic hostnames still accept a password.

**Correct pattern:**

```
Enabling SSO   = create SamlSsoConfig / AuthProvider  -> adds an authentication route
Enforcing SSO  = My Domain login policy change        -> removes the password route

Verify enforcement in Setup -> Login History, not in Single Sign-On Settings.
The Login URL column shows which hostname each login actually arrived on.

Before the enforcement step: prove a break-glass account through the
My Domain login URL, from a session-free browser.
```

**Detection hint:** any generated runbook that ends at "save the SAML configuration" and describes the outcome as users being unable to use passwords. If the words "My Domain login policy" or "prevent logins from `login.salesforce.com`" do not appear, the enforcement step is missing.

---

## Anti-Pattern 3: Crossing the Two Provisioning Handler Interfaces

**What the LLM generates:**

```apex
global class MyJitHandler implements Auth.SamlJitHandler {
    global User createUser(Id portalId, Auth.UserData data) {   // wrong interface's shape
        ...
    }
}
```

or the reverse — a six-parameter `createUser` on a class declared as `Auth.RegistrationHandler`.

**Why it happens:** the two interfaces do the same conceptual job and have identically named methods, so the model blends them. It also invents an `Auth.UserData` parameter for the SAML handler because `Auth.UserData` is the more frequently discussed type.

**Correct pattern:**

```apex
// SAML JIT — six parameters, raw attribute map, no Auth.UserData
global User createUser(Id samlSsoProviderId, Id communityId, Id portalId,
                       String federationId, Map<String, String> attributes,
                       String assertion)
global void updateUser(Id userId, Id samlSsoProviderId, Id communityId,
                       Id portalId, String federationId,
                       Map<String, String> attributes, String assertion)

// OIDC / social — two and three parameters, Auth.UserData carries everything
global User createUser(Id portalId, Auth.UserData data)
global void updateUser(Id userId, Id portalId, Auth.UserData data)
```

`Auth.SamlJitHandler` is wired through `samlJitHandlerId` on `SamlSsoConfig`; `Auth.RegistrationHandler` is wired through `registrationHandler` on `AuthProvider`. Both need an execution user with Manage Users.

**Detection hint:** check that the parameter count matches the declared interface — six and eight for `Auth.SamlJitHandler`, two and three for `Auth.RegistrationHandler`. Any `Auth.UserData` parameter on a class implementing `Auth.SamlJitHandler` is wrong.

---

## Anti-Pattern 4: Inventing Numeric Limits for the SSO Surface

**What the LLM generates:** confident numbers — a Federation ID character limit, a maximum number of SAML configurations per org, an assertion clock-skew tolerance in minutes, a session-timeout default, a certificate key size requirement — stated without qualification because the shape of the sentence demands a number.

**Why it happens:** identity documentation across vendors is full of such numbers, and the model has absorbed a mixture of Okta, Entra ID, Ping and Salesforce values. Numbers are also the most fluent thing to generate: "the assertion must be used within 5 minutes" reads better than "within the validity window the IdP sets."

**Correct pattern:**

```
State the mechanism, not a number you cannot source.

  Instead of: "Federation IDs are limited to 512 characters."
  Write:      "Federation ID is a text field on User; check its length limit
               in the Object Reference for the target API version before
               designing a mapping that could exceed it."

  Instead of: "Salesforce tolerates 5 minutes of clock skew."
  Write:      "The assertion carries NotBefore and NotOnOrAfter; if the IdP
               and Salesforce clocks disagree the assertion is rejected as
               expired or not-yet-valid. Fix the IdP clock."

Numbers that matter and CAN be sourced: API version thresholds for fields
(isPkceEnabled 59.0, flow 64.0, ExtlClntAppSamlConfigurablePolicies 63.0,
decryptionCertificate 30.0, salesforceLoginUrl 47.0,
useSameDigestAlgoForSigning 55.0).

Constraints that are documented and must NOT be softened into a preference:
standard JIT requires Federation ID ("Specify Federation ID for the
identityMapping value to use this feature"), and includeOrgIdInIdentifier
cannot be disabled once enabled.
```

**Detection hint:** scan generated SSO guidance for bare digits followed by "characters", "minutes", "seconds", "bits" or "configurations". Each one needs a citation to a page that was actually read, or it needs to be rewritten as a mechanism.

---

## Anti-Pattern 5: Routing an SSO Question to the Connected Apps / OAuth Surface

**What the LLM generates:** "To set up single sign-on, create a connected app, enable OAuth settings, select the scopes your identity provider needs, and give the consumer key and secret to your IdP administrator."

**Why it happens:** "connected app" is the most frequently occurring Salesforce authentication token in training data, and OAuth and SAML co-occur constantly in identity writing. The model also sees connected apps used legitimately in the *identity-provider* direction and generalises that to the service-provider direction, where they have no role.

**Correct pattern:**

```
Salesforce consumes an assertion (someone else authenticates the user)
  -> SamlSsoConfig            (SAML 2.0)
  -> AuthProvider             (OpenID Connect, social, custom)

Salesforce issues an assertion (a downstream app trusts Salesforce)
  -> External client app + ExtlClntAppSamlConfigurablePolicies
  -> (legacy) connected app with samlConfig

An application needs a token to call the Salesforce API
  -> connected app / external client app with OAuth settings
  -> this is NOT single sign-on for people
```

**Detection hint:** if the question is about a person logging in and the answer's first artefact is a consumer key, consumer secret, or OAuth scope list, the routing is wrong. Redirect to the SAML or OpenID Connect surface.

---

## Anti-Pattern 6: Presenting the Connected-App Identity-Provider Runbook as Current

**What the LLM generates:** step-by-step instructions to create a connected app, tick "Enable SAML", and fill in ACS URL, Entity Id, Subject Type and Name ID Format — presented as the way to make Salesforce an identity provider, with no caveat.

**Why it happens:** that runbook was correct for years and dominates the corpus. The restriction is recent and appears as a short note rather than a rewritten chapter.

**Correct pattern:**

```
Salesforce Security Guide v67.0 (Summer '26):
  "Connected apps creation is restricted as of Spring '26. You can continue
   to use existing connected apps during and after Spring '26. However, we
   recommend using external client apps instead. If you must continue
   creating connected apps, contact Salesforce Support."

New registration  -> ExternalClientApplication
                     + ExtlClntAppConfigurablePolicies (SAML plugin enabled)
                     + ExtlClntAppSamlConfigurablePolicies  (API 63.0+, .ecaSamlPlcy)
                     Parent distribution state must be Local.

Existing connected app -> leave it; it keeps working.
```

**Detection hint:** any generated `ConnectedApp` metadata containing a `<samlConfig>` block, or any prose instructing the reader to create a *new* connected app for SSO, without a sentence naming the Spring '26 restriction.

---

## Anti-Pattern 7: Treating My Domain as an Optional Prerequisite to Turn On

**What the LLM generates:** "First, enable My Domain: go to Setup → My Domain, choose a subdomain, wait for it to be registered, then deploy it to all users. Once deployed, you can configure SSO."

**Why it happens:** for several years that really was step one, and the deploy-to-users flow generated a lot of documentation. The model reproduces the era it saw most.

**Correct pattern:**

```
Current state (First-Generation Managed Packaging Developer Guide, v66.0):
  "All Salesforce orgs have a My Domain, an org-specific subdomain for the
   URLs that Salesforce hosts for that org. Customers have the option to
   prevent user and SOAP API logins from the generic login.salesforce.com
   and test.salesforce.com hostnames. When those options are enabled,
   logins require the My Domain login URL."

So the SSO-relevant question is not "is My Domain enabled" but:
  1. What is the org's My Domain login URL?  (Apex: DomainCreator.getOrgMyDomainHostname(),
     available API 54.0+)
  2. Is the login policy still accepting the generic hostnames?
```

**Detection hint:** generated guidance whose first step is enabling or deploying My Domain, or that describes SSO as blocked until My Domain is "turned on". Rewrite as a login-policy question.

---

## Anti-Pattern 8: Offering Delegated Authentication as the Simple Option

**What the LLM generates:** "If your identity system doesn't support SAML, use delegated authentication — just enter your gateway URL in Single Sign-On Settings and enable the Is Single Sign-On Enabled permission." Sometimes accompanied by sample code that accepts and validates the user's password.

**Why it happens:** the configuration surface genuinely is small — a URL and a permission — so it reads as the low-effort path. The model does not surface the enablement gate, the availability coupling, or the credential-handling warning, because those live in prose rather than in the step list.

**Correct pattern:**

```
Before recommending delegated authentication, state all three:

1. It is not self-service. Archived Security Guide: "You must contact
   Salesforce to enable the delegated authentication feature before you
   can configure it in your org."

2. Salesforce calls your endpoint on every login attempt. Your endpoint's
   availability becomes the org's login availability.

3. Do not accept the password. Archived Security Guide: "Because Salesforce
   doesn't use the password field other than to pass it back to you, don't
   pass in a password. Instead, pass another authentication token, such as
   a Kerberos Ticket, so that your corporate passwords aren't passed to or
   from Salesforce."

Then ask whether the credential store already sits behind an IdP that
speaks SAML or OpenID Connect. It usually does.
```

**Detection hint:** any recommendation of delegated authentication that omits the "contact Salesforce" gate, or any sample gateway implementation whose signature accepts and checks a password field.
