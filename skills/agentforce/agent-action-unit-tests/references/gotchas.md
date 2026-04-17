# Gotchas — Agent Action Unit Tests

## Gotcha 1: Test.startTest/stopTest required for async

**What happens:** Queueable from inside Invocable doesn't run in test without the boundary.

**When it occurs:** Action enqueues a Queueable.

**How to avoid:** Always wrap the invocation in Test.startTest/stopTest.


---

## Gotcha 2: @InvocableVariable default values

**What happens:** Missing fields on Request become null, not default.

**When it occurs:** Manual construction in test.

**How to avoid:** Explicitly set every field in Request; don't rely on defaults.


---

## Gotcha 3: Asserting on user_message strings

**What happens:** UX change breaks 40 tests at once.

**When it occurs:** Copy-pasted UX copy in asserts.

**How to avoid:** Assert on reason_code only; assert UX copy in one dedicated 'copy-deck' test.

