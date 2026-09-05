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

## Gotcha 4: The formula-length ceiling this skill used to quote is not in any of the guides

**What happens:** A long formula eventually fails to deploy. The number people quote for the threshold — 5,000 characters, with the error `Compiled formula is too big to execute` — is folklore as far as this corpus is concerned. `grep -n -i "5,000 bytes\|5000 bytes\|Compiled formula"` across `api_meta.txt`, `object_reference.txt`, `apexdev.txt` and `salesforce_app_limits_cheatsheet.txt` returns **zero hits**, and `FlowFormula` (`api_meta.txt` L70596–L70622) documents no length bound at all.

Two different 3,900 figures *are* grounded, and they bound different things — do not merge them:

| Source | Line | Bounds |
|---|---|---|
| `apexdev.txt` | L28143–L28144 — *"bound by the formula field character limit, but not the compile size limit. A formula can contain up to 3,900 characters including spaces, return characters, and comments."* | the **source text** of a formula |
| `object_reference.txt` | L2210 — *"The length of text calculated fields is 3,900 characters or less—anything longer is truncated."* | the **returned string** of a Text formula field |

The `apexdev.txt` sentence also confirms a separate compile-size limit exists without naming its number.

**When it occurs:** Formatted-output formulas concatenating 30+ fields, or `CASE` statements covering 20+ branches.

**How to avoid:** UNVERIFIED (2026-09-05) whether the 3,900 source-character limit binds a Flow `FlowFormula` `<expression>`. Compose at ~3,000 rather than arguing about which ceiling applies. The composition mechanic *is* grounded — the guide's own flow sample composes `<formulas>` by name at `api_meta.txt` L73357–L73362. Deeper than 3 layers, push to Apex Invocable.

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

## Gotcha 9: Percent fields are ALREADY divided by 100 inside a formula

**What happens:** `Discount_Percent__c` shows `15` in the UI for 15%, so authors "correct" for it with `Amount * (Discount_Percent__c / 100)`. In formula context the field already evaluates to `0.15`, so the extra division returns 1/100th of the intended discount — no deploy error, no runtime fault. Salesforce: "percent fields are expressed divided by 100 in formulas (100% is expressed as 1; 50% is expressed as 0.5)."

**When it occurs:** Any Flow Formula resource, formula field, or validation rule that multiplies by or range-checks a Percent field.

**How to avoid:** In formula context multiply directly — `{!opportunity.Amount} * {!opportunity.Discount_Percent__c}` — and compare against fractions (`> 0.5`, never `> 50`).

**Outside a formula, Flow does the opposite, and this is the part that catches people.** Salesforce documents the two paths side by side: *reference* an sObject variable's percent field **into a formula** and it "Divides by 100 — 100 becomes 1"; *pass* a numerical value **into** an sObject variable's percent field and it "Doesn't change — 100 remains 100". So one Flow can hold both conventions at once: a Formula resource reading `Discount_Percent__c` sees `0.15`, while an Assignment writing that same field takes `15`. A Decision comparing the field directly is on the second path — bound it with `> 50`, not `> 0.5`. Mixing the two up is silent in both directions.

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

## Gotcha 26: HYPERLINK *is* a Flow formula function — what varies is whether its output is encoded

**Correction (2026-09-05).** This gotcha previously said `HYPERLINK` is not available in Flow. The Metadata API guide contradicts that directly. `FlowSettings.doesFormulaGenerateHtmlOutput` (`api_meta.txt` L116860–L116863): *"Indicates whether **flow formula functions that generate HTML, such as BR(), IMAGE(), and HYPERLINK()**, include encoded markers (`__BR_ENCODED__`) (true) or not (false). Available in API version 48.0 and later."* The guide names all three as flow formula functions.

**What happens:** The function is available; whether its result renders as a link or as a literal string carrying an encoded marker is an **org setting**, not a property of Flow. The same formula produces a working anchor in one org and `__BR_ENCODED__`-laden text in another.

**When it occurs:** Moving a flow between orgs whose Process Automation Settings differ, or working in an org where the related critical update was never activated (see Gotcha 43 for the `BR()` twin).

**How to avoid:** Check `doesFormulaGenerateHtmlOutput` on both orgs before shipping a formula that builds markup. Confirm the function itself is legal in your org's Flow context with `SELECT Function.Name FROM FormulaFunctionAllowedType WHERE Type = 'FLOW' AND Function.Name = 'HYPERLINK'` (`object_reference.txt` L149310–L149400) rather than trusting either this file or a help article.

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

## Gotcha 32: `||` appears in a documented Salesforce formula sample — so "the dialect has no C-family operators" is too strong

**Correction (2026-09-05).** The Metadata API guide ships a formula `<expression>` that uses `||`: `api_meta.txt` L102276–L102277, inside a `RecommendationStrategy` sample —
`NOT(ISPICKVAL($Record.Account.SLA__c, "Gold") || ISPICKVAL($Record.Account.SLA__c, "Platinum"))`.

**What happens:** The blanket claim that Salesforce formula syntax rejects `&&` and `||` is contradicted by Salesforce's own sample, at least for that expression context. UNVERIFIED (2026-09-05) whether a Flow `FlowFormula` `<expression>` accepts them — the corpus contains no Flow sample using either operator, and no statement either way.

**When it occurs:** Reviewing generated formulas, or porting an expression between contexts (`FormulaFunctionAllowedType.Type` distinguishes `FLOW` from `VALIDATION` from `VISUALFORCE`, `object_reference.txt` L149355–L149365 — the guide models context differences as real).

**How to avoid:** Write `AND(a, b)` / `OR(a, b)` anyway. They are unambiguous, they are what every documented Flow sample uses, and they sidestep a question this corpus cannot settle. But do not *fail a review* on an `||` with "that is invalid syntax" — say "use the function form for consistency" instead, because the strong claim is not defensible.

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

---

## Gotcha 41: An omitted `<dataType>` silently makes the formula a Number formula

**What happens:** `FlowFormula` (`api_meta.txt` L70596–L70612) has three fields, and the guide states the default outright: *"dataType defaults to Number if it isn't defined in a formula."* A `<formulas>` block whose expression returns text or a Boolean, written without `<dataType>`, becomes a Number formula. Nothing in the formula itself fails. The error surfaces at whichever element consumes the resource — a `leftValueReference` on a decision, an `inputAssignments` on a record update — and names *that* element, so the diagnosis starts in the wrong place.

**When it occurs:** Hand-written XML, XML assembled by a generator, and any flow migrated from a tool that did not emit `dataType`. `dataType` is available in API version 31.0 and later, so pre-31 sources have none by construction.

**How to avoid:** Declare `<dataType>` on every `<formulas>` block. Valid values are exactly `Boolean`, `Currency`, `Date`, `DateTime`, `Number`, `String`, `Time` — the Flow Builder UI's "Text" is `String` in the XML, which is its own source of round-trip surprises. `scripts/check_flow_formula_and_expression_patterns.py` rule `FFX01` fails on a missing `dataType`.

---

## Gotcha 42: `scale` is Number/Currency-only, has no documented default, and decides what the record shows

**What happens:** `api_meta.txt` L70618–L70622: *"Scale of the return value, specifically, the number of digits to the right of the decimal point. Available only when the data type is Number or Currency. Corresponds to the Decimal Places field in Flow Builder."* The guide never says what `scale` is when omitted. A Currency formula with no `<scale>` writing into a Currency field with 2 decimal places can produce a stored value that does not match the arithmetic a reviewer does by hand, and the difference is small enough to survive review.

**When it occurs:** Currency and Number formulas that feed `inputAssignments` on a record update, especially where the source fields are themselves scaled differently.

**How to avoid:** Set `<scale>` explicitly on every Number and Currency formula, matched to the target field's decimal places. Do not set it on any other type — the guide scopes it to two. Checker rule `FFX02` warns on a Number/Currency formula with no `scale`.

---

## Gotcha 43: Four org-level settings change what an identical formula does

**What happens:** Two orgs, byte-identical flow XML, different behaviour. The Metadata API guide documents four `FlowSettings` fields that alter formula evaluation without touching the formula:

| Field | Line | What it changes |
|---|---|---|
| `doesFormulaEnforceDataAccess` | L116855–L116858 | *"whether formula resources and formula fields in a flow enforce **record-level** security"* — corresponds to the Enforce Data Access in Flow Formulas critical update, API 48.0+ |
| `doesFormulaGenerateHtmlOutput` | L116860–L116863 | whether HTML-generating flow formula functions (`BR()`, `IMAGE()`, `HYPERLINK()`) include encoded markers (`__BR_ENCODED__`) |
| `enableFlowBREncodedFixEnabled` | L116865–L116868 | whether `BR()` produces a line break or resolves to `_BR_ENCODED_` as a literal value |
| `enableFlowFormulasFixEnabled` | L116910–L116915 | *"whether process and flow formulas return null values when the calculations involve a null record variable or null lookup relationship field. When the value is true, those formulas return null values at run time. When the value is false, those formulas return **unhandled exceptions** at run time."* |

**When it occurs:** Any cross-org deploy. The last one is the sharpest: the same null-lookup formula is a silent null in one org and an unhandled fault in another. That is the difference between a wrong report and a flow error email.

**How to avoid:** Diff the four values between source and target org before deploying a formula-heavy flow. The guide's own `FlowSettings` sample sets three of them (`api_meta.txt` L117067–L117071). Note the first one says **record-level**, not field-level — a common misstatement, and one this package previously made in `references/well-architected.md`.

---

## Gotcha 44: `isViewedAsPlainText` is named backwards from what it does

**What happens:** `api_meta.txt` L72824–L72829: *"If set to true, the flow resource remembers the View as Plain Text setting used for the text template after the flow resource is saved. If set to false, the flow resource uses the View as Rich Text setting. **The default value is false.**"* So the default — and the value in the guide's own sample at L73573–L73577 — is **rich text**. A template body written as plain prose that happens to contain a `<` or an `&` is being handed to a rich-text renderer.

**When it occurs:** Templates that embed generated content, customer-supplied text, or a formula result that itself concatenates user input.

**How to avoid:** Choose deliberately per template. Rich text (`false`) for anything with markup; `true` for anything that must render literally. And note the twin risk in `text`: *"Actual text of the template. Supports merge fields."* — a merge field naming a resource that does not exist is a deploy failure whose message points at the flow, not at the template. Checker rule `FFX04` resolves every merge field in every text template against the flow's own resource names.

---

## Gotcha 45: `filterFormula` and `filters` can both be set on `<start>`, and the guide never says which wins

**What happens:** `FlowStart` documents `filterFormula` (L72390–L72392, API 55.0+), `filterLogic` (L72395–L72400) and `filters` (L72402–L72404) as three adjacent, independent fields. There is **no** exclusivity sentence, no "only one of", no cross-reference between them. A flow carrying both deploys. Which entry condition the runtime honours is not readable from the XML.

**When it occurs:** A flow whose entry condition was migrated from condition rows to a formula, where the rows were never deleted; or a merge of two branches that each edited the `<start>` block.

**How to avoid:** Pick one and delete the other. For contrast, this is what an exclusivity statement looks like when Salesforce writes one — `FlowElementReferenceOrValue` (L70411–L70413): *"Defines a reference to an existing element or a particular value that you specify. **Make sure that you specify only one of the fields.**"* Because no equivalent sentence exists for `filterFormula`/`filters`, checker rule `FFX05` reports the pair as a WARN rather than an ERROR — the defect is unreadability, not a documented violation.

---

## Gotcha 46: `$Record__Prior` is undocumented; the declarative equivalent is not

**What happens:** `grep -n 'Record__Prior' api_meta.txt` returns **zero hits**. `$Record` is grounded (L74307 in the `FlowTestParameter` contract, L74350 in the `FlowTest` sample, L102253 in a `RecommendationStrategy` expression). The prior-value token appears nowhere in the Metadata API guide, so nothing in this corpus states which flow types expose it, whether it is populated on create, or what it holds on delete.

Meanwhile the *behaviour* it is usually reached for — "only run when this changed" — has a fully documented field, in two places: `doesRequireRecordChangedToMeetCriteria` on `FlowStart` (L72315–L72318) and on `FlowRule` (L71321–L71324), both API 50.0 and later: *"If set to true, conditions evaluate to true only if the record didn't meet the required conditions before the triggering update but now meets the conditions after the update."*

**When it occurs:** Writing an entry condition as `TEXT($Record.Status__c) <> TEXT($Record__Prior.Status__c)` when the requirement was "fire when the record newly qualifies".

**How to avoid:** Reach for `doesRequireRecordChangedToMeetCriteria` first — it is documented, it is a checkbox rather than an expression, and `flow/flow-record-save-order-interaction` owns its interaction with the save order. Use `$Record__Prior` only when you genuinely need the old *value* rather than a change in qualification, and record that you are using an undocumented token.

---

## Gotcha 47: Compound fields reject `BLANKVALUE`, `CASE`, `NULLVALUE`, `PRIORVALUE` and every comparison operator

**What happens:** `object_reference.txt` L2936–L2937: *"The only formula functions that you can use with compound fields are `ISBLANK`, `ISCHANGED`, and `ISNULL`. You can't use `BLANKVALUE`, `CASE`, `NULLVALUE`, `PRIORVALUE`, or the equality and comparison operators with compound fields."* Compound fields are the address and geolocation fields (`BillingAddress`, `MailingAddress`, a `Location__c` geolocation) plus `Name` on Person Accounts.

This collides head-on with the rest of this skill: the default advice everywhere else is "wrap every nullable operand in `BLANKVALUE`". On a compound field that advice is invalid, and the only null test available is `ISBLANK` or `ISNULL`.

**When it occurs:** A formula that guards `{!$Record.BillingAddress}` the way it guards every other nullable field.

**How to avoid:** Operate on the compound field's *components* (`BillingStreet`, `BillingCity`, `BillingPostalCode`), which are ordinary fields with the full function set. Reserve `ISBLANK` on the compound field itself for a presence test. Checker rule `FFX03` cannot detect this — it does not know field types — so it is a review item, not a mechanical one.

---

## Gotcha 48: `ISNULL` and `ISBLANK` both exist, and this corpus documents neither's semantics

**What happens:** `object_reference.txt` L2936 names `ISBLANK`, `ISCHANGED` and `ISNULL` as three distinct formula functions. That is the *only* place in the entire corpus where `ISNULL` appears. Nothing in `api_meta.txt`, `object_reference.txt`, `apexdev.txt` or `apexrefguide.txt` states how either behaves on a Text field, a Number field, or a picklist — the guidance everyone repeats ("`ISBLANK` treats empty string as blank for Text; `ISNULL` is the legacy spelling that only handles Number and Date") comes entirely from the Formula Operators and Functions help article.

**When it occurs:** Reviewing a formula that mixes both, or porting one from a validation rule.

**How to avoid:** UNVERIFIED (2026-09-05): every claim in this package about `ISBLANK` vs `ISNULL` vs `BLANKVALUE` vs `NULLVALUE` behaviour per data type — including Gotchas 16, 17 and 39 above. They are the working semantics practitioners rely on and they are almost certainly right; they are simply not confirmable from these guides. What you *can* settle from the org is which of the four is legal in a Flow context at all: `SELECT Function.Name, Function.ExampleString FROM FormulaFunctionAllowedType WHERE Type = 'FLOW' AND Function.Name IN ('ISBLANK','ISNULL','BLANKVALUE','NULLVALUE')` (`object_reference.txt` L149310–L149400). `ExampleString` (L149244–L149247) is documented as *"Describes the function and what arguments you can use with it"* — the closest thing to the help article that lives inside your own org.
