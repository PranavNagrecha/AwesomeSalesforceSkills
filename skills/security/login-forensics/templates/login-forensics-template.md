# Login Forensics — Work Template

Use this template when investigating login activity, responding to a suspected account compromise, or configuring login security controls in a Salesforce org.

---

## Scope

**Skill:** `login-forensics`

**Request summary:** (describe what was asked — e.g., "investigate user 005XX for suspicious logins last week", "identify all accounts affected by IP 198.51.100.x", "configure Login Flow for Data Export Admin profile")

**Investigation type:**
- [ ] Reactive — incident response for a suspected compromise
- [ ] Proactive audit — compliance review or threat hunt
- [ ] Configuration — setting up login controls (Login Flow, IP ranges, session timeout)

---

## Context Gathered

Answer these before starting work:

| Question | Answer |
|---|---|
| Does the org have the Event Monitoring add-on? | Yes / No / Unknown |
| Investigation window (start date – end date) | |
| Is the window within the 6-month LoginHistory retention limit? | Yes / No |
| Target user(s) — UserId or username | |
| Suspicious IP or IP range (if known) | |
| Was MFA enabled for the affected user(s) at the time? | |
| Are there active sessions that need to be revoked? | |

---

## Investigation — LoginHistory SOQL

### Single-user login timeline

```soql
SELECT LoginTime, LoginType, SourceIp, Status, Browser, Platform, LoginUrl
FROM LoginHistory
WHERE UserId = '<USER_ID>'
  AND LoginTime >= <START_DATE>T00:00:00Z
  AND LoginTime <= <END_DATE>T23:59:59Z
ORDER BY LoginTime DESC
LIMIT 500
```

Replace `<USER_ID>`, `<START_DATE>`, and `<END_DATE>`.

### Failed logins only (org-wide, narrow time window)

```soql
SELECT UserId, LoginTime, LoginType, SourceIp, Status, Browser, Platform
FROM LoginHistory
WHERE LoginTime >= LAST_N_DAYS:7
  AND Status != 'Success'
ORDER BY LoginTime DESC
LIMIT 1000
```

### IP-based breadth query (find all users who logged in from a suspicious IP)

```soql
SELECT UserId, LoginTime, SourceIp, Status, Browser
FROM LoginHistory
WHERE SourceIp LIKE '<IP_PREFIX>.%'
  AND LoginTime >= LAST_N_DAYS:30
ORDER BY LoginTime DESC
LIMIT 1000
```

Replace `<IP_PREFIX>` with the suspicious IP prefix (e.g., `198.51.100`).

### Identity verification check (MFA bypass detection)

```soql
SELECT UserId, VerificationTime, Activity, Status, Comments
FROM IdentityVerificationHistory
WHERE UserId = '<USER_ID>'
  AND VerificationTime >= LAST_N_DAYS:30
ORDER BY VerificationTime DESC
LIMIT 200
```

Status values to flag: `Skipped`, `Failure`. Investigate `Trusted` records if the org policy does not allow trusted devices.

---

## Investigation — Login Forensics Feature (Event Monitoring Add-On Only)

If the org has the Event Monitoring add-on:

1. Navigate to Setup > Login Forensics
2. Filter by username and date range
3. Drill into individual sessions for page visit history and correlated API activity
4. Export session data for SIEM ingestion if needed

---

## Findings Summary

| Finding | Severity | Evidence |
|---|---|---|
| (describe finding) | High / Medium / Low | (SOQL query name, result count, or Setup location) |

---

## Remediation Actions

### Immediate (if active compromise suspected)

- [ ] Freeze affected user: Setup > Users > Edit > uncheck "Active"
- [ ] Revoke active sessions: Setup > Session Management, filter by user, revoke all
- [ ] Reset password and notify user via out-of-band channel (not email if email is compromised)
- [ ] Remove trusted devices: Setup > Identity Verification > remove all trusted devices for user

Apex snippet for programmatic session revocation (run via Developer Console):

```apex
Auth.SessionManagement.revokeSessionsForUser(
    '<USER_ID>',
    Auth.SessionManagement.REVOKEALLSESSIONS_TYPE.ALL_SESSIONS
);
```

### Short-term (within 48 hours)

- [ ] Add Login IP Ranges to affected profile to restrict access to known CIDR blocks
- [ ] Review Login Hours restrictions — are they appropriate for this profile?
- [ ] Check whether Event Monitoring is exporting to SIEM for ongoing alerting

### Long-term (within 2 weeks)

- [ ] Implement automated `LoginHistory` export to SIEM for retention beyond 6 months
- [ ] Consider Login Flow for step-up authentication on high-privilege profiles
- [ ] Review Transaction Security Policies for country-based login blocking (event-monitoring skill)

---

## Login Flow Configuration (if applicable)

**Profile to attach:** _______________
**Flow name:** _______________
**Sandbox tested?** Yes / No
**Error exit path verified?** Yes / No

Steps:
1. Build Screen Flow in Flow Builder (type: Screen Flow)
2. Setup > Login Flows > New
3. Connect Flow to target profile
4. Test in sandbox with a user on that profile
5. Confirm that a flow error produces a clean error screen, not a login loop
6. Deploy to production after sandbox validation

---

## Checklist

Copy from SKILL.md review checklist and tick as completed:

- [ ] Confirmed whether org has Event Monitoring add-on
- [ ] SOQL queries filtered by `LoginTime` range (avoid 30,000-row truncation)
- [ ] Cross-user IP pivot query run to assess credential stuffing scope
- [ ] `IdentityVerificationHistory` reviewed for `Skipped` or unexpected `Trusted` statuses
- [ ] Compromised accounts frozen and sessions revoked
- [ ] Investigation window confirmed within 6-month `LoginHistory` retention limit
- [ ] If Login Flow configured: tested in sandbox before production deployment

---

## Notes

(Record deviations from standard pattern, org-specific constraints, or open questions)
