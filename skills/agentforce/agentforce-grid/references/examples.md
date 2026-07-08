# Examples — Agentforce Grid

Agentforce Grid is a **no-code** Studio tool — there is no deployable metadata or Apex for a
worksheet. The examples below are therefore *design specs*: a compact JSON representation of a
worksheet's ordered columns that mirrors what you build in the Grid UI, plus the reasoning
behind each choice. The JSON shape matches `templates/grid-worksheet-spec.example.json` and is
lintable with `scripts/check_agentforce_grid.py`.

> Grid was introduced in Winter '26 and its setup is documented as **Beta** — treat behavior,
> limits, and UI as subject to change.

## Example 1: Bulk HTML → Markdown clean-up (Data → AI → Action)

**Context:** hundreds of Accounts have `Description` fields storing legacy HTML. You want clean
Markdown written back to each record.

**Problem:** doing this in Apex or Flow means building, testing, and deploying code for a
one-off bulk job. Grid runs it as a left-to-right pipeline, per row, no code.

**Solution (worksheet design):**

```json
{
  "workbook": "Account Description Cleanup",
  "worksheet": "HTML to Markdown",
  "beta_acknowledged": true,
  "billing_reviewed": true,
  "columns": [
    { "name": "Accounts", "type": "data", "source": "salesforce",
      "object": "Account", "fields": ["Id", "Description"],
      "filter": "Description != null", "maxResults": 200 },
    { "name": "Markdown", "type": "ai", "mode": "use-ai", "model": "GPT 5",
      "instruction": "Convert the HTML in the Description to clean Markdown.",
      "runForEachRow": true, "references": ["Accounts"] },
    { "name": "WriteBack", "type": "action", "action": "update-record",
      "object": "Account", "field": "Description", "references": ["Markdown"] }
  ]
}
```

**Why it works:** the leftmost **data column** imports only the fields needed with a filter and
a `maxResults` cap (bounding the job count and the cost). The **AI column** in *Use AI* mode
references `Accounts` and runs for each row. The **action column** (Update Record) references
the AI output and writes it back — every reference points to a column to its left, so the
left-to-right dependency chain is valid.

---

## Example 2: Read-only insight generation (Data → AI, no write-back)

**Context:** you want a one-line AI summary per Account for a review meeting, but you must not
mutate any CRM data.

**Problem:** adding an Update Record column would write data you didn't intend to change and
spend credits on writes you don't need.

**Solution:**

```json
{
  "workbook": "Account Insights",
  "worksheet": "Summaries",
  "beta_acknowledged": true,
  "billing_reviewed": true,
  "columns": [
    { "name": "Accounts", "type": "data", "source": "salesforce",
      "object": "Account", "fields": ["Id", "Name", "Industry", "AnnualRevenue"],
      "maxResults": 100 },
    { "name": "Summary", "type": "ai", "mode": "prompt-template",
      "template": "Account_Summary", "runForEachRow": true,
      "references": ["Accounts"] }
  ]
}
```

**Why it works:** no action column means the run is read-only. The AI column uses a reusable,
governed **prompt template** rather than an ad-hoc instruction. Inspect results in the Output
Preview (JSON view) — nothing is written back.

---

## Example 3: Data Cloud (Data 360) source

**Context:** the records to summarize live in a Data Cloud data model object, not a standard
object.

**Solution:** point the data column at the DMO — Grid data columns query standard Salesforce
objects *or* Data Cloud data model objects.

```json
{
  "workbook": "Unified Profile Insights",
  "worksheet": "Segment Summaries",
  "beta_acknowledged": true,
  "billing_reviewed": true,
  "columns": [
    { "name": "Profiles", "type": "data", "source": "data-cloud",
      "object": "UnifiedIndividual__dlm", "fields": ["Id__c", "Name__c"],
      "maxResults": 250 },
    { "name": "Insight", "type": "ai", "mode": "use-ai", "model": "GPT 5",
      "instruction": "Summarize the profile's engagement in one sentence.",
      "runForEachRow": true, "references": ["Profiles"] }
  ]
}
```

**Why it works:** `source: "data-cloud"` (Data 360) is a first-class data-column source
alongside `salesforce`. Everything downstream behaves the same.

---

## Example 4: Chained AI columns (Data → AI → AI → Action)

**Context:** you first extract a value with one AI step, then reformat it with a second, then
write the final result back.

**Solution:**

```json
{
  "workbook": "Case Tagging",
  "worksheet": "Extract and Normalize",
  "beta_acknowledged": true,
  "billing_reviewed": true,
  "columns": [
    { "name": "Cases", "type": "data", "source": "salesforce",
      "object": "Case", "fields": ["Id", "Description"], "maxResults": 200 },
    { "name": "RawTag", "type": "ai", "mode": "use-ai", "model": "GPT 5",
      "instruction": "Extract the primary product mentioned.",
      "runForEachRow": true, "references": ["Cases"] },
    { "name": "NormTag", "type": "ai", "mode": "use-ai", "model": "GPT 5",
      "instruction": "Map the product to the official picklist value.",
      "runForEachRow": true, "references": ["RawTag"] },
    { "name": "WriteTag", "type": "action", "action": "update-record",
      "object": "Case", "field": "Product__c", "references": ["NormTag"] }
  ]
}
```

**Why it works:** the second AI column references the first AI column (to its left), not the
data column — Grid lets any column consume any earlier column via the `@` picker. Cost here is
`rows × 3` model/action runs, which the Billing Calculator estimate should reflect.

---

## Anti-Pattern: referencing a column that hasn't run yet

**What practitioners do:** place an Update Record column *before* the AI column whose output it
should write, or reference a column to its right.

**What goes wrong:** columns process left to right; a column can only consume columns to its
left. A forward reference is unresolvable — the write-back has nothing to write.

```json
// WRONG — WriteBack (index 1) references Markdown (index 2), which runs later
{ "columns": [
  { "name": "Accounts", "type": "data", "source": "salesforce", "object": "Account" },
  { "name": "WriteBack", "type": "action", "action": "update-record",
    "object": "Account", "field": "Description", "references": ["Markdown"] },
  { "name": "Markdown", "type": "ai", "mode": "use-ai", "model": "GPT 5",
    "references": ["Accounts"] }
] }
```

**Correct approach:** order columns so every reference points left — data first, then the AI
step, then the action that writes its output. `check_agentforce_grid.py` flags forward and
unknown references.
