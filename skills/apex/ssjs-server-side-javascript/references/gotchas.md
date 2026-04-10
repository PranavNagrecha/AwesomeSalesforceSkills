# Gotchas — SSJS Server-Side JavaScript

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Script Activity Timeout Terminates Silently at 30 Minutes

**What happens:** A Script Activity that runs longer than 30 minutes is forcibly terminated by the Marketing Cloud platform. The step is marked as an error in Automation Studio, but no partial completion is recorded — work done before the termination is not rolled back, but work not yet done is simply abandoned. There is no callback, no cleanup hook, and no warning log entry indicating how far the script progressed.

**When it occurs:** Processing large volumes of Data Extension rows in a procedural SSJS loop; calling external APIs with high per-record latency; running complex in-memory aggregations on datasets with hundreds of thousands of rows.

**How to avoid:** Prefer SQL Query Activities for bulk set-based operations on Data Extensions — they are significantly faster and not subject to the 30-minute Script Activity limit. When SSJS loops are unavoidable, break the work into smaller batches using cursor-based paging tracked in a "state" Data Extension, and chain multiple Script Activities in the Automation. Always estimate row count * per-row processing time before implementing a loop-based solution.

---

## Gotcha 2: `var` Is Function-Scoped, Not Block-Scoped — No `let` or `const`

**What happens:** Any use of `let`, `const`, arrow functions, template literals, destructuring, the spread operator, or `Promise` in SSJS causes a syntax error or runtime error. The Marketing Cloud SSJS engine runs an ES3-compatible dialect that predates these features by many years. The error message is often cryptic — `let` produces a "syntax error" that points at the line but gives no hint about the cause.

**When it occurs:** When developers write SSJS using modern JavaScript habits. This is the single most common mistake when AI assistants generate SSJS code — they default to ES6+ syntax.

**How to avoid:** Always use `var`. Use `function` declarations instead of arrow functions. Use string concatenation with `+` instead of template literals. Use `Stringify()` instead of `JSON.stringify()` and `Platform.Function.ParseJSON()` instead of `JSON.parse()`. Validate SSJS by looking for `let`, `const`, `=>`, backticks, `...` spread, and `async`/`await` before deploying.

---

## Gotcha 3: WSProxy Retrieve Returns Paged Results — Missing `HasMoreRows` Causes Silent Data Loss

**What happens:** `prox.retrieve()` returns only the first page of results (typically up to 2,500 rows). If the result set is larger and the caller does not check `result.HasMoreRows` and call `prox.getNextPage()`, the remaining rows are silently discarded. The script completes successfully with no error, and the practitioner has no indication that data was missed unless they compare the result count against a known total.

**When it occurs:** Any time a WSProxy retrieve could match more than 2,500 rows. Common scenarios: retrieving from large Data Extensions, querying All Subscribers, or pulling Send-level tracking data.

**How to avoid:** Always wrap `prox.retrieve()` in a `while` loop that checks `result.HasMoreRows` and calls `result = prox.getNextPage()` to advance. See the example in `references/examples.md` for the correct loop pattern. Log the total row count after the loop completes to verify expected volume.

---

## Gotcha 4: AMPscript Executes Before SSJS — Output Cannot Flow Backwards

**What happens:** In a mixed SSJS/AMPscript file, the Marketing Cloud rendering engine processes all AMPscript substitutions and function calls first, then evaluates SSJS blocks. This means AMPscript `@variables` set before an SSJS block can be injected into SSJS string literals (because AMPscript runs first and substitutes the values into the raw text). However, SSJS output or SSJS-set values cannot be read by AMPscript in the same render pass — AMPscript has already finished executing by the time SSJS runs.

**When it occurs:** When developers try to use SSJS to compute a value and then use that value in an AMPscript conditional in the same content block. Or when they expect `Write()` output to be consumable by AMPscript.

**How to avoid:** Design the data flow to go AMPscript → SSJS, not SSJS → AMPscript. If SSJS output must influence downstream rendering, write it to a Data Extension first, then read it in a subsequent request or Activity step.

---

## Gotcha 5: `Platform.Load("Core", "1.1.1")` Is Required for Most Built-In Functions

**What happens:** Functions like `Platform.Function.Lookup()`, `Platform.Function.ParseJSON()`, `Stringify()`, `Platform.Function.Now()`, and many other Marketing Cloud built-in functions are not available unless the Core library is explicitly loaded. Without `Platform.Load("Core", "1.1.1")`, calls to these functions throw a "not found" or "undefined" error. The error message does not tell you that the Core library is missing — it simply says the function does not exist.

**When it occurs:** When SSJS is authored without the Platform.Load call, or when copying SSJS snippets from documentation that omit the library declaration.

**How to avoid:** Always include `Platform.Load("Core", "1.1.1");` as the first statement inside the `<script runat="server">` tag, before any other code. Treat it as mandatory boilerplate for every SSJS block that uses Marketing Cloud built-in functions.
