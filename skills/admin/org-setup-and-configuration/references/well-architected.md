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

## Official Sources Used

- Salesforce Help — MFA for Salesforce — https://help.salesforce.com/s/articleView?id=sf.security_overview_2fa.htm&type=5
- Salesforce Help — My Domain Overview — https://help.salesforce.com/s/articleView?id=sf.domain_name_overview.htm&type=5
- Salesforce Help — Session Settings — https://help.salesforce.com/s/articleView?id=sf.admin_sessions.htm&type=5
- Salesforce Help — Network Access (Trusted IP Ranges) — https://help.salesforce.com/s/articleView?id=sf.security_networkaccess.htm&type=5
- Salesforce Help — CSP Trusted Sites — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
