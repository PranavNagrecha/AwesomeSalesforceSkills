# Deploy order — M1-S04 (hourly channel-health check: Schedulable + Queueable + tests)

Build `tier2-webhook` · step `M1-S04` · type `automation` · owner `apex-builder`
(run inline under `build-step-runner`) · API version **67.0** (assumption A11) ·
`build_mode: design-only` — **nothing here has been deployed, and neither agent deploys anything.**

---

## 0. Rebuild record — 2026-09-12

This step was built once, `failed` on its own P0, reset to `pending`, amended, and rebuilt.
The amendment is recorded in `plan.json` at `steps[M1-S04].amendments[0]`
(by "dry-run operator (Fable) + requester", fields `inputs` and `templates`).

**The P0 that caused it.** The first build took `include_logger: true` at its word and wired
every class through `templates/apex/ApplicationLogger.cls`. That class writes
`Application_Log__c` rows and reads `Logger_Setting__mdt.getInstance('Default')`, and
`skills/apex/error-handling-framework/references/code-examples.md` § 9 rows 1–3 make both
**compile** prerequisites of shipping it. Clarification **Q16** had already answered "We have
no existing Apex log object in the org", and M1-S01 ships none. `apex-builder` emits `.cls`
files only and M1-S01 was already `documented`, so the step could not fix it — the package
would not have compiled in the target org.

**What the requester decided, and what changed here:**

| Decision (now bound in `plan.json`) | What this rebuild changed |
|---|---|
| `include_logger: false`. No `ApplicationLogger`. The visible log for this feature **is** `Integration_Failure__c` (Q16–Q18); anything else is `System.debug` | `ApplicationLogger.cls` and its `-meta.xml` **deleted** from this step's artefacts; `templates[]` no longer lists it. Every log call is now `System.debug(LoggingLevel.…)` — `ERROR` on the three failure paths, `INFO`/`WARN` on the run outcome |
| Alert recipients = **active assignees of `Tier2_Webhook_Admin`**, resolved at run time from `PermissionSetAssignment` → `Assignee.Email`, inactive skipped. No Custom Label, no CMDT — nothing ships one | The empty `alertRecipients` constant and its `// UNKNOWN:` marker are **gone**. New `resolveRecipients()` runs the query; `sendAlert(result, recipients)` now takes the roster as a parameter so both the populated and the empty case are testable without setup DML |
| If the roster is empty: `System.debug` **and** an `Integration_Failure__c` row of Severity `Warning`, so the gap is visible | New `recordRecipientGap()`. New test `noActiveRecipientRecordsAWarningFailureRowAndSendsNothing` asserts the row and that nothing was mailed |
| The `WITH USER_MODE`-on-aggregate question stays **UNVERIFIED** — omit the clause and say so | Unchanged code; the `// reason:` comment in `evaluate()` now names the UNVERIFIED status explicitly, and § 4 item 2 below records it |

**One round-1 ambiguity closed itself.** The first build flagged a tension between
"`execute()` … does nothing else" (D11) and `include_logger: true`. With the logger gone
there is nothing left to weigh, so `execute()` is now a single `System.enqueueJob` statement
and nothing else — the literal reading of D11.

**Unchanged by the amendment:** the two Q24 thresholds and how "escalations exist" is read,
the CRON literal, the org-wide sender (A4), the `outputs[]` list, and `depends_on: [M1-S01]`.

**One stale sibling in `inputs{}`.** `amend-step` replaces `inputs` wholesale, and the older
`inputs.recipients` key still reads "The distribution list address is taken from the
deploy-order note rather than hardcoded per environment." The newer, dated
`inputs.alert_recipients` supersedes it and is what this rebuild implements. Worth a
prose-only amendment so a later reader is not left choosing between two bound inputs.

---

## 1. What this step ships

| # | File | Declared in `outputs[]`? | Role |
|---|---|---|---|
| 1 | `classes/Tier2ChannelHealthSchedulable.cls` (+ `-meta.xml`) | yes | the clock. `JOB_NAME`, the hourly CRON literal, and one `System.enqueueJob` |
| 2 | `classes/Tier2ChannelHealthQueueable.cls` (+ `-meta.xml`) | yes | the worker. Three `COUNT()` queries, the two Q24 thresholds, roster resolution, the alert email, the recipient-gap row |
| 3 | `classes/Tier2ChannelHealthTest.cls` (+ `-meta.xml`) | yes | 11 test methods |
| 4 | `classes/TestDataFactory.cls` (+ `-meta.xml`) | **no — undeclared** | byte-identical copy of `templates/apex/tests/TestDataFactory.cls`; shipped under the template-provenance rule (§ 2) |
| 5 | `deploy-order.md` (this file) | **no — undeclared** | named by `agents/apex-builder/AGENT.md` Output Contract item 2 as where template provenance is recorded |

No `package.xml`. `apex-builder`'s Output Contract names none, and
`standards/build-orchestration.md` § 5 **The Apex exception** puts these four `ApexClass`
members in the build-level manifest step **M1-S05**, which `depends_on` this step.

Items 4–5 remain undeclared artefacts: the step's `templates[]` still cites
`templates/apex/tests/TestDataFactory.cls` and its `outputs[]` still declares six paths,
none of them the copy. `amend-step` is the writer for that and is refused once a step has
left `pending`, so the correction belongs to whoever re-plans. `check-outputs` passes on the
six declared paths regardless.

---

## 2. Template-class provenance

`agents/apex-builder/AGENT.md` Step 6: every `templates/apex/**` class an emitted class or
test references must ship in this step's outputs as a verbatim copy plus its `-meta.xml`, or
already be declared by an earlier step. M1-S01 and M1-S02 declare none.

| Referenced | Shipped here | `diff` against the template |
|---|---|---|
| `TestDataFactory` — `Tier2ChannelHealthTest.seed()` calls `createCases(1, null, overrides)` | `classes/TestDataFactory.cls` + `-meta.xml` | empty — verified this run |
| `ApplicationLogger` | **no longer referenced** — removed by the 2026-09-12 amendment (§ 0) | n/a |

**M1-S03 may ship an identical `TestDataFactory.cls`, and that is not a collision at deploy.**
`scripts/mock_deploy.py:copy_artefacts` rebases every file onto
`<dest>/<path-relative-to-the-step-dir>`, so `artefacts/M1-S03/classes/TestDataFactory.cls`
and `artefacts/M1-S04/classes/TestDataFactory.cls` land on the same assembled path and the
later step overwrites the earlier. Both are byte-identical to the template, so the assembled
tree is correct either way. Two consequences remain for a human:

1. **M1-S05 must emit each `ApexClass` member once.** A `package.xml` listing
   `TestDataFactory` twice is a manifest defect, not a deploy-tree one.
2. **The structural fix is a plan change, not a file change.**
   `standards/build-orchestration.md` § 4, Apex row note: when more than one Apex step shares
   a template dependency, the plan runs a dedicated *Apex foundations* step first. This plan
   has two Apex steps and no such step. Recommend it at the M1 gate.

---

## 3. Deploy prerequisites — read before any deploy of this step

The two blocking prerequisites the first build reported (`Application_Log__c`,
`Logger_Setting__mdt`) are **gone**: the amendment removed the dependency rather than
satisfying it. What remains:

| # | Prerequisite | Status | Consequence if unmet |
|---|---|---|---|
| 1 | `Integration_Failure__c` (with `Status__c`, `Severity__c`, `Error_Message__c`, `Last_Attempted_At__c`) and `Case.Tier2_Notified_At__c` (**M1-S01**) | shipped by M1-S01 | the Queueable does not compile |
| 2 | `Tier2_Webhook_Admin` (**M1-S02**) deployed **and assigned** | M1-S02 ships the permission set; the assignment is an org action | with no active assignee the job writes a Severity `Warning` gap row every hour and alerts nobody |
| 3 | The scheduling user can **read `PermissionSetAssignment`** | **UNBOUND — see § 4 item 1** | `resolveRecipients()` throws or returns empty in user mode, and the alert silently degrades to the gap path |
| 4 | The org-wide email address `support-noreply@acme.example`, **verified**, with the scheduling user's profile in its allowed-profiles list | assumption **A4** — deploy prerequisite, not a build artefact | the job logs the unmet prerequisite at `LoggingLevel.ERROR` and sends nothing. It never falls back to the running user as the From address |
| 5 | `Tier2_Webhook_Admin` assigned to the user who will run `System.schedule` | decision **D14**, assumption **A13** | the counts return 0 or throw, and the check reports a healthy channel it cannot see |

---

## 4. UNVERIFIED and unbound — decisions written the narrowest legal way

1. **`PermissionSetAssignment` read access is not granted by anything this build ships, and
   the query shape is one the library flags.** Two separate points:
   - *Access.* `Tier2_Webhook_Admin` grants `Integration_Failure__c` object and field
     permissions and the `Case.Tier2_Notified_At__c` field permission. It grants nothing on
     `PermissionSetAssignment`. At API 67.0 the query in `resolveRecipients()` runs in user
     mode, so the scheduling user needs read on that object — typically a sysadmin-ish
     profile permission. No answer, decision or step input names it. **Confirm at the M1
     gate**; if the scheduling user cannot read it, every run degrades to the gap path.
   - *Shape.* `skills/apex/apex-user-and-permission-checks/references/llm-anti-patterns.md`
     Anti-Pattern 3 flags "SOQL on `PermissionSetAssignment` with a `PermissionSet.Name`
     string literal" and prescribes a Custom Permission instead. That anti-pattern is about
     **gating behaviour** on an assignment. This is **roster resolution** — "who holds this"
     is a question `FeatureManagement.checkPermission` cannot answer, only "can the running
     user" — and the requester bound the query explicitly on 2026-09-12. The name is a
     `@TestVisible` constant (`ROSTER_PERMISSION_SET`) so a rename is one edit. A security
     scan **will** flag this line; this note is the answer to it.
   - *A caveat nobody has ruled on.* If `Tier2_Webhook_Admin` is ever assigned through a
     Permission Set **Group** rather than directly, whether a row with
     `PermissionSet.Name = 'Tier2_Webhook_Admin'` still appears for that user is **not
     stated by any cited skill** and is not asserted here. Q19 assigns it directly to three
     named admins, so the query is right for the org as designed; re-check it if a PSG is
     introduced.
2. **`WITH USER_MODE` is not written on the three `COUNT()` queries — and that is now a
   plan-bound UNVERIFIED, not a judgment call.** Step input `aggregate_user_mode_note`
   (2026-09-12): whether the clause is legal on an aggregate `COUNT()` is stated in no cited
   skill; omit it and rely on API 67.0's default user mode. `agents/_shared/AGENT_CONTRACT.md`
   § *Apex security idiom by API version* (67.0+ row) is what makes the omission safe rather
   than lax. A `// reason:` comment in `evaluate()` records it in the code.
   `WITH SECURITY_ENFORCED` does not compile at 67.0 and appears nowhere.
3. **Case record visibility is not guaranteed.** `Tier2_Webhook_Admin` grants
   `viewAllRecords` on `Integration_Failure__c`, so the two failure counts are complete for
   any assignee. It deliberately carries **no** `objectPermissions` row for `Case`
   (assumption **A14**), so the third query returns only Cases the scheduling user can see
   under the org's Case sharing model. If that user cannot see other people's Cases,
   `successesLastDay` reads 0 and the job raises a **false** dead-channel alert. The answers
   name no Case OWD.
4. **One skill-checklist item is deliberately absent from `execute()`.**
   `skills/apex/apex-scheduled-jobs`' Review Checklist asks that `execute()` "refuses to
   dispatch when a prior run of the same worker is still in flight", and the canonical
   `NightlyRollupScheduler` implements it. The step input's `shape` says `execute()` "only
   enqueues a Queueable and does nothing else" (decision **D11**), and the guard costs a SOQL
   query. The plan won. Unlike round 1, **nothing else is in `execute()` either** — the
   logging line that created the round-1 tension went with `include_logger: false`.
5. **The recipient-gap row counts toward this job's own thresholds.** `recordRecipientGap()`
   writes an `Integration_Failure__c` row of Severity `Warning`, and the threshold queries
   count rows with **no Severity filter** — the step input defines rule 1 as
   "`Integration_Failure__c` rows created in the last hour exceed three", and adding a filter
   would be inventing a threshold nobody stated. Consequence: an org with no active assignee
   accumulates one self-inflicted row per hour, and after four hours rule 1 fires on the
   job's own output. It still cannot alert anyone — that is the condition — but the rows are
   in the list view and in the counts. If a reviewer wants the gap rows excluded, that is a
   threshold change to the plan, not a code change here.
6. **No duplicate-alert suppression.** While the channel is dark, this job emails the roster
   **every hour for up to 24 hours**. Q24 asked for the alert and said nothing about
   repetition, and no answer names an acknowledgement mechanism. At the alert's daily ceiling
   this is at most 24 sends × roster size against the org's 5,000 daily external emails,
   which counts **recipients**, not calls.

A seventh, smaller one: the seeded `Endpoint__c` value in the test omits its `https://`
scheme. The value is fixture text on a `Text` field and nothing asserts on it; the scheme was
dropped because a `//` inside an Apex string literal mis-lexes any static checker that blanks
line comments before string literals — `check_apex_scheduled_jobs.py:strip_comments` is one.
A comment in the test records it. This is a library observation, not a platform constraint.

---

## 5. Order against the rest of the build

| This step | Ordering | Why |
|---|---|---|
| **after M1-S01** | hard | Apex referencing an sObject or field not in the org fails to compile. `depends_on: [M1-S01]` |
| **after M1-S02** | soft at compile, **hard in practice** | not a compile dependency, but the permission set is the alert roster: deploy it and assign it before the first hourly run, or every run writes a gap row |
| **independent of M1-S03** | — | no shared symbol. Both may ship `TestDataFactory`; see § 2 |
| **before M1-S05** | hard | M1-S05 aggregates these `ApexClass` members into the build-level `package.xml` |

Members M1-S05 must carry for this step, **four** of them:
`Tier2ChannelHealthSchedulable`, `Tier2ChannelHealthQueueable`, `Tier2ChannelHealthTest`,
`TestDataFactory` — the last **once across M1-S03 and M1-S04**.

---

## 6. Post-deploy: scheduling the job — for a human to run, never for an agent

The active job is **data, not metadata**: `package.xml` deploys the class, and nothing in it
recreates a `CronTrigger`. Scheduling is a post-deploy step, and re-running a release requires
aborting the prior job first — a duplicate name throws
`System.AsyncException: The Apex job named "jobName" is already scheduled for execution`
(`skills/apex/apex-scheduled-jobs`, Core Concepts).

Run as **the user who should own the schedule** — scheduled Apex runs as the user who
scheduled it (assumption A13), and the CRON expression is read **in that user's time zone**,
then frozen onto `CronTrigger.TimeZoneSidKey`. On the hour that makes no difference to when
this job fires; it will if the literal ever changes. That user must also satisfy § 3 rows 3–5.

```apex
// Anonymous Apex. Run as the scheduling user named at the M1 gate.
// 1. Abort any live job of this name so the script is re-runnable.
for (CronTrigger ct : [
        SELECT Id FROM CronTrigger
        WHERE CronJobDetail.Name = :Tier2ChannelHealthSchedulable.JOB_NAME
          AND State IN ('WAITING','ACQUIRED','EXECUTING','PAUSED','PAUSED_BLOCKED','BLOCKED')]) {
    System.abortJob(ct.Id);
}

// 2. Pre-flight the ceiling: 100 scheduled Apex classes, 5 in Developer Edition.
System.debug([
    SELECT COUNT() FROM CronTrigger
    WHERE CronJobDetail.JobType = '7'
      AND State IN ('WAITING','ACQUIRED','EXECUTING','PAUSED','PAUSED_BLOCKED','BLOCKED')]);

// 3. Confirm the alert roster is not empty BEFORE the first run, or the first thing
//    this job does is write itself a Severity Warning row (section 4 item 5).
System.debug([
    SELECT COUNT() FROM PermissionSetAssignment
    WHERE PermissionSet.Name = 'Tier2_Webhook_Admin' AND Assignee.IsActive = true]);

// 4. Schedule.
System.schedule(
    Tier2ChannelHealthSchedulable.JOB_NAME,
    Tier2ChannelHealthSchedulable.CRON_EXPRESSION,
    new Tier2ChannelHealthSchedulable()
);
```

Verify afterwards on **both** job tables — a green `CronTrigger` over a job that did no work
is this domain's characteristic false-clean signal — and on the debug log, which is now the
only place a healthy run leaves a trace:

```soql
SELECT Id, CronJobDetail.Name, CronExpression, State, NextFireTime, PreviousFireTime,
       TimesTriggered, TimeZoneSidKey
FROM CronTrigger WHERE CronJobDetail.Name = 'Tier 2 Channel Health Check'

SELECT Id, Status, ExtendedStatus, CreatedDate
FROM AsyncApexJob
WHERE JobType = 'Queueable' AND ApexClass.Name = 'Tier2ChannelHealthQueueable'
ORDER BY CreatedDate DESC LIMIT 10
```

**A consequence of `include_logger: false` worth naming:** a healthy run now leaves **no
record at all** outside the debug log and the `AsyncApexJob` row, because the only durable
sink this feature has is `Integration_Failure__c` and a healthy run has no failure to write
there. Set a debug-log trace flag on the scheduling user for the first few runs.

Two more operational facts from the same skill: **a sandbox refresh does not copy scheduled
jobs**, so this script runs again after every refresh; and **an active schedule locks this
class and every class it references** — `Tier2ChannelHealthQueueable`, and through the test,
`TestDataFactory` — against deployment until the job is aborted. Put the abort step before
the deploy in every later release that touches any of them.

---

## 7. Governor-limit budget

| Class / path | SOQL | DML | Email | Notes |
|---|---|---|---|---|
| `Tier2ChannelHealthSchedulable.execute()` | 0 | 0 | 0 | one statement. Runs under **synchronous** limits (100 SOQL / 6 MB / 10,000 ms) — hence the dispatcher shape |
| `Tier2ChannelHealthQueueable.evaluate()` | **3**, all aggregate `COUNT()` | 0 | 0 | flat at any volume: `COUNT()` returns one value, so cost does not scale with row count. Asserted by `queryBudgetStaysFlatAtBulkVolume` at 202 rows |
| `resolveRecipients()` | 1 (`PermissionSetAssignment`) | 0 | 0 | one row per assignment; the roster is three admins per Q19 |
| `sendAlert()` — roster present | 1 (`OrgWideEmailAddress`) | 0 | 1 message | recipients count against the org's 5,000 external-email/day cap |
| `recordRecipientGap()` — roster empty | 0 | **1** | 0 | the only DML this feature performs |
| Worst case, one run | 5 | 1 | 1 | async limits are 200 SOQL / 150 DML; headroom is not the constraint here |

---

## 8. Test plan and what is NOT covered

Eleven methods in `Tier2ChannelHealthTest`. `System.schedule` and every async hand-off sit
inside `Test.startTest()` / `Test.stopTest()`. **No `PermissionSetAssignment` is inserted
anywhere**: it is a setup object, and setup DML mixed with this class's record DML in one
transaction throws `MIXED_DML_OPERATION` (`skills/apex/apex-system-runas` gotchas). The roster
is passed into `sendAlert` as a parameter instead, and `resolveRecipients()` is asserted
against whatever assignments the org actually holds.

| Method | Covers |
|---|---|
| `scheduleCreatesAWaitingCronTriggerAndDispatchesTheQueueable` | `CronExpression`, `State`, `TimesTriggered`, `NextFireTime`, `CronJobDetail.Name`/`JobType`, and one dispatched `AsyncApexJob` |
| `productionCronIsHourlyOnTheHour` | the production CRON literal is six fields, hourly, one day field marked no-specific-value |
| `belowBothThresholdsRaisesNoAlert` | the silent path on the seeded healthy state |
| `moreThanThreeFailuresInAnHourRaisesTheBurstAlert` | Q24 rule 1 at its first firing value (four) |
| `noSuccessInTwentyFourHoursWhileEscalationsOccurredRaisesTheSilentAlert` | Q24 rule 2 |
| `aQuietWindowWithNoEscalationsRaisesNoAlert` | the distinction rule 2 exists to make: nothing happened ≠ everything failed |
| `noActiveRecipientRecordsAWarningFailureRowAndSendsNothing` | the amendment's gap path: one Severity `Warning` row naming the permission set, `Status__c` New, zero email invocations |
| `alertPathDependsOnTheOrgWideAddressPrerequisite` | § 3 row 4's guard, asserted in both directions so the test is portable between an org that has the address and one that does not; also that a populated roster never takes the gap path |
| `rosterResolutionReturnsTheDistinctActiveAssigneeEmails` | the roster query's contract: active only, blanks dropped, de-duplicated |
| `subjectAndBodyNameTheRuleThatFired` | subject/body rendering, and that no literal merge token reaches the body |
| `queryBudgetStaysFlatAtBulkVolume` | three queries at 202 rows, measured with `Limits.getQueries()` |

**Deliberately uncovered, and why.** The eight lines of `sendAlert` that build and send the
`Messaging.SingleEmailMessage` are reachable only in an org where the org-wide address row
exists. `OrgWideEmailAddress` cannot be inserted by a test, so in a scratch org or a fresh
sandbox that branch is unreachable by construction, and
`alertPathDependsOnTheOrgWideAddressPrerequisite` asserts the suppression side instead.
`rosterResolutionReturnsTheDistinctActiveAssigneeEmails` executes the roster query in every
org but only exercises its filtering where assignments exist. Estimated coverage on
`Tier2ChannelHealthQueueable` is therefore **~80–85 % without the address and ~95 % with it**;
`Tier2ChannelHealthSchedulable` is fully covered. That is an estimate from reading the bodies,
**not a measured number** — no Apex test has been run, because this loop does not deploy.
Above the 75 % deployability floor either way; below the repo's 85 % bar in an org without the
address.

**No offline compile check ran, and there is no way to run one.** There is no offline Apex
compiler in the `sf` CLI: `sf apex run --file` *executes* a local file as an anonymous block
against a required `--target-org`, and nothing in the `apex` command group type-checks a
`.cls`. The compile gate is `sf project deploy start --dry-run`, which needs an org this build
does not have. What did run on the rebuilt artefacts, from the build directory, all exit 0:

```text
python3 skills/apex/apex-scheduled-jobs/scripts/check_apex_scheduled_jobs.py --manifest-dir artefacts/M1-S04
    → Scanned 4 .cls file(s): 0 ERROR, 0 WARN, 0 ADVISORY
python3 skills/apex/apex-queueable-patterns/scripts/check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S04
    → Scanned 4 Apex file(s), 1 implementing Queueable; 0 ERROR, 0 WARN, 0 ADVISORY
python3 skills/apex/error-handling-framework/scripts/check_error_handling_framework.py --manifest-dir artefacts/M1-S04
    → No issues found.
python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir artefacts/M1-S04
    → 4 files, 2 @IsTest artifacts, 0 findings, score 100   (not declared on this step; run as due diligence)
```

Plus, outside the checkers: every `*.cls` is brace-, paren- and bracket-balanced under a
string- and comment-aware lexer, all four `-meta.xml` files parse at `apiVersion 67.0`, and
`ApplicationLogger` appears nowhere in the package except in two block comments recording
that it was removed.

---

## 9. Validate-only command — for a human to run, never for an agent

```bash
python3 scripts/mock_deploy.py .sfskills/builds/tier2-webhook/plan.json \
  --org-alias <alias> --milestone M1
```

It hard-codes `checkOnly: true`. The round-1 blocker is gone — there is no longer a class in
this step referencing metadata the build does not ship — so this step should now compile
against an org that already holds M1-S01's objects. Run it after the milestone verifies and
before the G3 decision; its `summary.md` under `reports/mock-deploy/<ts>/` is the evidence
the gate rests on.
