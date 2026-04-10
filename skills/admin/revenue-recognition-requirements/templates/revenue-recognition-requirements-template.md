# Revenue Recognition Requirements — Work Template

Use this template when configuring or troubleshooting Salesforce Billing revenue recognition
for a specific product, order, or amendment scenario.

---

## Scope

**Skill:** `revenue-recognition-requirements`

**Request summary:** (fill in what the practitioner or stakeholder asked for)

**Org:** (sandbox / production name)

**Date:**

---

## Context Gathered

Answer each question before proceeding with any configuration or investigation.

- **Salesforce Billing installed?** (confirm blng__ namespace is present): Yes / No
- **Finance Periods exist for all service dates in scope?**
  - Query: `SELECT Id, Name, blng__StartDate__c, blng__EndDate__c, blng__Status__c FROM blng__FinancePeriod__c WHERE blng__Status__c = 'Active' ORDER BY blng__StartDate__c`
  - Earliest Finance Period found:
  - Latest Finance Period found:
  - Gaps identified:
- **Products in scope and their current blng__RevenueRecognitionRule__c:**

  | Product Name | Product2 Id | Revenue Recognition Rule | Treatment | Distribution Method |
  |---|---|---|---|---|
  | (fill in) | | | | |

- **Order / Amendment details:**
  - Order Id:
  - Order Start Date:
  - Order End Date:
  - Amendment or new order?

- **Known constraints or Finance reporting requirements:**

---

## Diagnosis (For Troubleshooting Tasks)

If blng__RevenueSchedule__c records are missing after Order activation, work through this checklist:

- [ ] Finance Periods exist and are Active for all dates in the Order's service range
- [ ] Product2 has blng__RevenueRecognitionRule__c populated (not null)
- [ ] The Order was CPQ-sourced (not manually created — manually created Orders may bypass Billing triggers)
- [ ] The blng__ namespace is installed and Data Pipelines is enabled
- [ ] No process or trigger is suppressing the Billing managed package automation

**Root cause identified:**

**Resolution plan:**

---

## Configuration Plan (For New Setup Tasks)

### Revenue Recognition Rule Configuration

For each product requiring revenue recognition:

| Product | Treatment | Distribution Method | Reason |
|---|---|---|---|
| (fill in) | Rateable / Immediate / Event-Based | Daily Proration / Equal Distribution / Single Period | |

**Finance Period coverage required:**
- From: (earliest Order start date in scope)
- To: (latest Order end date in scope)
- Finance Periods to create (if any):

**Bundle / Performance Obligation notes:**
- Are any products bundles with distinct ASC 606 performance obligations? Yes / No
- If yes, which components need separate Revenue Recognition Rules?
- blng__StandaloneSellingPrice__c set on each component? Yes / No / N/A

---

## Amendment Reconciliation Notes

Complete this section for any contract amendment scenario.

- **Original Order Id:**
- **Amendment Order Id:**
- **Original blng__RevenueSchedule__c Id and total amount:**
- **New blng__RevenueSchedule__c Id (delta) and total amount:**
- **ERP integration approach:** Sums both schedules independently / Requires single consolidated schedule
- **Manual reconciliation required?** Yes / No
  - If yes, describe the reconciliation step:

---

## GL Integration Verification

- **blng__RevenueTransaction__c records generated?** Yes / No / Not yet (Finance Period not closed)
- **GL account codes on transaction records match ERP mapping?** Yes / No / Not verified
- **Recognized amount on blng__RevenueSchedule__c matches sum of blng__RevenueTransaction__c records?** Yes / No

---

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them:

- [ ] Finance Periods exist and are Active for all service date periods covered by the Order
- [ ] Every in-scope Product2 has blng__RevenueRecognitionRule__c lookup populated
- [ ] Recognition treatment matches the ASC 606 performance obligation type for each product
- [ ] Distribution method handles partial-month proration correctly (Daily Proration for variable start dates)
- [ ] For bundles: blng__StandaloneSellingPrice__c is set on each distinct performance obligation component
- [ ] blng__RevenueSchedule__c records were auto-generated at Order activation (not manually created)
- [ ] Revenue schedule line amounts sum to the correct total contract value
- [ ] blng__RevenueTransaction__c GL events carry correct GL account codes for ERP integration
- [ ] For amendments: original revenue schedule reviewed; manual reconciliation performed if contract value changed

---

## Notes and Deviations

(Record any deviations from the standard configuration pattern and the reason accepted by Finance.)
