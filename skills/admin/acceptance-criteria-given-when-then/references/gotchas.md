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
a request to <named credential>`. This signals to test-class-generator to enqueue
and poll, and signals to UAT to wait before checking the downstream system.

---

## Gotcha 9: A Then That Promises Two Outcomes the Save Order Never Delivers Together

**What happens:** The AC reads "Then the save is rejected **and** the requester
receives the acknowledgement", or "Then the record is blocked **and** the case
is routed to the escalation queue". The build cannot satisfy it, and whoever
implements it silently drops half. The reviewer signs off on a criterion that
was never testable.

**When it occurs:** Whenever one criterion mixes a *blocking* outcome with a
*downstream* one. The save order settles it: custom validation rules run at
step 5 ("Runs most system validation steps again… and runs any custom
validation rules"), while assignment rules are step 9, auto-response rules step
10, escalation rules step 12 and entitlement rules step 15
(`apexdev.txt` L15442, L15449, L15450, L15461, L15471). A rejected save never
reaches steps 9–15. The same passage bites a second way: after a workflow field
update, "Custom validation rules, flows, duplicate rules, processes built with
Process Builder, and escalation rules aren't run again"
(`apexdev.txt` L15455–15457) — so an AC that expects a validation rule to
re-fire on the workflow-updated values is asserting a re-run that does not
happen.

**How to avoid:** Split the criterion at the save boundary. One Scenario asserts
the rejection and the unchanged record state; a separate Scenario asserts that
no downstream artefact fired for that attempt (see `references/worked-examples.md`
AC-006.1 and AC-006.3). If both must be true, they are two criteria against one
requirement, not one criterion with an `And`.

---

## Gotcha 10: "The Rule Assigns It" Has Two Outcomes, and the AC Only Ever Names One

**What happens:** The criterion says "Then the case is routed to the Billing
queue". It is silent about what happens to a case that matches no entry. The
build ships, the first unmatched case appears, and its owner is whatever the
org's fall-through happens to be — often the integration user, which no queue
list view shows. Nobody notices until a customer chases.

**When it occurs:** On every criteria-driven rule engine, because they all
define an order and a fall-through. Assignment rule entries are evaluated in
file order — "Rules are processed in the order they appear within the
AssignmentRules container" (`api_meta.txt` L23712–23713) — and the fall-through
is a separate org setting: `CaseSettings.defaultCaseOwner` "Specifies the
default owner of a case when assignment rules fail to locate an owner"
(`api_meta.txt` L111700–111701). Escalation rules have the same shape:
"Escalation rules are processed in the order they appear in the EscalationRules
container" (`api_meta.txt` L59421–59423), so an entry placed after a broader one
is unreachable.

**How to avoid:** For every rule-type requirement, write a criterion whose Given
is "a record matching no entry" and whose Then names the fall-through owner
explicitly. Where entry order decides the outcome, say which entry is first in
the Given. The checker fails a rule-type requirement that has no criterion
marked `negative: true`.

---

## Gotcha 11: A Criterion Marked "Automated in Apex" That the Test Cannot Actually Trigger

**What happens:** The AC is handed to the test generator as automatable. The
generated test inserts a Case, asserts the queue owner, and fails — or worse,
passes for the wrong reason because the test user happened to be the fall-through
owner. The team concludes the rule is broken and rewrites working metadata.

**When it occurs:** On any assignment-rule criterion, because rules do not run
on an API insert unless the caller asks. In Apex the ask is
`Database.DMLOptions.assignmentRuleHeader`, set on the record before insert with
either `useDefaultRule` or an `assignmentRuleId` (`apexdev.txt` L8530–8560); and
`useDefaultRule` "affects only the default assignment rule and does not disable
other existing assignment rules on the object"
(`apexrefguide.txt` L148033–148034). There is a second trap in the same place:
with no assignment rules in the org, in API version 30.0 and later a record
created with `useDefaultRule` set to true "is unassigned and doesn't get assigned
to the default owner" (`apexdev.txt` L8566–8569) — the opposite of the pre-30.0
behaviour a lot of older test code assumes. Outside Apex the defaults disagree
across tools: Data Loader's "Assignment rule" setting is blank until populated
and "overrides Owner values in your CSV file"
(`salesforce_data_loader.txt` L379–383); Bulk API 2.0's `assignmentRuleId` is
Optional on the job resource (`api_asynch.txt` L1591–1595); REST "defaults to
using the active assignment rules" when the header is absent
(`api_rest.txt` L691–694).

**How to avoid:** Put the entry path into the Given, not into the test author's
head: "Given the insert carries `assignmentRuleHeader.useDefaultRule = true`" for
an Apex criterion, "Given Data Loader's Assignment rule setting holds the id of
`<rule>`" for a load criterion. Two criteria that differ only in entry path are
two criteria, and the load one is manual.

---

## Gotcha 12: A Business-Hours SLA Written as Clock Time

**What happens:** The criterion says "Then the case escalates 8 hours after
creation". The build uses the business-hours clock. A Friday-evening case
escalates on Monday, the tester logs a defect against working metadata, and the
team "fixes" it by moving the entry to `businessHoursSource` = `None` — which
then pages Tier 2 at 02:00 on a Sunday for a Severity 4 case.

**When it occurs:** Any SLA, escalation, entitlement or milestone criterion where
the author writes elapsed time without saying which clock measures it.
`BusinessHours` states it plainly: "Escalation rules are run only during these
hours", and "If business hours are associated with any Holiday records, then
business hours and escalation rules associated with business hours are suspended
during the dates and times specified as holidays"
(`object_reference.txt` L53105, L53107–53108). The milestone equivalent hides in
a sign: `timeLength` on a milestone time trigger is measured against the target
completion date, where "Negative values… correspond to warning time triggers"
and "Positive values… correspond to violation time triggers"
(`api_meta.txt` L59210–59217). "Warn the owner before the SLA is missed" with no
sign is satisfied by a violation trigger.

**How to avoid:** Every elapsed-time Then names three things — the number, the
unit, and the calendar (`businessHoursSource` `None` / `Case` / `Static`,
`api_meta.txt` L59461–59466). Every warning criterion states that the trigger is
before the target. Add one holiday criterion per calendar; a holiday is the
cheapest test that distinguishes the two clocks.

---

## Gotcha 13: A Proof Query Against a Field Nobody Tracks

**What happens:** The criterion's oracle is "the Case History shows the owner
change". The tester opens the related list and it is empty, so the criterion is
recorded as failed even though the routing worked. Or the reverse — the query
returns nothing, the automated check passes vacuously, and a broken rule ships.

**When it occurs:** Whenever a criterion proves an automated change through
history. `CaseHistory` "Represents historical information about changes that have
been made to the associated Case" (`object_reference.txt` L63138–63139), but
history "is available for **tracked fields** of the object"
(`object_reference.txt` L62819) — field history tracking is a per-field setting
that has to be deployed like anything else. The attribution the criterion
usually wants comes from a different setting again: `CaseSettings.defaultCaseUser`
"Specifies the user listed in the Case History related list for automated case
changes from: Assignment rules, Escalation rules, On-Demand Email-to-Case…"
(`api_meta.txt` L111705–111712).

**How to avoid:** State the tracking in the Background, next to the sandbox and
the personas — the way `references/worked-examples.md` § 3 does. If the field
cannot be tracked, pick a different oracle (the record's current value plus a
control record) rather than leaving a query that cannot fail.
