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
