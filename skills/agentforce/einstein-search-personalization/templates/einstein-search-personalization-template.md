# Einstein Search Personalization — Configuration Checklist Template

Use this template when configuring or reviewing Einstein Search personalization for an org.

## Org Eligibility Check

| Check | Status | Notes |
|---|---|---|
| Edition is Enterprise, Performance, or Unlimited | [ ] Pass / [ ] Fail | Required — not available on Professional or lower |
| Lightning Experience is enabled for target users | [ ] Pass / [ ] Fail | Einstein Search is Lightning-only |
| Einstein Search is enabled in Setup | [ ] Pass / [ ] Fail | Setup > Einstein Search > Settings |

## Personalization Signals Configuration

| Signal | Enabled | Rationale |
|---|---|---|
| Activity (recent/frequent views) | [ ] Yes / [ ] No | Recommended for most CRM orgs |
| Location (geographic proximity) | [ ] Yes / [ ] No | Valuable for territory-based sales orgs |
| Ownership (owned records and related) | [ ] Yes / [ ] No | Recommended for account-executive models |
| Specialization (industry/status patterns) | [ ] Yes / [ ] No | Valuable in high-volume orgs with clear segmentation |

**Note:** All four signals should be on for most orgs. Selectively disabling signals is only appropriate when a signal is not meaningful for the user base (e.g., ownership signal in a shared-pool service team).

## Natural Language Search (NLS) Assessment

| Check | Status | Notes |
|---|---|---|
| NLS is required by stakeholders | [ ] Yes / [ ] No | If No, skip NLS configuration |
| All target objects are in NLS-supported list | [ ] Pass / [ ] Fail | Supported: Accounts, Contacts, Opportunities, Cases, Leads ONLY |
| No custom objects in NLS scope | [ ] Confirmed | Custom objects cannot use NLS — use filter panels instead |
| Org language is English | [ ] Confirmed | NLS is English-only; non-English queries fall back to keyword search |
| Object labels have NOT been renamed | [ ] Confirmed / [ ] Renamed | If renamed, document original English names users must type for NLS |

### FLS Audit for NLS Fields

List the fields commonly referenced in expected NLS queries and confirm FLS Read access for target profiles.

| Object | Field | Target Profile | FLS Read Access |
|---|---|---|---|
| Case | Status | Service Agent | [ ] Confirmed |
| Case | Priority | Service Agent | [ ] Confirmed |
| Case | CreatedDate | Service Agent | [ ] Confirmed |
| Account | Name | Sales Rep | [ ] Confirmed |
| Account | BillingCity | Sales Rep | [ ] Confirmed |
| Account | Industry | Sales Rep | [ ] Confirmed |
| Contact | Name | All users | [ ] Confirmed |
| Opportunity | StageName | Sales Rep | [ ] Confirmed |
| Opportunity | CloseDate | Sales Rep | [ ] Confirmed |
| Lead | Status | Marketing | [ ] Confirmed |
| (add rows as needed) | | | |

**Note:** If a field lacks FLS Read access, NLS criteria for that field are silently ignored. No error is shown.

## Promoted Search Terms Configuration

| Keyword | Object | Record | Shared with Target Users | Configured |
|---|---|---|---|---|
| (example: "acme") | Account | Acme Corp | [ ] Confirmed | [ ] Done |
| | | | | |
| | | | | |

**Note:** Promoted results are global (not per-user). They respect sharing rules — users without access to a promoted record will not see it, but no error is shown.

## Searchable Objects Review

| Object | In Global Search Scope | Correct for this Org |
|---|---|---|
| Account | [ ] Yes / [ ] No | [ ] Confirmed |
| Contact | [ ] Yes / [ ] No | [ ] Confirmed |
| Opportunity | [ ] Yes / [ ] No | [ ] Confirmed |
| Case | [ ] Yes / [ ] No | [ ] Confirmed |
| Lead | [ ] Yes / [ ] No | [ ] Confirmed |
| (custom objects to add) | [ ] Yes / [ ] No | [ ] Confirmed |

## User Communication Checklist

Before go-live, confirm the following have been communicated to users and admins:

- [ ] Personalization improves over 1–2 weeks of active use; new users see generic results initially
- [ ] NLS is English-only; non-English queries fall back to keyword search without warning
- [ ] NLS only works for Accounts, Contacts, Opportunities, Cases, and Leads
- [ ] If object labels have been renamed, users must type the original English object name for NLS
- [ ] Promoted results are the same for all users (not personalized per user)
- [ ] FLS gaps silently exclude NLS criteria — any unexpectedly broad NLS results should prompt an FLS review

## Post-Launch Validation

| Check | Target Date | Owner |
|---|---|---|
| Survey users on search relevance 2 weeks after go-live | | |
| Review promoted results for accuracy and relevance | | |
| Re-audit FLS if new fields are added to NLS query patterns | | |
| Confirm new users are getting expected ramp-up experience | | |

## Request Summary

**Requestor:**
**Date:**
**Use case description:**
**Edition confirmed:**
**Lightning Experience confirmed:**
**Key constraints or special requirements:**
