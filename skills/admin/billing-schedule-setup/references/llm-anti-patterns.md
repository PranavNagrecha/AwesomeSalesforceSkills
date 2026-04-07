# LLM Anti-Patterns — Billing Schedule Setup

Common mistakes AI coding assistants make when generating or advising on Billing Schedule Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Native Revenue Schedules with blng__RevenueSchedule__c

**What the LLM generates:** Instructions to "enable Revenue Schedules in Setup > Products > Schedule Settings" and populate the revenue schedule on the OpportunityLineItem, claiming this will integrate with Salesforce Billing invoicing.

**Why it happens:** LLMs trained on broad Salesforce documentation see many references to "revenue schedules" across CPQ, Revenue Cloud, standard Salesforce, and Salesforce Billing. The term appears in all contexts, and the model blurs the object boundaries. Native Salesforce revenue schedules (OpportunityLineItem splits) are far more commonly documented than `blng__RevenueSchedule__c`, so the model defaults to the native object.

**Correct pattern:**
```
Salesforce Billing uses blng__RevenueSchedule__c (managed package object, blng__ namespace)
for revenue recognition timing. This is a completely separate object from:
  - Native OpportunityLineItem revenue schedule splits
  - Standard Schedule Settings in Setup > Products

Do NOT enable "Revenue Schedules" in standard Setup to influence Billing behavior.
Configure blng__RevenueRecognitionRule__c on Product2 and let Billing create
blng__RevenueSchedule__c records at Order activation.
```

**Detection hint:** Any response that says "enable Revenue Schedules in Setup" or references `OpportunityLineItemSchedule` in a Salesforce Billing context is wrong.

---

## Anti-Pattern 2: Treating Billing Schedule Records as Manually Creatable

**What the LLM generates:** A Data Loader import spec or Apex DML block that directly inserts `blng__BillingSchedule__c` records with all required fields populated, framed as a migration or backfill solution for Orders that activated before Billing was configured.

**Why it happens:** The LLM sees `blng__BillingSchedule__c` as a standard custom object and applies general Salesforce knowledge — "any sObject can be inserted via Apex or Data Loader." It does not know that the Invoice Run engine requires records to carry internal managed package flags set only by the Order activation trigger.

**Correct pattern:**
```
blng__BillingSchedule__c records must be created by the Billing package's
Order activation trigger, not by direct DML.

For backfill: reactivate the Order (set to Draft, then re-activate).
For migration: use Salesforce Professional Services tooling or the
Billing package's supported import mechanisms.

Do NOT insert blng__BillingSchedule__c via Apex, Flow, or Data Loader —
Invoice Runs will silently skip these records.
```

**Detection hint:** Any response that includes `insert billingScheduleList;` or a Data Loader mapping for `blng__BillingSchedule__c` as a creation step is likely wrong.

---

## Anti-Pattern 3: Setting Billing Policy on the Order Instead of the Account

**What the LLM generates:** Instructions to set `blng__BillingPolicy__c` on the `Order` record during Order creation or at activation, reasoning that the Order drives the billing process.

**Why it happens:** The `Order` object does have a `blng__BillingPolicy__c` field, and LLMs see this field in object reference documentation and infer it is the authoritative source for the invoice engine. The Account-level lookup is less prominent in generated content because it is a non-obvious indirection.

**Correct pattern:**
```
The Invoice Run engine reads blng__BillingPolicy__c from the Account record,
not from the Order record.

Correct: Set Account.blng__BillingPolicy__c to the desired Billing Policy.
Incorrect: Setting Order.blng__BillingPolicy__c only (ignored by Invoice Run).

The Order field is populated from the Account at Order creation as a reference
copy. Always set the policy on the Account.
```

**Detection hint:** Any setup instruction that says "on the Order record, set Billing Policy" without also setting it on the Account is incomplete or wrong.

---

## Anti-Pattern 4: Assuming Milestone Billing Fires Automatically

**What the LLM generates:** A configuration guide for Milestone billing that says invoice generation is automatic "when the milestone is marked complete" — implying no additional steps are needed beyond updating the milestone status.

**Why it happens:** In-Advance and In-Arrears billing schedules are automatic (Invoice Run picks them up by date). LLMs generalize this to Milestone billing, not knowing that Milestone billing requires a separate, explicitly-triggered Invoice Run scoped to the milestone completion date.

**Correct pattern:**
```
Milestone billing requires TWO explicit actions per milestone:

1. Update the blng__BillingScheduleItem__c record:
   - blng__MilestoneDate__c: set to the actual completion date
   - blng__Status__c: "Complete"

2. Manually create and post a blng__InvoiceRun__c:
   - blng__TargetDate__c: set to the milestone completion date
   - blng__Status__c: Posted

Updating milestone status alone does NOT generate an invoice.
The Invoice Run must be explicitly triggered.
```

**Detection hint:** Any Milestone billing guide that does not mention a manual Invoice Run trigger step is incomplete.

---

## Anti-Pattern 5: Ignoring Data Pipelines as a Prerequisite

**What the LLM generates:** A complete Billing configuration guide (Legal Entity, Billing Policy, Billing Treatment, Billing Rule, Product setup) that does not mention Data Pipelines, assumes billing schedules will generate automatically after Order activation, and does not include any verification step for the dependency.

**Why it happens:** Data Pipelines is a separate Salesforce feature not part of the Billing package itself. LLMs trained on Billing documentation do not see Data Pipelines mentioned in the same context because it is a background infrastructure dependency documented separately. The failure mode (silent non-creation of billing schedules) is also not prominently documented, so LLMs have no training signal to flag it.

**Correct pattern:**
```
Salesforce Billing requires Data Pipelines to be enabled.
This is a hard dependency — without it, blng__BillingSchedule__c records
are not created at Order activation and no error is thrown.

Verification step (must appear in every Billing setup guide):
  Setup > Data Pipelines > Confirm "Enabled" toggle is ON

This must be checked:
  - During initial Billing configuration
  - After every sandbox refresh (does not carry over automatically)
  - During any troubleshooting of missing billing schedules
```

**Detection hint:** Any Billing setup guide that does not include a Data Pipelines verification step is missing a required prerequisite.

---

## Anti-Pattern 6: Recommending Evergreen for Fixed-Term Contracts Without Termination Logic

**What the LLM generates:** Evergreen billing schedule configuration for all subscription products, citing it as the "most flexible" option because it has no end date and automatically rolls forward — without noting that it does not self-terminate when the Order or Contract end date is reached.

**Why it happens:** LLMs see "Evergreen" described as flexible and ongoing in Billing documentation and recommend it broadly for subscription scenarios. The documentation of the self-cancellation limitation is subtle, and LLMs do not flag the operational gap it creates for fixed-term contracts.

**Correct pattern:**
```
Use Evergreen ONLY for genuine month-to-month arrangements with no contractual end date.

For fixed-term subscriptions (e.g., 12-month annual contract), use In-Advance
or In-Arrears with an end date — these respect the Order end date and stop
generating schedule items when the term ends.

If Evergreen is used for fixed-term contracts, build an explicit termination
process: a Flow or Apex that cancels the blng__BillingSchedule__c when the
Order end date is reached. Do not rely on the platform to self-terminate.
```

**Detection hint:** Any recommendation to use Evergreen for an annual or multi-year subscription without a termination process is an anti-pattern.
