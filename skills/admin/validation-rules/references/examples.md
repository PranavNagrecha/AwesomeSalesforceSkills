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
