# LLM Anti-Patterns — Opportunity Trigger Patterns

Common mistakes AI coding assistants make when generating or advising on Opportunity trigger patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: DML on OpportunitySplit in a Before Context

**What the LLM generates:**

```apex
trigger OpportunityTeamMemberTrigger on OpportunityTeamMember (before insert) {
    for (OpportunityTeamMember otm : Trigger.new) {
        insert new OpportunitySplit(
            OpportunityId = otm.OpportunityId,
            SplitOwnerId = otm.UserId,
            SplitPercentage = 100,
            SplitTypeId = someId
        );
    }
}
```

**Why it happens:** LLMs associate "before insert" with "set up related data early." They do not have reliable training signal about the specific platform restriction on `OpportunitySplit` DML in before contexts.

**Correct pattern:**

```apex
trigger OpportunityTeamMemberTrigger on OpportunityTeamMember (after insert) {
    // Only after insert is valid for OpportunitySplit DML
    OpportunityTeamMemberHandler handler = new OpportunityTeamMemberHandler();
    handler.onAfterInsert(Trigger.new);
}
```

**Detection hint:** Look for `insert`, `update`, or `delete` on `OpportunitySplit` inside any `before` trigger context. Flag immediately.

---

## Anti-Pattern 2: Checking Stage Without Comparing to oldMap

**What the LLM generates:**

```apex
for (Opportunity opp : Trigger.new) {
    if (opp.StageName == 'Closed Won') {
        // Create order record
    }
}
```

**Why it happens:** LLMs pattern-match on the common "check a field value in a trigger" template and omit the delta check. This generates an order record on every save of a Closed Won opportunity — including field updates that have nothing to do with stage.

**Correct pattern:**

```apex
for (Opportunity opp : Trigger.new) {
    Opportunity old = Trigger.oldMap.get(opp.Id);
    if (opp.StageName == 'Closed Won' && old.StageName != 'Closed Won') {
        // Only fires when transitioning INTO Closed Won
    }
}
```

**Detection hint:** Any condition like `opp.StageName == '<value>'` inside an update trigger handler without a corresponding `old.StageName != '<value>'` comparison is a delta-check omission.

---

## Anti-Pattern 3: SOQL or DML Inside the Opportunity Loop for Rollups

**What the LLM generates:**

```apex
for (Opportunity opp : Trigger.new) {
    AggregateResult ar = [
        SELECT SUM(Amount) total
        FROM Opportunity
        WHERE AccountId = :opp.AccountId AND IsClosed = false
    ][0];
    update new Account(Id = opp.AccountId, Open_Pipeline__c = (Decimal) ar.get('total'));
}
```

**Why it happens:** LLMs default to imperative loop patterns. The natural reading of "for each Opportunity, update its Account" becomes "for each record in the loop, query and update." Training data contains many single-record examples that work without bulkification.

**Correct pattern:**

```apex
// Collect all AccountIds first, then one query, then one DML
Set<Id> accountIds = new Set<Id>();
for (Opportunity opp : Trigger.new) {
    if (opp.AccountId != null) accountIds.add(opp.AccountId);
}
// One aggregate SOQL outside the loop
// One update DML outside the loop
```

**Detection hint:** Any SOQL or DML statement whose opening bracket appears inside a `for (... : Trigger.new)` or `for (... : Trigger.old)` loop body.

---

## Anti-Pattern 4: Revenue Split Percentages That Don't Sum to 100

**What the LLM generates:**

```apex
Integer share = 100 / members.size(); // e.g. 33 for 3 members
for (User u : members) {
    splitsToUpsert.add(new OpportunitySplit(
        SplitPercentage = share, // 33 + 33 + 33 = 99 — FAILS
        ...
    ));
}
```

**Why it happens:** LLMs apply naive integer division. They do not model the platform's hard constraint that Revenue split percentages must total exactly 100. The off-by-one is invisible until the DML throws `FIELD_INTEGRITY_EXCEPTION`.

**Correct pattern:**

```apex
Integer count = members.size();
Integer baseShare = 100 / count;
Integer remainder = 100 - (baseShare * count); // e.g. 1 for 3 members

for (Integer i = 0; i < count; i++) {
    Integer share = (i == 0) ? baseShare + remainder : baseShare; // 34 + 33 + 33 = 100
    splitsToUpsert.add(new OpportunitySplit(SplitPercentage = share, ...));
}
```

**Detection hint:** Any split distribution that uses `100 / count` as the only arithmetic without a remainder correction. Also look for missing assertions in test methods (`System.assertEquals(100, totalPercent)`).

---

## Anti-Pattern 5: Accessing Trigger.oldMap Without Checking for Insert Context

**What the LLM generates:**

```apex
trigger OpportunityTrigger on Opportunity (before insert, before update, after update) {
    for (Opportunity opp : Trigger.new) {
        String prevStage = Trigger.oldMap.get(opp.Id).StageName; // NPE on insert!
    }
}
```

**Why it happens:** LLMs often generate a single handler method dispatched by multiple trigger events. They either omit the context guard entirely, or add it as a comment but not as executable code.

**Correct pattern:**

```apex
// Option A: separate the handler dispatch by context
if (Trigger.isUpdate) handler.onUpdate(Trigger.new, Trigger.oldMap);
if (Trigger.isInsert) handler.onInsert(Trigger.new);

// Option B: null-safe access inside the handler
Opportunity old = (Trigger.oldMap != null) ? Trigger.oldMap.get(opp.Id) : null;
if (old != null && opp.StageName != old.StageName) { ... }
```

**Detection hint:** Any access to `Trigger.oldMap` or `Trigger.old` inside a method that is also reachable from an insert context without a preceding `if (Trigger.isUpdate)` or `oldMap != null` guard.

---

## Anti-Pattern 6: Suggesting Flow to Manage OpportunitySplit Records

**What the LLM generates:** "Use a Record-Triggered Flow on Opportunity to update the OpportunitySplit child records when the team changes."

**Why it happens:** LLMs default to Flow recommendations for related-record updates because Flow handles most child-record scenarios. They do not model the limitation that `OpportunitySplit` is not a standard-supported object in Flow's Create/Update Records actions.

**Correct pattern:** OpportunitySplit DML requires Apex. There is no Flow action or standard element that can insert, update, or delete `OpportunitySplit` records. Use an Apex trigger or an invocable method called from Flow — with the DML executing in Apex, not in Flow's record operation layer.

**Detection hint:** Any recommendation to use a Flow "Update Records" or "Create Records" element with `OpportunitySplit` as the target object.
