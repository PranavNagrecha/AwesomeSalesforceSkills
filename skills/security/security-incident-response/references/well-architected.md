# Well-Architected Notes — Security Incident Response

## Relevant Pillars

- **Security** — Primary pillar. Incident response is entirely a Security concern: evidence preservation, containment, eradication, and verification of attacker removal are all security operations. The skill maps directly to Salesforce's Trusted pillar: protecting data confidentiality, account integrity, and access controls.
- **Operational Excellence** — Incident response readiness requires pre-built runbooks, pre-configured alerting (LoginAnomaly policies, Transaction Security Policies), and documented investigation procedures. Orgs that wait until an incident occurs to figure out forensic tooling are in a severely degraded operational posture.
- **Reliability** — A well-executed IR process ensures service can be restored quickly. Eradication checklists, data integrity verification, and attacker-persistence removal are reliability operations that return the org to a known-good state.

## Architectural Tradeoffs

**Event Monitoring add-on cost vs. forensic capability gap:**
The free tier's 5-event-type, 1-day EventLogFile retention is nearly useless for incident response — most investigations start more than 24 hours after the first attacker action. Orgs that handle sensitive data without the Event Monitoring add-on are making an implicit architectural bet that they will never have a security incident, or that SetupAuditTrail + LoginHistory (both free) will be sufficient. In most cases, that bet is lost: SetupAuditTrail shows admin config changes but not data access; LoginHistory shows login events but not what was queried or exported. Shield or the Event Monitoring add-on is the minimum recommended posture for any org holding PII, financial data, or health data.

**Reactive Transaction Security Policies vs. preventive controls:**
Transaction Security Policies provide real-time blocking capability, but they require Shield or Event Monitoring to configure and they only block events after activation. They are not a substitute for Identity governance (privileged access, least-privilege, MFA), but they provide an important defense-in-depth layer. Architecturally, policies should be configured before an incident as prevention — not created for the first time during one.

**Manual AuthSession deletion vs. Setup > Session Management UI:**
The Setup UI for Session Management is adequate for revoking a single user's sessions. For bulk revocation across multiple compromised accounts, or for scripted/repeatable IR, using the REST API to DELETE `AuthSession` records is more reliable and auditable. The REST API approach also works in headless/automated IR workflows.

**LoginAnomaly ML detection vs. manual LoginHistory analysis:**
LoginAnomaly provides automated detection of suspicious login patterns using ML, but requires Shield. Without Shield, orgs must rely on manual or scripted analysis of LoginHistory — which requires knowing what to look for (unusual IPs, impossible travel, new device fingerprints). LoginAnomaly reduces analyst time for detection but introduces dependency on Salesforce's ML model accuracy and on having the alerting policy correctly configured. Neither approach eliminates the need for the other: even with LoginAnomaly, forensic analysis of LoginHistory is required to establish the full attack timeline.

## Anti-Patterns

1. **Password Reset as Complete Containment** — Resetting a compromised user's password without revoking active sessions and OAuth tokens leaves the attacker in control via existing sessions and refresh tokens. Password reset is one step in a multi-step containment sequence, not the complete response.

2. **Forensic Investigation After Containment** — Containing the incident (freezing accounts, deleting sessions) before preserving forensic evidence risks destroying the very logs needed to understand the blast radius. In free-tier orgs with 1-day EventLogFile retention, running containment first can wipe out all forensic evidence. Always preserve evidence before containment.

3. **Treating SetupAuditTrail as the Complete Audit Log** — SetupAuditTrail covers Setup-UI configuration changes but does not fully capture API-driven metadata deploys, SOQL queries, report exports, or file downloads. Using it as the sole forensic source produces incomplete blast-radius assessments. Combine with EventLogFile (Report, ReportExport, DataExport, ApiTotalUsage) for full picture.

## Official Sources Used

- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
  Used for: overall Salesforce security model, session management, account freeze/revoke procedures
- Salesforce Help: Event Monitoring — https://help.salesforce.com/s/articleView?id=sf.bi_setup_enable_event_monitoring.htm&type=5
  Used for: EventLogFile event types, retention tiers, REST API download procedures
- Salesforce Help: Transaction Security Policies — https://help.salesforce.com/s/articleView?id=sf.transaction_security_overview.htm&type=5
  Used for: enforcement actions (Block, MFA, Notification, End Session), Enhanced Condition Builder availability (Spring '21+), event types supported
- Salesforce Help: Real-Time Event Monitoring — https://help.salesforce.com/s/articleView?id=sf.real_time_em_overview.htm&type=5
  Used for: LoginAnomaly event type, RTEM event object schema, Shield license requirement
- Salesforce Help: Login Anomaly Detection — https://help.salesforce.com/s/articleView?id=sf.real_time_em_threat_detection_login_anomaly.htm&type=5
  Used for: LoginAnomaly ML detection behavior, Score field, SecurityEventData structure
- Salesforce Object Reference: AuthSession — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_authsession.htm
  Used for: AuthSession field schema, DELETE capability for session revocation
- Salesforce Object Reference: SetupAuditTrail — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_setupaudittrail.htm
  Used for: SetupAuditTrail 180-day retention, Section values, free availability
- Salesforce Architects: A Primer on Forensic Investigation of Salesforce Security Incidents — https://www.salesforce.com/blog/forensic-investigation-salesforce-security-incidents/
  Used for: forensic investigation methodology, containment sequence ordering, eradication checklist
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  Used for: Trusted pillar framing, operational excellence posture for IR readiness
