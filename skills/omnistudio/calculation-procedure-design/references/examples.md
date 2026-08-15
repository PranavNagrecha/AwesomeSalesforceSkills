# Calculation Procedure — Examples

Every object name, field name, and picklist value below is quoted from the
Salesforce object reference for the Business Rules Engine objects
(`ExpressionSet`, `ExpressionSetVersion`, `CalculationMatrix`,
`CalculationMatrixVersion`, `CalculationMatrixColumn`) at API 67.0, or from the
Industries Common Resources Developer Guide. The vocabulary matters here more
than usual: the designer labels ("Calculation Procedure", "Calculation Matrix")
and the API names (`ExpressionSet`, `CalculationMatrix` — labelled *Decision
Matrix* in the object reference) diverge, and half the mistakes in this domain
come from mixing them.

---

## Example 0: The Names, Reconciled

**Context:** Three vocabularies describe the same two artifacts, and every doc
search returns a mixture.

| Designer label | API object | Version object | Since |
|---|---|---|---|
| Calculation Procedure | `ExpressionSet` | `ExpressionSetVersion` | API 55.0 |
| Calculation Matrix | `CalculationMatrix` (object reference labels it **Decision Matrix**) | `CalculationMatrixVersion` | API 53.0 |
| — | `CalculationMatrixColumn` | — | API 53.0 |

Supporting objects worth knowing exist:

- `ExpressionSetDefinitionId` on `ExpressionSet`, and
  `ExpressionSetDefinitionVerId` on `ExpressionSetVersion` — a definition layer
  sits above both, and both references are **required**.
- `ExpressionSetView` — "a consolidated view of file-based expression sets,
  which function as **read-only templates that must be cloned before
  modification**."
- `ExpsSetObjectAliasFieldVw` — "a consolidated view of source objects, their
  aliases, and associated fields with aliases used in expression sets, **for
  permission verification purposes**." This is the object to query when
  answering "which fields does this expression set actually touch, and can this
  user read them?"

**Why it works:** Every downstream fact — which field activates a version,
which field breaks a tie, how a wildcard is expressed — is stated in the object
reference, and you cannot look it up under the designer's name.

---

## Example 1: Activation Is A Different Field On Each Object

**Context:** A procedure returns null in production. Both the procedure and its
matrix "look activated" in the designer.

**Problem:** The two objects use **different field names, with different
semantics**, for what the UI presents as one concept:

| Object | Activation field | Type | Documented meaning |
|---|---|---|---|
| `ExpressionSetVersion` | **`IsActive`** | boolean, default `false` | active status |
| `CalculationMatrixVersion` | **`IsEnabled`** | boolean, default `false` | "Specifies whether this version is active." |

There is **no `Status` field** on `ExpressionSetVersion`, and no `IsActive` on
`CalculationMatrixVersion`. Any code, query, or deployment script that assumes
one name works on both silently reads a nonexistent field — or, worse, compiles
against the wrong object and reports a version as active when it is not.

**Solution — a verification query you can run before blaming the logic:**

```sql
-- Is the procedure version live?
SELECT Id, Name, VersionNumber, IsActive, StartDateTime, EndDateTime, Rank
FROM   ExpressionSetVersion
WHERE  ExpressionSetId = :expressionSetId
ORDER  BY VersionNumber DESC

-- Is the matrix version live, and which one wins right now?
SELECT Id, Name, VersionNumber, IsEnabled, StartDateTime, EndDateTime,
       Rank, MatrixType, LoadProcessStatus
FROM   CalculationMatrixVersion
WHERE  CalculationMatrixId = :matrixId
ORDER  BY Rank DESC, VersionNumber DESC
```

**Why it works:** It converts "it looks active" into a fact, and it surfaces
`LoadProcessStatus` at the same time — see Example 5.

---

## Example 2: Wildcards Are Configured Per Column, Not Written As `*`

**Context:** A pricing matrix needs a fallback row for regions that have no
specific rate.

**Problem — the version almost everyone writes first:**

| Region | ProductTier | BasePrice |
|---|---|---|
| NA | Gold | 100 |
| NA | `*` | 60 |
| `*` | `*` | 50 |

This assumes `*` is a magic token the platform understands. It is not. A
wildcard is a **column-level opt-in with an explicitly configured value**:

| `CalculationMatrixColumn` field | Type | Documented meaning |
|---|---|---|
| `IsWildcardColumn` | boolean, default `false` | "Specifies that this column can contain a wildcard value such as ALL." |
| `WildcardColumnValue` | string | "The value that indicates a wildcard, for example ALL." |

So the wildcard token is whatever *you* set `WildcardColumnValue` to, on each
column where you set `IsWildcardColumn` to `true`. A column that has not opted
in treats every value as a literal — including `*`, which will simply never
match a real region.

**Solution:**

```text
CalculationMatrixColumn: Region
    ColumnType          = Input
    DataType            = Text
    IsWildcardColumn    = true
    WildcardColumnValue = 'ALL'
    DisplaySequence     = 1

CalculationMatrixColumn: ProductTier
    ColumnType          = Input
    DataType            = Text
    IsWildcardColumn    = true
    WildcardColumnValue = 'ALL'
    DisplaySequence     = 2

CalculationMatrixColumn: BasePrice
    ColumnType          = Output
    DataType            = Currency
    DisplaySequence     = 3
```

Rows then use the configured token:

| Region | ProductTier | BasePrice |
|---|---|---|
| NA | Gold | 100 |
| NA | ALL | 60 |
| ALL | ALL | 50 |

**Why it works:** The fallback is now a real match rather than a literal string
nobody sends. And because the opt-in is per column, you can permit a wildcard on
`Region` while requiring an exact `ProductTier` — which is usually what the
business actually meant.

---

## Example 3: Ranges Are A Column Data Type, Not A Pair Of Min/Max Columns

**Context:** An insurance rating matrix banded on driver age and prior claims.

**Problem — the hand-rolled version:**

| DriverAgeMin | DriverAgeMax | PriorClaimsMin | PriorClaimsMax | BaseRate |
|---|---|---|---|---|
| 16 | 24 | 0 | 0 | 1.80 |
| 25 | 64 | 0 | 0 | 1.00 |

Four input columns to express two dimensions. It works only if the procedure
does the comparison itself, and it doubles the surface where an off-by-one
lands.

**Solution — the platform models ranges as a column data type.**
`CalculationMatrixColumn.DataType` is a restricted picklist with exactly these
values:

```text
Boolean | Currency | Number | NumberRange | Percent | Text | TextRange
```

`NumberRange` and `TextRange` are range types. The boundaries live in:

| Field | Type | Documented meaning |
|---|---|---|
| `RangeValues` | textarea | "A list of values that define range boundaries." |

So the same matrix becomes two input columns:

```text
CalculationMatrixColumn: DriverAge
    ColumnType   = Input
    DataType     = NumberRange
    RangeValues  = 16, 25, 65, 121      <- boundaries, not pairs

CalculationMatrixColumn: PriorClaims
    ColumnType   = Input
    DataType     = NumberRange
    RangeValues  = 0, 1, 3, 100

CalculationMatrixColumn: BaseRate
    ColumnType   = Output
    DataType     = Number
```

| DriverAge | PriorClaims | BaseRate |
|---|---|---|
| 16–24 | 0 | 1.80 |
| 16–24 | 1–2 | 2.50 |
| 25–64 | 0 | 1.00 |
| 25–64 | 1–2 | 1.25 |
| 65–120 | 0–99 | 1.20 |

**Why it works:** Boundaries are declared once, so the bands cannot overlap or
leave a gap by construction — the failure mode that hand-rolled Min/Max columns
exist to produce. Half the column count, and the comparison moves out of your
procedure steps.

<!-- UNVERIFIED: the object reference documents RangeValues as "a list of
values that define range boundaries" but does not state the exact serialization
(delimiter, whether boundaries are inclusive of the lower or upper edge, or how
the first and last bands are open-ended). Confirm the boundary convention
against a live matrix before relying on edge behaviour at 24/25 and 64/65. -->

---

## Example 4: Version Selection Is Date-Range Plus Rank — And Rank Is The Tiebreaker

**Context:** A rate change takes effect on 1 January. Two matrix versions must
coexist across the boundary.

**Problem:** Teams assume overlapping effective ranges are undefined behaviour.
They are not — the platform defines the resolution explicitly, and the
mechanism is worth using rather than avoiding.

`CalculationMatrixVersion.Rank`, verbatim:

> "When the invocation time of a matrix call is between the `StartDateTime` and
> `EndDateTime` of more than one **enabled** matrix version, the version with
> the highest `Rank` is chosen."

Three conditions therefore gate selection: `IsEnabled` = true, the invocation
time falls inside `[StartDateTime, EndDateTime]`, and among the survivors the
highest `Rank` wins.

`ExpressionSetVersion` carries the same three fields — `IsActive`,
`StartDateTime`, `EndDateTime`, `Rank` — so procedure versions select the same
way.

**Solution — the boundary crossing, done deliberately:**

```text
CalculationMatrixVersion  v6
    IsEnabled      = true
    StartDateTime  = 2026-01-01T00:00:00Z
    EndDateTime    = 2026-12-31T23:59:59Z
    Rank           = 10

CalculationMatrixVersion  v7                (the new rates)
    IsEnabled      = true
    StartDateTime  = 2027-01-01T00:00:00Z
    EndDateTime    = null                   (open-ended)
    Rank           = 20
```

Non-overlapping dates mean `Rank` never has to adjudicate — which is the
design you want for a routine schedule change.

**Where `Rank` earns its keep** is the emergency correction: v7 ships with a
wrong rate at 09:00 on 2 January. Rather than editing v7 in place — which
changes history — publish v8 with the same `StartDateTime` and a higher `Rank`:

```text
CalculationMatrixVersion  v8                (the correction)
    IsEnabled      = true
    StartDateTime  = 2027-01-01T00:00:00Z
    EndDateTime    = null
    Rank           = 30                     <- outranks v7, same window
```

v7 remains enabled and auditable; v8 wins every lookup from now on. Setting
`IsEnabled = false` on v7 would also work, but destroys the record that it was
ever live.

**Why it works:** Effective dates express the *plan*; `Rank` expresses the
*override*. Using dates for both is what forces people into destructive edits.

---

## Example 5: The Matrix That Loaded Halfway

**Context:** New rates uploaded from CSV. Spot checks pass. A subset of
customers is quoted at the old rate for a week.

**Problem:** `CalculationMatrixVersion.LoadProcessStatus` is a restricted
picklist describing the CSV upload:

```text
Completed | CompletedWithErrors | Failed | InProgress | Pending
```

`CompletedWithErrors` is the dangerous one. The load reports as *completed*, the
version is enabled, and an unknown subset of rows never landed. Nothing about
the runtime behaviour signals it — a missing row is indistinguishable from a
row that legitimately falls through to the wildcard.

**Solution — gate activation on the load status, not on the upload finishing:**

```sql
SELECT Id, Name, VersionNumber, LoadProcessStatus, IsEnabled
FROM   CalculationMatrixVersion
WHERE  CalculationMatrixId = :matrixId
AND    LoadProcessStatus != 'Completed'
```

Any row returned is a version that must not be enabled. Add a row-count
assertion alongside it: the number of `CalculationMatrixRow` records for the
version should equal the number of data rows in the source CSV. A count
mismatch is the only reliable detector of a partial load, because the platform
does not tell you which rows failed at query time.

**Why it works:** It moves the check from "did the upload finish" — which
`CompletedWithErrors` satisfies — to "did every row arrive," which it does not.

---

## Example 6: Invoking An Expression Set — The Four Documented Surfaces

**Context:** "How do I call this from code?" is where models fabricate most
freely in this domain.

**Solution — the surfaces Salesforce documents:**

**1. Connect REST API** — the one to use from outside the platform:

```http
POST /services/data/v67.0/connect/business-rules/expressionSet/${expressionSetName}
Content-Type: application/json
```

```json
{
  "inputs": [{
    "age": "25",
    "state": "CA",
    "PatientId": "001xx000003GYjnAAG"
  }],
  "options": {
    "effectiveDate": "2022-12-03T10:15:30Z",
    "useDatesOnly": "true",
    "actionContextCode": "9QLxx0000004C92GAE"
  }
}
```

| Property | Type | Required | Meaning |
|---|---|---|---|
| `inputs` | `Map<String, Object>[]` | yes | "List of inputs passed to an expression set. An input may contain multiple variables." |
| `options.effectiveDate` | string (ISO 8601) | no | the timestamp version selection is evaluated against |
| `options.useDatesOnly` | string | no | |
| `options.actionContextCode` | string | no | |
| `options.explainabilitySpecName` | string | no | |

Available since **API version 55.0**. The response is a *Business Rules Result*.

Two conventions in the request body that are easy to get wrong: for **field
aliases**, append `Id` to the object alias and pass the source object ID (hence
`PatientId` above); for **context definitions**, append `Id` to the developer
name and pass the context ID.

`options.effectiveDate` is the lever that makes back-dated calculation correct:
it lets you evaluate against the version that was live on the quote's issue
date rather than the version live today.

**2. Flow** — the "Invoke an active expression set" invocable action.

**3. Integration Procedure** — two distinct designer actions:

- **Expression Set** — "Invokes Expression Sets and returns results"
- **Decision Matrix** — "Calls Decision Matrices with specified inputs"

Use the Decision Matrix action when you need a raw lookup with no surrounding
procedure logic; it skips a layer.

**4. Apex** — via the invocable action, or by calling the Connect REST resource
over a Named Credential.

**What does not exist:** there is no `ConnectApi.EvaluationService` class and no
`executeExpression()` method. The `ConnectApi` namespace has many `*Service`
classes, which makes `ConnectApi.<Domain>Service.<verb>()` a productive-looking
template — but Business Rules Engine has Connect *REST* resources without a
mirrored Apex class. See `references/llm-anti-patterns.md`.

**Why it works:** Each surface has a documented contract, and the REST one in
particular gives you `effectiveDate`, which no amount of Apex cleverness
replaces.

---

## Example 7: Simulation Results Are Stored On The Version

**Context:** Regression-testing a rate change.

**Solution:** `ExpressionSetVersion.LatestSimulationResult` is a textarea
holding "JSON-formatted simulation results." The platform's own test run is
therefore queryable, not just viewable in the designer.

```sql
SELECT Id, Name, VersionNumber, IsActive, LatestSimulationResult
FROM   ExpressionSetVersion
WHERE  ExpressionSetId = :expressionSetId
AND    VersionNumber = :candidateVersion
```

Note the field name: **Latest**SimulationResult. It holds one result, and each
run overwrites it. It is a convenience for the last run, not a test history —
so keep your own fixture set in source control and diff against it. Store the
fixture as a JSON file next to the matrix CSV so the two move together.

Two related fields shape what a simulation is comparing:

- `ExpressionSetVersion.DecimalScale` (int) — decimal places for non-local
  resources such as context tags. A fixture that passes at one `DecimalScale`
  and fails at another is a rounding-configuration difference, not a logic bug.
- `ExpressionSet.ExecutionScale` — a restricted picklist (`High` / `Low`)
  specifying execution scope for input processing.

**Why it works:** Testing that reads from the platform's own stored result
compares like with like, and knowing `DecimalScale` exists prevents an
afternoon spent debugging a rounding difference as if it were a rule error.

---

## Example 8: Grouped Matrices — When One Matrix Is Really Twelve

**Context:** The same rate structure repeats per region, and each region's
rates change on its own schedule.

**Solution:** `CalculationMatrixVersion.MatrixType` is "either **Standard** or
**Grouped**." A grouped matrix partitions rows by key:

| Field | Documented meaning |
|---|---|
| `GroupKey` | "A key for grouping matrix rows in different versions, such as geographic region or product code." |
| `GroupKeyValue` | the value assigned to the `GroupKey` for a specific version |
| `SubGroupKey` | "A subkey for grouping matrix rows in different versions" |
| `SubGroupKeyValue` | the value assigned to the `SubGroupKey` for a specific version |

`GroupKey`/`SubGroupKey` are read-only (Filter, Group, Nillable, Sort); the
`*Value` fields are createable and updateable.

**Why this beats twelve separate matrices:** each region's rows become a
separately versioned, separately dated, separately rankable unit *within one
matrix definition*. EMEA can publish a new version on its own schedule without
touching NA's rows, and the procedure keeps referencing one matrix. Twelve
matrices means twelve lookup steps and twelve activation coordinations.

**When to stay Standard:** when the dimensions are genuinely independent inputs
rather than partitions of one rate structure. Region as a `GroupKey` says "the
same rules, different numbers per region." Region as an *input column* says
"region participates in the lookup." If a row could sensibly wildcard on region,
it is an input column, not a group key.

---

## Anti-Pattern: Editing An Enabled Matrix Version To Fix A Rate

**What practitioners do:** open the live version, correct the wrong number,
save. It is one click and it works immediately.

**What goes wrong:** the version's identity no longer matches its history. Any
quote, premium, or eligibility decision produced before the edit was computed
from a matrix that no longer exists anywhere, and the audit trail points at the
edited version as if it had always held the corrected value. In a regulated
line of business that is not a documentation gap — it is an unreproducible
decision.

**Correct approach:** publish a new version with the same `StartDateTime` and a
higher `Rank`, as in Example 4. The prior version stays `IsEnabled = true` and
auditable; the new one wins every lookup from the moment it is enabled. The
cost is one extra version record. The benefit is that "what rate did we quote
on 3 January" remains answerable.
