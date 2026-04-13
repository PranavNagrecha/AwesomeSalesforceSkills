# Examples — Analytics Data Architecture

## Example 1: Simulating Incremental Recipe Processing via Snapshot-Join Technique

**Context:** A financial services org runs a daily Recipe that refreshes a `Service_Case_Analytics` dataset from 8 million Case records. Each full Recipe run takes 45 minutes and consumes a run slot from the org's 60-run rolling window. The business requires the dataset refreshed every 4 hours during business hours — a schedule that would exhaust the run budget entirely on this one dataset alone.

**Problem:** CRM Analytics Recipes do not support native incremental loads. Every Recipe run reads the full input dataset from scratch. Without a workaround, the org cannot achieve 4-hour refresh cycles at this data volume within the run budget.

**Solution:**

The snapshot-join technique creates a self-referencing Recipe that maintains a prior-run dataset and unions only the changed rows on subsequent runs.

Step 1 — Seed the initial snapshot (first run only):

```
Recipe: Case_Analytics_Full_Seed
Input: Case (Salesforce object, full sync)
  → Filter: CreatedDate >= 2020-01-01
  → Formula: snapshot_date = toDate(now(), "yyyy-MM-dd")
Output: case_snapshot (write mode: overwrite)
```

Step 2 — Subsequent runs use snapshot-join logic:

```
Recipe: Case_Analytics_Incremental
Input A: Case (Salesforce object, full sync)
Input B: case_snapshot (CRM Analytics dataset — prior run output)

Step 1 — Join A to B on CaseNumber (left outer)
  → Formula: is_changed = (Case.LastModifiedDate > case_snapshot.snapshot_date)

Step 2 — Split into two branches:
  Branch "changed": Filter where is_changed = true
    → Select fields from live Case source
    → Formula: snapshot_date = toDate(now(), "yyyy-MM-dd")

  Branch "unchanged": Filter where is_changed = false
    → Select same fields from case_snapshot
    → (snapshot_date carries forward from prior snapshot)

Step 3 — Append "changed" + "unchanged"

Step 4 — Output: case_snapshot (overwrite)
```

**Why it works:** Each run only physically processes the union append, not a full re-read of the business logic. The majority of rows come from the prior snapshot (already stored), so runtime drops from 45 minutes to 3–5 minutes. Run slot consumption is the same (one slot per run), but the shortened runtime frees the window for other refreshes. The snapshot_date comparison correctly identifies rows modified since the last run.

**Key constraint:** The schema of the Recipe output must exactly match the schema of the `case_snapshot` dataset it reads. Any schema drift (new fields, renamed fields) requires a full-seed re-run before resuming incremental processing.

---

## Example 2: Architecting ELT to Push Transforms into Dataflow and Avoid SAQL Runtime Overhead

**Context:** A sales operations team reports that their CRM Analytics pipeline dashboard is slow — charts take 8–12 seconds to render. Investigation reveals the SAQL powering the key pipeline chart performs a runtime join between the `Opportunity` dataset (1.2M rows) and the `Account` dataset (180K rows) to pull in Account Industry and Region for every user interaction.

**Problem:** SAQL joins execute at query time — for every dashboard render, every filter change, every user session. In a dataset with 1.2M rows joined to 180K rows at runtime, the query must perform a hash-join in memory on the analytics engine for each interaction. With 30+ concurrent users, this creates significant latency and inconsistent performance under load.

**Solution:**

Move the join into the dataflow as an Augment transformation so the denormalized dataset is written once per refresh cycle, not computed per user query.

Before (SAQL at runtime):
```saql
q = load "Opportunity";
a = load "Account";
q = cogroup q by 'AccountId', a by 'Id';
q = foreach q generate
    q.'Name' as 'Opportunity_Name',
    q.'Amount' as 'Amount',
    a.'Industry' as 'Industry',
    a.'BillingState' as 'Region';
```

After (Augment in dataflow JSON — runs once per refresh):
```json
{
  "opp_augmented": {
    "action": "augment",
    "parameters": {
      "left": "opp_extract",
      "right": "account_extract",
      "left_key": ["AccountId"],
      "right_key": ["Id"],
      "right_select": ["Industry", "BillingState"],
      "operation": "LookupSingleValue"
    }
  }
}
```

Updated SAQL (post-ELT — no join required):
```saql
q = load "opp_augmented";
q = group q by 'Industry';
q = foreach q generate 'Industry', sum('Amount') as 'Total_Amount';
q = order q by 'Total_Amount' desc;
q = limit q 10;
```

**Why it works:** The Augment runs once during the dataflow execution window (e.g., 02:00 AM daily). The output dataset `opp_augmented` is fully denormalized and stored. Dashboard SAQL now performs a simple group-by on a flat dataset — rendering time drops from 8–12 seconds to under 1 second. The join cost is paid once per refresh, not once per user interaction.

---

## Anti-Pattern: Claiming Recipes Process Only Changed Rows Without a Snapshot-Join

**What practitioners do:** Architects design a Recipe refresh schedule on the assumption that CRM Analytics Recipes detect and process only new or modified records — similar to how traditional ETL tools with CDC (change data capture) operate. They schedule Recipes to run every 30 minutes expecting minimal processing time.

**What goes wrong:** Every Recipe run reads the full input dataset from scratch. A Recipe connected to a 5M-row object will read all 5M rows on every run, regardless of how many records changed. A 30-minute schedule generates 48 Recipe runs per day — well over the 60-run rolling window when combined with other jobs — and each run takes as long as a full load. The system hits both the run limit and performance degradation simultaneously.

**Correct approach:** Use Data Sync incremental mode for Salesforce object sources in dataflows where true native incremental is required. For Recipes that must run frequently against large datasets, implement the snapshot-join technique to minimize the rows that need active transformation. Validate run schedules against the 60-run rolling window before finalizing any refresh cadence.
