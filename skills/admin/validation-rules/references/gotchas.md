# Gotchas: Validation Rules

---

## Rules Fire During Data Loads — Always Have a Bypass

**What happens:** A data migration is scheduled. The data team uses Data Loader to insert 50,000 Account records. The import fails at record 1 because a validation rule requires a field that isn't in the migration dataset. The migration stops. The data team asks the admin to "turn off validation rules" — and the admin deactivates rules in production, forgetting one, then can't remember which ones were active.

**When it bites you:** Every data migration, every batch import, every API integration that writes records.

**How to avoid it:**
- Add a `NOT($Permission.Bypass_Validation_Rules)` clause to every validation rule
- Create a Permission Set that grants this Custom Permission
- Assign the Permission Set to the integration/migration user
- Never deactivate rules in production — use the bypass mechanism
- After the migration, revoke the Permission Set from the migration user

---

## PRIORVALUE Does Not Work on Insert

**What happens:** An admin writes a rule to flag when a Stage changes backward (e.g. from "Closed Won" back to "Prospecting"). The formula uses `PRIORVALUE(StageName)`. On a new record insert, `PRIORVALUE(StageName)` returns null. The formula evaluates with null as the prior value, producing unexpected results — sometimes firing an error on every new record.

**When it bites you:** First user tries to create a new record and gets a validation error. The admin says "that rule shouldn't fire on new records." It does, because PRIORVALUE returns null and the formula wasn't guarded.

**How to avoid it:**
```
// BAD — fires unexpectedly on insert because PRIORVALUE is null
AND(
  ISPICKVAL(StageName, "Prospecting"),
  ISPICKVAL(PRIORVALUE(StageName), "Closed Won")
)

// GOOD — NOT(ISNEW()) excludes inserts entirely
AND(
  NOT(ISNEW()),
  ISPICKVAL(StageName, "Prospecting"),
  ISPICKVAL(PRIORVALUE(StageName), "Closed Won")
)
```

---

## Validation Rules Fire in Undefined Order — No Dependencies Between Rules

**What happens:** An admin writes Rule A ("Field X is required if Status is Active") and Rule B ("Status cannot be Active if Field Y is blank"). The admin tests them separately. They both work. But when both fire at once on the same record, the user sees two errors in an order the admin didn't expect, and the second error references a field that the first error's fix would have resolved.

**When it bites you:** Complex objects with 10+ validation rules. Users get overwhelmed by multiple simultaneous errors they can't resolve in order.

**How to avoid it:**
- Don't write rules that depend on each other's outcomes
- Validate one concern per rule — keep rules atomic
- Test all rules simultaneously with a deliberately broken record (set multiple bad values at once)
- Document rule dependencies if they exist and note that evaluation order is not guaranteed

---

## Blank vs Null in Number and Currency Fields

**What happens:** A validation rule uses `ISBLANK(Annual_Revenue__c)` to check if a currency field is empty. The field has value `0`. The rule fires — but the user entered `0` intentionally. `ISBLANK()` returns FALSE for 0 (0 is not blank), but `ISNULL()` would return FALSE too (0 is not null). However, an empty number field IS null. The admin expects ISBLANK to catch "no value entered" but the behaviour differs by field type.

**Rules:**
- Text fields: `ISBLANK(TextField__c)` catches both blank and null
- Number/Currency fields: `ISBLANK(NumberField__c)` returns TRUE only for null (not 0)
- Checkbox fields: Never blank — always TRUE or FALSE
- Date fields: `ISBLANK(DateField__c)` returns TRUE for null

**How to avoid it:**
- For number/currency required-field checks: `ISBLANK(Revenue__c)` is correct — it fires only when no value is entered (null), not when 0 is entered
- If you need to catch both null AND zero: `OR(ISBLANK(Revenue__c), Revenue__c = 0)`
- Document in the rule description which values the rule is designed to catch

---

## Rules Fire on REST and SOAP API by Default

**What happens:** A Mulesoft integration creates Opportunity records via REST API. A new validation rule is deployed. No one tells the integration team. The integration starts failing silently — records aren't being created, the error is being swallowed by the Mulesoft flow, and it takes three days to notice that 500 Opportunities are missing.

**When it bites you:** After any validation rule deployment to production, when integrations aren't part of the test plan.

**How to avoid it:**
- Always include integration testing in validation rule deployment plans
- Maintain a list of all integrations that write to each object
- Use the bypass Custom Permission pattern for all integration users
- Monitor integration failure rates after any metadata deployment (use a Salesforce dashboard or your integration platform's monitoring)
