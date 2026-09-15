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
- This gotcha is about **number/currency/date/text** fields only. A **picklist** field behaves differently
  again — `ISBLANK()`/`ISNULL()` don't just give a surprising answer on a picklist, they don't compile at all.
  See Gotcha 14 below.

---

## Rules Fire on REST and SOAP API by Default

**What happens:** A Mulesoft integration creates Opportunity records via REST API. A new validation rule is deployed. No one tells the integration team. The integration starts failing silently — records aren't being created, the error is being swallowed by the Mulesoft flow, and it takes three days to notice that 500 Opportunities are missing.

**When it bites you:** After any validation rule deployment to production, when integrations aren't part of the test plan.

**How to avoid it:**
- Always include integration testing in validation rule deployment plans
- Maintain a list of all integrations that write to each object
- Use the bypass Custom Permission pattern for all integration users
- Monitor integration failure rates after any metadata deployment (use a Salesforce dashboard or your integration platform's monitoring)

---

## A User Checkbox Bypass Is Not a Custom Permission

**What happens:** Validation (or Flow) gates on `$User.Suspend_Rules__c` or a named User Id (`CreatedById = '005…'`). The checkbox is granted by whoever can edit User. The Id dies when the person leaves. Both look like a "bypass" in a screenshot.

**When it bites you:** Small-team orgs that grew; PE / founder-led Salesforce; any rule that mentions a person.

**How to avoid it:**
- Bypass with `NOT($Permission.Bypass_Validation_Rules)` on a Custom Permission granted by Permission Set.
- Rank: Custom Permission > User checkbox > Profile name > hardcoded `005` Id. Never ship the last two as the design.
- Name-picklists ("who owns this") are not `Lookup(User)` — they cannot deactivate, reassign, or report as people.

---

## A Workflow Field Update Re-Saves the Record and Validation Rules Do Not Run Again

**What happens:** The order of execution runs custom validation rules at step 5, then saves at step 7, then
runs workflow rules at step 11. When a workflow rule has a field update, the platform "updates the record
again" and "runs system validations again" — but the Apex Developer Guide is explicit that at that point
"custom validation rules, flows, duplicate rules, processes built with Process Builder, and escalation rules
aren't run again." A workflow field update can therefore leave a committed record in exactly the state your
validation rule exists to prevent.

**When it bites you:** Legacy orgs still carrying workflow rules. A rule enforces "Discount cannot exceed
20%", a workflow field update sets Discount to 25% when Tier changes, and the record commits at 25%. The
audit report shows records that violate an active rule and nobody can reproduce it by hand.

**How to avoid it:**
- Inventory workflow field updates on every object before trusting a validation rule as an invariant.
- Migrate the workflow field update to a before-save record-triggered flow (step 3) — that runs *before*
  validation at step 5, so the validation rule sees the flow's value and can reject it.
- Where the invariant genuinely must hold in the database, back it with a `@InvocableMethod`-free before-save
  flow plus the validation rule, not the validation rule alone.
- Treat "records exist that violate an active rule" as a workflow-field-update symptom until proven otherwise.

---

## Opportunity Validation Rules Do Not Fire When a Line Item Changes the Opportunity

**What happens:** The Apex Developer Guide states that before and after triggers *and validation rules* don't
fire for an opportunity when you modify an opportunity product on the opportunity, or when an opportunity
product schedule changes an opportunity product — even if the opportunity product changes the opportunity.
Roll-up summary fields still update and workflow rules still run. So `Amount` moves, the roll-up recalculates,
and the rule guarding `Amount` never evaluates.

**When it bites you:** Any Opportunity rule written against `Amount`, `TotalOpportunityQuantity`, or a
roll-up summary of line items. The rule tests perfectly when an admin edits Amount by hand and is inert in
the actual business process, which is line-item driven.

**How to avoid it:**
- Never guard a line-item-derived Opportunity field with an Opportunity validation rule.
- Put the rule on `OpportunityLineItem` instead, where the user's edit actually lands.
- If the invariant is genuinely opportunity-level (total discount across all lines), a record-triggered flow
  or trigger on `OpportunityLineItem` that re-checks the parent is the only surface that sees the change —
  see `flow/record-triggered-flow-patterns`.

---

## errorDisplayField Silently Relocates to Top of Page

**What happens:** `errorDisplayField` names the field the error appears next to. The Metadata API Developer
Guide's ValidationRule field table adds the condition nobody reads: "If you do not specify a value **or the
field isn't visible on the page layout**, the value changes automatically to Top of Page." Removing a field
from one layout, or shipping a new record type with a lean layout, moves the error message without touching
the rule, without a deploy, and without a warning.

**When it bites you:** After a page-layout change or a new record type. Users on the affected layout report a
banner at the top of the page with no indication of which field to fix; users on the original layout see the
inline error and cannot reproduce the complaint.

**How to avoid it:**
- Add `errorDisplayField` to the change-impact list for any field removed from a layout.
- Assert on it in Apex: `Database.Error.getFields()` returns the field the error attached to, so a test can
  fail when the error silently relocates (see `references/metadata-examples.md`, Test 1).
- Write the error message so it names its own field. A message that reads correctly at the top of the page
  costs nothing and survives the relocation.

---

## VLOOKUP Stops Seeing Org Data Inside Apex Tests as of API 28.0

**What happens:** In API version 27.0 and earlier, the `VLOOKUP` validation rule function always looked up org
data in addition to test data when fired by a running Apex test. Starting with version 28.0 it no longer
accesses organization data from a running test — it sees only data the test created, unless the test class or
method is annotated `@IsTest(SeeAllData=true)`. The same rule therefore behaves differently in a test and in
production.

**When it bites you:** A rule that validates a value against a Custom Object lookup table (approved product
codes, valid country codes, allowed discount tiers). The lookup table is org data seeded once by an admin. In
a test it is empty, `VLOOKUP` returns nothing, and the rule either passes everything or blocks everything —
the opposite of what production does.

**How to avoid it:**
- Any test that exercises a `VLOOKUP`-based rule must either create the lookup rows itself or be annotated
  `@IsTest(SeeAllData=true)`.
- Prefer Custom Metadata Types over a Custom Object for lookup tables the rule reads — they are visible in
  tests without `SeeAllData`, and validation rules on custom metadata types have been supported since API
  version 40.0.
- A `VLOOKUP` rule with a green test is not evidence the rule works. Verify it manually in a sandbox that has
  the lookup data.

---

## ValidationRule Does Not Support the Wildcard in package.xml

**What happens:** The Metadata API Developer Guide states plainly that ValidationRule "doesn't support the
wildcard character `*` (asterisk) in the package.xml manifest file." A manifest with
`<members>*</members><name>ValidationRule</name>` does not error usefully — it simply retrieves nothing, and
the deploy that follows is missing every rule while reporting success.

**When it bites you:** Building a change set manifest by hand, or scripting an org-comparison retrieve. The
diff comes back clean because the rules were never retrieved, and the release goes out without them.

**How to avoid it:**
- Name each rule explicitly as `Object.RuleName`, or retrieve the enclosing object with
  `<name>CustomObject</name>` — retrieving the object returns every rule on it.
- After any wildcard-based retrieve, count the `<validationRules>` elements you got against the count in
  Setup before you trust the diff.
- `references/metadata-examples.md` has both manifest shapes.

---

## Translated Error Messages Live in a Separate Metadata Type

**What happens:** `errorMessage` on the rule is the default-language string only. Every translated version is
a `ValidationRuleTranslation` entry — `name` plus `errorMessage` — inside a `CustomObjectTranslation`
component, deployed as a separate file per language. Deploying the object, or the rule, carries none of them.

**When it bites you:** Multi-language orgs. A rule is edited in English, deploys cleanly, and non-English
users keep seeing the old message — or see the English one — because the translation was never touched. The
guide also warns that retrieving or deploying translations from a package can override existing translations,
which appear in the Rename Tabs and Labels UI until reset.

**How to avoid it:**
- Add `CustomObjectTranslation` for every active language to the same manifest whenever a rule's
  `errorMessage` changes.
- Make "message changed → translations updated" a line in the rule's change history, not a tribal habit.
- Rewording an error message is a translation-affecting change even when the logic is untouched.

---

## Compound Fields Cannot Be Used in a Validation Rule at All

**What happens:** As of API version 20.0, validation rules can't have compound fields. Compound fields include
addresses, first and last names, dependent picklists, and dependent lookups. `ISBLANK(BillingAddress)` or a
rule that treats `Name` on Contact as one value does not fail at save time with a helpful message — it fails
when the formula is compiled, at deploy or at save in Setup.

**When it bites you:** "Billing address is required before an Account can be activated" is the single most
requested validation rule and the compound field `BillingAddress` cannot express it.

**How to avoid it:**
- Validate the **components**: `BillingStreet`, `BillingCity`, `BillingPostalCode`, `BillingCountry` — each is
  an ordinary field and each works in a formula.
- For a person's name, validate `FirstName` and `LastName` separately, not `Name`.
- For a dependent picklist, `ISPICKVAL` the controlling and dependent fields independently; the dependency
  itself is enforced by the field configuration, not by the rule.
- `admin/formula-fields` covers which field types are addressable in formula syntax generally.

---

## Gotcha 14: ISBLANK() / ISNULL() Applied Directly to a Picklist Field Does Not Compile

**What happens:** `ISBLANK(StageName)` and `ISNULL(StageName)` look like the same null/blank guard that
works on every other field type, and the "GOOD" pattern for guarding a picklist check against blank looks
exactly like guarding a text or date field against blank. It isn't. Applying `ISBLANK(` or `ISNULL(` directly
to a picklist field is rejected at deploy/save time with:

> `Field StageName is a picklist field. Picklist fields are only supported in certain functions.`

Proven live on **2026-09-12** via `sf project deploy start --dry-run` at **API 67.0** against a formula of the
shape `AND(NOT(ISBLANK(StageName)), ISPICKVAL(StageName, "Closed Won"), ...)` — this is the exact defect this
skill previously shipped in its own "Formula Best Practices → GOOD" example in `SKILL.md`, corrected
2026-09-12 to `NOT(ISBLANK(TEXT(StageName)))`.

**When it occurs:** Any formula that null-guards a picklist the "obvious" way — `NOT(ISBLANK(Field__c))` or
`NOT(ISNULL(Field__c))` — before or alongside an `ISPICKVAL(Field__c, ...)` check on the same field. It fails
at compile time (deploy or Setup save), not at run time, so no record ever has to hit the rule to find the
bug — the deploy itself is rejected.

**How to avoid it:**
- Wrap the picklist in `TEXT()` first — `TEXT()` converts a picklist to a string, and `ISBLANK()`/`ISNULL()`
  accept a string. `NOT(ISBLANK(StageName))` → `NOT(ISBLANK(TEXT(StageName)))`.
- Functions confirmed (by this skill's own metadata-examples and formula patterns) to accept a picklist field
  **directly**, with no `TEXT()` wrapper needed: `ISPICKVAL(Field, "Value")` (equality check — see every
  example in `references/examples.md`), `PRIORVALUE(Field)` (prior value — see the PRIORVALUE gotcha above),
  and `ISCHANGED(Field)` (change detection — see `templates/admin/validation-rule-patterns.md`). None of these
  fail in this skill's own worked examples, which is the closest thing to a corpus confirmation available here.
- `CASE(Field, ...)` is commonly documented elsewhere as accepting a picklist directly, and `TEXT(Field)` by
  definition takes a picklist as input (that is its purpose) — both are consistent with the platform's own
  "certain functions" framing in the error text.
  > UNVERIFIED (2026-09-12): the exact list of functions that accept a picklist field directly is a Formula
  > Language / Functions reference claim. It is **not** confirmed in this skill's fetched corpus
  > (`api_meta.txt` — Metadata API Developer Guide — and `salesforce_apex_developer_guide.txt` — Apex
  > Developer Guide); neither documents formula-function argument-type semantics. Only the compile failure
  > itself is proven, via the live `sf project deploy start --dry-run` probe cited above. Verify the full
  > function list against the Formula Language reference before treating it as exhaustive.
- Run `scripts/check_validation_rules.py` before deploying — it flags this pattern as `VR-PICK-01` (HIGH,
  blocking) whenever a field is passed to both `ISBLANK(`/`ISNULL(` directly and to `ISPICKVAL(` as its first
  argument in the same formula.

---

## Gotcha 15: HasOpportunityLineItem Is Platform-Set, Read-Only, and Never True on Insert

**What happens:** "an opportunity cannot reach Propose without products" gets built as a roll-up
summary of `OpportunityLineItem` onto Opportunity, or a formula field, or a trigger — and then a
validation rule reads that. All three are unnecessary work, and two of them are actively wrong:
a roll-up recalculates but, per the "Opportunity Validation Rules Do Not Fire When a Line Item
Changes the Opportunity" gotcha above, its recalculation does not itself hand the Opportunity
rule a save to evaluate. The Opportunity already carries the answer:

> `HasOpportunityLineItem` — Type `boolean`; Properties `Defaulted on create, Filter, Group,
> Sort`. "Read-only field that indicates whether the opportunity has associated line items."
> — Object Reference for the Salesforce Platform, Opportunity
> (`knowledge/imports/salesforce-channel-revenue-management.md:3911-3918`); set to true "when an
> `OpportunityLineItem` is inserted for that Opportunity" (same guide, line 4696).

**Three consequences the `Properties` line alone gives you:**

| Property present | Property absent | What follows |
|---|---|---|
| `Filter`, `Group`, `Sort` | — | You can report and filter on it. `skills/admin/pipeline-review-design/references/gotchas.md:91` uses exactly this to put a "has products" column on a pipeline review |
| — | no `Create`, no `Update` | It is read-only, as the description says outright. You cannot seed it in a data load, default it on a record type, or repair it — the only way to make it true is to insert a line item |
| `Defaulted on create` | — | It has a value on every insert, and that value is `false`: a line item is inserted *for* an Opportunity, so no line item can exist during the Opportunity's own insert transaction (derived from the line 4696 quote, which does not spell out the insert case) |

**When it bites you:**

- **An `ISNEW()` fire condition bricks record creation.** Because the field is false on every
  insert, a rule that fires on `AND(ISNEW(), ISPICKVAL(StageName,"Propose"), NOT(HasOpportunityLineItem))`
  does not gate creation at `Propose` — it forbids it. Reps discover this as "I can't create the
  deal at all" and start creating at `Qualify` and immediately editing, which is the workflow
  the rule should have asked for explicitly instead of enforcing by accident.
- **Quantity and price checks do not live here.** `Quantity`, `UnitPrice` and `TotalPrice` are
  `OpportunityLineItem` fields. "At least one product" is a header question and
  `HasOpportunityLineItem` answers it; "every line has a positive quantity" is a line-item
  question and the rule belongs on `OpportunityLineItem`, where the rep's edit lands.
- **The gate is on the stage change, not on the product.** The rule evaluates when the
  Opportunity header is saved. The rep's real sequence is create → add products → change stage,
  and a rep who moves the stage first is told to go back and add a product. That is the intended
  flow, but it is a flow the requester has to have agreed to.

**The corpus disagrees with itself about the reverse direction, and it matters here.** Whether
*deleting the last line item* from a deal already at `Propose` re-fires this rule is not settled
by the sources this library carries:

| Source | Says |
|---|---|
| Apex Developer Guide, Trigger and Order of Execution Considerations (cited in `references/well-architected.md`, and the basis of the line-item gotcha above) | Validation rules don't fire for an opportunity when you modify an opportunity product, even if the opportunity product changes the opportunity |
| Object Reference, Opportunity → Usage (`knowledge/imports/salesforce-channel-revenue-management.md:4299-4302`) | "On opportunities and opportunity products, the workflow rules, validation rules, and Apex triggers fire when an update to a child opportunity product or schedule causes an update to the parent record" |

> UNVERIFIED (2026-09-15): these two official sources are in direct conflict and no probe in
> this repo has settled it. Treat the rule as enforcing the **forward** gate only (you cannot
> move the stage forward without products) and do **not** promise the requester that it prevents
> a deal from ending up at `Propose` with zero products after a deletion. If that invariant is
> genuinely required, the surface that certainly sees the deletion is a record-triggered flow or
> trigger on `OpportunityLineItem` — see `flow/record-triggered-flow-patterns`.

**How to avoid it:**

- Use `NOT(HasOpportunityLineItem)` as the business condition; do not build a roll-up, a formula
  field or a trigger to count line items. `scripts/check_validation_rules.py` flags the count
  shapes as `VR-OPP-01` (INFO, advisory).
- Guard with `NOT(ISNEW())` plus `ISCHANGED(StageName)` so the rule gates the transition and
  neither forbids creation nor freezes records already sitting at the gated stage.
- Decide four things with the requester before writing the formula: which stages are gated;
  whether `Closed Lost` is one of them; whether a deal may be **created** already at a gated
  stage (if not, the answer is a separate `ISNEW()` rule with its own message, not an `ISNEW()`
  clause in this one); and whether deletion of the last line item must be caught, which this
  rule cannot be relied on to do.
- Before activating, list the deals the rule would block using the field's own filterability —
  it is reportable, which is why `admin/pipeline-review-design` already recommends it as a
  column.
