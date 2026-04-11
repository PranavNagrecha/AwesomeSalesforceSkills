# Compliant Data Sharing Setup — Work Template

Use this template when working on a CDS setup task in an FSC org.

---

## Scope

**Skill:** `compliant-data-sharing-setup`

**Request summary:** (fill in what the user asked for — e.g., "Enable CDS for Account and Opportunity to isolate retail banking from wealth management")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- FSC installed and API version confirmed: [ ] Yes / [ ] No — version: ___
- CDS target objects: (list the objects requiring ethical-wall enforcement)
  - [ ] Account
  - [ ] Opportunity
  - [ ] Interaction
  - [ ] Interaction Summary
  - [ ] Financial Deal (requires Deal Management enabled)
- Current OWD for each target object:
  - Account: ___ (must be Private or Public Read-Only)
  - Opportunity: ___ (must be Private or Public Read-Only)
  - Financial Deal: ___ (must be Private or Public Read-Only)
- Deal Management enabled: [ ] Yes / [ ] No / [ ] Not applicable
- CDS Manager permission assigned to admin(s): [ ] Yes / [ ] No
- CDS User permission assigned to business users: [ ] Yes / [ ] No
- Existing sharing rules on target objects that need audit: (list any)

---

## Prerequisites Checklist

Complete all before enabling CDS:

- [ ] OWD changed to Private or Public Read-Only for all target objects
- [ ] Sharing recalculation completed after OWD change
- [ ] Deal Management enabled (if Financial Deal is in scope)
- [ ] CDS Manager permission set assigned
- [ ] CDS User permission set assigned to all participant-eligible users

---

## CDS Enablement Steps

### 1. IndustriesSettings Configuration

Objects to enable (check all that apply):

- [ ] `enableCompliantDataSharingForAccount = true`
- [ ] `enableCompliantDataSharingForOpportunity = true`
- [ ] `enableCompliantDataSharingForInteraction = true`
- [ ] `enableCompliantDataSharingForInteractionSummary = true`
- [ ] `enableCompliantDataSharingForFinancialDeal = true`

Deployment method: [ ] Setup UI / [ ] Metadata deploy

### 2. Page Layout Updates

- [ ] Financial Deal Participants related list added to Account layout (if applicable)
- [ ] Financial Deal Participants related list added to Financial Deal layout (if applicable)

### 3. Participant Role Records

Define the Participant Roles needed for this org:

| Role Name | Access Level | Business Line / Use Case |
|---|---|---|
| (e.g., Relationship Manager) | (Edit) | (Retail Banking) |
| (e.g., Wealth Advisor) | (Edit) | (Wealth Management) |
| (e.g., Co-Advisor) | (Read) | (Wealth Management) |
| (e.g., Compliance Reviewer) | (Read) | (Cross-line compliance) |

---

## Sharing Rule Audit

List any sharing rules on target objects and their disposition:

| Sharing Rule Name | Object | Disposition (Keep / Remove) | Reason |
|---|---|---|---|
| | | | |

---

## Validation Steps

- [ ] Enabled CDS object shows "Compliant Data Sharing" in Setup > Sharing Settings
- [ ] Manager user confirmed to NOT see subordinate-owned records
- [ ] Participant Role assignment on a test record grants access to the assigned user
- [ ] User without CDS User permission cannot be added as a participant
- [ ] Financial Deal Participants related list visible on layout (if applicable)
- [ ] Cross-line access test: user from Line A cannot see Line B records (no participant assignment)

---

## Disabling CDS (if needed in future)

- [ ] All `AccountParticipant` / `OpportunityParticipant` / `FinancialDealParticipant` records deleted
- [ ] Participant record count confirmed at zero
- [ ] Salesforce Support ticket submitted for flag deactivation

---

## Notes

Record any deviations from the standard pattern and why:

(e.g., "Financial Deal CDS deferred to Phase 2 — Deal Management enablement requires separate change request")
