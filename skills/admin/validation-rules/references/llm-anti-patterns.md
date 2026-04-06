# LLM Anti-Patterns — Validation Rules

Common mistakes AI coding assistants make when generating or advising on Salesforce Validation Rules.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing the formula for when the record IS valid instead of when it is INVALID

**What the LLM generates:** `Amount > 0` — "This ensures the amount is positive."

**Why it happens:** LLMs think in terms of "what makes data valid" and write the condition accordingly. Salesforce validation rules fire (show error) when the formula evaluates to TRUE. The formula should express the INVALID condition. `Amount > 0` fires the error when Amount IS positive -- the opposite of what is intended.

**Correct pattern:**

```
Validation rules fire when formula = TRUE (invalid condition).

Wrong: Amount > 0 (fires error when Amount IS positive)
Right: Amount <= 0 (fires error when Amount is zero or negative)

Or more safely with null handling:
OR(
  ISBLANK(Amount),
  Amount <= 0
)

Mnemonic: "The formula describes the BAD state."
```

**Detection hint:** Read the formula and ask: "If this is TRUE, should I block the save?" If the answer is "no, that is the valid state," the logic is inverted. Check if the formula describes the valid condition instead of the invalid one.

---

## Anti-Pattern 2: Not including a bypass mechanism for integrations and data loads

**What the LLM generates:** `ISPICKVAL(Status, 'Closed') && ISBLANK(Resolution__c)` — "Block save if closed without resolution."

**Why it happens:** LLMs write strict validation without considering that integrations, Data Loader, and migration scripts may need to create or update records that do not meet the validation criteria. Without a bypass, data loads fail on every non-compliant record.

**Correct pattern:**

```
Add a bypass guard to validation rules:
1. Create a custom permission: Bypass_Validation_Rules.
2. Add a bypass check to the formula:
   AND(
     NOT($Permission.Bypass_Validation_Rules),
     ISPICKVAL(Status, 'Closed'),
     ISBLANK(Resolution__c)
   )
3. Assign the Bypass_Validation_Rules permission to the
   integration user's permission set.
4. For data loads: assign the bypass permission temporarily,
   then remove it after the load completes.
5. Document which rules have bypass guards and which do not.
```

**Detection hint:** If the validation rule formula has no bypass mechanism (no `$Permission`, no `$User`, no `$Profile` check), integrations will be blocked. Regex: absence of `\$Permission\.` or `\$User\.` or `\$Profile\.` in the formula.

---

## Anti-Pattern 3: Not scoping the rule to specific record types

**What the LLM generates:** `ISBLANK(Industry)` — "Require Industry on all Account records."

**Why it happens:** LLMs write universal rules without considering that different record types may have different requirements. An "Individual" Account record type may not need an Industry value, but a "Business" Account record type does. Without record type scoping, the rule blocks valid saves for unintended record types.

**Correct pattern:**

```
Scope validation rules to relevant record types:
AND(
  RecordType.DeveloperName = 'Business_Account',
  ISBLANK(Industry)
)

Or exclude specific record types:
AND(
  RecordType.DeveloperName != 'Individual',
  ISBLANK(Industry)
)

Best practice:
- Always consider whether the rule should apply to ALL record types.
- Use RecordType.DeveloperName (not RecordType.Name) for reliability
  across translations and label changes.
```

**Detection hint:** If a validation rule formula does not reference `RecordType` and the object has multiple record types, the rule may be over-scoped. Check if the object has record types and whether the rule should apply to all of them.

---

## Anti-Pattern 4: Writing error messages that do not tell the user how to fix the problem

**What the LLM generates:** Error message: "Validation error."

**Why it happens:** LLMs focus on the formula logic and write placeholder error messages. Users see the error message on their screen and need to know what is wrong and how to fix it. A vague message causes support tickets and user frustration.

**Correct pattern:**

```
Error message best practices:
1. State what is wrong: "Close Date cannot be in the past."
2. State how to fix it: "Please select a Close Date that is today or later."
3. Identify the field: place the error on the specific field
   (not at the top of the page) using the Error Location setting.
4. Use plain language, not technical jargon.

Example:
  Formula: CloseDate < TODAY()
  Error Message: "Close Date must be today or a future date.
  Please update the Close Date before saving."
  Error Location: Field → CloseDate

Bad: "Validation error" or "Invalid data" or "Error: rule 47 failed."
```

**Detection hint:** If the error message is fewer than 10 words or does not explain how to fix the problem, it is too vague. Check the error message for action-oriented language (e.g., "please update," "select a valid," "enter a value").

---

## Anti-Pattern 5: Using ISNEW() without considering updates that should also be validated

**What the LLM generates:** `AND(ISNEW(), ISBLANK(Priority))` — "Require Priority on new records."

**Why it happens:** LLMs use ISNEW() to restrict the rule to record creation, but the business rule often applies to updates too. If a user creates a record with Priority filled, then later edits the record and blanks out Priority, the validation does not fire because ISNEW() is false on updates.

**Correct pattern:**

```
Consider whether the rule should fire on insert AND update:

Insert-only validation (rare):
  AND(ISNEW(), ISBLANK(Priority))
  Use only if the field should be required at creation but can be
  blanked later (uncommon).

Insert and update validation (common):
  ISBLANK(Priority)
  Fires on every save — insert or update.

Update-only validation (for status transitions):
  AND(
    NOT(ISNEW()),
    ISCHANGED(Status),
    ISPICKVAL(Status, 'Closed'),
    ISBLANK(Resolution__c)
  )
  Only fires when Status changes to Closed on an existing record.
```

**Detection hint:** If the formula uses `ISNEW()` for a field that should always be required, updates will bypass the rule. Check if the business requirement applies only to creation or to all saves.

---

## Anti-Pattern 6: Not handling null values in picklist comparisons

**What the LLM generates:** `Status != 'Active'` — "Fire error when status is not Active."

**Why it happens:** LLMs use direct comparison operators on picklist fields. In Salesforce formulas, picklist fields should use ISPICKVAL() or TEXT() for comparisons. Direct comparison with != may not behave as expected for picklists, and does not handle the null case correctly.

**Correct pattern:**

```
Picklist comparison in validation rules:
Wrong: Status != 'Active'
Right: NOT(ISPICKVAL(Status, 'Active'))

With null handling:
AND(
  NOT(ISBLANK(TEXT(Status))),
  NOT(ISPICKVAL(Status, 'Active'))
)

Rules:
- Use ISPICKVAL() for picklist equality checks.
- Use TEXT() to convert picklist to text for CONTAINS or REGEX.
- Always consider: what if the picklist is blank?
- ISPICKVAL(field, '') returns TRUE when the picklist is blank.
```

**Detection hint:** If the formula uses `=` or `!=` directly on a picklist field instead of `ISPICKVAL()`, the comparison may not work correctly. Regex: `[A-Za-z_]+\s*(!=|==|=)\s*'[^']*'` on a known picklist field.
