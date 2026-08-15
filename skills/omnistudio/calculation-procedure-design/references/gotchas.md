# Calculation Procedure — Gotchas

Behaviour that produces a silently wrong number, an unreproducible decision, or
a version that looks live and is not. Field names and picklist values are from
the object reference for the Business Rules Engine objects at API 67.0.

---

## 1. The Activation Field Has A Different Name On Each Object

**What happens:** A deployment script, a validation query, or a health-check
report says a matrix version is active when it is not — or fails to compile
against a field that does not exist on the object it was pointed at.

**When it occurs:** Whenever one mental model is applied to both objects. They
genuinely differ:

| Object | Activation field | Notes |
|---|---|---|
| `ExpressionSetVersion` | **`IsActive`** (boolean, default `false`) | there is **no `Status` field** on this object |
| `CalculationMatrixVersion` | **`IsEnabled`** (boolean, default `false`) | "Specifies whether this version is active." No `IsActive` field. |

**How to avoid:** Never generalise from one to the other. Query both explicitly
in any pre-release check. The UI presents both as "activate," which is exactly
why the API-level difference goes unnoticed until something automated touches
it.

---

## 2. `*` Is Not A Wildcard — Wildcards Are Configured Per Column

**What happens:** A fallback row with `*` in the region column never matches.
Every unmatched input falls through to whatever the procedure does with a null
output, which is usually a cryptic downstream failure rather than a clean
error.

**When it occurs:** `*` is the wildcard convention in almost every rules engine
and every spreadsheet idiom, so it is what people write. On this platform the
wildcard is a **column-level opt-in with an explicitly configured token**:

- `CalculationMatrixColumn.IsWildcardColumn` (boolean, default `false`) —
  "Specifies that this column can contain a wildcard value such as ALL."
- `CalculationMatrixColumn.WildcardColumnValue` (string) — "The value that
  indicates a wildcard, for example ALL."

A column that has not opted in treats `*` as a literal string, and no real
input will ever equal it.

**How to avoid:** Set `IsWildcardColumn = true` and `WildcardColumnValue` on
every column that needs a fallback, and use *that* token in the rows. Being
per-column is a feature: permit a wildcard on `Region` while requiring an exact
`ProductTier`, which is usually what the business meant.

---

## 3. Ranges Are A Column `DataType`, Not A Pair Of Min/Max Columns

**What happens:** A matrix carries `AgeMin`/`AgeMax` input columns and the
procedure does the comparison in its own steps. It works, and it doubles the
surface for off-by-one errors while hiding the band structure from anyone
reading the matrix.

**When it occurs:** Porting a spreadsheet directly. The platform has first-class
range support:

`CalculationMatrixColumn.DataType` is a restricted picklist with exactly these
values:

```text
Boolean | Currency | Number | NumberRange | Percent | Text | TextRange
```

Boundaries go in `CalculationMatrixColumn.RangeValues` (textarea) — "a list of
values that define range boundaries."

**How to avoid:** Use `NumberRange` / `TextRange` with declared boundaries. One
column per dimension, bands that cannot overlap or gap by construction, and the
comparison out of your procedure steps.

<!-- UNVERIFIED: the object reference does not state RangeValues' exact
serialization — the delimiter, whether a boundary belongs to the band above or
below it, or how the first and last bands are bounded. Confirm the inclusivity
convention against a live matrix before relying on behaviour exactly at a
boundary value. -->

---

## 4. Overlapping Version Windows Are Resolved By `Rank`, Not Undefined

**What happens:** Teams avoid overlapping effective dates entirely because they
believe overlap is non-deterministic. It is not, and avoiding it costs them the
cleanest correction mechanism available.

**The documented rule**, verbatim from `CalculationMatrixVersion.Rank`:

> "When the invocation time of a matrix call is between the `StartDateTime` and
> `EndDateTime` of more than one **enabled** matrix version, the version with
> the highest `Rank` is chosen."

Selection is therefore three conditions: `IsEnabled` = true, invocation time
inside `[StartDateTime, EndDateTime]`, highest `Rank` among the survivors.
`ExpressionSetVersion` carries the same four fields and selects the same way.

**How to use it:** Non-overlapping dates for planned schedule changes; an
overlapping higher-`Rank` version for corrections. The alternative — editing the
live version — destroys the audit trail (see §5).

**The real hazard is equal ranks.** Two enabled versions with overlapping
windows and the *same* `Rank` have no documented tiebreaker. Assign distinct,
intentional ranks and leave gaps (10, 20, 30) so a correction can slot between
them without renumbering.

---

## 5. Editing An Enabled Version Destroys Reproducibility

**What happens:** A wrong rate is corrected in place on the live version. Every
decision made before the edit was computed from a matrix state that no longer
exists, and the audit trail now attributes the corrected value to the whole
period.

**When it occurs:** Under time pressure, because it is one click and it works.

**How to avoid:** Publish a new version with the same `StartDateTime` and a
higher `Rank`. The prior version stays enabled and auditable; the new one wins
every subsequent lookup. Setting `IsEnabled = false` on the old version also
works but erases the record that it was ever live — prefer the rank override
where the history matters, which in pricing, rating, and eligibility is always.

---

## 6. `CompletedWithErrors` Means A Partially Loaded Matrix

**What happens:** A CSV rate upload reports as finished. An unknown subset of
rows never landed. Quotes for the affected combinations fall through to the
wildcard row or return null.

**When it occurs:** `CalculationMatrixVersion.LoadProcessStatus` is a restricted
picklist:

```text
Completed | CompletedWithErrors | Failed | InProgress | Pending
```

`Failed` is loud. `CompletedWithErrors` is not — it reads as success in a
status column, and the runtime gives no signal, because a missing row is
indistinguishable from a row that legitimately falls through.

**How to avoid:** Gate enablement on `LoadProcessStatus = 'Completed'`, not on
the upload finishing. Add a row-count assertion — `CalculationMatrixRow` count
for the version must equal the source CSV's data-row count. The count check is
the only reliable partial-load detector, because the platform does not expose
which rows failed at query time.

---

## 7. `DecimalScale` Changes The Answer Without Changing The Rules

**What happens:** A fixture that passed in one org fails by a cent in another.
The rules are byte-identical.

**When it occurs:** `ExpressionSetVersion.DecimalScale` (int) specifies decimal
places for non-local resources such as context tags. Two versions of the same
logic with different `DecimalScale` values produce different rounded outputs.

**How to avoid:** Treat `DecimalScale` as part of the version's contract.
Include it in the fixture header, assert it in pre-release checks, and diff it
across environments — an unexplained penny difference between sandbox and
production is this field far more often than it is a rule change.

Related: `ExpressionSet.ExecutionScale` is a restricted picklist (`High` /
`Low`) specifying execution scope for input processing. Record it alongside
`DecimalScale` when documenting a procedure's runtime contract.

---

## 8. `LatestSimulationResult` Holds One Result, Not A History

**What happens:** A team treats the designer's stored simulation output as a
regression suite. Each run overwrites the previous one, so there is nothing to
compare against.

**When it occurs:** `ExpressionSetVersion.LatestSimulationResult` is a textarea
containing "JSON-formatted simulation results" — note **Latest**.

**How to avoid:** Keep your own fixture set in source control — input/expected
pairs as a JSON file stored next to the matrix CSV so the two move together —
and diff against it after every activation. Use `LatestSimulationResult` for
what it is: a queryable record of the most recent run, useful for confirming a
run happened and for pulling its output without opening the designer.

Test fixtures also do not validate schema: a renamed input simply matches no
row rather than raising. Assert on outputs, and include at least one case per
band boundary plus one case that must hit the wildcard.

---

## 9. Activation Order Across Referenced Artifacts Is Not Managed For You

**What happens:** A procedure is activated while a matrix it references — or a
sub-expression-set it calls — is not enabled. The failure surfaces at the
lookup step, at runtime, in production.

**When it occurs:** Activating a new version of one artifact does not
auto-activate anything it references. `ExpressionSetVersion` and
`CalculationMatrixVersion` have independent lifecycles, independent version
numbers, and independent effective dates.

**How to avoid:** Activate leaves first, roots last: matrices and
sub-expression-sets before the procedures that reference them. Then verify with
a single query per referenced artifact rather than trusting the designer's
green state — see `examples.md` Example 1 for the queries.

---

## 10. File-Based Expression Sets Are Read-Only Templates

**What happens:** Someone tries to edit a Salesforce-supplied expression set
directly and either cannot, or edits a copy without realising the original will
be replaced on upgrade.

**When it occurs:** `ExpressionSetView` provides "a consolidated view of
file-based expression sets, which function as **read-only templates that must
be cloned before modification**." `ExpressionSet.Type` is a restricted picklist
distinguishing `Custom` from `Standard`.

**How to avoid:** Clone before modifying, and record the source template and
version in the clone's `Description`. Check `Type` before treating any
expression set as yours to change.

---

## 11. Aggregation Over A Scalar Silently Aggregates One Item

**What happens:** A sum step returns the single input value instead of a total.
No error.

**When it occurs:** An aggregation step is passed a scalar where the caller
intended a collection — commonly because the calling Integration Procedure's
Data Mapper returned one record and the JSON collapsed to an object rather than
a one-element array.

**How to avoid:** Validate collection shape in the caller, not the procedure.
An IP that always returns a list — even a one-element list — removes the whole
class. Add a fixture whose input collection has exactly one element; it is the
case that distinguishes correct aggregation from an accidental pass-through,
and it is almost never in the fixture set.

---

## 12. Calculation Procedure Results Are Not Cached For You

**What happens:** A FlexCard or OmniScript calls a procedure on every input
change and the UI becomes unresponsive.

**When it occurs:** The procedure is invoked directly from a UI component
rather than through a cached read path. Nothing about the Business Rules Engine
memoizes results.

**How to avoid:** Call the procedure from an Integration Procedure and wrap the
call in a **Cache Block** when the inputs are stable — see
`omnistudio/integration-procedure-cacheable-patterns`. Two constraints from
that skill carry over directly: cache keys must be alphanumeric and ≤ 50
characters, and the minimum Platform Cache TTL is 5 minutes, so a procedure
whose freshness contract is tighter than that should not be cached at all.

---

## 13. Back-Dated Calculation Needs `effectiveDate`, Not "Today"

**What happens:** A quote reissued in March is priced with March's rates instead
of the rates in force on its original January issue date.

**When it occurs:** The caller does not pass an effective date, so version
selection evaluates against the invocation time.

**How to avoid:** The Connect REST resource accepts
`options.effectiveDate` — an ISO 8601 timestamp — precisely for this. Decide
early whether your domain requires it; retrofitting back-dating after the fact
means every caller changes. If the answer is yes, the business date (quote
issue date, policy effective date, claim date) becomes a required input on
every invocation path, not an optional one.
