# Well-Architected Notes — SSO Configuration

## Relevant Pillars

- **Security** — SSO configuration decides who the org trusts to assert identity, and how tightly that assertion is bound to a Salesforce user record. The specific things to watch: the audience value (`samlEntityId`) must be unique to this org so an assertion minted for a sandbox cannot be replayed at production; `requestSignatureMethod` should be `RSA-SHA256` rather than the still-permitted `RSA-SHA1`; and the identity mapping should be a value the IdP controls and the user cannot edit. Mapping to `Username` couples authentication to a field admins routinely change during onboarding and email-domain migrations; `FederationId` does not.
- **Operational Excellence** — the operational cost of SSO is concentrated in two recurring events: certificate rotation and user onboarding. Both are predictable and both take an org down when they are nobody's job. The artefact that discharges this pillar is not the SAML setting; it is the calendar entry for the IdP signing certificate and the named owner for populating the matching key on new users.
- **Reliability** — SSO makes the identity provider a hard dependency of the login path. Delegated authentication makes an internally-operated web service a hard dependency of every single login attempt. Neither is wrong, but both must be designed with the availability target of the login page itself, and both require a tested path that does not traverse the dependency. A break-glass account that has never completed a login is a design artefact, not a control.
- **Adaptable** — the identity-provider role in particular is mid-transition. Registrations that used to be connected apps now belong on external client apps, and `AuthProvider` gained a Flow-based registration handler in API version 64.0 alongside the Apex one. Configurations built as deployable metadata under source control absorb these moves; configurations that exist only as clicks in a production org do not.

## Architectural Tradeoffs

**Federation ID versus Username as the identity mapping.** Username is tempting because it already exists on every user and needs no data project. It ties authentication to a field that changes: usernames are edited during mergers, domain migrations, and sandbox refreshes, and each edit silently breaks that user's SSO. Federation ID costs a population project up front and an ownership decision forever, and buys a matching key that only the IdP and the identity team touch. Choose Federation ID unless the org is small enough that the population project genuinely does not pay for itself.

**Just-in-Time provisioning versus push provisioning.** JIT creates the user at first login, which means zero users exist until they arrive and nobody maintains a joiner process. Its weakness is the leaver: JIT has no event at all when someone leaves the IdP, so deactivation must come from somewhere else. Push provisioning (see `security/scim-provisioning-integration`) creates and deactivates on the IdP's lifecycle events, at the cost of a running integration. Orgs with meaningful licence spend or regulatory deprovisioning requirements should not rely on JIT alone.

**Standard JIT versus a handler class.** Standard JIT is a checkbox and has no code to own, test, package or deploy. It also has no branch: if a claim is missing or a profile has to be derived from org data, there is nowhere to express that. A handler class buys arbitrary logic and costs an Apex class, a test class, an execution user, and a failure mode that surfaces to end users as an opaque login error. Start with standard JIT and move to a handler when a specific requirement forces it, not preemptively.

**IdP MFA versus Salesforce MFA.** If the IdP already enforces MFA for the corporate estate, asserting it once at the IdP is simpler and gives users one enrolment. The `AuthProvider` field `requireMfa` exists for the opposite case — it "requires multi-factor authentication (MFA) for single sign-on with this auth provider based on the MFA status of each user," which lets Salesforce apply its own challenge on top. Running both is not free: users get challenged twice and start looking for the route that challenges them less.

**SSO-only versus a password fallback.** Closing the generic login hostnames removes an entire class of credential-stuffing exposure and makes the IdP's controls universal. It also removes the org's independent recovery path. The resolution is not to keep the fallback open for everyone; it is to keep exactly one governed, tested, vaulted account able to use it, and to treat that account as a security control with its own review cadence.

## Anti-Patterns

1. **Declaring SSO enforced when only SSO enablement happened.** Creating a SAML configuration adds an authentication route; it does not remove password authentication on the generic login hostnames. Audits that check for the existence of a SAML setting rather than for the login-policy state produce false assurance. Check the login policy and the Login URL column in Login History, not the presence of a configuration.

2. **Pointing `errorUrl` at a page behind the identity provider.** The browser that reaches the error URL has just failed to authenticate. Any destination requiring authentication converts a diagnosable error into a redirect loop, and the resulting support tickets describe a hang rather than a cause.

3. **Giving the JIT execution user System Administrator because the handler failed.** The execution user must hold Manage Users, and it needs read access to whatever the handler queries — that is a permission set, not a blanket admin profile. Escalating to admin makes every future login-time provisioning defect an admin-privileged code path.

4. **Treating an OAuth connected app as an SSO configuration.** OAuth governs an application's delegated access to data; SAML and OpenID Connect govern how a person establishes a browser session. Building the first when the requirement was the second leaves users still typing Salesforce passwords and leaves the org with an ungoverned broad-scope app.

5. **Reaching for delegated authentication to avoid federation work.** It is not the lightweight option. It requires Salesforce to enable the feature, requires a callout on every login attempt, and puts an internally-operated endpoint on the critical path of authentication. Almost every credential store that motivates it already sits behind an IdP that speaks SAML or OpenID Connect.

## Contradiction Log

### Supported SSO types — archived Security Guide versus current Security Guide

**This skill says:** build with SAML 2.0 or OpenID Connect. Delegated authentication is covered as an inherited-org concern and is actively discouraged for new work.

**The archived Salesforce Security Guide (Spring '18, API 42.0) says:** Salesforce supports three types of SSO — federated authentication using SAML, delegated authentication, and authentication providers — presenting them as peers.

**The current Salesforce Security Guide (v67.0, Summer '26) says:** "Salesforce supports SSO with SAML and OpenID Connect. You can also use predefined authentication providers to set up SSO with third parties that use a custom authentication protocol, such as Facebook." Delegated authentication is not presented alongside them.

**Context where this skill applies:** any new configuration.
**Context where the archived guide applies:** understanding or decommissioning delegated authentication in an inherited org, where its mechanics are no longer documented in the current edition.
**Resolution status:** Resolved. The current guide wins on what to build; the archived guide is cited only for delegated-authentication mechanics, and every such claim is version-tagged in `references/gotchas.md`.

### Salesforce-as-identity-provider surface — connected app versus external client app

**This skill says:** new service-provider registrations should use an external client app with `ExtlClntAppSamlConfigurablePolicies`.

**The `ConnectedApp` Metadata API documentation says:** `ConnectedAppSamlConfig` remains a documented sub-type with a full field set, which reads as a currently recommended path.

**The current Salesforce Security Guide (v67.0, Summer '26) says:** "Connected apps creation is restricted as of Spring '26. You can continue to use existing connected apps during and after Spring '26. However, we recommend using external client apps instead."

**Context where this skill applies:** creating a new registration in a Spring '26 or later org.
**Context where the connected-app documentation applies:** maintaining an existing connected app, which continues to be supported.
**Resolution status:** Resolved, with a stale-risk marker on Gotcha 6 — re-check whether the restriction is extended, relaxed, or paired with a migration path.

## Official Sources Used

Fetched and verified 2026-08-15 unless noted.

- Metadata API Developer Guide — `SamlSsoConfig` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_samlssoconfig.htm — source for every field name, valid-value enum and API-version note in the SAML settings table, for the `.samlssoconfig` / `samlssoconfigs` file layout, and for the `samlEntityId`, `errorUrl`, `logoutUrl`, `userProvisioning`, `samlJitHandlerId` and `executionUserId` descriptions quoted in SKILL.md and gotchas.md.
- Metadata API Developer Guide — `AuthProvider` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_authproviders.htm — source for the `providerType` enum, the required-field list, the `.authprovider` / `authproviders` file layout and the "file name matches the URL suffix" behaviour, and for the `requireMfa`, `executionUser`, `includeOrgIdInIdentifier`, `isPkceEnabled` (API 59.0+) and `flow` (API 64.0+) semantics.
- Metadata API Developer Guide — `ExtlClntAppSamlConfigurablePolicies` — https://developer.salesforce.com/docs/atlas.en-us.262.0.api_meta.meta/api_meta/meta_extlclntappsamlconfigurablepolicies.htm — source for the external-client-app identity-provider path: API version 63.0, `.ecaSamlPlcy` suffix, required `acsUrl` / `entityUrl` / `externalClientApplication`, issuer defaulting to My Domain, and the `AES_128` / `AES_256` encryption values.
- Metadata API Developer Guide — `ConnectedApp` (`ConnectedAppSamlConfig`) — https://developer.salesforce.com/docs/atlas.en-us.248.0.api_meta.meta/api_meta/meta_connectedapp.htm — source for the legacy Salesforce-as-IdP field set, including `samlSubjectType`, `samlNameIdFormat`, `samlSigningAlgoType` (API 50.0+) and the `Triple_Des` encryption option that the external client app path does not carry forward.
- Metadata API Developer Guide — `MyDomainDiscoverableLogin` — https://developer.salesforce.com/docs/atlas.en-us.248.0.api_meta.meta/api_meta/meta_mydomaindiscoverablelogin.htm — source for the identity-first Discovery login page (API version 48.0, `apexHandler`, `executeApexHandlerAs`), the mechanism behind routing different user populations to different IdPs from one login page.
- Metadata API Developer Guide — `Network` — https://developer.salesforce.com/docs/atlas.en-us.248.0.api_meta.meta/api_meta/meta_network.htm — source for the Experience Cloud authentication surface used in Example 2: `allowInternalUserLogin` (API 40.0+), `selfRegistration` / `selfRegProfile`, site-level `logoutUrl`, and `networkPageOverrides`.
- Metadata API Developer Guide — `SecuritySettings` / `SessionSettings` — https://developer.salesforce.com/docs/atlas.en-us.248.0.api_meta.meta/api_meta/meta_securitysettings.htm — source for the session-side settings that interact with an SSO cutover: `lockSessionsToIp`, `logoutURL`, `sessionTimeout`, `forceRelogin`.
- Apex Reference Guide — `Auth.SamlJitHandler` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_Auth_SamlJitHandler.htm — source for the exact `createUser` / `updateUser` signatures, the case-sensitivity of the `attributes` map, the `Sfdc.SamlAssertion` key for decrypted assertions, and the Manage Users requirement on the execution user.
- Apex Reference Guide — `Auth.RegistrationHandler` — https://developer.salesforce.com/docs/atlas.en-us.248.0.apexref.meta/apexref/apex_auth_plugin.htm — source for the two-method OIDC/social handler signatures used in Example 2.
- Apex Reference Guide — `Auth.UserData` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Auth_UserData.htm — source for the property list a registration handler can read, including `attributeMap`, `idToken` and `userInfoJSONString`.
- Salesforce Security Guide, Version 67.0 (Summer '26), last updated 24 April 2026 — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf — source for the current supported-protocol statement, the MFA requirement text ("applies equally to direct logins with a Salesforce username and password and to logins via single sign-on (SSO)"), the Spring '26 connected-app creation restriction note, the "Enforce login IP ranges on every request" behaviour, the "Legacy SAML service provider access" permission-placement guidance, and the Login History My Domain column.
- Salesforce Security Guide, archived edition (Spring '18, API 42.0) — https://developer.salesforce.com/docs/atlas.en-us.212.0.securityImplGuide.meta/securityImplGuide/sso_about.htm and https://developer.salesforce.com/docs/atlas.en-us.212.0.securityImplGuide.meta/securityImplGuide/sso_delauthentication_configuring.htm — the only fetchable source for delegated-authentication mechanics: the "you must contact Salesforce to enable" gate, the `AuthenticationService.wsdl` download, the Delegated Gateway URL, the `Is Single Sign-On Enabled` permission, and the instruction not to pass a corporate password. Every claim drawn from it is version-tagged.
- Metadata API Developer Guide — Metadata Types index (Summer '26, API 67.0) — https://developer.salesforce.com/docs/atlas.en-us.262.0.api_meta.meta/api_meta/meta_types_list.htm — used to confirm which identity-related metadata types exist in the current release, including that `ExtlClntAppSamlConfigurablePolicies` is present and that no separate My Domain login-policy type is exposed.
- First-Generation Managed Packaging Developer Guide, Version 66.0 (Spring '26) — local corpus: `knowledge/imports/pkg1-dev.md`, "Use the My Domain Login URL for Logins" — source for the verbatim statement that all orgs have a My Domain and that customers can prevent logins from `login.salesforce.com` and `test.salesforce.com`, and for `System.DomainCreator` being available from API version 54.0.
- Headless Identity Implementation Guide, Version 66.0 (Spring '26) — local corpus: `knowledge/imports/headless-identity-impl-guide.md` — background on adding an auth provider or SAML identity provider as a login option on an Experience Cloud site and driving it from an app, which is the shape Example 2 builds toward.

### Pre-seeded scaffold sources (retained, not used for any claim in this package)

These arrived with the `new_skill.py` scaffold. They are retained per the content contract but no factual claim in this package rests on them, and none were fetched for this revision — the Shield and Apex-security topics they cover belong to `security/platform-encryption` and `security/secure-coding-review-checklist`.

- Shield Platform Encryption Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5
- Secure Apex Classes — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- Salesforce Security Guide (Help edition) — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5 — superseded for this package by the PDF edition listed above, which is the copy that was actually read.
