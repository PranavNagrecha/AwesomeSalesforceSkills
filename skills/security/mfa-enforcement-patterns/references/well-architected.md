# Well-Architected Notes — MFA Enforcement

## Relevant Pillars

- **Security** — Primary pillar, and the highest-leverage single control against
  credential-based compromise. Salesforce's framing is explicit about the threats:
  MFA exists "to protect users from security threats like phishing, credential
  stuffing, and account takeovers." What matters architecturally is that the control's
  value collapses at its weakest population, not at its average. An org where 99% of
  logins are MFA-protected and the remaining 1% is an integration authenticating with
  a username and password has moved the attack, not stopped it — and moved it to the
  identity with the broadest object access in the org.

- **Operational Excellence** — MFA is not a project that ends. Its permanent
  operational surface is the exception register (which drifts toward permanence unless
  the expiry is structural), the integration inventory (which grows every time someone
  onboards a partner), and the evidence layer (which only exists if Authentication
  Method References were configured with the identity provider). None of these appear
  on a Setup screen, and all three are where compliance drifts.

- **Reliability** — The failure mode is asymmetric and badly timed. Enforcement
  breaks unattended processes, at 02:00, with an authentication error that looks
  identical to a credential problem. Sequencing the integration migration first, in
  parallel, is the difference between a rollout and an incident.

- **Performance** — Only through session lifetime: shorter sessions mean more
  re-authentication, and each re-authentication is an MFA prompt. That is a friction
  budget to spend deliberately per risk tier rather than a performance problem.

## Architectural Trade-offs

**Salesforce MFA versus IdP MFA.** Delegating to the identity provider centralises
the enrolment experience, gives users one factor for every application, and puts the
policy where the identity team already works. It also moves the *coverage* question
outside Salesforce's visibility: an IdP policy scoped to a group that excludes
contractors is invisible from Salesforce, and the contractual requirement "applies
equally to … logins via single sign-on (SSO)." The trade is not security versus
convenience — it is centralised experience versus local visibility, and the price of
the former is a written coverage statement from the IdP owner plus configured
Authentication Method References.

**Detective reporting versus `HIGH_ASSURANCE` enforcement.** A Login History report
finds non-MFA sessions after they have happened, and the gap between the login and the
follow-up is the exposure. `requiredSessionLevel = HIGH_ASSURANCE` on a profile makes
the platform refuse at resource-access time. Enforcement is strictly better where the
population's data warrants it, at the cost of a hard failure for anyone whose session
does not qualify — which is the correct behaviour and still needs a support path.
Note the side effect that outlives the decision: a per-profile `sessionTimeout`
permanently opts that profile out of org-wide timeout changes.

**Migrating integrations versus exempting them.** Exemption is one change and
preserves the credential — a copyable string in a config store, subject to password
expiry, of exactly the shape credential stuffing targets. Migration to client
credentials or JWT bearer is more work, removes the password entirely, and the
platform enforces the design by requiring `oauthClientCredentialUser` to hold the API
Only permission. The migration is also the only one of the two that ever *finishes*:
an exemption is a standing item on the register forever.

**Exception expiry: procedural versus structural.** A review cadence depends on
someone doing the review. A required `Expires_On__c` with a validation-rule cap, and
renewal as a new record with a new approval, depends on nobody. The structural version
costs a validation rule and buys the property that an exception cannot quietly
persist — because extending it is an event with an approver's name on it rather than
an invisible field edit.

**Session lifetime versus MFA friction.** Short sessions limit session-theft value
and increase prompt frequency. The right answer differs per risk tier, which is why
`ProfileSessionSetting` is per profile — but every profile given a custom timeout
leaves the org-wide session policy behind permanently, so the tiering should be
deliberate and few.

## Anti-Patterns

1. **Treating MFA as a boolean.** The interactive-login case is a platform default in
   production orgs. Everything that is not an interactive login is the actual work,
   and every failed rollout fails on a population nobody listed.

2. **Counting the security token as a factor.** It is something the user knows, sent
   in the same channel as the password. Two secrets in one channel is one factor.

3. **Exempting integrations.** Preserves the credential and creates a permanent
   register entry. Migrate to a token-based flow; MFA then stops applying because
   there is no interactive login.

4. **Assuming SSO transfers the obligation.** It transfers the authentication. The
   coverage statement and the Authentication Method References configuration are both
   still yours.

5. **Reporting where you could enforce.** `HIGH_ASSURANCE` refuses at
   resource-access time; a report finds the problem after the session existed.

6. **Exceptions without a structural expiry.** "Review periodically" is how an
   exception becomes permanent. Required expiry, capped by validation, renewed by a
   new record with a new approval.

7. **Classifying by permission rather than by who authenticates.** API Only governs
   where an identity can go, not how it authenticates. A human with a password is an
   interactive user whatever the flag says.

8. **Omitting external and Experience Cloud users.** Separate configuration, separate
   decision — and absent from the matrix means assumed covered.

9. **Planning only for the authenticator app.** Security keys and desktop TOTP need
   procurement lead time, which makes device-constrained populations a T-30 decision
   rather than a cutover discovery.

10. **Declaring an integration migrated when the new flow works.** The old path is
    still there. Thirty days with no username-password subtype in Login History, then
    block the legacy flows org-wide.

## Official Sources Used

- Salesforce Security Guide — Multi-Factor Authentication (the definition of a factor; "Salesforce requires MFA for logins to Salesforce products"; "This contractual requirement applies equally to direct logins with a Salesforce username and password and to logins via single sign-on (SSO)"; "MFA is a default part of the direct login experience for production orgs") — https://help.salesforce.com/s/articleView?id=platform.security_overview.htm&type=5
- Salesforce Security Guide — Monitor Login History (Authentication Method References and the requirement to agree values with the OpenID provider; the OAuth login subtypes; "For security, we recommend blocking user-agent and username-password flows") — https://help.salesforce.com/s/articleView?id=platform.security_login_history.htm&type=5
- Salesforce Security Guide — Real-Time Event Monitoring ("Multi-factor authentication was previously called two-factor authentication. Some MFA-related values reference 'TwoFa'") — https://help.salesforce.com/s/articleView?id=platform.real_time_event_monitoring_overview.htm&type=5
- Salesforce Security Guide — Enhanced Transaction Security (the MFA action, and its degradation to a block on mobile, Lightning Experience, and API) — https://help.salesforce.com/s/articleView?id=platform.enhanced_transaction_security_intro.htm&type=5
- Metadata API Developer Guide — ProfileSessionSetting (`requiredSessionLevel`, `sessionTimeout` valid values and the org-wide-override consequence; API 40.0 and later) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profilesessionsetting.htm
- Metadata API Developer Guide — SessionSecurityLevel ("Multi-factor authentication (MFA) requires HIGH_ASSURANCE"; the `LOW` level caveat) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profilesessionsetting.htm
- Metadata API Developer Guide — ConnectedApp / ConnectedAppOauthConfig (`isClientCredentialEnabled`, `oauthClientCredentialUser` and its API Only requirement) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_connectedapp.htm
- Metadata API Developer Guide — OrgPreferenceSettings, `enableApiUserLtngOutAccessPref` ("If a user has the API Only User permission, they can access Salesforce only via APIs, regardless of their other permissions") — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_orgpreferencesettings.htm
- Salesforce Help — OAuth 2.0 Client Credentials Flow for Server-to-Server Integration — https://help.salesforce.com/s/articleView?id=platform.remoteaccess_oauth_client_credentials_flow.htm&type=5
- Salesforce Help — Exclude Exempt Users from MFA for Salesforce Orgs (the existence and exact label of the **Waive Multi-Factor Authentication for Exempt Users** user permission) — https://help.salesforce.com/s/articleView?id=sf.security_mfa_exclude_exempt_users.htm&type=5
- `security/mfa-enforcement-strategy` — the 2026 enforcement waves (dates for sandbox and production; phishing-resistant MFA for privileged users; the org-wide setting becoming non-deselectable; the Waive permission ceasing to waive MFA). That package's quotes were verified verbatim against the Summer '26 Security Guide, pp. 404–407; this package carries them by reference rather than re-asserting them.
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- PARTIALLY RESOLVED 2026-08-14: the enforcement dates are no longer absent
     from this package. They are carried from security/mfa-enforcement-strategy
     (which an adversarial review verified verbatim against the Summer '26
     Security Guide, pp. 404-407) and cited to it rather than re-asserted here.
     The Multi-Factor Authentication FAQ itself was still NOT retrieved in this
     pass - help.salesforce.com is an Aura SPA that does not serve article text
     to a fetcher. Questions about WHICH products are contractually in scope
     still have to be answered from the FAQ directly. -->
<!-- UNVERIFIED: the sandbox wave for "MFA for all employee users" may have
     shifted. Multiple secondary sources (Salesforce Ben, 2026-07-06) report
     that Salesforce paused this wave on 2026-07-01 and restarted the sandbox
     rollout on 2026-07-06, with production still landing 2026-07-20 over a
     longer stagger, and quote Salesforce as having "briefly delayed enforcement
     while we worked to resolve an issue in which users with existing security
     keys were incorrectly prompted to register new ones during the
     phishing-resistant MFA enrollment process." NONE of that is a primary
     source, and the primary source (the MFA enforcement Help page) could not be
     retrieved. This package therefore carries the ORIGINAL published dates from
     -strategy and does not assert the revision. The direction of the risk is
     mild: the revised sandbox date is later, so a reader planning against
     June 22 plans early. Confirm against the Help page before quoting either
     date to an auditor. -->
<!-- UNVERIFIED: the "Multi-Factor Authentication for User Interface Logins"
     permission appears in the Security Guide's list of permissions that
     Enhanced Transaction Security can act on, but this pass did NOT retrieve
     its own documentation. Its exact effect (and its relationship to the
     default direct-login MFA experience) is not asserted here. -->
<!-- RESOLVED 2026-08-14: the "Waive Multi-Factor Authentication for Exempt
     Users" permission DOES exist. Salesforce Help documents it under "Exclude
     Exempt Users from MFA for Salesforce Orgs"
     (sf.security_mfa_exclude_exempt_users.htm). The package now names it - but
     names it in order to say that it no longer waives MFA, which is the more
     important fact and the reason the previous refusal to mention it was
     misrouting readers. The behavioural change is carried from
     security/mfa-enforcement-strategy. -->
<!-- UNVERIFIED: the 180-day review cap in the examples is a governance
     convention chosen for illustration, not a Salesforce requirement. Since the
     2026 waves it bounds a REVIEW CADENCE, not a period of validity - there is
     no platform waiver left for it to bound. Set it against your own policy.
     Restated in rendered text in references/examples.md Example 4, where the
     rule appears, rather than only here. -->
