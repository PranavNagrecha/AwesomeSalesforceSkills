# LLM Anti-Patterns — Flow Formula And Expression Patterns

Common mistakes AI coding assistants make when generating or advising on Flow formula expressions. These patterns let the consuming agent self-check its own output before returning it.

---

## Anti-Pattern 1: Using `=` for picklist comparison

**What the LLM generates:**

```
{!opportunity.StageName} = "Closed Won"
```

**Why it happens:** SQL/Python/JavaScript training bias — `=` is the natural equality operator, and many code samples in training data treat picklists as strings. Salesforce documentation is explicit that this is wrong but the wrong pattern is more common in scraped Q&A.

**Correct pattern:**

```
ISPICKVAL({!opportunity.StageName}, "Closed Won")
```

**Detection hint:** grep the formula body for `= "` or `== "` against any field whose name ends in a picklist convention or whose schema is known to be a picklist. Any direct equality comparison against a literal string for a picklist field is a bug.

---

## Anti-Pattern 2: Not wrapping nullable inputs in BLANKVALUE

**What the LLM generates:**

```
{!opportunity.Amount} - {!opportunity.Discount__c}
```

**Why it happens:** LLMs treat `Discount__c` as if it were a non-null Number (Java/Python default). Salesforce formula NULL semantics are SQL-like, so any null input produces a null output that propagates to downstream Decisions and Updates as a P1 bug.

**Correct pattern:**

```
{!opportunity.Amount} - BLANKVALUE({!opportunity.Discount__c}, 0)
```

**Detection hint:** scan for arithmetic operators (`+`, `-`, `*`, `/`) and Boolean operators (`AND(`, `OR(`) where any operand references a custom field that is not marked Required in metadata. Any unwrapped nullable input is a candidate for `BLANKVALUE`.

---

## Anti-Pattern 3: Generating a monster formula in one resource

**What the LLM generates:** A single Formula resource with 40+ concatenations and conditional formatting branches, thousands of characters long.

**Why it happens:** LLMs prefer to produce the entire solution in a single artifact when asked. Length is not a constraint a fluent generator feels, and the ceiling it would otherwise respect is not documented anywhere (Anti-Pattern 35).

**Correct pattern:** Compose into multiple Formula resources, each focused and well under 3,000 chars:

```
// formattedHeader (~1,500 chars)
// formattedBody   (~2,000 chars)
// formattedFooter (~1,500 chars)
// composedOutput = {!formattedHeader} & {!formattedBody} & {!formattedFooter}
```

**Detection hint:** count the characters in any generated Formula resource expression body. If `len(expression) > 4500`, refactor before returning to the user.

---

## Anti-Pattern 4: Reusing the same Formula resource in 10 loop-body element references

**What the LLM generates:** A loop body where the Decision condition, three Assignments, an Update, and an email body all reference `{!isHighValueOpportunity}`.

**Why it happens:** LLMs apply DRY reflexively — "use the formula resource everywhere it's needed" is a default heuristic. The lazy-re-evaluation cost is a Salesforce-specific platform behaviour that doesn't exist in most other declarative platforms LLMs are trained on.

**Correct pattern:** Cache the formula in an Assignment at the top of the loop body, then reference the variable everywhere downstream:

```
// First Assignment in loop body:
//   cachedHighValue (Boolean) = {!isHighValueOpportunity}
// All six downstream references use {!cachedHighValue}.
```

**Detection hint:** count `{!FormulaResourceName}` occurrences inside each Loop element. If `count > 2` and the formula expression body has any function call (not a single field reference), recommend caching.

---

## Anti-Pattern 5: Ignoring the TZ difference between TODAY() and NOW()

**What the LLM generates:** A formula like `IF(NOW() > {!record.SomeDeadlineDateTime}, "OVERDUE", "ON TRACK")` without commenting on the org-default-TZ semantic of `NOW()`, then in another flow uses `TODAY()` for "today" without commenting on the running-user-TZ semantic.

**Why it happens:** LLM training data treats date/time functions as universal — `now()` and `today()` semantics in Python or JavaScript are similar enough across runtimes. Salesforce's `NOW()` (org default TZ) vs `TODAY()` (running user TZ) split is unique and not consistently documented in training data.

**Correct pattern:** Pick the right function deliberately and document the choice:

```
// Comparing to a stored DateTime — use $Flow.CurrentDateTime for per-interview consistency:
{!$Flow.CurrentDateTime} > {!record.SomeDeadlineDateTime}

// Comparing "is this today from the user's perspective?" — TODAY() is right:
{!record.CloseDate} = TODAY()

// Comparing "is this today in org-default time?" — $Flow.CurrentDate is right:
{!record.CloseDate} = {!$Flow.CurrentDate}
```

**Detection hint:** flag every use of `NOW()` and `TODAY()` and ask the agent to confirm in the response whether the running-user TZ or the org-default TZ is intended.

---

## Anti-Pattern 6: Using `&&` and `||` instead of AND() / OR()

**What the LLM generates:**

```
{!flag1} && {!flag2} || {!flag3}
```

**Why it happens:** C-family operator bias. The vast majority of code in training corpora uses `&&` / `||`. Salesforce formula syntax does not.

**Correct pattern:**

```
OR(AND({!flag1}, {!flag2}), {!flag3})
```

**Detection hint:** grep the formula body for `&&` or `||`. Any occurrence is a parse error.

---

## Anti-Pattern 7: Dividing a Percent field by 100 inside a formula

**What the LLM generates:**

```
{!opportunity.Amount} * ({!opportunity.Discount_Percent__c} / 100)
```

**Why it happens:** The UI renders `15` for 15%, so the model reasons the stored value must be `15` and helpfully scales it. In formula context the platform has already applied that division, so the extra `/ 100` returns 1/100th of the intended amount — and nothing, deploy or runtime, flags it.

**Correct pattern:**

```
{!opportunity.Amount} * {!opportunity.Discount_Percent__c}
```

**Detection hint:** grep the formula body for `/ 100`; if the numerator is a Percent-type field, the division is a bug, and so is the comparison form `{!pct} > 50` (should be `> 0.5`). Do not go by field name — a Number field called `Tax_Rate__c` holding `7.5` genuinely does need the `/ 100`.

---

## Anti-Pattern 8: Using PRIORVALUE or ISCHANGED in a Flow Formula

**What the LLM generates:**

```
ISCHANGED({!record.StageName})
```

**Why it happens:** These functions exist in Validation Rules and the LLM has seen them in formula training data without distinguishing the runtime context.

**Correct pattern (record-triggered flow):**

```
{!$Record.StageName} != {!$Record__Prior.StageName}
```

**Correct pattern (other flow types):** `PRIORVALUE` / `ISCHANGED` semantics do not exist outside record-triggered context — load prior value via Get Records or accept it as a subflow input.

**Detection hint:** grep for `PRIORVALUE(` or `ISCHANGED(`. Any occurrence in a Flow Formula resource is wrong.

---

## Anti-Pattern 9: Implicit Date-to-Text concatenation in a multi-locale org

**What the LLM generates:**

```
"Created on " & {!record.CreatedDate}
```

**Why it happens:** String concatenation with a Date "just works" in most languages. Salesforce's locale-dependent rendering of the resulting string is non-obvious until a multi-locale user files a bug.

**Correct pattern:**

```
"Created on " & TEXT(DATEVALUE({!record.CreatedDate}))
```

**Detection hint:** scan for `&` operands that reference a Date or DateTime field without an enclosing `TEXT()` call.

---

## Anti-Pattern 10: Using = against a multi-select picklist

**What the LLM generates:**

```
{!account.Industries__c} = "Healthcare"
```

**Why it happens:** Multi-select picklists look like single-select to LLMs that haven't internalised the semicolon-delimited storage format.

**Correct pattern:**

```
INCLUDES({!account.Industries__c}, "Healthcare")
```

**Detection hint:** grep for `= "` against any field whose Salesforce type is MultiselectPicklist. INCLUDES is the only correct primitive.

---

## Anti-Pattern 11: VALUE() without an ISNUMBER guard

**What the LLM generates:**

```
VALUE({!screenInput.QuantityText})
```

**Why it happens:** LLMs assume parsing succeeds; in real screen flows the input may be empty or non-numeric.

**Correct pattern:**

```
IF(ISNUMBER({!screenInput.QuantityText}), VALUE({!screenInput.QuantityText}), 0)
```

**Detection hint:** any unguarded `VALUE(` against a Screen-input or external-source Text variable is a runtime exception waiting to happen.

---

## Anti-Pattern 12: Division without a zero-or-null guard

**What the LLM generates:**

```
{!revenue} / {!cogs}
```

**Why it happens:** Division by zero is a runtime decision in most languages. In Salesforce formulas it returns `#Error!` which propagates as a parse-style failure.

**Correct pattern:**

```
IF(OR(ISBLANK({!cogs}), {!cogs} == 0), 0, {!revenue} / {!cogs})
```

**Detection hint:** every `/` should be inside an `IF` that guards both NULL and zero denominators.

---

## Anti-Pattern 13: Treating empty string as distinct from NULL for Text fields

**What the LLM generates:**

```
IF({!textField} == NULL, "no value", {!textField})
```

**Why it happens:** LLM treats Salesforce as Java-typed.

**Correct pattern:**

```
BLANKVALUE({!textField}, "no value")
```

**Detection hint:** any `== NULL` or `!= NULL` comparison should be replaced with `ISBLANK` or `BLANKVALUE`.

---

## Anti-Pattern 14: Recommending a 6-layer composed formula chain

**What the LLM generates:** Six Formula resources composing into a final answer, each referencing the next.

**Why it happens:** LLMs decompose recursively. Each layer is short enough to pass any length check, and the chain becomes unreadable at depth.

**Correct pattern:** Cap composition at 3 layers. Beyond that, switch to an Apex Invocable Action with the same input/output contract.

**Detection hint:** trace the dependency graph of any Formula resource. If depth > 3, recommend Apex.

---

## Anti-Pattern 15: Using TEXT(picklist) and assuming the result is the user-facing label

**What the LLM generates:**

```
"Stage: " & TEXT({!opportunity.StageName})
```

…then surprised when the rendered output shows API names like `"Closed_Won"` instead of `"Closed Won"`.

**Why it happens:** LLMs conflate "convert to text" with "convert to displayable text".

**Correct pattern:** Map API names to labels explicitly:

```
"Stage: " & CASE(
  TEXT({!opportunity.StageName}),
  "Prospecting", "Prospecting",
  "Closed_Won",  "Closed Won",
  TEXT({!opportunity.StageName})
)
```

Or use a Custom Metadata mapping table loaded via Get Records.

**Detection hint:** any `TEXT(` against a known picklist field that feeds user-facing output should be flagged for label mapping.

---

## Anti-Pattern 16: Asserting that HYPERLINK() is unavailable in Flow

**Corrected 2026-09-05 — the previous version of this entry was itself the anti-pattern.**

**What the LLM generates:** "`HYPERLINK()` doesn't work in Flow formulas — build the `<a>` tag by hand."

**Why it happens:** It is a widely repeated claim, and an assistant that has internalised "Flow formulas are a restricted subset" generalises from that.

**The guide says otherwise.** `api_meta.txt` L116860–L116863, `FlowSettings.doesFormulaGenerateHtmlOutput`: *"whether **flow formula functions that generate HTML, such as BR(), IMAGE(), and HYPERLINK()**, include encoded markers (`__BR_ENCODED__`)."* All three are named as flow formula functions. What varies is output encoding, and it varies by **org setting**, not by context.

**Correct pattern:** Say what actually varies — "`HYPERLINK()` is a Flow formula function; whether its output renders as a link depends on `doesFormulaGenerateHtmlOutput` and `enableFlowBREncodedFixEnabled` in the target org's Process Automation Settings" — and offer the query that settles it: `SELECT Function.Name FROM FormulaFunctionAllowedType WHERE Type = 'FLOW' AND Function.Name = 'HYPERLINK'`.

**Detection hint:** any confident "function X is not available in Flow" with no `FormulaFunctionAllowedType` query behind it. Availability is a per-org, per-context fact with a queryable answer; do not assert it from memory.

---

## Anti-Pattern 17: Generating a Flow formula that uses Apex method syntax

**What the LLM generates:**

```
{!textVar}.toUpperCase()
```

or

```
{!record.fields.Name.value}
```

**Why it happens:** Cross-context bleed from Apex / Java / JavaScript training data.

**Correct pattern:** `UPPER({!textVar})`. Field access is `{!record.Name}`, not `.fields.Name.value`.

**Detection hint:** any `.method()` syntax inside a Flow formula is wrong; only function-call syntax (`UPPER(...)`) is supported.

---

## Anti-Pattern 18: Forgetting that ISBLANK on a Number returns FALSE for zero

**What the LLM generates:**

```
IF(ISBLANK({!quantity}), "missing", "present")
```

…and is surprised when `quantity = 0` returns `"present"`.

**Why it happens:** LLM models "blank" loosely as "no meaningful value", which would include zero in many contexts.

**Correct pattern:**

```
IF(OR(ISBLANK({!quantity}), {!quantity} == 0), "missing", "present")
```

**Detection hint:** any `ISBLANK` against a Number/Currency field where zero is semantically equivalent to "no value" should also test for zero.

---

## Anti-Pattern 19: Using NOT without parentheses around the argument

**What the LLM generates:**

```
NOT ISPICKVAL({!stage}, "Won")
```

**Why it happens:** Style copying from natural language ("not is-pick-val").

**Correct pattern:**

```
NOT(ISPICKVAL({!stage}, "Won"))
```

**Detection hint:** regex `NOT [^(]` flags any NOT followed by a non-paren character.

---

## Anti-Pattern 20: Recommending NULL-coalesce inline operators that don't exist

**What the LLM generates:**

```
{!textVar} ?? "default"
```

**Why it happens:** Modern language bleed (TypeScript, C#, Swift).

**Correct pattern:**

```
BLANKVALUE({!textVar}, "default")
```

**Detection hint:** grep for `??` or `?.` operators. Neither exists in Salesforce formula syntax.

---

## Anti-Pattern 21: Assuming formula resources are globally addressable across subflows

**What the LLM generates:** A subflow referencing `{!isStrategicAccount}` defined in a parent flow.

**Why it happens:** Subflow scoping is platform-specific knowledge.

**Correct pattern:** Pass the Boolean as a subflow input variable. Each subflow has its own formula resource scope.

**Detection hint:** any subflow referencing a Formula resource by name without a corresponding subflow input variable is wrong.

---

## Anti-Pattern 22: Using TIMENOW() or DATEDIF() that don't exist in Salesforce formula

**What the LLM generates:** `TIMENOW()` (from Excel), `DATEDIF()` (from Excel), `STR_TO_DATE()` (from MySQL).

**Why it happens:** Cross-dialect bleed from spreadsheets and SQL.

**Correct pattern:** `NOW()` returns DateTime; `TIMEVALUE(...)` extracts Time. Date math is `Date2 - Date1` for day delta. `DATEVALUE(textInIsoFormat)` for parsing.

**Detection hint:** check every function call against the Salesforce Formula Operators and Functions reference. Reject anything not in the documented list.

---

## Anti-Pattern 23: Concatenating a Number directly without TEXT() coercion

**What the LLM generates:**

```
"Total: " & {!total}
```

**Why it happens:** JavaScript-style implicit coercion expectation.

**Correct pattern:**

```
"Total: " & TEXT({!total})
```

**Detection hint:** any `&` operand that references a Number / Currency / Percent field without `TEXT()` should be flagged. Behaviour is platform-version-dependent and not portable.

---

## Anti-Pattern 24: Using ROUND assuming banker's rounding

**What the LLM generates:** Code that depends on `ROUND(2.5, 0) == 2` (banker's rounding).

**Why it happens:** Python / Java default rounding semantics.

**Correct pattern:** Salesforce `ROUND` uses away-from-zero rounding. `ROUND(2.5, 0) == 3`. Document the behaviour at every use site.

**Detection hint:** any financial formula with ROUND should explicitly note the rounding mode.

---

## Anti-Pattern 25: Expanding a long spec into one formula resource

**What the LLM generates:** A single Formula resource expanding 40 input fields into a long formatted output, hitting 6,000 characters.

**Why it happens:** LLMs aim for one-shot completeness.

**Correct pattern:** Pre-emptively decompose at ~3,000 chars even if the spec implies a single formula.

**Detection hint:** measure character length of every generated Formula resource body. If > 4,000, refactor.

---

## Anti-Pattern 26: Recommending CASE that returns mixed types

**What the LLM generates:**

```
CASE(TEXT({!stage}), "Won", 100, "Lost", 0, "Open")
```

**Why it happens:** Number-or-string return types are common in dynamic languages.

**Correct pattern:** All return values in a CASE must be the same type. Either all Number (`100, 0, 50`) or all Text (`"100", "0", "Open"`).

**Detection hint:** check that every return value in a CASE is the same type.

---

## Anti-Pattern 27: Using `IF(condition, TRUE, FALSE)` instead of just `condition`

**What the LLM generates:**

```
IF({!a} > {!b}, TRUE, FALSE)
```

**Why it happens:** Verbose translation of "if greater then true else false".

**Correct pattern:**

```
{!a} > {!b}
```

**Detection hint:** grep for `IF(*, TRUE, FALSE)` and `IF(*, FALSE, TRUE)` (the latter being `NOT(...)`).

---

## Anti-Pattern 28: Not documenting which TZ a date formula uses

**What the LLM generates:** A Formula resource using `TODAY()` or `NOW()` without setting the Description field.

**Why it happens:** LLM ships expression but forgets metadata.

**Correct pattern:** Set the Description on every date-touching formula resource: "Returns running-user-TZ date" or "Returns org-default-TZ datetime". Helps future reviewers.

**Detection hint:** any generated Formula resource that uses `NOW()`, `TODAY()`, `$Flow.CurrentDate`, or `$Flow.CurrentDateTime` should have a non-empty Description noting TZ contract.

---

## Anti-Pattern 29: Recommending a Formula resource for collection aggregation

**What the LLM generates:** "Use a Formula resource to sum the Amount across all Opportunity records in your collection."

**Why it happens:** LLM treats Flow Formula language as more capable than it is.

**Correct pattern:** Flow Formula has no aggregation primitives over collections. Use a Loop element with an Assignment that accumulates into a Number variable, OR use the platform's collection-sum mechanic if available, OR push to Apex Invocable.

**Detection hint:** any guidance that says "use a formula to aggregate / sum / count over a collection" is wrong.

---

## Anti-Pattern 30: Generating REGEX inside a loop body without flagging cost

**What the LLM generates:** A Loop body where each iteration evaluates `REGEX({!loopVar.Email}, "^.*@.*\\..*$")`.

**Why it happens:** REGEX feels like a normal function call.

**Correct pattern:** Either cache the result if referenced multiple times per iteration, or move the REGEX out of the loop if applicable, or push to Apex if scale > 200 records.

**Detection hint:** any REGEX inside a Loop element should trigger a cost-warning in the agent's response.

---

## Anti-Pattern 31: Emitting a `<formulas>` block with no `<dataType>`

**What the LLM generates:**

```xml
<formulas>
    <name>customerGreeting</name>
    <expression>&quot;Hello, &quot; &amp; {!$Record.FirstName}</expression>
</formulas>
```

**Why it happens:** The model writes the two fields the expression needs — a name and the expression itself — and treats type as inferable from the body. In every language it has seen, it would be. Here it is not.

**What the guide says:** `api_meta.txt` L70609 — *"dataType defaults to Number if it isn't defined in a formula."* That block is now a **Number** formula returning a string. It deploys. It fails at the element that consumes it.

**Correct pattern:**

```xml
<formulas>
    <name>customerGreeting</name>
    <dataType>String</dataType>
    <expression>&quot;Hello, &quot; &amp; {!$Record.FirstName}</expression>
</formulas>
```

**Detection hint:** parse the flow and assert `<dataType>` on every `<formulas>` child. Also check the value is one of the seven documented enums — note that Flow Builder's "Text" is `String` in XML, and `Text` is not a valid `FlowDataType` for a formula.

---

## Anti-Pattern 32: Inventing `$Flow.` and `$Setup.` globals that the Metadata API guide has never heard of

**What the LLM generates:** `{!$Flow.InterviewGuid}` to correlate fault logs, `{!$Setup.My_Setting__c.Threshold__c}` inside a Flow formula, `{!$Profile.Name}` in an entry condition.

**Why it happens:** These read like siblings of tokens the model has genuinely seen. Global-variable namespaces are exactly the kind of surface a fluent generator extends by analogy.

**What the corpus says:** across `api_meta.txt`, only `$Flow.CurrentDateTime` (L27212, L73380, L73641, L73744), `$Flow.ActiveStages` (L69784–L69840), `$Flow.CurrentStage` (L71996), `$User.*` (L12949, L31153, L66249, L66825), `$Organization.*` (L66217, L140282) and `$Permission.CustomPermission` / `$Permission.StandardPermission` (L67560–L67562) appear at all. `$Flow.InterviewGuid`, `$Flow.CurrentDate`, `$Flow.FaultMessage`, `$Flow.InterviewStartTime`, `$Profile.` and `$Setup.` return **zero hits**.

**Correct pattern:** Use the ones you can cite. For the rest, state the negative — "`$Flow.FaultMessage` is real and widely used but is not documented in the Metadata API guide" — rather than either dropping it or presenting it as grounded.

**Detection hint:** grep the generated expression for `{!$` and check each token against the list above. A token not on it needs an UNVERIFIED marker, not silence.

---

## Anti-Pattern 33: Putting the branching logic in an inline decision condition instead of a Boolean formula resource

**What the LLM generates:** A `<rules>` block with a formula-mode `conditionLogic` and the expression inlined in the condition body, because the user asked for "a decision that branches on a formula" and that is the literal reading.

**Why it happens:** Literal instruction-following, plus the Flow Builder UI genuinely offers "Formula Evaluates to True" as a criteria mode.

**What the guide says:** `FlowRule.conditionLogic` (`api_meta.txt` L71301–L71313) documents exactly three shapes — `and`, `or`, and advanced logic like `1 AND (2 OR 3)` capped at 1,000 characters. There is no formula value, no `<formula>` child on `FlowRule`, and `grep -n 'formula_evaluates'` returns zero hits. The inline shape is undocumented.

**Correct pattern:** Declare a Boolean `FlowFormula`, reference it as the rule's `leftValueReference`, compare it to `booleanValue true` with `conditionLogic and`. That is the shape the guide's own decision sample uses (L73310–L73325), it is assertable by a `FlowTest` (an inline condition body is not), and it is greppable by name.

**Detection hint:** any generated `<rules>` whose `conditionLogic` is not `and`, `or`, or a numeric advanced-logic string. Tolerate it when reading someone else's flow; do not author it.

---

## Anti-Pattern 34: Wrapping a compound field in BLANKVALUE

**What the LLM generates:**

```
BLANKVALUE({!$Record.BillingAddress}, "(no address)")
```

**Why it happens:** This skill's own headline advice is "guard every nullable operand with `BLANKVALUE`". The model applies it uniformly, which is exactly what a good rule-follower does.

**What the guide says:** `object_reference.txt` L2936–L2937 — *"The only formula functions that you can use with compound fields are `ISBLANK`, `ISCHANGED`, and `ISNULL`. You can't use `BLANKVALUE`, `CASE`, `NULLVALUE`, `PRIORVALUE`, or the equality and comparison operators with compound fields."*

**Correct pattern:** Operate on the components — `BLANKVALUE({!$Record.BillingStreet}, "(no street)")` — which are ordinary fields. Use `ISBLANK` on the compound field only as a presence test.

**Detection hint:** any function other than `ISBLANK`/`ISCHANGED`/`ISNULL` applied to an address field, a geolocation field, or `Name` on a Person Account. The check needs field types, so it belongs in review rather than in the static checker.

---

## Anti-Pattern 35: Quoting the 5,000-character formula limit as fact

**What the LLM generates:** "Flow formulas are limited to 5,000 characters" — often with the error string `Compiled formula is too big to execute (5,001 characters)` attached for authenticity.

**Why it happens:** It is the single most-repeated number in Salesforce formula folklore, and this package itself asserted it until 2026-09-05.

**What the corpus says:** `grep -n -i "5,000 bytes\|5000 bytes\|Compiled formula"` across `api_meta.txt`, `object_reference.txt`, `apexdev.txt` and `salesforce_app_limits_cheatsheet.txt` returns **zero hits**. `FlowFormula` (L70596–L70622) documents no length bound. The only grounded figure is 3,900 source characters (`apexdev.txt` L28144), stated for formula fields.

**Correct pattern:** Give the grounded number, name what it bounds, and mark the Flow binding UNVERIFIED. Then give advice that does not depend on the number: compose at ~3,000 characters, because a formula that long is unreviewable regardless of where the ceiling sits.

**Detection hint:** any numeric platform limit in generated output with no `grep -n` line or guide section beside it. In this domain specifically, "5,000" is the tell.
