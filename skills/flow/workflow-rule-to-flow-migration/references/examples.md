# Examples — Workflow Rule to Flow Migration

## Example 1: Field Update Migration Using the Tool

**Context:** A Contact Workflow Rule fires when `LeadSource` is set to "Web" and updates `Rating` to "Hot". No ISCHANGED criteria, no task actions.

**Problem:** The team wants the fastest migration path before the December 31 2025 deadline.

**Solution:**
1. Setup > Migrate to Flow > select "Contact Rating Updater" rule > Convert
2. Open generated inactive flow in Flow Builder
3. Verify Decision condition: `{!$Record.LeadSource} = "Web"` (static comparison — tool handles correctly)
4. Add Fault Path to Update Records element (tool omits fault paths)
5. In Flow Trigger Explorer, set priority = 10 (no other Contact flows active)
6. Test: Execute Anonymous bulk-creates 200 Contacts with LeadSource = "Web"; assert Rating = "Hot" on all
7. Activate flow; deactivate "Contact Rating Updater" rule immediately

**Why it works:** Static-value comparison criteria and field updates are the tool's strongest use case. The critical additions are the Fault Path and bulk test.

---

## Example 2: Time-Based Action Replacement with Scheduled Path

**Context:** An Opportunity Workflow Rule sends a follow-up email 3 days after `CloseDate` when Stage = "Closed Won". This is a time-based action.

**Problem:** The Migrate to Flow tool cannot convert time-based actions. The team needs a manual Scheduled Path.

**Solution:**

In a new record-triggered flow (Opportunity, trigger on create/update, run after save):

```
Entry Criteria:
  {!$Record.StageName} = "Closed Won"

Scheduled Path:
  Schedule: 3 Days After Opportunity.CloseDate
  
  Action: Send Email (Email Alert: Opportunity_FollowUp_Alert)
```

Key configuration:
- Set "Schedule Path" type to "Time After" with field = `CloseDate`, offset = 3 days
- Move the email alert action into the Scheduled Path (not the immediate path)
- Deactivate original Workflow Rule only after confirming no critical pending scheduled actions

**Why it works:** Scheduled Paths in record-triggered flows precisely replicate time-based workflow behavior. The offset field maps directly to the Workflow time trigger configuration.

---

## Anti-Pattern: Running Tool on a Rule with ISCHANGED Criteria

**What practitioners do:** Run the Migrate to Flow tool on a Workflow Rule that uses `ISCHANGED(Status)` in its entry criteria, then activate the generated flow without reviewing the Decision conditions.

**What goes wrong:** The tool may omit the ISCHANGED condition or generate a condition that fires on every Status value, not just changes. The flow then fires on every update to the record — including unrelated field changes — causing spurious field updates and email alerts in production.

**Correct approach:** Before running the tool, audit every rule's entry criteria. Any rule with ISCHANGED() or ISNEW() must be manually rebuilt using `{!$Record__Prior.FieldName} != {!$Record.FieldName}` in a Decision node.
