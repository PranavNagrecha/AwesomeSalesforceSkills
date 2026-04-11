# Health Cloud Multi-Cloud Architecture Decision Template

Use this template to document multi-cloud scope, license model decisions, and topology rationale for a Health Cloud implementation. Complete every section before finalizing the architecture with the customer.

---

## Project Context

**Customer name:** (fill in)

**Salesforce edition contracted:** (Enterprise / Unlimited)

**Health Cloud license count (internal users):** (fill in)

**Implementation phase:** (Discovery / Design / Build / UAT / Go-Live)

**Primary architect:** (fill in)

**Date:** (YYYY-MM-DD)

---

## 1. Persona Inventory

List every user type that will interact with the Salesforce platform and classify each as internal or external.

| Persona | Internal or External | Primary Cloud Touchpoints | Estimated User Count |
|---|---|---|---|
| Care Coordinator | Internal | Health Cloud, Service Cloud (Cases), OmniStudio | |
| Nurse / Clinician | Internal | Health Cloud, OmniStudio | |
| Care Program Manager | Internal | Health Cloud, Marketing Cloud Connect | |
| System Administrator | Internal | Health Cloud, all clouds | |
| Patient (portal user) | External | Experience Cloud for Health Cloud | |
| Caregiver / Family Member | External | Experience Cloud for Health Cloud | |
| (add rows as needed) | | | |

---

## 2. Cloud Scope Decision

For each Salesforce cloud, confirm whether it is in scope, whether it is bundled in the Health Cloud license, and whether a separate purchase is required.

| Salesforce Cloud / Product | In Scope? | Bundled in Health Cloud License? | Separate Purchase Required? | Notes |
|---|---|---|---|---|
| Service Cloud (Cases, Omni-Channel, Entitlements) | Yes / No | YES — implicit in HC license | No | Internal care team only |
| OmniStudio (OmniScripts, DataRaptors, FlexCards) | Yes / No | YES — bundled in HC license | No | Requires 3 PSLs per user |
| Experience Cloud for Health Cloud | Yes / No | NO — separate add-on SKU | Yes | Patient/caregiver portals |
| Marketing Cloud + Health Cloud Connect | Yes / No | NO — separate product | Yes | Requires dedicated HIPAA BAA |
| CRM Analytics for Health Cloud | Yes / No | NO — separate add-on | Yes | Basic reports included in HC |
| MuleSoft (EHR integration) | Yes / No | NO — separate product | Yes | Named credential callouts are free |
| Salesforce Shield (encryption, event monitoring) | Yes / No | NO — separate add-on | Yes | Evaluate for PHI field encryption |

---

## 3. Permission Set License (PSL) Assignment Matrix

Complete this matrix for every internal persona and external user type. Confirm PSL quantities against the signed order form.

### Internal Users

| Persona | Health Cloud PSL | Health Cloud Platform PSL | OmniStudio User PSL | Notes |
|---|---|---|---|---|
| Care Coordinator | Required | Required (if using OmniStudio) | Required (if using OmniStudio) | |
| Nurse / Clinician | Required | Required (if using OmniStudio) | Required (if using OmniStudio) | |
| Care Program Manager | Required | Confirm | Confirm | |
| System Administrator | Required | Required | Required | |

### External / Portal Users

| Persona | Health Cloud for Experience Cloud PSL | Notes |
|---|---|---|
| Patient (portal user) | Required | Must be assigned before UAT with external test users |
| Caregiver / Family Member | Required | Same PSL as patient portal users |

**PSL quantity validation:**

- Health Cloud PSL purchased: ______
- Health Cloud Platform PSL purchased: ______
- OmniStudio User PSL purchased: ______
- Health Cloud for Experience Cloud PSL purchased: ______

Confirm quantities match the counts in the Persona Inventory above.

---

## 4. HIPAA BAA Scope Confirmation

For every cloud that will touch Protected Health Information (PHI), confirm BAA coverage.

| Salesforce Cloud | Will Touch PHI? | BAA in Place? | BAA Reference / Date | Action Required |
|---|---|---|---|---|
| Health Cloud (CRM platform) | Yes | Confirm | | |
| Experience Cloud for Health Cloud | Yes (patient record access) | Covered under HC BAA | | |
| Marketing Cloud | Confirm | Confirm separately | | Execute MC HIPAA BAA before PHI sync |
| MuleSoft (if used for EHR integration) | Confirm | Confirm separately | | |

**Key rule:** PHI must NOT flow from Health Cloud to Marketing Cloud until a Marketing Cloud HIPAA BAA is executed and on file. Until then, restrict the Marketing Cloud Health Cloud Connect sync to non-PHI fields only.

---

## 5. Org Topology Decision

**Recommended topology:** (Single-org / Hub-and-spoke)

### Single-Org (default recommendation)

- All internal care team users and Experience Cloud portal users share one Salesforce org
- Data isolation between internal and external users is achieved via OWD, Sharing Sets, and PSL-gated permission sets
- Marketing Cloud is connected via Marketing Cloud Health Cloud Connect
- Choose this unless a documented regulatory requirement mandates separation

**Rationale for single-org choice:** (fill in)

### Hub-and-Spoke (only if regulatory separation is required)

- Each business unit or subsidiary with distinct data residency requirements gets a separate Salesforce org (spoke)
- A central integration layer (MuleSoft, Platform Events) aggregates cross-entity patient records
- Used when: behavioral health data under 42 CFR Part 2 must be segregated, or international data residency requirements mandate separate orgs

**Regulatory driver for multi-org:** (fill in or mark N/A)

---

## 6. Experience Cloud Site Configuration Checklist

Complete this section if an Experience Cloud patient or caregiver portal is in scope.

- [ ] Experience Cloud for Health Cloud add-on SKU confirmed on order form
- [ ] PersonAccount enabled in the org (confirm with Salesforce Setup > Account Settings)
- [ ] Patient identity model uses PersonAccount (not standard Contact)
- [ ] Experience Cloud site created using Health Cloud portal template
- [ ] Sharing Sets configured for CareProgramEnrollee and CarePlan (patient access to own records)
- [ ] Health Cloud for Experience Cloud PSL assigned to all portal user profiles
- [ ] OWD for Health Cloud objects confirmed as Private (or Controlled by Parent)
- [ ] Guest User access restricted to minimum necessary data (no PHI accessible without login)
- [ ] External test users (not "View Site as" admin preview) used to validate portal access in UAT

---

## 7. Marketing Cloud Integration Decision

Complete this section if Marketing Cloud is in scope.

**Use case for Marketing Cloud:** (appointment reminders / care program campaigns / re-engagement journeys / other)

**PHI fields that will flow to Marketing Cloud:**
- (list each field: e.g., patient name, appointment date, care program enrollment status)

**Marketing Cloud HIPAA BAA status:** (Not executed / In progress / Executed — date: ________)

**Interim restriction (until BAA is executed):**
Marketing Cloud Health Cloud Connect will sync ONLY the following non-PHI fields until the BAA is in place:
- (list approved non-PHI fields only)

**Marketing Cloud Synchronization Dashboard monitoring:** (Configured / Not yet configured)

---

## 8. OmniStudio Deployment Decision

Complete this section if OmniStudio OmniScripts or FlexCards are in scope.

**OmniStudio use cases in scope:**
- [ ] Patient intake assessment (SDOH screening, medication reconciliation)
- [ ] Guided care plan creation
- [ ] EHR data retrieval Integration Procedures
- [ ] Patient portal OmniScripts (served through Experience Cloud site)
- [ ] Other: (fill in)

**PSL assignment confirmed for all OmniStudio users:** (Yes / No — see PSL matrix above)

**Three-PSL validation query (run against each care coordinator user):**

```bash
sf data query \
  --query "SELECT PermissionSetLicense.DeveloperName, Assignee.Name \
           FROM PermissionSetLicenseAssign \
           WHERE PermissionSetLicense.DeveloperName IN \
           ('HealthCloudPsl','HealthCloudPlatformPsl','OmniStudioUser')" \
  --use-tooling-api
```

Confirm all three PSLs appear for every OmniStudio user before UAT.

---

## 9. Architecture Decision Record (ADR) Summary

**Decision:** (One-sentence summary of the multi-cloud topology and key licensing decisions)

**Context:** (What constraints, requirements, and regulatory obligations drove the decisions)

**Options considered:**
1. Single-org with Experience Cloud for Health Cloud — (outcome: chosen / not chosen, reason)
2. Hub-and-spoke multi-org — (outcome: chosen / not chosen, reason)
3. Marketing Cloud vs. internal notifications — (outcome: chosen / not chosen, reason)

**Consequences:**
- (List the positive and negative consequences of the chosen topology)
- (Note any risks that must be monitored post-go-live)

**Approved by:** (architect / lead / customer sign-off)

**Date approved:** (YYYY-MM-DD)

---

## 10. Open Questions and Risks

| # | Question or Risk | Owner | Due Date | Status |
|---|---|---|---|---|
| 1 | Marketing Cloud HIPAA BAA execution timeline | | | Open |
| 2 | PersonAccount migration plan for brownfield Contact records | | | Open |
| 3 | Experience Cloud for Health Cloud PSL quantity on order form | | | Open |
| 4 | (add rows as needed) | | | |
