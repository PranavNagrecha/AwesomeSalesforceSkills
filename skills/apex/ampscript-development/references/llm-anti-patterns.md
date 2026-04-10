# LLM Anti-Patterns — AMPscript Development

Common mistakes AI coding assistants make when generating or advising on AMPscript in Salesforce Marketing Cloud.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using SSJS When AMPscript Is the Correct Tool for Subscriber-Level Rendering

**What the LLM generates:** A `<script runat="server">` block with `Platform.Load("Core", "1")` and `DataExtension.Init()` to perform a subscriber-level field lookup inside an email body, when `Lookup()` or `AttributeValue()` in AMPscript would accomplish the same thing more simply.

**Why it happens:** LLMs trained on general web content see more JavaScript/SSJS examples in Marketing Cloud developer forums than AMPscript examples for equivalent tasks. JavaScript training data generalizes into SSJS suggestions. The model also conflates "server-side" with "JavaScript" by default.

**Correct pattern:**

```
%%[
SET @tier = Lookup("Loyalty_DE", "Tier", "SubscriberKey", _subscriberkey)
]%%
<p>Your tier: %%=v(@tier)=%%</p>
```

**Detection hint:** Look for `<script runat="server">` in email body content for tasks that only require a DE Lookup and conditional rendering. If no HTTP calls or complex manipulation are needed, SSJS is the wrong tool.

---

## Anti-Pattern 2: Incorrect FOR Loop Row Access — Direct Array Notation Instead of Row() and Field()

**What the LLM generates:** AMPscript FOR loops that attempt to access rowset elements using array-style notation like `@rows[@i]` or `@rows.FieldName`, or that call `LookupRows()` without assigning the result to a variable before the loop.

**Why it happens:** LLMs familiar with Python, JavaScript, or other languages with native array iteration assume similar syntax works in AMPscript. AMPscript does not support bracket notation or dot notation on rowsets — it requires the `Row()` and `Field()` functions.

**Correct pattern:**

```
%%[
SET @rows = LookupRows("Orders_DE", "SubscriberKey", _subscriberkey)
SET @rowCount = RowCount(@rows)

FOR @i = 1 TO @rowCount DO
  SET @row = Row(@rows, @i)
  SET @orderNum = Field(@row, "OrderNumber")
NEXT @i
]%%
```

**Detection hint:** Look for `@rows[@i]`, `@rows.FieldName`, or any FOR loop that does not include `SET @row = Row(@rows, @i)` followed by `Field(@row, "FieldName")` for field access.

---

## Anti-Pattern 3: Missing Null Guard Before FOR Loop

**What the LLM generates:** A FOR loop over a `LookupRows()` result without first checking `RowCount(@rows) > 0`, which causes the surrounding HTML markup (table tags, list tags) to render even when no rows match — producing empty or broken layout elements for subscribers with no data.

**Why it happens:** LLMs generate the "happy path" loop without considering that `LookupRows()` returns an empty rowset (not null) when no records match. The loop body correctly executes zero times, but outer HTML wrappers (tables, divs) are still emitted.

**Correct pattern:**

```
%%[
SET @rows = LookupRows("Orders_DE", "SubscriberKey", _subscriberkey)
SET @rowCount = RowCount(@rows)
]%%

%%[ IF @rowCount > 0 THEN ]%%
<ul>
%%[ FOR @i = 1 TO @rowCount DO ]%%
  %%[ SET @row = Row(@rows, @i) ]%%
  <li>%%=Field(@row, "OrderNumber")=%%</li>
%%[ NEXT @i ]%%
</ul>
%%[ ELSE ]%%
<p>No orders found.</p>
%%[ ENDIF ]%%
```

**Detection hint:** Look for `FOR @i = 1 TO RowCount(...)` or `FOR @i = 1 TO @rowCount` blocks that are not wrapped in an `IF @rowCount > 0 THEN` guard.

---

## Anti-Pattern 4: Using Block Syntax in Email Subject Line or Preheader

**What the LLM generates:** AMPscript block syntax (`%%[ SET @name = AttributeValue("FirstName") ]%%`) placed directly in the subject line or preheader field, with the expectation that the variable will be evaluated and produce personalized output.

**Why it happens:** The LLM sees that block syntax works in the email body and generalizes it to all content areas. The distinction between block syntax (body only) and inline syntax (all fields including subject/preheader) is a Marketing Cloud-specific constraint that does not appear in general programming training data.

**Correct pattern:**

Subject line field content (inline only):
```
Hi %%=AttributeValue("FirstName")=%%, your exclusive offer is inside
```

If computation is needed, set the variable in a body block and reference it inline in the subject:
```
Subject line: Your %%=v(@tierName)=%% member offer inside
Body block: %%[ SET @tierName = AttributeValue("LoyaltyTier") ]%%
```

**Detection hint:** Look for `%%[` or `]%%` in subject line or preheader field values. Any occurrence of block delimiters in those fields is incorrect.

---

## Anti-Pattern 5: Using Curly/Smart Quotes in AMPscript String Literals

**What the LLM generates:** AMPscript with Unicode smart quotes (`"field"` or `'value'`) in string literals, function arguments, or DE names — typically when the LLM renders output via a rich-text system or when the user pastes the generated code into a rich-text editor before copying into Marketing Cloud.

**Why it happens:** LLMs generate output that may be rendered with typographic quotes by the interface. The distinction between ASCII straight quotes and Unicode curly quotes is invisible in most rendered text, so the error is not apparent until the AMPscript parser rejects the character at send time.

**Correct pattern:**

```
%%[
/* Correct — ASCII straight double quotes */
SET @tier = Lookup("Loyalty_DE", "Tier", "SubscriberKey", _subscriberkey)
]%%
```

Incorrect (will cause parse failure):
```
%%[
/* Wrong — curly/smart quotes */
SET @tier = Lookup("Loyalty_DE", "Tier", "SubscriberKey", _subscriberkey)
]%%
```

**Detection hint:** Run a find for Unicode code points U+201C (`"`), U+201D (`"`), U+2018 (`'`), U+2019 (`'`) in the raw HTML source of the email. Any occurrence inside a `%%[ ... ]%%` block is a parse failure risk.

---

## Anti-Pattern 6: Referencing an Undeclared Variable

**What the LLM generates:** AMPscript that uses a variable (`@tier`, `@name`, etc.) in a conditional expression or output position before the variable has been assigned with a `SET` statement, or that assumes a variable set in one content block is available in a separate `%%[ ... ]%%` block in a different template region.

**Why it happens:** In most programming languages, undefined variables either throw a compile-time error or return a language-defined null/undefined value silently. AMPscript returns empty string for undeclared variables in some contexts but can also raise a runtime error depending on the function context. LLMs assume the more lenient behavior universally.

**Correct pattern:**

```
%%[
/* Always SET before use */
SET @discount = ""
SET @tier = AttributeValue("LoyaltyTier")

IF @tier == "Gold" THEN
  SET @discount = "GOLD20"
ENDIF
]%%

<p>Your code: %%=v(@discount)=%%</p>
```

**Detection hint:** Look for `v(@varName)`, `IF @varName ==`, or `Field(@row, ...)` calls where `@varName` does not have a preceding `SET @varName =` statement in the same or an earlier `%%[ ... ]%%` block in the content area.
