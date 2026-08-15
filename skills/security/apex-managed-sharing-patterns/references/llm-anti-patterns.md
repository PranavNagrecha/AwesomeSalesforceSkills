# LLM Anti-Patterns — Apex Managed Sharing Patterns

Mistakes AI coding assistants reliably make when asked to "share this record with
that user in Apex." These patterns help the consuming agent self-check its own
output before it ships.

## Anti-Pattern 1: Inventing an Apex Sharing Reason on a Standard Object

**What the LLM generates:**

```apex
OpportunityShare s = new OpportunityShare(
    OpportunityId          = opptyId,
    UserOrGroupId          = userId,
    OpportunityAccessLevel = 'Read',
    RowCause = Schema.OpportunityShare.RowCause.Deal_Team__c
);
```

**Why it happens:** Almost every tutorial about Apex managed sharing uses a custom
object (usually `Job__c`, from the official docs), and the model generalises the
`Schema.X__Share.RowCause.Y__c` shape to whatever object the user named. Standard
objects have `__Share` sObjects with `RowCause` fields, so nothing about the shape
looks wrong.

**Correct pattern:**

```
Apex sharing reasons exist ONLY on custom objects. Before generating any
RowCause reference, check whether the target object name ends in __c.

  Target ends in __c   -> Schema.Target__Share.RowCause.Reason__c is valid,
                          provided the SharingReason metadata is deployed.
  Standard object      -> the only RowCause you can set from Apex is 'Manual'
                          (which is also the default, so omit the field).

For a standard object, first evaluate the built-in team feature:
  Account     -> AccountTeamMember
  Opportunity -> OpportunityTeamMember
  Case        -> CaseTeamMember
These write platform-maintained share rows with RowCause = 'Team'.
```

**Detection hint:** grep the generated Apex for `RowCause` where the sObject name
does not contain `__Share` preceded by a `__c`-suffixed object. If the object is
`AccountShare`, `ContactShare`, `OpportunityShare`, `CaseShare`, `LeadShare`, or
any other standard share object and `RowCause` is set to anything other than
`'Manual'`, the code will not compile.

---

## Anti-Pattern 2: Omitting the Revoke Path Entirely

**What the LLM generates:** a `grantAccess(recordId, userId)` method, a trigger
that calls it on `after insert`, and a test that asserts the share row exists.
Nothing removes the row.

**Why it happens:** The prompt is almost always phrased as a grant ("give the
recruiter access"). Revocation is implied by the business rule but never stated,
and the model optimises for the literal request.

**Correct pattern:**

```
Every managed-sharing implementation is a pair, not a method:

  grant(recordIds)  - called on after insert AND after update
  revoke(recordIds) - called when the driving relationship changes or is
                      deleted, filtered by the application's own RowCause

The update path must handle re-assignment: when Recruiter__c changes from
User A to User B, A's share must be deleted in the same transaction that
creates B's. A grant-only implementation leaves A with permanent access.

The delete MUST filter on RowCause, or it will remove Owner, Rule, Team, and
Manual shares that other mechanisms own:

  delete as system [SELECT Id FROM Job__Share
                    WHERE ParentId IN :ids
                      AND RowCause = :Schema.Job__Share.RowCause.Recruiter__c];
```

**Detection hint:** if the generated class has no `delete` against a `__Share`
object, or has one whose WHERE clause omits `RowCause`, it is incomplete. Ask what
happens when the lookup field is cleared.

---

## Anti-Pattern 3: Writing Share Rows in a `before` Trigger

**What the LLM generates:**

```apex
trigger JobTrigger on Job__c (before insert) {
    JobShareService.grantForJobs(Trigger.new);   // ParentId is null here
}
```

**Why it happens:** Models associate "do work on the incoming records" with
`before` triggers because that is the correct context for field defaulting and
validation, which dominates the trigger examples in training data.

**Correct pattern:**

```
Share rows point at a committed record Id. In before insert the record has no
Id, so ParentId is null and the DML fails with REQUIRED_FIELD_MISSING.

Always use after insert / after update for share DML.

ParentId and RowCause are both documented as not updateable, so a share row
cannot be repaired later - it can only be deleted and re-inserted. Getting the
context right the first time is the only option.
```

**Detection hint:** search the generated trigger for `before insert` or
`before update` in the same file as a `__Share` insert. Any co-occurrence is a bug.

---

## Anti-Pattern 4: Per-Record DML Inside the Loop

**What the LLM generates:**

```apex
for (Job__c job : Trigger.new) {
    Job__Share s = new Job__Share(/* ... */);
    insert s;                                  // DML inside a loop
}
```

**Why it happens:** The share object is constructed per record, so the DML gets
written next to the constructor. Single-record examples in documentation reinforce
this — the official `manualShareRead(Id, Id)` sample takes one record because it is
illustrating the share object, not the trigger pattern.

**Correct pattern:**

```
Build a List<Object__Share>, insert once outside the loop, and use the
partial-success form so one invalid row does not roll back the batch:

  List<Database.SaveResult> results =
      Database.insert(shares, false, AccessLevel.SYSTEM_MODE);

Then walk the results. Treat FIELD_FILTER_VALIDATION_EXCEPTION whose message
contains 'AccessLevel' as an expected non-error: it means the requested access
was not more permissive than the object's org-wide default, so the row was
redundant. Log everything else.
```

**Detection hint:** any `insert`, `update`, or `delete` keyword indented inside a
`for` block in the generated handler. Also flag bare `insert shares;` without the
`allOrNone = false` form — a single bad `UserOrGroupId` (an inactive user, a
deleted group) then aborts the entire trigger.

---

## Anti-Pattern 5: Claiming `with sharing` Prevents Share Inserts

**What the LLM generates:** advice such as "mark the service class `without
sharing` so it can insert share records," or the inverse, "`with sharing` will
block the share insert, so this is safe."

**Why it happens:** The keyword is named `sharing`, and the class is about sharing.
The model conflates two unrelated mechanisms.

**Correct pattern:**

```
with sharing / without sharing / inherited sharing control whether the RUNNING
USER'S record-level access is enforced on the SOQL and DML inside the class.
They have nothing to do with permission to write __Share rows.

Permission to write an Apex managed share comes from one place only:
  "Only users with 'Modify All Data' permission can add or change Apex managed
   sharing on a record."  - Apex Developer Guide

So a `with sharing` class CAN insert share rows, and a `without sharing` class
CANNOT insert them if the running user lacks Modify All Data - unless the DML
itself runs in system mode.

At API 67.0, database operations default to user mode and a bare class defaults
to with sharing. The correct construction is therefore:

  - class stays `with sharing` (queries respect the user)
  - the __Share DML alone is explicit:
      Database.insert(shares, false, AccessLevel.SYSTEM_MODE);
```

**Detection hint:** any explanation that ties `with sharing` to the *ability* to
create shares. Also flag `AccessLevel.USER_MODE` on `__Share` DML in code intended
to run for non-admin users — it works in an admin sandbox and fails in production.

---

## Anti-Pattern 6: Skipping the Recalculation Class

**What the LLM generates:** a complete, correct trigger and service class, with no
mention of `Database.Batchable` or the Apex Sharing Recalculation registration.

**Why it happens:** The recalculation class is a separate documentation topic and
is not required to make the happy path work. Everything passes in a scratch org.

**Correct pattern:**

```
An Apex managed sharing implementation is not complete without a recalculation
class, because the platform destroys your share rows on events you do not
control:

  "Salesforce automatically recalculates sharing for all records on an object
   when its organization-wide sharing default access level changes ... all types
   of sharing are removed if the access they grant is considered redundant."

  "When sharing is recalculated, Salesforce also runs all Apex sharing
   recalculations."

Deliverable list for any Apex managed sharing story:
  1. SharingReason metadata (one per distinct reason)
  2. Service class with grant + revoke, both RowCause-scoped
  3. after insert / after update trigger
  4. Database.Batchable recalculation class
  5. Registration under Object Manager -> [object] -> Apex Sharing Recalculation
     (Salesforce Classic only)
  6. Tests using System.runAs that assert visibility AND revocation
```

**Detection hint:** if the answer has no class implementing
`Database.Batchable<sObject>`, ask what rebuilds the shares after an OWD change.
There is no good answer other than "nothing."

---

## Anti-Pattern 7: Testing Share Row Counts Instead of Actual Visibility

**What the LLM generates:**

```apex
insert job;
Assert.areEqual(2, [SELECT COUNT() FROM Job__Share WHERE ParentId = :job.Id]);
```

**Why it happens:** Row-count assertions are easy to generate and always pass when
the insert succeeded. They look like they test sharing.

**Correct pattern:**

```
A __Share row that exists is not proof of access. Assert what the target user
can actually read:

  System.runAs(recruiter) {
      Assert.areEqual(1, [SELECT COUNT() FROM Job__c WHERE Id = :job.Id]);
  }

And always include the negative half - remove the driving relationship and
assert the count drops to 0. The revoke path is the one that becomes a
compliance finding, and a row-count test never exercises it.

Note that COUNT() inside runAs reflects the running user's record access, which
is the only assertion that proves the sharing model works end to end.
```

**Detection hint:** a test class that touches `__Share` but never calls
`System.runAs`. Also flag tests that assert only on the grant and never on the
revoke.
