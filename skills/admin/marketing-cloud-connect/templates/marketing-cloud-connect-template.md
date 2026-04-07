# Marketing Cloud Connect — Work Template

Use this template when configuring, auditing, or troubleshooting Marketing Cloud Connect for a Salesforce org.

## Scope

**Skill:** `marketing-cloud-connect`

**Request summary:** (fill in what the user asked for — setup, sync issue, scope issue, triggered send, tracking gap)

**Out of scope:** MCAE/Pardot connector, Marketing Cloud Growth Edition, custom REST API MC integrations

---

## Context Gathered

Answer these before taking action:

- **MC Connect package installed?** Yes / No / Unknown
  - Package namespace: `et4ae5` — verify in Setup > Installed Packages
- **Connector user username:** ____________________
  - Is it a standard internal Salesforce user (not community/portal)? Yes / No
  - Marketing Cloud permission set assigned? Yes / No
  - API Enabled on profile? Yes / No
  - Password expiration policy: Never Expires / Expires (risk)
- **MC account type:** Single-org / Enterprise 2.0 multi-BU
- **Number of connected Business Units:** ____
- **Current scope setting:**
  - Salesforce side (MC Connect > Configuration): Org-Wide / BU-specific / Unknown
  - Marketing Cloud side (Setup > Salesforce Integration): Org-Wide / BU-specific / Unknown
- **Synchronized objects enabled:** (check all that apply)
  - [ ] Contact  [ ] Lead  [ ] Campaign  [ ] CampaignMember  [ ] Case  [ ] Other: ____
- **Field counts for synced objects:** (fill in for each)
  - Contact: _____ fields (limit: 250)
  - Lead: _____ fields (limit: 250)
  - Other: _____ fields (limit: 250)
- **Last SDS sync timestamp:** ____________________ (check MC Contact Builder > Data Sources)
- **Known failure mode:** ____________________

---

## Approach

Which pattern from SKILL.md applies? Choose one:

- [ ] **Initial Setup** — installing package, creating connector user, connecting account, enabling SDS
- [ ] **Scope Mismatch Diagnosis** — missing subscribers, lower-than-expected audience counts
- [ ] **SDS Sync Stall** — sync not running, timestamp not advancing
- [ ] **Triggered Send Setup** — Flow/Process Builder to MC transactional email
- [ ] **Tracking Write-Back Gap** — Campaign Member activity not populating after sends
- [ ] **Connector User Remediation** — broken auth, password/profile change recovery
- [ ] **Data Hygiene / GDPR Deletion** — deleted SF records still in MC, compliance gap

**Pattern justification:** (explain why this pattern fits the situation)

---

## Checklist

Work through in order:

### Prerequisites
- [ ] MC Connect managed package (et4ae5) is installed in the Salesforce org
- [ ] Connector user exists, is a standard internal user, has Marketing Cloud permission set
- [ ] Connector user profile has API Enabled = true
- [ ] Connector user is excluded from org-wide password expiration policy

### Connection
- [ ] MC Connect > Configuration shows status: **Connected**
- [ ] If not connected: re-authenticate in Marketing Cloud Setup > Salesforce Integration with connector user credentials
- [ ] Marketing Cloud account ID confirmed and Business Unit mapping documented

### Scope
- [ ] Scope setting confirmed on Salesforce side (MC Connect > Configuration)
- [ ] Scope setting confirmed on Marketing Cloud side (Setup > Salesforce Integration)
- [ ] Scope settings are aligned between both sides
- [ ] Test audience count run in each BU and compared against SF report

### Synchronized Data Sources
- [ ] Required objects are enabled for sync
- [ ] Field count for each synced object is under 250; excluded fields are documented
- [ ] Last sync timestamp is within the past 30 minutes (or a fresh sync was triggered)
- [ ] SDS DEs visible in Marketing Cloud Contact Builder > Data Sources > Synchronized

### Sendable DE Setup
- [ ] No send job targets an SDS DE directly
- [ ] Sendable DEs exist, built from SDS via SQL query or Contact Builder relationship
- [ ] SubscriberKey field mapping confirmed (ContactID or custom key strategy)

### Tracking
- [ ] Campaign and CampaignMember are in SDS sync
- [ ] After test send: Campaign Member email activity fields populated (allow 30 min)
- [ ] For Case tracking: SAP object sync confirmed if using Case sends

### Triggered Sends (if applicable)
- [ ] Triggered Send Definition is Active in Marketing Cloud
- [ ] Flow action mapped correctly: Subscriber Key = Contact ID, Email = Contact Email
- [ ] End-to-end test completed: Flow fires → MC send log record created → email delivered
- [ ] MC-side send failure alerting configured

---

## Configuration Log

Document the final state for future reference:

| Item | Value |
|---|---|
| Connector user username | |
| Connector user profile | |
| MC account ID | |
| Connected Business Units | |
| Scope type | |
| Synced objects | |
| Date last verified | |

---

## Notes

Record any deviations from the standard pattern and why. Include any excluded fields, scope decisions, or known issues accepted as acceptable risk.
