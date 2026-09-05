# Gotchas — UAT Test Case Design

Non-obvious behaviors and authoring failures that produce false-pass UAT runs in real Salesforce projects.

---

## Gotcha 1: Testing as System Administrator

**What happens:** The case runs green. The feature ships. In production, regular
users hit a P1 permission error or — worse — bypass a validation rule that was
scoped to a custom permission Sys Admin already had.

**When it occurs:** Whenever the `permission_setup` block is missing, vague
("the right permissions"), or names the System Administrator profile.

**How to avoid:** Every case must name a non-Admin profile + the explicit PSG.
The check_uat_case.py script enforces this — `permission_setup` cannot be empty
and the persona cannot be "System Administrator." For deny cases, the persona is
named WITHOUT the PSG so the deny is the test result, not the absence of setup.

---

## Gotcha 2: Missing Data Setup → Setup-Reason Failures

**What happens:** The case fails because the parent Account did not exist, the
required picklist value was retired, or the validation rule needed a Contact
that was not seeded. The team logs a feature defect when there was none.

**When it occurs:** When `data_setup` is empty or the case description assumes
"there will be records." Especially common in fresh sandboxes.

**How to avoid:** Make `data_setup` an explicit ordered list: every record,
every import file, every parent the steps depend on. For >5 records or
relationship-heavy seeds, cite `templates/apex/tests/TestDataFactory.cls` and
invoke from anonymous Apex before the run begins.

---

## Gotcha 3: UI-Coupled Steps That Break on Lightning vs Classic

**What happens:** The case steps reference "click the New button on the related
list" but the user is in Classic (or vice versa) where the action is in a
different UI region. Tester reports "step 3 unclear, blocked."

**When it occurs:** When step language assumes one UI mode without saying so.
Also bites when the persona's profile defaults to a different UI mode than the
case author assumed.

**How to avoid:** State the **form factor** in `precondition`, not just
"Lightning". A record-page override carries a `formFactor` whose values are
distinct pages: `Large` "represents the Lightning Experience desktop
environment", `Small` "represents the Salesforce mobile app on a phone or
tablet", and "The null value (which is the same as specifying no value)
represents Salesforce Classic" (`api_meta.txt` L39827–39835). Three form
factors means up to three different pages under one story, and a case that
says only "Lightning" does not say which. Then cite UI elements by developer
name where possible rather than visible label, since labels move with
translations and release upgrades.

---

## Gotcha 4: Missing Pass/Fail Evidence

**What happens:** The tester writes "Pass" with no screenshot or recording.
Three weeks later the BA cannot prove the AC was met. The auditor asks for
evidence and finds nothing.

**When it occurs:** When `evidence_url` is left blank because "the tester
remembers." Compounded when the run was on a sandbox that was later refreshed,
destroying any forensic ability to reconstruct.

**How to avoid:** `evidence_url` is required at run time. Tester attaches a
screenshot or screen-recording link (Quip, Drive, internal SharePoint) before
setting `pass_fail`. The check script enforces presence of this field for any
case marked Pass or Fail (Blocked / Not Run are exempt).

---

## Gotcha 5: Over-Testing — One Case Per Click

**What happens:** A 6-step Opportunity wizard produces 36 UAT cases. Reviewers
cannot map them to AC. The run takes 4 hours instead of 1. Negative paths get
dropped under time pressure.

**When it occurs:** When authors decompose by UI action instead of AC scenario.
Often a sign the AC block was skipped and the team is writing scripts from the
story description.

**How to avoid:** Decompose by `ac_id`. If a case has 6 steps in its `steps`
array, that's fine — one AC scenario per case is the contract, not one click
per case.

---

## Gotcha 6: Under-Testing — One Case Per Story

**What happens:** The team writes a single case per user story that walks the
whole feature in one breath. When it fails, no one knows which AC broke. The
RTM cannot close at AC granularity.

**When it occurs:** When stories are written with only narrative requirements
and no Given/When/Then AC. Or when the team is rushing and skipping the
decomposition step.

**How to avoid:** Each AC scenario in the source story produces ≥1 case. If a
story has 4 AC scenarios, the case set has ≥4 cases (more if personas split).
Reject case sets where `case_count < ac_scenario_count`.

---

## Gotcha 7: No Negative Path

**What happens:** Every case passes happy-path. Production ships. Day 2,
a user submits invalid input and the validation rule that should have blocked
the save silently passes because the team never tested the failure path.

**When it occurs:** When the case set is generated from happy-path AC only and
the negative scenarios in the AC block were ignored.

**How to avoid:** ≥1 case per story with `negative_path: true`. The check
script enforces this per-story — a story with no negative-path case fails the
gate. Negative cases come from the AC's failure scenarios; do not invent new
ones.

---

## Gotcha 8: No Traceability to AC

**What happens:** Cases lack `story_id` or `ac_id`. The RTM cannot reconcile
which AC was proven. When an auditor asks "show me the case that proved
AC-734-2," the team cannot answer.

**When it occurs:** When cases are authored as flat scripts without the
schema's mandatory ID fields, or when an "untraceable" placeholder is used
because the AC was not stable when the case was written.

**How to avoid:** `story_id` and `ac_id` are required in the schema. Cases
written before the AC stabilizes are drafts, not deliverables — block them
from execution until both IDs resolve to real artifacts.

---

## Gotcha 9: Permission Set Group Recalculation Lag

**What happens:** The case assigns a PSG, the tester immediately runs the
script, and the steps fail because the entitlement has not propagated yet.
False-fail logged.

**When it occurs:** Right after a fresh PSG assignment, and after any deploy
that changes a permission set inside the group — the group goes stale, not
just the assignment.

**How to avoid:** Stop guessing at a delay and read the status.
`PermissionSetGroup.Status` is a filterable, restricted picklist with exactly
four values: `Updated` ("The group is current"), `Outdated` ("The group
requires recalculation"), `Updating` ("The group is in recalculation mode")
and `Failed` ("The group recalculation failed")
(`object_reference.txt` L217708–217712; the same enumeration is on the
metadata type at `api_meta.txt` L95345–95352). Gate the run on it:

```sql
SELECT DeveloperName, Status FROM PermissionSetGroup
WHERE  DeveloperName IN ('Support_Agent')
```

Anything but `Updated` means the precondition is not met and the case is
`Blocked`, not `Fail`.

**UNVERIFIED (2026-09-05):** the "log out and log back in" advice that used to
sit here appears in none of the extracted guides. It is cheap and harmless, so
keep it as a tester habit — but the status query is the gate, and a case whose
only protection is a re-login is still guessing.

---

## Gotcha 10: A Permission Set Cannot Deny, So a Deny Case Must Name an Absence

**What happens:** The author writes a deny case as "assign the persona the
`Read_Only_PS` permission set, then confirm they cannot edit." The tester
assigns it, the edit succeeds anyway, and a P1 security defect is raised
against a build that is behaving correctly.

**When it occurs:** Whenever a deny case is written as a positive setup step —
"give them the restricted permission set" — instead of as a withheld one.
Especially common when the author is thinking in terms of profiles, where a
setting can be off.

**How to avoid:** Permission sets are additive by construction: "Represents a
set of permissions that's used to grant more access to one or more users
without changing their profile or reassigning profiles. **You can use
permission sets to grant access but not to deny access.**"
(`api_meta.txt` L94703–94705). So a deny case's `permission_setup` names what
is *not* assigned, and says so explicitly enough that a helpful tester does
not add it back:

```yaml
permission_setup:
  - "Assign Billing_Case_Access only"
  - "DO NOT add the tester to Tier_2_Support_Queue — the absence is the test condition"
  - "Confirm neither viewAllRecords nor modifyAllRecords is set on Case for that grant"
```

The last line matters because those two fields are the ones that override the
sharing model: they grant access "regardless of the sharing settings for the
object" and are "Similar to the Modify All Data user permission, but limited
to the individual object level" (`api_meta.txt` L95085–95092, L95109–95116).
A deny case that leaves them unchecked is not testing the sharing model.

---

## Gotcha 11: An API Load Skips the Layout Half of Validation, Not the Custom Rules

**What happens:** Two opposite failures from the same misunderstanding. Either
the team writes only a UI case and is surprised when a loader run inserts rows
with a layout-required field blank; or the team writes a loader case "because
validation rules don't fire under the API", the rule fires, and they log a
defect against correct behaviour.

**When it occurs:** Any story with both a UI path and a Data Loader, Bulk API
or REST path — which is most intake and migration stories.

**How to avoid:** Read the save order and split the case by what each path
runs. At **step 2**, "For requests from a standard UI edit page" Salesforce
checks "Compliance with layout-specific rules" and "Required values at the
layout level and field-definition level", while "For requests from other
sources such as an Apex application or a SOAP API call, Salesforce validates
foreign keys, field formats, maximum field lengths, and restricted picklists"
(`apexdev.txt` L15419–15421, L15436–15437) — no layout rules, no layout-level required
fields. At **step 5**, Salesforce "Runs most system validation steps again…
and runs any custom validation rules", for every source
(`apexdev.txt` L15442–15443). And before any of it, "the browser runs
JavaScript validation if the record contains any dependent picklist fields…
**No other validation occurs on the client side**"
(`apexdev.txt` L15404–15406).

So: custom validation rules are proven by either case. Layout-required fields
and dependent-picklist restriction are proven only by the UI case. Write both,
and write down which half each one covers.

---

## Gotcha 12: An Empty List View Is Not a Deny

**What happens:** The deny case's step is "search the list views; the record
does not appear." It does not appear, the case passes, and in production the
persona opens the record by pasting its id.

**When it occurs:** Any org with a **scoping rule** on the object, and any
deny case whose only oracle is a list view or a search result.

**How to avoid:** Two distinct mechanisms produce an empty list, and only one
of them is a deny. A restriction rule "has `enforcementType` set to `Restrict`
and controls the access that specified users have to designated records"; a
scoping rule "has `enforcementType` set to `Scoping` and **controls the
default records that your users see without restricting access**"
(`api_meta.txt` L106018–106020). A scoping rule therefore empties the list and
leaves the direct-id path open.

The second trap is the query most people reach for instead. `UserRecordAccess`
"doesn't consider whether a user's access is blocked by a restriction rule" —
"If a user's access is blocked even though query results state that they
should have access, check to see if a restriction rule on the object prevents
the user's access" (`object_reference.txt` L303130–303131, L303228–303230).
So the SOQL can say `HasReadAccess = true` for a record the tester genuinely
cannot open.

A sound deny case therefore has three steps, not one: the list view is empty,
the **direct record id** is refused, and `UserRecordAccess` agrees. Plus a
setup line ruling out a scoping or restriction rule, so the pass is
attributable. (`UserRecordAccess` also caps at 200 ids per query —
`object_reference.txt` L303231 — so a bulk deny case pages the ids.)

---

## Gotcha 13: A Refresh Inside the UAT Window Destroys the Build, and the Copied Jobs Run

**What happens:** Halfway through the cycle the sandbox is refreshed. The
build is gone, the seeded data is gone, and the passing evidence now points at
records that no longer exist. Separately, from the moment the refresh
completes, production's scheduled jobs start firing in the sandbox.

**When it occurs:** Whenever the UAT window is planned without the refresh
calendar in front of it, which is easy because a Full sandbox can only be
refreshed every 29 days and so feels far away
(`admin/sandbox-strategy` § Type Capacities and Refresh Windows).

**How to avoid:** Book the window against the refresh date and record both in
the run context, then treat the copied schedule as a precondition rather than
a surprise. CronTrigger records are copied with `State = 'WAITING'` and begin
evaluating their next fire time immediately
(`devops/sandbox-data-isolation-gotchas` § Gotcha 3) — and that schedule is
readable, which is what makes a time-based case runnable at all:

```sql
SELECT CronJobDetail.Name, State, NextFireTime, PreviousFireTime
FROM   CronTrigger
ORDER  BY NextFireTime
```

`NextFireTime` is "The next date and time the job is scheduled to run. null if
the job is not scheduled to run again" and `PreviousFireTime` is "The most
recent date and time the job ran. null if the job has not run before current
local time" (`object_reference.txt` L86765–86771, L86780–86786). A time-based
case's precondition is that query's output, not a stopwatch — the tester
cannot advance the clock, only read it.

---

## Gotcha 14: `Blocked` Reported as `Fail` Corrupts the Defect Data

**What happens:** Deliverability was reset by a refresh, so the acknowledgement
never arrived. The tester records `Fail`. A P1 defect is raised against the
auto-response rule, an admin spends a day on a rule that was always correct,
and the defect log now says the build had a P1 it never had.

**When it occurs:** Every time the run sheet offers Pass/Fail as a binary, and
whenever the person triaging is the person who ran the case.

**How to avoid:** Keep all four enum values live — `Pass`, `Fail`, `Blocked`,
`Not Run` — and name who decides between the last three. `Blocked` means the
precondition was not met: the PSG status was `Outdated`, deliverability was
`System Email Only`, the seeded record was missing. A `Blocked` row still gets
an owner and a closing note, because a sandbox refreshed mid-cycle is a process
defect even when the build is fine — but it never gets a `defect_id` against
the build. And a re-run after the fix is a **new run-sheet row**: editing the
original deletes the evidence the defect was raised against.

---

## Gotcha 15: An Escalation That Notifies Without Reassigning Leaves No History Row

**What happens:** The negative escalation case asserts "no owner-change row in
`CaseHistory`", finds none, and passes. In production the escalation was
firing all along — it was configured to notify, not to reassign, so it never
wrote a history row to find.

**When it occurs:** Any escalation entry whose action is a notification, and
any case whose sole oracle is `CaseHistory`.

**How to avoid:** Assert on the action the entry actually declares.
`EscalationAction` carries `assignedTo` ("The name of the user or queue the
item is assigned to"), `assignedToType` (`User` or `Queue`),
`assignedToTemplate` ("the template to use for the email that is automatically
sent to the new owner specified by the escalation rule"), `notifyCaseOwner`,
`notifyEmail`, `notifyTo` and `notifyToTemplate`
(`api_meta.txt` L59483–59517). A reassigning entry is provable from
`CaseHistory`; a notifying entry is only provable from a mailbox or an email
log. Read the entry before writing the expected result, and give a negative
case both oracles.

A related trap on the same object: the history row is only readable if the
field is tracked. `CaseHistory` is available "for **tracked fields** of the
object" (`object_reference.txt` L62818–62819), so `Case.OwnerId` and
`Case.Status` have to be in the tracking list before any of these cases can
fail safely — declare that in the run context, not in a step.
