# Well-Architected Notes — Session Management And Timeout

## Relevant Pillars

- **Security** — Session management is a core security control. Proper timeout configuration prevents unauthorized access from unattended workstations, limits the window of exposure if a session token is compromised, and enforces the principle of least privilege over time. Concurrent session limits prevent credential sharing, which undermines auditability and individual accountability. Session IP locking provides a defense against session hijacking by binding the session to the originating IP address.

- **Reliability** — Overly aggressive session timeouts cause reliability problems for users. If users are forced to re-authenticate in the middle of complex data entry, unsaved work is lost. This creates a perception that the platform is unreliable and drives workaround behaviors (browser auto-refresh, saving partial records) that introduce data quality issues. The timeout hierarchy must balance security requirements against the operational reality of how users interact with the system.

- **Operational Excellence** — Session configuration should be managed as code via the Metadata API SecuritySettings type, deployed through CI/CD pipelines, and version-controlled. Manual Setup clicks are error-prone and non-repeatable across environments. Documenting the effective timeout per user persona (accounting for the minimum-wins rule across all three layers) is essential for change management and compliance audits.

## Architectural Tradeoffs

The central tradeoff is **security stringency vs. user productivity**. Shorter timeouts reduce the window of exposure but increase re-authentication friction. The three-tier timeout hierarchy (org, profile, Connected App) provides granular control to resolve this tradeoff per user population rather than applying a single value globally.

A secondary tradeoff is **session IP locking vs. mobile/remote access flexibility**. IP locking is a strong anti-hijacking control, but it is incompatible with network environments where the egress IP changes (mobile carriers, VPNs with rotating exit nodes, split-tunnel networks). Enabling it without analyzing the network topology causes legitimate users to be locked out.

Concurrent session limits create a tradeoff between **preventing credential sharing and supporting legitimate multi-device use**. Setting the limit too low (1-2) blocks users who move between devices. Setting it too high (15-20) provides little protection against sharing.

## Anti-Patterns

1. **Single-tier timeout for all users** — Setting one aggressive org-wide timeout to satisfy compliance for a small admin population, punishing all users. Instead, use profile-level overrides to differentiate. The org-wide value should be the most permissive acceptable default, with profiles tightening for specific groups.

2. **Ignoring the Connected App timeout layer** — Configuring org-wide and profile timeouts carefully but ignoring Connected App session policies. A Connected App with a very short timeout can cause unexpected logouts for users authenticating through it. A Connected App with no timeout configured may effectively bypass intended restrictions if the user's session through that app is not subject to the profile override.

3. **Manual session configuration without metadata deployment** — Configuring session settings via Setup clicks in production without a corresponding Metadata API SecuritySettings component in version control. This leads to configuration drift between environments and makes it impossible to audit, reproduce, or roll back session policy changes.

## Official Sources Used

- Session Settings — https://help.salesforce.com/s/articleView?id=sf.admin_sessions.htm
- Metadata API SecuritySettings — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_securitysettings.htm
- Salesforce Well-Architected Trusted Security — https://architect.salesforce.com/well-architected/trusted/security
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
