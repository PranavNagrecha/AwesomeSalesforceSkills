# MCAE (Pardot) Setup — Work Template

Use this template when working on an MCAE business unit setup or configuration task.

## Scope

**Skill:** `mcae-pardot-setup`

**Request summary:** (fill in what the user or project asked for)

**In scope for this engagement:**
- [ ] Net-new BU setup (connector activation, connector user, tracking domain)
- [ ] Salesforce User Sync enablement
- [ ] Field sync rule configuration
- [ ] Campaign connector setup
- [ ] Multi-BU configuration
- [ ] Troubleshooting existing sync issues
- [ ] Other: ___________

**Explicitly out of scope:** Marketing Cloud Engagement (Journey Builder, Email Studio). If the requester mentions these, redirect to the Marketing Cloud Engagement skill.

---

## Context Gathered

Answer these before proceeding:

**Org and BU state:**
- MCAE BU ID: ___________
- Connector current status (Active / Paused / Error): ___________
- Salesforce org edition: ___________
- Account Engagement Lightning App installed? (Yes / No / Unknown): ___________

**Connector user:**
- Designated connector user (email / username): ___________
- Service account or named person? (Service account is required): ___________
- Profile assigned: ___________
- Marketing User checkbox confirmed? (Yes / No): ___________
- View All Data confirmed? (Yes / No): ___________
- Modify All Data confirmed? (Yes / No): ___________
- API Enabled confirmed? (Yes / No): ___________

**User Sync state:**
- User Sync currently enabled? (Yes / No): ___________
- If not yet enabled: number of existing MCAE users to pre-validate: ___________
- Profile-to-role mapping decided? (Yes / No / In progress): ___________

**Field sync:**
- Objects intended for sync: Lead / Contact / Account / Opportunity / Campaign (circle all that apply)
- Any custom fields mapped? List: ___________
- FLS audit on connector user completed? (Yes / No): ___________

**Tracking domain:**
- Tracking subdomain to use: ___________
- DNS CNAME record created? (Yes / No): ___________
- Domain showing Active in MCAE? (Yes / No): ___________

**Campaign connector:**
- Number of MCAE campaigns needing Salesforce campaign links: ___________
- Campaign Member Status values to map: Sent / Opened / Clicked / Responded / Unsubscribed (add others): ___________

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Net-New Business Unit Setup (first-time configuration from scratch)
- [ ] Multi-Business-Unit Org (multiple BUs, each with their own connector)
- [ ] Troubleshooting Existing BU (connector/sync issues on a live BU)

Describe any deviations from the standard pattern and the reason:

___________

---

## Setup Sequence Checklist

Work through these in order. Do not proceed to the next step if a previous step is not confirmed.

### Phase 1 — Foundation

- [ ] Account Engagement Lightning App installed and visible in Lightning nav for admin users
- [ ] Connector service account created (dedicated email, not a named person)
- [ ] Connector user holds: Marketing User checkbox, View All Data, Modify All Data, API Enabled
- [ ] Connector user FLS audited against all fields intended for sync
- [ ] Salesforce v2 connector verified (auth handshake passed)
- [ ] Salesforce v2 connector status: **Active** (not Paused, not Error)

### Phase 2 — Tracking and Field Sync

- [ ] Tracking domain CNAME created in DNS
- [ ] Tracking domain shows Active in MCAE Domain Management
- [ ] Field sync rules reviewed and explicitly set for all mapped fields
  - CRM-authoritative fields set to "Use Salesforce's Value"
  - MCAE-authoritative fields set to "Use Pardot's Value"
  - Shared fields set to "Use Most Recently Updated"
- [ ] Recycle Bin Sync setting decision documented: Enabled / Disabled (reason: _________)

### Phase 3 — User Sync

- [ ] All existing MCAE users verified to have matching Salesforce user records
- [ ] Profile-to-role mapping finalized and documented
- [ ] User Sync enabled
- [ ] Test: new Salesforce user on mapped profile appears in MCAE within 5 minutes
- [ ] Test: deactivated Salesforce user is deactivated in MCAE automatically

### Phase 4 — Campaign Connector and End-to-End Validation

- [ ] At least one MCAE campaign linked to a Salesforce campaign
- [ ] Campaign Member Status values configured: Sent, Opened, Clicked, Responded, Unsubscribed
- [ ] End-to-end test performed:
  - [ ] Test form submission creates MCAE prospect
  - [ ] Prospect syncs to Salesforce Lead or Contact within 5 minutes
  - [ ] Campaign Member record created in Salesforce campaign

---

## Field Sync Rule Matrix

| Salesforce Field | MCAE Field | Object | Sync Rule | Owning System | Notes |
|---|---|---|---|---|---|
| Email | Email | Lead/Contact | Use Salesforce's Value | Salesforce | Key sync field — do not allow MCAE override |
| FirstName | First Name | Lead/Contact | Use Most Recently Updated | Both | |
| LastName | Last Name | Lead/Contact | Use Most Recently Updated | Both | |
| Company / Account Name | Company | Lead/Contact | Use Most Recently Updated | Both | |
| Title | Job Title | Lead/Contact | Use Most Recently Updated | Both | |
| HasOptedOutOfEmail | Do Not Email | Lead/Contact | Use Pardot's Value | MCAE | Opt-out must never be overwritten by CRM |
| Score (AE Score) | Score | Lead/Contact | Use Pardot's Value | MCAE | Do not write to this from CRM side |
| OwnerId | Assigned User | Lead/Contact | Use Salesforce's Value | Salesforce | CRM owns assignment |
| (custom) | (custom) | | | | |

---

## Profile-to-Role Mapping

| Salesforce Profile | MCAE Role | Access Level | Notes |
|---|---|---|---|
| (e.g., Marketing Admin) | Administrator | Full MCAE admin access | |
| (e.g., Marketing User) | Marketing | Can create/send campaigns | |
| (e.g., Sales User) | Sales | Read-only prospect access | |

---

## Notes

Record any deviations from the standard pattern, open questions, or follow-up items:

___________

**Configuration decisions requiring stakeholder sign-off:**
- Recycle Bin Sync: Enabled / Disabled — Sign-off from: ___________
- User Sync enabled on: __________ — Sign-off from: ___________
- Connector service account owner: ___________
