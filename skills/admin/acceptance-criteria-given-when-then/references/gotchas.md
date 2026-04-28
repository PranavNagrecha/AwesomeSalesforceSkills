# Gotchas — Acceptance Criteria Given/When/Then

Non-obvious failure modes when authoring behavior-driven AC for Salesforce
features. Each gotcha lists what happens, when it bites, and how to avoid
it in the AC block itself — not in the downstream test code.

---

## Gotcha 1: UI-Coupled Phrasing ("Click the Save button")

**What happens:** The AC reads "When the user clicks the Save button" or
"navigates to the Opportunities tab". Six months later Lightning App Builder
moves the button into a Quick Action overflow, the page layout changes the
tab name, or the org switches to a custom App with its own navigation. The
AC is now wrong but the underlying behavior is unchanged. UAT scripts
written from this AC fail for non-functional reasons.

**When it occurs:** Whenever the AC author defaults to describing the click
path instead of the observable outcome. Especially common for stories that
involve quick actions, dynamic forms, or component visibility rules.

**How to avoid:** Replace "click Save" with "the record is saved", "click
the New button" with "the user creates a new <Object>", "navigate to the
Reports tab" with "the user opens a list of <Reports> they have access to".
The click path belongs in the UAT script, not the AC.

---

## Gotcha 2: Missing Negative-Path Scenarios

**What happens:** The AC enumerates only the happy path. The build team
implements the happy path. UAT passes. In production, the deny case is
never triggered correctly: the validation rule fires the wrong message, the
sharing rule allows the wrong user, the FLS hides the wrong field.

**When it occurs:** When the author treats "the user can do X" as the
complete story and forgets that "the user without permission cannot do X
and gets response Y" is a separate Scenario. Especially common on
permission-set-driven features and validation-rule-driven features.

**How to avoid:** Treat every happy-path Scenario as half-done until you
write its paired deny-case Scenario. The lint script enforces a 1:1 ratio
of "should" to "should not" Scenarios for permission-tagged stories.

---

## Gotcha 3: AC That Tests Implementation Instead of Behavior

**What happens:** The AC says "Given a Process Builder fires when an
Opportunity is updated" or "When the Apex trigger
`OpportunityTrigger.beforeUpdate` runs". This couples the AC to the
implementation tool. When the team migrates Process Builder to Flow per
the platform retirement timeline, the AC is now misleading even though the
behavior is unchanged.

**When it occurs:** When the AC author confuses "what happens" (behavior)
with "how it happens" (implementation). Frequently happens when the author
is also the developer.

**How to avoid:** Drop tool names from the AC. Replace "a Process Builder
fires" with "the system updates the related Account". The choice between
Flow / Apex / Approval / Platform Event is made later, citing
`standards/decision-trees/automation-selection.md`.

---

## Gotcha 4: Ambiguous "Should Work Correctly"

**What happens:** The AC says "the validation should work correctly" or
"the data should be saved properly". There is no observable oracle. UAT
testers interpret "correctly" differently. Apex tests written from this AC
have to invent assertions, and they invent the wrong ones.

**When it occurs:** When the author runs out of patience and falls back to
fuzzy adjectives. Especially common at the end of long stories where the
last few ACs get progressively vaguer.

**How to avoid:** Every Then clause must contain a concrete, named
observable: a field with a value, a record with specific fields, a
validation error with the exact message text, a Task on a named record, an
HTTP request to a named credential. If the AC author cannot name the
observable, the requirement is not yet ready to build.

---

## Gotcha 5: Missing Permission-Boundary Precondition

**What happens:** The AC says "the user can edit Stage" with no Given for
the user's permission set or sharing context. The implementation team picks
a default (usually "anyone with Edit on Opportunity"). The business
intended "only users in the Sales_Rep_PSG who own the record". UAT misses
this because the testing user happens to satisfy both definitions. The
defect surfaces in production when a Service Agent edits a Stage they
should never have been able to touch.

**When it occurs:** Always when the story tags a sharing-relevant object
(Account, Opportunity, Case, Lead, custom objects with private OWD) but
omits the permission Given.

**How to avoid:** A Background block at the top of the AC block names every
user identity, profile, PSG, and the OWD/sharing context. The lint script
fires an error when the story tags a sharing-relevant object but no
"permission set" / "PSG" / "profile" mention exists in the AC.

---

## Gotcha 6: Overlapping AC Across Two Stories

**What happens:** Story A's AC says "the system creates a Task on Stage
update". Story B's AC also says "the system creates a Task on Stage
update". When Story A is delivered first, Story B's AC is now satisfied
trivially. The team marks Story B complete with no work done — but the
nuance that Story B intended (a different Task subject, a different
assignee, a different reminder time) is lost.

**When it occurs:** When two stories touch the same automation point and
their ACs were written by different authors who did not coordinate.

**How to avoid:** When drafting AC, search the existing backlog for the
same When clause. If another story already owns it, either (a) rewrite
this AC to scope only the delta or (b) merge the two stories. Cross-story
AC overlap is a backlog-management smell, not a test-design smell.

---

## Gotcha 7: Single-Record Bias on Trigger / Flow Behavior

**What happens:** The AC describes only "when the user updates the record"
behavior. The Apex test class generated from the AC uses one record. Tests
pass in CI. The first Data Loader load of 200 records fails with
"Apex CPU time limit exceeded" or "Too many SOQL queries" because the
trigger was not bulkified. The AC never asked it to be.

**When it occurs:** Any story where the implementation will be a trigger,
record-triggered flow, or validation rule. Single-record AC produces a
test that exercises only the 1-record path.

**How to avoid:** For every behavior bound to a trigger / flow /
validation, add a Scenario with explicit volume (200 minimum, higher when
the integration shape implies bulk). The lint script flags any AC block
that mentions "trigger", "flow", or "validation rule" without at least one
Scenario containing a count >= 200.

---

## Gotcha 8: Synchronous Then on Async Behavior

**What happens:** The AC says "When the Opportunity is closed, then the
external billing system is updated immediately". The implementation is a
Queueable that fires after the transaction commits. The Then is technically
false at the moment the calling save returns. Apex tests written from this
AC produce flaky CI because they assert before the async job has run.

**When it occurs:** When the AC author does not know (or has not asked) the
architect whether the integration is sync or async.

**How to avoid:** For any callout-bound or job-bound behavior, write the
Then as `Then eventually within N seconds the external system has received
a request to <named credential>`. This signals to test-generator to enqueue
and poll, and signals to UAT to wait before checking the downstream system.
