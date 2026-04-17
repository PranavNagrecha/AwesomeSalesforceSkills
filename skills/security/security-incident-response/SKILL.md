---
name: security-incident-response
description: "When to use: active or suspected Salesforce org compromise, unauthorized access investigation, attacker containment, forensic evidence collection from EventLogFile/LoginHistory, session revocation, OAuth token cleanup, eradication of attacker persistence, and post-incident recovery verification. Trigger keywords: org compromised, suspicious login, attacker access, session revocation, forensic investigation, breach response, event log forensics, login anomaly investigation, incident response runbook. Does NOT cover general security setup, permission set design, field-level security configuration, or proactive security hardening — those are separate skills. NOT for general security setup."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how to respond to a Salesforce org compromise"
  - "attacker has access to my Salesforce org what do I do"
  - "how to revoke active sessions and OAuth tokens in Salesforce"
  - "forensic investigation Salesforce EventLogFile"
  - "suspicious login detected in Salesforce what are next steps"
  - "how to contain a Salesforce security breach"
  - "login anomaly detected in Salesforce incident response"
tags:
  - incident-response
  - event-monitoring
  - forensics
  - transaction-security
  - session-management
  - login-anomaly
  - authsession
  - shield
  - breach-response
inputs:
  - Known or suspected attack window (start/end timestamps)
  - Compromised user(s) or IP addresses
  - Salesforce org type (free-tier vs Event Monitoring add-on vs Shield)
  - Access to admin credentials for forensic queries and containment actions
outputs:
  - Forensic evidence export (EventLogFile CSVs, LoginHistory SOQL results, SetupAuditTrail records)
  - Blast-radius assessment (what data was accessed, what config was changed)
  - Containment actions log (sessions revoked, tokens deleted, accounts frozen)
  - Eradication checklist (unauthorized access removed, backdoors closed)
  - Post-incident verification summary
dependencies:
  - security/event-monitoring
  - security/transaction-security-policies
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Security Incident Response — Salesforce

## Overview

This skill covers the complete lifecycle of responding to a suspected or confirmed Salesforce security incident: preserving forensic evidence, containing the attacker, eradicating persistence mechanisms, recovering to a known-good state, and verifying the attacker has been fully removed.

Salesforce incident response differs from traditional IR because evidence lives in platform objects (EventLogFile, LoginHistory, SetupAuditTrail, AuthSession), containment requires both UI and API actions, and evidence retention windows are critically short in free-tier orgs (1-day EventLogFile retention vs. 30-day with Event Monitoring add-on / Shield).

The cardinal rule: **preserve evidence before containment**. In free-tier orgs, beginning containment first risks permanently destroying EventLogFile records before they can be downloaded.

## Key Platform Concepts

### Forensic Evidence Sources

| Source | Retention | License | What It Shows |
|---|---|---|---|
| EventLogFile | 1 day (free) / 30 days (add-on/Shield) | Free tier: 5 event types only | API usage, report exports, logins, data exports, SOQL queries (ApiTotalUsage) |
| LoginHistory | 6 months | Free | Login IP, geolocation, MFA used, login type, browser/client |
| SetupAuditTrail | 180 days | Free | Setup-UI config changes (not Metadata API deploys) |
| AuthSession | Live only | Free | Active sessions — query and DELETE to revoke |
| LoginAnomaly (RTEM) | Real-time | Shield required | ML-scored suspicious login events |

### Event Monitoring Tiers

- **Free tier**: 5 event types (Login, Logout, URI, API, LightningPageView), **1-day retention** — nearly useless for incidents discovered >24 hours after the attack.
- **Event Monitoring add-on**: 70+ event types, **30-day retention** — includes ReportExport, DataExport, ApiTotalUsage, MetadataApiOperation.
- **Shield**: Includes Event Monitoring add-on plus Real-Time Event Monitoring (RTEM) with LoginAnomaly, PermissionSetAssignment, ApiAnomalyEventStore.

### Transaction Security Policy Enforcement Actions

Policies can enforce one of four actions when a matching platform event fires:
- **Block** — prevents the operation from completing
- **Two-Factor Authentication (MFA challenge)** — requires step-up auth
- **Notification** — emails the org admin; no blocking
- **End Session** — terminates the user's current session

Policy configuration: Enhanced Condition Builder (no-code, available Spring '21+) or legacy Apex `PolicyCondition` class. Policies only apply to events fired **after** activation — they are not retroactive.

### Session Revocation

Freezing a user in Setup does not revoke active sessions or OAuth tokens. Full containment requires:
1. Freeze user (blocks new logins) — Setup > Users > Freeze
2. Delete active `AuthSession` records via REST API or Setup > Session Management
3. Revoke OAuth tokens — Setup > Connected Apps > OAuth Usage > Revoke All (per user), or DELETE `AuthToken` records via API

### LoginAnomaly vs. LoginHistory

- **LoginHistory**: free, 6-month retention, shows every login with IP/country/MFA/login type — requires manual analysis to detect anomalies.
- **LoginAnomaly** (Real-Time Event Monitoring): Shield-only, ML-scored events with risk `Score` field — automated detection, but requires a Transaction Security Policy with Notification/Block action to generate admin alerts. The two are **not interchangeable**.

## Recommended Workflow

1. **Scope and license check** — Identify the org's Event Monitoring tier (free / add-on / Shield). Query `EventLogFile` to determine which event types are available and how far back logs exist. If the org is free-tier and the incident window is >24 hours old, assess whether EventLogFile evidence has already expired.

2. **Preserve forensic evidence (before any containment)** — Download all EventLogFile CSVs covering the attack window via REST API. Query and export LoginHistory, SetupAuditTrail, and AuthSession for the affected users. If Shield is active, query LoginAnomaly and ApiAnomalyEventStore. Save all exports externally before proceeding.

3. **Assess blast radius** — Analyze EventLogFile (ReportExport, DataExport, ApiTotalUsage event types) to determine what records were accessed or exported. Check SetupAuditTrail for configuration changes (permission set assignments, connected app creation, profile edits). Cross-reference MetadataApiOperation events for API-based deploys.

4. **Contain the attacker** — Execute in sequence: (a) freeze compromised user accounts; (b) delete active AuthSession records via REST API or Setup > Session Management; (c) revoke OAuth tokens for connected apps used by the attacker; (d) activate or tighten Transaction Security Policies to block ongoing attack vectors (e.g., Block on ReportExport or API usage above threshold).

5. **Eradicate persistence** — Audit and remove: unauthorized connected apps, suspicious Apex classes/triggers installed during the window, anomalous named credentials, newly created admin/privileged users, and any permission set or profile changes that were not authorized. Restore modified Flow metadata to pre-incident versions.

6. **Recover and verify** — Reset credentials for all affected accounts, rotate Named Credential secrets and OAuth client secrets for any compromised integrations, and verify data integrity for records that may have been modified. Confirm the attacker no longer has any access path by re-querying AuthSession and LoginHistory.

7. **Harden for the future** — Configure a Transaction Security Policy for LoginAnomaly (if Shield is licensed) with a Notification action. Implement automated daily EventLogFile export to an external store for ongoing retention beyond the platform default. Document the incident timeline, blast radius, and remediation steps for post-incident review.

## SOQL Reference Queries

### LoginHistory — suspicious logins for a user in a time window
```soql
SELECT Id, UserId, LoginTime, SourceIp, LoginGeo.Country, LoginType,
       AuthenticationServiceId, Status, Browser, Platform, IsMFAEnabled
FROM LoginHistory
WHERE UserId = '005XXXXXXXXXXXXXXX'
  AND LoginTime >= 2026-01-01T00:00:00Z
  AND LoginTime <= 2026-01-10T23:59:59Z
ORDER BY LoginTime DESC
```

### SetupAuditTrail — config changes in attack window
```soql
SELECT Id, Action, Section, Display, CreatedDate, CreatedBy.Username
FROM SetupAuditTrail
WHERE CreatedDate >= 2026-01-01T00:00:00Z
ORDER BY CreatedDate DESC
LIMIT 200
```

### Active sessions for a user
```soql
SELECT Id, UsersId, LoginTime, LastActivityDate, SessionType, SourceIp
FROM AuthSession
WHERE UsersId = '005XXXXXXXXXXXXXXX'
```

### EventLogFile — available event types and dates
```soql
SELECT Id, EventType, LogDate, LogFileLength, LogFileContentType
FROM EventLogFile
WHERE LogDate >= 2026-01-01T00:00:00Z
ORDER BY LogDate DESC
```

### Recently modified Apex classes (detect metadata changes)
```soql
SELECT Id, Name, LastModifiedDate, LastModifiedBy.Username
FROM ApexClass
WHERE LastModifiedDate >= 2026-01-01T00:00:00Z
ORDER BY LastModifiedDate DESC
```

## Official Sources Used

- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Help: Event Monitoring — https://help.salesforce.com/s/articleView?id=sf.bi_setup_enable_event_monitoring.htm&type=5
- Salesforce Help: Transaction Security Policies — https://help.salesforce.com/s/articleView?id=sf.transaction_security_overview.htm&type=5
- Salesforce Help: Real-Time Event Monitoring — https://help.salesforce.com/s/articleView?id=sf.real_time_em_overview.htm&type=5
- Salesforce Help: Login Anomaly Detection — https://help.salesforce.com/s/articleView?id=sf.real_time_em_threat_detection_login_anomaly.htm&type=5
- Salesforce Object Reference: AuthSession — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_authsession.htm
- Salesforce Object Reference: SetupAuditTrail — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_setupaudittrail.htm
- Salesforce Architects: A Primer on Forensic Investigation of Salesforce Security Incidents — https://www.salesforce.com/blog/forensic-investigation-salesforce-security-incidents/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
