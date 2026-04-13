# Integration User Management — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `integration-user-management`

**Request summary:** (fill in what the user asked for)

**Integration name / system:** (e.g., MuleSoft ETL, Dataloader batch job, External Portal API)

**Target org:** (sandbox / production / scratch org name)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Org-wide MFA enforcement enabled?** Yes / No / Unknown
- **Authentication method:** OAuth Client Credentials / Named Credential / (other — describe)
- **Objects and fields required:**

  | Object | Read | Create | Edit | Delete | Notes |
  |---|---|---|---|---|---|
  | (e.g., Account) | Yes | No | No | No | Billing fields only |
  | | | | | | |

- **Known constraints or limits:** (e.g., API call volume, IP restrictions, certificate requirements)
- **Failure modes to watch for:** MFA waiver missing / permission set license mismatch / Connected App run-as mismatch

---

## Integration User Details

| Field | Value |
|---|---|
| Username | (e.g., mulesoft-erp@company.sf.prod) |
| License | Salesforce Integration |
| Profile | Minimum Access - API Only Integrations |
| Created date | |
| Created by | |

---

## Permission Sets Assigned

| Permission Set Name | PSL | Objects Covered | DML Granted | Assigned Date |
|---|---|---|---|---|
| (e.g., MuleSoft ETL Integration Access) | Salesforce API Integration | Account (Read), Order__c (Create, Edit) | Read, Create, Edit | |
| | | | | |

---

## MFA Waiver

| Field | Value |
|---|---|
| MFA enforcement active in org? | Yes / No |
| Waiver required? | Yes / No |
| Waiver granted via | Permission set: (name) / User permission (direct) |
| Date granted | |
| Approved by | |
| Business justification | Server-to-server integration; no interactive login possible on API Only profile |
| Next review date | (recommended: annual) |

---

## Connected App / Authentication

| Field | Value |
|---|---|
| Connected App name | |
| Auth flow | OAuth 2.0 Client Credentials |
| Run As user | (must match integration user username above) |
| Consumer Key stored in | Named Credential / External Credential / Secure vault |
| IP restrictions configured? | Yes / No |

---

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] New Integration User from Scratch — building a net-new identity for a new integration
- [ ] Scoping Permission Sets Per Integration — auditing or splitting an existing over-permissioned user
- [ ] Other — describe:

---

## Checklist

Complete each item before marking the task done.

- [ ] Integration user created with Salesforce Integration license
- [ ] Profile set to Minimum Access - API Only Integrations (not admin, not standard)
- [ ] All object/field access granted via targeted permission sets (none via profile)
- [ ] Permission sets use the Salesforce API Integration PSL
- [ ] Permission sets scoped to only required objects and DML operations
- [ ] MFA User Exemption assigned if org-wide MFA is enforced (and documented above)
- [ ] Connected App run-as set to this integration user (not an admin user)
- [ ] OAuth Client Credentials flow configured and tested (no username-password flow)
- [ ] Login History verified: Status = Success, LoginType = OAuth 2.0, SourceIp = expected IP
- [ ] Integration user confirmed unable to log in via browser / Salesforce UI
- [ ] This template completed and committed to project record

---

## Login History Verification

Paste the SOQL query used to verify login activity:

```sql
SELECT Id, UserId, LoginTime, Status, LoginType, Application, Browser, SourceIp
FROM LoginHistory
WHERE UserId = '<paste integration user Id here>'
ORDER BY LoginTime DESC
LIMIT 50
```

Expected results:
- Status = `Success`
- LoginType = `OAuth 2.0` (or appropriate for the configured flow)
- Browser = `No User Agent` (confirms API-only; no interactive browser session)
- SourceIp = (matches expected integration infrastructure IP)

---

## Notes

Record any deviations from the standard pattern and why. Include any temporary workarounds and the target date for resolving them.

(e.g., "Org MFA enforcement scheduled for next quarter — MFA waiver will be required then. Calendar reminder set for [date].")
