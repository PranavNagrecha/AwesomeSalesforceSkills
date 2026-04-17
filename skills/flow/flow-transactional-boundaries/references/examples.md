# Flow Transactional Boundaries — Worked Examples

## Example 1: Collapsing a Same-Record After-Save into a Before-Save

**Context:** An org has an After-Save record-triggered flow on `Opportunity` named `Set_Stage_Defaults` that only updates fields on the triggering record when the Opportunity is created. During peak import windows the team hits `System.LimitException: Too many DML statements: 151` in the combined Apex + Flow transaction. The root cause: the After-Save flow charges an extra DML per opportunity.

**Target boundary:** Before-Save (same-record field enrichment).

**Refactor steps:**

1. Create a new record-triggered flow on `Opportunity`.
2. In the Start element, select **Trigger the Flow When**: "A record is created".
3. In the Start element, select **Optimize the Flow For**: "Fast Field Updates" — this is Before-Save.
4. Add a Decision element `Stage_Is_Blank` with outcome `StageName is null OR empty`.
5. On the True branch, add an Assignment element `Set_Default_Stage` with:
   - `$Record.StageName` = "Prospecting"
   - `$Record.Probability` = 10
6. On both branches, add an Assignment `Seed_Owner_Region` that computes `$Record.OwnerRegion__c` from `$Record.Owner.Region__c` (available because the trigger already loaded the Owner reference on related-read).
7. Activate the new flow; deactivate the After-Save version.

**Verification:**
- Bulk-insert 200 Opportunities via the Developer Console anonymous window: `insert [... 200 Opportunities ...];`
- Confirm `Limits.getDmlStatements()` in a trigger log shows 1 (not 201).
- Confirm the fields are set on read-back.

**Why this works:** Before-Save writes fold into the platform's pending INSERT. Zero extra DML. The 150-limit headroom that the After-Save flow was consuming is returned to Apex and other automation.

**Gotcha encountered:** Before-Save cannot call Send Email actions. The original After-Save flow had a "send welcome email" action buried in its path; that action was moved to a separate After-Save flow with an entry condition that checks only the fields the email cares about.

---

## Example 2: Moving a Callout-Heavy After-Save to a Scheduled Path

**Context:** A `Case_Enrichment_Flow` on `Case` After-Save calls an invocable Apex action that makes an HTTP callout to a customer-data service, then updates the Case with the enriched fields. This fails at bulk with `You have uncommitted work pending` because callouts cannot mix with DML in the same transaction.

**Target boundary:** Scheduled Path with 0-hour offset.

**Refactor steps:**

1. Open `Case_Enrichment_Flow` and add a Scheduled Path in the Start element.
2. Name: `Async_Enrich`. Time Source: "When the Record is Created". Offset: 0 Hours.
3. MOVE the `Invocable: Enrich_Case_External` and subsequent `Update Records` into the Scheduled Path branch.
4. In the immediate Run Immediately branch, leave only the Decision that validates whether enrichment is eligible (`Case.Priority != 'Low' AND Case.CustomerTier__c != null`). If eligible, the flow exits the immediate branch — the Scheduled Path picks up later.
5. Add a Fault Path on the `Invocable: Enrich_Case_External` element:
   - Connect to a `Create Records` element that writes a row to `Integration_Error_Log__c` with Case Id, error text, and timestamp.
   - Connect onward to an `Update Records` element that sets `Case.EnrichmentStatus__c = 'Failed'`.
6. Activate.

**Verification:**
- Insert a Case via API.
- Confirm the Case commits immediately with `EnrichmentStatus__c = 'Pending'`.
- Wait 2–5 minutes. Confirm a subsequent update sets `EnrichmentStatus__c = 'Enriched'` (or `'Failed'` with a row in the error log).

**Why this works:** The user/API caller gets an immediate, successful save. The callout runs in a separate async transaction with its own budget and failure path. The originating save cannot be rolled back by a downstream callout failure, which is the correct semantics for non-blocking enrichment.

**Cross-transaction compensation:** if an enrichment fails and the business requires retry, a nightly Batch Apex job sweeps `Case` records where `EnrichmentStatus__c = 'Failed' AND LastModifiedDate > LAST_N_DAYS:2` and re-enqueues via a `Re-Enqueue Enrichment` Platform Event.

---

## Example 3: Orchestrating a Multi-Stakeholder Approval With Explicit Boundaries

**Context:** A capital-expense approval must go through Intake (requestor fills form), Manager Review (approve/reject), Finance Review (approve/reject), and Final Booking (creates downstream record in ERP via MuleSoft). Each stage runs for hours to days. Using one big Screen Flow with Pause elements creates operational fragility: a failed Pause leaves the interview stuck.

**Target boundary:** Flow Orchestration with one Stage per stakeholder role.

**Orchestration structure:**

```
Orchestration: CapEx_Approval
  Stage_1_Intake
    Step_1A: Interactive — Assigned to: $Record.RequestedBy
            Flow: CapEx_Intake_Form_Screen (Screen Flow)
    Step_1B: Background — Flow: CapEx_Validate_Required_Fields_Autolaunched
  Stage_2_Manager
    Step_2A: Interactive — Assigned to: $Record.ManagerId
            Flow: CapEx_Manager_Review_Screen
  Stage_3_Finance
    Step_3A: Interactive — Assigned to: Queue: Finance_Approvers
            Flow: CapEx_Finance_Review_Screen
  Stage_4_Book
    Step_4A: Background — Flow: CapEx_Send_To_ERP_Autolaunched
            (calls invocable Apex → Platform Event → MuleSoft consumer)
```

**Boundary behavior:**

- Each Step is a separate transaction. If Step 3A's screen flow fails on a validation, Steps 1A/1B/2A's committed work is unaffected.
- Between Steps, Orchestration persists the Orchestration Work Item in storage. Managers can see pending work in the Work Guide list view.
- If Step 4A's Send-To-ERP publish fails (Platform Event queue full, for example), Orchestration marks the step as Failed and exposes a Retry affordance. Meanwhile Stages 1–3 are committed and auditable.

**Implementation notes:**

- Each interactive step uses a Screen Flow; the Screen Flow may have internal Pause elements for intra-step waits (e.g., wait for attached document upload).
- The Background step `CapEx_Send_To_ERP_Autolaunched` is NOT called synchronously from Step 3A, which is why the transaction boundary is clean. The Orchestration runtime enqueues Step 4A after Step 3A completes.
- Add a fault step on `CapEx_Send_To_ERP_Autolaunched` that writes to `CapEx_Error__c` and notifies the Finance_Approvers queue via Chatter.

**Why this works:** Orchestration forces the cross-transaction mindset. No stage's work can be rolled back by a later stage failing, which is the correct semantics for days-long processes with independent stakeholders. Limit budgets reset at each stage boundary.

---

## Example 4: Flow Called from Apex Queueable

**Context:** A reusable `Case_SLA_Recompute` autolaunched flow centralizes SLA math. A Batch Apex job `CaseSLARecalcBatch` processes 200 cases per execute and needs to reuse the Flow logic.

**Target boundary:** Flow runs inside the Batch Apex execute transaction, with async limits.

**Caller code pattern:**

```apex
public class CaseSLARecalcBatch implements Database.Batchable<sObject> {
    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return Database.getQueryLocator([SELECT Id FROM Case WHERE SLA_Recompute_Requested__c = TRUE]);
    }
    public void execute(Database.BatchableContext ctx, List<Case> scope) {
        if (Limits.getDmlStatements() > 120) return;
        for (Case c : scope) {
            Map<String, Object> params = new Map<String, Object>{ 'caseId' => c.Id };
            Flow.Interview.createInterview('Case_SLA_Recompute', params).start();
        }
    }
    public void finish(Database.BatchableContext ctx) {}
}
```

**Boundary behavior:**

- Each `execute` is its own async transaction, with 200 SOQL / 150 DML / 60,000 ms CPU / 12 MB heap.
- The Flow runs N times (once per case), each call sharing THIS execute's budget. That's why the loop is risky: 200 flow invocations, each with even 1 DML, exhausts the budget.

**Refactor for scale:** Convert the flow to accept a Case Id collection, OR call the flow once and move the loop inside (collection-based). The correct bulk pattern: one interview, List<Id> input, loop inside the flow, one DML at the end.

```apex
Map<String, Object> params = new Map<String, Object>{ 'caseIds' => (List<Id>) new Map<Id, Case>(scope).keySet() };
Flow.Interview.createInterview('Case_SLA_Recompute_Bulk', params).start();
```

The flow's internal Loop now iterates in-memory, building a single `casesToUpdate` collection, and commits once.

**Why it matters:** "Called from Apex" does NOT isolate the Flow from governor limits. It inherits them. Every call site must be budget-aware, and bulkification is mandatory.
