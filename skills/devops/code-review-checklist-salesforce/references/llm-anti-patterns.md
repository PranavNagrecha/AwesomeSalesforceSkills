# LLM Anti-Patterns — Code Review Checklist Salesforce

Common mistakes AI coding assistants make when generating or advising on Code Review Checklist Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Approving “small batch only” triggers

**What the LLM generates:** “This trigger is fine because typical updates are under ten records.”

**Why it happens:** Training data favors average-case reasoning; Salesforce always reserves the right to deliver up to 200 records per invocation.

**Correct pattern:**

```
Treat 200 rows as the default test and review scenario for synchronous trigger code unless the platform API guarantees a smaller chunk (document with official reference).
```

**Detection hint:** Phrases like “low volume”, “usually small”, “only marketing uses it” without a 200-row test or bulk map pattern.

---

## Anti-Pattern 2: Equating coverage percent with review pass

**What the LLM generates:** “Coverage is 85%, so the change is safe to deploy.”

**Why it happens:** CI output prominently displays coverage; models latch onto the number.

**Correct pattern:**

```
Require assertions, branch coverage on error paths, and bulk tests; cite code coverage best practices that warn against coverage as the only metric.
```

**Detection hint:** No mention of assertions, only a coverage percentage in the conclusion.

---

## Anti-Pattern 3: Java-style synchronized blocks for “thread safety”

**What the LLM generates:** Suggestions to synchronize Apex statics as if multi-threaded user code ran in parallel within one transaction.

**Why it happens:** Cross-language pattern transfer. In Apex, `synchronized` is only a reserved keyword, and a static variable is static only within the scope of one Apex transaction — it is reset across transaction boundaries, so there is no cross-request shared memory to guard.

**Correct pattern:**

```
Explain per-transaction static scope; use statics only with clear reset semantics in tests.
When two requests really can update the same record, lock it with SELECT ... FOR UPDATE.
```

**Detection hint:** Keywords `synchronized`, “race condition” between two Apex requests in the same org, or a static used as a cross-user cache.

---

## Anti-Pattern 4: Recommending `seeAllData=true` by default

**What the LLM generates:** “Add `seeAllData=true` so the test can query standard PricebookEntry.”

**Why it happens:** Shortest path to green tests when org data dependencies are misunderstood.

**Correct pattern:**

```
Create the Product2 and PricebookEntry rows in `@testSetup`, using Test.getStandardPricebookId()
for the standard price book (it returns the ID even when the test cannot query org data);
reserve `seeAllData` for rare cases with team approval.
```

**Detection hint:** `@IsTest(SeeAllData=true)` added without a documented exception in the review notes.

---

## Anti-Pattern 5: Blanket “use without sharing for performance”

**What the LLM generates:** Refactor every service class to `without sharing` to avoid sharing row checks.

**Why it happens:** Confusion between sharing overhead and legitimate need for system-level operations.

**Correct pattern:**

```
Default to least privilege; scope elevated sharing to documented methods; pair with USER_MODE or stripInaccessible for returned data.
```

**Detection hint:** `without sharing` on UI-facing controllers or broad service facades with no threat-model comment.

---

## Anti-Pattern 6: "Triggers always run in system mode"

**What the LLM generates:** "No need to check FLS here — Apex triggers run in system context, so the query sees every field and record."

**Why it happens:** For most of Apex's history system mode was the default, and older training text says so flatly. The model does not read the trigger's `-meta.xml`.

**Correct pattern:**

```
Read the trigger's apiVersion first. A trigger has no sharing keyword and runs without sharing,
but at 67.0+ its unqualified SOQL/SOSL/DML run in user mode, re-applying the user's FLS and sharing.
Require an explicit WITH USER_MODE / WITH SYSTEM_MODE on every trigger and handler query.
```

**Detection hint:** "system context" or "system mode" asserted about a trigger with no mention of its API version.
