# Gotchas — Revenue Cloud Architecture

Real-world issues that bite RLM (and adjacent CPQ classic /
Salesforce Billing) implementations.

---

## Gotcha 1: Synchronous callouts from triggers are blocked

**What happens.** `Http.send()` from inside a trigger throws a
runtime exception. The platform does not allow synchronous outbound
callouts from a trigger context.

**When it occurs.** Engineers porting "fire on insert -> push to
ERP" patterns naively into a trigger.

**How to avoid.** Use `@future(callout=true)`, Queueable with
`Database.AllowsCallouts`, or — preferred — emit a Platform Event /
let CDC carry the change and have an off-platform consumer call the
ERP.

---

## Gotcha 2: `LegalEntity` proliferation kills reporting

**What happens.** Without governance, `LegalEntity` rows multiply
beyond the legal / accounting boundaries that justify them.
Reporting, tax-jurisdiction routing, and accounting-period
maintenance scale linearly with the count.

**When it occurs.** Regional finance teams ask for "their own"
entity for operational convenience.

**How to avoid.** Architect rule: a `LegalEntity` exists only for a
legal-or-tax separation reason. Operational separation goes through
`Account.Region__c` or similar without expanding LegalEntity count.

---

## Gotcha 3: RLM and `blng__` Salesforce Billing have different objects

**What happens.** Code references `Invoice` (native RLM); production
runs `blng__` package; deployment fails. Or vice versa.

**When it occurs.** Designs that don't pin down namespace at the
start.

**How to avoid.** Confirm namespace via Setup -> Installed Packages
before designing data model extensions or Apex.

---

## Gotcha 4: Order activation timing affects asset creation

**What happens.** Test data setup creates an Order without
activating it; expects assets to appear. They don't — assets are
created on Order activation in RLM, not on insert.

**When it occurs.** Apex tests or integration tests that skip the
activation step.

**How to avoid.** Activate the Order in test setup (`OrderStatus =
'Activated'` plus the platform's activation pathway) or mock the
asset creation.

---

## Gotcha 5: `BillingSchedule` vs `Invoice` semantics

**What happens.** Engineer assumes `BillingSchedule` *is* the
invoice. It's not — `BillingSchedule` is the rule that drives invoice
generation. `Invoice` rows are produced by running the schedule.

**When it occurs.** Reading docs quickly without the data-model
walkthrough.

**How to avoid.** Read the official RLM Billing data-model overview;
draw the relationship diagram before any code.

---

## Gotcha 6: AccountingPeriod close blocks new posts

**What happens.** Finance closes an `AccountingPeriod`. Subsequent
attempts to post invoices into the closed period fail with a
period-closed error. Integration retries hammer the system.

**When it occurs.** Month-end close while integrations are still
sending late-arrival invoices.

**How to avoid.** Coordinate close timing with integration cadence.
Implement consumer-side dead-letter handling for closed-period
errors so the integration doesn't retry indefinitely.

---

## Gotcha 7: Assets persist independently of Contract

**What happens.** Contract is amended or canceled. Existing assets
do not auto-disappear; their `AssetStatePeriod` history records the
state changes but the rows remain.

**When it occurs.** Engineers trying to "delete the contract to
clean up" mid-implementation.

**How to avoid.** Treat Asset as a long-lived entity with a
historical state, not a child of Contract. Cancellation captures a
final state period, not a delete.

---

## Gotcha 8: Pricebook and PricebookEntry are still standard objects

**What happens.** Engineer assumes RLM Pricing replaces
Pricebook2 / PricebookEntry. RLM Pricing extends them — the
underlying objects remain. Integration that bypasses
PricebookEntry breaks RLM pricing rules.

**When it occurs.** "Greenfield RLM" assumption that the data model
is wholly new.

**How to avoid.** Read the official "Plan Your Revenue Cloud
Implementation" guide. Many objects are familiar standard objects
extended with RLM behavior.

---

## Gotcha 9: Cross-entity invoicing requires explicit LegalEntity routing

**What happens.** Order on a US Account is invoiced through the EU
LegalEntity by accident. Tax treatment and accounting end up wrong;
correction is a manual finance task.

**When it occurs.** Lookup defaulting / Apex automation that infers
LegalEntity from running-user context rather than Account
attributes.

**How to avoid.** Make LegalEntity assignment explicit and visible
on the Order / Quote. Validation rule blocks save when LegalEntity
disagrees with Account.Region__c (or similar business rule).
