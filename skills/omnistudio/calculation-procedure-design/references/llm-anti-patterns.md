# LLM Anti-Patterns — Calculation Procedure Design

Mistakes AI coding assistants reliably make when designing Calculation
Procedures and Calculation Matrices. Each entry names the wrong output, the
mechanism producing it, the corrected version, and a mechanical check.

This domain is unusually hostile to language models for a specific reason: the
designer labels and the API names diverge (**Calculation Procedure** →
`ExpressionSet`; **Calculation Matrix** → `CalculationMatrix`, which the object
reference labels *Decision Matrix*), and the field vocabulary is irregular
enough that generation regularises it into plausible non-existent names.

---

## Anti-Pattern 1: `*` As A Wildcard

**What the LLM generates:** a fallback row using an asterisk, presented as
standard practice:

```text
| Region | ProductTier | BasePrice |
|--------|-------------|-----------|
| NA     | Gold        | 100       |
| NA     | *           | 60        |
| *      | *           | 50        |
```

**Why it happens:** `*` is the wildcard in shell globbing, SQL `LIKE` patterns
(as `%`), regular expressions, spreadsheet lookups, and effectively every rules
engine the model has read about. It is one of the most over-determined
conventions in the entire training corpus. Salesforce's choice — a per-column
opt-in with a user-configured token — is not merely different, it is
*structurally* different, because the wildcard is a property of the column
rather than a property of the value. A model producing a *table* has no natural
place to express a column property, so it emits the value-level convention it
knows.

**Correct pattern:**

```text
Wildcards are configured on CalculationMatrixColumn:

    IsWildcardColumn     boolean, default false
                         "Specifies that this column can contain a
                          wildcard value such as ALL."
    WildcardColumnValue  string
                         "The value that indicates a wildcard,
                          for example ALL."

The token is whatever YOU set WildcardColumnValue to, on each column
where IsWildcardColumn is true. A column that has not opted in treats
'*' as a literal string that no real input will ever equal.

Rows then use the configured token:

    | Region | ProductTier | BasePrice |
    | NA     | Gold        | 100       |
    | NA     | ALL         | 60        |
    | ALL    | ALL         | 50        |
```

**Detection hint:** Grep any proposed matrix for `*` in a data cell. Then check
the column definitions: for every column whose rows contain a fallback token,
`IsWildcardColumn` must be `true` and `WildcardColumnValue` must equal that
token exactly. A fallback row on a column that has not opted in is dead rows —
it will never match, and it fails silently.

---

## Anti-Pattern 2: Modelling Ranges As Min/Max Column Pairs

**What the LLM generates:**

```text
| DriverAgeMin | DriverAgeMax | PriorClaimsMin | PriorClaimsMax | BaseRate |
| 16           | 24           | 0              | 0              | 1.80     |
| 25           | 64           | 0              | 0              | 1.00     |
```

**Why it happens:** Min/Max column pairs are how you express a band in a
spreadsheet, in a SQL `BETWEEN`, and in every hand-rolled rating table. The
model is faithfully reproducing the source artifact it was almost certainly
shown — a spreadsheet — rather than translating it into the platform's model.
The output also *works*, in the sense that a procedure can compare against it,
which removes the feedback that would otherwise correct the pattern.

**Correct pattern:**

```text
CalculationMatrixColumn.DataType is a RESTRICTED picklist:

    Boolean | Currency | Number | NumberRange | Percent | Text | TextRange

NumberRange and TextRange are first-class range types. Boundaries live in:

    RangeValues   textarea
                  "A list of values that define range boundaries."

So two dimensions need two columns, not four:

    DriverAge     ColumnType = Input   DataType = NumberRange
    PriorClaims   ColumnType = Input   DataType = NumberRange
    BaseRate      ColumnType = Output  DataType = Number

Bands cannot overlap or gap by construction, and the comparison
moves out of your procedure steps.
```

**Detection hint:** Any pair of columns whose names differ only by a
`Min`/`Max`, `From`/`To`, `Start`/`End`, or `Lower`/`Upper` suffix. That naming
pair is the signature of a hand-rolled range, and it should almost always be
one `NumberRange` or `TextRange` column instead.

---

## Anti-Pattern 3: Using `IsActive` On A Matrix Version (Or `Status` On Either)

**What the LLM generates:** activation code or a validation query against a
field that does not exist on that object:

```apex
// WRONG — CalculationMatrixVersion has no IsActive field
List<CalculationMatrixVersion> live = [
    SELECT Id FROM CalculationMatrixVersion WHERE IsActive = true
];

// ALSO WRONG — ExpressionSetVersion has no Status field
List<ExpressionSetVersion> esv = [
    SELECT Id FROM ExpressionSetVersion WHERE Status = 'Active'
];
```

**Why it happens:** `IsActive` is the Salesforce house convention — it is on
`User`, `Product2`, `CampaignMember`, dozens of standard objects, and on
`ExpressionSetVersion` itself. Having just used `IsActive` correctly on the
expression set, the model carries it to the sibling object by local coherence.
`Status` arrives from the same instinct one level up: a versioned artifact with
a lifecycle "should" have a status picklist, and many Salesforce objects do.
Both errors are generalisations from genuinely strong patterns.

**Correct pattern:**

```text
ExpressionSetVersion        -> IsActive   (boolean, default false)
                               NO Status field on this object

CalculationMatrixVersion    -> IsEnabled  (boolean, default false)
                               "Specifies whether this version is active."
                               NO IsActive field on this object

The UI calls both "activate". The API does not.
```

**Detection hint:** Mechanical and total. `IsActive` on
`CalculationMatrixVersion`, `IsEnabled` on `ExpressionSetVersion`, or `Status`
on either is a compile-time or query-time failure. A `describeSObjects()` call,
or one SOQL query in an anonymous block, settles it in seconds — and this check
has no false positives.

---

## Anti-Pattern 4: Inventing A `ConnectApi` Apex Class To Invoke An Expression Set

**What the LLM generates:** a confident one-liner against a class that does not
exist:

```apex
// DOES NOT COMPILE — ConnectApi.EvaluationService is not a real class
Map<String, Object> result =
    ConnectApi.EvaluationService.executeExpression(expressionSetName, inputs);
```

Variants substitute `ConnectApi.BusinessRulesEngine`,
`ConnectApi.ExpressionSetService`, or an `.evaluate()` / `.run()` method on the
same imagined class.

**Why it happens:** The `ConnectApi` namespace is genuinely large and genuinely
heterogeneous — dozens of `*Service`-suffixed classes spanning Chatter,
Communities, Commerce, Einstein. That makes
`ConnectApi.<Domain>Service.<verb>()` a **highly productive naming template**,
and the model completes it for any domain that has a Connect REST API, on the
assumption that every Connect REST resource has a mirrored Apex class. It does
not. Business Rules Engine has Connect *REST* resources with no corresponding
`ConnectApi` Apex class. The tell is that the surrounding explanation is
usually correct — the model knows expression sets are invoked rather than
queried, and knows Connect is involved — so only the symbol is confabulated,
and it lands in a code block a developer pastes straight into a class.

**Correct pattern:**

```text
Documented invocation surfaces for Business Rules Engine expression sets:

  Connect REST API   POST /services/data/v67.0/connect/business-rules
                          /expressionSet/${expressionSetName}
                     Available since API version 55.0.
                     Body: { "inputs": Map<String,Object>[],
                             "options": { effectiveDate, useDatesOnly,
                                          actionContextCode,
                                          explainabilitySpecName } }
                     Response: Business Rules Result

  Flow               the "Invoke an active expression set" action

  OmniStudio IP      the "Expression Set" action  (invokes expression sets)
                     the "Decision Matrix" action (calls decision matrices)

  Apex               via the invocable action, or by calling the Connect
                     REST resource over a Named Credential

There is NO ConnectApi.EvaluationService class and no executeExpression()
method.
```

**Detection hint:** Two independent checks. (1) Confirm any
`ConnectApi.<Something>` symbol appears in the ConnectApi Namespace class list
— the namespace is documented exhaustively, so absence is proof of
non-existence, not merely absence of evidence. (2) Treat the inference "this
feature has a Connect REST API, therefore it has a `ConnectApi` Apex class" as
invalid: the two surfaces are curated independently and REST coverage is much
broader. Any generated code pairing a correct REST resource with a same-named
Apex class is exhibiting exactly this error.

---

## Anti-Pattern 5: An Apex If-Else Ladder Instead Of A Matrix

**What the LLM generates:** a 200-line Apex class replicating a rate card as
nested conditionals, when asked to "implement this pricing logic."

**Why it happens:** "Implement" reads as "write code," and the model is far more
practised at Apex than at declarative rate tables. The generated class is also
*correct* — it computes the right numbers — so nothing in a functional review
rejects it. The cost is entirely non-functional and entirely deferred: every
rate revision now needs a developer, a deployment, and a test run, and the
rates live in a place the business cannot read.

**Correct pattern:**

```text
The dividing line is tabular vs algorithmic.

Matrix when:
  - the rule is a lookup: given these inputs, return these outputs
  - the values change on a business schedule, not a release schedule
  - the business owns the numbers and should be able to see them
  - correctness at a past date must be reproducible (versioning +
    effective dates + Rank give you this for free)

Apex when:
  - genuine iteration or recursion is required
  - the calculation calls out mid-computation
  - the logic is algorithmic rather than tabular

Hybrid, which is usually right:
  matrix for the rate lookup, procedure steps for the arithmetic,
  Apex only for what neither can express.
```

**Detection hint:** Any Apex `if`/`else if` chain, `switch`, or `Map` literal
whose branch conditions are business values (regions, tiers, age bands,
product codes) rather than control flow. That is a rate table wearing a code
costume, and it belongs in a matrix.

---

## Anti-Pattern 6: Editing The Active Version To Fix A Rate

**What the LLM generates:** "Update the rate in the matrix to 1.35" — a direct
edit to the enabled version, presented as the fix.

**Why it happens:** The model treats a matrix as a mutable data table, which is
what it looks like. Versioning with effective dates and rank-based selection is
a Salesforce-specific lifecycle that is thinly represented in training data
relative to the enormous corpus about editing rows in tables. The model is also
optimising for the instruction it was given ("fix the rate"), and the direct
edit satisfies it completely.

**Correct pattern:**

```text
Never edit an enabled version. Publish a new one that outranks it.

    v7 (wrong)   IsEnabled = true
                 StartDateTime = 2027-01-01T00:00:00Z
                 EndDateTime   = null
                 Rank          = 20

    v8 (fix)     IsEnabled = true
                 StartDateTime = 2027-01-01T00:00:00Z   <- same window
                 EndDateTime   = null
                 Rank          = 30                     <- outranks v7

Documented selection rule (CalculationMatrixVersion.Rank):
  "When the invocation time of a matrix call is between the
   StartDateTime and EndDateTime of more than one enabled matrix
   version, the version with the highest Rank is chosen."

v7 stays enabled and auditable. v8 wins every lookup from now on.
Setting IsEnabled = false on v7 also works but erases the record
that it was ever live — prefer the rank override where history matters.
```

**Detection hint:** Any instruction that mutates a matrix row, or any
`update` DML against a `CalculationMatrixVersion` or `CalculationMatrixRow`
whose parent version has `IsEnabled = true`. Also flag any remediation plan for
a wrong rate that does not name a new version number.

---

## Anti-Pattern 7: Version Selection Explained Without `Rank`

**What the LLM generates:** "The procedure automatically selects the version
whose effective date range covers the calculation date" — accurate as far as it
goes, and incomplete in the way that matters.

**Why it happens:** Date-effective selection is the intuitive half and appears
in most prose about versioned rules. `Rank` is a tiebreaker documented in a
single field description on the object reference. A model summarising the
concept reproduces the narrative half and drops the field-level half, which is
also the half that determines the answer whenever two versions overlap.

**Correct pattern:**

```text
Selection is THREE conditions, not one:

  1. IsEnabled = true          (IsActive on ExpressionSetVersion)
  2. invocation time falls within [StartDateTime, EndDateTime]
  3. among the survivors, HIGHEST Rank wins

Both CalculationMatrixVersion and ExpressionSetVersion carry all four
fields: the activation boolean, StartDateTime, EndDateTime, Rank.

Two enabled versions with overlapping windows and the SAME Rank have
no documented tiebreaker. Assign distinct ranks with gaps (10, 20, 30)
so a correction can slot between them without renumbering.
```

**Detection hint:** Any explanation of version selection that mentions dates
but not `Rank`; any version design where two enabled versions share a rank; any
matrix whose versions were all created at the default rank.

---

## Anti-Pattern 8: Treating `LoadProcessStatus = 'CompletedWithErrors'` As Success

**What the LLM generates:** a deployment or data-load runbook that waits for the
CSV load to finish and then enables the version, with no status assertion — or
one that checks only for `Failed`.

**Why it happens:** "Completed" is the substring the model matches on, and in
almost every other status enum a completed state is a success state. The
platform's enum has a genuinely unusual middle value that means *finished and
wrong*. Checking for `Failed` also feels like sufficient error handling,
because in most enums the failure state is the only non-success state.

**Correct pattern:**

```text
CalculationMatrixVersion.LoadProcessStatus is a restricted picklist:

    Completed | CompletedWithErrors | Failed | InProgress | Pending

Gate enablement on EQUALITY with 'Completed', never on absence of 'Failed':

    SELECT Id, Name, VersionNumber, LoadProcessStatus, IsEnabled
    FROM   CalculationMatrixVersion
    WHERE  CalculationMatrixId = :matrixId
    AND    LoadProcessStatus != 'Completed'

Any row returned must not be enabled.

Then assert row counts: CalculationMatrixRow count for the version must
equal the source CSV's data-row count. This is the only reliable
partial-load detector — the platform does not expose which rows failed
at query time, and a missing row is indistinguishable at runtime from a
row that legitimately falls through to the wildcard.
```

**Detection hint:** Any activation step conditioned on `!= 'Failed'` rather than
`== 'Completed'`. Any matrix load procedure with no row-count assertion.

---

## Anti-Pattern 9: Ignoring `effectiveDate` On Back-Dated Calculations

**What the LLM generates:** an invocation that passes only `inputs`, omitting
`options` — so version selection evaluates against the invocation time.

**Why it happens:** `options` is documented as not required, and the model
correctly omits optional parameters when the prompt does not mention them. The
requirement that a March recalculation must price at January's rates is a
domain fact, not an API fact, so nothing in the API surface prompts for it.

**Correct pattern:**

```json
{
  "inputs": [{ "age": "25", "state": "CA", "PatientId": "001xx000003GYjnAAG" }],
  "options": {
    "effectiveDate": "2027-01-15T00:00:00Z",
    "useDatesOnly": "true"
  }
}
```

```text
options.effectiveDate is an ISO 8601 timestamp. Version selection
evaluates against it instead of "now", which is what makes a reissued
quote price at the rates in force on its original issue date.

Decide this early. Retrofitting back-dating means every caller changes:
the business date (quote issue date, policy effective date, claim date)
becomes a REQUIRED input on every invocation path, not an optional one.

Two body conventions that are easy to get wrong:
  - field aliases:       append "Id" to the object alias, pass the
                         source object ID  (hence "PatientId")
  - context definitions: append "Id" to the developer name, pass the
                         context ID
```

**Detection hint:** Any expression-set invocation in a pricing, rating,
premium, or eligibility path that omits `options.effectiveDate`. Ask the
question that exposes it: "if this quote is recalculated in six months, must it
produce the same number?" If yes and `effectiveDate` is absent, it will not.
