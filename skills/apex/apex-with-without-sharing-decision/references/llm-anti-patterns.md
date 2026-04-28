### LLM Anti-Patterns — Apex With / Without / Inherited Sharing Decision

Common mistakes AI coding assistants make when authoring or reviewing
the sharing keyword on an Apex class.

## Anti-Pattern 1: Defaulting to `without sharing` for "convenience"

**What the LLM generates:** When the user reports a permission error
during development, the model rewrites the controller as
`without sharing` to make the test pass.

**Why it happens:** The model treats a permission exception like any
other test failure — pick the path of least resistance. It does not
recognize that flipping the class to system context is a security
regression, not a bug fix.

**Correct pattern:**

```apex
// Keep the controller `with sharing`. Diagnose the permission error:
//   1. Is the user missing a permission set? Add it.
//   2. Is one specific query needing system context? Override THAT
//      query with WITH SYSTEM_MODE and document why.
//   3. Is the class doing org-wide work that doesn't belong in a
//      controller at all? Move it to a separate `without sharing`
//      service class with a // reason: comment.
public with sharing class MyController {
    // ...
}
```

**Detection hint:** PR diff that flips an `@AuraEnabled` class from
`with sharing` to `without sharing` with no `// reason:` comment and no
business-logic justification in the description.

---

## Anti-Pattern 2: `with sharing` on a System-context utility that needs elevation

**What the LLM generates:** Applying `with sharing` to every class
"because security." A nightly batch that needs to aggregate across all
opportunities ships as `with sharing` and silently under-counts because
the integration user has limited perimeter.

**Why it happens:** The model has internalized "with sharing = safe"
and applies it as a global default without checking whether the class
needs system context.

**Correct pattern:**

```apex
// reason: org-wide revenue aggregation must include opportunities
//         outside the integration user's role hierarchy.
public without sharing class RevenueAggregationBatch
        implements Database.Batchable<SObject> {
    // ...
}
```

**Detection hint:** Batch / Schedulable / Queueable class declared
`with sharing` with no comment justifying why user-scoped behavior is
correct for the job.

---

## Anti-Pattern 3: Forgetting class sharing is inherited through called methods

**What the LLM generates:** Author reviews a `with sharing` controller
and concludes "this code is safe" without inspecting the helper classes
it calls. One of the helpers is bare or `without sharing`, and queries
inside the helper run unrestricted.

**Why it happens:** The model's mental model treats each class as an
isolated unit and does not propagate sharing analysis across method
boundaries.

**Correct pattern:**

```apex
public with sharing class CaseController {
    @AuraEnabled
    public static List<Case> getMyCases() {
        return CaseSelector.recentForCurrentUser();
    }
}

// CaseSelector should be `inherited sharing`, not bare:
public inherited sharing class CaseSelector {
    public static List<Case> recentForCurrentUser() {
        return [SELECT Id FROM Case WHERE OwnerId = :UserInfo.getUserId()];
    }
}
```

**Detection hint:** A `with sharing` entry point that calls into a
class with no sharing keyword. Check the call graph during review.

---

## Anti-Pattern 4: Confusing `WITH USER_MODE` with the class-level keyword

**What the LLM generates:** Suggests `WITH USER_MODE` on every query
as a substitute for declaring `with sharing` on the class — or
conversely, declares `with sharing` and adds `WITH USER_MODE` to every
query, doubling enforcement and surprising users with unexpected FLS
errors.

**Why it happens:** The model conflates the two enforcement layers.
Class keyword controls **sharing only**; `WITH USER_MODE` enforces
**sharing PLUS field/object permissions** on a single statement.

**Correct pattern:**

```apex
// Class default: with sharing.
// Per-query elevation for one statement that needs system context:
public with sharing class MetricsController {
    @AuraEnabled(cacheable=true)
    public static Integer countAllOpenCases() {
        // reason: org-wide KPI tile, must not filter by user perimeter
        return [
            SELECT COUNT() FROM Case WHERE IsClosed = false WITH SYSTEM_MODE
        ];
    }
}
```

**Detection hint:** PRs that add `WITH USER_MODE` to every query in a
`with sharing` class (redundant, and silently introduces FLS
enforcement that may break the page) — or use `WITH USER_MODE` as the
sole enforcement mechanism on a bare class.

---

## Anti-Pattern 5: Assuming Triggers run `with sharing`

**What the LLM generates:** Suggests `with sharing` on a trigger
handler class to "make the trigger respect sharing." But the trigger
body itself runs in system context — DML in the trigger ignores
sharing regardless of the handler keyword. Only SOQL queries inside the
handler are affected by the handler's keyword.

**Why it happens:** Model assumes trigger and handler share a single
sharing context. They don't.

**Correct pattern:**

```apex
// Trigger body always runs in system context — the trigger keyword
// only affects SOQL queries inside the handler class.
trigger AccountTrigger on Account (before insert, after update) {
    new AccountTriggerHandler().run();  // DML inside runs system-context
}

// Most handlers want `without sharing` deliberately — the trigger is
// system code and queries should match. Declare it explicitly.
public without sharing class AccountTriggerHandler {
    public void run() { /* ... */ }
}
```

**Detection hint:** PRs adding `with sharing` to a trigger handler
without a clear story for why the queries inside the handler should be
user-scoped. In most trigger-framework codebases, handlers should be
`without sharing` and explicit.

---

## Anti-Pattern 6: Treating bare class as "the same as `with sharing`"

**What the LLM generates:** "This class has no keyword, but it's
called from an `@AuraEnabled` method, so it's `with sharing` by
default — no change needed."

**Why it happens:** Model knows the post-API-v34 default for Lightning
entry points and over-generalizes. In other call paths (called from a
`without sharing` Apex class, anonymous Apex, some legacy contexts),
a bare class still runs effectively `without sharing`.

**Correct pattern:** never ship a bare class. Always declare an
explicit keyword. The repo's checker flags bare classes containing
`@AuraEnabled` annotations.

**Detection hint:** Any production class file where the `class` line
has no `with sharing`, `without sharing`, or `inherited sharing`
keyword.
