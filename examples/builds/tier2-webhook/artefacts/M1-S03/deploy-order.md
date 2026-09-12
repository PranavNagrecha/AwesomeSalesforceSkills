# Deploy order — M1-S03 (escalation trigger, publish-and-enqueue service, webhook Queueable, Finalizer retry, resend path, tests)

Build `tier2-webhook` · step `M1-S03` · type `automation` · owner `apex-builder`
(run inline under `build-step-runner`) · API version **67.0** (assumption A11) ·
`build_mode: design-only` — **nothing here has been deployed, and neither agent deploys anything.**

This is the step's **third** run. Run 1 refused (`REFUSAL_INPUT_AMBIGUOUS`, envelope
`envelopes/M1-S03/2026-09-12T10-57-25Z.json`); the requester and the dry-run operator
answered with **remedy B** (`amendments[1]`, `2026-09-12T11:03:46Z`), and run 2 built to
that amended plan. Run 2 passed every checker and **failed the org**. § 0 is that record;
§ 4 is what the remedy-B amendment cost and what it bought.

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
| 13 | `deploy-order.md` (this file) | **no — undeclared** | named by `agents/apex-builder/AGENT.md` Output Contract item 2 as where template provenance is recorded |

**20 declared paths, all present; 5 undeclared files.** The undeclared five are a plan
gap this run could not close: the step's `templates[]` cites both template classes and
its `outputs[]` declares neither, and `check-outputs` only ever confirms paths the plan
declared. `amend-step` is the writer for that and it is refused once a step has left
`pending`, so the correction belongs to whoever re-plans. `check-outputs` passes on the
twenty regardless.

**No `package.xml`.** `apex-builder`'s Output Contract names none, and
`standards/build-orchestration.md` § 5 **The Apex exception** puts these twelve
`ApexClass` and two `ApexTrigger` members in the build-level manifest step **M1-S05**,
which `depends_on` this step.

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
| `TestDataFactory` (`createCases(count, accountId, overrides)` in all three test classes' `@TestSetup`) | `classes/TestDataFactory.cls` + `-meta.xml` | **empty — verified this run** |
| `MockHttpResponseGenerator` (`withResponse(status, body)` in every callout test) | `classes/MockHttpResponseGenerator.cls` + `-meta.xml` | **empty — verified this run** |

Both are self-contained: neither references another `templates/apex` class and neither
names a custom object or custom metadata type. That is the whole reason they survived
remedy B while three others did not (§ 4).

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
step contributes:

```text
ApexClass:   CaseTriggerHandler, IntegrationFailureTriggerHandler, Tier2EscalationService,
             Tier2WebhookQueueable, Tier2WebhookFinalizer, Tier2EscalationServiceTest,
             Tier2WebhookQueueableTest, IntegrationFailureResendTest,
             MockHttpResponseGenerator, TestDataFactory   ← also contributed by M1-S04
ApexTrigger: CaseTrigger, IntegrationFailureTrigger
```

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
| From `artefacts/M1-S02/` | `OnCall_Tool` (as `callout:OnCall_Tool`), `Tier2_Webhook_Admin` (named in the 401 message only) |
| Standard objects and fields | `Case.Id/CaseNumber/Subject/Priority/Status/OwnerId`, `Group.Id/Name/DeveloperName/Type`, `QueueSObject.QueueId/SObjectType`, `User.Id` |
| Shipped in this step | `CaseTriggerHandler`, `IntegrationFailureTriggerHandler`, `Tier2EscalationService`, `Tier2WebhookQueueable`, `Tier2WebhookFinalizer`, `TestDataFactory`, `MockHttpResponseGenerator` |

**Zero unresolved symbols**, and zero references to `ApplicationLogger`, `TriggerControl`,
`HttpClient`, `BaseService`, `SecurityUtils` or any other `templates/apex` class this build
does not ship.

Every non-platform `Type.method(...)` in the emitted code was checked against a source this
run: `templates/apex/tests/TestDataFactory.cls` for `createCases`,
`templates/apex/tests/MockHttpResponseGenerator.cls` for `withResponse`,
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
