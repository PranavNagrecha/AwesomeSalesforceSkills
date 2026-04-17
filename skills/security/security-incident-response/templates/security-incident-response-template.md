# Security Incident Response Runbook — Salesforce

> **Template usage:** Copy this file, rename it with the incident identifier (e.g., `IR-2026-001-runbook.md`), and fill in each section as the investigation proceeds. Do not leave placeholders in a completed runbook.

---

## Incident Metadata

| Field | Value |
|---|---|
| Incident ID | IR-YYYY-NNN |
| Detected At | YYYY-MM-DDTHH:MM:SSZ |
| Detected By | (Admin name / automated alert / ticket) |
| Org ID | (15- or 18-char Org ID) |
| Org Type | Production / Full Sandbox / Partial Sandbox |
| Event Monitoring Tier | Free (1-day / 5 types) / Add-on (30-day / 70+ types) / Shield |
| Initial Severity | P1 (active exfiltration) / P2 (confirmed access) / P3 (suspected access) |
| Incident Commander | |
| Scribe / Documenter | |

---

## Phase 1: Preserve Evidence

> **Complete this phase entirely before starting containment.**
> In free-tier orgs, EventLogFile records expire after ~24 hours. Download them first.

### 1.1 Confirm Event Monitoring Tier

Run in Salesforce Developer Console or Workbench (SOQL):

```soql
SELECT EventType, LogDate, LogFileLength, LogFileContentType
FROM EventLogFile
WHERE LogDate >= LAST_N_DAYS:30
ORDER BY LogDate DESC
```

- [ ] Record available event types and earliest log date:
  - Earliest available log date: _______________
  - Event types available: _______________
  - Tier conclusion: Free / Add-on / Shield

### 1.2 Download EventLogFile CSVs

For each EventLogFile record in the attack window, download the CSV via REST:

```
GET /services/data/v60.0/sobjects/EventLogFile/{Id}/LogFile
Authorization: Bearer {ACCESS_TOKEN}
```

Priority event types to download first:
- `ReportExport` — records every report exported to CSV/Excel
- `DataExport` — data export wizard activity
- `ApiTotalUsage` — SOQL and API call volume per user
- `MetadataApiOperation` — Metadata API deploys (add-on required)
- `Report` — report view events (not just exports)
- `Login` — successful and failed logins
- `LoginAs` — admin "login as user" events

- [ ] EventLogFile CSVs downloaded and saved to: _______________
- [ ] Download timestamp: _______________

### 1.3 Export LoginHistory

```soql
SELECT Id, UserId, User.Username, LoginTime, SourceIp,
       LoginGeo.Country, LoginGeo.City, LoginType,
       AuthenticationServiceId, Status, Browser, Platform,
       IsMFAEnabled, LoginSubType
FROM LoginHistory
WHERE LoginTime >= {ATTACK_WINDOW_START}
  AND LoginTime <= {ATTACK_WINDOW_END}
ORDER BY LoginTime DESC
```

- [ ] LoginHistory exported. Records count: _______________
- [ ] Suspicious IPs/countries identified: _______________

### 1.4 Export SetupAuditTrail

```soql
SELECT Id, Action, Section, Display, CreatedDate,
       CreatedBy.Username, CreatedBy.Id, DelegateUser
FROM SetupAuditTrail
WHERE CreatedDate >= {ATTACK_WINDOW_START}
ORDER BY CreatedDate DESC
LIMIT 500
```

- [ ] SetupAuditTrail exported. Records count: _______________
- [ ] Suspicious config changes identified: _______________

### 1.5 Snapshot Active Sessions for Affected Users

```soql
SELECT Id, UsersId, Users.Username, LoginTime, LastActivityDate,
       SessionType, SourceIp, LoginGeoId, ParentId, UserType
FROM AuthSession
WHERE UsersId IN ({USER_ID_LIST})
```

- [ ] AuthSession snapshot exported. Active sessions: _______________

### 1.6 (Shield only) Export Real-Time Event Monitoring Data

```soql
SELECT EventDate, UserId, User.Username, Score, SecurityEventData,
       SourceIp, PolicyId
FROM LoginAnomalyEventStore
WHERE EventDate >= {ATTACK_WINDOW_START}
ORDER BY Score DESC
```

```soql
SELECT EventDate, UserId, User.Username, Score, SecurityEventData,
       ApiType, ApiFamily, HttpMethod
FROM ApiAnomalyEventStore
WHERE EventDate >= {ATTACK_WINDOW_START}
ORDER BY Score DESC
```

- [ ] RTEM events exported (if Shield). Records: _______________

---

## Phase 2: Contain

> Start containment only after Phase 1 is complete and evidence is saved externally.

### 2.1 Freeze Compromised User Accounts

For each compromised user:
- Setup > Users > Find user > Freeze

Or via API:
```
PATCH /services/data/v60.0/sobjects/User/{UserId}
{"IsFrozen": true}
```

| User | Frozen At | Frozen By |
|---|---|---|
| | | |
| | | |

### 2.2 Delete Active Sessions (AuthSession)

For each session identified in Phase 1.5:

```
DELETE /services/data/v60.0/sobjects/AuthSession/{SessionId}
```

Or bulk via Setup > Session Management > filter by user > terminate.

- [ ] Sessions deleted. Count: _______________
- [ ] Deletion timestamp: _______________

### 2.3 Revoke OAuth Tokens

Navigate to: Setup > Connected Apps > OAuth Usage > find the Connected App > Revoke All for affected user(s).

Or query and delete via API:

```soql
SELECT Id, AppName, UserId, UseCount, LastUsedDate
FROM ConnectedApplication
WHERE UserId IN ({USER_ID_LIST})
```

- [ ] OAuth tokens revoked. Apps affected: _______________

### 2.4 Disable or Restrict Suspected Connected Apps

If a specific Connected App was used in the attack:
- Setup > Connected Apps > Edit > set IP Relaxation to "Enforce IP Restrictions"
- Or disable the app entirely until investigation is complete

- [ ] Connected App actions taken: _______________

### 2.5 Activate Transaction Security Policies to Block Ongoing Vectors

Examples of reactive policies to activate during active incidents:
- Block ReportExport for all users except System Administrator profile
- Block DataExport events
- Notify on API usage > 500 calls per hour per user

- [ ] Policies activated: _______________
- [ ] Activation timestamp (important for forensic timeline): _______________

---

## Phase 3: Eradicate

### 3.1 Audit for Unauthorized Users or Profile Changes

```soql
SELECT Id, Username, IsActive, ProfileId, Profile.Name,
       LastModifiedDate, LastModifiedBy.Username, CreatedDate, CreatedBy.Username
FROM User
WHERE LastModifiedDate >= {ATTACK_WINDOW_START}
ORDER BY LastModifiedDate DESC
```

- [ ] No unauthorized users created: YES / NO
- [ ] No unauthorized profile/permission set changes: YES / NO
- [ ] Unauthorized changes found: _______________

### 3.2 Audit for Unauthorized Connected Apps

```soql
SELECT Id, Name, CreatedDate, CreatedBy.Username, LastModifiedDate
FROM ConnectedApplication
WHERE CreatedDate >= {ATTACK_WINDOW_START}
ORDER BY CreatedDate DESC
```

- [ ] Unauthorized Connected Apps found: YES / NO
- [ ] Actions taken: _______________

### 3.3 Audit for Unauthorized Apex / Flow Changes

```soql
SELECT Id, Name, LastModifiedDate, LastModifiedBy.Username, Status
FROM ApexClass
WHERE LastModifiedDate >= {ATTACK_WINDOW_START}
ORDER BY LastModifiedDate DESC
```

```soql
SELECT Id, DeveloperName, LastModifiedDate, LastModifiedBy.Username, Status
FROM Flow
WHERE LastModifiedDate >= {ATTACK_WINDOW_START}
ORDER BY LastModifiedDate DESC
```

- [ ] Unauthorized Apex changes found: YES / NO
- [ ] Unauthorized Flow changes found: YES / NO
- [ ] Metadata restored from source control: YES / NO / N/A

### 3.4 Audit Named Credentials

```soql
SELECT Id, DeveloperName, LastModifiedDate, LastModifiedBy.Username
FROM NamedCredential
WHERE LastModifiedDate >= {ATTACK_WINDOW_START}
```

- [ ] Unauthorized Named Credential changes found: YES / NO

### 3.5 Reset Credentials

- [ ] Compromised user passwords reset
- [ ] MFA enforced or verified for affected user profiles
- [ ] Connected App client secrets rotated for any apps used in the attack
- [ ] Named Credential secrets rotated as needed
- [ ] API keys or external integration credentials rotated as needed

---

## Phase 4: Recover

### 4.1 Restore Data Integrity

Based on EventLogFile analysis, identify records that may have been modified:

```soql
SELECT Id, Name, LastModifiedDate, LastModifiedBy.Username
FROM {OBJECT_API_NAME}
WHERE LastModifiedDate >= {ATTACK_WINDOW_START}
  AND LastModifiedBy.Username = '{COMPROMISED_USER}'
ORDER BY LastModifiedDate DESC
```

- [ ] Data integrity verified: YES / NO / PARTIAL
- [ ] Records requiring restore: _______________
- [ ] Restore method: manual / data loader / backup restore

### 4.2 Re-enable Affected Users

After eradication is confirmed:
- Unfreeze affected legitimate users (PATCH User IsFrozen = false)
- Confirm MFA is enforced before re-enabling

- [ ] Users re-enabled: _______________
- [ ] Re-enable timestamp: _______________

### 4.3 Remove Reactive Transaction Security Policies or Adjust

Reactive policies activated in Phase 2 may be too broad for permanent use:
- Review each policy
- Adjust thresholds or scope
- Document policies that should remain permanently

- [ ] Policies reviewed and adjusted: _______________

---

## Phase 5: Post-Incident Hardening and Verification

### 5.1 Verify No Remaining Attacker Access

```soql
SELECT Id, UsersId, Users.Username, SourceIp, LoginTime, SessionType
FROM AuthSession
WHERE UsersId IN ({AFFECTED_USER_ID_LIST})
```

Expected result: 0 records, or only legitimate sessions from known IPs.

- [ ] No remaining attacker sessions: YES / NO

### 5.2 Verify LoginAnomaly Alerting is Configured (Shield only)

Confirm a Transaction Security Policy exists for LoginAnomaly with Notification or Block action.

- [ ] LoginAnomaly policy verified: YES / NO / N/A (no Shield)

### 5.3 Configure Ongoing EventLogFile Export

To avoid future forensic evidence gaps, set up automated daily EventLogFile export:
- Use a scheduled integration (MuleSoft, custom Apex, or external scheduler) to query and download EventLogFile CSVs daily
- Store in an external SIEM or S3-compatible store with longer retention (90+ days recommended)

- [ ] Automated export configured: YES / NO / Deferred
- [ ] Target storage: _______________

---

## Blast Radius Summary

| Category | Details |
|---|---|
| Affected users | |
| Attack window (confirmed) | |
| Data accessed (objects/reports) | |
| Data exported (if any) | |
| Config changes made | |
| Metadata changes (Apex/Flow) | |
| Persistence mechanisms found | |
| Estimated records accessed | |
| PII/sensitive data in scope | YES / NO / UNKNOWN |

---

## Timeline

| Timestamp (UTC) | Event |
|---|---|
| | Incident first detected |
| | Evidence preservation started |
| | Evidence preservation complete |
| | Containment started |
| | Containment complete |
| | Eradication started |
| | Eradication complete |
| | Recovery started |
| | Recovery complete |
| | Incident closed |

---

## Lessons Learned

- What detection/monitoring gaps were exposed?
- What process gaps caused delay?
- What controls would have prevented or detected the incident earlier?
- Recommended hardening actions and owners:

| Action | Owner | Target Date |
|---|---|---|
| | | |
| | | |

---

*Generated from: `skills/security/security-incident-response/templates/security-incident-response-template.md`*
