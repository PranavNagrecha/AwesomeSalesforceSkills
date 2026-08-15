# Data Mapper Transform Audit Worksheet

One per Transform under investigation. Fill sections 1 and 2 **before** changing
anything — an optimization with no before-profile cannot be defended and will be
reversed by the next person.

Salesforce renamed DataRaptor to Omnistudio Data Mapper; this worksheet covers
the Transform type only.

---

## 1. Context — answer before reading the mappings

- Data Mapper name:
- Runtime:
  - [ ] Managed package (Vlocity lineage, `vlocity_*` namespaces, DataPacks)
  - [ ] Standard (Salesforce standard objects, Metadata API)
- Invoked from:
  - [ ] Integration Procedure — name and step position:
  - [ ] OmniScript
  - [ ] Apex — class and method:
  - [ ] REST / external caller
- If invoked from Apex, which API is the call site using?
  - [ ] `vlocity_*.DRGlobal.processObjectsJSON()` (managed package)
  - [ ] `ConnectApi.OmniDesignerConnect.executeDataMapper()` (standard)
  - > If the org is on the standard runtime and the call site is the first
  > option, fix that **before** profiling. Salesforce documents up to 60% better
  > performance for the swap, so a baseline taken on the old call site is not
  > comparable to anything measured afterwards.
- Enclosing transaction is:
  - [ ] Synchronous (10,000 ms CPU / 6 MB heap)
  - [ ] Asynchronous (60,000 ms CPU / 12 MB heap)

## 2. Before-profile — at PRODUCTION row and field counts

Not the designer preview. Three rows measure fixed overhead and nothing that
scales.

| Measure | Value | Source |
|---|---|---|
| Input rows | | production sample |
| Input fields per row | | production sample |
| Output fields per row | | |
| Transform wall-clock | | IP timing output |
| **Transaction** CPU total | | Apex debug log |
| **Transaction** peak heap | | Apex debug log |
| Transaction SOQL used | | Apex debug log |
| CPU spent BEFORE this Transform | | Apex debug log |

- Failure mode observed, verbatim from the exception:
  - [ ] CPU time → the cost is expressions. Fix: fewer, cheaper evaluators.
  - [ ] Heap → the cost is materialization. Fix: project upstream, merge steps.
  - [ ] SOQL → a custom function is querying per row.
  - [ ] None — it is slow but not failing.
- Does the transaction have room for a Transform improvement to matter?
  (If CPU-before-Transform is already near the limit, the answer is no and the
  work belongs elsewhere.)

## 3. Chain map

| # | Transform / step name | Consumed by | Can merge with previous? | Reused elsewhere? |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

- Adjacent steps with no consumer between them:
- Of those, which compose cleanly (no explanatory comment required)?
- Steps reused by another Integration Procedure (**cannot** be merged away):

## 4. Field-evaluator audit

Cheapest first: direct mapping → Transform Map Values → formula → custom function
into Apex. Demote every row as far as it will go.

| Input JSON Path | Output JSON Path | Current evaluator | Cheapest sufficient | Read by any consumer? | Action |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

- Mappings whose output no consumer reads (delete these first):
- Mappings using a custom function that a formula could express:
- Custom functions performing SOQL or DML (each is one per row):

## 5. List handling

- [ ] Any output path receiving **more than one** input list?
  - If yes: replaced with a `LIST(...)` formula? Direct multi-list mappings have
    no guaranteed output order.
- [ ] List outputs declare output data type `List<Map>`
- [ ] Ordering requirements written down, so the next reader knows the formula is
      load-bearing rather than decorative

## 6. Upstream payload

- Fields arriving at the Transform:
- Fields the output plus all formulas actually read:
- Ratio (arriving ÷ used):
- [ ] Extract narrowed to the used field list
- [ ] Paging considered, if the payload cannot fit the synchronous budget at all

## 7. Bulk-Apex plan

| Per-row custom function | Rows at peak | Queries per call | Replace with one array-level step? |
|---|---|---|---|
| | | | |

- New step position in the Integration Procedure (must be **before** the
  Transform, so the Transform maps a field that is already present):

## 8. Changes made

| # | Change | Rationale | Measured delta |
|---|---|---|---|
| 1 | | | |
| 2 | | | |

## 9. After-profile

| Measure | Before | After | Delta |
|---|---|---|---|
| Transform wall-clock | | | |
| Transaction CPU total | | | |
| Transaction peak heap | | | |
| Transaction SOQL used | | | |

## 10. Sign-Off

- [ ] Runtime and call-site API recorded
- [ ] Apex call sites on the standard runtime use the Connect API
- [ ] Before- and after-profiles taken at production row and field counts
- [ ] Failure mode (CPU vs heap) identified before choosing the fix
- [ ] Every mapping sits at the cheapest evaluator that can express it
- [ ] No mapping produces output nothing reads
- [ ] Multi-list merges use a `LIST()` formula; output type is `List<Map>`
- [ ] No custom function performs SOQL or DML per row
- [ ] Merges avoided where a step is reused, or where the result needs explaining
- [ ] Nothing was written to `OmniDataTransform` / `OmniDataTransformItem`
- [ ] Each delta attributed to a specific change, so the next reader can tell
      which change earned which improvement
