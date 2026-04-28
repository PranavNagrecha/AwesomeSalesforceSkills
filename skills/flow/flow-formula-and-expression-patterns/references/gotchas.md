# Gotchas — Flow Formula And Expression Patterns

Non-obvious Salesforce platform behaviors in Flow Formula authoring that cause real production problems. Each gotcha includes detection, root cause, and fix.

---

## Gotcha 1: NULL propagates through arithmetic, comparison, and logical operators

**What happens:** `NULL + 1` evaluates to `NULL`, not `1`. `NULL && TRUE` evaluates to `NULL`, not `FALSE`. `NULL > 0` evaluates to `NULL`. The NULL propagates downstream — into Assignments (writing NULL back to records), into Decisions (throwing "Comparison value cannot be null"), into Update Records (overwriting populated fields with NULL).

**When it occurs:** Any time a Formula resource consumes a non-required field, the output of a Get Records that may be empty, or an optional Screen input.

**How to avoid:** Wrap every nullable input with `BLANKVALUE(input, defaultValue)` for non-Boolean types, and `IF(ISBLANK(input), FALSE, input)` for Booleans, BEFORE composing the rest of the expression.

---

## Gotcha 2: ISPICKVAL is required for picklist comparison; `=` is a silent locale bug

**What happens:** `{!opportunity.StageName} = "Closed Won"` returns TRUE in an English-only org and FALSE the moment a translation pack is enabled — silently. No deploy error, no runtime warning.

**When it occurs:** Most acutely after a translation pack is added or a picklist label is edited (the API name didn't change but the label did, breaking any `=` comparison against a literal).

**How to avoid:** Always use `ISPICKVAL(picklistField, "ApiNameValue")` for single-select and `INCLUDES(multiPicklistField, "ApiNameValue")` for multi-select. The literal must be the API name, not the label.

---

## Gotcha 3: Lazy re-evaluation — every `{!FormulaResourceName}` reference recomputes the formula

**What happens:** Flow does not cache Formula resource results. A Formula resource referenced 6 times inside a loop body that iterates 200 records evaluates 1,200 times per flow run. CPU-time governors (10s sync, 60s async) breach at scale.

**When it occurs:** Whenever a non-trivial Formula resource (concatenation, REGEX, nested IF, CASE, date math) is referenced more than 2-3 times, especially inside Loop bodies or Decision conditions inside loops.

**How to avoid:** Add an Assignment at the top of the loop body that materialises the formula result into a typed variable. Switch all downstream references to read the variable. Variable reads are not lazy.

---

## Gotcha 4: 5,000-character limit per Formula resource expression

**What happens:** Deploy fails with `The formula expression is invalid: Compiled formula is too big to execute (5,001 characters)`. No partial-deploy fallback — the entire flow rejects.

**When it occurs:** When a single formula has organically grown over many edits — typically formatted-output formulas concatenating 30+ fields with conditional formatting, or large CASE statements covering 20+ branches.

**How to avoid:** Compose into multiple Formula resources at ~3,500 chars. Each child counts independently against the 5,000 cap. Going deeper than 3 layers of composition is a smell — push to Apex Invocable.

---

## Gotcha 5: TODAY() and NOW() use different time zones

**What happens:** `TODAY()` returns the running user's local date in the user's TZ. `NOW()` returns the org's default TZ. In a multi-TZ org, the same flow run for a user in Pacific and a user in Eastern can return different `TODAY()` values when the run happens near midnight.

**When it occurs:** Cross-TZ teams. A flow that compares `TODAY()` to a stored Date field (rendered per-user-TZ) can be off-by-one for users on the far side of the org's default TZ.

**How to avoid:** Document the TZ contract on every cross-TZ formula. If you need a deterministic org-default-TZ date, use `{!$Flow.CurrentDate}`. If you need a per-interview constant DateTime, use `{!$Flow.CurrentDateTime}` instead of `NOW()`.

---

## Gotcha 6: TEXT(picklistField) returns the API name, not the label

**What happens:** A Display Text component shows "PROSPECTING" instead of "Prospecting", surprising end-users.

**When it occurs:** Whenever a formula renders a picklist value in user-facing output without an explicit label-mapping step.

**How to avoid:** Either build a `CASE(TEXT(picklist), "API1", "Label 1", ...)` mapping, or store labels in a Custom Metadata Type and Get-Records into it. Do not assume `TEXT(picklist)` returns user-facing text.

---

## Gotcha 7: Implicit Date-to-Text concatenation uses running-user locale

**What happens:** `"Created on " & {!record.CreatedDate}` renders `"Created on 10/27/2026"` for US users and `"Created on 27/10/2026"` for UK users. Same flow, same data, different output.

**When it occurs:** Multi-locale orgs. Outputs that need to be deterministic (audit log lines, integration payloads, email-template headers).

**How to avoid:** Wrap with `TEXT()`. `TEXT(DATEVALUE({!record.CreatedDate}))` returns the ISO `YYYY-MM-DD` form regardless of locale.

---

## Gotcha 8: VALUE() throws on non-numeric input — no graceful fallback

**What happens:** `VALUE({!screenInput.QuantityText})` with input `"abc"` throws `Argument 1 cannot be of type Text` at runtime, halting the flow.

**When it occurs:** Screen Flow inputs from Text components that are not constrained to numerics; bridges from external systems that send Text where Numbers are expected.

**How to avoid:** Wrap with `IF(ISNUMBER(input), VALUE(input), 0)` — `ISNUMBER` returns TRUE if the input parses cleanly. Or use a Number Screen component instead of Text.

---

## Gotcha 9: Percent fields are stored as the displayed number, not as a decimal

**What happens:** `Discount_Percent__c = 15` (meaning 15%). Multiplying `Amount * Discount_Percent__c` returns `Amount * 15`, not `Amount * 0.15`.

**When it occurs:** Any formula that does arithmetic on a Percent field.

**How to avoid:** Always divide Percent fields by 100 before multiplying: `Amount * (Discount_Percent__c / 100)`.

---

## Gotcha 10: DATETIMEVALUE requires GMT input, not local time

**What happens:** `DATETIMEVALUE("2026-04-27 14:00:00")` returns 14:00 GMT, NOT 14:00 in the user's local TZ.

**When it occurs:** Flows that take user-entered date+time strings and convert them. The user expects "2 PM Pacific" but gets "2 PM GMT" stored, off by 7-8 hours.

**How to avoid:** Use the DateTime Screen component, which returns a properly-zoned DateTime, or do explicit TZ math: `DATETIMEVALUE("2026-04-27 14:00:00") + (8/24)` to shift from PT to GMT.

---

## Gotcha 11: Division by zero returns #Error!, not 0 or NULL

**What happens:** `{!revenue} / {!cogs}` with `cogs = 0` returns `#Error!`. If used downstream the entire formula chain returns `#Error!` and any Decision condition throws.

**When it occurs:** Margin and ratio calculations where the denominator can legitimately be zero.

**How to avoid:** Always guard with `IF(OR(ISBLANK(denom), denom == 0), 0, num / denom)`.

---

## Gotcha 12: REGEX is CPU-expensive inside loops

**What happens:** A REGEX call costs roughly 10-50× more CPU than a simple field comparison. Inside a 200-iteration loop with 3 references per iteration, REGEX dominates the flow's CPU budget.

**When it occurs:** Email validation, phone validation, complex pattern matching inside a loop body.

**How to avoid:** Cache the REGEX result in an Assignment per iteration. If the REGEX is constant per iteration's input, evaluate once outside the loop.

---

## Gotcha 13: Decision condition formula re-evaluates on each Decision execution

**What happens:** A Decision element inside a loop that references 3 Formula resources executes those formulas on every iteration. 200 iterations × 3 formulas = 600 evaluations.

**When it occurs:** Loop body with a Decision element that branches on multiple Formula resources.

**How to avoid:** Pre-compute the formula results into cached variables in an Assignment at the top of the loop body. The Decision then reads variables, not formulas.

---

## Gotcha 14: $Flow.FaultMessage is empty outside a fault path

**What happens:** A formula that references `{!$Flow.FaultMessage}` in the main path renders empty string.

**When it occurs:** Logging formulas mistakenly placed in the happy path instead of a fault path.

**How to avoid:** Only reference `$Flow.FaultMessage` from elements connected to a fault path. Confirm with Flow Debug that the path under test actually traversed the fault connector.

---

## Gotcha 15: Boolean checkbox fields can be NULL, not just TRUE/FALSE

**What happens:** A Checkbox field loaded via Get Records on a record that was created before the field existed (or imported via a tool that set it to NULL) returns NULL, not FALSE. `IF({!flag}, "Yes", "No")` with NULL flag returns "No" — but `AND({!flag}, TRUE)` returns NULL, breaking downstream logic.

**When it occurs:** Long-lived orgs with legacy data, or fields recently added with no default.

**How to avoid:** Coalesce to FALSE before use: `IF(ISBLANK({!flag}), FALSE, {!flag})`.

---

## Gotcha 16: ISBLANK on a Number returns TRUE only for NULL, not for zero

**What happens:** `ISBLANK({!quantity})` with `quantity = 0` returns FALSE, not TRUE. Users who think "blank" includes "zero" are surprised.

**When it occurs:** Zero-as-default-value validation logic.

**How to avoid:** Use `OR(ISBLANK({!quantity}), {!quantity} == 0)` if zero should also count as "no value".

---

## Gotcha 17: Text fields treat empty string and NULL as interchangeable for ISBLANK

**What happens:** `ISBLANK("")` returns TRUE. `ISBLANK(NULL)` returns TRUE. This is the OPPOSITE of Number/Date/Boolean behaviour.

**When it occurs:** Asymmetric NULL-checking across types in the same formula.

**How to avoid:** Just remember the rule: Text → empty and null both blank. All other types → only null is blank.

---

## Gotcha 18: CASE returns Text — not the type of the matched value

**What happens:** `CASE(TEXT(stage), "Won", 100, "Lost", 0, 50)` returns the numeric values as Text. Using the result in arithmetic requires `VALUE()`.

**When it occurs:** When CASE return values look numeric and the developer assumes the formula return type is Number.

**How to avoid:** Set the Formula resource Data Type to Text and explicitly `VALUE()` at the call site, or restructure with nested IF whose branches return Number.

---

## Gotcha 19: Flow formula language does NOT include PRIORVALUE or ISCHANGED

**What happens:** Authors copy a Validation Rule formula like `ISCHANGED(StageName)` into a Flow Formula resource and get a deploy error.

**When it occurs:** Migration from Workflow Rules / Validation Rules / Process Builder to Flow.

**How to avoid:** In a record-triggered flow, compare `{!$Record.StageName}` (new) to `{!$Record__Prior.StageName}` (prior). For non-record-triggered flows, the prior-value concept doesn't exist — read the prior value with a Get Records or via a passed-in input parameter.

---

## Gotcha 20: Multi-select picklist string format is semicolon-delimited, no spaces

**What happens:** `{!account.Industries__c}` with selections "Healthcare" and "Manufacturing" returns the literal string `"Healthcare;Manufacturing"`. Comparing to `"Healthcare; Manufacturing"` fails.

**When it occurs:** Authors hand-build comparison literals with spaces after semicolons.

**How to avoid:** Always use `INCLUDES()` instead of `=`. INCLUDES handles the delimiter parsing internally.

---

## Gotcha 21: $Flow.CurrentDate vs TODAY() — org TZ vs running-user TZ

**What happens:** `{!$Flow.CurrentDate}` returns the date in the org's default TZ. `TODAY()` returns the date in the running user's TZ. They diverge near midnight for users in non-default TZs.

**When it occurs:** Multi-TZ orgs running flows for users worldwide.

**How to avoid:** Pick deliberately. Document the choice. Default to `TODAY()` when "today from the user's perspective" is intended; default to `{!$Flow.CurrentDate}` when "today from the org's perspective" is intended (matches Workflow / Process Builder behaviour).

---

## Gotcha 22: Concatenating an empty string with another value returns the value, not NULL

**What happens:** `"" & {!someText}` returns the value of `someText`, even if `someText` is NULL — Salesforce converts NULL to empty string in concatenation context.

**When it occurs:** Defensive concatenation patterns where authors expect NULL propagation.

**How to avoid:** Do not rely on this for NULL detection. Use `ISBLANK()` explicitly.

---

## Gotcha 23: Currency conversion — formula uses corporate currency, not record currency

**What happens:** In multi-currency orgs, a formula like `Amount > 100000` evaluates `Amount` in the corporate currency, not the record's currency. The displayed value matches the record currency but the comparison is on corporate.

**When it occurs:** Multi-currency orgs running cross-currency comparisons.

**How to avoid:** Be aware that all formula arithmetic on Currency fields normalises to corporate currency. Document the behaviour at every cross-currency comparison.

---

## Gotcha 24: ROUND uses banker's rounding, not standard rounding

**What happens:** `ROUND(2.5, 0)` returns `3` (away from zero, not banker's). Documented Salesforce behaviour but surprising for engineers expecting Java/Python banker's rounding.

**When it occurs:** Financial calculations where rounding behaviour is regulated.

**How to avoid:** Read the ROUND docs once. Use `MROUND` or explicit `IF(...)` if you need a different rounding mode.

---

## Gotcha 25: Date arithmetic produces Number, DateTime arithmetic produces fractional days

**What happens:** `Date2 - Date1` returns a Number of days. `DateTime2 - DateTime1` returns a Number of days as a fraction (e.g. `0.5` for 12 hours).

**When it occurs:** Authors expect "minutes between two DateTimes" — the formula returns days, must be multiplied by 1440.

**How to avoid:** `(DateTime2 - DateTime1) * 1440` for minutes; `* 24` for hours; `* 86400` for seconds.

---

## Gotcha 26: HYPERLINK is not available in Flow formulas

**What happens:** `HYPERLINK(url, text)` works in formula fields (because the rendering layer interprets the result as HTML) but is not useful in Flow Formula resources because Flow resources are always rendered as plain text in non-HTML contexts.

**When it occurs:** Authors copy formula-field hyperlink patterns into Flow.

**How to avoid:** For Display Text components, write the HTML `<a>` tag directly using rich text. For email actions, build the HTML in the email body, not in a Formula resource.

---

## Gotcha 27: Long Text Area fields can exceed formula string handling limits

**What happens:** `LEN({!longText})` on a Long Text Area returning > 32,768 chars hits formula string-handling limits and throws.

**When it occurs:** Logging formulas that try to LEN or substring large text fields.

**How to avoid:** Trim with `LEFT()` to a safe size first, then operate on the trimmed value.

---

## Gotcha 28: Cross-record-trigger formula reads of related fields require Get Records first

**What happens:** A Formula resource referencing `{!$Record.Account.Owner.Email}` works in a record-triggered flow because the platform pre-loads the parent. In a non-triggered flow, the same dotted path returns NULL because the parent is not loaded.

**When it occurs:** Reusing a formula across triggered and non-triggered flow contexts.

**How to avoid:** In non-triggered flows, do an explicit Get Records on the parent and reference the loaded variable, not a dotted path.

---

## Gotcha 29: Formula resources inside subflows do not inherit caller's variables

**What happens:** A Formula resource defined in subflow A and referenced in subflow B by name is a deploy error.

**When it occurs:** Authors expect formula resources to be globally addressable.

**How to avoid:** Each subflow has its own formula scope. Pass the input value via a subflow input variable; redefine the formula inside the subflow if reuse is needed.

---

## Gotcha 30: TIMENOW() does not exist; use NOW() and extract time

**What happens:** Authors write `TIMENOW()` expecting a Time-typed value; Flow rejects with "function does not exist".

**When it occurs:** Authors familiar with Excel formulas.

**How to avoid:** Flow has `NOW()` (DateTime), `TODAY()` (Date), `TIMEVALUE(textOrDateTime)` (Time). No bare `TIMENOW()`.

---

## Gotcha 31: Decimal precision matches the formula resource's Decimal Places setting

**What happens:** A Number Formula resource configured with 0 decimal places truncates `1.5` to `1`, not `2` (truncation, not rounding).

**When it occurs:** Decimal Places set conservatively to 0 for "whole numbers only" fields.

**How to avoid:** Set Decimal Places to match the precision needed. If you want rounding, do it explicitly with `ROUND()` and let the storage format match.

---

## Gotcha 32: `&&` and `||` are NOT supported in Salesforce formula syntax

**What happens:** `{!a} && {!b}` produces a parse error.

**When it occurs:** Authors with Java/JavaScript background.

**How to avoid:** Use `AND(a, b)` and `OR(a, b)` functions. Salesforce formula language predates the C-family operators in this dialect.

---

## Gotcha 33: NOT requires parentheses around its argument

**What happens:** `NOT ISPICKVAL(stage, "Won")` parses but is fragile; `NOT(ISPICKVAL(stage, "Won"))` is the documented form.

**When it occurs:** Defensive style.

**How to avoid:** Always parenthesise NOT's argument.

---

## Gotcha 34: $Flow.FaultMessage truncates at 255 characters

**What happens:** Long fault messages are clipped. Authors logging fault messages to a field that can hold 32K of text only see the first 255.

**When it occurs:** Centralised error logging where the full fault message matters.

**How to avoid:** Concatenate `$Flow.FaultMessage` with `$Flow.CurrentDateTime` and `$Flow.CurrentRecord` into a single log line; if you need richer fault context, capture inside an Apex Invocable that has access to full exception chain.

---

## Gotcha 35: TEXT(DateTime) returns GMT, not user TZ

**What happens:** `TEXT(NOW())` for a Pacific user at noon Pacific returns `"2026-04-27 19:00:00Z"`, not `"2026-04-27 12:00:00"`.

**When it occurs:** Logging or display use cases where the user expects local time.

**How to avoid:** Build the local-time string explicitly: subtract the TZ offset before TEXT, or use a Display Text component with `{!datetime}` (which formats per running user TZ) instead of TEXT.

---

## Gotcha 36: Concatenation with NULL Number returns the NULL string "null"

**What happens:** `"Total: " & {!nullableNumber}` returns `"Total: "` for some platform versions and `"Total: null"` for others. Inconsistent.

**When it occurs:** Concatenating Number/Currency/Percent without NULL-guarding.

**How to avoid:** `"Total: " & TEXT(BLANKVALUE({!nullableNumber}, 0))` — explicit cast and default.

---

## Gotcha 37: Formula resource type cannot be changed after creation

**What happens:** A Formula resource created as Number cannot be changed to Text without deleting and recreating. Re-creation breaks all existing references.

**When it occurs:** Late-stage refactor when the team realises the wrong type was chosen.

**How to avoid:** Decide return type up front. If a change is needed, deprecate the old resource and add a new one with a new name; migrate references in a planned batch.

---

## Gotcha 38: Operator precedence — `*` and `/` bind tighter than `+` and `-`, but be explicit

**What happens:** `1 + 2 * 3` returns `7`, not `9`. Standard precedence — but easy to misread when the formula spans multiple lines.

**When it occurs:** Multi-term arithmetic formulas.

**How to avoid:** Parenthesise every grouping. Lint your own formulas: if a reviewer has to think about precedence, add parens.

---

## Gotcha 39: NULLVALUE is the legacy spelling — BLANKVALUE is current

**What happens:** Both work in Salesforce formulas. NULLVALUE only works on Numbers and Dates; BLANKVALUE works on Text too.

**When it occurs:** Authors copying old patterns from training materials.

**How to avoke:** Standardise on BLANKVALUE for everything.

---

## Gotcha 40: Reactive screen-component formulas re-run on every dependent input change

**What happens:** A Display Text component bound to `{!totalFormula}` re-evaluates the formula every time any referenced screen input changes — typing a single character in a related Number field triggers a re-evaluation.

**When it occurs:** Reactive screens (Winter '24+) with dense formula bindings.

**How to avoid:** Keep reactive formulas trivial. For expensive computations, defer to a server-side action triggered on next/save instead of binding to a reactive formula.
