# Examples: Validation Rules

---

## Example: Required Field Based on Stage (Opportunity)

**Business requirement:** Close Date is required when Stage is "Closed Won" or "Closed Lost".

```
// Object: Opportunity
// Field: CloseDate
// Condition: Required when Stage is Closed Won or Closed Lost

AND(
  OR(
    ISPICKVAL(StageName, "Closed Won"),
    ISPICKVAL(StageName, "Closed Lost")
  ),
  ISBLANK(CloseDate)
)
```

**Error message (Field-level on CloseDate):**
> "Close Date is required when an Opportunity is Closed. Enter a Close Date to save."

**With bypass for integration user:**
```
AND(
  OR(
    ISPICKVAL(StageName, "Closed Won"),
    ISPICKVAL(StageName, "Closed Lost")
  ),
  ISBLANK(CloseDate),
  NOT($Permission.Bypass_Opportunity_Validation)
)
```

**Why the bypass is structured this way:** The Custom Permission `Bypass_Opportunity_Validation` is granted to the integration user's Permission Set. Adding `NOT($Permission...)` as the last AND condition means the rule only fires if none of the bypass conditions are met.

---

## Example: Date Must Be in the Future (Event Object)

**Business requirement:** Event Start Date cannot be in the past when creating a new event.

```
// Object: Event (or custom object with a date field)
// Fires on: Insert only (new records)
// Condition: Start date is in the past

AND(
  ISNEW(),                           // Only on insert — not on edit
  NOT(ISBLANK(StartDateTime)),       // Field has a value
  StartDateTime < NOW()              // Date is in the past
)
```

**Why `ISNEW()`:** Without this, editing an existing past event (to add notes, change status) would fire the error. The rule is only meaningful on creation.

**Error message (Field-level on StartDateTime):**
> "Start Date must be today or in the future. You cannot schedule events in the past."

---

## Example: Conditional Required with Record Type Scope

**Business requirement:** For "Enterprise" Opportunity record type, Annual Contract Value (ACV__c) is required when Stage is "Proposal/Quote" or later.

```
// Object: Opportunity
// Only applies to "Enterprise" Record Type

AND(
  RecordType.DeveloperName = "Enterprise",          // Scoped to Enterprise RT only
  OR(
    ISPICKVAL(StageName, "Proposal/Quote"),
    ISPICKVAL(StageName, "Negotiation/Review"),
    ISPICKVAL(StageName, "Closed Won"),
    ISPICKVAL(StageName, "Closed Lost")
  ),
  ISBLANK(ACV__c)
)
```

**Error message (Field-level on ACV__c):**
> "Annual Contract Value (ACV) is required for Enterprise opportunities at Proposal stage or later. Enter the expected annual contract value to proceed."

**Why `RecordType.DeveloperName` not `RecordType.Name`:** Developer Name is the API name — it doesn't change if someone renames the Record Type label. Name is the label and can be renamed by any admin. Always use DeveloperName in formulas.

---

## Example: Bypass for Admin/Integration Users via Custom Permission

**Setup:**
1. Create Custom Permission: API Name = `Bypass_Validation_Rules`, Label = `Bypass Validation Rules`
2. Create Permission Set: `Integration_BypassValidation`
3. Add Custom Permission to the Permission Set
4. Assign Permission Set to the integration user

**Formula pattern (add to ANY rule that needs a bypass):**
```
AND(
  [... your validation condition ...],
  NOT($Permission.Bypass_Validation_Rules)
)
```

**Why Custom Permissions are better than Profile checks:**
- `$Profile.Name <> "System Administrator"` breaks if the profile is renamed
- Custom Permissions can be granted to any user via Permission Set — no profile dependency
- Custom Permissions are auditable (who has them, when granted)
- Multiple bypass permissions can be created for different scenarios

---

## Example: Cross-Object Validation (Parent Field Drives Child Requirement)

**Business requirement:** A Case cannot be closed unless the parent Account has an active Support Contract (Support_Contract_Active__c = TRUE).

```
// Object: Case
// Cross-object formula — checks parent Account field

AND(
  ISPICKVAL(Status, "Closed"),
  NOT(Account.Support_Contract_Active__c)
)
```

**Error message (Page-level):**
> "This Case cannot be closed because the Account does not have an active Support Contract. Contact your Account Manager to activate a Support Contract before closing this Case."

**Gotcha:** Cross-object validation rules can only traverse one level up (Case → Account is fine; Case → Account → Parent_Account is not). For deeper traversal, use a Flow or Apex trigger instead.

**Performance note:** Cross-object formulas query the parent record on every save. On high-volume objects, this adds latency. Acceptable for Case (typically lower volume), worth noting for very high-volume objects.

---

## Example: At Least One Opportunity Product Before a Late Stage (Opportunity)

**Business requirement:** an Enterprise opportunity cannot move to `Propose` (or any later
open stage) until the rep has added at least one product line from the price book.

### The mechanism — the header already carries the answer

The naive readings of this requirement are a roll-up summary counting `OpportunityLineItem`
rows, a formula field over the child records, or a trigger. None is necessary. Opportunity
carries a standard boolean that the platform maintains for exactly this question:

> `HasOpportunityLineItem` — Type `boolean`; Properties `Defaulted on create, Filter, Group,
> Sort`. "Read-only field that indicates whether the opportunity has associated line items. A
> value of `true` means that Opportunity line items have been created for the opportunity."
> — Object Reference for the Salesforce Platform, Opportunity
> (`knowledge/imports/salesforce-channel-revenue-management.md:3911-3918`)

> "The Opportunity `HasOpportunityLineItem` field is set to true when an `OpportunityLineItem`
> is inserted for that Opportunity."
> — same guide, OpportunityLineItem → Usage
> (`knowledge/imports/salesforce-channel-revenue-management.md:4696`)

So the business condition is `NOT(HasOpportunityLineItem)`, gated on the stage.

> org-verified 2026-09-19 (checkOnly compile; re-firing after a line-item deletion remains
> UNVERIFIED — a checkOnly deploy exercises no deletion). The corpus cited above grounds the
> field's existence, type, read-only semantics and when the platform sets it, but made no
> formula-context claim; the dry run settled that part. northwind-sales M2 dry run 1
> (2026-09-19T14:56Z, `.sfskills/builds/northwind-sales/reports/mock-deploy/2026-09-19T14-56-10Z/`)
> compiled this `errorConditionFormula` with only a description-length error returned — so
> `HasOpportunityLineItem` **is** addressable in validation-rule formula context. What the run
> did not and could not test is whether the rule re-fires when a line item is deleted off an
> Opportunity already at `Propose`: a checkOnly deploy runs no DML. See Gotcha 15.

### The formula

```
AND(
  NOT($Permission.Bypass_Opportunity_Sales_Validation),
  RecordType.DeveloperName = "Enterprise",
  NOT(ISNEW()),
  ISCHANGED(StageName),
  OR(
    ISPICKVAL(StageName, "Propose"),
    ISPICKVAL(StageName, "Negotiate"),
    ISPICKVAL(StageName, "Closed Won")
  ),
  NOT(HasOpportunityLineItem)
)
```

Read in the canonical order from `templates/admin/validation-rule-patterns.md` — bypass,
relevance gate, business condition:

| Clause | Why it is there |
|---|---|
| `NOT($Permission.Bypass_Opportunity_Sales_Validation)` | The bypass pattern this skill uses everywhere — Custom Permission, first inside the `AND`, granted by Permission Set. See the "Bypass for Admin/Integration Users via Custom Permission" example above |
| `RecordType.DeveloperName = "Enterprise"` | Renewals run a different process and must not be gated. `DeveloperName` is text, so it is compared with `=`, never `ISPICKVAL` |
| `NOT(ISNEW())` | **Load-bearing, not boilerplate.** A line item is inserted *for* an Opportunity that already exists, so `HasOpportunityLineItem` cannot be true during the Opportunity's own insert. An `ISNEW()` fire condition would make creating a deal at `Propose` impossible rather than merely gated |
| `ISCHANGED(StageName)` | The rule fires on the **transition into** a late stage, not on every later edit. Without it, a deal already sitting at `Propose` with no products is frozen — every save of every other field is rejected, which is the "existing records are trapped" failure the `NOT(ISNEW())` guard in the PRIORVALUE gotcha exists to prevent |
| `OR(ISPICKVAL(...))` | The stages the requester named. `Closed Lost` is deliberately absent — a deal lost before a quote was ever built has no products and blocking it teaches reps to park dead deals in `Negotiate` |
| `NOT(HasOpportunityLineItem)` | The business condition. The formula describes the **invalid** state |

For a sharper transition test — fire only when moving *forward* into `Propose` from an earlier
stage — swap `ISCHANGED(StageName)` for
`ISPICKVAL(PRIORVALUE(StageName), "Discover")`. `PRIORVALUE` is already safe here because
`NOT(ISNEW())` is present; see "PRIORVALUE Does Not Work on Insert" in `references/gotchas.md`.

### The metadata

```xml
<!-- force-app/main/default/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Opportunity_Products_Required_At_Propose</fullName>
    <active>true</active>
    <description>Enterprise deals must carry at least one price-book line before Propose. Reads the platform-maintained HasOpportunityLineItem rather than a roll-up count. Owner: RevOps. Bypass: Bypass_Opportunity_Sales_Validation.</description>
    <errorConditionFormula>AND(
  NOT($Permission.Bypass_Opportunity_Sales_Validation),
  RecordType.DeveloperName = "Enterprise",
  NOT(ISNEW()),
  ISCHANGED(StageName),
  OR(
    ISPICKVAL(StageName, "Propose"),
    ISPICKVAL(StageName, "Negotiate"),
    ISPICKVAL(StageName, "Closed Won")
  ),
  NOT(HasOpportunityLineItem)
)</errorConditionFormula>
    <errorDisplayField>StageName</errorDisplayField>
    <errorMessage>Add at least one product before moving this opportunity to Propose. Use the Products related list to add a line from the price book, then change the Stage.</errorMessage>
</ValidationRule>
```

`errorDisplayField` is `StageName` and not a product field, because `StageName` is the field the
user just changed and the only field in scope that is on every Opportunity layout. The message is
written to read correctly at the top of the page too, since `errorDisplayField` relocates
silently when the field leaves a layout — see `references/gotchas.md`.

### Related coverage

- `references/gotchas.md`, "HasOpportunityLineItem Is Platform-Set…" — read-only semantics,
  what it cannot do, and the corpus conflict over whether a line-item edit re-fires this rule.
- `skills/admin/pipeline-review-design/references/gotchas.md:91` — the same field as a **report
  column**. It is filterable, so a pipeline review can list the deals this rule would now block
  before the rule is switched on. That is the cleanup query for the "does the data already
  violate this rule today?" question in `SKILL.md`.
- `skills/admin/products-and-pricebooks/references/gotchas.md` — the catalog side: do not build a
  second source of truth for a fact the header already holds.
