# Gotchas — SSO Configuration

Non-obvious Salesforce platform behaviors that cause real production problems when configuring single sign-on.

## Gotcha 1: A Working SAML Configuration Does Not Close the Password Door

**What happens:** The SAML Single Sign-On Setting is created, the IdP is wired up, pilot users authenticate cleanly, and the project is declared done. Months later an audit finds that half the user base never went through the IdP at all — they kept using the same bookmark and the same password they always had. Nothing in the SSO configuration blocks that.

**When it occurs:** Every SSO rollout that treats "SSO works" as the finish line. It is especially common in orgs that migrated from a trial or a Developer Edition where the team is used to the generic login hostname.

**Why:** Creating a SAML configuration registers a *new* way to authenticate. It does not deregister username-and-password authentication, which is a property of the login hostname policy, not of the SAML setting. The First-Generation Managed Packaging Developer Guide (v66.0, Spring '26) describes the actual control: customers "have the option to prevent user and SOAP API logins from the generic `login.salesforce.com` and `test.salesforce.com` hostnames. When those options are enabled, logins require the My Domain login URL." Those options live in the My Domain configuration, not in Single Sign-On Settings.

**How to avoid:** Treat the login-policy change as a separate, explicitly scheduled step with its own approval and its own rollback. Before making it, verify from Login History that in-scope users are arriving on the My Domain login URL — the Security Guide notes the Login History surfaces this: "My Domain — You can see when users are logging in with a My Domain URL, which is displayed in the Login URL column." A cutover where the Login URL column still shows generic hostnames is a cutover that has not happened.

**Source:** [T1] First-Generation Managed Packaging Developer Guide v66.0 (Spring '26), "Use the My Domain Login URL for Logins"; Salesforce Security Guide v67.0 (Summer '26), Monitor Login History.

---

## Gotcha 2: `errorUrl` Is Fetched by a Browser That Has Not Authenticated

**What happens:** SSO fails for one user — a missing Federation ID, an expired certificate — and instead of a readable error page they get a redirect loop, a blank page, or a second login prompt that also fails. The support ticket describes a hang, not an error, so the real cause never surfaces.

**When it occurs:** Whenever `errorUrl` points at a destination that itself requires a session — an internal Lightning page, a Visualforce page that is not exposed through a public site, or a corporate page sitting behind the identity provider that has just rejected the user.

**Why:** The Metadata API states both the constraint and what satisfies it: "When there's an error during login, specify the URL of the page where users are directed. It must be publicly accessible, such as a public site Visualforce page. The URL can be absolute or relative." The test is anonymous accessibility, not whether the host is Salesforce-owned — a Visualforce page exposed through a public site is the documented example of a *good* error URL, while the same page reachable only with a session is not. The browser arriving here has, by definition, just failed to authenticate, so any destination that requires authentication sends it back into the login sequence, which fails again, which redirects to the error URL again.

**How to avoid:** Choose the destination, then prove it is anonymous. A public site Visualforce page and a static page on the corporate marketing site both qualify; an internal Lightning or Setup URL does not. Put the service-desk contact route on it and a request-id or timestamp the user can quote. Test it by opening the URL in a private browsing window with no session at all — that test, not the hostname, is what decides whether the page qualifies.

**Source:** [T1] Metadata API Developer Guide, `SamlSsoConfig` — `errorUrl` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_samlssoconfig.htm

---

## Gotcha 3: Federation ID Is Empty on Every User Until Someone Fills It In

**What happens:** The org picks Federation ID as the identity mapping because that is the recommended pattern, the SAML configuration is correct, the assertion is signed and valid — and every login fails to resolve a user. Or worse, a handful of users authenticate as each other because two records share a value copied from a spreadsheet.

**When it occurs:** On first cutover in any org where nobody ran a population project first, and again during every subsequent user-onboarding wave that forgets the field. The failure is invisible in Setup because `FederationIdentifier` is not on the default User layout in many orgs.

**Why:** `identityMapping` on `SamlSsoConfig` accepts `Username`, `FederationId`, or `UserId`. Choosing `FederationId` tells Salesforce to resolve the assertion subject against `User.FederationIdentifier` — a field that ships blank and is populated only by an admin, a data load, JIT provisioning, or a provisioning integration. Salesforce does not derive it from the username or the email. Note also that the choice is not always free: the Metadata API documents standard Just-in-Time provisioning as requiring it — "Specify Federation ID for the identityMapping value to use this feature" — so an org that wants `userProvisioning` has already had this mapping chosen for it, and inherits the population problem with it.

**How to avoid:** Make the population and uniqueness audit a gating task ahead of the configuration, not a follow-up. Query the in-scope population for blanks and for duplicates before the pilot, add `FederationIdentifier` to the User layout so the field is visible to whoever onboards staff, and decide explicitly whether the ongoing owner is a data load, JIT, or an SCIM-style provisioning integration (see `security/scim-provisioning-integration`). If the answer is "we will do it manually," expect this gotcha again within a quarter.

**Source:** [T1] Metadata API Developer Guide, `SamlSsoConfig` — `identityMapping` valid values `Username`, `FederationId`, `UserId` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_samlssoconfig.htm

---

## Gotcha 4: `includeOrgIdInIdentifier` Cannot Be Turned Off Again

**What happens:** An `AuthProvider` of type `Salesforce` is pointed at a second org — commonly a sandbox alongside production, or two sandboxes refreshed from the same source. Users collide, because the third-party user identifier is the same value in both. The admin enables `includeOrgIdInIdentifier` to disambiguate, then discovers that the change is not reversible and that existing account links were formed under the previous identifier shape.

**When it occurs:** Multi-sandbox identity setups, ISV orgs, and any topology where the same auth provider serves more than one upstream Salesforce org.

**Why:** The Metadata API describes the field as "used to differentiate between users with the same user ID from two sources (such as two sandboxes)" and states that once enabled it cannot be disabled. It applies only to Salesforce-managed auth providers.

**How to avoid:** Make the multi-source question part of the design conversation before the provider is created, not after the first collision. If there is any chance a second org will be added later, set the flag at creation while there are no account links to invalidate. If you inherit a provider with the wrong setting, plan for relinking users rather than for a configuration toggle.

**Source:** [T1] Metadata API Developer Guide, `AuthProvider` — `includeOrgIdInIdentifier`, available API version 32.0 and later — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_authproviders.htm

---

## Gotcha 5: The JIT Handler Runs as the Execution User, and Its Failures Look Like Login Failures

**What happens:** JIT provisioning is wired up with an Apex handler. In the sandbox it works. In production, first-time users get a generic login error with no useful detail, and Login History shows a failure that names nothing about Apex. The handler is throwing — on a missing claim, on a validation rule, on a lookup the execution user cannot see — and the exception surfaces to the user as an authentication problem.

**When it occurs:** Any handler-based JIT deployment where the execution user's permissions differ from the developer's, or where the assertion in production carries different claim casing than the test fixture.

**Why:** Two mechanics combine. First, `executionUserId` on `SamlSsoConfig` is documented as "the user that runs the Apex handler class. The user must have the Manage Users permission" — so sharing, field-level security and object permissions all resolve against that account, not against the person signing in, who has no user record yet. Second, the `attributes` map handed to `Auth.SamlJitHandler.createUser` is case-sensitive on its keys, so `Email` and `email` are different claims and the wrong one silently returns null.

**How to avoid:** Agree the exact claim names, including case, in writing with the IdP team, and assert them in the Apex tests rather than assuming them. Write the handler so that a missing required claim produces a deliberate, described exception rather than a null-pointer several lines later. Give the execution user a dedicated permission set rather than borrowing an admin account, and confirm it can read every object the handler queries. When the IdP encrypts assertions, remember the decrypted copy arrives in the same map under the key `Sfdc.SamlAssertion` — a handler that reads the raw `assertion` parameter for an encrypted flow gets ciphertext.

**Source:** [T1] Metadata API Developer Guide, `SamlSsoConfig` — `executionUserId`; [T1] Apex Reference Guide, `Auth.SamlJitHandler` interface, `createUser` / `updateUser` parameters — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_Auth_SamlJitHandler.htm

---

## Gotcha 6: The Salesforce-as-Identity-Provider Path Moved, and the Old Instructions Still Look Right

**What happens:** An architect follows a familiar runbook — create a connected app, tick "Enable SAML", fill in ACS URL and entity Id — and finds they cannot create the connected app at all. Or an AI assistant emits `ConnectedAppSamlConfig` metadata that no longer represents the recommended path, and the deployment is accepted in an org that still has legacy connected apps while being wrong for anything new.

**When it occurs:** From Spring '26 onward, in orgs that have not been granted an exception.

**Why:** The Salesforce Security Guide (v67.0, Summer '26) carries the note verbatim: "Connected apps creation is restricted as of Spring '26. You can continue to use existing connected apps during and after Spring '26. However, we recommend using external client apps instead. If you must continue creating connected apps, contact Salesforce Support." The replacement surface for the identity-provider role is `ExtlClntAppSamlConfigurablePolicies`, available from API version 63.0, with the file suffix `.ecaSamlPlcy`. It is not a drop-in rename: it requires a parent `ExternalClientApplication` whose distribution state is Local and whose `ExtlClntAppConfigurablePolicies` has the SAML plugin enabled, and its `encryptionType` offers only `AES_128` and `AES_256` where `ConnectedAppSamlConfig` also offered `Triple_Des`.

**How to avoid:** For any new service-provider registration, build the external client app first and attach SAML policies to it. Keep existing connected apps in place — they continue to work — but stop treating the connected-app runbook as the default. Check the target org's release before quoting either path as available.

`[STALE-RISK: re-check whether connected-app creation restrictions have been extended, relaxed, or paired with a migration tool, and whether ExtlClntAppSamlConfigurablePolicies has gained fields such as an encryption option beyond AES_128/AES_256.]`

**Source:** [T1] Salesforce Security Guide v67.0 (Summer '26), Connected Apps — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf ; [T1] Metadata API Developer Guide, `ExtlClntAppSamlConfigurablePolicies` — https://developer.salesforce.com/docs/atlas.en-us.262.0.api_meta.meta/api_meta/meta_extlclntappsamlconfigurablepolicies.htm

---

## Gotcha 7: Logout Is a Separate Configuration From Login, and the Default Sends Users Somewhere Useless

**What happens:** A user clicks Logout, lands on a generic Salesforce marketing page, then clicks their bookmark and is immediately signed back in without being asked for anything. On a shared or kiosk machine that is a real exposure, and it is reported as "logout is broken" when the platform is behaving exactly as configured.

**When it occurs:** Whenever `logoutUrl` is left at its default and single logout was never configured. It is most visible on shared devices, in contact centres, and on Experience Cloud sites.

**Why:** Two independent settings are involved. `logoutUrl` on `SamlSsoConfig` is documented as the URL to direct the user to when they click the Logout link, and its default is `https://salesforce.com`. Ending the Salesforce session does not end the IdP session, so the next SP-initiated request is satisfied silently by the still-live IdP cookie. Terminating both sides requires the SAML single logout fields — `singleLogoutUrl` and `singleLogoutBinding`, which accepts `RedirectBinding` or `PostBinding` — plus matching configuration at the IdP. On Experience Cloud, the site has its own `logoutUrl` on the `Network` metadata type, which is a third place the behaviour can be set.

**How to avoid:** Decide the intended post-logout destination as a requirement, not a default. If the requirement is "the next person at this machine must authenticate," configure single logout on both sides and test it on a real shared device — not by closing a private browsing window, which hides the IdP cookie you are trying to observe. Set the Experience Cloud site's own logout destination separately.

**Source:** [T1] Metadata API Developer Guide, `SamlSsoConfig` — `logoutUrl`, `singleLogoutUrl`, `singleLogoutBinding`; `Network` — `logoutUrl`, available API version 28.0 and later — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_samlssoconfig.htm

---

## Gotcha 8: Delegated Authentication Puts Your Endpoint in the Login Path and Asks for a Password It Should Not Get

**What happens:** A team reaches for delegated authentication because the credential store speaks LDAP and nothing else, and discovers three things in sequence: the feature cannot be switched on from Setup, every single login now depends on the availability of a web service they operate, and the naive implementation ships corporate passwords across the boundary.

**When it occurs:** Legacy modernisation projects, and any design that treats delegated authentication as a lighter-weight alternative to SAML. It is not lighter-weight; it is older.

**Why:** Salesforce gates the feature deliberately — the archived Security Guide states "You must contact Salesforce to enable the delegated authentication feature before you can configure it in your org." Once enabled, configuration involves downloading `AuthenticationService.wsdl` from Setup, entering a Delegated Gateway URL in Single Sign-On Settings, enabling the `Is Single Sign-On Enabled` permission on the relevant users, and standing up an endpoint Salesforce can reach on a permitted outbound port. Salesforce calls that endpoint on each login attempt, so its latency and availability become the org's login latency and availability. The guide is also explicit about the credential-handling risk: "Because Salesforce doesn't use the password field other than to pass it back to you, don't pass in a password. Instead, pass another authentication token, such as a Kerberos Ticket, so that your corporate passwords aren't passed to or from Salesforce."

**How to avoid:** Prefer SAML or OpenID Connect. Nearly every LDAP estate already sits behind an IdP that speaks one of them, and adopting it removes the callout dependency, the WSDL, and the credential-in-transit problem in one move. If delegated authentication genuinely cannot be avoided, design the endpoint for the availability target of the login page itself, and pass a token rather than a password exactly as the guide instructs.

`[STALE-RISK: confirm whether delegated authentication remains available for new enablement, and re-read the current permitted-port list before publishing an endpoint — the port range quoted in older editions of the guide contains an evident typo and should not be repeated from memory.]`

**Source:** [T1] Salesforce Security Guide, Single Sign-On / Configuring Delegated Authentication (archived edition, Spring '18, API 42.0) — https://developer.salesforce.com/docs/atlas.en-us.212.0.securityImplGuide.meta/securityImplGuide/sso_about.htm ; [T1] Salesforce Security Guide v67.0 (Summer '26) for the current supported-protocol statement.

---

## Source Disagreement Note

The archived Salesforce Security Guide (Spring '18) presents three SSO types — federated authentication, delegated authentication, and authentication providers. The current Security Guide (v67.0, Summer '26) frames the supported set as "SSO with SAML and OpenID Connect," plus predefined authentication providers, and does not present delegated authentication alongside them.

**Resolution:** the current guide wins for what to build. The archived guide is cited here only for delegated authentication mechanics, which are not documented in the current edition and which practitioners still encounter in inherited orgs. Any delegated-authentication detail taken from the archived edition is version-tagged in this file and should be re-verified against the target org before it is acted on.
