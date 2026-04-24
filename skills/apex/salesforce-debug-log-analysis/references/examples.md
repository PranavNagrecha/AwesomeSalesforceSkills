# Examples — Salesforce Debug Log Analysis

Worked examples of forensic log investigations using the Recommended Workflow. Each example shows the symptom, the triage output, the specific events extracted, the mechanism identified, and the report delivered.

## Example 1: Flip-flop Opportunity Stage Across Two Logs

**Context:** A sales user reports that Opportunity Stage keeps reverting from `Negotiation` to `Qualification` minutes after they save. Two `apex-*.log` files were captured with Trace Flag at `WORKFLOW,FINER; APEX_CODE,FINEST`.

**Problem:** Multiple automations touch Stage — a record-triggered flow, a legacy process, and a managed-package trigger.

**Solution (applied workflow):**

1. **Triage** — both logs are ~3 MB each, 6 s apart. First log opens with a UI `CODE_UNIT_STARTED|UiActionHandler`; second opens with `CODE_UNIT_STARTED|[EventService…]` (async event).
2. **Timeline** — log A at 14:02:11 (size 3.1 MB), log B at 14:02:17 (size 3.4 MB, +6.0 s). Tight parent/child pair.
3. **Classify** — field-write attribution: load `flows.md`, `apex-and-async.md`, `managed-packages.md`, `recipes.md`.
4. **Extract transitions**:
   ```bash
   grep -nE "FLOW_ASSIGNMENT_DETAIL|WF_FIELD_UPDATE|VARIABLE_ASSIGNMENT.*StageName" log_a.log log_b.log
   ```
   Log A shows `FLOW_ASSIGNMENT_DETAIL|Opp_AfterUpdate|varStage|Negotiation` at dump index 42. Log B shows `WF_FIELD_UPDATE|Opportunity|StageName|Qualification` inside the legacy process at dump index 39.
5. **Mechanism** — the flow writes `Negotiation` in the sync transaction; a time-based workflow queued earlier fires after the record save and writes back `Qualification` via `WF_FIELD_UPDATE` (mechanism #1: direct Apex-equivalent write, legacy automation path).
6. **Report** delivered to user:

   > **Headline:** The Workflow Rule "Stage Reset on Owner Change" is overwriting the Stage six seconds after each save.
   >
   > **Evidence:** `log_b.log` line 8,211: `WF_FIELD_UPDATE|Opportunity|StageName|Qualification`. The workflow criterion `ISCHANGED(OwnerId)` was true because the flow in `log_a.log` reassigned the owner at line 6,402.
   >
   > **Recommendations:** (1) Deactivate the workflow field update; (2) move any still-needed logic into the record-triggered flow as a same-transaction assignment; (3) long-term, migrate all legacy workflow rules via [devops/migrate-workflow-pb]() decision tree.

**Why it works:** Transitions-only output and the mechanism classification kept the analysis focused on the single event (`WF_FIELD_UPDATE`) that actually set the reverted value, rather than blaming any of the dozen automations that merely fired.

---

## Example 2: `UNABLE_TO_LOCK_ROW` During Nightly Batch

**Context:** A `CpqBatch_SyncQuotes` scheduled batch fails intermittently around 02:15 UTC with `UNABLE_TO_LOCK_ROW, unable to obtain exclusive access to this record`.

**Problem:** The batch locks parent Account records; another process is touching the same Accounts at the same time.

**Solution (applied workflow):**

1. **Triage** — six logs uploaded, all within a 90-second window.
2. **Timeline** — shows three clusters: batch execute() scopes at 02:14:58, 02:15:02, 02:15:07, plus two queueable logs at 02:15:01 and 02:15:06 from `mc_sf` (Marketing Cloud Connect) namespace.
3. **Classify** — concurrency: load `error-codes.md`, `recipes.md`.
4. **Cross-reference record IDs**:
   ```bash
   grep -oE "001[a-zA-Z0-9]{15,18}" apex-*.log | sort | uniq -c | sort -rn | head -20
   ```
   Top 5 Account IDs appear in *both* the batch logs and the MC Connect queueable logs.
5. **Mechanism** — two transactions lock the same Accounts in overlapping windows. The batch uses `FOR UPDATE` (implied via update DML); the MC Connect queueable also updates `Account.MC_LastSync__c`. Whichever starts second gets `UNABLE_TO_LOCK_ROW`.
6. **Report:**

   > **Headline:** Marketing Cloud Connect queueable (`mc_sf` namespace) is updating the same Accounts your batch locks. They collide every 5 minutes because both are on the same schedule pattern.
   >
   > **Evidence:** Account `001Hu00001abc` appears at line 412 of `batch-0215.log` as `DML_BEGIN|Op:Update|Type:Account|Rows:1` and at line 1,203 of `mc_sync-0215.log` in the same second.
   >
   > **What the log cannot tell you:** whether MC Connect's schedule is configurable in your org — check Setup > Scheduled Jobs.
   >
   > **Recommendations:** (1) Reschedule the CPQ batch off the 5-minute boundary; (2) add `Database.LockResult`-based retry in the batch `execute()`; (3) long-term, move the sync to a Platform Event subscriber so both sides bulk-process.

**Why it works:** Counting record IDs across logs surfaced the overlap that no single log would have shown.

---

## Example 3: Governor Limit `Too many SOQL queries: 101` In LWC Action

**Context:** A Service Agent LWC page throws `System.LimitException: Too many SOQL queries: 101` when opening a Case with many related contacts.

**Problem:** The `@AuraEnabled` controller method is queried in a loop somewhere.

**Solution (applied workflow):**

1. **Triage** — single log, 1.8 MB, opens with `CODE_UNIT_STARTED|[EventService...aura]|CaseDetailController.getRelatedInfo`.
2. **Timeline** — one transaction, 4.2 s duration.
3. **Classify** — governor limit + UI framework: load `governor-and-performance.md`, `ui-frameworks.md`.
4. **Extract SOQL events**:
   ```bash
   grep -nE "SOQL_EXECUTE_BEGIN" case-action.log | awk -F'|' '{print $4}' | sort | uniq -c | sort -rn | head
   ```
   Output:
   ```
    87 SELECT Id, Name FROM Contact WHERE AccountId = :accountId
     8 SELECT Id FROM Case WHERE ContactId = :contactId
     2 SELECT Id FROM User WHERE Id = :UserInfo.getUserId()
   ```
5. **Mechanism** — 87 Contact queries means the method is calling a helper once per Contact. Confirmed at line 4,112: `METHOD_ENTRY|ContactHelper.fetchCases` appears 87 times.
6. **Report:**

   > **Headline:** `ContactHelper.fetchCases` runs a SOQL query once per Contact; with 87 Contacts on this Account, it hits 101 total (the other 14 come from validation and managed packages).
   >
   > **Evidence:** `grep "METHOD_ENTRY|ContactHelper.fetchCases" | wc -l` = 87. Line 4,112 shows the first invocation.
   >
   > **Recommendations:** (1) Rewrite `fetchCases` to accept `Set<Id> contactIds` and issue one query; (2) refer to `apex/apex-aggregate-queries` for bulk patterns; (3) add a governor check in the controller entry point to fail fast if Contact count > 50.

**Why it works:** Sorting SOQL by text and counting occurrences isolates the bulkification miss in one shell pipeline.

---

## Example 4: `INSUFFICIENT_ACCESS_OR_READONLY` On Merge

**Context:** A user merges two Leads via the standard UI and sees `INSUFFICIENT_ACCESS_OR_READONLY: not accessible: []`. The empty bracket list is notorious for hiding which record is actually inaccessible.

**Solution (applied workflow):**

1. **Triage** — single UI log, 900 KB.
2. **Classify** — sharing/FLS: load `security-sharing.md`, `error-codes.md`, `recipes.md`.
3. **Extract all record IDs touched during the merge**:
   ```bash
   grep -oE "00Q[a-zA-Z0-9]{15,18}|003[a-zA-Z0-9]{15,18}" merge.log | sort -u
   ```
   Three Lead IDs, twelve Contact IDs, four Task IDs, one Campaign ID.
4. **Mechanism** — Lead merge cascades to related child records (Tasks, Campaign Members). The log shows `DML_BEGIN|Op:Update|Type:Task` immediately before the failure. Task assignment rules run as the *running user*, not as the merging user, so the target user may lack access to one of the related Tasks.
5. **Report:**

   > **Headline:** The merge is failing on one of the related Task records, not the Leads themselves. Task assignment runs in the running user's sharing context.
   >
   > **Evidence:** Line 2,341 of `merge.log`: `DML_BEGIN|Op:Update|Type:Task` immediately followed by `EXCEPTION_THROWN|INSUFFICIENT_ACCESS_OR_READONLY`.
   >
   > **What the log cannot tell you:** which specific Task ID the user cannot access — the bracket list is empty by design for INSUFFICIENT_ACCESS.
   >
   > **Recommendations:** (1) Query all Tasks on both Leads as System Administrator; (2) for each one, test `SELECT Id FROM Task WHERE Id = '<id>' AND IsAccessible__c = true` while impersonating the merging user via Setup > Login as User; (3) grant sharing access or reassign the blocking Task before retrying the merge.

**Why it works:** The log confirmed the *category* of failure (Task update mid-merge); the remediation was deliberately pushed outside the log because the log genuinely cannot identify the blocked record.

---

## Anti-Example: Blaming the First Trigger You See

**What practitioners do:** They run `grep CODE_UNIT_STARTED log.log | head`, see `OpportunityBeforeUpdate` fire, and blame that trigger for the flip-flop.

**What goes wrong:** The first trigger logged is rarely the writer. Triggers run in an order the log does not display until you build the cascade. In a flip-flop, the writer is typically a *later* automation (workflow field update, time-based action, or managed-package trigger).

**Correct approach:** Always classify the writing mechanism (Step 5 of the workflow) before accusing a specific automation. Grep for the target field in `VARIABLE_ASSIGNMENT`, `FLOW_ASSIGNMENT_DETAIL`, and `WF_FIELD_UPDATE` events — not just `CODE_UNIT_STARTED`.
