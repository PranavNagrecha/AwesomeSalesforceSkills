# Billing Schedule Setup — Work Template

Use this template when configuring or troubleshooting Salesforce Billing (blng__ namespace) billing schedules, billing policies, or invoice runs.

## Scope

**Skill:** `billing-schedule-setup`

**Request summary:** (fill in what the user asked for — e.g., "configure monthly in-advance billing for annual subscriptions" or "debug why billing schedules are not generating after Order activation")

---

## Prerequisites Confirmed

Before proceeding, confirm all of the following:

- [ ] Salesforce Billing managed package (blng__ namespace) is installed in this org
- [ ] Data Pipelines is enabled: Setup > Data Pipelines > Enabled toggle is ON
- [ ] Orders are CPQ-sourced (created from a CPQ Quote, not manually created)
- [ ] Account records that will be invoiced have `blng__BillingPolicy__c` set (not just the Order)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- **Schedule type required:** <!-- In-Advance / In-Arrears / Evergreen / Milestone / Dynamic Invoice Plan -->
- **Billing period:** <!-- Monthly / Quarterly / Annually / Custom -->
- **Billing day of month:** <!-- e.g., 1st of the month -->
- **Legal Entity name:** <!-- e.g., "Acme Corp US Entity" -->
- **Tax Policy name:** <!-- e.g., "Standard US Tax" -->
- **Known constraints:** <!-- e.g., multi-entity, milestone sign-offs required, usage data import needed -->
- **Failure mode observed (if troubleshooting):** <!-- e.g., "BillingSchedule__c records not created after Order activation" -->

---

## Configuration Chain Status

Track each required record in the dependency order:

| Record Type | Record Name | Status |
|---|---|---|
| `blng__LegalEntity__c` | <!-- name --> | Not Started / Created / Verified |
| `blng__TaxPolicy__c` | <!-- name --> | Not Started / Created / Verified |
| `blng__BillingPolicy__c` | <!-- name --> | Not Started / Created / Verified |
| `blng__BillingTreatment__c` | <!-- name --> | Not Started / Created / Verified |
| `blng__BillingRule__c` | <!-- name --> | Not Started / Created / Verified |
| Product2 Billing Rule Lookup | <!-- product name --> | Not Assigned / Assigned / Verified |
| Account Billing Policy Lookup | <!-- account name --> | Not Set / Set / Verified |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Standard In-Advance subscription billing (monthly or other period)
- [ ] In-Arrears billing (usage-based, charge after period)
- [ ] Evergreen billing (month-to-month, no end date)
- [ ] Milestone billing (manual Invoice Run trigger per milestone)
- [ ] Dynamic Invoice Plan (custom date/amount schedule)

**Reason for choice:** (explain why this pattern was selected)

---

## Invoice Run Configuration

| Field | Value |
|---|---|
| `blng__InvoiceDate__c` | <!-- e.g., 2026-05-01 --> |
| `blng__TargetDate__c` | <!-- must be >= invoice date; set to TODAY() to include same-day items --> |
| `blng__Status__c` | Draft (before submission) → Posted (to execute) |
| Scope | <!-- All accounts / specific account set --> |

For Milestone billing — list each milestone and its Invoice Run:

| Milestone | Completion Date | Invoice Amount | Invoice Run Status |
|---|---|---|---|
| <!-- Milestone 1 name --> | <!-- date --> | <!-- $amount --> | Not Run / Submitted / Posted |
| <!-- Milestone 2 name --> | <!-- date --> | <!-- $amount --> | Not Run / Submitted / Posted |

---

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them:

- [ ] Data Pipelines is enabled in Setup (hard dependency confirmed)
- [ ] Legal Entity, Billing Policy, Billing Treatment, and Tax Policy are all created and linked in the correct order
- [ ] Every Product2 in scope has a `blng__BillingRule__c` lookup populated with the correct schedule type
- [ ] The Account record has `blng__BillingPolicy__c` set to the correct Billing Policy
- [ ] `blng__BillingSchedule__c` records were auto-generated upon Order activation (no manual records)
- [ ] Invoice Run `blng__TargetDate__c` is set to capture all intended billing schedule items
- [ ] Invoice Run batch completed without errors (check Setup > Apex Jobs)
- [ ] `blng__Invoice__c` records show correct amounts, line counts, and invoice dates
- [ ] Milestone billing (if applicable): only completed milestones have been invoiced; future milestones are pending

---

## Notes

Record any deviations from the standard pattern and why:

<!-- Example: "Billing Policy was set at the Order level by previous admin — corrected to Account level. Required re-running Invoice Run." -->
