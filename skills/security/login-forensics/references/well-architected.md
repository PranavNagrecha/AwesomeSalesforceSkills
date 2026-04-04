# Well-Architected Notes — Login Forensics

## Relevant Pillars

- **Security** — Login forensics is a core security operations capability. Reconstructing login timelines, identifying unauthorized access, and confirming MFA enforcement directly support the Security pillar's principle of protecting data and controlling access. Orgs without a login audit practice cannot reliably detect or contain account compromise.
- **Operational Excellence** — Maintaining exportable login history, establishing incident response runbooks for login anomalies, and automating SIEM exports are all operational excellence concerns. Manual UI-based login review does not scale and introduces gaps during high-volume incidents.
- **Reliability** — Login Flows used for step-up authentication must be tested in sandbox before production deployment. A misconfigured Login Flow can block all logins for an attached profile, causing a reliability incident.

## Architectural Tradeoffs

**LoginHistory (free) vs. Login Forensics feature (paid):**
The free `LoginHistory` sObject covers the vast majority of incident response use cases: who logged in, from where, with what browser, and whether they succeeded. The Login Forensics feature in the Event Monitoring add-on adds session-level detail (pages visited, correlated API calls) that is valuable for insider threat investigations but is rarely needed for reactive credential-stuffing response. Start with `LoginHistory` SOQL before recommending the paid feature.

**Native login controls vs. external enforcement:**
Salesforce Login IP Ranges and Login Hours provide free, native controls that enforce login restrictions at the platform level. These should be configured before investing in Login Flows or Transaction Security Policies. Login Flows are powerful but add deployment complexity; Transaction Security Policies require a Shield or Event Monitoring license. Apply the most cost-effective control first.

**6-month retention cliff vs. SIEM investment:**
`LoginHistory` is useful for short-window investigations but fails compliance requirements that demand annual or multi-year lookback. Orgs with PCI DSS, SOX, or HIPAA obligations should treat the 6-month cliff as a forcing function to implement SIEM integration rather than a limitation to work around.

## Anti-Patterns

1. **Treating the Setup > Login History UI as the authoritative investigation tool** — The UI shows only 20,000 records org-wide, does not support cross-user IP pivots, cannot be exported to CSV directly, and does not surface `IdentityVerificationHistory` inline. Using the UI for incident response during a credential stuffing event leads to missed compromises and slow containment. Always use SOQL via Developer Console, REST API, or a scripted exporter.

2. **Assuming Trusted status in IdentityVerificationHistory means MFA was completed** — Compliance reports that count `IdentityVerificationHistory` records with `Status = 'Trusted'` as "MFA enforcement evidence" misrepresent the platform behavior. Trusted records mean the MFA challenge was skipped due to a device or IP allowlist. Auditors who accept this framing are accepting evidence of bypass, not evidence of verification.

3. **Building Login Flows without sandbox testing on the target profile** — A Login Flow error that does not have a correct error-path exit will trap all users on the attached profile in an unresolvable login loop. Always test Login Flows in sandbox with a profile-matched test user, confirm the error path exits cleanly, and have a System Administrator bypass procedure documented before deploying to production.

## Official Sources Used

- Salesforce Security Guide — login history, identity verification, session management behavior
  https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Help: Monitor Login History — LoginHistory object retention, fields, and UI behavior
  https://help.salesforce.com/s/articleView?id=sf.users_login_forensics.htm&type=5
- Salesforce Help: Identity Verification History — IdentityVerificationHistory object and Status values
  https://help.salesforce.com/s/articleView?id=sf.security_overview_identity_verification_history.htm&type=5
- Salesforce Help: Login Flows — Login Flow configuration and profile attachment
  https://help.salesforce.com/s/articleView?id=sf.security_login_flow.htm&type=5
- Salesforce Object Reference: LoginHistory — field definitions, access behavior, retention
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_loginhistory.htm
- Salesforce Well-Architected Overview — Security pillar and Operational Excellence framing
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
