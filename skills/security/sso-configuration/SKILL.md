---
name: sso-configuration
description: "Use when configuring single sign-on into or out of a Salesforce org. Trigger keywords: SAML SSO setup, configure single sign-on, identity provider metadata, Just-in-Time provisioning, My Domain SSO, OpenID Connect, SSO-only login, Salesforce as identity provider. NOT for SSO failures - use security/sso-saml-troubleshooting. NOT for OAuth integration access - use admin/connected-apps-and-auth."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do I set up SAML single sign-on with Okta into Salesforce"
  - "configure Entra ID as the identity provider for our Salesforce logins"
  - "what has to be in place before we turn SSO on, is My Domain required"
  - "stop users signing in with a Salesforce password now that SSO is live"
  - "create users automatically the first time they log in through the IdP"
  - "should our portal use IdP-initiated or SP-initiated login"
  - "add Google sign-in as a login option on our Experience Cloud site"
  - "make Salesforce the identity provider for a third-party app"
  - "how do I avoid locking myself out when I enforce SSO-only login"
tags:
  - sso
  - saml
  - openid-connect
  - identity-provider
  - my-domain
  - just-in-time-provisioning
  - auth-provider
  - federated-authentication
inputs:
  - "Which identity provider is authoritative (Entra ID, Okta, Ping, ADFS, Google, or Salesforce itself) and whether it speaks SAML 2.0 or OpenID Connect"
  - "The IdP's federation metadata: entity/issuer string, sign-on endpoint URL, and the X.509 signing certificate"
  - "The matching key that ties an IdP subject to a Salesforce user: Federation ID, Username, or User Id"
  - "Whether users already exist in Salesforce or must be created at first login (and who owns deprovisioning)"
  - "Which audiences are in scope: internal users only, Experience Cloud external users, or both"
  - "Whether the org must also act as an identity provider for downstream apps"
outputs:
  - "A deployable SamlSsoConfig (or AuthProvider) metadata file with issuer, entity Id, certificate and identity mapping filled in"
  - "A documented IdP-side configuration: ACS URL, audience/entity Id, NameID format and claim mapping"
  - "A Just-in-Time provisioning decision, and an Auth.SamlJitHandler or Auth.RegistrationHandler class when the standard form is not enough"
  - "An SSO-only login cutover plan with a named break-glass path"
  - "A certificate expiry and rotation calendar for both sides of the trust"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-08-15
---

# SSO Configuration

This skill activates when an admin or architect is standing up single sign-on for a Salesforce org: choosing between SAML, OpenID Connect and delegated authentication, filling in the SAML Single Sign-On Setting, wiring Just-in-Time provisioning, or turning Salesforce into an identity provider for a downstream app. It covers the build. Diagnosing a login that already fails belongs to `security/sso-saml-troubleshooting`.

---

## Before Starting

Gather this context before touching Setup. Each answer changes the configuration, not just the wording of the advice.

- **Which side of the trust is Salesforce on?** As a *service provider*, Salesforce consumes assertions and the artefact is a `SamlSsoConfig` or an `AuthProvider`. As an *identity provider*, Salesforce issues assertions and the artefact is an external client app with SAML policies. The two roles are independent and an org can hold both at once.
- **What is the matching key, and does it already exist on every user?** `identityMapping` accepts `Username`, `FederationId`, or `UserId`. Federation ID is the usual choice because it decouples the IdP subject from the Salesforce username, but it is blank on every user record until somebody populates it. Auditing that field is a prerequisite task, not a post-cutover cleanup.
- **Does the IdP publish federation metadata XML?** Uploading the IdP's metadata file fills issuer, login URL and signing certificate in one step and removes three transcription errors. If the IdP only offers a portal page, expect to copy values by hand and expect at least one to be wrong.
- **Who is in scope?** Internal users, Experience Cloud external users, and API/integration users each authenticate differently. Integration users that hold `API Enabled` and log in through the SOAP or REST API are not covered by an interactive SAML flow and need their own plan.
- **What is the break-glass path?** Before any SSO-only enforcement, name the account that can still log in with a password and the URL it will use. Decide this first; it is far cheaper than a support case.
- **Who owns the certificates?** Both the IdP signing certificate and any Salesforce request-signing certificate expire. Record both expiry dates and an owner now.

---

## Core Concepts

### Choosing the mechanism

| Mechanism | Protocol | Configured as | Use when | Watch for |
|---|---|---|---|---|
| **Federated authentication** | SAML 2.0 | `SamlSsoConfig` (Setup → Single Sign-On Settings) | An enterprise IdP is authoritative for employees | Certificate rotation; audience/entity Id must match exactly |
| **Authentication provider** | OpenID Connect / vendor protocols | `AuthProvider` (Setup → Auth. Providers) | Social or consumer sign-in, Experience Cloud, or an OIDC-only IdP | Registration handler is required to create users |
| **Salesforce as IdP** | SAML 2.0 | External client app with `ExtlClntAppSamlConfigurablePolicies` | Salesforce credentials should unlock a downstream app | Connected-app creation is restricted from Spring '26 |
| **Delegated authentication** | SOAP callout to your endpoint | Delegated Gateway URL + `Is Single Sign-On Enabled` permission | Legacy only; a credential store that speaks nothing else | Salesforce must call out on every login; feature is off by default |

The Salesforce Security Guide (Summer '26) states plainly: "Salesforce supports SSO with SAML and OpenID Connect. You can also use predefined authentication providers to set up SSO with third parties that use a custom authentication protocol, such as Facebook." Delegated authentication survives from an earlier era and is deliberately gated — the archived Security Guide says "You must contact Salesforce to enable the delegated authentication feature before you can configure it in your org." Treat that gate as a signal, not an obstacle to route around.

### My Domain is the substrate, not an optional extra

Every SSO redirect Salesforce performs is anchored on the org's My Domain hostname. The First-Generation Managed Packaging Developer Guide (v66.0, Spring '26) records the current state: "All Salesforce orgs have a My Domain, an org-specific subdomain for the URLs that Salesforce hosts for that org. Customers have the option to prevent user and SOAP API logins from the generic `login.salesforce.com` and `test.salesforce.com` hostnames. When those options are enabled, logins require the My Domain login URL."

Those two sentences carry the whole SSO-only pattern. The org already has a My Domain; the lever you pull is the login-policy option that stops the generic hostnames from working. Until that lever is pulled, `login.salesforce.com` keeps accepting username-and-password logins no matter how correct the SAML configuration is, and every audit finding that says "SSO is enforced" is wrong.

In Apex, `System.DomainCreator.getOrgMyDomainHostname()` returns the My Domain login hostname; `System.DomainCreator` is available in API version 54.0 and later. Use it instead of hard-coding a hostname into a login flow or a packaged component.

### The SAML Single Sign-On Setting, field by field

Setup labels differ from Metadata API field names. This table is the mapping, using the `SamlSsoConfig` type — components have the suffix `.samlssoconfig` and live in the `samlssoconfigs` folder.

| Metadata field | What it holds | Notes |
|---|---|---|
| `samlVersion` | `SAML1_1` or `SAML2_0` | Choose `SAML2_0`. Several other fields are documented "For SAML 2.0 only" |
| `issuer` | "The identification string for the Identity Provider" | Must match the `Issuer` element the IdP actually emits, character for character |
| `samlEntityId` | "The issuer in SAML requests generated by Salesforce, and is also the expected audience of any inbound SAML Responses" | This is the value the IdP must set as `Audience` |
| `identityMapping` | `Username`, `FederationId`, or `UserId` | The join key to the User record |
| `identityLocation` | `SubjectNameId` or `Attribute` | Where in the assertion the identity is read from |
| `attributeName` | "The name of the identity provider's application. Get this name from your identity provider" | Take the documented description literally — it is not a free-text SAML attribute name of your choosing |
| `attributeNameIdFormat` | NameID format used when the identity sits in an attribute | "For SAML 2.0, only and when `identityLocation` is set to `Attribute`"; documented values include `unspecified`, `emailAddress`, `persistent` |
| `validationCert` | "The certificate used to validate the request. Get this certificate from your identity provider" | The IdP's public signing certificate |
| `decryptionCertificate` | Certificate used to decrypt inbound assertions | Available from API version 30.0; only needed if the IdP encrypts assertions |
| `loginUrl` | "For SAML 2.0 only: The URL where Salesforce sends a SAML request to start the login sequence" | Populates SP-initiated flow; blank means IdP-initiated only |
| `logoutUrl` | Where the Logout link sends the user | Defaults to `https://salesforce.com`, which is almost never what you want |
| `errorUrl` | Destination for login errors | Must be publicly accessible — it is reached by an unauthenticated browser |
| `redirectBinding` | HTTP POST vs HTTP Redirect for outbound SAML messages | Match what the IdP expects to receive |
| `requestSignatureMethod` | `RSA-SHA1` or `RSA-SHA256` | Pick SHA-256 unless the IdP genuinely cannot verify it |
| `requestSigningCertId` | 18-character Id of the Salesforce cert that signs `AuthnRequest` | From Certificate and Key Management |
| `useConfigRequestMethod` | Applies the configured request signature method during single logout | When false, single logout falls back to the documented default of RSA-SHA1 |
| `useSameDigestAlgoForSigning` | Matches the digest algorithm to `requestSignatureMethod` | Available from API version 55.0; documented default is true for configurations created after Spring '22. When false the digest defaults to SHA-1, so setting `requestSignatureMethod` to RSA-SHA256 alone does not give you a SHA-256 digest |
| `singleLogoutUrl` / `singleLogoutBinding` | SLO endpoint and binding (`RedirectBinding` or `PostBinding`) | Single logout is separate configuration from single sign-on |
| `userProvisioning` | "If true, Just-in-Time user provisioning is enabled, which creates users the first time they log in" | The same entry adds: "Specify Federation ID for the identityMapping value to use this feature." Standard JIT is therefore unavailable on a `Username` or `UserId` mapping. See the JIT section below |
| `samlJitHandlerId` | "The name of an existing Apex class that implements the `Auth.SamlJitHandler` interface" | Handler-based JIT |
| `executionUserId` | "The user that runs the Apex handler class. The user must have the Manage Users permission" | Required whenever a handler is set |
| `salesforceLoginUrl` | Login URL for the web SSO flow | Available from API version 47.0; carries the config Id as a parameter when encryption is enabled |

Deployable shape:

```xml
<!-- force-app/main/default/samlssoconfigs/Corporate_IdP.samlssoconfig-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<SamlSsoConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Corporate IdP</name>
    <samlVersion>SAML2_0</samlVersion>
    <issuer>https://sts.windows.net/8f3a1c4e-0000-0000-0000-000000000000/</issuer>
    <samlEntityId>https://acme.my.salesforce.com</samlEntityId>
    <identityMapping>FederationId</identityMapping>
    <identityLocation>SubjectNameId</identityLocation>
    <validationCert>Corporate_IdP_Signing_2026</validationCert>
    <loginUrl>https://login.microsoftonline.com/8f3a1c4e-0000-0000-0000-000000000000/saml2</loginUrl>
    <logoutUrl>https://acme.my.salesforce.com/secur/logout.jsp</logoutUrl>
    <errorUrl>https://acme.example.com/sso-error</errorUrl>
    <redirectBinding>false</redirectBinding>
    <requestSignatureMethod>RSA-SHA256</requestSignatureMethod>
    <userProvisioning>false</userProvisioning>
</SamlSsoConfig>
```

### IdP-initiated versus SP-initiated

Both flows can be live on the same configuration; they are not a mode switch.

- **SP-initiated** starts at the Salesforce My Domain login page. Salesforce builds an `AuthnRequest` and redirects to `loginUrl`. This is the flow that makes a deep link work: a user who clicks a link to a record is returned to that record after authenticating, because Salesforce carries the destination through `RelayState`. If `loginUrl` is empty, this flow cannot happen.
- **IdP-initiated** starts at the IdP's app catalogue. The IdP posts an unsolicited `Response` to the Salesforce assertion consumer endpoint. Deep links do not survive unless the IdP is configured to set `RelayState` itself.

Configure SP-initiated for internal users; it is the flow that behaves correctly for email links, bookmarks, mobile app re-authentication and session timeout. Add IdP-initiated when the business wants a tile on the IdP dashboard.

### Just-in-Time provisioning: two distinct forms

**Standard JIT.** Set `userProvisioning` to true and let the platform create and update the User from assertion attributes. There is no Apex. The Metadata API attaches a hard prerequisite to the flag — "Specify Federation ID for the identityMapping value to use this feature" — so standard JIT is not available on a `Username` or `UserId` mapping, and the assertion must carry every field the User object requires. Standard JIT gives you no control over what happens when an attribute is missing.

**Handler-based JIT.** Set `samlJitHandlerId` to an Apex class implementing `Auth.SamlJitHandler`, and set `executionUserId` to a user with Manage Users. The interface is:

```apex
global class CorporateJitHandler implements Auth.SamlJitHandler {

    global User createUser(Id samlSsoProviderId, Id communityId, Id portalId,
                           String federationId, Map<String, String> attributes,
                           String assertion) {
        User u = new User();
        u.FederationIdentifier = federationId;
        u.Username  = attributes.get('username');
        u.Email     = attributes.get('email');
        u.LastName  = attributes.get('lastName');
        u.FirstName = attributes.get('firstName');
        u.Alias     = u.LastName.left(8);
        u.ProfileId = resolveProfile(attributes.get('department'));
        u.TimeZoneSidKey  = 'Europe/London';
        u.LocaleSidKey    = 'en_GB';
        u.EmailEncodingKey = 'UTF-8';
        u.LanguageLocaleKey = 'en_US';
        insert u;
        return u;
    }

    global void updateUser(Id userId, Id samlSsoProviderId, Id communityId,
                           Id portalId, String federationId,
                           Map<String, String> attributes, String assertion) {
        User u = new User(Id = userId);
        u.Email     = attributes.get('email');
        u.ProfileId = resolveProfile(attributes.get('department'));
        update u;
    }

    private Id resolveProfile(String department) {
        // Map an IdP claim to a Salesforce Profile. Never default to System Administrator.
        return [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1].Id;
    }
}
```

The `attributes` map is case-sensitive on its keys, so the claim names agreed with the IdP team are load-bearing. When the IdP encrypts assertions, the decrypted assertion is supplied in the map under the key `Sfdc.SamlAssertion`.

For OpenID Connect and social providers the equivalent is `Auth.RegistrationHandler`, whose signatures are `User createUser(Id portalId, Auth.UserData data)` and `void updateUser(Id userId, Id portalId, Auth.UserData data)`. `Auth.UserData` exposes `identifier`, `firstName`, `lastName`, `fullName`, `email`, `link`, `username`, `locale`, `provider`, `siteLoginUrl`, `attributeMap`, `idToken`, `userInfoJSONString` and `idTokenJSONString`. From API version 64.0 an `AuthProvider` can point at an Identity User Registration Flow instead of an Apex class through the `flow` field — the Metadata API is explicit that you use one or the other ("To use an Apex class instead, omit the flow field and specify an Apex class in the registrationHandler field"). The flow path also exposes `flowDefaultProfile` and `flowDefaultAccount`, the default profile and default account assigned to users it creates; neither is marked Required, so set them deliberately rather than assuming the platform supplies them.

### OpenID Connect and social sign-on

`AuthProvider` components live in the `authproviders` directory with the extension `.authprovider`, and the file name matches the URL suffix — the suffix that appears in the callback URL, so renaming the file changes the URL the IdP must be told about. `providerType` accepts `Apple`, `Bitbucket`, `Custom`, `Facebook`, `GitHub`, `Google`, `Janrain`, `LinkedIn`, `Microsoft`, `MicrosoftACS`, `MuleSoft`, `OpenIdConnect`, `Salesforce`, `Slack`, and `Twitter`.

| Field | Required for | Notes |
|---|---|---|
| `friendlyName`, `providerType` | All providers | |
| `authorizeUrl`, `tokenUrl`, `userInfoUrl` | OpenID Connect | `tokenUrl` and `userInfoUrl` available from API version 29.0 |
| `sendClientCredentialsInHeader` | OpenID Connect | Sends client credentials as a Basic header instead of a query string |
| `idTokenIssuer` | OIDC / Microsoft | "The source of the authentication token in `https:` URI format"; Salesforce validates the returned `id_token` |
| `consumerKey`, `consumerSecret` | Third-party app registration | `consumerSecret` cannot be changed after initial setup and exports as a placeholder |
| `registrationHandler` + `executionUser` | Any provider that creates users | Execution user must have Manage Users |
| `isPkceEnabled` | Optional, API 59.0+ | Supported for Custom, Facebook, Google, Microsoft, OpenIdConnect and Salesforce provider types |
| `requireMfa` | Optional | "Requires multi-factor authentication (MFA) for single sign-on with this auth provider based on the MFA status of each user" |
| `includeOrgIdInIdentifier` | Optional, API 32.0+ | Disambiguates identical user Ids from two sources such as two sandboxes — **cannot be disabled once enabled** |

```xml
<!-- force-app/main/default/authproviders/CorporateOidc.authprovider-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<AuthProvider xmlns="http://soap.sforce.com/2006/04/metadata">
    <friendlyName>Corporate OIDC</friendlyName>
    <providerType>OpenIdConnect</providerType>
    <authorizeUrl>https://idp.example.com/oauth2/v1/authorize</authorizeUrl>
    <tokenUrl>https://idp.example.com/oauth2/v1/token</tokenUrl>
    <userInfoUrl>https://idp.example.com/oauth2/v1/userinfo</userInfoUrl>
    <idTokenIssuer>https://idp.example.com</idTokenIssuer>
    <defaultScopes>openid profile email</defaultScopes>
    <sendClientCredentialsInHeader>true</sendClientCredentialsInHeader>
    <sendAccessTokenInHeader>true</sendAccessTokenInHeader>
    <isPkceEnabled>true</isPkceEnabled>
    <requireMfa>false</requireMfa>
    <registrationHandler>CorporateOidcRegistrationHandler</registrationHandler>
    <executionUser>identity.admin@acme.com</executionUser>
</AuthProvider>
```

### Salesforce as the identity provider

When Salesforce issues the assertion, the service provider is registered as an app in the org. Historically that meant a connected app with a `samlConfig` block carrying `acsUrl`, `entityUrl`, `samlSubjectType` (`Username`, `FederationId`, `UserId`, `PersistentID`, `CustomAttr`), `samlNameIdFormat`, `encryptionCertificate` and `samlSigningAlgoType`.

That path is closing. The Salesforce Security Guide (Summer '26) carries the note: "Connected apps creation is restricted as of Spring '26. You can continue to use existing connected apps during and after Spring '26. However, we recommend using external client apps instead." New IdP registrations should use `ExtlClntAppSamlConfigurablePolicies`, available from API version 63.0, with the suffix `.ecaSamlPlcy`. It requires `acsUrl`, `entityUrl` and a parent `externalClientApplication`; the parent must have distribution state Local and the SAML plugin enabled in its `ExtlClntAppConfigurablePolicies`. Its `issuer` defaults to the org's My Domain when left blank, and its `encryptionType` offers `AES_128` and `AES_256` only — the older `Triple_Des` option from `ConnectedAppSamlConfig` is not carried forward.

---

## Common Patterns

### Pattern: SP-initiated SAML with Federation ID matching

**When to use:** Employees authenticate against a corporate IdP, user records already exist in Salesforce, and deep links must survive authentication.

**How it works:**
1. Populate `User.FederationIdentifier` on every in-scope user with the value the IdP will put in the SAML `Subject`. Confirm uniqueness before enabling anything — the field is an external key and a collision fails the login.
2. Create the SAML Single Sign-On Setting by uploading the IdP's federation metadata XML, then correct anything the upload guessed: `samlEntityId`, `errorUrl`, `logoutUrl`.
3. Give the IdP team the entity Id you set in `samlEntityId` as the SAML *audience*, and the ACS URL from the Setting. Ask them to send the Federation ID in the `Subject` `NameID`.
4. Test with one pilot user while the login form is still available. Confirm the Login History row shows the My Domain login URL.
5. Only then change the My Domain login policy to stop accepting the generic hostnames.

**Why not IdP-initiated only:** IdP-initiated flows lose the requested destination. A user clicking a case link from an email lands on the home page, and the help desk hears about it every day.

### Pattern: OpenID Connect for an Experience Cloud site with a registration handler

**When to use:** External users authenticate with a consumer or partner identity that has no Salesforce user record yet.

**How it works:**
1. Register the Salesforce callback URL at the OIDC provider and capture the client id and secret.
2. Create the `AuthProvider` with `providerType` `OpenIdConnect`, the three endpoint URLs, `idTokenIssuer`, and `sendClientCredentialsInHeader` set to true.
3. Write an `Auth.RegistrationHandler` that resolves a Contact and Account before inserting the User — an external user without a Contact cannot be created. Set `executionUser` to an admin with Manage Users.
4. Add the provider to the site's login options, and decide `allowInternalUserLogin` deliberately: it "determines whether internal users can log in with their internal credentials on the site login page."
5. Point `Network.logoutUrl` somewhere that makes sense for the site, and use `networkPageOverrides` if the standard login page is being replaced.

**Why not standard JIT here:** standard JIT has no place to put the Contact and Account resolution that an external user requires.

### Pattern: SSO-only login without locking yourself out

**When to use:** Security requires that the corporate IdP is the only way in, including for admins.

**How it works:**
1. Nominate a break-glass account: a dedicated admin user, not a person's daily account, with a long generated password stored in the corporate vault and MFA registered.
2. Confirm that account can authenticate through the My Domain login URL *before* restricting anything, and record the exact URL in the runbook.
3. Change the My Domain login policy so the generic `login.salesforce.com` and `test.salesforce.com` hostnames stop accepting logins for the org.
4. Layer profile-level Login IP Ranges only after SSO is stable. If the org also selects "Enforce login IP ranges on every request" in Session Settings, note that the Security Guide says the option "affects all user profiles that have login IP restrictions" — it is not scoped to the profile you were thinking about.
5. Rehearse the break-glass path on a calendar cadence. A path that has never been tested is not a path.

**Why not rely on a single admin's account:** the failure you are protecting against is the IdP being unreachable, which is exactly when nobody can log in to fix it.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Enterprise IdP, employees, records already exist | SAML `SamlSsoConfig`, `identityMapping` = `FederationId`, SP-initiated | Decouples IdP subject from Salesforce username; deep links survive |
| IdP speaks OIDC only | `AuthProvider` with `providerType` `OpenIdConnect` | SAML settings cannot consume an `id_token` |
| Consumer or partner sign-in on a site | `AuthProvider` + `Auth.RegistrationHandler` | External users need Contact and Account resolution before insert |
| Users must be created at first login, no special logic | `userProvisioning` = true (standard JIT), which the Metadata API documents as requiring `identityMapping` = `FederationId` | No Apex to own, test or deploy |
| User creation depends on org data or claim mapping | `samlJitHandlerId` + `executionUserId` | Handler can query, branch and fail loudly |
| Salesforce credentials must unlock a downstream app | External client app + `ExtlClntAppSamlConfigurablePolicies` | Connected-app creation is restricted from Spring '26 |
| Credential store speaks neither SAML nor OIDC | Reconsider before choosing delegated authentication | Requires a Salesforce-enabled feature and a callout on every login |
| Two sandboxes feed the same auth provider | Set `includeOrgIdInIdentifier` at creation | It cannot be enabled retrospectively without disruption |
| Org must accept assertions *and* issue them | Configure both; they do not conflict | Service-provider and identity-provider roles are independent |

---

## Recommended Workflow

1. **Fix the trust direction and the protocol.** Decide whether Salesforce is the service provider, the identity provider, or both, and whether the wire protocol is SAML 2.0 or OpenID Connect. Everything downstream branches here.
2. **Audit the matching key.** Query the User records in scope and confirm the chosen `identityMapping` field is populated and unique. Fix that data before creating any configuration.
3. **Create the configuration from IdP metadata.** Upload the IdP's federation metadata XML into the SAML Single Sign-On Setting, or fill the `AuthProvider` endpoints from the provider's discovery document. Then set the values the import cannot know: `samlEntityId`, `errorUrl`, `logoutUrl`, `requestSignatureMethod`.
4. **Hand the SP values back to the IdP team.** Give them the entity Id (as *audience*), the ACS URL, the expected NameID format, and the claim names your handler reads. Ambiguity here is the single largest source of failed cutovers.
5. **Decide and build provisioning.** Choose standard JIT, a handler class, or pre-provisioned users. If a handler is used, set `executionUserId` to a user with Manage Users and write tests that cover a missing claim.
6. **Pilot with the login form still available.** Test SP-initiated, IdP-initiated, logout, and a deep link, with one user, before restricting anything. Confirm the Login History row shows the My Domain login URL.
7. **Restrict, then run the checker.** Change the My Domain login policy, verify break-glass, and run `python3 skills/security/sso-configuration/scripts/check_sso_configuration.py --manifest-dir <metadata-dir>` to catch the metadata-shape defects listed in `references/gotchas.md`.

---

## Review Checklist

- [ ] `identityMapping` field is populated and unique on every in-scope User record
- [ ] `samlEntityId` in Salesforce and `Audience` at the IdP are byte-identical, including trailing slash
- [ ] `issuer` matches the IdP's emitted `Issuer` element, not the IdP's console URL
- [ ] `errorUrl` is reachable by an unauthenticated browser and does not itself require SSO
- [ ] `logoutUrl` is not left at the default `https://salesforce.com`
- [ ] `requestSignatureMethod` is `RSA-SHA256` unless the IdP has a documented limitation
- [ ] If `userProvisioning` is true, `identityMapping` is `FederationId` — the Metadata API documents standard JIT as requiring it
- [ ] Every handler-bearing config (`samlJitHandlerId` or `registrationHandler`) has an execution user with Manage Users
- [ ] JIT handler has Apex tests covering a missing claim and a duplicate matching key
- [ ] IdP signing certificate expiry date is recorded with a named owner and a rotation runbook
- [ ] Break-glass account tested through the My Domain login URL and its credentials vaulted
- [ ] SP-initiated deep link tested end to end, not just the login page
- [ ] MFA position is explicit: either the IdP asserts it, or `requireMfa` / Salesforce MFA covers the gap
- [ ] API-only and integration users have an authentication plan that does not depend on the browser flow

---

## Salesforce-Specific Gotchas

Short form; the mechanism and the recovery for each are in `references/gotchas.md`.

1. **A correct SAML configuration changes nothing about who can still use a password.** Enabling SSO adds a route; it does not remove the existing one. The removal is a My Domain login-policy change.
2. **`errorUrl` is fetched by a browser that has not authenticated.** Pointing it at a Salesforce page, or at anything behind the IdP, turns a recoverable login error into a redirect loop.
3. **`includeOrgIdInIdentifier` on an `AuthProvider` is one-way.** The Metadata API states it cannot be disabled after enabling, and existing third-party account links were created under the old identifier shape.
4. **A JIT handler runs as `executionUserId`, not as the person logging in.** Sharing, field-level security and Manage Users all resolve against that account, and a handler that silently fails leaves the user with a generic login error.
5. **Salesforce's MFA requirement follows the user through SSO.** The Security Guide describes it as a *contractual* requirement that "applies equally to direct logins with a Salesforce username and password and to logins via single sign-on (SSO)." Delegating authentication does not delegate the obligation. Read "contractual" precisely: it is a term you are bound by, not an interlock the platform enforces on the SSO path for you, so satisfying it at the IdP is a decision that has to be recorded rather than assumed.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `SamlSsoConfig` metadata file | Deployable SAML setting with issuer, entity Id, certificate, identity mapping and bindings |
| `AuthProvider` metadata file | Deployable OIDC or social provider with endpoints, PKCE and registration handler wiring |
| IdP configuration sheet | Audience/entity Id, ACS URL, NameID format, claim names and signing algorithm, handed to the IdP team |
| JIT handler class + tests | `Auth.SamlJitHandler` or `Auth.RegistrationHandler` implementation with negative-path coverage |
| SSO cutover and break-glass runbook | Login-policy change sequence, tested emergency access path, rollback step |
| Certificate rotation calendar | Expiry dates and owners for the IdP signing certificate and any Salesforce request-signing certificate |

---

## Related Skills

- `security/sso-saml-troubleshooting` — use once a configured SSO login is failing; it walks assertion capture, the SAML Assertion Validator and Login History
- `admin/connected-apps-and-auth` — OAuth and connected/external client apps for integration access, which is a different problem from interactive user sign-on
- `security/oauth-token-management` — access and refresh token lifecycle after an OAuth-based login has succeeded
- `security/certificate-and-key-management` — creating and rotating the certificates this skill references by name
- `security/mfa-enforcement-strategy` — org-wide MFA sequencing, including how SSO changes who has to be enrolled where
- `security/ip-range-and-login-flow-strategy` — login flows that run after authentication, for step-up or conditional checks
- `security/scim-provisioning-integration` — pushing user lifecycle from the IdP instead of pulling it at login time with JIT
- `lwc/experience-cloud-multi-idp-sso` — multiple identity providers on one Experience Cloud site
