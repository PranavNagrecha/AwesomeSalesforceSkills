# Einstein Activity Capture Setup — Work Template

Use this template when configuring or troubleshooting Einstein Activity Capture for a Salesforce org.

## Scope

**Skill:** `einstein-activity-capture-setup`

**Request summary:** (fill in what the user asked for — e.g., initial EAC rollout, adding a new user group, troubleshooting sync failure, adding exclusion domains)

## Context Gathered

Answer these before taking any action:

- **Org edition / license:** (Einstein for Sales add-on / Sales Cloud Einstein / Einstein 1 Sales — confirm PSL seats available)
- **Email platform:** (Microsoft 365 / Google Workspace / Exchange on-premises version)
- **Auth type selected:** (User-Level OAuth / Org-Level OAuth — note: Google Workspace = User-Level only)
- **Target user count:** (how many users will be assigned EAC)
- **Exclusion domains:** (list approved by Legal/Compliance — must be finalized before user assignment)
- **Privacy requirements:** (Private Activities mode needed for any user groups?)
- **Calendar sync direction:** (bi-directional / email-client to Salesforce only)
- **Current org storage:** (Setup > Storage Usage — note current usage and headroom)
- **Salesforce release version:** (Spring '25 / Summer '25 / later — affects storage model and SOQL queryability)

## Configuration Profile Plan

| Profile Name | Auth Type | Email Sync | Calendar Sync | Calendar Direction | Private Activities | Assigned User Groups |
|---|---|---|---|---|---|---|
| (e.g. EAC-SalesTeam) | Org-Level OAuth | Yes | Yes | Bi-directional | No | Sales Reps profile |
| (e.g. EAC-Executives) | User-Level OAuth | Yes | Yes | One-directional | Yes | VP-level users |

## Exclusion Domain Registry

Approved by: (Legal contact name, date approved)

| Domain / Address | Reason for Exclusion | Approved By |
|---|---|---|
| (e.g. competitor.com) | Competitor — do not sync | Legal |
| (e.g. outside-counsel.com) | Legal hold communications | Legal |

## PSL Assignment Checklist

- [ ] Einstein Activity Capture PSL seats confirmed available in Setup > Company Information > Permission Set Licenses
- [ ] PSL assigned to ALL target users (before Configuration profile assignment)
- [ ] Bulk PSL assignment method used: (Manual / Data Loader / other)

## Configuration and Assignment Checklist

- [ ] EAC toggle enabled in Setup > Activity Settings > Einstein Activity Capture
- [ ] Exclusion list reviewed and approved by Legal/Compliance
- [ ] Configuration profile(s) created with correct settings
- [ ] For Org-Level OAuth: Azure AD app consent completed by Microsoft 365 Global Admin
- [ ] EAC PSL assigned to ALL target users
- [ ] Users assigned to correct Configuration profile(s)
- [ ] For User-Level OAuth: users notified and confirmed account connection
- [ ] Sync verified on test Contact/Opportunity records after 4 hours
- [ ] Unresolved Items queue reviewed and actioned
- [ ] Storage consumption baseline recorded

## Sync Verification Results

**Test Contact:** (name, email address used)
**Test email subject:** (subject of email used for verification)
**Appeared on Activity Timeline:** Yes / No
**Appeared on related Opportunity:** Yes / No
**Unresolved Items count at T+4h:** (number)
**Storage before EAC go-live:** (GB)
**Storage at T+1 week:** (GB)

## Notes

Record any deviations from standard pattern and why. Note any unusual findings in Unresolved Items or sync health.

- Deviation:
- Reason:
- Follow-up needed:
