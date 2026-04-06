# Examples — Sales Cloud Architecture

## Example 1: Layered Automation for High-Volume Opportunity Management

**Context:** A B2B SaaS company processes 10,000 opportunities per quarter across 500 sales reps. The org has accumulated 12 Process Builders and 4 Apex triggers on the Opportunity object over three years. Stage changes sometimes take 8+ seconds and occasionally hit governor limits during bulk imports.

**Problem:** Without a unified automation architecture, each team added their own Process Builder or trigger independently. The result is nondeterministic execution order, redundant SOQL queries (the same Account query runs in three different automations), and conflicting field updates where a discount-approval Process Builder overwrites values set by a forecast-sync trigger.

**Solution:**

```text
Automation Ownership Map — Opportunity Object

Before-Save (Record-Triggered Flow):
  - Field defaults (Stage -> Probability mapping)
  - Validation (Amount > 0 when Stage = Negotiation)
  - Discount threshold flagging

After-Save (Single Dispatcher Trigger -> Domain Handler):
  - OpportunityHandler.cls
    ├── onAfterInsert()  -> Territory assignment, activity creation
    ├── onAfterUpdate()  -> Stage-change notifications, forecast sync
    └── onAfterDelete()  -> Commission recalculation event

Async (Platform Event: SalesEvent__e):
  - ERP order creation (subscriber: ERPOrderSubscriber.cls)
  - Commission system notification (subscriber: CommissionSubscriber.cls)

Scheduled (Batch Apex):
  - Stale opportunity cleanup — weekly
  - Forecast snapshot — nightly
```

**Why it works:** Consolidating all before-save logic into a single Flow eliminates redundant queries. Routing all after-save logic through a single dispatcher trigger guarantees execution order and enables bulkification across all handlers. Decoupling external system notifications through Platform Events means the user's save completes in under 2 seconds regardless of ERP availability.

---

## Example 2: Territory-Driven Data Model for Multi-Region Sales Org

**Context:** A manufacturing company operates in 14 countries with 2,000 sales reps. Territories are realigned quarterly based on revenue performance. The current architecture uses role hierarchy for both organizational reporting and territory-based sharing, creating a maintenance nightmare every quarter when territories shift but the org chart does not.

**Problem:** Without separating territory management from organizational hierarchy, every quarterly territory realignment requires manual role-hierarchy changes affecting 200+ roles, breaking sharing rules, dashboard filters, and report folder access. The realignment takes two weeks of admin time and produces a forecast blackout period.

**Solution:**

```text
Architecture Decision: Separate Concerns

1. Role Hierarchy — Organizational structure only
   - CEO > VP Sales > Regional Director > Manager
   - Used for: report folder access, dashboard visibility, approval routing

2. Enterprise Territory Management — Sales territory structure
   - Global > Region > Country > District > Named Account
   - Used for: opportunity ownership, forecast rollup, sharing
   - Assignment Rules:
     - Rule 1: Billing Country -> Country territory
     - Rule 2: Annual Revenue > $10M -> Named Account territory
     - Rule 3: Industry = Healthcare -> Vertical specialist overlay

3. Territory Snapshot Object (Custom)
   - Territory_Snapshot__c
     - Territory_Id__c (lookup)
     - Snapshot_Date__c
     - Assigned_Rep__c
     - Opportunity_Count__c
     - Pipeline_Value__c
   - Populated nightly by batch Apex
   - Used for historical territory performance reporting
```

**Why it works:** Enterprise Territory Management supports rule-based reassignment that executes in minutes instead of weeks. Separating role hierarchy from territory hierarchy means quarterly realignment does not disrupt organizational access controls. The snapshot object enables historical reporting without querying live territory membership, which has no built-in history tracking.

---

## Anti-Pattern: Shadow Pipeline Objects

**What practitioners do:** Instead of extending the standard Opportunity object, teams create a custom `Deal__c` object to track their pipeline because "Opportunity doesn't support our process." They duplicate fields like Amount, Stage, Close Date, and Account lookup, then build custom reports and dashboards on `Deal__c`.

**What goes wrong:** Forecasting, Einstein Analytics, Pipeline Inspection, and every Sales Cloud feature that reads from Opportunity no longer reflects the real pipeline. Two sets of reports exist with conflicting numbers. Lead conversion does not create `Deal__c` records, so a manual process bridges the gap. Data quality degrades as reps update one object but not the other.

**Correct approach:** Extend Opportunity with record types, custom fields, and custom page layouts to support the unique process. Use validation rules and Flow to enforce process-specific requirements per record type. Reserve custom objects for genuinely new entities (e.g., Deal Desk Approval, Sales Play Assignment) that have a many-to-one relationship with Opportunity.
