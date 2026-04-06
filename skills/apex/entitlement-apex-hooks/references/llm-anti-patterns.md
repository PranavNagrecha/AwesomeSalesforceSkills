# LLM Anti-Patterns — Entitlement Apex Hooks

Common mistakes AI coding assistants make when generating or advising on Entitlement Apex Hooks.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Setting IsCompleted = true Instead of Writing CompletionDate

**What the LLM generates:**

```apex
for (CaseMilestone cm : milestones) {
    cm.IsCompleted = true;  // WRONG
}
update milestones;
```

**Why it happens:** `IsCompleted` is a boolean field and LLMs trained on general Salesforce patterns assume boolean checkboxes are writable. The field name semantically implies it controls completion. Training data rarely contains the counter-intuitive detail that this specific field is a read-only formula derived from `CompletionDate`.

**Correct pattern:**

```apex
for (CaseMilestone cm : milestones) {
    cm.CompletionDate = System.now();  // CORRECT
}
update milestones;
```

**Detection hint:** Search generated code for `IsCompleted\s*=\s*true` — any occurrence is a bug.

---

## Anti-Pattern 2: Attempting to Write SlaExitDate

**What the LLM generates:**

```apex
// Extend deadline by 1 hour for high-priority cases
for (CaseMilestone cm : milestones) {
    cm.SlaExitDate = cm.SlaExitDate.addHours(1);  // WRONG — silently discarded
}
update milestones;
```

**Why it happens:** LLMs infer that if a field exists on an object and is not explicitly documented as formula-derived, it must be writable. The requirement to adjust deadlines dynamically is common, and the LLM generates the most direct-looking implementation. Training data from Stack Overflow and community boards often contains this incorrect pattern without the correction.

**Correct pattern:**

```
Deadline adjustment is not achievable through Apex on SlaExitDate. Use separate
entitlement processes (e.g., Priority-Platinum, Priority-Standard) with different
milestone time triggers, and apply the correct process to the case based on attributes
at case creation time.
```

**Detection hint:** Search generated code for `SlaExitDate\s*=` — any write assignment is incorrect.

---

## Anti-Pattern 3: Trigger on CaseMilestone to Detect Violations

**What the LLM generates:**

```apex
trigger CaseMilestoneTrigger on CaseMilestone (after update) {
    for (CaseMilestone cm : Trigger.new) {
        CaseMilestone old = Trigger.oldMap.get(cm.Id);
        // WRONG — IsViolated is set by background platform process, not DML
        if (!old.IsViolated && cm.IsViolated) {
            // This block never executes for actual violations
            EscalationService.escalate(cm.CaseId);
        }
    }
}
```

**Why it happens:** The reactive trigger pattern is the canonical Salesforce pattern for reacting to state changes. LLMs generalize it to all field transitions without knowing that `IsViolated` is set by a platform background job, not by a user or automation DML call that would fire a trigger.

**Correct pattern:**

```apex
// Use Scheduled Apex — poll for violations at a regular interval
public class ViolationDetector implements Schedulable {
    public void execute(SchedulableContext sc) {
        List<CaseMilestone> violated = [
            SELECT Id, CaseId FROM CaseMilestone
            WHERE IsViolated = true AND CompletionDate = null
            AND Case.ViolationEscalated__c = false
            LIMIT 200
        ];
        // Apply business logic here
    }
}
```

**Detection hint:** Look for `trigger ... on CaseMilestone` combined with `IsViolated` comparison inside the trigger body.

---

## Anti-Pattern 4: Missing Entitlement Process Hierarchy in Test Setup

**What the LLM generates:**

```apex
@isTest
static void testMilestoneCompletion() {
    Case c = new Case(Status = 'New', Subject = 'Test');
    insert c;
    c.Status = 'In Progress';
    update c;
    // Query milestones — returns empty list because no entitlement process applied
    List<CaseMilestone> milestones = [SELECT Id, IsCompleted FROM CaseMilestone WHERE CaseId = :c.Id];
    System.assertEquals(1, milestones.size()); // FAILS: size is 0
}
```

**Why it happens:** LLMs do not reliably model the prerequisite chain (EntitlementProcess > MilestoneType > EntitlementProcessMilestone > Entitlement > Account association > Case entitlement application) needed to produce `CaseMilestone` records. They generate tests that look structurally correct but run against cases that have no entitlement process applied, so `CaseMilestone` records never exist.

**Correct pattern:**

```apex
@testSetup
static void setupEntitlementData() {
    // Build the full hierarchy: Account > Entitlement > EntitlementProcess >
    // MilestoneType > EntitlementProcessMilestone > Case with EntitlementId
    // (see Entitlements Implementation Guide test data section)
}
```

**Detection hint:** A test class for CaseMilestone logic that does not insert an `Entitlement` and `EntitlementProcess` in `@testSetup` will produce vacuously passing tests.

---

## Anti-Pattern 5: Non-Bulk Trigger With Per-Record SOQL

**What the LLM generates:**

```apex
trigger CaseMilestoneTrigger on Case (after update) {
    for (Case c : Trigger.new) {
        if (Trigger.oldMap.get(c.Id).Status == 'New' && c.Status != 'New') {
            // WRONG — SOQL inside loop hits 101 query limit at 101+ cases
            List<CaseMilestone> ms = [
                SELECT Id FROM CaseMilestone
                WHERE CaseId = :c.Id AND CompletionDate = null
            ];
            for (CaseMilestone m : ms) { m.CompletionDate = System.now(); }
            update ms;
        }
    }
}
```

**Why it happens:** LLMs commonly generate readable per-record patterns from training examples that use small single-record test scenarios. The bulk-safety requirement (collect IDs, query once outside the loop, DML once outside the loop) requires a discipline that LLMs apply inconsistently.

**Correct pattern:**

```apex
trigger CaseMilestoneTrigger on Case (after update) {
    Set<Id> changedIds = new Set<Id>();
    for (Case c : Trigger.new) {
        if (Trigger.oldMap.get(c.Id).Status == 'New' && c.Status != 'New') {
            changedIds.add(c.Id);
        }
    }
    if (changedIds.isEmpty()) return;
    List<CaseMilestone> toUpdate = [
        SELECT Id FROM CaseMilestone
        WHERE CaseId IN :changedIds AND CompletionDate = null
        AND MilestoneType.Name = 'First Response'
    ];
    for (CaseMilestone m : toUpdate) { m.CompletionDate = System.now(); }
    update toUpdate;
}
```

**Detection hint:** Search for `[SELECT` or `update` or `insert` inside a `for (Case c :` loop body — any DML or SOQL inside a record-iteration loop is a bulk-safety violation.

---

## Anti-Pattern 6: Using before update Instead of after update for CaseMilestone DML

**What the LLM generates:**

```apex
trigger CaseTrigger on Case (before update) {
    // Milestone DML here — WRONG context for writing to a different object
    List<CaseMilestone> ms = [SELECT Id FROM CaseMilestone WHERE CaseId IN :caseIds];
    for (CaseMilestone m : ms) { m.CompletionDate = System.now(); }
    update ms;  // Can cause mixed-DML issues depending on org setup
}
```

**Why it happens:** LLMs default to `before update` for performance (avoids a re-query of the saved record) without recognizing that writing to a related object (CaseMilestone) from a `before update` trigger on Case can produce mixed-DML errors and is architecturally incorrect because the Case record has not yet been committed when the trigger fires.

**Correct pattern:** Use `after update` on Case when the business logic requires writing to related `CaseMilestone` records. The case is already committed and the related record write is a separate, clean DML operation.

**Detection hint:** Any trigger that specifies `before update` or `before insert` and then issues DML to `CaseMilestone` is suspect.
