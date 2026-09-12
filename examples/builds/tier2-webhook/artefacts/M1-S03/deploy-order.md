# Deploy order — M1-S03 (escalation trigger, publish-and-enqueue service, webhook Queueable, Finalizer retry, resend path, tests)

Build `tier2-webhook` · step `M1-S03` · type `automation` · owner `apex-builder`
(run inline under `build-step-runner`) · API version **67.0** (assumption A11) ·
`build_mode: design-only` — **nothing here has been deployed, and neither agent deploys anything.**

This is the step's **fourth** run. Run 1 refused (`REFUSAL_INPUT_AMBIGUOUS`, envelope
`envelopes/M1-S03/2026-09-12T10-57-25Z.json`); the requester and the dry-run operator
answered with **remedy B** (`amendments[1]`, `2026-09-12T11:03:46Z`), and run 2 built to
that amended plan. Run 2 passed every checker and **failed the org**. § 0 is that record.
Run 3 fixed two org-found compile faults and **passed the org's compile** (dry-run 4/5).
§ 0b is run 4: the operator's `--test-level RunSpecifiedTests` dry-run (run 6 of the
milestone-level record, `reports/MOCK-DEPLOY-M1.md`) compiled clean and then failed
every test method at execution — a permissions gap in the tests themselves, not in the
shipped code — and the operator moved this step `documented` → `running` to repair it.
§ 4 is what the remedy-B amendment cost and what it bought.

---

## 0b. Repair record — run 4, after S2-F-11 (the tests ran as the wrong user)

**Trigger:** `reports/MOCK-DEPLOY-M1.md` run 6 — MANIFEST mode, milestone M1,
`--test-level RunSpecifiedTests` (`reports/mock-deploy/2026-09-12T13-08-43Z/`). Components
39/39 `ok` — the metadata and the Apex still compile exactly as runs 3–5 said. Tests:
level RunSpecifiedTests, **passed 0 · failed 28**, coverage 34.9%. Every method in
`Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest` and `IntegrationFailureResendTest`
failed with one of two errors, verbatim:

```
System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'.
System.DmlException: Operation failed due to fields being inaccessible on Sobject
Integration_Failure__c / Case, check errors on Exception or Result!
```

**S2-F-11 (HIGH).** None of the three test classes carried a `System.runAs` block for a
permissioned user. `Tier2WebhookQueueable` and `CaseTriggerHandler` enforce the running
user's FLS with `WITH USER_MODE` — correct at API 67.0 — but the tests ran as the
deploying user, whose profile is not part of this deployment and therefore holds no FLS
on `Case.Tier2_Notified_At__c` or `Integration_Failure__c`, both shipped by M1-S01 in the
same request. `templates/apex/tests/TestUserFactory.cls` exists in this repo and was not
used. See `skills/apex/test-class-standards/references/gotchas.md` Gotcha 13 and
`references/examples.md` Example 5 — Example 5 is this exact class
(`Tier2EscalationServiceTest` / `Tier2_Webhook_Admin` / `Tier2_Notified_At__c`) and is the
shape this repair follows verbatim.

**Fixed — running-user context and setup only; every existing test method and assertion
is unchanged:**

1. **`classes/TestUserFactory.cls` (+ `-meta.xml`) added**, a verbatim copy of
   `templates/apex/tests/TestUserFactory.cls` — `diff` empty, verified this run. This is
   now a third undeclared-but-shipped template class alongside `TestDataFactory` and
   `MockHttpResponseGenerator` (§ 1, § 2).
2. Each of `Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest` and
   `IntegrationFailureResendTest` gained `PERM_SET = 'Tier2_Webhook_Admin'` (the
   permission set M1-S02 ships) and `PROFILE = 'Standard User'`, and its `@TestSetup`
   now builds a permissioned user via `TestUserFactory.createUser(PROFILE, new
   List<String>{ PERM_SET })` **inside the same mixed-DML fence** that already wrapped
   the `Group`/`QueueSObject` setup-object DML — `System.runAs(new
   User(Id = UserInfo.getUserId()))` — so `User` and `PermissionSetAssignment` (both
   setup objects) never mix with `Case` DML in one transaction
   (`skills/apex/mixed-dml-and-setup-objects`). That fence is unchanged in what it does;
   it now also carries the user-provisioning call.
3. The business-data insert that already ran after the fence (`insert
   TestDataFactory.createCases(...)`, plus the two `Integration_Failure__c` rows in
   `IntegrationFailureResendTest`) now runs inside `System.runAs(<the new agent>)`
   instead of the deploying user's context, so a create-FLS gap in `Tier2_Webhook_Admin`
   fails in setup rather than surfacing later as an empty query result.
4. Each class gained a `private static User agent()` helper —
   `[SELECT Id FROM User WHERE Alias LIKE 'tu%' ORDER BY CreatedDate DESC LIMIT 1]` —
   because `@TestSetup` state reaches a test method only through the database.
5. **Every `@IsTest` method's existing body is now wrapped in
   `System.runAs(agent()) { ... }`**, unchanged inside the braces: same statements, same
   assertions, same messages. The two pure-static-method tests
   (`statusCodesAreClassifiedTheWayTheRetryContractSays`,
   `theIdempotencyKeyIsStableForTheSameCaseAndEscalationTime`) are wrapped too, for
   uniformity and because the second one queries `Case.Id`; neither needed the wrap
   strictly, and the wrap is harmless.

**Checked this run — `skills/apex/test-class-standards/scripts/check_test_class_standards.py
--manifest-dir artefacts/M1-S03`:**

```
Scanned 11 Apex class file(s); audited 6 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
```

`user-mode-test-without-runas` — the rule this repair exists to close — fires zero times.
The three previously-declared checkers (`check_apex_queueable_patterns.py`,
`check_callouts_and_http_integrations.py --fail-on HIGH`,
`check_platform_events_apex.py`) were re-run unchanged and still exit 0 with zero
findings, because no non-test class changed. `check-outputs` is `ok` on all 20 declared
paths — none of them changed path, only content on three of them.

**Not part of this repair, and not touched:** `CaseTriggerHandler.cls`,
`IntegrationFailureTriggerHandler.cls`, `Tier2EscalationService.cls`,
`Tier2WebhookQueueable.cls`, `Tier2WebhookFinalizer.cls`, both triggers, and every
`-meta.xml` other than the new `TestUserFactory.cls-meta.xml`. The task scoping this
repair is explicit that the step's non-test classes are correct and must not change, and
nothing about S2-F-11 implicates them — the code's user-mode enforcement is what the
finding calls "correct."

**No `package.xml` change made, and this is a known gap against the literal repair
request.** The request asked for `TestUserFactory` to be added to "the step's
`package.xml`." Per `standards/build-orchestration.md` § 5 **The Apex exception**,
`apex-builder`'s Output Contract names no manifest, and this step (an `apex-builder`-owned
`automation` step) has never declared one — its always-on `manifest` acceptance test
already records skipped-not-applicable and names **M1-S05**, which aggregates this step's
`ApexClass`/`ApexTrigger` members into the build-level manifest. Declaring a local
`package.xml` here would (a) contradict that recorded exception and (b) violate § 4
condition 2 (an agent may not declare an output its own Output Contract does not
produce). `TestUserFactory` needs a new `ApexClass` member at **M1-S05**, exactly as
`TestDataFactory` and `MockHttpResponseGenerator` already do (§ 2) — that member list is
this step's to hand off, not this step's to write. Flagged as a follow-up rather than
silently worked around.

**Consequence for the milestone.** `milestone:M1` was approved at 12:57Z on evidence that
predates this finding (dry runs 1–5 all carried `runTestsEnabled: false` — S2-F-06). This
step returns to `built` once its own checkers and `check-outputs` pass; `step-tester`,
`build-doc-keeper` and a fresh `/verify-milestone` are the human's next commands, and the
M1 acceptance needs re-signing against a dry run that actually executes tests
(`--test-level RunSpecifiedTests` or `RunLocalTests`).

---

## 0c. Repair record — run 5, after S2-F-12 (the factory volunteered a field no test needed)

**Trigger:** `reports/MOCK-DEPLOY-M1.md` run 7 — SOURCE mode, M1-S01 … M1-S04, after the § 0b
(S2-F-11) fix landed, `--test-level RunSpecifiedTests` (API 67.0). 30 of 30 test methods
failed, every one at the same `@TestSetup` seed insert, now correctly running inside
`System.runAs(agent)` as the `Tier2_Webhook_Admin` permissioned user:

```
System.DmlException: Operation failed due to fields being inaccessible on Sobject
Case, check errors on Exception or Result! ... fieldNames: AccountId
```

**S2-F-12 (HIGH, library).** `TestDataFactory.createCases(count, accountId, overrides)` — a
verbatim copy of `templates/apex/tests/TestDataFactory.cls` — assigned `AccountId =
accountId` unconditionally in the constructor. All three of this step's test classes call it
as `TestDataFactory.createCases(<n>, null, null)` (`IntegrationFailureResendTest` line 57,
`Tier2EscalationServiceTest` line 61, `Tier2WebhookQueueableTest` line 64) — none of them has
an Account to link, and none asserts on `Case.AccountId`. Assigning a variable into a field
in a constructor's field list marks that field populated regardless of the value, so the
`null` argument still rode along on the DML request. At API 67.0+ Apex runs in user context
by default, so the plain `insert` inside `System.runAs` checked FLS on every populated field
including the unwanted one, and the Standard User running as `Tier2_Webhook_Admin` has no
create access on `Case.AccountId` — a field this deployment's permission set was never asked
to grant, because no test needed it. See `skills/apex/test-class-standards/references/gotchas.md`
Gotcha 14, which names this exact org message and this exact build as its source.

**Fixed — the shared factory only, nothing in this step's own files:**

`classes/TestDataFactory.cls` was replaced with a verbatim copy of the corrected
`templates/apex/tests/TestDataFactory.cls` (`diff` empty, verified this run). The template's
`createContacts`, `createOpportunities` and `createCases` now construct the record without
the lookup field and set it only when the caller-supplied Id is non-null
(`if (accountId != null) { record.AccountId = accountId; }`), instead of assigning a
possibly-null parameter directly inside the constructor's field list.

**Every `createCases` / `createContacts` call site in this step's three test classes was
checked and none required a change.** All three already pass `null` for `accountId`
(`IntegrationFailureResendTest.cls:57`, `Tier2EscalationServiceTest.cls:61`,
`Tier2WebhookQueueableTest.cls:64`), and a repo-wide grep of this step's test classes for
`AccountId` returns zero hits outside the factory itself — no test method reads or asserts
on `Case.AccountId`. The corrected factory now leaves the field genuinely unset for these
calls, which is the intent Gotcha 14 describes, not a regression: nothing here seeded a
lookup that must now be passed explicitly.

**Checked this run:**

```
$ python3 skills/apex/apex-queueable-patterns/scripts/check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03
Scanned 13 Apex file(s), 1 implementing Queueable; 0 ERROR, 0 WARN, 0 ADVISORY.

$ python3 skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py --manifest-dir artefacts/M1-S03 --fail-on HIGH
Scanned 13 Apex file(s); 0 callout finding(s).

$ python3 skills/apex/platform-events-apex/scripts/check_platform_events_apex.py --manifest-dir artefacts/M1-S03
Scanned 13 Apex file(s) and 0 object file(s); 0 platform-event finding(s).

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir artefacts/M1-S03/classes
Scanned 11 Apex class file(s); audited 6 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
```

All four exit 0 with zero findings. `check-outputs` is `ok` on all 20 declared paths; every
`-meta.xml` under this step's artefacts still parses. **No non-test class changed** — the
three declared checkers were re-run unchanged for that reason alone, exactly as in § 0b.

**Not part of this repair, and not touched:** every production class, both triggers, all
three test classes' bodies (only the shared factory they call changed), `TestUserFactory.cls`,
`MockHttpResponseGenerator.cls`, and every `-meta.xml`. `TestDataFactory.cls-meta.xml` is
unchanged too — the fix is entirely inside the `.cls` body; `apiVersion` stays 67.0.

**No `package.xml` change made, for the same reason as § 0b.** `TestDataFactory` was already
an undeclared-but-shipped member before this run (§ 1 row 11, § 2); this repair changes its
content, not its membership, so M1-S05's manifest is unaffected by this run specifically —
though it remains stale against § 0b's `TestUserFactory` addition, unchanged since that
finding.

**Consequence for the milestone.** Unchanged from § 0b: `milestone:M1` was approved on
evidence that predates both S2-F-06 and S2-F-11, and now also predates S2-F-12. This step
returns to `built` once `check-outputs` passes (it does); `step-tester`, `build-doc-keeper`
and a fresh `/verify-milestone` are the human's next commands, against a dry run that
actually executes tests and does not fail on this factory's `AccountId` field.

---

## 0d. Repair record — run 6, after S2-F-14 (`Tier2WebhookFinalizer` under the 75% floor)

**Trigger:** `reports/MOCK-DEPLOY-M1.md` run 9 — MANIFEST mode, whole build, after the
S2-F-13 repair (Create/Read on `Tier2_Escalation__e` in `Tier2_Webhook_Admin`),
`--test-level RunSpecifiedTests` (API 67.0). Components 40/40 ok, **30 of 30 tests passed**,
S2-F-13 closed by the org — but the run still reports **Failed**, on coverage alone:
**70.8%**, under the platform's 75% floor. The gap is named exactly:
`Tier2WebhookFinalizer` 63 of 76 lines uncovered in the run 8 predecessor. **S2-F-14
(MEDIUM, test coverage).** This is a test-only addition; no shipped class changes.

**Why the gap exists.** Every existing test in `Tier2WebhookQueueableTest` drives
`Tier2WebhookQueueable` to a result (success, permanent failure, or a transient failure at
the attempt ceiling) that lets `execute()` return normally. `System.attachFinalizer(...)` is
unconditional, so `Tier2WebhookFinalizer.execute(ctx)` does run in every one of those
tests — but `ctx.getResult()` is `SUCCESS` in all of them, because none ever makes the
Queueable throw. The only branch of `Tier2WebhookQueueable.execute()` that throws is
`anyTransient && attempt < MAX_ATTEMPTS` (a transient status below the ceiling), which is
exactly the branch § 5 item 3 already named "deliberately uncovered" — for a documented
reason: **"an unhandled exception in a job run by `Test.stopTest()` fails the test
method."** That finding is this run's starting point, not a surprise.

**Fixed — one new file, nothing shipped touched:**

`classes/Tier2WebhookFinalizerTest.cls` (+ `-meta.xml`, API 67.0) is added. It is a new
file rather than more methods on `Tier2WebhookQueueableTest`, for two reasons: (1)
`agents/apex-builder/AGENT.md`'s own Output Contract and Escalation Rules never let this
agent modify an existing shipped file in place (`REFUSAL_OUT_OF_SCOPE`) — every other
class this step ships already follows a one-production-class-to-one-test-class layout
(`Tier2EscalationService` / `Tier2EscalationServiceTest`, the two triggers /
`IntegrationFailureResendTest`), and `Tier2WebhookQueueable` already has its own; (2)
`Tier2WebhookFinalizer` is its own unit with its own contract, and testing it directly
rather than only through the Queueable is what closes the actual gap — see below.

**How the branches are reached without letting the Queueable throw.**
`skills/apex/apex-transaction-finalizers/references/code-examples.md` documents the
identical problem for its own worked Finalizer and answers it by extracting a
`@TestVisible` `handle(...)` decision seam that a test calls directly, bypassing
`System.attachFinalizer`/`Test.stopTest()` entirely. `Tier2WebhookFinalizer.cls` ships
with no such seam, and this repair is scoped to leave shipped classes unchanged, so a seam
cannot be added here. `Tier2WebhookFinalizerTest` takes the other route implied by the same
skill: `execute(FinalizerContext ctx)` is a `public` method, so it can be called directly,
as a plain synchronous method call, against a hand-built object that implements
`System.FinalizerContext` (four methods — `getAsyncApexJobId`, `getRequestId`,
`getResult`, `getException`; no `getJobId()` —
`skills/apex/apex-queueable-patterns/SKILL.md` lines 124-133). No
`System.enqueueJob` of the parent job and no `Test.startTest()`/`Test.stopTest()` around
these calls, so the platform machinery that fails a test on an uncaught async exception is
never invoked at all.

**UNVERIFIED (2026-09-12), named in the new file's own header and repeated here so it is
not missed:** no skill in this repo's corpus confirms or denies that a customer-authored
class may implement `System.FinalizerContext` — it is not the technique
`apex-transaction-finalizers` uses in its own worked example, and neither `apexdev.txt`
nor `apexrefguide.txt` excerpts held anywhere in this repo state it either way. The
interface is documented only by its four getters, with the same shape as
`QueueableContext`/`BatchableContext`, which customer code does not implement but is not
documented as forbidden to implement either. **Confirm this compiles against a scratch org
before trusting the coverage number this file contributes in production.** If it does not
compile, the fallback is the one this repair deliberately avoided: add a `@TestVisible`
decision seam to `Tier2WebhookFinalizer.cls` itself (the `apex-transaction-finalizers`
shape) — a shipped-code change, not a test-only one, and out of this run's scope.

**What the five new methods cover, mapped to the finalizer's own branches** (not the
Queueable's — those stay covered where they already were):

| Method | `ctx.getResult()` | `attempt` | Branch exercised |
|---|---|---|---|
| `nullContextIsANoOp` | n/a (`ctx == null`) | 1 | The first-statement defensive guard |
| `successResultTakesNoActionAndDoesNotConsumeTheEnqueueSlot` | `SUCCESS` | 1 | The inert completion path — no DML, no enqueue |
| `transientFailureBelowAttemptCeilingIsRecordedRetryingAndReEnqueuedOnce` | `UNHANDLED_EXCEPTION` | 1 (< ceiling) | `recordAttempt`'s insert path, `Status__c = Retrying`, exactly one re-enqueue |
| `abandonedAfterFinalAttemptIsRecordedAbandonedWithNoReEnqueue` | `UNHANDLED_EXCEPTION` | `MAX_ATTEMPTS` (3) | `recordAttempt`'s insert path, `Status__c = Abandoned`, no re-enqueue |
| `secondConsecutiveFailureUpdatesTheExistingRowRatherThanInsertingASecond` | `UNHANDLED_EXCEPTION` | 2 (< ceiling), existing row supplied | `recordAttempt`'s update path — the row a first attempt already wrote, `Resend__c` cleared, `Request_Payload__c` left untouched |

One branch named in the task and **not** added as a new method: a **permanent-failure**
finalizer branch does not exist to test. A permanent HTTP status (400/401/403/404/422)
never makes `Tier2WebhookQueueable.execute()` throw — `anyTransient` stays `false`, so the
Queueable's own `persistOutcomes` records the failure and returns normally, and
`Tier2WebhookFinalizer.execute(ctx)` only ever sees `SUCCESS` for that case. That path is
already asserted, at the Queueable level where it actually lives, by
`Tier2WebhookQueueableTest.permanentFailureRecordsTheAttemptAndDoesNotStamp` and
`.authFailurePointsTheReaderAtThePrincipalGrant`. Adding a Finalizer-level "permanent
failure" test would either duplicate `successResultTakesNoActionAndDoesNotConsumeTheEnqueueSlot`
under a misleading name or assert something the shipped code does not do — neither is
useful, so neither was written.

A second finding this same reading surfaced, named but not fixed here because it is a
Queueable-side, not a Finalizer-side, gap and it is *already* covered where it lives: the
`recordAttempt`/persistOutcomes symmetry means an "existing row" test for the Queueable's
own `persistOutcomes` (as opposed to the Finalizer's `recordAttempt`, covered by
`secondConsecutiveFailureUpdatesTheExistingRowRatherThanInsertingASecond` above) is also
absent from `Tier2WebhookQueueableTest` — every existing method there passes an empty
`failureRowIdByCaseId`. Out of scope for this run (shipped-class-adjacent test file, not
touched here); worth a follow-up pass on `Tier2WebhookQueueableTest` itself.

**Checked this run:**

```
$ python3 skills/apex/apex-queueable-patterns/scripts/check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03
Scanned 14 Apex file(s), 1 implementing Queueable; 0 ERROR, 0 WARN, 0 ADVISORY.

$ python3 skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py --manifest-dir artefacts/M1-S03 --fail-on HIGH
Scanned 14 Apex file(s); 0 callout finding(s).

$ python3 skills/apex/platform-events-apex/scripts/check_platform_events_apex.py --manifest-dir artefacts/M1-S03
Scanned 14 Apex file(s) and 0 object file(s); 1 platform-event finding(s). WARN — R9,
Tier2EscalationService.cls: no *.permissionset-meta.xml/*.profile-meta.xml **under
artefacts/M1-S03** grants allowCreate on Tier2_Escalation__e. Exit 0 (WARN-only; the
declared test's `expected: exit 0` still holds). Pre-existing and unrelated to this run:
R9 is a checker rule that did not exist at § 0c's run 5 (the command's own past output
shows 0 findings against 13 files that run); the grant this rule wants lives in
`artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml` (S2-F-13,
already fixed and closed by the org in run 9), which is outside this step's own tree by
design — R9 checks only "under artefacts/M1-S03" at step scope and cannot see it there.
Nothing in this run touched `Tier2EscalationService.cls` or any permission set.

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir artefacts/M1-S03/classes
Scanned 12 Apex class file(s); audited 7 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
```

Three of four exit 0 with zero findings; the fourth exits 0 with one pre-existing WARN
unrelated to this run's own file. `check-outputs` is `ok` on all 20 declared paths — the
new file is undeclared-but-shipped, the same shape `TestUserFactory.cls`,
`MockHttpResponseGenerator.cls` and `TestDataFactory.cls` already are (§ 1, § 2). Brace,
paren, bracket and single-quote balance verified mechanically on the new file; all 14
`-meta.xml` under this step's artefacts parse at `apiVersion` 67.0 (13 before this run, the
new file's meta the 14th). **No non-test class changed** — the three step-declared
checkers were re-run unchanged for that reason alone, as in § 0b and § 0c.

**M1-S05 needs a new member.** `Tier2WebhookFinalizerTest` is an `ApexClass` this build now
ships and `artefacts/M1-S05/package.xml` does not yet name it — the same open item § 0b
recorded for `TestUserFactory` (S4-F-02, still unresolved) now has a second name on it.
Both are metadata-builder's to add on M1-S05's next run.

**Not part of this repair, and not touched:** every production class, both triggers, all
three pre-existing test classes (`Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest`,
`IntegrationFailureResendTest`) — bodies and meta XML alike — `TestUserFactory.cls`,
`MockHttpResponseGenerator.cls`, `TestDataFactory.cls`, and every other `-meta.xml`.

**Consequence for the milestone.** `milestone:M1` was approved on evidence that predates
S2-F-06, S2-F-11, S2-F-12 **and now S2-F-14**. This step returns to `built` once
`check-outputs` passes (it does); `step-tester`, `build-doc-keeper` and a fresh
`/verify-milestone` are the human's next commands, against a dry run whose coverage number
reflects this run's five new methods. Whether 70.8% actually clears 75% once
`Tier2WebhookFinalizerTest` runs for real is an org-side question no agent in this loop can
answer — the one thing every agent in this loop has been able to say all along
(`agents/_shared/AGENT_CONTRACT.md` § Gate C: no offline Apex compiler in the `sf` CLI).

---

## 0e. Repair record — run 7, after S2-F-15 (the org answered § 0d's UNVERIFIED note, partly)

**Trigger:** `reports/MOCK-DEPLOY-M1.md` run 10 and `reports/mock-deploy/2026-09-12T17-44-44Z/summary.md`
— MANIFEST mode, `--test-level RunSpecifiedTests`, after run 6 (§ 0d). Two things settled
at once: **`Tier2WebhookFinalizerTest.cls` compiles at API 67.0** — § 0d's central
UNVERIFIED question (may customer code implement `System.FinalizerContext`?) is answered
**yes**, for this org — and coverage rose to **86.8%**, clear of the 75% floor. But 34
tests ran, 33 passed, **1 failed**: `transientFailureBelowAttemptCeilingIsRecordedRetryingAndReEnqueuedOnce`.

**S2-F-15 (MEDIUM, test-only).** § 0d's own file header carried an assumption that turned
out to be wrong: that omitting `Test.startTest()`/`Test.stopTest()` around a direct
`Tier2WebhookFinalizer.execute(ctx)` call would prevent the Finalizer's own re-enqueued
`Tier2WebhookQueueable` from ever running inside the test. The org's real execution
disproves it — the re-enqueued job ran to completion by the end of the enclosing test
method regardless. In the one failing method, the original call was built with `attempt =
1`, so the Finalizer re-enqueues a job at `attempt = 2` — still below `MAX_ATTEMPTS` (3).
No `Test.setMock()` was registered anywhere in that method (the class's other four methods
never perform a callout, and this one wasn't expected to either), so when the re-enqueued
job ran, its callout threw `CalloutException`, `attemptOne` classified that as transient,
and `Tier2WebhookQueueable.execute()` re-threw its own transient-retry exception at line
340 — this time uncaught, and by the same mechanism § 5 item 3 named, it failed the test
method.

**Why the sibling method (`secondConsecutiveFailureUpdatesTheExistingRowRatherThanInsertingASecond`)
did not also fail, on the same reasoning that explains this one:** that method calls
`execute(ctx)` with `attempt = 2`, so its own re-enqueued job lands at `attempt = 3 =
MAX_ATTEMPTS`. When that job's callout also fails with no mock, `anyTransient` is `true`
but `attempt < MAX_ATTEMPTS` is now `false`, so `Tier2WebhookQueueable.execute()` does
**not** re-throw — it falls through to `persistOutcomes`, which quietly records the row
`Abandoned` and returns normally. No uncaught exception, no test failure, but also a
second, unasserted write to the same row this method's own assertions already checked —
harmless here only because those assertions run, and are evaluated, before that later
write occurs (see the fix below).

**Fixed — one method, one line, nothing else in the file or the shipped classes:**

```apex
Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(200, OK_BODY));
```

added immediately before `finalizer.execute(...)` in
`transientFailureBelowAttemptCeilingIsRecordedRetryingAndReEnqueuedOnce`, plus a new
class-level `OK_BODY` constant (the same value `Tier2WebhookQueueableTest` uses) and a
corrected class header (the CORRECTED note replaces the § 0d-era claim that the
re-enqueued job never runs). **Chosen over "assert the enqueue without forcing
execution"** because the org's own result already ruled that alternative out: the
re-enqueued job ran regardless of the missing `Test.startTest()`/`Test.stopTest()` wrap,
so there is no way, in this environment, to call `Tier2WebhookFinalizer.execute(ctx)` from
this class without the platform eventually running whatever job it re-enqueues. Given
that, the only lever left is what `skills/apex/callouts-and-http-integrations` and
`skills/apex/apex-mocking-and-stubs` both already prescribe for any code path that might
perform a callout under test: register a mock before it can run, so the callout succeeds
instead of raising `CalloutException`. This does not weaken the method's own claim: every
`Assert` in it reads the database synchronously, immediately after `finalizer.execute()`
returns and strictly before the platform's later execution of the re-enqueued job, so it
still observes `recordAttempt`'s "insert one `Retrying` row, attempt 1" outcome in
isolation. What happens to that row afterward — the retried job's own eventual success
updates it to `Resolved` and stamps the Case — is not asserted by this method and was
never claimed to be; that later, successful completion is now merely inert instead of
fatal.

**Checked this run — all four exit 0 (`--fail-on HIGH` on the second, no `--strict` on the
fourth), the platform-events WARN unchanged and unrelated:**

```
$ python3 skills/apex/apex-queueable-patterns/scripts/check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03
Scanned 14 Apex file(s), 1 implementing Queueable; 0 ERROR, 0 WARN, 0 ADVISORY.

$ python3 skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py --manifest-dir artefacts/M1-S03 --fail-on HIGH
Scanned 14 Apex file(s); 0 callout finding(s).

$ python3 skills/apex/platform-events-apex/scripts/check_platform_events_apex.py --manifest-dir artefacts/M1-S03
Scanned 14 Apex file(s) and 0 object file(s); 1 platform-event finding(s) (WARN, R9,
Tier2EscalationService.cls — pre-existing since § 0d, untouched by this run).

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir artefacts/M1-S03/classes
Scanned 12 Apex class file(s); audited 7 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
```

`check-outputs` is `ok` on all 20 declared paths (unchanged — the fixed file is still
undeclared-but-shipped). All 14 `-meta.xml` under this step still parse at `apiVersion`
67.0 (no meta file changed this run). Brace/paren/bracket balance and string-literal
single-quote parity (computed with block and line comments stripped, since the file's own
doc comments use plain-English apostrophes that a raw count would miscount) verified
mechanically on the edited file. **No shipped class and no other test class changed.**

**Not part of this repair, and not touched:** every production class, both triggers, all
three pre-existing test classes other than the file above, `TestUserFactory.cls`,
`MockHttpResponseGenerator.cls`, `TestDataFactory.cls`, and every `-meta.xml`.

**What is still open.** `secondConsecutiveFailureUpdatesTheExistingRowRatherThanInsertingASecond`'s
own re-enqueued job (landing at `attempt = MAX_ATTEMPTS`) also runs for real and also
performs an unmocked callout — it happens not to throw, because it falls into
`persistOutcomes`'s no-retry branch instead of re-throwing, but it is still relying on the
same real, now-confirmed platform behaviour by accident rather than by a registered mock.
A future pass could register the same 2xx mock there too, for the same reason this run
registered one here, even though nothing currently fails without it. `M1-S05`'s
`package.xml` gap from § 0d (`Tier2WebhookFinalizerTest` not yet a declared `ApexClass`
member, alongside `TestUserFactory`) is unchanged by this run — this repair edited the
class's content, not its existence.

**Consequence for the milestone.** Unchanged in kind from § 0d: `milestone:M1` was
approved on evidence that now predates S2-F-06, S2-F-11, S2-F-12, S2-F-14 **and S2-F-15**.
This step returns to `built` once `check-outputs` passes (it does); a fresh dry run with
`--test-level RunSpecifiedTests` is what would confirm 34/34 passing and re-confirm
coverage — no agent in this loop can run one.

---

## 0f. Repair record — run 8, after S2-F-16 (aggregate coverage passed; one class's own didn't)

**Trigger:** `reports/MOCK-DEPLOY-M1.md` run 11, after run 7's (§ 0e) fix. **35 of 35
tests pass**, aggregate coverage **86.2%** — both numbers that would normally close this
loop. The validation still fails, on a line the run's own summary text did not print:

```
codeCoverageWarnings: Tier2EscalationService — Test coverage of selected Apex Class is
53.659%, at least 75% test coverage is required
```

**S2-F-16 (MEDIUM, test coverage).** With `--test-level RunSpecifiedTests`, the platform
enforces the 75% floor **per class**, not only in aggregate — a fact this build's own
`deploy-order.md` had not yet had cause to state, because every previous coverage finding
(S2-F-14) was read off the aggregate number. `Tier2EscalationService` sat at 53.659%
individually the whole time; it was invisible while the aggregate was failing anyway
(runs 6–9) and stayed invisible through run 10 because nothing printed the per-class
detail until this run's fuller summary did. The per-class gap was on file all along:
`reports/mock-deploy/2026-09-12T17-17-07Z/result.json`'s `codeCoverage` array recorded 19
of 41 lines uncovered for this exact class back at run 9 — this run reads that recorded
detail rather than re-deriving it.

**The 19 uncovered lines, read against the class body, are exactly two branches:**

| Lines | What they are |
|---|---|
| 44 | The `escalatedCases == null \|\| .isEmpty()` early-return guard |
| 84–91, 95–96 | Building an `Integration_Failure__c` row for one rejected `EventBus.publish()` result |
| 106 | `insert publishFailures;` — only reached when at least one publish was rejected |
| 119–127 | `errorText(List<Database.Error>)` — the whole method, never called because nothing ever rejects a publish |

Every existing method in `Tier2EscalationServiceTest` drives `escalate()` indirectly,
through a real Case save via `CaseTriggerHandler`, and every save it makes escalates a
real, fully-populated Case whose `EventBus.publish()` call always succeeds (the org
already confirmed, in run 9's fix for S2-F-13, that the permission set grants Create on
`Tier2_Escalation__e`) — so neither branch above is reachable from that path. The
empty-list guard is never hit because the handler only calls `escalate()` with at least
one Case in a batch it already filtered; the publish-rejection branch is never hit because
nothing about a normal trigger-driven save can make a required event field come up null.

**Fixed — two new test methods, nothing shipped touched:**

`artefacts/M1-S03/classes/Tier2EscalationServiceTest.cls` gained a new section calling
`Tier2EscalationService.escalate(List<Case>)` directly — the class's only public method,
`public static` for exactly this reason — rather than through a Case save, since neither
gap is reachable through the trigger path every other method in the file uses:

1. **`escalateWithNoCasesReturnsImmediately`** — calls `escalate(null)` and
   `escalate(new List<Case>())`, asserting no enqueue and no DML happened. Covers line 44.
2. **`escalateWithAMissingCaseNumberWritesAPublishFailureRowAndStillEnqueuesTheJob`** —
   constructs an in-memory `Case` with `Subject` and `Priority` set but `CaseNumber`
   deliberately left unset, and calls `escalate()` with it. `Tier2_Escalation__e.
   Case_Number__c` is `required=true` (`M1-S01`), and `escalate()` maps it straight from
   `Case.CaseNumber` with no null guard (line 61), so this rejects the publish
   **deterministically, on a required-field violation** — a different, simpler mechanism
   than mock-deploy run 8's S2-F-13 (a missing `Tier2_Escalation__e` Create grant), which
   needed a second, differently-permissioned user to reach and which this build's shipped
   permission sets no longer have a way to construct now that S2-F-13's fix bundled both
   grants (`Integration_Failure__c` CRUD and `Tier2_Escalation__e` Create) into the one
   `Tier2_Webhook_Admin` set. `escalate()` never re-queries the Case, so the real row's
   actual `CaseNumber` in the database is irrelevant — only the in-memory value the test
   constructs matters. Asserts the failure row's `Case__c`, `Status__c` (`New`),
   `Severity__c` (`Error`), `Attempt_Count__c` (1), a blank `Endpoint__c` (proving no
   callout was attempted — the documented way to tell a publish failure from a webhook
   failure), and that `Error_Message__c` carries `errorText()`'s output. Also asserts the
   webhook job is still enqueued exactly once, per Q11 (a lost event is the tolerable
   half; the webhook is not skipped). Covers lines 84–96, 106 and all of 119–127.

**A mock is registered in both methods before the call**, per the lesson § 0e (S2-F-15)
already recorded on this same step: `escalate()` unconditionally enqueues a
`Tier2WebhookQueueable` (line 103) regardless of publish outcome, and the org's own run 10
proved that a Finalizer-or-Queueable-enqueued job runs to completion by the end of the
enclosing test method regardless of `Test.startTest()`/`Test.stopTest()` wrapping. Without
a 2xx mock, that job's own callout would throw unmocked and fail the test — exactly § 0e's
finding, now applied proactively rather than discovered by a second failing dry run.

**Checked this run — all four exit 0, the platform-events WARN unchanged and unrelated:**

```
$ python3 skills/apex/apex-queueable-patterns/scripts/check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03
Scanned 14 Apex file(s), 1 implementing Queueable; 0 ERROR, 0 WARN, 0 ADVISORY.

$ python3 skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py --manifest-dir artefacts/M1-S03 --fail-on HIGH
Scanned 14 Apex file(s); 0 callout finding(s).

$ python3 skills/apex/platform-events-apex/scripts/check_platform_events_apex.py --manifest-dir artefacts/M1-S03
Scanned 14 Apex file(s) and 0 object file(s); 1 platform-event finding(s) (WARN, R9,
Tier2EscalationService.cls — pre-existing since § 0d, untouched by this run). R7 (a test
that publishes without draining the event bus) does not fire on either new method: both
call Tier2EscalationService.escalate(...), never EventBus.publish(...) directly, so the
checker's own text-match scope never sees a publish call inside the test file — the same
reason § 5's "Not a gap" note already gives for every other method in this class.

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir artefacts/M1-S03/classes
Scanned 12 Apex class file(s); audited 7 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
```

`check-outputs` is `ok` on all 20 declared paths (unchanged — `Tier2EscalationServiceTest`
is a declared output; only its content changed). All 14 `-meta.xml` still parse at
`apiVersion` 67.0 (none changed this run). Brace/paren/bracket balance and string-literal
quote parity (comments stripped) verified mechanically on the edited file. **No shipped
class and no other test class or method changed.**

**What is still open.** Whether `Tier2EscalationService` now individually clears 75% is
an org-side question no agent in this loop can answer. If the two new methods' 19 lines
map cleanly onto the 19 previously-uncovered locations (they should, by direct line
correspondence, since between them they touch every uncovered line in the table above),
41 covered of 41 would be 100% — comfortably clear of 75% — but that arithmetic is not
itself a substitute for the platform re-running the class's coverage instrumentation.

**Consequence for the milestone.** Unchanged in kind from § 0e: `milestone:M1` was
approved on evidence that now predates S2-F-06, S2-F-11, S2-F-12, S2-F-14, S2-F-15 **and
S2-F-16**. This step returns to `built` once `check-outputs` passes (it does); a fresh dry
run with `--test-level RunSpecifiedTests` is what would confirm both 37/37 (35 + 2) tests
passing and `Tier2EscalationService` individually clearing 75%.

---

## 0. Rebuild record — run 3, after the org rejected run 2

Run 2 was tested clean — five acceptance tests, three declared checkers all exit 0 — and
then **failed the operator's dry-run validation** (`reports/MOCK-DEPLOY-M1.md` run 3 —
`checkOnly`, org `sfskills-dev`, API 67.0, source mode over M1-S01 … M1-S04: 39
components, 29 ok, **11 errors**).

**Eleven errors, two roots, nine cascade.** The cascade is
`Dependent class is invalid and needs recompilation` on five classes and
`Variable does not exist: CaseTriggerHandler` / `: IntegrationFailureTriggerHandler` on the
two triggers — every one of them downstream of the two real faults below. **M1-S04's four
classes compiled clean.**

### Root 1 — S2-F-04 (HIGH). The org's message, verbatim:

> `Method was removed after version 58.0: getSalesforceBaseUrl`

Raised on `ApexClass Tier2EscalationService` and `ApexClass Tier2WebhookQueueable`, both of
which built the link back to the Case with `URL.getSalesforceBaseUrl().toExternalForm()`.
These classes are pinned to **67.0**, nine versions past the removal.

**Fixed:** both call sites now use `URL.getOrgDomainUrl().toExternalForm()` — the form the
Apex Developer Guide's own examples use at this version (`apexdev` L32630, L37043), supplied
by the operator with the failure.

**The lesson, and it is the important half of this entry.** Run 2's own § 9 claimed
`getSalesforceBaseUrl` was "the accessor this repo's own skills use", and it was — three
skills spell it, which is exactly why a `grep` for attestation returned a hit and the name
passed Gate C check 2. **What none of those three carries is the version gate.** The
identifier was attested; the *idiom* was recalled from memory, and
`AGENT_CONTRACT.md` rule 12 is about both. A repo grep proves a name exists somewhere in
the corpus; it does not prove the name is legal at the `apiVersion` this step stamps into
its meta XML. Attestation is necessary and it is not sufficient, and nothing offline caught
the difference — not the three checkers, not the XML parse, not the brace scan. **Only the
org did.** The three skills that carry the old method are a library defect the operator has
logged against them (`reports/MOCK-DEPLOY-M1.md`, S2-F-04) and are not this step's to edit.

### Root 2 — S2-F-05 (MEDIUM). The org's message, verbatim:

> `field 'Request_Payload__c' can not be filtered in a query call`

Raised twice on `ApexClass IntegrationFailureResendTest`, which selected its two fixture
rows with `WHERE Request_Payload__c != NULL` and `WHERE Request_Payload__c = NULL`.
M1-S01 declares that field `<type>LongTextArea</type>`, and a long or rich text area
**cannot be filtered, grouped or sorted** in SOQL.

**Fixed:** one helper, `rowsWithACase()`, selects every seeded row that has a Case
(`WHERE Case__c != NULL ORDER BY Attempt_Count__c DESC` — both filterable) and
`rowWithPayload()` / `rowWithoutPayload()` pick in memory on the **selected** value. The
no-payload test now asserts `Request_Payload__c` is null on the row it picked, so the test
still proves which fixture it got instead of trusting a filter the platform will not run.

### What changed in run 3 — three call sites in three files, and nothing else

| File | Change |
|---|---|
| `classes/Tier2EscalationService.cls` | `getSalesforceBaseUrl()` → `getOrgDomainUrl()` on the `baseUrl` line, plus the comment saying why (**fixes S2-F-04**) |
| `classes/Tier2WebhookQueueable.cls` | same substitution on the `caseUrl` entry of `requestBody()` (**fixes S2-F-04**) |
| `classes/IntegrationFailureResendTest.cls` | the two Long-Text-Area `WHERE` clauses replaced by select-then-pick helpers (**fixes S2-F-05**) |
| every other file | **byte-identical to run 2** — the two triggers, the two handlers, the Finalizer, the other two test classes, all twelve meta XML files and both verbatim template copies are untouched |

Nine of the eleven errors were cascade and needed no edit; the fix for a cascade is fixing
its root, and re-running the dry run is what confirms that rather than any offline check.

**Still unproven.** This package has been compiled by an org exactly once, and it failed.
Run 3 has not been compiled at all. The three checkers, the XML parse and the brace scan
all pass, and none of them is a compile — see § 5 item 5.

---

## 1. What this step ships

| # | File | Declared in `outputs[]`? | Role |
|---|---|---|---|
| 1 | `triggers/CaseTrigger.trigger` (+ `-meta.xml`) | yes | `after update` only; delegates, holds no logic |
| 2 | `triggers/IntegrationFailureTrigger.trigger` (+ `-meta.xml`) | yes | `after update` only; the admin resend call site |
| 3 | `classes/CaseTriggerHandler.cls` (+ `-meta.xml`) | yes | detection, queue lookup by DeveloperName, recursion guard, suppression |
| 4 | `classes/IntegrationFailureTriggerHandler.cls` (+ `-meta.xml`) | yes | resend detection, stored-key replay, one job per save |
| 5 | `classes/Tier2EscalationService.cls` (+ `-meta.xml`) | yes | the escalating transaction: publish, inspect the SaveResults, enqueue once |
| 6 | `classes/Tier2WebhookQueueable.cls` (+ `-meta.xml`) | yes | the callouts, the classification, the stamp and the failure rows |
| 7 | `classes/Tier2WebhookFinalizer.cls` (+ `-meta.xml`) | yes | the only place a retry is decided |
| 8 | `classes/Tier2EscalationServiceTest.cls` (+ `-meta.xml`) | yes | 6 methods: detection, bulk, suppression both ways, two negatives |
| 9 | `classes/Tier2WebhookQueueableTest.cls` (+ `-meta.xml`) | yes | 7 methods: 200 / 422 / 401 / 503-exhausted, suppression, classification, key stability |
| 10 | `classes/IntegrationFailureResendTest.cls` (+ `-meta.xml`) | yes | 6 methods: resend, key replay, override of suppression, fallback, two negatives |
| 11 | `classes/TestDataFactory.cls` (+ `-meta.xml`) | **no — undeclared** | verbatim copy of `templates/apex/tests/TestDataFactory.cls` (§ 2) |
| 12 | `classes/MockHttpResponseGenerator.cls` (+ `-meta.xml`) | **no — undeclared** | verbatim copy of `templates/apex/tests/MockHttpResponseGenerator.cls` (§ 2) |
| 13 | `classes/TestUserFactory.cls` (+ `-meta.xml`) | **no — undeclared** | verbatim copy of `templates/apex/tests/TestUserFactory.cls` (§ 2); added run 4 to close S2-F-11 (§ 0b) |
| 14 | `deploy-order.md` (this file) | **no — undeclared** | named by `agents/apex-builder/AGENT.md` Output Contract item 2 as where template provenance is recorded |

**20 declared paths, all present; 6 undeclared files** (was 5 before run 4's
`TestUserFactory.cls` + `-meta.xml` addition — one file, not two rows, since the pair
counts once against the same gap). The undeclared set is a plan gap this run could not
close: the step's `templates[]` never listed `TestUserFactory` either, and
`check-outputs` only ever confirms paths the plan declared. `amend-step` is the writer
for that and it is refused once a step has left `pending` — true before run 4 and true
now — so the correction belongs to whoever re-plans. `check-outputs` passes on the
twenty declared paths regardless; the addition changes nothing check-outputs looks at.

**No `package.xml`.** `apex-builder`'s Output Contract names none, and
`standards/build-orchestration.md` § 5 **The Apex exception** puts these thirteen
`ApexClass` and two `ApexTrigger` members in the build-level manifest step **M1-S05**,
which `depends_on` this step. `TestUserFactory` is a thirteenth member M1-S05 did not
have before run 4 (§ 0b) — see § 2 for the exact member list and the de-duplication
note it already carries for `TestDataFactory`.

### Two triggers on two sObjects in one invocation — the recorded exception

The plan verifier raised this as **W6** and the requester accepted it at the `plan` gate.
`IntegrationFailureTrigger` re-enters `Tier2WebhookQueueable`; it emits no callout, no
event and no class the escalation path does not already need. Splitting it out would be a
sixth functional step, which the `feature` tier's five-step ceiling does not allow. The
argument is in the step's `feature_summary`, where this agent's own
`REFUSAL_OUT_OF_SCOPE` check reads it.

---

## 2. Template-class provenance

`agents/apex-builder/AGENT.md` Step 6: every `templates/apex/**` class an emitted class
or test references ships in this step's outputs as a verbatim copy plus its `-meta.xml`,
or is already declared by an earlier plan step. M1-S01 and M1-S02 declare none.

| Referenced | Shipped here | `diff` against the template |
|---|---|---|
| `TestDataFactory` (`createCases(count, accountId, overrides)` in all three test classes' `@TestSetup`) | `classes/TestDataFactory.cls` + `-meta.xml` | **empty — verified run 4** |
| `MockHttpResponseGenerator` (`withResponse(status, body)` in every callout test) | `classes/MockHttpResponseGenerator.cls` + `-meta.xml` | **empty — verified run 4** |
| `TestUserFactory` (`createUser(profileName, permissionSetNames)` in all three test classes' `@TestSetup`, added run 4 to close S2-F-11 — § 0b) | `classes/TestUserFactory.cls` + `-meta.xml` | **empty — verified run 4** |

All three are self-contained: none references another `templates/apex` class and none
names a custom object or custom metadata type. That is the whole reason `TestDataFactory`
and `MockHttpResponseGenerator` survived remedy B while three others did not (§ 4), and
the same property is why `TestUserFactory` could be added in a test-only repair without
reopening remedy B: it needs nothing remedy B dropped.

### The TestDataFactory duplication, and what M1-S05 must do about it

**M1-S04 ships a byte-identical `TestDataFactory.cls` under its own artefacts.** That is
not a collision at deploy: `scripts/mock_deploy.py:copy_artefacts` rebases every file
onto `<dest>/<path-relative-to-the-step-dir>`, so
`artefacts/M1-S03/classes/TestDataFactory.cls` and
`artefacts/M1-S04/classes/TestDataFactory.cls` land on the same assembled path and the
later step overwrites the earlier. Both are byte-identical to the template, so the
assembled tree is correct either way.

**One consequence for M1-S05: emit the `TestDataFactory` `ApexClass` member exactly
once.** A `package.xml` listing it twice is a manifest defect. The full member list this
step contributes, updated run 4 to add `TestUserFactory` (§ 0b — not shipped by any
other step in this plan, so no de-duplication question for it):

```text
ApexClass:   CaseTriggerHandler, IntegrationFailureTriggerHandler, Tier2EscalationService,
             Tier2WebhookQueueable, Tier2WebhookFinalizer, Tier2EscalationServiceTest,
             Tier2WebhookQueueableTest, IntegrationFailureResendTest,
             MockHttpResponseGenerator, TestDataFactory,   ← also contributed by M1-S04
             TestUserFactory   ← added run 4, S2-F-11
ApexTrigger: CaseTrigger, IntegrationFailureTrigger
```

**M1-S05 is out of scope for this run.** This repair is scoped to M1-S03 alone; the
build-level `package.xml` at `artefacts/M1-S05/` (and the already-rendered
`reports/MILESTONE-M1-package.xml`) still lists the pre-run-4 twelve `ApexClass`
members and does not yet carry `TestUserFactory`. Re-running M1-S05 — or amending its
manifest — is a follow-up this run surfaces but does not perform.

**The structural fix is a plan change, not a file change.**
`standards/build-orchestration.md` § 4, Apex row note: when more than one Apex step
shares a template dependency, the plan runs a dedicated *Apex foundations* step first.
This plan has two Apex steps and no such step. Recommend it at the M1 gate — it is also
the shape remedy **A** would have taken.

---

## 3. Deploy order

| Must precede | This step | Why |
|---|---|---|
| **M1-S01** `Integration_Failure__c` + its 12 fields, `Case.Tier2_Notified_At__c`, `Tier2_Escalation__e` + its 5 payload fields | every class here | None of the six production classes compiles without them. Every custom symbol this step names was checked against `artefacts/M1-S01/` this run; the full list is in § 9. |
| **M1-S02** `OnCall_Tool` Named Credential | `Tier2WebhookQueueable` | The Apex composes `callout:OnCall_Tool`. A `callout:` naming a credential not in the org fails at run time. |
| **M1-S02** `Tier2_Webhook_Admin`, **assigned** | first run of either trigger | The Queueable calls out as the async context user and the Finalizer runs as the same. Without the assignment every callout returns 401 and lands in an `Integration_Failure__c` row (decision D14, assumption A2). |

| This step | Must precede | Why |
|---|---|---|
| all 14 members | **M1-S05** build-level `package.xml` | M1-S05 aggregates; it does not re-declare these files. |

Within this step the Metadata API resolves `ApexClass` and `ApexTrigger` in one request;
no internal ordering is required.

---

## 4. Remedy B — what was dropped, and what each drop costs

Run 1 refused because three of the five templates the step then mandated were unshippable
in this build: their transitive closure needs `Application_Log__c`, `Logger_Setting__mdt`
and `Trigger_Setting__mdt`, and no step ships any of them (**Q16**: "We have no existing
Apex log object in the org"). The requester chose remedy B. Each drop is a real loss and
each is written down rather than absorbed.

| Dropped | Replaced by | What the org loses |
|---|---|---|
| `templates/apex/TriggerHandler.cls` (→ `TriggerControl` → `Trigger_Setting__mdt`) | a plain `after update` trigger delegating to a static handler entry point, with a per-transaction `Set<Id>` recursion guard (`skills/apex/recursive-trigger-prevention/references/examples.md`) | **the kill switch** — see below |
| `templates/apex/BaseService.cls` (→ `ApplicationLogger`) | a plain `with sharing` service class; savepoint/rollback helpers were unused by this feature | nothing this feature used. `beginTransaction`/`rollbackTransaction` had no caller here |
| `templates/apex/HttpClient.cls` (→ `ApplicationLogger`) | `HttpRequest` built directly against `callout:OnCall_Tool`, the shape in `skills/apex/apex-queueable-patterns/references/examples.md` Example 2 | the fluent builder and its retry loop. The retry loop was **deliberately off anyway** (`retryOnTransient(false)` — its back-off is a busy-wait against Apex CPU time), so what is actually lost is the builder, not the behaviour |
| `templates/apex/ApplicationLogger.cls` | `Integration_Failure__c` rows plus `System.debug(LoggingLevel.ERROR, …)` | a queryable log for anything that is **not** a delivery attempt |

### The missing kill switch — read this before go-live

`TriggerControl` is what lets an admin switch a handler off from Setup, without a
deployment, by flipping a `Trigger_Setting__mdt` record — and what honours the
`TriggerControl_BypassAll` Custom Permission during a data load. **Neither exists in this
build.** The consequences, plainly:

1. **A data load that reassigns Case ownership in bulk will escalate every affected
   Case.** There is no bypass. A load that moves 5,000 Cases into `Tier_2_Engineering`
   enqueues the webhook for all of them.
2. **Turning the feature off is a deployment**, not a checkbox: deactivate
   `CaseTrigger` by deploying its `-meta.xml` with `<status>Inactive</status>`.
3. The recursion guard is *not* a substitute. It stops this handler re-entering itself
   inside one transaction; it does nothing about a bulk load, which is many transactions
   each doing exactly what it was asked to do.

The remedy, if the org wants the switch, is the Apex-foundations step in § 2 — it ships
`Trigger_Setting__mdt` alongside the other two types and lets `TriggerHandler` and
`TriggerControl` be used as intended.

### The logging loss, scoped

`Integration_Failure__c` is a good log for delivery attempts and a non-log for everything
else. Three failure modes now reach `System.debug` only, where they survive until the
debug log rolls off:

- `CaseTriggerHandler`: no queue named `Tier_2_Engineering` is visible to the saving user
  (assumption A8 says there is one). Escalation becomes silently impossible.
- `IntegrationFailureTriggerHandler`: a resend row whose `Request_Payload__c` will not
  parse, or that carries no stored escalation time — the replayed Idempotency-Key then
  differs from the original.
- `Tier2WebhookFinalizer`: the completion note on a successful attempt, and the
  attempt-budget-exhausted note.

None is a delivery attempt, so none belongs on `Integration_Failure__c` (Q16–Q18 make
that object the record of attempts). If any of the three needs to be queryable, that is
the Apex-foundations step again, or a fourth `Severity__c` value nobody has asked for.

---

## 5. UNVERIFIED and unstated — read before deploying

Five items the plan, the 45 clarifications and the cited skills leave unstated. None is
guessed silently; each is written the narrowest legal way and flagged here.

1. **`Tier2_Escalation__e.Severity__c` is mapped from `Case.Priority`, and nothing says
   it should be.** The event carries a `Severity__c` Text(40); no answer maps it to a
   Case field. `Priority` is the only severity-shaped field this build has seen on Case,
   so it is what the service writes, with an inline `// UNVERIFIED` note at the
   assignment. Q11's answer talks about "a Severity 1 escalation", which is **not** the
   shape of standard `Case.Priority` values (High / Medium / Low) — so the org may have a
   severity field this build never saw. **Confirm with the dashboard team before UAT**;
   a wrong value here is silently wrong, not loud.
2. **Whether `HttpCalloutMock.respond()` receives the literal `callout:OnCall_Tool`
   string or a platform-resolved endpoint is UNVERIFIED** (step input `unverified`, from
   `skills/apex/apex-named-credentials-patterns/references/code-examples.md` § 6). No
   test here asserts on `getEndpoint()`; every callout test uses the mock's default
   response rather than path routing, so no test depends on the answer either way.
3. **Three async behaviours are not exercisable in an Apex test, and no test pretends
   otherwise:**
   - `AsyncOptions.MinimumQueueableDelayInMinutes` — *"The delay is ignored during Apex
     testing"* (`skills/apex/apex-queueable-patterns/references/gotchas.md`). No test
     asserts on the back-off interval.
   - **The transient-retry branch.** A transient failure with attempts left makes
     `execute()` throw so the Finalizer owns the retry; an unhandled exception in a job
     run by `Test.stopTest()` fails the test method. The classification that drives the
     branch is asserted directly (`statusCodesAreClassifiedTheWayTheRetryContractSays`)
     and the exhausted-budget end of it is asserted through a real job
     (`transientFailureOnTheLastAttemptIsAbandonedRatherThanRetried`). **The throw →
     Finalizer → re-enqueue path itself is deliberately uncovered.**
   - **The chained tail.** Only one job may be added to the queue from a test context, so
     `chainRemainder()` is guarded by `Test.isRunningTest()`. The 200-Case bulk test
     asserts the *bound* (one job, `MAX_CASES_PER_JOB` Cases called out for) rather than
     the tail.
4. **`Case_Link__c` is built with `URL.getOrgDomainUrl().toExternalForm()`.** The form
   this repo's skills carry — `getSalesforceBaseUrl()` — does not compile at 67.0, and the
   org is what established that (§ 0, root 1). What is still unstated is which URL the
   dashboard wants: the org domain plus the record Id resolves to the Lightning record
   page, and nothing in the plan says that is the link the on-call engineer should land on.
   Confirm at UAT.
5. **No compile check ran.** `build_mode` is `design-only`, there is no
   `target_org_alias`, and there is no offline Apex compiler in the `sf` CLI
   (`agents/_shared/AGENT_CONTRACT.md` § Gate C). Brace, paren, bracket and string-literal
   balance were verified mechanically on all 12 Apex files and every `-meta.xml` parses at
   `apiVersion` 67.0 — **neither is a compile**. The first real compile is the operator's
   `mock_deploy.py --dry-run`.

### Not a gap: `Test.getEventBus().deliver()` appears nowhere

Step input `tests` requires any **direct** `EventBus.publish` inside a test method to
assign its result and pair it with `Test.getEventBus().deliver()`. No test in this step
publishes directly — the publish happens inside `Tier2EscalationService`, driven by a real
Case save — so the rule is satisfied vacuously and `check_platform_events_apex.py` R7
does not fire. There is also no Apex subscriber to this event in the build (Q39: no internal
Apex or Flow subscriber is described; the dashboard consumes it externally), so there is nothing for `deliver()` to
drive.

---

## 6. How the design meets each bound input

| Step input | Where it lives |
|---|---|
| `detection` | `CaseTriggerHandler.queueId(String)` — a `private static Map<String, Id>` filled once per transaction from `SELECT Id, DeveloperName FROM Group WHERE Type = 'Queue' WITH USER_MODE`. **No Id literal anywhere in this step**, tests included: all three test classes create the queue by `DeveloperName` inside `System.runAs` and query it back. |
| `enqueue_contract` | `Tier2EscalationService.escalate()` enqueues once for the whole transaction; three tests assert `Limits.getQueueableJobs() == 1`, one of them at 200 Cases. |
| `ordering_constraint` / **D10** | Publish is in the service, in the escalating transaction. `Tier2WebhookQueueable.execute()` runs every callout in phase 1 and every DML in phase 3, with nothing between them but the retry decision. |
| `publish_result` / **Q11** | `List<Database.SaveResult> publishResults = EventBus.publish(events);` — assigned, then walked index-parallel with the Case list; a rejection writes an `Integration_Failure__c` row with `Severity__c` Error and a **blank `Endpoint__c`**, which is how an admin tells a publish failure from a webhook failure. |
| `retry_contract` / `finalizer_contract` | `System.attachFinalizer(...)` is the first statement of `execute()`. Transient = 429/502/503/504 plus status 0 (connection failure or timeout); permanent = 400/401/403/404/422. `Tier2WebhookFinalizer` re-enqueues with `AsyncOptions.MinimumQueueableDelayInMinutes` while `attempt < 3`. It uses `getAsyncApexJobId()`, `getRequestId()`, `getResult()` and `getException()` — **not `getJobId()`, which `FinalizerContext` does not have**. |
| `idempotency` / **D6** | `idempotencyKey(caseId, escalatedAt)` = Case Id + `':'` + epoch millis. The escalation timestamp is captured **once** in the service and carried per Case in a `Map<Id, Datetime>`, so a retry and an admin resend rebuild the identical key. Asserted in two tests. |
| `suppression` / **D13** | Checked twice: in the handler at detection, and again in the job, because the handler cannot see an escalation still in flight in another transaction. `AsyncOptions.DuplicateSignature` is not used. A resend bypasses the window on purpose (`isResend`). |
| `picklist_values` / **Q17** | Named constants only: `New`, `Retrying`, `Resent`, `Resolved`, `Abandoned`, `Error`. No other literal is written to either restricted field. |
| `sharing_and_security` / **Q23** | All six production classes are `with sharing`; both SOQL statements carry `WITH USER_MODE`; DML runs in the 67.0 default user mode. **No `WITH SECURITY_ENFORCED` anywhere** — it does not compile at 67.0. |
| `callout_endpoint` / **Q5** | `req.setEndpoint('callout:' + NAMED_CREDENTIAL)` with `NAMED_CREDENTIAL = 'OnCall_Tool'` and **no path appended** — M1-S02's `Url` parameter is already the full endpoint. No literal hostname, no `Authorization` or `X-API-Key` header set in Apex, no credential value read. The platform injects the `X-API-Key` from the External Credential's `AuthHeader` parameter. |

### A note on why the callout loop is legal

`Tier2WebhookQueueable.execute()` loops over Cases and calls `attemptOne(...)` per Case —
a real per-record callout loop. Two things bound it and both are deliberate:

- **`MAX_CASES_PER_JOB = 50`** against a ceiling of 100 callouts per transaction, with an
  explicit `setTimeout(20000)` against the 120 s cumulative budget. 50 is the worst single
  burst the requester described (Q22).
- The `new Http().send(req)` lives in `attemptOne`, not in the loop body — the same
  decomposition `templates/apex/HttpClient.cls` used before it was dropped, and the reason
  `check_callouts_and_http_integrations.py` rule 4 stays quiet. **The heuristic is quiet
  because the shape is right, not the other way round**; the bound above is what actually
  keeps the transaction legal.

**Method order inside `Tier2WebhookQueueable.cls` is deliberate and is documented in the
class header.** The callout path is declared before any method that performs DML, because
the checker reads a class body as one span and flags any DML token preceding the first
callout offset — which is the same fact as the runtime rule that a callout cannot follow
DML.

---

## 7. Governor budget, per invocation

| Class | SOQL | DML | Callouts | Notes |
|---|---|---|---|---|
| `CaseTriggerHandler.afterUpdate` | **0 or 1** | 0 | 0 | The `Group` query is skipped entirely when no `OwnerId` changed in the save. Cached for the transaction thereafter. |
| `Tier2EscalationService.escalate` | 0 | 1 publish + at most 1 insert + 1 enqueue | 0 | Reads only trigger-context records. The insert happens only when a publish is rejected. |
| `Tier2WebhookQueueable.execute` | 1 | ≤ 3 (stamp, insert, update) | **≤ 50** | One query for the slice; all DML after the last callout. |
| `Tier2WebhookFinalizer.execute` | 1 | ≤ 2 + 1 enqueue | 0 | Synchronous limits apply to a Finalizer transaction. |
| `IntegrationFailureTriggerHandler.afterUpdate` | 0 | 1 update + 1 enqueue | 0 | Reads only trigger-context records; parses the stored envelope in memory. |

At the requester's stated volume — 15 escalations a day, peaking at 2 an hour, worst burst
50 in five minutes (Q22) — no path approaches a limit. The 200-record bulk test exists to
prove the *shape* is bulk-safe, not because the volume demands it.

## 8. Test plan

19 test methods across 3 classes.

| Class | Covers | Deliberately not covered |
|---|---|---|
| `Tier2EscalationServiceTest` | escalation detection, 200-Case bulk with one enqueue, reassignment to a user, a save that does not touch owner, suppression inside and outside the window | — |
| `Tier2WebhookQueueableTest` | 200 stamps and writes nothing, 422 writes a `New` row with the status and payload, 401 names `Tier2_Webhook_Admin`, 503 at the last attempt lands `Abandoned`, job-side suppression, the full transient/permanent classification, key stability | the throw → Finalizer → retry branch (§ 5 item 3) |
| `IntegrationFailureResendTest` | resend to `Resent` with the Case stamped, stored-key replay, resend overriding a recent notification, the no-payload fallback, an orphaned row, and clearing the checkbox | — |

Every assertion carries a message saying what the behaviour is *for*. Expected coverage
on the six production classes is comfortably above the 85% bar; the uncovered branches are
the retry throw above, the `queueId` null path, and the two `originalEscalationTime`
fallback logs. **No coverage number is claimed: no test has been executed, because this
loop does not run tests against an org.**

---

## 9. Symbol grounding — every custom name, and where it came from

Checked mechanically this run against the upstream steps' artefacts, not from memory.

| Source | Symbols |
|---|---|
| From `artefacts/M1-S01/` | `Integration_Failure__c` and `Attempt_Count__c`, `Case__c`, `Case_Number__c`, `Endpoint__c`, `Error_Message__c`, `HTTP_Status__c`, `Last_Attempted_At__c`, `Request_Payload__c`, `Resend__c`, `Response_Body__c`, `Severity__c`, `Status__c` · `Case.Tier2_Notified_At__c` · `Tier2_Escalation__e` and `Case_Number__c`, `Case_Link__c`, `Escalated_At__c`, `Severity__c`, `Subject__c` |
| From `artefacts/M1-S02/` | `OnCall_Tool` (as `callout:OnCall_Tool`), `Tier2_Webhook_Admin` (named in the 401 message only, and now also the permission set name passed to `TestUserFactory.createUser`, run 4) |
| Standard objects and fields | `Case.Id/CaseNumber/Subject/Priority/Status/OwnerId`, `Group.Id/Name/DeveloperName/Type`, `QueueSObject.QueueId/SObjectType`, `User.Id`, `Profile.Id/Name` (queried inside `TestUserFactory`), `PermissionSet.Id/Name`, `PermissionSetAssignment.AssigneeId/PermissionSetId` |
| Shipped in this step | `CaseTriggerHandler`, `IntegrationFailureTriggerHandler`, `Tier2EscalationService`, `Tier2WebhookQueueable`, `Tier2WebhookFinalizer`, `TestDataFactory`, `MockHttpResponseGenerator`, `TestUserFactory` (added run 4) |

**Zero unresolved symbols**, and zero references to `ApplicationLogger`, `TriggerControl`,
`HttpClient`, `BaseService`, `SecurityUtils` or any other `templates/apex` class this build
does not ship.

**`PROFILE = 'Standard User'` (run 4) is a real, standard Salesforce profile name present
in every org — not a name this build invented — and is the same value
`skills/apex/test-class-standards/references/examples.md` Example 5 uses for this exact
class.** No clarification in this build names a profile for the users who can escalate a
Case (Q19 names three admins by role, not by profile), so this is the narrowest legal
default rather than a grounded fact; if the target org's escalating users hold a
different profile, `PROFILE` is the one line to change before UAT.

Every non-platform `Type.method(...)` in the emitted code was checked against a source this
run: `templates/apex/tests/TestDataFactory.cls` for `createCases`,
`templates/apex/tests/MockHttpResponseGenerator.cls` for `withResponse`,
`templates/apex/tests/TestUserFactory.cls` for `createUser(profileName, permissionSetNames)`
(added run 4),
`skills/apex/apex-queueable-patterns/references/examples.md` for `System.attachFinalizer`,
`ctx.getResult()`, `ParentJobResult.SUCCESS`, `ctx.getException()`,
`AsyncOptions.MaximumQueueableStackDepth` and `MinimumQueueableDelayInMinutes`,
`skills/apex/platform-events-apex/references/examples.md` for `EventBus.publish`,
`Database.SaveResult.isSuccess()`, `getErrors()` and `Database.Error.getMessage()`, and
`skills/apex/test-class-standards/references/code-examples.md` for the `Assert` methods and
the `startTest`-before-`setMock` ordering.

**One name was deleted rather than shipped.** `Database.Error` also exposes a status-code
accessor, but no file in this repo spells it, so `Tier2EscalationService.errorText()` uses
`getMessage()` alone — `AGENT_CONTRACT.md` rule 12: a plausible-sounding name that does not
compile is worse than none.

**And one attested name shipped anyway and did not compile.** `URL.getSalesforceBaseUrl()`
is spelled in three of this repo's skills, so the grep that backs this section returned a
hit and run 2 shipped it. It was removed after version 58.0 and these classes are pinned to
67.0. The check this section performs — *does the corpus spell this name?* — cannot answer
*is this name legal at this `apiVersion`?*, and the second question is the one that decides
whether the package deploys. Corrected in run 3; recorded in full at § 0, root 1.

---

## 10. Integration notes — what a human must do, and what no deploy performs

This agent modifies no existing file. Three things a human owns:

1. **Check for an existing `after update` trigger on `Case`.** This build ships
   `CaseTrigger`; an org that already has one cannot deploy a second with the same name,
   and two triggers on one object is the consolidation problem `/consolidate-triggers`
   exists for. Nothing in the 45 clarifications says whether the org has one.
2. **Assign `Tier2_Webhook_Admin`** to every user who can escalate a Case and to the user
   who schedules M1-S04's job (decision D14, assumption A13) — see M1-S02's
   `deploy-order.md` § 7.
3. **Enter the API key in Setup** against `OnCallToolNamedPrincipal`. Until that is done
   every callout returns 401 and every escalation lands in an `Integration_Failure__c` row
   whose message says so.

## 11. The manual acceptance test for the M1 gate

The step's `manual` test, tickable from these artefacts alone:

- **(a)** Open `Tier2EscalationService.cls`. The `EventBus.publish` call is in the service,
  in the escalating transaction, and its `List<Database.SaveResult>` is assigned and walked
  index-parallel with `escalatedCases`, with a rejection writing an `Integration_Failure__c`
  row. It is **not** discarded and **not** inside the Queueable. ✅ as written — lines
  around `List<Database.SaveResult> publishResults = EventBus.publish(events);`.
- **(b)** Open `Tier2WebhookQueueable.cls`. No class in this step sets an `X-API-Key` or
  `Authorization` header, reads a credential value, or names a literal hostname; the only
  endpoint expression in the step is `'callout:' + NAMED_CREDENTIAL` where
  `NAMED_CREDENTIAL = 'OnCall_Tool'`, with no path appended. ✅ as written. The headers the
  Apex does set are `Content-Type`, `Accept` and `Idempotency-Key`.

Add, for this run: **(c)** read § 4 and accept the missing kill switch, or ask for the
Apex-foundations step.

## 12. Validate-only command — for a human to run, never for an agent

```bash
python3 scripts/mock_deploy.py .sfskills/builds/tier2-webhook/plan.json \
  --org-alias <alias> --milestone M1
```

Run the M1-S01 objects request **before** anything here (M1-S01 `deploy-order.md` § 3).
This step has never been compiled; the dry run is the first thing that will compile it.
