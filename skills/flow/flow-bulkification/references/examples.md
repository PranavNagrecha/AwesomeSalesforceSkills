# Examples — Flow Bulkification

## Example 1: Collect Then Update Related Records

**Context:** An after-save Opportunity flow must update related renewal `Task` records whenever the stage changes.

**Problem:** The original design loops through tasks and runs `Update Records` for each one, which fails during mass stage updates.

**Solution:**

```text
Start: Opportunity after-save
Get Records: Renewal Tasks for all triggering Opportunity Ids
Loop: Renewal Tasks
Assignment: Set Status = 'Needs Review' on a task collection variable
Update Records: task collection variable
```

**Why it works:** The flow performs one query and one DML operation for the batch instead of repeating both per record.

---

## Example 2: Move Same-Record Enrichment To Before-Save

**Context:** A record-triggered Case flow sets SLA flags and default routing values on the same Case.

**Problem:** The flow was built as after-save and re-updated the Case, triggering extra automation and using unnecessary DML.

**Solution:**

```text
Start: Case before-save
Decision: Is Priority blank or missing SLA?
Assignment: Set Priority and SLA fields on $Record
End
```

**Why it works:** Before-save updates on the triggering record are the most efficient path and avoid a separate database write.

---

## Anti-Pattern: Get Records Inside A Loop

**What practitioners do:** They loop through Accounts and place `Get Records` inside the loop to find Cases or Contacts for each Account.

**What goes wrong:** Query count grows with the number of loop iterations. The flow passes single-record testing and then fails during imports or integrations.

**Correct approach:** Query the related records once outside the loop, then use collection variables and decisions inside the loop to match the relevant records.

---

## Example 3: Reading The Failure Before It Happens

**Context:** A reviewer is handed a flow and asked "will this survive the nightly
integration?" The flow deploys, the flow test passes, and there is no org to load-test
against before Friday.

**Problem:** "Looks bulk-safe" is not an answer. The answer is in the connector graph and
it is arithmetic.

**Solution:** Extract three numbers from the XML — the elements on the loop cycle, the
elements off it, and the expected fan-out — then multiply. The cycle is
`loop.nextValueConnector` → … → back to the loop; anything reachable on it runs once per
item. Here is the review of the two flows in `references/metadata-examples.md`, side by
side:

```text
FLOW                     ON THE LOOP CYCLE               OFF THE CYCLE       SOQL   DML
                                                                             /int   /int
-----------------------------------------------------------------------------------------
..._ANTIPATTERN          Get_Parent_Shipment (SOQL)      Get_Shipment_Lines  1+L    L
                         Update_One_Line (DML+filters)
Shipment_AfterSave_      Stage_Line (Assignment only)    Get_Shipment_Lines  1      1
SyncLines                                                Update_Shipment_Lines

L = lines per shipment (12 typical, 40 worst case)

              200-record chunk, ANTIPATTERN     200-record chunk, corrected
  SOQL        200 x (1 + 12) = 2,600            200 x 1 = 200
  DML         200 x 12      = 2,400            200 x 1 = 200

  Budget      100 SOQL / 150 DML per transaction   (apexdev.txt L19544, L19554)
  Verdict     fails inside shipment 8             fails: 200 > 150 DML
```

**Why it works — and why the second verdict still says "fails":** the arithmetic is the
whole review, and it does not stop being useful when the answer is uncomfortable. Removing
the in-loop elements takes this flow from 2,600 SOQL to 200, which is the difference
between "hopeless" and "one design decision away". The remaining 200 DML statements are
the *interview* multiplier, not the loop multiplier, and no amount of collection
discipline inside one interview removes it — that is a question about whether the
platform's cross-interview bulk element folds those 200 into fewer statements, which the
guides do not state (`references/gotchas.md` § the platform bulkifies across interviews).
Measure it with `FLOW_BULK_ELEMENT_LIMIT_USAGE` on a real 200-record load before
promising the number, and if it does not fold, the escalation in `SKILL.md` Pattern 3
applies.

The reviewable artefact is the table, not the opinion. Run it on any flow with a loop:

```bash
python3 skills/flow/flow-bulkification/scripts/check_flow_bulkification.py \
  --manifest-dir force-app/main/default --max-dml 3
```
