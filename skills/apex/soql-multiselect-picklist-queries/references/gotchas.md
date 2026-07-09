# Gotchas — SOQL Multi-Select Picklist Queries

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `=` under-matches and looks correct on demo data

**What happens:** `WHERE MSP1__c = 'AAA'` returns only records whose *entire* stored selection
is exactly `AAA`. Any record that also selected another value (stored as `AAA;BBB`) is silently
excluded — no error, just a short result set.

**When it occurs:** whenever the value being matched is one of several possible selections. It
hides during testing because demo records often have a single value selected, so `=` appears to
work; it breaks once real users select combinations.

**How to avoid:** use `INCLUDES ('AAA')` for "has this value." Reserve `=` for the rare case
where you genuinely need the whole selection to equal one exact string.

---

## Gotcha 2: `ORDER BY` on the field is a hard error, not a no-op

**What happens:** adding `ORDER BY MSP1__c` makes the query fail. Multi-select picklist is on
the list of `ORDER BY`-unsupported data types (with rich text area, long text area, encrypted
fields, and data category group reference).

**When it occurs:** any attempt to sort results by the multi-select field, including inside a
dynamic query string assembled from a generic "sort by column X" feature.

**How to avoid:** order by a supported field, or return the rows and sort them in Apex. If a UI
lets users sort arbitrary columns, exclude multi-select fields from the sortable set.

---

## Gotcha 3: comma inside the quotes is not an OR

**What happens:** `INCLUDES ('AAA,BBB')` does not mean "AAA or BBB." The comma sits *inside* a
single quoted operand, so it is treated as part of the literal value being matched — not as a
group separator.

**When it occurs:** when the author confuses the two grammars. OR is expressed by *separate*
quoted operands (`INCLUDES ('AAA','BBB')`); AND is a semicolon *inside* one operand
(`INCLUDES ('AAA;BBB')`).

**How to avoid:** commas go *between* quoted operands (OR); semicolons go *inside* an operand
(AND). Never put a comma inside the quotes unless the stored value literally contains one.

---

## Gotcha 4: matching the display label instead of the API name

**What happens:** a query that filtered fine yesterday returns nothing after an admin renames a
picklist label or the org is translated, because the query hard-coded the old display value.

**When it occurs:** labels are edited/translated while the value API names stay stable, and the
query was written against the label.

**How to avoid:** match by the value's **API name** (supported in API version 39.0 and later),
which is decoupled from the display label. Confirm the query runs at 39.0+ before relying on
this behavior.

---

## Gotcha 5: dynamic INCLUDES built by string concatenation

**What happens:** a `Database.query('... INCLUDES (\'' + userInput + '\')')` string either
breaks on a value that contains a quote or semicolon, or becomes a SOQL-injection vector when
`userInput` is attacker-controlled.

**When it occurs:** the value set is dynamic (user input, Flow, LWC) and the developer builds
the clause by concatenation instead of binding.

**How to avoid:** prefer static SOQL with a bind variable — filter literals in a `WHERE` clause
are a supported bind position, and a bind works with `INCLUDES`. If the query must be dynamic,
escape with `String.escapeSingleQuotes` at minimum, and keep values in binds. See
`apex/apex-dynamic-soql-binding-safety`.
