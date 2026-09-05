# Examples — Flow Governor Limits Deep Dive

## Example 1: SOQL-in-loop breach

**Context:** Record-triggered Flow on Account, batch size 200. Inside a Loop over Contacts, a Get Records fetches the matching Case.

**Math:** 200 accounts × avg 5 contacts = 1000 iterations. 1 SOQL per iteration = 1000 SOQL. Limit = 100. Breach at iteration 100.

**Fix:** Hoist Get Records outside the loop with an IN-clause over all needed Ids. Single SOQL, map result by key, access inside loop.

---

## Example 2: Shared transaction budget

**Context:** Opportunity save fires: 2 After-Save Flows, 1 Validation Rule, 1 Apex trigger. Each needs its share of the 100-SOQL budget.

**Allocation (200-record batch):**
- Apex trigger: 15 SOQL
- VR: 3 SOQL
- Flow A: 4 SOQL
- Flow B: 4 SOQL
- Total: 26 SOQL

Headroom: 74 SOQL. Safe to add a fifth automation consuming up to ~50 SOQL (with buffer).

---

## Example 3: CPU timeout tuning

**Context:** Flow with 15 Decisions and 5 Assignments inside a Loop over 500 records. Times out at 10,000ms CPU.

**Fix:**
- Pre-compute the Decision branch outside the loop where possible.
- Replace nested Loop with a single Loop + Map lookup.
- Move heavy Formula evaluations out of inner Decisions.

Result: 8500ms → 3200ms.

---

## Example 4: Async offload

**Context:** After-Save flow needs 10 enrichment Get Records per record. At 200 records: 2000 SOQL. Fresh-transaction via Scheduled Path +0 gets fresh 100 SOQL per batch.

**Fix:** Add Scheduled Path with 0-minute delay. Same business logic, but async execution. Trade-off: 1-5 minute delivery lag.

---

## Anti-Pattern: Adding a flow without shared-budget math

Team adds Flow #6 to a busy Account stack. Tests pass in sandbox (no concurrent data). Production fires it alongside 5 other automations; 101 SOQL; silent breach. Fix: shared-budget forecast before deployment.

---

## The limits budget worksheet

Fill one of these per object + trigger type, not per flow — the meters are per transaction, so the
worksheet's unit has to be the transaction too. Copy the fenced block; it is designed to paste into a
PR description or a design doc, and the four "Arithmetic?" rows tell you which numbers you are allowed
to fill in from the metadata and which need a measurement.

```text
LIMITS BUDGET WORKSHEET
Object + trigger type : Facility_Audit__c / RecordAfterSave
Peak batch size (p99) : 200 records
Rows per record       : 6 critical findings
Date / author         : 2026-09-05 / <you>

                            Ceiling   Trigger   Flow A   Flow B   VR/     TOTAL   %      Arithmetic?
                            (sync)    (Apex)    (this)   (other)  rollup
--------------------------------------------------------------------------------------------------
SOQL queries                    100         15        1        4       3      23   23%   yes
SOQL query rows              50,000      3,000    1,200      800       0   5,000   10%   yes
DML statements                  150          3        4        2       1      10    7%   yes
DML rows                     10,000        400    1,600      400       0   2,400   24%   yes
Email invocations                10          0        1        1       0       2   20%   yes
Publish-immediately calls       150          0        1        0       0       1    1%   yes  (*)
Callouts                        100          0        0        0       0       0    0%   yes
Future calls                     50          0        0        0       0       0    0%   yes
Jobs in queue (enqueueJob)       50          0        0        0       0       0    0%   yes
Stack depth (recursive save)     16          2        1        1       0       4   25%   yes  (**)
CPU time (ms)                10,000          ?        ?        ?       ?       ?    ?    NO   - measure
Heap (bytes)              6,000,000          ?        ?        ?       ?       ?    ?    NO   - measure

(*)  Only if the platform event's publish behavior is "Publish Immediately". If it is
     "Publish After Commit" the spend moves to the DML statements row instead.
(**) Count each level of the cascade a DML sets off, not each element.

Ceilings: apexdev.txt L19542-L19599 (SOQL L19544, rows L19546, DML L19554, DML rows L19556,
stack depth L19559, callouts L19563, future L19568, enqueueJob L19573, email L19575,
heap L19577, CPU L19579, publish-immediately L19598).

MEASURED (fill after a sandbox run at peak batch size)
  Source: debug log, Workflow category at FINER
  FLOW_START_INTERVIEW_LIMIT_USAGE     : SOQL __/100  DML __/150   <- inherited before this flow ran
  FLOW_INTERVIEW_FINISHED_LIMIT_USAGE  : SOQL __/___  CPU __/_____ <- note the DENOMINATOR: it tells
                                                                      you whether this ran at sync or
                                                                      async ceilings
  CUMULATIVE_LIMIT_USAGE / LIMIT_USAGE_FOR_NS : transaction total, all namespaces

VERDICT
  [ ] every arithmetic row  < 70% of ceiling
  [ ] CPU and heap MEASURED, not estimated, and < 70%
  [ ] no DML element inside a loop      (checker E1)
  [ ] no Get Records inside a loop      (checker W1)
  [ ] every apex action states flowTransactionModel (checker A1)
  [ ] the co-tenant list is complete: SELECT ApiName FROM FlowDefinitionView
      WHERE TriggerObjectOrEventLabel = '<object>' AND IsActive = true

  If any arithmetic row is above 70%: reduce the spend first (loops), then split the
  transaction (NewTransaction / AsyncAfterCommit). In that order - see
  references/well-architected.md "The Budget Ladder".
```

Two columns do the work. **TOTAL** is the only number that means anything, because the meters do not
know which automation spent them. **Arithmetic?** is the honesty column: the ten `yes` rows come from
counting elements in the metadata and can be filled in at review time; the two `NO` rows cannot be
derived from any published figure and must be left blank until someone has run the batch. A worksheet
with numbers in the CPU and heap rows and no log excerpt attached has been invented.

Generate the `yes` rows for the flows you control with:

```bash
python3 skills/flow/flow-governor-limits-deep-dive/scripts/check_flow_governor_limits_deep_dive.py \
  --manifest-dir force-app --dml-budget 10
```
