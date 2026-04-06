# LLM Anti-Patterns — Omni-Channel Custom Routing

Common mistakes AI coding assistants make when generating or advising on Omni-Channel custom routing via Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Setting IsReadyForRouting = true on the Initial Insert

**What the LLM generates:** A single `PendingServiceRouting` insert that sets both `RoutingType = 'SkillsBased'` and `IsReadyForRouting = true` simultaneously, followed by a separate `SkillRequirement` insert.

**Why it happens:** LLMs treat the flag as a simple "enabled" boolean and assume the routing engine handles late-arriving child records gracefully, similar to how record-level flags work in other Salesforce contexts (e.g., `IsActive` on custom settings). They miss that `IsReadyForRouting` is a trigger for immediate engine evaluation, not a configuration toggle.

**Correct pattern:**

```apex
// WRONG
insert new PendingServiceRouting(
    WorkItemId = caseId,
    ServiceChannelId = channelId,
    RoutingType = 'SkillsBased',
    IsReadyForRouting = true  // ← DO NOT set on insert
);

// CORRECT
PendingServiceRouting psr = new PendingServiceRouting(
    WorkItemId = caseId,
    ServiceChannelId = channelId,
    RoutingType = 'SkillsBased',
    IsReadyForRouting = false  // ← always false on insert
);
insert psr;
// ... insert SkillRequirement records ...
psr.IsReadyForRouting = true;
update psr; // ← only flip AFTER child records exist
```

**Detection hint:** Search generated code for `IsReadyForRouting = true` appearing inside an `insert` DML statement or a `new PendingServiceRouting(...)` constructor call.

---

## Anti-Pattern 2: Hardcoding ServiceChannelId

**What the LLM generates:** Apex that embeds a literal 18-character Salesforce Id for `ServiceChannelId`, often sourced from a Setup URL the developer inspected in their development org.

**Why it happens:** LLMs imitate patterns from training examples where Ids are sometimes hardcoded in test code or quick demos. They do not model the org-lifecycle consequence of sandbox refreshes and deployments.

**Correct pattern:**

```apex
// WRONG
psr.ServiceChannelId = '0N9000000000XyzAAE'; // hardcoded — breaks on sandbox refresh

// CORRECT
ServiceChannel sc = [
    SELECT Id FROM ServiceChannel WHERE DeveloperName = 'Cases' LIMIT 1
];
psr.ServiceChannelId = sc.Id;
```

**Detection hint:** Search for string literals that match the pattern `'0N9[A-Za-z0-9]{15}'` assigned to `ServiceChannelId`. Any such literal is wrong.

---

## Anti-Pattern 3: Querying Skill by DeveloperName Inside a Loop

**What the LLM generates:** A `for` loop over work items that issues a `[SELECT Id FROM Skill WHERE DeveloperName = :name LIMIT 1]` query inside each iteration to resolve the Skill Id.

**Why it happens:** LLMs default to the clearest imperative style — "for each record, look up the skill it needs" — without modeling Apex governor limits. Single-record unit tests pass, so the LLM has no training signal that this pattern fails at bulk.

**Correct pattern:**

```apex
// WRONG — SOQL in loop
for (Case c : cases) {
    Skill s = [SELECT Id FROM Skill WHERE DeveloperName = 'Product_Support' LIMIT 1]; // ← SOQL in loop
    // ...
}

// CORRECT — bulk query + map
Set<String> skillNames = new Set<String>{ 'Product_Support', 'Spanish_Language' };
Map<String, Id> skillMap = new Map<String, Id>();
for (Skill s : [SELECT Id, DeveloperName FROM Skill WHERE DeveloperName IN :skillNames]) {
    skillMap.put(s.DeveloperName, s.Id);
}
for (Case c : cases) {
    Id skillId = skillMap.get('Product_Support'); // ← map lookup, no SOQL
    // ...
}
```

**Detection hint:** Any `[SELECT ... FROM Skill ...]` or `[SELECT ... FROM ServiceChannel ...]` query appearing inside a `for` loop over records is a governor-limit bug.

---

## Anti-Pattern 4: Omitting Orphan Cleanup on Exception

**What the LLM generates:** A try/catch block that catches the exception, logs it, and returns — but does not delete the `PendingServiceRouting` records that were already inserted before the failure.

**Why it happens:** LLMs model try/catch as "log and continue" without modeling the stateful side effect: the orphaned `PendingServiceRouting` record that persists in the database and blocks future routing attempts for the same work item.

**Correct pattern:**

```apex
// WRONG — orphan left behind
try {
    insert psrList;
    insert srList;
    update psrList;
} catch (Exception ex) {
    System.debug('Routing failed: ' + ex.getMessage()); // ← orphan not cleaned up
}

// CORRECT — delete orphans on failure
List<PendingServiceRouting> inserted = new List<PendingServiceRouting>();
try {
    insert psrList;
    inserted.addAll(psrList);
    insert srList;
    update psrList;
} catch (Exception ex) {
    if (!inserted.isEmpty()) {
        delete inserted; // ← prevent DUPLICATE_VALUE on next attempt
    }
    System.debug('Routing failed: ' + ex.getMessage());
}
```

**Detection hint:** Any `catch` block that handles a routing sequence without a `delete` on the already-inserted `PendingServiceRouting` list is incomplete.

---

## Anti-Pattern 5: Assuming SkillRequirement Can Be Inserted Before PendingServiceRouting

**What the LLM generates:** Code that constructs `SkillRequirement` records with a `RelatedRecordId` value derived from a `PendingServiceRouting` instance that has not yet been inserted (e.g., using `new Id(...)` or assuming the Id will be populated before DML).

**Why it happens:** LLMs sometimes model DML as non-blocking or assume that `Id` fields are populated at construction time (a pattern that exists in some other ORMs). In Apex, `Id` is null until after a successful `insert`.

**Correct pattern:**

```apex
// WRONG — psr.Id is null before insert
PendingServiceRouting psr = new PendingServiceRouting(...);
SkillRequirement sr = new SkillRequirement(
    RelatedRecordId = psr.Id, // ← null — insert hasn't happened yet
    ...
);
insert psr;
insert sr; // ← sr.RelatedRecordId is null; will fail

// CORRECT — insert PSR first, then use populated Id
PendingServiceRouting psr = new PendingServiceRouting(...);
insert psr; // ← psr.Id is now populated
SkillRequirement sr = new SkillRequirement(
    RelatedRecordId = psr.Id, // ← valid Id
    ...
);
insert sr;
```

**Detection hint:** Any `SkillRequirement` constructor or field assignment referencing `psr.Id` (or equivalent variable name) before a preceding `insert psr` statement is a null-Id bug.

---

## Anti-Pattern 6: Using Queue-Based RoutingType with SkillRequirement Records

**What the LLM generates:** A `PendingServiceRouting` record with `RoutingType = 'QueueBased'` (or omitting `RoutingType` entirely) while also inserting `SkillRequirement` child records.

**Why it happens:** LLMs conflate the two routing modes. The `RoutingType` field controls which engine evaluates the `PendingServiceRouting` record. `QueueBased` routing ignores `SkillRequirement` records entirely; the records insert without error but have no effect.

**Correct pattern:**

```apex
// WRONG — QueueBased routing ignores SkillRequirement records
PendingServiceRouting psr = new PendingServiceRouting(
    RoutingType = 'QueueBased', // ← wrong if skill matching is needed
    ...
);

// CORRECT — SkillsBased routing activates SkillRequirement evaluation
PendingServiceRouting psr = new PendingServiceRouting(
    RoutingType = 'SkillsBased', // ← required for skill matching
    ...
);
```

**Detection hint:** Any code that inserts `SkillRequirement` records alongside a `PendingServiceRouting` record with `RoutingType != 'SkillsBased'` is silently broken.
