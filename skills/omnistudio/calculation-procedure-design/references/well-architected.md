# Well-Architected Notes — Calculation Procedure Design

## Relevant Pillars

- **Adaptable** — the headline win. A rate card in a Calculation Matrix is
  owned, versioned, and revised by the business on its own schedule. The same
  card as an Apex if-else ladder needs a developer, a deployment, and a test run
  for every revision. This is the pillar that justifies the design to a product
  owner.
- **Resilient** — version selection by `IsEnabled` / `IsActive` +
  `[StartDateTime, EndDateTime]` + `Rank` preserves historical correctness for
  free. A decision made in January remains reproducible in June without anyone
  having built a snapshotting mechanism, provided nobody edited a live version.
- **Performant** — a matrix lookup beats a code path for tabular rules, and
  keeps the procedure's step count low. The counterweight is that nothing
  memoizes procedure results, so a hot UI path needs a cached Integration
  Procedure in front of it.
- **Trusted** — in pricing, rating, and eligibility the requirement is not only
  a correct number but a *defensible* one. `ExpressionSetVersion` carries
  `ShouldShowExplExternally` and the Connect REST options include
  `explainabilitySpecName`, which means explainability is a first-class part of
  the platform's model rather than something to bolt on.

## Architectural Tradeoffs

- **Matrix vs procedure steps vs Apex.** Matrix for lookups, procedure steps for
  the arithmetic that combines them, Apex only for genuine iteration, recursion,
  or mid-computation callouts. The tell that logic is in the wrong layer: an
  Apex branch condition that is a business value (a region, a tier, an age band)
  rather than control flow.
- **Standard vs Grouped matrices.** `MatrixType` = `Grouped` with
  `GroupKey`/`SubGroupKey` lets each partition version, date, and rank
  independently inside one matrix definition — EMEA publishes without touching
  NA. `Standard` is right when the dimensions are genuinely independent lookup
  inputs. The discriminator: if a row could sensibly wildcard on that dimension,
  it is an input column, not a group key.
- **Effective dates vs rank overrides.** Dates express the *plan* (a scheduled
  rate change); `Rank` expresses the *override* (a correction to a live
  version). Teams that use dates for both end up editing enabled versions,
  which is where audit trails go to die. Leave rank gaps (10, 20, 30) so a
  correction can slot in without renumbering.
- **Many small matrices vs one large one.** Small matrices review and diff
  cleanly but multiply lookup steps and activation coordination — and activation
  order across referenced artifacts is not managed for you. Large matrices are
  easier to reason about at a glance and harder to review line by line.
  Grouped matrices are frequently the right middle.
- **Wildcard fallback vs explicit raise.** A wildcard row means every input
  produces a number, which is operationally smooth and hides genuinely unknown
  inputs. An explicit raise surfaces them and interrupts the user. Choose by
  blast radius: a wrong price is worse than a blocked quote in most regulated
  lines, and better than one in most self-service ones.
- **Caching vs freshness.** Wrapping the procedure call in a Cache Block cuts
  UI latency, but Platform Cache's 5-minute TTL floor means a rate whose
  freshness contract is tighter than that should not be cached at all — see
  `omnistudio/integration-procedure-cacheable-patterns`.

## Matrix Hygiene

- Wildcards: `IsWildcardColumn = true` **and** a set `WildcardColumnValue` on
  every column carrying a fallback token. A fallback row on a column that has
  not opted in is a dead row.
- Ranges: one `NumberRange` / `TextRange` column per dimension with declared
  `RangeValues`, not Min/Max column pairs.
- Versions: distinct, gapped `Rank` values. No two enabled versions sharing a
  rank in an overlapping window.
- Loads: enablement gated on `LoadProcessStatus = 'Completed'` (not on absence
  of `Failed`), plus a `CalculationMatrixRow` count assertion against the source
  CSV.
- Activation order: leaves before roots — matrices and sub-expression-sets
  before the procedures that reference them.
- Runtime contract recorded per version: `DecimalScale`, `ExecutionScale`, and
  whether callers pass `options.effectiveDate`.
- Fixtures in source control next to the matrix CSV, including one case per band
  boundary, one case that must hit the wildcard, and one single-element
  collection case for any aggregation step.

## Official Sources Used

- **ExpressionSet — Industries Common Resources Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/sforce_api_objects_expressionset.htm
  — source for the object's availability (API version 55.0 and later), its
  supported calls, and the fields `ApiName`, `Description`, `ExecutionScale`
  (restricted picklist, High / Low), `ExpressionSetDefinitionId` (required),
  `Name`, `OwnerId`, `Type` (Custom / Standard), and `UsageType` (defaults to
  `Bre` when Business Rules Engine is enabled). Verified 2026-08-14.
- **ExpressionSetVersion — Public Sector Solutions Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.psc_api.meta/psc_api/sforce_api_objects_expressionsetversion.htm
  — source for `IsActive` (default false), `Rank`, `StartDateTime`,
  `EndDateTime`, `VersionNumber`, `DecimalScale`, `LatestSimulationResult`
  ("JSON-formatted simulation results"), `IsLoopingEnabled` with
  `LoopStartVariableName` / `LoopIncrementVariableName` / `LoopEndVariableName`,
  `ShouldShowExplExternally`, and `ExpressionSetDefinitionVerId`. Also the
  load-bearing negative: **this object has no `Status` field.** Verified
  2026-08-14.
- **CalculationMatrixVersion — Public Sector Solutions Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.psc_api.meta/psc_api/sforce_api_objects_calculationmatrixversion.htm
  — source for `IsEnabled` ("Specifies whether this version is active",
  default false — and the absence of an `IsActive` field), `Rank` and its
  verbatim selection rule, `StartDateTime` / `EndDateTime`, `MatrixType`
  (Standard or Grouped), `GroupKey` / `GroupKeyValue` / `SubGroupKey` /
  `SubGroupKeyValue`, `LoadProcessStatus` (Completed, CompletedWithErrors,
  Failed, InProgress, Pending), `ApiName` (API 56.0 and later),
  `CalculationMatrixId`, and `VersionNumber`. Verified 2026-08-14.
- **CalculationMatrixColumn — Public Sector Solutions Developer Guide (API 67.0)** —
  https://developer.salesforce.com/docs/atlas.en-us.psc_api.meta/psc_api/sforce_api_objects_calculationmatrixcolumn.htm
  — source for `ColumnType` (restricted picklist: Input, Output), `DataType`
  (restricted picklist: Boolean, Currency, Number, NumberRange, Percent, Text,
  TextRange), `IsWildcardColumn` ("Specifies that this column can contain a
  wildcard value such as ALL", default false), `WildcardColumnValue` ("The
  value that indicates a wildcard, for example ALL"), `RangeValues` ("A list of
  values that define range boundaries"), and `DisplaySequence`. Verified
  2026-08-14.
- **Expression Set Invocation (POST) — Industries Common Resources Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/connect_resources_bre_expression_set.htm
  — source for the resource path
  `/connect/business-rules/expressionSet/${expressionSetName}`, the POST
  method, availability since API version 55.0, the request schema (`inputs` as
  `Map<String, Object>[]`, required; `options` with `effectiveDate`,
  `useDatesOnly`, `actionContextCode`, `explainabilitySpecName`), the Business
  Rules Result response type, the worked example body, and the field-alias /
  context-definition `Id`-suffix conventions. Verified 2026-08-14.
- **Expression Set (parent topic) and Expression Set Standard Objects —
  Industries Common Resources Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/expression_set_parent.htm
  and .../expression_set_standard_objects.htm
  — source for the definition of an expression set ("a series of steps
  connected in a logical flow built from variables, constants, conditions,
  calculations, lookups, and aggregations"), and for `ExpressionSetView`
  ("read-only templates that must be cloned before modification") and
  `ExpsSetObjectAliasFieldVw` (source objects, aliases and fields, "for
  permission verification purposes"). Verified 2026-08-14.
- **Expression Set Invocable Actions — Industries Common Resources Developer Guide** —
  https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/expression_set_invocable_actions.htm
  — source for the "Invoke an active expression set" invocable action as the
  Flow-facing surface. Verified 2026-08-14.
- **Master Integration Procedure Designer Elements — Trailhead** —
  https://trailhead.salesforce.com/content/learn/modules/omnistudio-integration-procedure-fundamentals/explore-integration-procedure-designer-elements
  — source for the two OmniStudio-facing invocation actions: **Expression Set**
  ("Invokes Expression Sets and returns results") and **Decision Matrix**
  ("Calls Decision Matrices with specified inputs"). Verified 2026-08-14.
- **Salesforce Well-Architected** — https://architect.salesforce.com/well-architected/overview
  — framing for the Adaptable / Resilient / Trusted pillar notes above.

### Sources deliberately not used

The Salesforce Help articles on Calculation Procedures, Calculation Matrices,
and Expression Sets (`os_calculation_procedures`, `os_calculation_matrices`,
`ind.expression_sets`, `build_your_expression_set`) are canonical prose for this
topic, but `help.salesforce.com` renders no article text to a document fetcher,
so nothing from them is quoted here. Every field name, picklist value, and
limit in this package is grounded in the object reference or the Industries
Common Resources Developer Guide instead. Where the object reference documents a
field but not its exact semantics — notably the serialization and inclusivity
convention of `RangeValues` — the gap is marked inline with `<!-- UNVERIFIED -->`
rather than filled in by inference.
