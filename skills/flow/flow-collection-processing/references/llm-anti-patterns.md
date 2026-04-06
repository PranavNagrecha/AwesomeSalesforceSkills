# LLM Anti-Patterns — Flow Collection Processing

Common mistakes AI coding assistants make when generating or advising on Flow collection processing with Loop, Collection Filter, Collection Sort, and Transform elements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using a Loop to filter a collection instead of Collection Filter

**What the LLM generates:**

```
[Loop: For each record in allContacts]
    [Decision: Is Status = Active?]
        Yes --> [Assignment: Add to activeContacts collection]
        No --> (skip)
```

**Why it happens:** LLMs default to explicit loops because they map to traditional programming. The Collection Filter element does the same operation in a single step with no loop overhead.

**Correct pattern:**

```
[Collection Filter: Filter allContacts where Status = Active --> activeContacts]
```

Collection Filter is declarative, cleaner, and avoids the loop-based pattern that complicates the flow canvas.

**Detection hint:** Loop + Decision + Assignment pattern where the only purpose is filtering a collection by field criteria.

---

## Anti-Pattern 2: Placing DML inside a Loop when processing a collection

**What the LLM generates:**

```
[Loop: For each Contact in collection]
    [Update Records: Update this Contact's Account]
```

**Why it happens:** LLMs model the update per-item because it is the simplest mental model. Each iteration consumes a DML statement, quickly hitting the 150-DML limit.

**Correct pattern:**

```
[Loop: For each Contact in collection]
    [Assignment: Set fields on currentAccount, add to accountsToUpdate collection]
[Update Records: Update all records in accountsToUpdate]
```

Accumulate changes in a collection variable inside the loop. Perform one bulk DML after the loop exits.

**Detection hint:** Create/Update/Delete Records element that is a direct child of a Loop element.

---

## Anti-Pattern 3: Not using the Transform element for collection-to-collection mapping

**What the LLM generates:**

```
[Loop: For each Opportunity]
    [Assignment: Create new Task record variable]
    [Assignment: Set Task.Subject = Opportunity.Name]
    [Assignment: Set Task.WhatId = Opportunity.Id]
    [Assignment: Add Task to tasksCollection]
```

**Why it happens:** LLMs use loops with multiple assignments to create one record type from another. The Transform element does this mapping in a single declarative step.

**Correct pattern:**

```
[Transform: Map Opportunities to Tasks]
    Source: opportunityCollection
    Target: taskCollection (Task SObject)
    Mappings:
        Task.Subject = Opportunity.Name
        Task.WhatId = Opportunity.Id
```

**Detection hint:** Loop that creates new SObject variables from an existing collection with field-by-field assignments.

---

## Anti-Pattern 4: Sorting a collection inside a Loop instead of using Collection Sort

**What the LLM generates:**

```
"Flow does not have a native sort capability, so you need to use Apex
to sort the collection before displaying it."
```

**Why it happens:** Older training data predates the Collection Sort element (introduced in Spring '22). LLMs recommend Apex or manual sorting when a built-in element exists.

**Correct pattern:**

```
[Collection Sort: Sort contactCollection by LastName ASC, FirstName ASC]
```

Collection Sort supports multiple sort fields and ascending/descending order.

**Detection hint:** Advice to use Apex invocable action or manual sorting when the need is straightforward single-object collection sorting.

---

## Anti-Pattern 5: Forgetting to initialize the accumulator collection variable before the Loop

**What the LLM generates:**

```
[Loop: For each record]
    [Assignment: Add record to outputCollection]
    // outputCollection was never created — runtime error
```

**Why it happens:** LLMs assume the collection variable exists. In Flow, you must explicitly create a collection variable (e.g., `outputCollection` of type `Record Collection`) before you can add items to it in a Loop.

**Correct pattern:**

1. Create a variable `outputCollection` of type `Record Collection (SObject)`
2. Ensure it is created before the Loop element in the flow path
3. Inside the Loop, use Assignment to add items to it

The collection variable must exist and be of the correct SObject type before the first `Add` assignment.

**Detection hint:** Assignment element adding to a collection variable that is not declared or initialized before the loop.

---

## Anti-Pattern 6: Using Loop + Assignment to count records instead of collection size

**What the LLM generates:**

```
[Set counter = 0]
[Loop: For each record in collection]
    [Assignment: counter = counter + 1]
[Decision: Is counter > 10?]
```

**Why it happens:** LLMs use the explicit counting pattern from imperative programming. Flow provides a direct way to check collection size using formula resources.

**Correct pattern:**

Use a formula or direct comparison:

```
[Decision: {!myCollection.size} > 10]
```

No loop needed to count records in a collection.

**Detection hint:** Loop whose only purpose is incrementing a counter variable to determine collection size.
