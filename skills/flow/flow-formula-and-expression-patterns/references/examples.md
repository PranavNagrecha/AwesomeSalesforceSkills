# Examples — Flow Formula And Expression Patterns

Worked examples covering NULL-safe formula authoring, picklist comparison correctness, lazy re-evaluation refactoring, type coercion, time-zone handling, and the 5,000-character composition pattern. Each example is shown as it would appear inside a Flow Formula resource expression body or a Decision condition.

---

## Example 1: NULL-Safe Discount Total

**Context:** An Order Item has an optional `Discount__c` (Currency, not required). Formula computes net price.

**Problem:** Without a NULL guard the formula returns NULL whenever Discount__c is empty, propagating NULL to a downstream Update Records and either silently writing NULL back or breaking a Decision condition.

**Solution:**

```
{!recordVar.Amount} - BLANKVALUE({!recordVar.Discount__c}, 0)
```

**Why it works:** `BLANKVALUE` returns the second arg only when the first is null/empty. The minus operator then sees `Amount - 0` instead of `Amount - NULL`.

---

## Example 2: NULL-Safe Description with Default Text

**Context:** Email template merges `Description__c`. Empty descriptions look broken in the rendered email.

**Solution:**

```
BLANKVALUE({!recordVar.Description__c}, "(no description provided)")
```

**Why it works:** Text fields treat empty string and NULL as interchangeable, so `BLANKVALUE` covers both.

---

## Example 3: ISPICKVAL Bug — Before / After

**Context:** Decision branches on Opportunity Stage.

**Wrong (P1 silent bug — passes in dev English-only orgs, fails the moment a translation pack is added):**

```
{!opportunity.StageName} = "Closed Won"
```

**Correct:**

```
ISPICKVAL({!opportunity.StageName}, "Closed Won")
```

**Why it works:** `ISPICKVAL` compares against the API name, not the rendered label. Locale-immune.

---

## Example 4: INCLUDES for Multi-Select Picklist

**Context:** Account has a multi-select `Industries__c`. Branch when "Healthcare" is one of the selections.

**Wrong:**

```
{!account.Industries__c} = "Healthcare"
```

**Correct:**

```
INCLUDES({!account.Industries__c}, "Healthcare")
```

**Why it works:** Multi-select picklists are stored as a semicolon-delimited string. `=` will only match when "Healthcare" is the ONLY selected value. `INCLUDES` does the membership check.

---

## Example 5: Negation of Picklist Comparison

**Wrong:**

```
NOT({!opportunity.StageName} = "Closed Lost")
```

**Correct:**

```
NOT(ISPICKVAL({!opportunity.StageName}, "Closed Lost"))
```

---

## Example 6: Multiple Picklist Values With OR

```
OR(
  ISPICKVAL({!opportunity.StageName}, "Closed Won"),
  ISPICKVAL({!opportunity.StageName}, "Closed Lost")
)
```

**Why it works:** Each `ISPICKVAL` is a Boolean; `OR` short-circuits per platform docs.

---

## Example 7: Lazy Re-Evaluation — BEFORE Refactor

**Context:** Loop over 200 Opportunities. Inside the loop body, six elements reference `{!isHighValueOpportunity}`, a Formula resource defined as:

```
AND(
  {!loopVar.Amount} > 100000,
  ISPICKVAL({!loopVar.Type}, "Existing Customer - Upgrade"),
  NOT(ISBLANK({!loopVar.Account.OwnerId}))
)
```

The six references are: a Decision condition, three Assignments, an Update, and an Email body. The formula evaluates 6 × 200 = 1,200 times per flow run.

---

## Example 8: Lazy Re-Evaluation — AFTER Refactor

**Solution:** Add an Assignment at the top of the loop body that materialises the result into a Boolean variable `cachedHighValue`.

```
// Assignment "cacheHighValue":
//   cachedHighValue (Boolean) = {!isHighValueOpportunity}
//
// Switch all six downstream references from {!isHighValueOpportunity} to {!cachedHighValue}.
```

Result: 200 evaluations of the formula resource per flow run. The other 1,000 reads are simple variable lookups.

**Why it works:** Variable reads are not lazy; only Formula resources re-evaluate.

---

## Example 9: Type Coercion — Text To Number

**Context:** A Screen Flow captures a numeric quantity from a Text input.

```
IF(
  ISBLANK({!screenInput.QuantityText}),
  0,
  VALUE({!screenInput.QuantityText})
)
```

**Why it works:** `VALUE()` throws at runtime if the input is non-numeric. The `ISBLANK` guard returns 0 for empty string instead of a runtime exception.

---

## Example 10: Type Coercion — Number To Text Without Locale Surprise

```
TEXT({!recordVar.Amount})
```

**Why it works:** `TEXT()` of a Number returns the unformatted numeric (no thousands separator, no localisation). Formatting with thousands separators requires explicit string surgery — see Example 35.

---

## Example 11: Type Coercion — Text To DateTime

```
DATETIMEVALUE({!screenInput.DateTimeText})
```

**Required input format:** `YYYY-MM-DD HH:MM:SS` in GMT. Any other format throws "Argument 1 cannot be of type Text" at runtime.

---

## Example 12: Date Math — Days Between Two Dates

```
{!opportunity.CloseDate} - TODAY()
```

**Returns:** A Number representing the day delta. Positive if Close Date is in the future, negative if past.

**NULL safety:** If `CloseDate` is null, returns NULL. Wrap with `IF(ISBLANK({!opportunity.CloseDate}), 0, {!opportunity.CloseDate} - TODAY())`.

---

## Example 13: Date Math — Add 30 Days

```
TODAY() + 30
```

**Returns:** A Date 30 days after today.

---

## Example 14: DateTime Math — Add 4 Hours

```
{!recordVar.CreatedDate} + (4 / 24)
```

**Returns:** A DateTime 4 hours after CreatedDate. DateTime arithmetic is in fractions of a day; `4 / 24` is 4 hours.

---

## Example 15: TODAY vs NOW Time Zone Difference

**Context:** Org default TZ is America/New_York. User runs the flow at 11 PM Pacific (2 AM Eastern next day).

```
// TODAY() returns the user's local date — yesterday from the user's POV.
// {!$Flow.CurrentDate} returns the org's default TZ date — today (Eastern).
TODAY() == {!$Flow.CurrentDate}   // FALSE in this scenario
```

**Why it matters:** A formula that compares stored Dates (which are stored in GMT and rendered per-user-TZ) to `TODAY()` can report a different result than the same comparison done in Apex with `Date.today()` — Apex uses the running user TZ too, but anything that uses the org default TZ (Workflow Field Updates, Process Builder defaults) will diverge.

---

## Example 16: NOW() Returns Org TZ — Be Explicit

```
DATETIMEVALUE(TEXT(NOW()))
```

**Returns:** The current DateTime in the org's default TZ.

**Pitfall:** Comparing this against a user-entered DateTime from a Screen Flow (which is interpreted in the running user's TZ) can be off by hours. Document the TZ contract on every cross-TZ formula.

---

## Example 17: $Flow.CurrentDateTime — Per-Interview Constant

```
{!$Flow.CurrentDateTime}
```

**Behaviour:** The DateTime when the interview started; it is constant for the duration of the interview, even if the interview spans multiple screens or pauses. Use this instead of `NOW()` when you need a single consistent timestamp across an interview.

---

## Example 18: String Concatenation With Date — Wrong

```
"Created on " & {!recordVar.CreatedDate}
```

**Problem:** Renders `"Created on 10/27/2026"` for US users and `"Created on 27/10/2026"` for UK users. Non-deterministic across locales.

---

## Example 19: String Concatenation With Date — Right

```
"Created on " & TEXT(DATEVALUE({!recordVar.CreatedDate}))
```

**Renders:** `"Created on 2026-10-27"` everywhere. ISO format.

---

## Example 20: CASE With Five Branches

```
CASE(
  TEXT({!opportunity.StageName}),
  "Prospecting",   "10",
  "Qualification", "20",
  "Proposal",      "60",
  "Negotiation",   "80",
  "Closed Won",    "100",
  "0"
)
```

**Why it works:** `CASE` short-circuits at the first matching value. Final argument is the default.

**Pitfall:** `CASE` returns Text; if you need Number, wrap with `VALUE()`.

---

## Example 21: Nested IF — Three Levels Deep (Maximum)

```
IF(
  {!opportunity.Amount} > 1000000, "Strategic",
  IF(
    {!opportunity.Amount} > 100000, "Enterprise",
    IF(
      {!opportunity.Amount} > 10000, "Mid-Market",
      "SMB"
    )
  )
)
```

**Why three levels max:** Beyond three nested IFs, switch to `CASE` if branching on a discrete value, or to an Apex Invocable if branching is more complex.

---

## Example 22: Compound Boolean With NULL-Safe Inputs

```
AND(
  NOT(ISBLANK({!opportunity.Amount})),
  {!opportunity.Amount} > 100000,
  ISPICKVAL({!opportunity.Type}, "New Customer"),
  NOT(ISBLANK({!opportunity.AccountId}))
)
```

**Why it works:** Every nullable input is guarded. The `>` comparison only runs after the `ISBLANK` check confirms a value exists.

---

## Example 23: Percent Field Arithmetic

**Context:** `Discount_Percent__c` is a Percent field with value 15 (meaning 15%).

**Wrong (treats 15 as 15.0):**

```
{!opportunity.Amount} * {!opportunity.Discount_Percent__c}
```

**Right:**

```
{!opportunity.Amount} * ({!opportunity.Discount_Percent__c} / 100)
```

**Why it matters:** Percent fields are stored as the displayed number (15), NOT as a decimal (0.15). Always divide by 100 before multiplying.

---

## Example 24: Currency Field With Conversion-Safe Math

```
ROUND({!opportunity.Amount} * (BLANKVALUE({!opportunity.Tax_Rate__c}, 0) / 100), 2)
```

**Why it works:** `ROUND(value, 2)` truncates to 2 decimal places, matching standard currency display. `BLANKVALUE` guards a nullable Tax_Rate__c.

---

## Example 25: Composed Formula Resource — Layer 1

**Formula resource `isStrategicAccount`:**

```
AND(
  {!account.AnnualRevenue} > 100000000,
  ISPICKVAL({!account.Industry}, "Financial Services"),
  {!account.NumberOfEmployees} > 1000
)
```

---

## Example 26: Composed Formula Resource — Layer 2

**Formula resource `isStrategicAndOpen` (references Layer 1):**

```
AND(
  {!isStrategicAccount},
  NOT(ISPICKVAL({!opportunity.StageName}, "Closed Won")),
  NOT(ISPICKVAL({!opportunity.StageName}, "Closed Lost"))
)
```

**Why composition:** Each formula stays focused and reusable. Layer 1 alone serves Account-level decisions; Layer 2 serves Opportunity decisions that ALSO need the Account-strategic check. Each layer counts independently against the 5,000-char limit.

---

## Example 27: 5,000-Character Split — Symptom

A monolithic Formula resource that concatenates 40 fields with conditional formatting starts hitting deploy errors:

```
The formula expression is invalid: Compiled formula is too big to execute (5,001 characters)
```

---

## Example 28: 5,000-Character Split — Refactor

Split into three Formula resources:

- `formattedHeader` — the first 1,500 chars of the original.
- `formattedBody` — the middle 2,000 chars.
- `formattedFooter` — the last 1,500 chars.

Then a parent Formula resource concatenates them:

```
{!formattedHeader} & {!formattedBody} & {!formattedFooter}
```

**Why it works:** The 5,000-char limit applies per Formula resource expression body, not per evaluation. Each child stays under the cap.

---

## Example 29: Decision Condition As Inline Formula

**Context:** A Decision element with a single outcome whose criteria is "Formula Evaluates to True":

```
AND(
  ISPICKVAL({!opportunity.StageName}, "Negotiation"),
  {!opportunity.Amount} > 50000,
  NOT(ISBLANK({!opportunity.CloseDate})),
  ({!opportunity.CloseDate} - TODAY()) < 14
)
```

**Why it works:** Decision-condition formulas evaluate once per element execution. Same language as Formula resources. Same NULL-safety and ISPICKVAL rules apply.

---

## Example 30: REGEX For Email Validation In Screen Component

```
REGEX({!screenInput.EmailText}, "^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
```

**Returns:** TRUE if the input matches a basic email pattern.

**Performance pitfall:** REGEX inside a loop over 200 records is a P0 CPU hot-spot. Cache the result in an Assignment if referenced multiple times per iteration.

---

## Example 31: $Flow.FaultMessage In a Fault-Path Formula

**Context:** Inside a fault path, log the platform-supplied error message:

```
"Flow failed at " & TEXT({!$Flow.CurrentDateTime}) & ": " & {!$Flow.FaultMessage}
```

**Why it works:** `$Flow.FaultMessage` is populated by the runtime in fault paths only. Outside a fault path it is empty.

---

## Example 32: Safe Division With Zero Guard

```
IF(
  OR(ISBLANK({!revenue}), {!cogs} == 0),
  0,
  ({!revenue} - {!cogs}) / {!cogs}
)
```

**Why it works:** Division by zero returns "#Error!" in formulas. The guard returns 0 instead.

---

## Example 33: Concatenating Account Name With Owner Name (NULL-safe)

```
BLANKVALUE({!account.Name}, "(no name)") & " — owned by " & BLANKVALUE({!account.Owner.Name}, "(unassigned)")
```

---

## Example 34: LEN For Length-Based Validation

```
IF(
  LEN({!screenInput.NotesText}) > 255,
  LEFT({!screenInput.NotesText}, 252) & "...",
  {!screenInput.NotesText}
)
```

**Use case:** Truncate long input before writing to a 255-char Text field.

---

## Example 35: Number Formatting With Thousands Separator (manual)

```
// For positive numbers up to 999,999 — manual formatting:
IF(
  {!amount} >= 1000,
  TEXT(FLOOR({!amount} / 1000)) & "," & RIGHT("000" & TEXT(MOD({!amount}, 1000)), 3),
  TEXT({!amount})
)
```

**Why manual:** Formula language has no built-in `FORMAT(number, pattern)`. For complex formatting, push to Apex Invocable.

---

## Example 36: Boolean Coalesce Pattern

```
IF(ISBLANK({!flag}), FALSE, {!flag})
```

**Why:** A nullable Boolean (`Checkbox` field on a record loaded via Get-Records) can be NULL — coalesce to FALSE before using in a Decision.

---

## Anti-Pattern: Computing The Same Formula Six Times Per Loop Iteration

**What practitioners do:** Define a Formula resource `{!isQualifiedLead}` and reference it in every element that needs the answer — Decision, Assignment 1, Assignment 2, Update, Email body, fault-path log message.

**What goes wrong:** In a loop over 1,000 leads, the formula evaluates 6,000 times. CPU time governor (10s sync, 60s async) breaches at scale.

**Correct approach:** First Assignment in the loop body sets a cached Boolean variable from the formula. All other references use the variable.

---

## Anti-Pattern: Using `=` Against A Picklist Label

**What practitioners do:** `{!account.Industry} = "Healthcare"` looks like SQL and evaluates correctly in their dev org.

**What goes wrong:** A translation pack lands in the next sandbox refresh and the formula returns FALSE for users on Spanish locale, silently breaking the branch. P1 in production.

**Correct approach:** `ISPICKVAL({!account.Industry}, "Healthcare")` for single-select; `INCLUDES({!account.Industries__c}, "Healthcare")` for multi-select.

---

## Anti-Pattern: Letting NULL Propagate Into A Decision

**What practitioners do:** Define a Formula resource `{!effectiveAmount}` as `{!opportunity.Amount} - {!opportunity.Discount__c}` and use it in a Decision condition `{!effectiveAmount} > 1000`.

**What goes wrong:** When `Discount__c` is NULL the formula returns NULL, the Decision throws "Comparison value cannot be null", and the flow fails. End-user sees "An unhandled fault has occurred in this flow."

**Correct approach:** Wrap `Discount__c` with `BLANKVALUE({!opportunity.Discount__c}, 0)` inside the Formula resource so the resource always returns a Number.

---

## Anti-Pattern: Letting A Formula Resource Grow To 4,800 Characters Then Adding "Just One More" Branch

**What practitioners do:** A formula has organically grown to 4,800 chars over many edits. The next add takes it to 5,100 and the deploy fails.

**What goes wrong:** Last-minute scramble in front of a release deadline. The split is rushed, behaviour drifts.

**Correct approach:** Compose pre-emptively at ~3,500 chars. Each child Formula resource gets a meaningful name and stays focused.
