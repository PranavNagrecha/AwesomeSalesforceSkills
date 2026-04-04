# Well-Architected Notes — Network Security and Trusted IPs

## Relevant Pillars

- **Security** — This skill is primarily a Security pillar skill. Network access controls are a defense-in-depth layer: Login IP Ranges restrict privileged access to known network locations; CSP Trusted Sites prevent unauthorized code injection via external resources; CORS prevents cross-origin API abuse from browser-based attackers. Salesforce Well-Architected frames network security as part of the "Protect Data and Manage Access" principle — controlling not just who can access data (identity) but from where (network) and on what surface (browser CSP).

- **Operational Excellence** — Configuration of Trusted IP Ranges and Login IP Ranges carries operational risk. Misconfigured Login IP Ranges can lock out administrators. Sandbox IP ranges lost on refresh cause repeated manual rework. The operational excellence dimension of this skill is about making network controls maintainable: documenting every range, using templates for post-refresh restoration, and testing restrictions before saving them in production.

- **Reliability** — CSP Trusted Sites and CORS entries are soft reliability concerns: an unconfigured CSP entry causes a silent component failure (external resource blocked) that is not immediately obvious to end users or administrators. Proactive CSP configuration before go-live prevents component degradation in production.

## Architectural Tradeoffs

**Static IP Ranges vs. Real-Time Transaction Security Policies:**
Login IP Ranges are static — they cannot react to dynamic risk signals (e.g., unusual login time, new device). They are simple to configure and require no add-on licenses but provide no adaptive enforcement. Transaction Security Policies (Salesforce Shield / Event Monitoring add-on) can enforce dynamic policies that consider multiple signals simultaneously. For organizations that need adaptive controls, Transaction Security Policies are the correct long-term architectural choice. For organizations with fixed network topologies and budget constraints, Login IP Ranges provide meaningful hardening at no additional cost.

**Org-Wide Trusted IP Ranges vs. Profile Login IP Ranges:**
Trusted IP Ranges are a convenience control (skipping email verification) and should be used liberally for known office and VPN ranges to improve user experience. Profile Login IP Ranges are a hard security control and should be applied conservatively — only to privileged profiles where IP restriction is a genuine security requirement, not to end-user profiles where it would cause widespread access friction.

**CSP Trusted Sites breadth vs. principle of least privilege:**
Each CSP Trusted Site entry is org-wide. Adding a broad domain (e.g., `https://*.example.com` as a wildcard) reduces maintenance overhead but increases the attack surface if any subdomain of `example.com` is compromised and begins serving malicious content. The architectural preference is to use the narrowest specific origin required. Accept the maintenance overhead of separate entries per subdomain for security-sensitive orgs.

## Anti-Patterns

1. **Using Trusted IP Ranges as a login restriction control** — Trusted IP Ranges bypass the email verification challenge but do not deny logins from outside those ranges. Using them with the intent to restrict access is a misconfiguration that provides the appearance of network-based access control without the reality. Login IP Ranges on profiles are the correct control for hard restriction.

2. **Configuring Login IP Ranges on the System Administrator profile without a break-glass recovery plan** — Applying Login IP Ranges to the System Administrator profile without retaining at least one System Administrator account on a non-IP-restricted profile creates a lockout risk. If the VPN goes down, all admins may be locked out simultaneously. Maintain a break-glass System Administrator account on a profile without Login IP Ranges, stored in a credential vault with documented access procedures.

3. **Adding wildcard CORS entries or broad CSP Trusted Sites entries as a shortcut** — Adding `https://*.salesforce.com` to CSP Trusted Sites or `https://*.example.com` to CORS to "fix everything at once" is an anti-pattern that undermines the security value of the allowlist. Enumerate specific origins from the browser console and add only what is required. Review and prune the lists annually.

4. **Failing to document IP ranges at time of configuration** — Trusted IP Ranges and Login IP Ranges have no description field that enforces justification. Without documentation (in the Description field or in a configuration register), ranges accumulate over time and no one knows which ranges are still in use or who added them. Apply the documentation standard in the work template at every configuration event.

## Official Sources Used

- Salesforce Help — Network Access (Trusted IP Ranges) — https://help.salesforce.com/s/articleView?id=sf.security_networkaccess.htm
- Salesforce Help — CSP Trusted Sites — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm
- Salesforce Help — CORS — https://help.salesforce.com/s/articleView?id=sf.security_cors.htm
- Salesforce Help — Set Login Restrictions (Login IP Ranges on Profiles) — https://help.salesforce.com/s/articleView?id=sf.admin_loginrestrict.htm
- Salesforce Help — My Domain Overview — https://help.salesforce.com/s/articleView?id=sf.domain_name_overview.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Well-Architected — Protect Data and Manage Access — https://architect.salesforce.com/well-architected/secure/protect-data-and-manage-access
