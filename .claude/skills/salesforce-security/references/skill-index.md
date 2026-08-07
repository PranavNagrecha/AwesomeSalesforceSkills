# SfSkills — `security` skill roster (48 packages)

The zero-setup lookup path: this file ships with the plugin and needs
no search index. Scan it, pick a package by name, then read that
package from the repository root under `${CLAUDE_PLUGIN_ROOT}`.

Generated from `registry/skills.json` by `scripts/build_plugin.py`.
Do not hand-edit.

**How to read a gloss.** The package id is on the line already, so the
gloss does not repeat it. It carries what the id cannot, in this order:
the package's own **trigger vocabulary** (the phrasings that should
land here), then its **`NOT for …` redirect** (which names the package
to use instead), then a short scope phrase if there is room. A
`…` marks a truncation, always at a word, keyword or
whole-clause boundary. Budget: 220 characters.

**A `NOT for X - use Y` clause is the most useful thing on the line.**
If your question is X, stop and open Y instead of this package.

- `skills/security/apex-managed-sharing-patterns/SKILL.md` — Grant row-level access programmatically via __Share records when declarative sharing rules cannot express the policy. NOT for OWD, role hierarchy, or criteria-based sharing rule design.
- `skills/security/api-only-user-hardening/SKILL.md` — Provision and harden integration (API-only) users: no UI login, IP restrictions, minimum permission set, session lifetime, and monitoring. NOT for human admin account hardening.
- `skills/security/api-security-and-rate-limiting/SKILL.md` — Triggers: 'API rate limit', '429 error', 'OAuth scope restriction', 'Connected App IP restriction', 'API usage monitoring', 'concurrent API limits', …. NOT for OAuth flow implementation, token exchange mechanics, or …
- `skills/security/certificate-and-key-management/SKILL.md` — creating, uploading, or rotating certificates in Salesforce, configuring mutual …. NOT for Named Credential configuration (use named-credentials-setup skill), NOT for Shield Platform Encryption key management. Trigger …
- `skills/security/clickjack-and-frame-protection/SKILL.md` — Configure clickjack protection headers and frame-ancestors for VF pages, LWR sites, and Aura apps. NOT for CSP or Trusted URL configuration.
- `skills/security/connected-app-security-policies/SKILL.md` — Managing OAuth policies, IP relaxation, session security, PKCE, and credential rotation for …. NOT for basic Connected App setup or creation. NOT for OAuth flow implementation (use oauth-flows-and-connected-apps).
- `skills/security/csp-and-trusted-urls/SKILL.md` — Configure Content Security Policy via Trusted URLs and CSP Trusted Sites so Lightning, LWR, and LWC can call third-party scripts, APIs, and frame …. NOT for clickjack configuration.
- `skills/security/customer-data-request-workflow/SKILL.md` — Implement GDPR/CCPA data subject rights (access, deletion, rectification) using Salesforce Privacy Center and/or custom workflow. NOT for general backup or org-level data retention policy.
- `skills/security/data-classification-labels/SKILL.md` — Classify Salesforce fields by data sensitivity and compliance category using the four built-in classification attributes …. NOT for data masking, Shield Platform Encryption, or runtime access control enforcement.
- `skills/security/dynamic-sharing-recalculation/SKILL.md` — Force or orchestrate sharing recalculation after bulk data loads, rule changes, or user/role reorgs so row access catches up with policy. NOT for designing new sharing rules — use sharing-selection tree.
- `skills/security/encrypted-field-query-patterns/SKILL.md` — Design SOQL, filters, reporting, and indexes against Shield Platform Encryption fields. Triggers: Shield Platform Encryption, encrypted field query, probabilistic vs deterministic encryption, encrypted SOQL filter, ….
- `skills/security/event-monitoring/SKILL.md` — Shield Event Monitoring: event log types, downloading logs via REST API and …. NOT for debug logs (use debug-logs-and-developer-console). NOT for custom platform event publishing/subscribing (use platform-events-apex).
- `skills/security/experience-cloud-security/SKILL.md` — configuring access controls, sharing, or site security for authenticated or guest Experience Cloud (community) users: external OWD, Sharing …. NOT for internal sharing model configuration (use sharing-and-visibility).
- `skills/security/ferpa-compliance-in-salesforce/SKILL.md` — Triggers: FERPA, student records privacy, LearnerProfile, parental disclosure, directory information opt-out, education data privacy, student consent, …. NOT for GDPR/CCPA general data privacy (see gdpr-data-privacy …
- `skills/security/field-audit-trail/SKILL.md` — Salesforce Shield Field Audit Trail: configuration, retention policies, querying archived field data, compliance requirements. NOT for field history tracking (use field-history-tracking).
- `skills/security/file-upload-virus-scanning/SKILL.md` — Triggers: 'virus scan salesforce upload', 'malware scan content version', 'quarantine uploaded file', 'clamav salesforce', 'file upload security'. NOT for field-level data validation.
- `skills/security/gdpr-data-privacy/SKILL.md` — Triggers: GDPR, data privacy, consent management, right to erasure, Individual object, ContactPointConsent, ShouldForget, data subject request, Privacy Center, …. NOT for general data quality cleanup, duplicate …
- `skills/security/guest-user-security/SKILL.md` — hardening the Experience Cloud guest user profile, controlling unauthenticated access to records …. NOT for Experience Cloud site creation (use Experience Cloud skills) or for authenticated external user security (use …
- `skills/security/guest-user-security-audit/SKILL.md` — Auditing the security posture of an Experience Cloud (Community) site's Guest …. NOT for Experience Cloud authenticated user setup (see experience/experience-cloud-user-management), NOT for general Salesforce profile …
- `skills/security/ip-range-and-login-flow-strategy/SKILL.md` — Design and implement Salesforce Login Flows (Screen Flows assigned to …. NOT for static IP allowlisting or profile Login IP Ranges (see network-security-and-trusted-ips), org-wide session policies, or SSO/SAML …
- `skills/security/ip-relaxation-and-restriction/SKILL.md` — Design IP-based access controls: profile login IP …. Triggers: login IP range, trusted IP, IP relaxation, restricted IP, IP allowlist, login hours. Does NOT cover: network-layer firewalling, corporate VPN design, ….
- `skills/security/login-forensics/SKILL.md` — Investigate Salesforce login activity using LoginHistory, IdentityVerificationHistory, and Login Forensics (Event Monitoring add-on): reconstruct …. NOT for MFA setup (use org-setup-and-configuration).
- `skills/security/mfa-enforcement-patterns/SKILL.md` — Design MFA enforcement: auto-enablement, Salesforce Authenticator …. Triggers: MFA, multi-factor, two-factor, Salesforce Authenticator, MFA exception, MFA SSO, api-only MFA. Does NOT cover: end-user password policies, ….
- `skills/security/mfa-enforcement-strategy/SKILL.md` — Plan and operate Salesforce org-wide multi-factor authentication (MFA) enforcement: verification methods …. NOT for designing Login Flow post-authentication logic, IP allowlists, or conditional step-up policies—use …
- `skills/security/network-security-and-trusted-ips/SKILL.md` — Configure and audit Salesforce network security controls — trusted IP ranges (org-wide Network Access), login IP …. NOT for org-wide session settings, MFA configuration, or real-time Transaction Security Policies.
- `skills/security/oauth-redirect-and-domain-strategy/SKILL.md` — Design Connected App OAuth callback URLs, My Domain naming, Enhanced Domains cutover, and cross-environment …. Triggers: oauth redirect uri, connected app callback, my domain, enhanced domains, sandbox url change, ….
- `skills/security/oauth-token-management/SKILL.md` — work depends on how Salesforce OAuth access and refresh tokens are issued …. NOT for choosing which OAuth grant or Connected App flow to implement (use integration/oauth-flows-and-connected-apps), Named Credential …
- `skills/security/org-hardening-and-baseline-config/SKILL.md` — defining or reviewing baseline org …. Triggers: 'org hardening', 'baseline security config', 'Health Check', 'CSP trusted sites', 'clickjack protection'. NOT for feature-level app permissions or record-sharing design.
- `skills/security/permission-set-groups-and-muting/SKILL.md` — Triggers: 'permission set group', 'muting permission set', 'profiles to permission sets', 'PSG architecture', 'muted permissions'. NOT for record-sharing design or CRUD/FLS review in Apex code.
- `skills/security/platform-encryption/SKILL.md` — deciding which Salesforce fields to encrypt at rest, choosing between …. NOT for TLS/transport encryption, Classic Encrypted Text fields, or field masking without Shield. Trigger keywords: Shield Platform …
- `skills/security/privileged-access-management/SKILL.md` — Design just-in-time elevation, break-glass accounts, and audit trails for Modify All Data / System Admin / Customize Application permissions. NOT for regular permission set design.
- `skills/security/recaptcha-and-bot-prevention/SKILL.md` — Triggers: 'enable reCAPTCHA on Web-to-Case', 'bot spam submissions on my Experience Site', 'Headless Identity reCAPTCHA v3 setup'. NOT for AppExchange security review (use secure-coding-review-checklist), NOT for …
- `skills/security/record-access-troubleshooting/SKILL.md` — Diagnose why a user can or cannot see/edit a record: UserRecordAccess SOQL, Why Can a …. NOT for field-level security (use field-level-security-audit). NOT for designing sharing (use sharing-selection decision tree).
- `skills/security/salesforce-shield-deployment/SKILL.md` — Roll out Shield (Platform Encryption + Event Monitoring + Field Audit Trail) end-to-end, sequencing feature enablement to avoid data lockout. NOT for Classic Encryption or general PE design.
- `skills/security/sandbox-data-masking/SKILL.md` — Triggers: data mask, sandbox masking, PII in sandbox, GDPR sandbox, HIPAA non-production, mask contacts, obfuscate fields non-production. NOT for sandbox refresh mechanics (use sandbox-refresh-and-templates), NOT for …
- `skills/security/scim-provisioning-integration/SKILL.md` — Triggers: 'scim provisioning', 'okta scim salesforce', 'entra salesforce provisioning', 'user deactivation automation', 'group to permission set mapping'. NOT for SSO/authentication setup (see single-sign-on skills).
- `skills/security/secure-coding-review-checklist/SKILL.md` — Use this skill to audit Apex, Visualforce, LWC, and Aura code for Salesforce security review …. NOT for network-level penetration testing, Shield Platform Encryption key management, or general org permission set design.
- `skills/security/security-health-check/SKILL.md` — Triggers: 'security health check score', 'health check failing settings', 'custom baseline', 'remediate health check findings', 'fix risk'. NOT for org hardening implementation, permission model design, or broad …
- `skills/security/security-incident-response/SKILL.md` — When to use: active or suspected …. Triggers: org compromised, suspicious login, attacker access, session revocation, forensic investigation, breach response, event log forensics, …. NOT for general security setup.
- `skills/security/service-account-credential-rotation/SKILL.md` — designing credential rotation for integration …. Triggers: 'rotate integration user password', 'connected app secret rotation', 'named credential rotation', 'stale service account', …. NOT for end-user password policies.
- `skills/security/session-high-assurance-policies/SKILL.md` — Enforce step-up authentication for sensitive pages/objects using High Assurance session level and login flow policies. NOT for initial MFA enrollment UX.
- `skills/security/session-management-and-timeout/SKILL.md` — configuring session timeout values, concurrent session limits, session IP locking, or logout behavior in Salesforce. Covers …. NOT for OAuth token refresh flows, login IP ranges, or MFA/identity-provider configuration.
- `skills/security/shield-event-log-retention-strategy/SKILL.md` — Triggers: 'shield event log retention', 'route event monitoring to splunk', 'how long to keep login history', 'siem salesforce integration', …. NOT for enabling Shield (see salesforce-shield-deployment).
- `skills/security/shield-kms-byok-setup/SKILL.md` — Configure Shield Platform Encryption with customer-supplied (BYOK) or customer-held (Cache-Only Key Service) tenant secrets, rotate them, and recover. NOT for Classic Encryption or field masking.
- `skills/security/sso-saml-troubleshooting/SKILL.md` — Diagnosing broken SAML SSO into Salesforce — IdP-initiated vs SP-initiated flows …. NOT for OAuth / OpenID Connect SSO (see security/oauth-openid-troubleshooting), NOT for setting up SSO from scratch (see …
- `skills/security/transaction-security-policies/SKILL.md` — Transaction Security policy creation and configuration: condition builder …. NOT for Event Monitoring log analysis or Shield Event Monitoring setup (use event-monitoring). NOT for Apex testing or debug-log analysis.
- `skills/security/visualforce-security-and-modernization/SKILL.md` — Triggers: 'should I rewrite this Visualforce page in LWC', 'CSRF protection disabled on Visualforce page is that safe', …. NOT for greenfield Visualforce architecture (use apex/visualforce-fundamentals — controller …
- `skills/security/xss-and-injection-prevention/SKILL.md` — Triggers: 'XSS in Visualforce', 'SOQL injection vulnerability', 'how to encode output in Apex', 'JSENCODE Visualforce', 'open redirect prevention'. NOT for Apex CRUD/FLS enforcement (use soql-security or …

