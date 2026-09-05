# LLM Anti-Patterns — Activity and Task Patterns

Common mistakes AI coding assistants make when working with Task/Event/Activity.

## Anti-Pattern 1: Querying the abstract Activity object

**What the LLM generates:** `SELECT Id, Subject FROM Activity WHERE ...`

**Why it happens:** Model treats Activity like any other SObject.

**Correct pattern:**

```
Activity is a read-only abstract parent. Query Task or Event directly.
If you need both in one call, query separately and union client-side,
or use ActivityHistory/OpenActivity subqueries from the parent record.
```

**Detection hint:** SOQL `FROM Activity` as the primary object.

---

## Anti-Pattern 2: Polymorphic query without TYPEOF

**What the LLM generates:** `SELECT Id, Subject, What.Name FROM Task` expecting Name to always work.

**Why it happens:** Model treats WhatId like a normal lookup.

**Correct pattern:**

```
WhatId is polymorphic. Only fields on the common parent (Name via
TYPEOF cast) are accessible. Use:

SELECT Id, Subject, What.Type,
  TYPEOF What
    WHEN Account THEN Name, Industry
    WHEN Opportunity THEN Amount
  END
FROM Task

Without TYPEOF, only What.Type is reliably available.
```

**Detection hint:** SOQL accessing `What.Name` on Task/Event without TYPEOF.

---

## Anti-Pattern 3: Looping DML to create tasks

**What the LLM generates:**

```
for (Opportunity o : opps) {
    insert new Task(WhatId = o.Id, Subject = 'Follow up');
}
```

**Why it happens:** Model writes row-at-a-time code.

**Correct pattern:**

```
Collect tasks in a List<Task>, then insert once:
List<Task> tasks = new List<Task>();
for (Opportunity o : opps) tasks.add(new Task(WhatId=o.Id, ...));
insert tasks;

DML in loops hits the 150-statement governor fast.
```

**Detection hint:** Apex with `insert new Task(...)` inside a `for` loop.

---

## Anti-Pattern 4: Adding custom field only to Task

**What the LLM generates:** Metadata proposing a custom field on Task object.

**Why it happens:** Model treats Task and Event as independent objects.

**Correct pattern:**

```
Custom fields are added to the Activity object and propagate to both
Task and Event. If a field only makes sense for one, enforce via
validation rules on IsTask/IsEvent. Otherwise expect it on both.
```

**Detection hint:** Custom field metadata targeted at `Task` object directly — should be on `Activity`.

---

## Anti-Pattern 5: Updating ActivityHistory records

**What the LLM generates:** Apex DML attempting to update an ActivityHistory record.

**Why it happens:** Model doesn't know ActivityHistory is a projection.

**Correct pattern:**

```
ActivityHistory and OpenActivity are read-only projections of Task
and Event on activity-enabled parents. Update the underlying Task or
Event record instead. DML on ActivityHistory fails with
"This object does not support DML."
```

**Detection hint:** Apex `update ahList` where `ahList` is `List<ActivityHistory>`.

---

## Anti-Pattern 6: Bare `insert tasks;` in a backfill or trigger

**What the LLM generates:**

```
List<Task> tasks = new List<Task>();
for (Opportunity o : opps) { tasks.add(new Task(WhatId = o.Id, OwnerId = o.OwnerId)); }
insert tasks;
```

**Why it happens:** The model has correctly learned "bulkify" and stops
there. The DML verb is the shortest thing that compiles, and nothing in
the code hints at the two side effects the platform attaches to it.

**Correct pattern:**

```
The bare verb has nowhere to put DMLOptions, so you get all-or-nothing
rollback AND an assignment email per task — creating or modifying a task
is one of the events EmailHeader.triggerUserEmail governs.

Database.DMLOptions dml = new Database.DMLOptions();
dml.optAllOrNone = false;
dml.EmailHeader.triggerUserEmail = false;
List<Database.SaveResult> rs =
    Database.insert(tasks, dml, AccessLevel.SYSTEM_MODE);
// then iterate rs and report the failures
```

**Detection hint:** a file that declares `List<Task>` or `List<Event>`
and contains `insert <var>;` with no `optAllOrNone` and no
`Database.insert(..., false)` anywhere in it. This is check A5 in
`scripts/check_activity_and_task_patterns.py`.

---

## Anti-Pattern 7: Deploying `ActivitiesSettings` to turn Shared Activities on

**What the LLM generates:** an `Activities.settings-meta.xml` containing
`<allowUsersToRelateMultipleContactsToTasksAndEvents>true</...>`, usually
as step one of a "relate a task to several contacts" plan.

**Why it happens:** Every other element in that file is deployable, and
the field name reads like a switch. The deploy then *succeeds*, so
nothing contradicts the model's assumption.

**Correct pattern:**

```
That field has been read-only in every API version since v36.0. The
deploy succeeds and changes nothing. Shared Activities is a Setup-only,
effectively one-way org change a human must make first.

Assert it instead of assuming it: TaskWhoIds and the TaskRelations child
relationship only exist once it is on, and the ceiling is one lead OR up
to 50 contacts per task.
```

**Detection hint:** the element name appearing anywhere in a `.settings`
file. This is check M1 in `scripts/check_activity_and_task_patterns.py`.

---

## Anti-Pattern 8: FLS metadata for a shared Activity field on one child only

**What the LLM generates:** a permission set with a single
`fieldPermissions` entry for `Task.Outcome__c`, because the user asked
about tasks.

**Why it happens:** The model scopes the permission to the object named
in the request and treats an unmentioned object as untouched.

**Correct pattern:**

```
Task and Event share field-level security. A missing entry in the
metadata is treated as FLS being disabled, not as "leave it alone", so a
Task-only permission set can strip Event access on deploy. Always write
both entries.
```

**Detection hint:** `fieldPermissions` naming `Task.<field>` without a
matching `Event.<field>` (or vice versa). This is check M4 in
`scripts/check_activity_and_task_patterns.py`.
