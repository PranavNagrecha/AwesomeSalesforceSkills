# Examples: Formula Fields

---

## Example: Account Health Status From Multiple Inputs

**Goal:** Show a simple health status to users without storing a separate field.

```text
CASE(
  TRUE,
  Open_Cases__c > 5, "At Risk",
  ARR__c >= 50000 && Last_Activity_Days__c <= 30, "Healthy",
  "Monitor"
)
```

**Why this works:** The formula is readable, business-facing, and does not need historical preservation.

---

## Example: Cross-Object Formula for Parent Visibility

**Goal:** Show the parent Account owner on Contact for reporting and page layout convenience.

```text
Account.Owner.Name
```

**Use carefully:** This is fine for display. Do not let a growing set of chained parent references become your reporting architecture.

---

## Example: Defensive Null Handling for Discount Math

**Goal:** Calculate a safe percentage without divide-by-zero behavior.

```text
IF(
  OR(ISBLANK(List_Price__c), List_Price__c = 0),
  NULL,
  (List_Price__c - Net_Price__c) / List_Price__c
)
```

**Why this works:** Blank and zero are handled explicitly, so the formula avoids misleading output.

---

## Example: Link Formula for User Navigation

**Goal:** Give users a quick link to an external contract record.

```text
HYPERLINK(
  "https://contracts.example.org/" & External_Contract_Id__c,
  "Open Contract",
  "_blank"
)
```

**Rule:** Keep this as convenience-only. The external key still belongs in a normal field.
