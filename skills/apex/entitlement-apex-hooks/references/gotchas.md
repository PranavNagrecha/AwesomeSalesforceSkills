# Gotchas — Entitlement Apex Hooks

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line citations are into the plain-text extracts of the v62 *Object Reference for the
Salesforce Platform* (`object_reference.txt`) and the v62 *Apex Developer Guide*
(`apexdev`). Where a claim that is widely repeated in the community has no support in
either extract, it is marked `UNVERIFIED` beside the claim and framed as something to
check in your own org rather than something to rely on.

## Gotcha 1: `IsCompleted` Is Not an Updateable Field — `CompletionDate` Is the Control

**What happens:** Code that sets `caseMilestone.IsCompleted = true` and calls `update`
does not complete the milestone. `IsCompleted`'s documented properties on `CaseMilestone`
are `Defaulted on create, Filter` — the `Update` property is absent
(`object_reference.txt L63404–63410`). `CompletionDate`, by contrast, carries
`Filter, Nillable, Update` (`object_reference.txt L63376–63382`), and is one of only two
fields on the whole object that do; the other is `StartDate`
(`object_reference.txt L63434–63440`).

**When it occurs:** Any time the completion write is modelled on the field whose *name*
describes the outcome instead of the field the API lets you set. It is the first thing
most developers and most code generators reach for.

**How to avoid:** Write `caseMilestone.CompletionDate = System.now()` and `update` the
list. Assert on `CompletionDate` being non-null, not on `IsCompleted` being `true`.

UNVERIFIED (2026-09-12): whether a non-null `CompletionDate` is what *causes* `IsCompleted`
to read back as `true`, and whether a write to `IsCompleted` is silently discarded rather
than rejected. Neither extract states either. What is grounded is the asymmetry above —
one field is updateable and the other is not — which is sufficient reason to write
`CompletionDate`. Verify the read-back behaviour in your own org before writing an
assertion that depends on it.

---

## Gotcha 2: There Is No `SlaExitDate` on `CaseMilestone` — Referencing It Does Not Compile

**What happens:** `cm.SlaExitDate = ...` on a `CaseMilestone` variable, or `SlaExitDate` in
a `SELECT` list against `CaseMilestone`, fails to compile. The field is not in the
`CaseMilestone` field list at all (`object_reference.txt L63352–63510`). The field of that
name belongs to `WorkOrder`, where it is read-only — `Filter, Nillable, Sort`, no `Update`
— and is documented as "the time that the work order exits the entitlement process"
(`object_reference.txt L317989–317993`). On `Case`, the entitlement-clock fields are
`SlaStartDate` (`Create, Filter, Nillable, Sort, Update` —
`object_reference.txt L62659–62665`) and `StopStartDate` (read-only —
`object_reference.txt L62684–62690`).

**When it occurs:** When a requirement asks for dynamically adjusting milestone deadlines
by case priority or customer tier, and the search for a writable deadline field lands on a
field name that exists on a neighbouring object. Older guidance in this skill described
`SlaExitDate` as a system-managed `CaseMilestone` field whose writes are silently
discarded. That was wrong in a way that matters: the failure is a compile error, which is
the good kind.

**How to avoid:** The `CaseMilestone` deadline field is `TargetDate`, and its properties
are `Filter` only — no `Update`, not even `Nillable`
(`object_reference.txt L63441–63447`). Deadlines are not adjustable from Apex at all. Model
variable deadlines as separate entitlement processes with different milestone time
triggers, and apply the right process to the case.

---

## Gotcha 3: Entitlement Rules Run at Step 15, After Every Trigger

**What happens:** An `after update` trigger on `Case` that queries `CaseMilestone` returns
nothing on the save that first puts the case into an entitlement process. The Apex
Developer Guide's order of execution puts "Executes all after triggers" at **step 8** and
"Executes entitlement rules" at **step 15** (`apexdev L15448, L15471`). Your trigger runs
seven steps before the engine that creates the milestone rows.

**When it occurs:** Most visibly on case creation flows that set `EntitlementId` and a
non-New `Status` in the same save, and in any test that inserts a case with an entitlement
and immediately expects milestones to exist. It also bites when an integration upserts a
case with its final status in one call.

**How to avoid:** Hang completion off a *later* save than the one that applies the
entitlement. In a test, insert the case, then update its `Status` in a separate DML — that
second save is the one where milestone rows exist. If the business genuinely needs
same-save completion, the work has to move to an asynchronous path that runs after commit
(`apexdev L15479–15489` lists enqueued queueable jobs and future methods as post-commit).

---

## Gotcha 4: A Workflow Field Update Makes the Trigger Body Run Twice

**What happens:** The completion trigger fires, stamps `CompletionDate`, and then fires
again on the same user save, stamping a fresh timestamp over the first one. Step 11 of the
order of execution says that when workflow rules produce field updates, the platform
"Updates the record again" and then "Executes before update triggers and after update
triggers, regardless of the record operation (insert or update), one more time (and only
one more time)" (`apexdev L15451, L15458–15459`).

**When it occurs:** In any org with an active workflow field update on `Case` — which is
most orgs with an entitlement process, because milestone actions and escalation rules
commonly set case fields.

**How to avoid:** Put `CompletionDate = NULL` in the `WHERE` clause of the milestone query.
It is not only the open-milestone filter; it is the idempotency guard. On the second pass
the already-stamped milestone no longer matches, the query returns an empty list, and the
service returns before it reaches DML. A test that asserts a second pass attempts zero
milestones is the one that proves this (see `references/code-examples.md`). Rule `EAH006`
in the skill's checker flags a `CaseMilestone` query missing this clause.

---

## Gotcha 5: `CaseMilestone` Supports Only `update()` — No `create()`, No `delete()`

**What happens:** `insert` or `delete` against a `CaseMilestone` fails. The object's
documented supported calls are `describeLayout()`, `describeSObjects()`, `query()`,
`retrieve()`, `update()` (`object_reference.txt L63346–63347`). There is no `create()` and
no `delete()`. The platform owns the lifecycle of these rows entirely; Apex gets one verb.

**When it occurs:** Most often in test code, where the instinct is to construct the fixture
you need. It also appears in "reset the SLA" requirements, where the proposed design is to
delete the milestone rows and let the engine recreate them.

**How to avoid:** Accept that your automation's only lever is `update()` on
`CompletionDate` or `StartDate`. Anything that requires a different set of milestone rows
is an entitlement-process change in Setup, not an Apex change. Rule `EAH004` in the
checker flags `insert` / `delete` / `upsert` on a `CaseMilestone` variable.

---

## Gotcha 6: A Test Cannot Create the Entitlement Process It Needs

**What happens:** A test class builds an `Account`, an `Entitlement` and a `Case`, queries
`CaseMilestone`, gets an empty list, and passes — proving nothing. The chain breaks at
`SlaProcess`, whose supported calls are `describeSObjects()`, `query()`, `retrieve()`,
`search()`, `describeLayout()` (`object_reference.txt L270650–270651`). No `create()`. A
test can create the `Entitlement` (`object_reference.txt L110181–110182`) and the
`MilestoneType` (`object_reference.txt L183197–183198`), but not the process that joins
them, and not the `CaseMilestone` rows themselves (Gotcha 5).

**When it occurs:** In every fresh scratch org and in any sandbox where entitlement
management has not been configured. The test is green, the coverage number is fine, and
the milestone automation has never executed once.

**How to avoid:** Two decisions, both explicit:

1. Reach the org's real process with `@IsTest(SeeAllData=true)` (`apexdev L5802–5813`).
   Note the cost: a `SeeAllData=true` class cannot also be `@IsTest(IsParallel=true)` —
   the two annotations cannot be used together (`apexdev L5824`).
2. Fail loudly when the prerequisite is missing. Query for an active `SlaProcess` and
   assert on it at the top of the test, with a message that names what the org is missing.
   A test that returns early on a missing process is indistinguishable from a passing one.

Keep at least one test method that needs no entitlement configuration — typically the
early-return path where no case status changed. It is the only assertion that still runs
in a bare scratch org.

---

## Gotcha 7: `TimeRemainingInMins` Is Text, Not a Number

**What happens:** A filter or comparison like `TimeRemainingInMins < 30` does not mean what
it looks like. On `CaseMilestone`, `TimeRemainingInMins` is typed **`text`**, with
properties `Group, Nillable, Sort`, and its documented description is "Time remaining to
reach the milestone target. The format is minutes and seconds"
(`object_reference.txt L63492–63499`). `TimeRemainingInHrs` is also `text`
(`object_reference.txt L63485–63491`). The neighbouring `TargetResponseInMins` *is* an
`int` (`object_reference.txt L63460–63466`) and `TimeRemainingInDays` is a `double`
(`object_reference.txt L63478–63484`), which is exactly why the mistake is easy — the
family of field names is not type-consistent.

**When it occurs:** Building "milestones due within N minutes" reports, dashboards, or
escalation queries, where the field whose name matches the requirement is the one that
cannot express it.

**How to avoid:** Compare `TargetDate` against `System.now()` in Apex, or use the numeric
`TimeRemainingInDays`. Rule `EAH007` in the checker flags numeric comparisons against the
two text fields.

---

## Gotcha 8: Stopping the SLA Clock Is a `Case` Field, Not a Milestone Field

**What happens:** Code that looks for a "pause" or "stop" control on `CaseMilestone` finds
nothing. The switch lives on `Case`: `IsStopped` is typed `boolean` with properties
`Create, Defaulted on create, Filter, Group, Sort, Update` and is documented as "Indicates
whether an entitlement process on a case is stopped (true) or not (false)"
(`object_reference.txt L62486–62503`). It is one of the few entitlement-adjacent fields
Apex may actually write. Its companion `Case.StopStartDate` — "the date and time an
entitlement process was stopped on the case" — is read-only: `Filter, Nillable, Sort`, no
`Update` (`object_reference.txt L62684–62690`).

**When it occurs:** Implementing "pause the clock while we are waiting on the customer".
The requirement is about milestones, so the search starts on the milestone object and ends
in the wrong place.

**How to avoid:** Write `Case.IsStopped` from a `Case` trigger or Flow, and let the engine
handle the milestone side. Note the feature gate: the parallel `IsStopped` field on
`WorkOrder` is documented as "available only if *Enable stopped time and actual elapsed
time* is selected on the Entitlement Settings page" (`object_reference.txt L317622–317631`),
so confirm that setting before designing around stop/resume.

NOT FOUND (2026-09-12): `StoppedTimeRemainingInMins` does not appear anywhere in the v62
Object Reference extract, on `CaseMilestone` or on any other object. Do not write code
against it on the strength of a community post; describe the field in your own org first.

UNVERIFIED (2026-09-12): what `TimeRemainingInMins` reads back as while
`Case.IsStopped = true`. The extract documents the field and documents the flag, but says
nothing about the interaction. Observe it in a sandbox before building a report on it.

---

## Gotcha 9: No Documented DML Event for the `IsViolated` Transition

**What happens:** An `after update` trigger on `CaseMilestone` written to catch
`IsViolated` going from `false` to `true` does not fire at the moment of violation. The
trigger will fire for other DML on the object — `update()` is supported
(`object_reference.txt L63346–63347`), so a `CompletionDate` write does fire it — but not
for the violation state itself.

**When it occurs:** Building real-time violation alerting with the reactive trigger pattern
that is correct nearly everywhere else on the platform.

**How to avoid:** Use the entitlement process's native milestone violation actions for
notifications and field updates, and Scheduled Apex polling
`WHERE IsViolated = true AND CompletionDate = NULL` when the response needs real logic.
Either way, add an idempotency guard, because a poll that runs every 30 minutes will see
the same violated milestone every 30 minutes until it is resolved.

UNVERIFIED (2026-09-12): that the platform sets `IsViolated` through a background
calculation rather than a DML operation. The Object Reference establishes only that
`IsViolated` is not updateable — properties `Defaulted on create, Filter`, no `Update`
(`object_reference.txt L63411–63419`) — and the Apex Developer Guide extract contains no
statement about trigger behaviour on this field. The design advice above is the safe one
either way: a scheduled poll works whether or not a trigger would also fire, and a trigger
that never fires produces exactly the silent failure this skill exists to prevent. Verify
in a sandbox before relying on a trigger.

---

## Gotcha 10: Partial-Success DML Hides Its Own Failures

**What happens:** `Database.update(milestones, false)` completes without throwing even when
individual milestones failed, and the failures disappear unless the returned results array
is iterated. The Apex Developer Guide is explicit: DML statements throw and roll back the
whole operation, while `Database` class methods "can either do so or allow partial success
… In the latter case of partial processing, `Database` class methods don't throw
exceptions. Instead, they return a list of errors for any errors that occurred on failed
records" (`apexdev L8429–8433`), and "you must iterate through the returned results to
identify which records succeeded or failed" (`apexdev L9061–9063`). The `optAllOrNone`
default is `false` — partial success (`apexdev L8665–8667`).

**When it occurs:** Whenever partial success is chosen (correctly) so that one locked or
inaccessible milestone does not roll back the case save that triggered it — and then the
`Database.SaveResult` loop is dropped as boilerplate.

**How to avoid:** Iterate the results, and send every `Database.Error` somewhere queryable
in production — `templates/apex/ApplicationLogger.cls` is the canonical destination in this
repo. One further consequence to design for: "If a DML call is made with partial success
allowed, triggers are fired during the first attempt and are fired again during subsequent
attempts" (`apexdev L15498–15500`), which compounds Gotcha 4.

---

## Gotcha 11: The Milestone Type Name Is a String Match Against Setup

**What happens:** A query filtered on `MilestoneType.Name = 'First Response'` returns zero
rows after an admin renames the milestone in Setup, or when the code's spelling never
matched. Zero rows is not an exception, so the automation silently stops completing
milestones and nothing in the org says so.

**When it occurs:** On every Setup rename, and on the first deploy into an org whose
milestone names differ from the org the code was written in.

**How to avoid:** Keep the name in one named constant (or, better, Custom Metadata) rather
than as a literal at each call site, so a rename is a one-line change. Where milestone
automation is business-critical, resolve the name to a `MilestoneType` Id once and assert
that the resolution found something rather than letting an empty result pass as "nothing to
do".

UNVERIFIED (2026-09-12): that `MilestoneType.Name` comparison in SOQL is case-*sensitive*.
Earlier revisions of this skill asserted it. Neither extract supports that claim, and SOQL
string comparison on standard text fields is generally case-insensitive, so the claim is
more likely wrong than right. Treat exact-casing discipline as good hygiene — it costs
nothing — but do not build a diagnosis on the assumption that a casing mismatch is what
broke the query. Check the name against Setup directly.

---

## Gotcha 12: A Test Class Ships Without the Template It Calls — `Variable does not exist: TestDataFactory`

**What happens:** `CaseMilestoneServiceTest.cls` (or any class built from this skill's
examples) deploys and fails to compile with `Variable does not exist: TestDataFactory`.
The class calls `TestDataFactory.createAccounts(...)` and `TestDataFactory.createCases(...)`,
but `references/code-examples.md` names `templates/apex/tests/TestDataFactory.cls` "by
relative path" rather than shipping it as one of the bundle's own four files, and
`templates/README.md` is explicit that templates are copied into the consuming project,
not deployed straight out of the shared `templates/` tree. A build step, or a manual
extraction, that ships the test class without also shipping a copy of `TestDataFactory.cls`
produces exactly this compile error — and the same failure mode applies to any other
canonical template class (`TriggerHandler`, `TriggerControl`, `ApplicationLogger`, …) a
generated class references without shipping.

**When it occurs:** Any time this bundle's `CaseMilestoneServiceTest.cls` is deployed
without `TestDataFactory.cls` present in the same deployable set — most visibly when a
multi-step build plan ships the Apex automation step's test class in one step and assumes
a template dependency "already exists" without any step that actually shipped it (F-37,
case-onboarding M4-S05, org dry run 2026-09-12).

**How to avoid:** Copy `templates/apex/tests/TestDataFactory.cls` and its `-meta.xml`
alongside `CaseMilestoneServiceTest.cls` in every deploy — see **Deploy prerequisites** and
the **Deploy order** table in `references/code-examples.md`. Run this skill's checker
(`EAH009`) against the full deployable tree before deploying; it WARNs when a shipped
`.cls` references `TestDataFactory` or another canonical template class with no matching
`.cls` under the same `--manifest-dir`. In a multi-step build plan, ship shared template
classes from one dedicated foundations step ahead of every Apex step that needs them
(`agents/build-planner/AGENT.md` Step 6) rather than assuming a later or earlier step
covered it.

---

## Gotcha 13: A `SeeAllData` Test Must Select Its Entitlement Process By Name, Not `LIMIT 1`

**What happens:** `requireActiveProcess()` (Gotcha 6) needs `@IsTest(SeeAllData=true)`
because `SlaProcess` has no `create()` call — the annotation "grant[s] test methods access
to all data in the organization" (`apexdev L5802–5813`). A version of that method filtered
only `WHERE IsActive = true LIMIT 1`, with no filter naming which process. In a scratch org
with nothing else configured, that query can only return the one process the test deployed,
so the gap is invisible. In a target org that already runs its own entitlement process for
the same case type, `LIMIT 1` with no `ORDER BY` returns whichever active row the platform
hands back first — the org's pre-existing process, not the deployed one — and if that
process carries no matching milestone, the test proceeds against the wrong process
entirely. It does not fail loudly: it queries a real `CaseMilestone` search space, finds no
open "First Response" milestone because the row it entered has none, and asserts "no open
milestone was generated" — a true statement about the wrong process, read as a false
statement about the deployed one.

**When it occurs:** Any `@IsTest(SeeAllData=true)` entitlement test deployed into an org
that has ever configured entitlement management on its own, independent of the build under
test — which is most orgs holding an active Service Cloud implementation. It is invisible
in every earlier dry run against a bare scratch org and surfaces for the first time against
a real target org.

**How to avoid:** Select the deployed process by name, not by recency or `LIMIT 1`, assert
the result count is exactly one (catching both "missing" and "more than one match"), and
name the process in the failure message so a future run that regresses says which
prerequisite is missing rather than just "assertion failed":

```apex
private static final List<String> STANDARD_PROCESS_NAMES = new List<String>{
    'First_Response_Standard', 'First Response Standard'
};

private static SlaProcess requireActiveProcess() {
    List<SlaProcess> processes = [
        SELECT Id, Name
        FROM SlaProcess
        WHERE IsActive = true
          AND Name IN :STANDARD_PROCESS_NAMES
    ];
    Assert.areEqual(
        1,
        processes.size(),
        'Expected exactly one active SlaProcess named "First_Response_Standard" (or its ' +
        'label form "First Response Standard") in this org — found ' + processes.size() +
        '. This test cannot create that row (SlaProcess has no create()), so the deployed ' +
        'process must exist, be active, and be the only match before this test proves ' +
        'anything.'
    );
    return processes[0];
}
```

UNVERIFIED (2026-09-12): whether the `SlaProcess.Name` field preserves the metadata
`<name>` attribute literally (e.g. `First_Response_Standard`) or whether the platform
stores or displays a space-separated label form (`First Response Standard`) instead.
Neither extract states it, and neither does this skill nor `admin/entitlements-and-milestones`.
Query both candidate spellings with `IN` and assert the count is exactly one, rather than
guessing which one your org uses — one match either way settles it without the test needing
to know in advance.

Checker rule `EAH010` flags a `SlaProcess` query in a `@IsTest`/`@TestSetup` file with no
`Name` filter.

**Where this came from:** `case-onboarding` build F-61 —
`.sfskills/builds/case-onboarding/reports/MOCK-DEPLOY-M5.md` runs 6–7;
`.sfskills/builds/case-onboarding/artefacts/M4-S05/deploy-order.md` § 10. The target org's
own pre-existing `Standard Case` process, carrying no `First Response` milestone, was
returned by the unfiltered query instead of the deployed `First_Response_Standard`.

---

## Gotcha 14: The Milestone Stamp Is a System-Integrity Write — Bound It in `AccessLevel.SYSTEM_MODE` and Assert No Swallowed `SaveResult` Errors

**What happens:** `CaseMilestoneService`'s completion query and DML ran without an explicit
access-level argument, so both inherited the API 67.0 default: user mode, as whichever
persona's save triggered the `after update` trigger. No permission set in the build granted
that persona any access — Create, Read, or Edit — to `CaseMilestone` at all, because nothing
in the requirements ever asked the case-working agent to control SLA infrastructure
directly. The query still found the open milestone (user-mode visibility on `CaseMilestone`
was not the gap), but `Database.update(openMilestones, false)` — partial-success DML — ran
as that same ungranted persona, and the platform refused the write. Partial success does not
throw; the refusal landed in `saveResults[i].getErrors()` exactly as documented (Gotcha 10),
and the test asserted only `result.attempted > 0`, never `result.failures`. The visible
symptom two calls downstream was a wrong count — a milestone that should have shown
`CompletionDate` still null, and a completed milestone that should have been skipped instead
showing as re-attempted — not the DML refusal itself, which never surfaced anywhere a
reviewer would see it.

**When it occurs:** Any milestone-completion service invoked from a trigger, where the
running user is the business persona whose save fired the trigger (not an integration user,
not the deploying admin) and where no permission set in the build grants that persona any
`CaseMilestone` access — the common shape, since `CaseMilestone` is a platform-owned object
(Gotcha 5) that no persona's job ordinarily calls for editing directly.

**How to avoid:** Treat the milestone stamp as a system-integrity write — the entitlement
engine's own completion signal, invoked from a trigger the moment a case leaves its opening
status, not a field the running persona deliberately edits — and bound it in an explicit
`AccessLevel.SYSTEM_MODE`, with a `// reason:` comment naming why: "In system mode, the
object and field-level permissions of the current user are ignored, and the record sharing
rules are controlled by the class sharing keywords" (`apexdev L11436–L11439`);
`AccessLevel.SYSTEM_MODE` is documented as an explicit argument to `Database` DML methods
including `update`, alongside `insert`, `upsert`, `merge`, `delete`, `undelete`, and
`convertLead` (`apexdev L11995–L12006`):

```apex
List<Database.SaveResult> saveResults = Database.update(
    openMilestones, false, AccessLevel.SYSTEM_MODE
);
```

The alternative — granting the persona Edit on `CaseMilestone` so the default user-mode
write succeeds — widens a persona to access nobody asked it to have, the same anti-pattern
`apex/test-class-standards` Gotcha 15 names for seeding test fixtures: don't choose between
"grant access the job doesn't need" and "can't do the write at all". Narrow to system mode
instead. See the access-mode decision table in `apex/apex-security-patterns` SKILL.md for
the general "integration/platform-utility code on a 67.0+ class must see all rows and
fields" shape this fits.

Whichever access level is used, assert on the `Database.SaveResult` array, not only on the
attempt count — a swallowed failure changes downstream counts in a way that looks like a
different bug:

```apex
Assert.areEqual(0, result.failures.size(), String.join(result.failures, ' | '));
```

UNVERIFIED (2026-09-12): whether `AccessLevel.USER_MODE` on a `Database.update` call is
what specifically makes `SaveResult.getErrors()` populate with the FLS refusal (the extract
documents the tip only for `AccessLevel.USER_MODE`, not for the plain no-argument default
this build started from — `apexdev L12006`). What is grounded is the asymmetry itself: a
refusal under partial-success DML never throws regardless of access level, so a test that
does not iterate `SaveResult` cannot tell a refused write from a silent no-op either way.

**Where this came from:** `case-onboarding` build F-62 —
`.sfskills/builds/case-onboarding/reports/MOCK-DEPLOY-M5.md` runs 7–8;
`.sfskills/builds/case-onboarding/artefacts/M4-S05/deploy-order.md` § 11. The first repair
in this build's history to change shipped code rather than only the test.

**See also:** Gotcha 10 (iterate `Database.SaveResult`, don't just trust partial-success
DML not to throw) is the general rule; this gotcha is the specific case where the write
itself needs an explicit access-level boundary before the `SaveResult` loop has anything
correct to report on. `apex/test-class-standards` Gotcha 15 draws the same
seed-in-system-mode-act-as-persona line for test fixtures; this gotcha draws it for shipped
service code.

---

## Checker Ignores Comments And String Literals

**What happens:** The skill checker flags a keyword that appears only in a comment or a string literal (for example a note that `WITH SECURITY_ENFORCED` is not used, or an assertion message that mentions `EventBus.publish`).

**When it occurs:** Before the checker blanked `//` line comments, `/* … */` block comments, and `'…'` string literals to spaces (same length, newlines preserved) for code-pattern rules.

**How to avoid:** Trust the checker on executable code only. Mentions inside comments and string literals are ignored for pattern matches; rules that intentionally read comments (for example a `// reason:` search) still read the original text.
