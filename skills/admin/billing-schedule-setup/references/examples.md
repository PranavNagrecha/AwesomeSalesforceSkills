# Examples — Billing Schedule Setup

## Example 1: Configuring Monthly In-Advance Billing for a SaaS Subscription Product

**Context:** A SaaS company sells an annual subscription product through CPQ. The contract requires invoicing on the first day of each month, starting the month after the Order is activated. The Billing package is installed but the implementation team has never configured Billing Rules or Billing Policies.

**Problem:** Orders are activating successfully but no `blng__BillingSchedule__c` records are created. Invoice Runs complete instantly with zero invoices generated. The team suspects the Billing Rules are misconfigured, but the actual root cause is that Data Pipelines was never enabled, silently blocking all billing schedule generation.

**Solution:**

Step 1 — Enable Data Pipelines:
```
Setup > Data Pipelines > Enable
(Requires Salesforce Data Pipelines permission set on the running user)
```

Step 2 — Create the configuration chain (must be in this order):
```
1. New blng__LegalEntity__c:
   Name: "Acme Corp US Entity"
   blng__Country__c: "United States"

2. New blng__TaxPolicy__c:
   Name: "Standard US Tax"
   blng__TaxableYesNo__c: true

3. New blng__BillingPolicy__c:
   Name: "Monthly SaaS Policy"
   blng__LegalEntity__c: [lookup to Acme Corp US Entity]
   blng__TaxPolicy__c: [lookup to Standard US Tax]

4. New blng__BillingTreatment__c:
   Name: "Monthly SaaS Treatment"
   blng__BillingPolicy__c: [lookup to Monthly SaaS Policy]
```

Step 3 — Create and attach a Billing Rule to the Product:
```
New blng__BillingRule__c:
   Name: "Monthly In-Advance Rule"
   blng__BillingType__c: "In Advance"
   blng__BillingDayOfMonth__c: 1
   blng__BillingFrequency__c: "Monthly"

On Product2 record:
   blng__BillingRule__c: [lookup to Monthly In-Advance Rule]
```

Step 4 — Set Billing Policy on the Account:
```
On Account record:
   blng__BillingPolicy__c: [lookup to Monthly SaaS Policy]
```

Step 5 — Activate the Order and verify:
```
Order Status → Activated
Navigate to Related > Billing Schedules
Confirm: one blng__BillingSchedule__c record per OrderProduct
```

Step 6 — Run Invoice Run:
```
New blng__InvoiceRun__c:
   blng__InvoiceDate__c: 2026-05-01
   blng__TargetDate__c: 2026-05-01
   blng__Status__c: Posted
```

**Why it works:** Enabling Data Pipelines unblocks the Order activation trigger that the Billing package hooks into. The configuration chain ensures every invoice has a Legal Entity, Tax Policy, and Treatment. Setting the Billing Policy on the Account (not the Order) is where the invoice engine reads it from.

---

## Example 2: Setting Up Milestone Billing for a Professional Services Engagement

**Context:** A professional services team sells a $120,000 implementation engagement broken into three milestones: 30% at project kickoff ($36,000), 40% at delivery ($48,000), 30% at acceptance ($36,000). Each milestone invoices only after that phase is formally signed off.

**Problem:** The team initially set up the product with an In-Advance billing schedule. The system auto-generates three equal monthly invoices of $40,000, with no relationship to milestone completion. The customer disputes the second invoice because delivery has not occurred yet.

**Solution:**

Step 1 — Reconfigure the Billing Rule:
```
blng__BillingRule__c:
   blng__BillingType__c: "Milestone"
   (Remove period-based fields — milestones use dates, not periods)
```

Step 2 — After Order activation, inspect the auto-generated blng__BillingSchedule__c:
```
The schedule record will have child blng__BillingScheduleItem__c records
corresponding to each milestone. Confirm three items exist with correct amounts.
```

Step 3 — When Milestone 1 (Kickoff) is complete, update the milestone item:
```
blng__BillingScheduleItem__c (Milestone 1):
   blng__MilestoneDate__c: 2026-04-10  (actual completion date)
   blng__Status__c: "Complete"
```

Step 4 — Trigger an Invoice Run scoped to the milestone date:
```
New blng__InvoiceRun__c:
   blng__InvoiceDate__c: 2026-04-10
   blng__TargetDate__c: 2026-04-10
   blng__Status__c: Posted
```

The run creates a blng__Invoice__c for $36,000 only. Milestone 2 and 3 items remain
in "Pending" status and are excluded from this run.

Step 5 — Repeat for each subsequent milestone as they complete.

**Why it works:** Milestone billing requires the admin or an Apex process to explicitly mark milestone items complete and then trigger an Invoice Run. Unlike In-Advance schedules, the engine does not poll for milestone completion — it only processes items that have been explicitly flagged and fall within the target date of the run. This gives the business full control over invoice timing without rebuilding the Order.

---

## Anti-Pattern: Setting Billing Policy on the Order Instead of the Account

**What practitioners do:** During initial Billing configuration, the admin sets `blng__BillingPolicy__c` on the Order record, reasoning that the Order is what drives invoicing. Orders activate successfully. The admin then creates an Invoice Run and it returns zero invoices.

**What goes wrong:** The Salesforce Billing invoice engine reads the Billing Policy from the Account record (`Account.blng__BillingPolicy__c`), not from the Order. The Order record has a `blng__BillingPolicy__c` field, but it is informational — the batch engine ignores it. If the Account has no Billing Policy set, the Invoice Run finds no eligible billing schedules even though the schedules exist.

**Correct approach:** Always set `blng__BillingPolicy__c` on the Account record. The value on the Order is populated from the Account at Order creation as a reference, but the invoice run queries the Account field directly. After correcting the Account lookup, re-run the Invoice Run — no Order reactivation is required.
