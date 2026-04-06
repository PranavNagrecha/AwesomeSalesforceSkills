# LLM Anti-Patterns — Sharing Recalculation Performance

Common mistakes AI coding assistants make when generating or advising on sharing recalculation performance.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming OWD Changes Are Low-Risk on Large Orgs

**What the LLM generates:** "You can change the OWD for this object from Public to Private in Setup > Sharing Settings. This is a standard admin operation and should complete quickly."

**Why it happens:** LLMs are trained on introductory Salesforce documentation and tutorials that describe OWD changes as simple checkbox operations. The documentation rarely emphasizes the recalculation cost at scale, and most training examples involve small sandboxes with minimal data.

**Correct pattern:**

```
Before changing OWD on [Object]:
- Check record count: SELECT COUNT() FROM [Object]
- If count > 500,000, schedule during a maintenance window — this operation
  will trigger a full background recalculation that can run for several hours.
- If count > 100,000 and direction is tightening (more restrictive), plan for
  30–90+ minutes of recalculation time depending on sharing rule complexity.
- Enable Defer Sharing Calculations first if making multiple OWD changes.
- Verify all Apex sharing reasons on this object have a registered batch recalculation class.
```

**Detection hint:** Look for phrasing like "simply change the OWD," "quick admin change," or "should complete quickly" alongside an OWD tightening recommendation. Any OWD tightening advice that omits record count, maintenance window, or deferral guidance is likely incomplete.

---

## Anti-Pattern 2: Omitting the Apex Managed Share Rebuild Class

**What the LLM generates:**

```apex
// Apex managed sharing example
OpportunityShare share = new OpportunityShare();
share.OpportunityId = opp.Id;
share.UserOrGroupId = userId;
share.OpportunityAccessLevel = 'Read';
share.RowCause = 'Custom_Territory__c';
insert share;
```

The LLM then moves on without mentioning that a recalculation batch class must be registered for `Custom_Territory__c`.

**Why it happens:** The DML pattern for creating Apex share rows is straightforward and well-documented. The requirement to register a `Database.Batchable` recalculation class is a separate Setup step that LLMs frequently omit because it is not part of the code authoring flow — it is a post-deployment configuration requirement.

**Correct pattern:**

```apex
// Step 1: implement the recalculation batch class
global class TerritoryShareRecalculation implements Database.Batchable<SObject> {
    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM Opportunity');
    }
    global void execute(Database.BatchableContext bc, List<Opportunity> records) {
        delete [SELECT Id FROM OpportunityShare
                WHERE RowCause = 'Custom_Territory__c'
                AND OpportunityId IN :records];
        insert TerritoryShareService.computeShares(records);
    }
    global void finish(Database.BatchableContext bc) {}
}

// Step 2 (non-code): Register in Setup:
// Object Manager > Opportunity > Apex Sharing Reasons > Custom_Territory__c
// > Edit > Recalculation Apex Class: TerritoryShareRecalculation
```

**Detection hint:** Any Apex managed sharing implementation that inserts rows with a custom `RowCause` but does not include a `Database.Batchable` recalculation class and a Setup registration step is incomplete.

---

## Anti-Pattern 3: Recommending "Just Recalculate Manually" Without Mentioning Defer Sharing Calculations

**What the LLM generates:** "After making your sharing rule changes, go to Setup > Sharing Settings and click 'Recalculate' to update sharing for all records."

**Why it happens:** The "Recalculate" button in Sharing Settings is a visible, documented UI element. LLMs recommend it as the natural follow-up to any sharing change. They are unaware that (a) clicking Recalculate on a large object is itself a full recalculation job that takes hours, and (b) if multiple structural changes are needed, batching them under Defer Sharing Calculations is far more efficient than manually triggering recalculation after each one.

**Correct pattern:**

```
When multiple sharing structure changes are needed:
1. Enable Defer Sharing Calculations (Setup > Defer Sharing Calculations)
2. Apply all structural changes (OWD edits, sharing rule additions, role changes)
3. Disable Defer Sharing Calculations — Salesforce triggers a single collapsed
   recalculation job instead of N separate jobs.

When a single ad-hoc recalculation is needed (e.g., suspected data integrity issue):
- Proceed with the Recalculate button, but only during off-peak hours if the
  object has > 500K records.
- Do NOT click Recalculate while another sharing recalculation job is already running.
```

**Detection hint:** Watch for "click Recalculate" advice that omits record volume context or does not mention the Defer Sharing Calculations option for batching multiple changes.

---

## Anti-Pattern 4: Recommending Criteria-Based Sharing Rules on High-Churn Fields

**What the LLM generates:** "To share all Opportunities with `Stage = 'Closed Won'` to the Finance team, create a criteria-based sharing rule: Object = Opportunity, Field = Stage, Operator = equals, Value = Closed Won, Share with = Finance group."

**Why it happens:** Criteria-based sharing rules are a legitimate and well-documented Salesforce feature. LLMs correctly identify that they can be used to share records based on field values. They do not model the recalculation cost that occurs every time the criteria field (`Stage`) is updated in bulk — a very common operation in sales orgs with automated stage progressions.

**Correct pattern:**

```
Before creating a criteria-based sharing rule, check:
1. How often is the criteria field updated? (Setup > Field History for audit)
2. Is the field updated in bulk by integrations or batch jobs?

If the criteria field is updated frequently in bulk:
- Prefer a role- or group-based sharing rule instead, and
  manage Finance team membership directly in the group.
- Criteria-based rules are safe when the criteria field changes rarely
  (e.g., a custom boolean set at record creation, or a picklist set by
  manual admin action).

If criteria-based rule is required:
- Acknowledge the recalculation cost to the stakeholder.
- Confirm the object's record volume and plan maintenance windows for
  batch operations that touch the criteria field.
```

**Detection hint:** Look for criteria-based sharing rule recommendations on `Stage`, `Status`, `Rating`, `Priority`, or any field that appears in bulk update patterns elsewhere in the org design.

---

## Anti-Pattern 5: Treating Defer Sharing Calculations as a Toggle That Can Stay Enabled Indefinitely

**What the LLM generates:** "Enable Defer Sharing Calculations in Setup to prevent performance issues from sharing recalculation. You can leave it enabled permanently to keep sharing jobs from running during business hours."

**Why it happens:** The word "Defer" suggests a benign delay mechanism. LLMs correctly identify that deferral prevents background jobs during business hours, but they do not model that while deferral is active, record access is inconsistent — users may retain access they should have lost, or be denied access they should have gained.

**Correct pattern:**

```
Defer Sharing Calculations should be used as a time-bounded maintenance operation:
1. Enable at the start of a maintenance window.
2. Apply all planned structural changes.
3. Disable at the end of the maintenance window to trigger a single
   collapsed recalculation job.

Do NOT leave Defer Sharing Calculations enabled indefinitely:
- Users will have stale, inconsistent access while deferral is active.
- Every structural change made during the deferral window accumulates in the
  pending queue — the longer it stays enabled, the larger and less predictable
  the collapsed job becomes when cleared.
- Security audits may flag indefinitely deferred sharing as a compliance gap.
```

**Detection hint:** Any recommendation to enable Defer Sharing Calculations "permanently," "by default," or without a corresponding step to disable it is incorrect.
