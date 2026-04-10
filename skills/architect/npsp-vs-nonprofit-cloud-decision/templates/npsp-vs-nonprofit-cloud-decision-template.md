# NPSP vs. Nonprofit Cloud Decision — Work Template

Use this template when guiding an organization through the NPSP vs. Nonprofit Cloud platform decision.

---

## Scope

**Skill:** `npsp-vs-nonprofit-cloud-decision`

**Organization name:** ___________________________

**Request summary:** (describe what the organization asked or what triggered this assessment)

---

## Context Gathered

### Current Platform State

- **Current product:** [ ] NPSP (managed package)  [ ] Nonprofit Cloud  [ ] Unknown — verify first
- **NPSP version / installed package version:** ___________________________
- **Add-on packages installed:** [ ] PMM  [ ] Elevate  [ ] Volunteers for Salesforce  [ ] Other: ___
- **Org age (approximate):** ___________________________

### Constituent and Data Profile

- **Approximate Contact/Account record count:** ___________________________
- **Approximate Opportunity/Donation record count:** ___________________________
- **Recurring Donation records:** [ ] Yes — count: ___  [ ] No
- **Program data volume (PMM):** ___________________________

### Customization Complexity

- **Custom Apex classes / triggers:** [ ] Yes  [ ] No  — count: ___
- **Active Flows / Process Builders:** count: ___
- **CRLP rollup definitions:** count: ___
- **Custom objects:** count: ___
- **External integrations:** ___________________________
- **Complexity score:** [ ] Low  [ ] Medium  [ ] High

### Feature Requirements

| Required Feature | Available in NPSP? | Available in NPC? |
|---|---|---|
| _____________________________ | [ ] Yes  [ ] No | [ ] Yes  [ ] No |
| _____________________________ | [ ] Yes  [ ] No | [ ] Yes  [ ] No |
| Gift Entry Manager | NO | YES |
| Salesforce Grantmaking | NO | YES |
| Native Program Management | Partial (PMM add-on) | YES |
| Agentforce / Einstein native | NO | YES |

---

## Decision Recommendation

**Recommended path:** [ ] Stay on NPSP  [ ] Migrate to Nonprofit Cloud  [ ] Conduct readiness assessment first

**Primary driver for this recommendation:**

___________________________

**Top 3 risks of the recommended path:**

1. ___________________________
2. ___________________________
3. ___________________________

**Key assumption that must hold for this recommendation to be valid:**

___________________________

---

## Explicit Architecture Notes (Required)

> IMPORTANT: Include all applicable statements below verbatim in any written deliverable.

- [ ] Confirmed: There is NO in-place upgrade path from NPSP to Nonprofit Cloud. Migration requires a net-new org.
- [ ] Confirmed: NPSP and NPC use different Account models (Household Accounts vs. Person Accounts). These are incompatible at the org level.
- [ ] Confirmed: NPSP is feature-frozen as of March 2023. No new features will be added. No hard EOL date has been announced as of April 2026.
- [ ] Confirmed: CRLP rollup definitions must be rebuilt from scratch in NPC — they do not transfer.
- [ ] If PMM is installed: Confirmed that a PMM-to-NPC Program Management feature parity assessment is required before committing to migration.

---

## Next Steps for Recommended Path

### If STAY on NPSP:

- [ ] Document the following re-evaluation triggers:
  - Salesforce announces a formal NPSP EOL date
  - A required new feature is confirmed NPC-exclusive
  - A critical integration breaks due to NPSP platform changes
  - A planned org consolidation creates a migration window
- [ ] Confirm data export / backup procedures are current
- [ ] Schedule annual NPSP support status review: date ___________________________

### If MIGRATE to Nonprofit Cloud:

- [ ] Identify and engage a Nonprofit Cloud certified implementation partner
- [ ] Initiate migration readiness assessment covering:
  - Customization inventory
  - CRLP rollup inventory
  - PMM feature parity assessment (if applicable)
  - Integration re-architecture plan
  - Data transformation design (Household → Person Account)
- [ ] Agree on high-level migration timeline: ___________________________
- [ ] Confirm executive sponsorship and change management resourcing

### If READINESS ASSESSMENT first:

- [ ] Define scope of assessment: ___________________________
- [ ] Timeline for assessment completion: ___________________________
- [ ] Decision-maker for go/stay after assessment: ___________________________

---

## Notes

Record any deviations from the standard framework or client-specific factors that affect the recommendation.

___________________________
