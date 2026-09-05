# Well-Architected Notes — Org Setup And Configuration

## Relevant Pillars

- **Security** — Every setting in this skill directly influences the org's security posture. MFA enforcement, session controls, password policies, trusted IP ranges, and CSP together form the authentication and browser-security baseline. Misconfigured org settings are a primary attack surface in compromised Salesforce orgs.
- **Operational Excellence** — My Domain deployment, CSP entries, and session settings require deliberate rollout planning. Deploying My Domain without updating integrations, or changing password policy without communicating to users, causes operational incidents. These settings need change management.
- **Reliability** — Overly aggressive session settings (short timeout + IP locking) or misconfigured My Domain deployments can cause user lockouts that affect business operations. The settings must reflect real usage patterns.

## Architectural Tradeoffs

**MFA via Salesforce vs MFA via IdP:** Enabling MFA at the Salesforce level is simpler to configure but duplicates MFA enforcement if the org uses SSO. If all users authenticate via an external IdP that enforces MFA, the Salesforce-side enforcement is redundant (Salesforce still honors the IdP MFA as satisfying the requirement). The preferred architecture for large orgs is IdP-enforced MFA with Salesforce MFA enabled as a backstop for direct logins only.

**Session timeout vs user convenience:** Short session timeouts increase security but reduce usability, particularly for users in long meetings or who step away from their desk. A reasonable default of 2 hours balances security and convenience. For regulated industries (healthcare, financial services), shorter timeouts are appropriate but should be paired with user communication.

**IP-locking vs MFA:** Locking sessions to IP is a legacy security control that predates MFA. With MFA enforced, the incremental security benefit of IP-locking is marginal, and the usability cost is significant. Prefer MFA enforcement over IP-locking as the primary session assurance mechanism.

**CSP strict mode vs permissive exceptions:** Every CSP Trusted Site entry is a deliberate reduction of browser security. Sites trusted for `script-src` can execute JavaScript in the user's browser context. Minimize entries, document business justification, and review periodically. Avoid adding wildcard domains.

## Anti-Patterns

1. **Deploying My Domain without auditing integration callback URLs** — The most common cause of post-go-live integration failures. Every Connected App, SSO configuration, and external system that uses the org's login URL must be updated before or immediately after My Domain deployment.

2. **Using trusted IP ranges as a substitute for MFA** — Trusted IP ranges only bypass the email verification challenge. They do not enforce authentication strength. An attacker with a stolen password who is on a trusted network (e.g., connected to the company VPN) can still log in without MFA if MFA is not independently enforced. Trusted ranges and MFA solve different problems and should both be in place.

3. **Accumulating CSP Trusted Sites with all available directives checked** — The "check all" approach defeats the purpose of CSP as a defense-in-depth control. Over time, orgs accumulate dozens of entries covering domains from defunct integrations, all granted broad trust across connect-src, style-src, img-src, font-src, frame-src, and media-src. Audit and prune CSP entries quarterly. Note: `script-src` is not exposed through the CSP Trusted Sites UI; external JavaScript must be delivered as a Salesforce static resource.

## Deploy-Time Tradeoffs

**One file per Setup page vs. per-setting granularity:** Settings components have no addressable `fullName` — there is exactly one `Security.settings` per org, and a deploy replaces the containers it carries. This is good for review (the whole authentication baseline is one diffable artefact) and dangerous for partial edits (`networkAccess` deployed without the org's existing ranges deletes them). The tradeoff resolves one way only: retrieve first, always, and treat the settings file as org state rather than as a change.

**Source-controlled vs. per-environment settings:** Some values are legitimately environment-specific and must not be promoted. `canOnlyLoginWithMyDomainUrl` is the clearest case — `true` in production is hardening, `true` in a sandbox removes the Sandboxes-page Log In action for admins. Treat the settings files as a promoted baseline with a small, named, documented divergence list, not as a file that must be byte-identical everywhere.

**What the API cannot carry:** My Domain registration, the org's default locale/time zone/currency (`Organization` object fields), and any feature setting outside Metadata API coverage are per-org manual actions. An org stand-up runbook that pretends everything is deployable will leave a new org subtly different from its template; naming the manual steps explicitly is the cheaper design.

## Official Sources Used

- Metadata API Developer Guide — `Settings` (file suffix and directory location, the `<members>` naming rule, wildcard limits, "Not all feature settings are available in Metadata API") — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports the *Org-Wide Settings Are Deployable Metadata* concept and the package.xml in `references/metadata-examples.md`
- Metadata API Developer Guide — `SecuritySettings`, including the `NetworkAccess`/`IpRange`, `PasswordPolicies` and `SessionSettings` subtypes (`sessionTimeout`, `maxLoginAttempts`, `lockoutInterval`, `complexity` and `expiration` enum lists; `lockSessionsToIp`; `enableMFADirectUILoginOptIn`; `enableAdminLoginAsAnyUser`; `canUsersGrantLoginAccess`; `disableTimeoutWarning`; `forceLogoutOnSessionTimeout`; the replace-in-place rule for `ipRanges`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports gotchas 6, 9, 10, 11 and the `Security.settings` example
- Metadata API Developer Guide — `MyDomainSettings` (`myDomainName`/`myDomainSuffix`/`domainPartition`/`useEdge` read-only in the API; `MySalesforce` vs `MySalesforceLimited` as the enhanced-domains signal; `redirectPriorMyDomain` resetting on a new domain deploy; `canOnlyLoginWithMyDomainUrl` and the sandbox Log In action) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports gotchas 7, 8 and 12
- Metadata API Developer Guide — `CspTrustedSite` (the six `isApplicableTo*` directives and two `canAccess*` flags with no `script-src` among them; the API 49.0 / 50.0–58.0 / 59.0+ default-grant changes; `endpointUrl` syntax rules; the 12 KB CSP header guidance) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports gotcha 13 and the *CSP strict mode vs permissive exceptions* tradeoff above
- Metadata API Developer Guide — `CompanySettings` (fiscal year only; "When changing fiscal year settings, quotas and adjustments can be purged"), `LanguageSettings` (ICU formats), `Profile` (`loginIpRanges`/`ProfileLoginIpRange`, `loginHours`, and the absence of any password-policy field), `OrgPreferenceSettings` (removed in API version 48.0) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports the stand-up order table and the profile-vs-org boundary in `references/metadata-examples.md`
- Object Reference for the Salesforce Platform — `Organization` (`InstanceName`, `IsSandbox`, `OrganizationType`, `DefaultLocaleSidKey`, `LanguageLocaleKey`, `TimeZoneSidKey`, `TrialExpirationDate`) and `User` (`PasswordExpirationDate`, API 63.0+) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf — supports the verification SOQL in `references/metadata-examples.md` and the expiry-cliff query in `references/examples.md`
- Salesforce Help — MFA for Salesforce — https://help.salesforce.com/s/articleView?id=sf.security_overview_2fa.htm&type=5
- Salesforce Help — Enable MFA for Your Entire Salesforce Org — https://help.salesforce.com/s/articleView?id=xcloud.security_mfa_org_wide_setting.htm&type=5 — "From Setup, use the Quick Find box to find and select Identity Verification", then select "Require multi-factor authentication (MFA) for all direct UI logins to your Salesforce org"
- Salesforce Help — My Domain Overview — https://help.salesforce.com/s/articleView?id=sf.domain_name_overview.htm&type=5
- Salesforce Help — Session Settings — https://help.salesforce.com/s/articleView?id=sf.admin_sessions.htm&type=5
- Salesforce Help — Network Access (Trusted IP Ranges) — https://help.salesforce.com/s/articleView?id=sf.security_networkaccess.htm&type=5
- Salesforce Help — CSP Trusted Sites — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
