# LLM Anti-Patterns — Formula Fields

Common mistakes AI coding assistants make when generating or advising on Salesforce formula fields.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not handling null values in formula expressions

**What the LLM generates:** `Account.AnnualRevenue / Account.NumberOfEmployees`

**Why it happens:** LLMs write formulas assuming all fields have values. When NumberOfEmployees is null or zero, the formula returns an error or #Error!. Every field reference in a formula that could be blank must be wrapped in null-handling functions.

**Correct pattern:**

```
IF(
  OR(ISBLANK(NumberOfEmployees), NumberOfEmployees = 0),
  NULL,
  AnnualRevenue / NumberOfEmployees
)

Null-handling rules:
- Numeric fields: check ISBLANK() and zero before division.
- Text fields: use BLANKVALUE(field, 'default') or ISBLANK().
- Date fields: check ISBLANK() before DATEVALUE() or date math.
- Cross-object references: check ISBLANK() on the relationship itself
  (e.g., ISBLANK(Account.OwnerId)) before traversing.
```

**Detection hint:** If the formula divides by a field without checking for zero or null, it will error on blank data. Regex: `/\s*[A-Za-z_]+\b` without a preceding `IF.*ISBLANK` guard.

---

## Anti-Pattern 2: Merging the Three Formula Size Limits Into One

**What the LLM generates:** A formula with 15+ nested IF statements, justified
with a limit statement like "the 5,000 compiled character limit (standard) or
3,900 compiled character limit (for some older objects)".

**Why it happens:** Salesforce enforces **three separate** formula size limits,
and every one of the numbers above is real — but they have been collapsed into
a single dimension and given a fictitious object-dependency. 3,900 is the limit
on the *source text you type*; 5,000 bytes is the *compile* limit; and there is
a third, 4,000 bytes, on the *saved* formula. A model that has absorbed two of
the three numbers has to reconcile them, and "it depends on the object" is the
cheapest available story — it explains the discrepancy without requiring the
model to know that the limits measure different things. There is no class of
"older objects" with a different formula limit; all three apply to every object
identically.

The practical damage runs both ways. An author told the compile limit is 3,900
refactors against a ceiling that is 22% too tight and splits a formula that
would have saved fine. An author told the *text* limit is 5,000 writes 4,500
characters of formula and cannot save it at all.

**Correct pattern:**

```
Three independent formula limits, all objects, no exceptions:
- Maximum number of characters (source text in the editor): 3,900
- Maximum formula size when saved:                          4,000 bytes
- Maximum formula size when compiled:                       5,000 bytes
- Maximum unique relationships referenced per formula:      10

They fail differently:
- Over 3,900 characters -> "Too many characters in field formula"
  Fix by shortening the TEXT: strip comments and whitespace, shorten
  field API names, factor repeated subexpressions into helper fields.
- Over 5,000 compiled bytes -> "Compiled formula is too big to execute
  (N characters). Maximum size is 5,000 characters"
  Fix by reducing QUERY complexity. Deleting whitespace or comments does
  NOT help here — compile size reflects the generated query, not the text.
- Cross-object references add hidden compile size overhead.

Strategies to stay under the limit:
1. Break complex formulas into helper formula fields:
   - Field 1: Revenue_Tier__c (formula: CASE on AnnualRevenue)
   - Field 2: Final_Score__c (formula: references Revenue_Tier__c)
2. Replace nested IFs with CASE() where possible (lower compile cost).
3. Use BLANKVALUE() instead of IF(ISBLANK()) to save characters.
4. Move truly complex logic to a Flow or Apex trigger that writes
   to a stored field instead of a formula.
```

**Detection hint:** Two checks. (1) If the formula has more than 10 nested IF
statements or spans more than 50 lines, it may exceed compile limits — count
nested `IF(` occurrences. (2) Grep any limit claim for the words `compiled` and
`3,900` in the same sentence, or `characters` and `5,000` in the same sentence:
both pairings are inverted. 3,900 belongs to characters, 5,000 bytes belongs to
compile size, 4,000 bytes belongs to save size. Any sentence that makes a
formula limit conditional on the object ("some objects", "older objects",
"standard objects") is fabricated — none of the three limits varies by object.

---

## Anti-Pattern 3: Using cross-object formulas beyond supported relationship depth

**What the LLM generates:** `Account.Parent.Parent.Parent.Owner.Manager.Name`

**Why it happens:** LLMs chain relationships without checking the Salesforce limit. Cross-object formulas can span up to 10 unique relationships but each hop adds compile size. Deep chains across 4+ parent levels are fragile, hard to maintain, and often exceed compile limits.

**Correct pattern:**

```
Cross-object formula limits:
- Maximum: 10 unique relationships per formula.
- Each relationship hop adds ~800 compiled characters of overhead.
- Practical limit: 3-4 hops before compile size becomes a problem.

If deeper traversal is needed:
1. Create a formula or roll-up field at an intermediate level.
2. Reference the intermediate field from the original formula.
   Example:
   - Account.Parent_Region__c (formula on Account: Parent.Region__c)
   - Opportunity.Account_Parent_Region__c (formula: Account.Parent_Region__c)
3. For frequently changing parent values, use a Flow to stamp
   the value on the child record instead of a formula.
```

**Detection hint:** If the formula chains more than 3 relationship hops (counting dots), it may hit compile limits or be unmaintainable. Count the number of `.` in a single field reference.

---

## Anti-Pattern 4: Treating formula fields as stored values for historical reporting

**What the LLM generates:** "Create a formula field to calculate the SLA compliance date. You can report on historical compliance."

**Why it happens:** LLMs do not distinguish between formula fields (calculated at read time from current data) and stored fields (persisted at write time). Formula fields always reflect the current state of their inputs. They cannot show what a value was at a past date. Historical reporting requires stored fields or snapshot reporting.

**Correct pattern:**

```
Formula fields are NOT historical:
- A formula field recalculates every time the record is viewed or queried.
- If input values change, the formula result changes retroactively.
- Example: Fiscal_Quarter__c formula based on CloseDate always shows
  the quarter for the CURRENT CloseDate, not the original.

For historical values:
1. Use a stored field updated by a Flow or trigger at the time of the event.
2. Use Reporting Snapshots to capture point-in-time values.
3. Use the Field History Tracking feature for up to 20 fields per object.
4. Use a Flow to copy the formula result to a stored field at
   a specific business milestone.
```

**Detection hint:** If the output creates a formula field for a value that the business needs to track historically, the formula will overwrite past values. Search for `historical`, `point-in-time`, or `as of date` in the requirement combined with a formula field solution.

---

## Anti-Pattern 5: Using IMAGE() or HYPERLINK() without considering Lightning rendering

**What the LLM generates:** `IMAGE("/img/samples/flag_green.gif", "Green", 15, 15)` or `HYPERLINK("/apex/CustomPage", "Click Here")`

**Why it happens:** LLMs generate formulas with Classic-era IMAGE() and HYPERLINK() patterns. In Lightning Experience, IMAGE() formulas render differently (relative URLs may break), and HYPERLINK() with relative URLs may not navigate correctly. Rich text formula rendering also differs between Classic and Lightning.

**Correct pattern:**

```
Lightning-compatible formula patterns:

IMAGE():
- Use full URLs, not relative paths:
  IMAGE("https://yourdomain.my.salesforce.com/img/icon.png", "Icon", 20, 20)
- Or use a Static Resource URL for self-hosted images.
- Or use a Custom Metadata field to store the image URL for portability.

HYPERLINK():
- Use full URLs or Lightning-compatible paths:
  HYPERLINK("/lightning/r/Account/" & Id & "/view", "View Account")
  Not: HYPERLINK("/" & Id, "View") — Classic path.
- For Visualforce pages:
  HYPERLINK("/apex/CustomPage?id=" & Id, "Open Page")

Both functions return Text type — set the formula return type to Text.
```

**Detection hint:** If the formula uses relative image paths (starting with `/img/`) or Classic-style URLs (starting with `"/"`), it may not render correctly in Lightning. Regex: `IMAGE\(\s*"\/img\/` or `HYPERLINK\(\s*"\/[^l]`.
