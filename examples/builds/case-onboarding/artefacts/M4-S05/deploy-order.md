# Deploy order — M4-S05 (First Response milestone completion: trigger, service, test)

Written by `agents/apex-builder`, run inline by `agents/build-step-runner`. **Nothing in this
build deploys.** No `sf` command of any kind was run, no org was contacted, and no Apex test
was executed.

**Note on declaration:** this file is *not* in `plan.json` `steps[M4-S05].outputs[]` — six paths
are declared and this is not one of them. It is written anyway because the human's deploy reads
it, following the same undeclared-`deploy-order.md` pattern `decisions.md` **O-M3S02-03** records
for M3-S01…M3-S04 and `artefacts/M4-S02/deploy-order.md` records for M4-S02. It is reported in
this run's envelope as an undeclared artefact rather than left for a reader to notice. If the
build wants it declared, the writer is
`python3 scripts/build_plan.py amend-step <plan> M4-S05 --file <amendment.json> --by <who>
--reason "<why>"` — this agent does not run it.

---

## 0. Rebuild record — F-37: the org rejected the test class

This step was first built at run `2026-09-12T08-12-19Z`, tested clean, and then **failed the
operator's dry-run validation**. It was reset `tested → failed → pending`, its `outputs[]` were
amended, and it was rebuilt at run `2026-09-12T08-32-00Z`. This section is that record.

**The org error** (`reports/MOCK-DEPLOY-M4.md` run 2 — `checkOnly`, org `sfskills-dev`, API 67.0):

```text
ApexClass CaseMilestoneServiceTest  (x5)   Variable does not exist: TestDataFactory
```

`CaseMilestoneTrigger` and `CaseMilestoneService` compiled. Only the test class failed, five
times — once per `TestDataFactory` reference.

**Why the first build was wrong, and why no local check caught it.** The test calls
`TestDataFactory.createAccounts(...)` and `TestDataFactory.createCases(...)`, which this step's
`templates[]` names and which `skills/apex/entitlement-apex-hooks/references/code-examples.md`
lists under "Referenced by relative path, not copied into this bundle". But
`templates/README.md` is explicit that a template is a **canonical building block copied into the
consuming project** — a repo-relative path is a citation for a human, not a deploy-time
reference an org can resolve. No step in this plan shipped the class, so
`CaseMilestoneServiceTest` compiled only in an org that already happened to have one. Nothing
local could have caught it: `check_entitlement_apex_hooks.py` reads one tree for `CaseMilestone`
mistakes and has no cross-class symbol resolution, `check-outputs` confirms declared paths rather
than references, and there is no offline Apex compiler in the `sf` CLI. It took a real org.

**What changed in the rebuild.** Exactly two files were added, and nothing else was edited:

| File | Provenance |
|---|---|
| `classes/TestDataFactory.cls` | **byte-identical copy** of `templates/apex/tests/TestDataFactory.cls` (`diff` is empty). The template itself was not modified. |
| `classes/TestDataFactory.cls-meta.xml` | `ApexClass`, `<apiVersion>67.0</apiVersion>`, `<status>Active</status>` — the same shape as the other three, from `templates/apex/TriggerHandler.cls-meta.xml`. |

`CaseMilestoneTrigger.trigger`, `CaseMilestoneService.cls`, `CaseMilestoneServiceTest.cls` and
their three `-meta.xml` files are **unchanged, byte for byte**. The factory copy changed no
reference: the class name the test already called is the class name now shipped beside it, so
there was nothing in the test to update.

**The factory was copied, not adapted.** The test needs `createAccounts(Integer, Map<String,
Object>)` and `createCases(Integer, Id, Map<String, Object>)`, and the template already has both
with those exact signatures. **No behaviour was added to the factory.** The one thing this
build's Cases need beyond the factory's defaults — `Origin` and `Priority` that survive M3-S01's
two active validation rules — is supplied by the **test**, through the factory's own `overrides`
map, in `CaseMilestoneServiceTest.caseOverrides(Id)`. That is the right side of the line: the
factory's defaults are shared across every consumer, and this build's validation rules are not.
See § 4 item 4.

**One consequence for the plan, carried to the M4 gate.** `classes/TestDataFactory.cls` is now a
**step-local** copy of a shared template. This is the only Apex step in the plan, so nothing
duplicates today — but a second Apex step declaring the same output would deploy the same class
twice under one `package.xml` member, which is a deploy conflict rather than a merge. The fix is
not to copy it again: **planner v6 should own a shared "Apex foundations" step** whose `outputs[]`
carry `TestDataFactory` (and, if the handler shape is ever adopted, `TriggerHandler`,
`TriggerControl` and `Trigger_Setting__mdt` — § 2), with every Apex step depending on it.
`reports/MOCK-DEPLOY-M4.md` F-37 records the same remedy.

---

## 1. What this step wrote, and the order it deploys in

| # | Component | File | Depends on |
|---|---|---|---|
| 1 | Setup (manual) | entitlement process with the `First Response` milestone, active, and Cases entering it | — |
| 2 | `ApexClass` | `classes/TestDataFactory.cls` (+ `-meta.xml`) — `@IsTest`, verbatim from the template | — |
| 3 | `ApexClass` | `classes/CaseMilestoneService.cls` (+ `-meta.xml`) | — |
| 4 | `ApexTrigger` | `triggers/CaseMilestoneTrigger.trigger` (+ `-meta.xml`) | 3 |
| 5 | `ApexClass` | `classes/CaseMilestoneServiceTest.cls` (+ `-meta.xml`) | 1, 2, 3, 4 |

Metadata deploys resolve within a single request, so a one-shot deploy of all four classes works;
the order above is what you need when they land in separate requests. **Step 2 is not optional** —
omitting it is exactly F-37 (§ 0).

Step 1 is genuinely first. The classes deploy without it, but every assertion that matters is
unreachable until an entitlement process exists and Cases are entering it — and the test is
written to fail loudly rather than pass vacuously when it is missing (§ 4).

All four `-meta.xml` files carry `<apiVersion>67.0</apiVersion>` and `<status>Active</status>`. The
`ApexClass` shape is copied verbatim from `templates/apex/TriggerHandler.cls-meta.xml`; the
`ApexTrigger` shape from `skills/apex/apex-design-patterns/references/code-examples.md` line 781.
`Inactive` is a valid `status` for `ApexTrigger` but **not** for `ApexClass` — writing it into a
`.cls-meta.xml` is a deploy error, not a disabled class.

**The `apiVersion` is load-bearing.** Per `agents/_shared/AGENT_CONTRACT.md` § *Apex security
idiom by API version*, at 67.0 SOQL, SOSL, DML and `Database` methods run in **user mode by
default**, and `WITH SECURITY_ENFORCED` **does not compile** — it was removed at 67.0. The one
query in this step therefore carries `WITH USER_MODE` (redundant at this version, but it states
the intent at the call site where a future version downgrade would otherwise change behaviour
silently) and `WITH SECURITY_ENFORCED` appears nowhere.

`package.xml` is deliberately **not** written here — see § 6.

---

## 2. Why there is no `CaseMilestoneTriggerHandler`, and what that costs

`skills/apex/entitlement-apex-hooks/references/code-examples.md` ships a **four-file** bundle:
service, trigger, test, **and** `CaseMilestoneTriggerHandler.cls`, a subclass of
`templates/apex/TriggerHandler.cls`. `skills/apex/apex-design-patterns` names the same shape —
"for triggers the adapter is one line — `new CaseTriggerHandler().run();`". This step wrote the
**two-file** shape instead (trigger calls the service directly), which is the shape
`skills/apex/entitlement-apex-hooks/references/examples.md` Example 1 documents.

Two facts settled it, and neither is a judgement about which pattern is better:

1. **`plan.json` `steps[M4-S05].outputs[]` declares three components, and a handler is not one of
   them.** `standards/build-orchestration.md` § 4 borrowed-agent condition 2 forbids declaring an
   output the owning agent's contract does not name; the converse — writing a component the plan
   does not declare — is an undeclared artefact `check-outputs` never confirms and the milestone
   manifest never carries.
2. **No step in this build deploys the base classes the handler needs.** `TriggerHandler.run()`
   calls `TriggerControl.isActive(...)` on its first line, and `TriggerControl` reads
   `Trigger_Setting__mdt`. A search of `plan.json` for `TriggerControl`, `ApplicationLogger` and
   `Trigger_Setting__mdt` returns **zero** occurrences in any step's `outputs[]`; `TriggerHandler`
   appears exactly once, in this step's `templates[]`, which is an instruction to *read* the file,
   not to deploy it. A handler extending `TriggerHandler` would not compile in the org this build
   produces.

**What the two-file shape costs, stated plainly for the gate:** no recursion guard, no depth
counter, no `skipOnce()`, and no `TriggerControl` kill switch. The idempotency guard that matters
in *this* domain is still present and is the stronger of the two — `CompletionDate = NULL` in the
query means a second pass finds nothing to stamp (§ 5, and the test method
`skipsAMilestoneThatIsAlreadyCompleted`). What is genuinely absent is the ability to disable this
trigger from Setup without a deploy.

**The remedy, if the build wants the handler shape:** it is a plan amendment, not a code tweak —
add `classes/CaseMilestoneTriggerHandler.cls` (+ `-meta.xml`) to this step's `outputs[]` **and**
add the three template components to some step's outputs, then rebuild this step. Carried to the
M4 gate as an open item.

---

## 3. The completion signal is a proxy, and Q50's answer named a different one — UNVERIFIED

`D10` settled the **mechanism**: an after-update Apex trigger on Case that stamps
`CaseMilestone.CompletionDate`. Nothing in the plan settles the **event** — the Case change that
means "the agent has responded".

- `Q50`'s recorded answer names *"satisfiable completion criteria on the first outbound
  EmailMessage, or a Flow that stamps CompletionDate"*. The first outbound `EmailMessage` is the
  signal that answer has in mind.
- `Q16`'s answer says what happens in the first minute (owner, acknowledgement, calendar,
  priority) — an **auto**-acknowledgement, which is not an agent's first response.
- No clarification anywhere in the Q38–Q53 SLA group names a Case field change as the signal.

**What this step implemented, and why:** the milestone completes when a Case **leaves Status
`New`**. That is the transition `references/examples.md` Example 1 documents ("cases that just
left 'New' status"), and it is the one transition both of this build's business processes share —
`artefacts/M1-S01/objects/Case/businessProcesses/` gives `New → Escalated → Closed` on
`Support_Process` and `New → Closed` on `Billing_Process`.

**This is a proxy, not the requirement.** A case can leave `New` without a customer-facing reply
(an agent triaging and escalating), and an agent can reply without leaving `New`. If the business
means the first outbound email, that is a **different artefact** — an after-insert trigger on
`EmailMessage` filtered to `Incoming = false` — which this step's `outputs[]` do not declare and
this step did not write.

**Carried to the M4 gate as an open item.** Either the gate accepts "leaves `New`" as the signal,
or Q50 is re-answered and a new step is planned. Nothing here is silently broken; the service
holds the rule in one named constant (`OPENING_STATUS`, `@TestVisible`), so a change is one line.

**Not implemented, deliberately:** `COMPLETING_STATUSES = {'Working', 'Escalated', 'Closed'}` from
`code-examples.md`. `Working` is not in either of this build's business processes, so two thirds
of that set would never match and the third (`Closed`) would complete the first-response milestone
only at case closure.

---

## 4. What the test needs from the org, and what it does not prove

`CaseMilestoneServiceTest` is `@IsTest(SeeAllData=true)`. That is forced, not chosen:

| Object | Can a test create it? |
|---|---|
| `MilestoneType` | yes |
| `Entitlement` | yes |
| `SlaProcess` | **no — there is no `create()` call** |
| `CaseMilestone` | **no — there is no `create()` call** |

The chain breaks in two places: the test can create the `Entitlement` and the `MilestoneType`, but
not the `SlaProcess` that joins them, and not the `CaseMilestone` rows that are the thing under
test. Both must come from the org. Two constraints follow: this class cannot also be
`@IsTest(IsParallel=true)` (the annotations cannot be combined), and it reads the org's real data,
so an admin deactivating the entitlement process breaks it.

**Prerequisites the target org must satisfy before these tests prove anything:**

1. An **active** `SlaProcess`. `requireActiveProcess()` asserts on it with a message naming what is
   missing, rather than returning early — a skipped test here is indistinguishable from a passing
   one.
2. That process must include a milestone whose `MilestoneType.Name` is exactly **`First Response`**
   — the name written at `artefacts/M4-S02/milestoneTypes/First Response.milestoneType-meta.xml`.
   A Setup rename returns zero rows, which is not an exception: the automation silently stops.
3. `Status = 'Closed'` must be reachable for the running user's default Case record type. `Closed`
   was chosen over `Escalated` precisely because both of this build's business processes expose it.
4. `Origin = 'Web'` and `Priority = 'Medium'` are set on every Case the test builds, because
   M3-S01's two active validation rules (`Origin_Must_Be_Known`, `Priority_Required_On_Agent_Save`)
   reject the `TestDataFactory` defaults — the factory ships `Origin = 'Email'`, which is not one
   of the three values this build's `CaseOrigin` standard value set defines.

**`requireActiveProcess()` takes `LIMIT 1` over *any* active process**, not necessarily
`First_Response_Premier` or `First_Response_Standard`. If the org has an unrelated active process,
the run fails on the milestone assertion in `triggerWritesCompletionDateOnAnOpenMilestone` with a
message saying so. That is a loud failure rather than a wrong pass, but it is a sharper filter the
skill does not document and this step did not invent one.

**What the four methods prove:**

| Method | Proves | Needs the entitlement process? |
|---|---|---|
| `triggerWritesCompletionDateOnAnOpenMilestone` | a **real `update` on Case runs the trigger** and `CompletionDate` reads back non-null | yes |
| `skipsAMilestoneThatIsAlreadyCompleted` | the `CompletionDate = NULL` idempotency guard makes a second identical pass a no-op | yes |
| `staysAtOneQueryAndOneDmlFor200Cases` | 200 Cases cost exactly one SOQL and at most one DML | yes |
| `ignoresCasesWhoseStatusDidNotChange` | an unchanged Status never reaches the query | **no** |

The fourth method is the only one that still runs in a bare scratch org, and it covers the
early-return path most production traffic actually takes. Only the first method exercises
`CaseMilestoneTrigger` itself; the other three call the service directly so the governor counters
are deterministic.

**Assertions, not coverage.** ≥75% is a deployability floor, not evidence a test asserts anything.
Every method above asserts on a value. The trigger is a one-line adapter covered only by method 1,
so an org missing the entitlement process deploys this bundle with the trigger at 0% coverage —
another reason § 1 step 1 is first.

**No compile check ran.** There is no offline Apex compiler in the `sf` CLI: the *apex Commands*
group retrieves logs, runs tests, and executes anonymous blocks, and only `sf apex run --file`
reads a local file — which it *executes* against a required `--target-org`. This build is
`design-only` with no org on file. Per `agents/apex-builder/GATES.md` Gate D this caps the run's
confidence at MEDIUM and is stated here rather than implied.

---

## 5. UNVERIFIED items carried forward from the skills

These are the skills' own markers, restated beside the code they affect rather than left in a
reference file. None was resolved by this step and none was guessed at.

| # | Claim | Status |
|---|---|---|
| 1 | That writing a non-null `CompletionDate` is what makes `IsCompleted` read back as `true` | **UNVERIFIED** (`gotchas.md` 1, `code-examples.md`). What is grounded is the asymmetry: `CompletionDate` and `StartDate` carry the `Update` property and `IsCompleted` does not. The test asserts on `CompletionDate != null`, never on `IsCompleted`. |
| 2 | The 3-argument `Database.update(records, allOrNone, AccessLevel)` overload | **UNVERIFIED** — no such call appears in the Apex Developer Guide extract. The service uses the **two-argument** form and relies on 67.0's default user mode, so it does not depend on the claim. |
| 3 | `Assert` message-carrying overloads, `Limits.getDmlStatements()` | **UNVERIFIED** — used by the test but absent from the corpus extract. If a compile fails on a message overload, drop the message argument: the assertion still holds, the diagnostic is lost. |
| 4 | That the platform sets `IsViolated` by background calculation rather than DML | **UNVERIFIED** (`gotchas.md` 9). Out of scope here — this step builds completion only. Violation polling (`MilestoneViolationScheduler`) is `Schedulable`, which **D8 rules out for this phase**. |
| 5 | That `MilestoneType.Name` SOQL comparison is case-**sensitive** | **UNVERIFIED** (`gotchas.md` 11) and more likely wrong than right. Exact casing is kept as hygiene, not as a diagnosis. |
| 6 | The `MilestoneUtils` helper class that circulates in community posts | **Does not appear** in the Apex Developer Guide or Apex Reference Guide extracts. Not used. |

Two things the code does **not** do, both compile-time facts rather than preferences:
`SlaExitDate` is not a `CaseMilestone` field at all (it belongs to `WorkOrder`), and `TargetDate`
carries `Filter` only — milestone deadlines are not adjustable from Apex. Neither appears in any
file this step wrote.

---

## 6. What this step does NOT write, and who does

| Not written here | Who owns it |
|---|---|
| `package.xml` | **M5-S05** (`type: docs`, `metadata-builder`, `depends_on` this step) aggregates the `ApexClass` members `CaseMilestoneService`, `CaseMilestoneServiceTest` and the `ApexTrigger` member `CaseMilestoneTrigger`. `standards/build-orchestration.md` § 5 *The Apex exception* settles it: `agents/apex-builder`'s Output Contract names no manifest, so § 4 borrowed-agent condition 2 forbids declaring one here. |
| `settings/Entitlement.settings-meta.xml` | Nobody — see `decisions.md` **O-M4S02-01**, carried to the M4 gate. |
| `TriggerHandler` / `TriggerControl` / `ApplicationLogger` / `Trigger_Setting__mdt` | Nobody in this build — see § 2. |
| A shared home for `TestDataFactory` | Nobody yet. This step ships a step-local copy (§ 0); a second Apex step would duplicate the class, so **planner v6 should own a shared "Apex foundations" step**. |
| Violation polling | Nobody — **D8** rules `Schedulable` out for this phase. |

**`ApplicationLogger` was deliberately not wired in.** `code-examples.md` names it as the canonical
destination for partial-success failures, and it carries dependencies (`Application_Log__c`,
`Logger_Setting__mdt`) that nothing in this build deploys, so the service would not compile. The
same file documents the fallback taken here, option 2: `System.debug(LoggingLevel.ERROR, …)`, with
the trade-off recorded rather than hidden — **a partial-success failure is visible only in a debug
log somebody happens to be capturing at the time.** The `for (Database.Error err : …)` loop is
intact; dropping it is what makes partial-success DML worse than all-or-nothing DML, because the
failures then vanish with no exception raised. If this org gains `ApplicationLogger`, replace the
two `System.debug` calls and nothing else.

---

## 7. Verification — the declared acceptance test, run verbatim from the build directory

`plan.json` `steps[M4-S05].acceptance_tests[0]`:

```text
$ python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py \
    --manifest-dir artefacts/M4-S05
scanned 4 Apex file(s) under artefacts/M4-S05: 0 ERROR, 0 WARN
EXIT=0
```

Four files, not three: the rebuild's `classes/TestDataFactory.cls` is scanned with the rest and
clears every rule. It contains no `CaseMilestone` reference at all, so the domain rules are inert
on it; `EAH001` is the one that could have fired, and the `for (Account a : accounts)` loop in
`bulkInsertStandardSet` holds no SOQL and no DML — both `insert` statements sit outside it.

`--strict` is **not** declared on this test; run anyway for information, it is also `EXIT=0`
(0 ERROR, 0 WARN), so no WARN is being carried silently under the non-strict exit code.

The eight rules that cleared: `EAH001` (no SOQL or DML inside any loop), `EAH002` (no assignment
to `IsCompleted`, `IsViolated` or `TargetDate`), `EAH003` (no `SlaExitDate`), `EAH004` (no
`insert`/`delete`/`upsert` on a `CaseMilestone` variable), `EAH005` (no `WITH SECURITY_ENFORCED`,
which at `apiVersion` 67.0 would be an **ERROR**, not a style note), `EAH006` (every
`CaseMilestone` query either filters `CompletionDate = NULL` or is pinned to Ids already held),
`EAH007` (no numeric comparison against the `text` fields `TimeRemainingInMins` /
`TimeRemainingInHrs`), `EAH008` (the trigger is `after update` on `Case`, not a before-trigger and
not a trigger on `CaseMilestone`).

Structural checks run alongside it: all four `-meta.xml` files parse with `ElementTree`, and
braces, parentheses and brackets balance in all four Apex files with comments and string literals
stripped. `diff templates/apex/tests/TestDataFactory.cls artefacts/M4-S05/classes/TestDataFactory.cls`
is empty, which is the check that the copy is verbatim.

**Org-side verification, after a real deploy** — a debug log, not a field check. Set a debug log on
the case owner with the **Workflow** category at **INFO** and push a Case through the intake
channel. Four entitlement-engine events are documented at that level: `SLA_PROCESS_CASE` (the
engine looked at this Case), `SLA_EVAL_MILESTONE` (a milestone was evaluated),
`SLA_NULL_START_DATE` (the Case never entered a process) and `SLA_END` (what the engine did,
including how many case milestones it inserted, updated or deleted). Absence of all four means the
engine never ran, which is an entitlement-on-the-Case problem and not a problem with any code in
this step.

---

## 8. Test-only repair — F-59: the tests never ran as a permissioned user

This step was `documented`, the operator moved it `documented -> running` for a **section 4
test-only repair of a documented step in a build whose gates are all approved**, and this section
is that record. `CaseMilestoneService.cls` and `CaseMilestoneTrigger.trigger` are unchanged, byte
for byte. Only `CaseMilestoneServiceTest.cls` gained a permissioned running context, and
`TestUserFactory.cls` + `TestDataFactory.cls` are new/refreshed alongside it.

**Trigger:** `reports/MOCK-DEPLOY-M5.md` run 4 — MANIFEST mode, every built step,
`--test-level RunSpecifiedTests --tests CaseMilestoneServiceTest` (API 67.0), the first run in this
build with Apex actually executing rather than only compiling. The operator's probe on a scratch
copy with the one unrelated F-28 component removed: 59/59 components ok, tests run 1, passed 0,
failed 3, coverage 36.4%. All three methods of `CaseMilestoneServiceTest` failed at their Case
insert with `System.DmlException: Operation failed due to fields being inaccessible on Sobject
Case` (`caseInsideProcess` line 103; `staysAtOneQueryAndOneDmlFor200Cases` line 193, against the
pre-repair line numbering).

**F-59 (HIGH).** The same pair of defects the `tier2-webhook` build hit first (S2-F-11, S2-F-12;
`skills/apex/test-class-standards/references/gotchas.md` Gotchas 13 and 14,
`references/examples.md` Example 5): (1) no test method ran inside a permissioned
`System.runAs`, so every method ran as the deploying user, whose profile carries no field
permissions for anything this deployment ships; and (2) the step's `TestDataFactory.cls` copy
predated commit `5edcb3281` and unconditionally assigned a possibly-null `accountId` into the
`Case`/`Contact`/`Opportunity` constructor, which user-mode DML at the apiVersion 67.0 default
counts as a populated field regardless of the value. Every earlier dry run of this build compiled
the Apex and executed no test (`runTestsEnabled: false`), so the G4 (M4 milestone) and G5 (M5
gate, pending) records rested on compile-only evidence for this step.

**Permission-set choice, and why.** The repair mints the running user with
`templates/apex/tests/TestUserFactory.cls` holding **`Case_Agent_Core` + `Case_Tier1`** — the
exact member list `artefacts/M2-S02/permissionsetgroups/PSG_Tier1_Prod.permissionsetgroup-meta.xml`
declares for "the 12 Tier 1 agents" — and Profile **`Acme Support Tier 1`**
(`artefacts/M2-S03/profiles/Acme Support Tier 1.profile-meta.xml`, whose own description says "All
object/field/tab access comes from PSG_Tier1_Prod"). This is the closest thing this build has to
"a Tier 1 agent working a case," which is what the trigger under test exists to serve — a Case
leaving `New` on an agent's save. The two other production personas were considered and rejected:

- `Case_Tier2` grants an identical footprint to `Case_Tier1` by design (`artefacts/M2-S02/
  deploy-order.md`: "`Case_Tier1` and `Case_Tier2` carry identical grants... the requirement
  separates the two teams by routing and by escalation concerns, not by access") — Tier 1 is the
  narrower, more literal reading of "a Tier 1 agent."
- `Case_Billing` withholds the `Support` record type entirely (`recordTypeVisibilities` names only
  `Case.Billing`) and this test's Cases are not scoped to a record type at all, so a Billing user
  is not the right stand-in.
- `Case_Intake_Integration` (`artefacts/M2-S01/permissionsets/`) is the integration-user persona
  that creates Cases on inbound intake, not the agent persona that works them after creation — the
  wrong side of the M1-S03 → M4-S05 handoff for this trigger.

`Case_Agent_Core` alone was not sufficient to name: it is the base grant every Case-working persona
composes with (`artefacts/M2-S02/deploy-order.md`: "composed into `PSG_Tier1_Prod`, `PSG_Tier2_Prod`
and `PSG_Billing_Prod`"), and `TestUserFactory.createUser` assigns `PermissionSet`s by name, not
`PermissionSetGroup`s, so the two member sets are named directly rather than the group.

**What Case_Agent_Core does and does not grant, and why the fixture is split accordingly.**
`Case_Agent_Core` grants Create + Edit + Read on `Case`, and **Read only** on `Account`,
`Contact` and `Entitlement` — never Create. `caseInsideProcess` (via `entitlementFor`) creates an
`Account` and an `Entitlement`; a real Tier 1 agent could not do that, and this repair does not
pretend one does. Those two inserts stay exactly where they were, running as whichever user the
test itself runs as — unchanged from before this repair. Only the `Case` insert (the one object
the permission set grants Create on), the Case status change that fires the trigger, and every
`CaseMilestoneService` call and its surrounding assertions now run inside `System.runAs` of the
minted agent. This is also why `mintAgent()` is called and the agent is threaded into
`caseInsideProcess` as a parameter rather than the whole helper running inside one outer
`System.runAs` — the Account/Entitlement half of that helper would fail FLS if it did.

**Fixed:**

1. `classes/TestUserFactory.cls` (+ `-meta.xml`, apiVersion 67.0, Active) **added**, a verbatim
   copy of `templates/apex/tests/TestUserFactory.cls` — `diff` empty, verified this run. This is
   now a fifth undeclared-but-shipped file alongside the four the plan already tracks (§ 0, § 1).
2. `classes/TestDataFactory.cls` **replaced** with a verbatim copy of the corrected template
   (commit `5edcb3281`) — `diff` empty. The only behavioural change in the factory itself is the
   pre-existing guard the template now carries: a lookup argument (`accountId`) is assigned to the
   record only when non-null, everywhere the factory takes one. No test method in this class ever
   passed a null `accountId` to `createCases`, so this replacement is hygiene against the same
   class of defect recurring, not a fix for a defect this specific test hit — the failing field
   was never isolated by name (no `e.getDmlFieldNames(0)` probe was run; the operator's probe
   named only "Case" and the failing line), and the operator's own S2-F-11/S2-F-12 pairing named
   both defects together without attributing this build's failure to one exclusively.
3. `classes/CaseMilestoneServiceTest.cls` — added `AGENT_PROFILE`, `AGENT_PERMISSION_SETS` and
   `mintAgent()` (the mixed-DML fence: `TestUserFactory.createUser`'s `User` and
   `PermissionSetAssignment` inserts are setup-object DML, fenced inside a `System.runAs`
   re-entering the current user so they never share a transaction with the `Account` /
   `Entitlement` / `Case` DML elsewhere in the class — `skills/apex/mixed-dml-and-setup-objects`).
   `caseInsideProcess` gained a `User agent` parameter and wraps only its `insert cases;` in
   `System.runAs(agent)`. Every one of the four `@IsTest` methods now calls `mintAgent()` and runs
   its action and assertions inside `System.runAs(agent)`. **No assertion, message string, or
   `Test.startTest`/`Test.stopTest` boundary was added, removed, or changed** — every `Assert.*`
   call is byte-identical to the pre-repair version, only re-indented one level for the enclosing
   block.

**Checked this run:**

```text
$ python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py \
    --manifest-dir artefacts/M4-S05 --strict
scanned 5 Apex file(s) under artefacts/M4-S05: 0 ERROR, 0 WARN

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py \
    --manifest-dir artefacts/M4-S05/classes --strict
Scanned 4 Apex class file(s); audited 3 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
{"score": 100, "findings": []}
```

`user-mode-test-without-runas: 0` — the rule this repair exists to close fires zero times.
`check-outputs` is `ok` on all 8 declared paths — none changed path, only content on one
(`CaseMilestoneServiceTest.cls`) and full replacement on another (`TestDataFactory.cls`).
`diff templates/apex/tests/TestUserFactory.cls artefacts/M4-S05/classes/TestUserFactory.cls` and
`diff templates/apex/tests/TestDataFactory.cls artefacts/M4-S05/classes/TestDataFactory.cls` are
both empty. All 5 `.cls`/`.trigger` files still balance braces/parens/brackets and all 5
`-meta.xml` files still parse with `ElementTree`.

**A checker-parsing hazard found and worked around, not a code defect.**
`check_test_class_standards.py`'s `strip_literals` blanks single-quoted spans but does not
understand comments (its own docstring: "comments preserved") — it scans the whole file
left-to-right pairing every `'` character as if each one opened or closed a string. A stray
apostrophe in prose (a possessive or contraction) inside a comment shifts that pairing for
everything after it, and once shifted, real code between two later, unrelated string literals gets
misread as one giant blanked string — which silently deleted every `System.runAs(agent)` call in
this class from the checker's view on the first two attempts at this repair, reporting
`user-mode-test-without-runas` as still failing even after the fix landed in the code. Three
pre-existing possessive apostrophes in this class's own comments (unrelated to this repair) were
the cause; they are rephrased above without changing what they say. No apostrophe survives in any
comment this repair touched. This is recorded here rather than filed as a skill defect because
fixing `strip_literals` to understand comments is `test-class-standards`' concern, not this step's
scope — flagged as a follow-up for `build-doc-keeper` to carry forward.

**Not part of this repair, and not touched:** `CaseMilestoneService.cls`,
`CaseMilestoneTrigger.trigger`, and every `-meta.xml` other than `TestUserFactory.cls-meta.xml`
(new). The task scoping this repair is explicit that the step's non-test classes are correct and
must not change, and F-59 does not implicate them — `CaseMilestoneService`'s own `WITH USER_MODE`
query is what made the running user's permissions matter in the first place.

**Obligation on `M5-S05`, not discharged here.** Per `standards/build-orchestration.md` § 5 *The
Apex exception*, this step declares no `package.xml`; `M5-S05` (`type: docs`, `metadata-builder`,
`depends_on` this step) aggregates this step's `ApexClass`/`ApexTrigger` members into the
build-level manifest, and it currently carries four Apex members from before this repair
(`CaseMilestoneService`, `CaseMilestoneServiceTest`, `TestDataFactory`, and the `ApexTrigger`
member `CaseMilestoneTrigger` — `artefacts/M5-S05/deploy-order.md` § 1). **`TestUserFactory` is a
new `ApexClass` member `M5-S05` must add before its manifest is accurate again** — the same
obligation `TestUserFactory` created for `M1-S05` in the `tier2-webhook` build
(`.sfskills/builds/tier2-webhook/artefacts/M1-S03/deploy-order.md` § 0b). This step does not edit
`M5-S05`'s files itself — per § 4 borrowed-agent condition 2 and this step's own Output Contract,
that is `M5-S05`'s to carry, not this step's to write. Carried to whichever human or agent next
runs `M5-S05` (or to `decisions.md`, via `build-doc-keeper`), not silently worked around.

**Consequence for the milestone/build gates.** `milestone:M4` was accepted on evidence that
predates this finding (every dry run before run 4 carried `runTestsEnabled: false` — same shape as
S2-F-06 in `tier2-webhook`). This step returns to `built` once this record is written; `step-tester`
and `build-doc-keeper` are the next commands, and the M4 acceptance and the pending M5/G5 decision
both need re-signing against a dry run that actually executes `CaseMilestoneServiceTest` and passes
— run 5 of `reports/MOCK-DEPLOY-M5.md`, once `M5-S05`'s manifest carries `TestUserFactory`.

---

## 9. Second test-only repair — F-60: the fixture insert itself failed FLS as the persona

This step was `built`, the operator's probe (`reports/MOCK-DEPLOY-M5.md` run 5) found the § 8
repair itself incomplete, and it was reset `built → failed → pending → running` for a second
**section 4 test-only repair of a documented step in a build whose gates are all approved**. This
section is that record. `CaseMilestoneService.cls` and `CaseMilestoneTrigger.trigger` remain
unchanged, byte for byte, exactly as in § 8. Only `CaseMilestoneServiceTest.cls` changes again, and
`TestDataFactory.cls` is refreshed to the current template.

**Trigger:** `reports/MOCK-DEPLOY-M5.md` run 5 — SOURCE mode, whole build minus the F-28 rule, after
the § 8 repair, `--tests CaseMilestoneServiceTest` (API 67.0).

**F-60 (HIGH, design — the most consequential finding of this build).** `Case_Agent_Core` grants
Create on `Case` with field permissions on exactly one field (`Severity__c`); `Case_Tier1` adds
none; the shipped profile carries no field or object permissions at all ("all access comes from the
group," by design). The § 8 repair wrapped the fixture `Case` insert itself in
`System.runAs(agent)` — that insert populates `Subject`, `Origin`, `AccountId`, `Priority` and
`EntitlementId`, none of which the Tier 1 persona's permission sets grant Edit on, so the org
rejected it with the same `fields being inaccessible on Sobject Case` error § 8 was written to fix,
now on the fixture rather than the deploying user. § 8's own permission-set analysis named exactly
this shape for `Account`/`Entitlement` (Read only, never Create — see § 8 "What `Case_Agent_Core`
does and does not grant") but did not carry the same reasoning to `Case`'s own *field* grants,
because `Case_Agent_Core` does grant object-level Create on `Case` — the gap was between object
access and field access on the one object the persona can create at all.

**The library gap this exposed, and the fix that does not widen the persona.** Neither
`skills/apex/test-class-standards` nor `admin/permission-sets-vs-profiles` distinguished, before
today, "fields the persona's own code path writes" from "fields a fixture needs populated for the
test to be meaningful" — conflating the two forces a false choice: widen the persona to fields its
layouts and processes never ask it to write (reintroducing the mirror-image defect
`admin/permission-sets-vs-profiles` warns against), or leave the fixture unable to seed at all.
`skills/apex/test-class-standards/references/gotchas.md` **Gotcha 15** ("Seed In System Mode, Act
As The Persona") now names the third option, and this repair takes it: seed the fixture in system
mode, and keep `System.runAs(persona)` scoped to the action under test.

**Fixed:**

1. `classes/TestDataFactory.cls` **refreshed** to a verbatim copy of the current template (commit
   `be09a7bff`) — `diff` empty. The template's only change since the § 8 copy (commit `5edcb3281`)
   is the addition of `insertAsSystem(List<SObject>)`, a thin wrapper over
   `Database.insert(records, AccessLevel.SYSTEM_MODE)` that Gotcha 15 names as the call site every
   fixture-only seed should read as intent through, rather than as a bare `AccessLevel` incantation
   at each call site.
2. `classes/CaseMilestoneServiceTest.cls`:
   - `entitlementFor` — the `Account` and `Entitlement` inserts move from a plain ambient `insert`
     to `TestDataFactory.insertAsSystem(...)`, stating explicitly in code what § 8 already
     documented in prose (the persona holds Read only on both, never Create).
   - `caseInsideProcess` — loses its `User agent` parameter entirely. The fixture `Case` insert (the
     one § 8 wrapped in `System.runAs(agent)`) is now `TestDataFactory.insertAsSystem(cases)`,
     seeded outside any persona context; the persona acts on the `Case` only afterward, in the
     calling test method.
   - `staysAtOneQueryAndOneDmlFor200Cases` and `ignoresCasesWhoseStatusDidNotChange` — both build
     their own `Case` fixtures directly (not through `caseInsideProcess`) and both had their `insert
     cases;` line inside `System.runAs(agent)`; both now seed via `TestDataFactory.insertAsSystem(
     cases)` before entering the `runAs` block. `ignoresCasesWhoseStatusDidNotChange`'s `Account`
     insert, already outside `runAs`, is likewise switched from a plain `insert` to
     `insertAsSystem` for consistency with the other three methods rather than because it was
     failing.
   - **What stayed inside `System.runAs(agent)`, unchanged:** every `Assert.*` call, every
     `Test.startTest`/`Test.stopTest` boundary, the `CaseMilestone` queries in
     `triggerWritesCompletionDateOnAnOpenMilestone`, the real `update responded;` that fires
     `CaseMilestoneTrigger`, and every `CaseMilestoneService.completeMilestones(...)` call — the
     action under test in each of the four methods, and the only DML or query a real Tier 1 agent
     performs.
   - The class-level doc comment gained a second repair paragraph (mirroring § 8's) naming F-60 and
     Gotcha 15; no possessive apostrophe was introduced into any comment this repair touched, per
     the checker-parsing hazard AB-M4S05-14 recorded in § 8.

**Checked this run:**

```text
$ python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py \
    --manifest-dir artefacts/M4-S05 --strict
scanned 5 Apex file(s) under artefacts/M4-S05: 0 ERROR, 0 WARN

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py \
    --manifest-dir artefacts/M4-S05/classes --strict
Scanned 4 Apex class file(s); audited 3 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
{"score": 100, "findings": []}
```

`check-outputs` is `ok` on all 8 declared paths — no path changed, content changed on
`CaseMilestoneServiceTest.cls` and full replacement on `TestDataFactory.cls`.
`diff templates/apex/tests/TestDataFactory.cls artefacts/M4-S05/classes/TestDataFactory.cls` and
`diff templates/apex/tests/TestUserFactory.cls artefacts/M4-S05/classes/TestUserFactory.cls` are
both empty. All 5 `.cls`/`.trigger` files still balance braces/parens/brackets and all 5
`-meta.xml` files still parse with `ElementTree`.

**Not part of this repair, and not touched:** `CaseMilestoneService.cls`,
`CaseMilestoneTrigger.trigger`, every `-meta.xml` file, and `classes/TestUserFactory.cls` (unchanged
since § 8; `mintAgent()`'s mixed-DML fence and permission-set choice are untouched). A parallel
repair to `M2-S02`'s permission sets (adding standard-field permissions to the Tier 1 sets, per
`reports/MOCK-DEPLOY-M5.md` run 5's own suggested fix) is out of scope for this step and this step
does not depend on it or wait for it — this repair stands on its own regardless of whether that
parallel repair lands, because it changes where DML runs, not what the persona is granted.

**Obligation on `M5-S05`, still not discharged here.** Unchanged from § 8:
`M5-S05`'s `package.xml` still owes a fifth `ApexClass` member, `TestUserFactory` — this run adds
no new Apex file, so the obligation is neither created nor resolved by this repair. Carried forward
exactly as § 8 left it.

**Consequence for the milestone/build gates.** This step returns to `built` once this record is
written; `step-tester` and `build-doc-keeper` are the next commands. The M4 acceptance and the
pending M5/G5 decision need re-signing against a dry run that actually executes
`CaseMilestoneServiceTest` and passes with the fixture seeded in system mode — run 6 of
`reports/MOCK-DEPLOY-M5.md`.

---

## 10. Third test-only repair — F-61: the milestone process was found by luck, not by name

This step was `built`, the operator's probe (`reports/MOCK-DEPLOY-M5.md` run 6) found the § 9
repair itself incomplete on the two milestone-dependent methods, and it was reset
`built → failed → pending → running` for a third **section 4 test-only repair of a documented step
in a build whose gates are all approved**. This section is that record. `CaseMilestoneService.cls`
and `CaseMilestoneTrigger.trigger` remain unchanged, byte for byte, exactly as in § 8 and § 9. Only
`CaseMilestoneServiceTest.cls` changes again; `TestDataFactory.cls` and `TestUserFactory.cls` are
untouched this run.

**Trigger:** `reports/MOCK-DEPLOY-M5.md` run 6 — after the § 9 repair,
`--tests CaseMilestoneServiceTest`. Result: the persona now creates and updates the `Case` — 2 of 4
methods pass (`staysAtOneQueryAndOneDmlFor200Cases` and `ignoresCasesWhoseStatusDidNotChange`, the
two that never depend on a real milestone row). `triggerWritesCompletionDateOnAnOpenMilestone` and
`skipsAMilestoneThatIsAlreadyCompleted` — the two that call `requireActiveProcess()` and then read
or complete a milestone against its result — still fail.

**F-61 (HIGH).** `requireActiveProcess()`'s query was `WHERE IsActive = true LIMIT 1`, with no name
filter at all — deploy-order.md § 4 flagged this exact gap as an open item before it was ever run
against an org ("takes `LIMIT 1` over *any* active process, not necessarily
`First_Response_Premier` or `First_Response_Standard`. If the org has an unrelated active process,
the run fails... That is a loud failure rather than a wrong pass, but it is a sharper filter the
skill does not document and this step did not invent one."). The target org has exactly that: an
active process already in place before this build deployed anything, carrying no `First Response`
milestone. `LIMIT 1` with no ordering guarantee handed that row back instead of
`First_Response_Standard`, so both methods that depend on a real milestone queried or completed
nothing and failed on the milestone assertion, not on any FLS or DML error — a different failure
shape from F-59/F-60, and not a fixture-seeding defect at all.

**Which process, and why Standard.** `artefacts/M4-S02/entitlementProcesses/` ships two active
processes, `First_Response_Premier.entitlementProcess-meta.xml` and
`First_Response_Standard.entitlementProcess-meta.xml`. This fixture is written for **Standard**:
`decisions.md` **D-M1S01-04** records that `Account.Support_Tier__c` (the field that would
otherwise select Premier vs. Standard) carries no field default because "the contracted tier is a
contractual fact about the account; a default would silently assert one" — this test's `Account`
fixture is a synthetic record with no contract behind it, so nothing entitles it to the Premier
process, and naming Standard explicitly is the only reading that does not assert a fact the fixture
does not have. Premier is not queried at all, and `PROCESS_NAME_CANDIDATES` is scoped to Standard's
two possible spellings only.

**The two spellings, and why both are queried — UNVERIFIED, stated rather than guessed.**
`artefacts/M4-S02/deploy-order.md` § 4.1 records that this build's `<name>` metadata attribute was
set to `First_Response_Standard` (matching the declared file base name) and that only
`SlaProcess.NameNorm` — a separate, lower-cased, derived field — is documented as being reshaped by
the platform; nothing in `skills/apex/entitlement-apex-hooks` or
`skills/admin/entitlements-and-milestones` states whether the `SlaProcess.Name` field itself
preserves the metadata `name` literally or whether the platform stores or displays a
space-separated label form (`First Response Standard`) instead. Rather than guess, the query filters
`Name IN ('First_Response_Standard', 'First Response Standard')` and asserts the result count is
exactly one — one match either way settles which spelling this org uses, without the test needing
to know in advance.

**Fixed:**

1. `classes/CaseMilestoneServiceTest.cls` — `requireActiveProcess()` no longer selects any active
   `SlaProcess`. The query adds `AND Name IN :STANDARD_PROCESS_NAMES` (a new
   `private static final List<String> STANDARD_PROCESS_NAMES` constant carrying both candidate
   spellings) and drops `LIMIT 1`. The `if (processes.isEmpty())` / `Assert.isTrue(false, ...)`
   pair is replaced with `Assert.areEqual(1, processes.size(), ...)`, so the method now fails
   loudly both when the named process is missing or inactive **and** when more than one row
   matches — a case the old `LIMIT 1` could never surface because it silently kept only the first
   row. The failure message names the process by its declared file
   (`artefacts/M4-S02/entitlementProcesses/First_Response_Standard.entitlementProcess-meta.xml`)
   and both spellings tried, and reports how many rows were actually found.
2. The class-level doc comment gained a third repair paragraph (mirroring § 8's and § 9's) naming
   F-61. **No assertion behaviour outside `requireActiveProcess()` changed** — the four `@IsTest`
   methods, `entitlementFor`, `caseInsideProcess`, `caseOverrides`, and `mintAgent()` are
   byte-for-byte unchanged from § 9. No possessive apostrophe was introduced into any comment this
   repair added, per the checker-parsing hazard `AB-M4S05-14` recorded in § 8.

**The diff, in full** (the only method whose body changed):

```diff
-    /**
-     * Returns an active entitlement process, or fails the run with a message that names
-     * the missing prerequisite. Deliberately an assertion rather than `return null` — a
-     * skipped test in this domain is indistinguishable from a passing one.
-     */
-    private static SlaProcess requireActiveProcess() {
-        List<SlaProcess> processes = [
-            SELECT Id, Name
-            FROM SlaProcess
-            WHERE IsActive = true
-            LIMIT 1
-        ];
-        if (processes.isEmpty()) {
-            Assert.isTrue(
-                false,
-                'No active SlaProcess in this org. CaseMilestoneServiceTest cannot ' +
-                'create one (SlaProcess has no create() call), so an entitlement ' +
-                'process with a "' + MILESTONE_TYPE + '" milestone must exist in the ' +
-                'target org before this test can prove anything.'
-            );
-        }
-        return processes[0];
-    }
+    /**
+     * Both spellings this test will accept for the deployed Standard-tier process name.
+     * F-61 (reports/MOCK-DEPLOY-M5.md run 6): requireActiveProcess() previously selected
+     * WHERE IsActive = true LIMIT 1 with no name filter, and a pre-existing active process
+     * already in the target org (no First Response milestone) was returned instead of the
+     * deployed First_Response_Standard. Standard, not Premier, is the process this test
+     * fixture is written to enter -- artefacts/M4-S02/entitlementProcesses/ ships both, and
+     * decisions.md D-M1S01-04 records that Support_Tier__c carries no field default, so
+     * Standard is the tier this fixture names explicitly rather than assumes. Neither
+     * skills/apex/entitlement-apex-hooks nor skills/admin/entitlements-and-milestones states
+     * whether SlaProcess.Name preserves the metadata name attribute literally
+     * (First_Response_Standard, per artefacts/M4-S02/deploy-order.md section 4.1 -- name was
+     * set to match the declared file base name) or whether the platform stores a
+     * space-separated label form (First Response Standard) -- UNVERIFIED, so both spellings
+     * are queried rather than guessed.
+     */
+    private static final List<String> STANDARD_PROCESS_NAMES = new List<String>{
+        'First_Response_Standard', 'First Response Standard'
+    };
+
+    /**
+     * Returns the one deployed Standard-tier entitlement process, or fails the run with a
+     * message that names it. Deliberately an assertion rather than `return null` -- a
+     * skipped test in this domain is indistinguishable from a passing one. Filtering by name
+     * (F-61) replaces the earlier any-active-process query, which a second active process in
+     * the target org made unsafe to assume picks the right one.
+     */
+    private static SlaProcess requireActiveProcess() {
+        List<SlaProcess> processes = [
+            SELECT Id, Name
+            FROM SlaProcess
+            WHERE IsActive = true
+              AND Name IN :STANDARD_PROCESS_NAMES
+        ];
+        Assert.areEqual(
+            1,
+            processes.size(),
+            'Expected exactly one active SlaProcess named "First_Response_Standard" (or ' +
+            'its label form "First Response Standard") in this org -- found ' +
+            processes.size() + '. CaseMilestoneServiceTest cannot create this row ' +
+            '(SlaProcess has no create() call), so the deployed Standard-tier entitlement ' +
+            'process at artefacts/M4-S02/entitlementProcesses/' +
+            'First_Response_Standard.entitlementProcess-meta.xml must exist, be active, ' +
+            'and be the only match before this test can prove anything.'
+        );
+        return processes[0];
+    }
```

**Checked this run:**

```text
$ python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py \
    --manifest-dir artefacts/M4-S05 --strict
scanned 5 Apex file(s) under artefacts/M4-S05: 0 ERROR, 0 WARN

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py \
    --manifest-dir artefacts/M4-S05/classes --strict
Scanned 4 Apex class file(s); audited 3 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
{"score": 100, "findings": []}
```

`check-outputs` is `ok` on all 8 declared paths — no path changed, content changed on
`CaseMilestoneServiceTest.cls` only. `TestDataFactory.cls` and `TestUserFactory.cls` are untouched
this run; their § 9 `diff`-empty status against the templates is unaffected. All 5
`.cls`/`.trigger` files still balance braces/parens/brackets and all 5 `-meta.xml` files still
parse with `ElementTree`.

**Not part of this repair, and not touched:** `CaseMilestoneService.cls`,
`CaseMilestoneTrigger.trigger`, every `-meta.xml` file, `classes/TestDataFactory.cls`, and
`classes/TestUserFactory.cls`. The three other `@IsTest` methods, `entitlementFor`,
`caseInsideProcess`, `caseOverrides`, and `mintAgent()` are unchanged from § 9 — F-61 is entirely
inside `requireActiveProcess()`.

**Obligation on `M5-S05`, still not discharged here.** Unchanged from § 8 and § 9: `M5-S05`'s
`package.xml` still owes a fifth `ApexClass` member, `TestUserFactory`. This run adds no new Apex
file, so the obligation is neither created nor resolved by this repair.

**Consequence for the milestone/build gates.** This step returns to `built` once this record is
written; `step-tester` and `build-doc-keeper` are the next commands. The M4 acceptance and the
pending M5/G5 decision need re-signing against a dry run that actually executes
`CaseMilestoneServiceTest` and passes all four methods against the named `First_Response_Standard`
process — run 7 of `reports/MOCK-DEPLOY-M5.md`.

---

## 11. Fourth repair — F-62: the first to touch shipped code, not test-only

This step was `built`, the operator's probe (`reports/MOCK-DEPLOY-M5.md` run 7) found the § 10
repair itself incomplete on behaviour rather than on lookup, and it was reset
`built → failed → pending → running` for a fourth repair. Every prior repair in this section (§ 8,
§ 9, § 10) was **test-only** — `CaseMilestoneService.cls` and `CaseMilestoneTrigger.trigger` were
unchanged, byte for byte, across all three. **This repair is not test-only.**
`CaseMilestoneService.cls` changes: its `CaseMilestone` query and DML now run in explicit system
mode. This is recorded here as a deviation from every prior section's "shipped code unchanged"
line, per the coordinator's own framing of the task.

**Trigger:** `reports/MOCK-DEPLOY-M5.md` run 7 — after the § 10 repair,
`--tests CaseMilestoneServiceTest`. Result: the deployed process is now found and the Case enters
it (F-61 confirmed fixed). The two milestone-dependent methods still fail, this time on
**behaviour**, not lookup:

```text
CaseMilestoneServiceTest.skipsAMilestoneThatIsAlreadyCompleted
  System.AssertException: Assertion Failed: A completed milestone must not be re-stamped.
  attempted > 0 means the CompletionDate = NULL filter is missing from the query.
  Expected: 0, Actual: 1

CaseMilestoneServiceTest.triggerWritesCompletionDateOnAnOpenMilestone
  System.AssertException: Assertion Failed: CompletionDate is the only writable completion
  control on CaseMilestone; if it is still null the trigger did not run or the update did
  not take.
```

**Diagnosis, confirmed from the code and from the persona's grants before any fix was
written.** Reading `CaseMilestoneService.cls` lines 100–160 (pre-repair) against the two
failures:

1. The query (`SELECT Id, CaseId, CompletionDate FROM CaseMilestone WHERE CaseId IN :caseIds AND
   MilestoneType.Name = :milestoneTypeName AND CompletionDate = NULL WITH USER_MODE LIMIT 10000`)
   ran `WITH USER_MODE`, which at `apiVersion` 67.0 is also the silent default — stating it
   explicitly changed nothing about what the query could see. It still found the open milestone
   (`skipsAMilestoneThatIsAlreadyCompleted`'s first pass logs `first.attempted > 0` — asserted and
   passing, per the test's own code, since that read-side grant question is separate from the
   write-side one below).
2. `Database.update(openMilestones, false)` ran with no `AccessLevel` argument, so it too
   inherited the class's 67.0 default: user mode, as the Tier 1 agent. `grep -rn CaseMilestone
   artefacts/M2-S02/` returns nothing — confirmed directly against the org-facing source: none of
   `Case_Agent_Core.permissionset-meta.xml`, `Case_Tier1.permissionset-meta.xml`,
   `Case_Tier2.permissionset-meta.xml` or `Case_Billing.permissionset-meta.xml` declares an
   `objectPermissions` block for `CaseMilestone` at all — no Create, no Read, no Edit, on any of
   the four. `Case_Agent_Core`'s own `objectPermissions` list names exactly `Case`, `Account`,
   `Contact`, `EmailMessage`, `Entitlement` (confirmed by reading the file directly) — `CaseMilestone`
   is absent, not merely read-only. `allOrNone = false` means this refusal did not throw; it landed
   in `saveResults[i].getErrors()` and was collected into `result.failures`, exactly as the
   `for (Database.SaveResult saveResult : saveResults)` loop is written to do.
3. The test never asserted on `first.failures` (only `first.attempted > 0`), and
   `triggerWritesCompletionDateOnAnOpenMilestone` never inspects a `CompletionResult` at all — it
   only re-queries `CaseMilestone.CompletionDate` after a real `update`. Both silent gaps meant the
   refusal surfaced only as a wrong count downstream: `skipsAMilestoneThatIsAlreadyCompleted`'s
   second pass found the same still-open row (`second.attempted` = 1, not 0, since the first pass
   never actually stamped it), and `triggerWritesCompletionDateOnAnOpenMilestone` read back
   `CompletionDate = null` because the trigger-invoked update was refused the same way.

**This reading matches the code and the persona's grants exactly** — no part of it required
revising against the evidence. `CaseMilestoneService.cls`'s own header comment already framed
`CaseMilestone` as platform-owned ("the platform creates and deletes the rows, Apex can only
update them"), which is consistent with no persona in this build ever having been granted access to
it.

**The fix, and why system mode rather than a wider grant.** Two candidates were on the table per
the task: narrow the write to system mode, or grant the Tier 1 persona Edit on `CaseMilestone`.
`skills/apex/apex-security-patterns` (`SKILL.md`, the access-mode decision table) names exactly this
shape — *"Integration, batch, or platform-utility code on a 67.0+ class must see all rows and
fields → Explicit `WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE` plus a `// reason:` comment"* — and
distinguishes it from *"Code both queries and updates data on behalf of a user"*, which is what
`WITH USER_MODE` / `as user` is for. Completing a milestone is the former: the entitlement engine's
own completion signal, invoked from a trigger the moment a Case leaves its opening Status, not a
field the Tier 1 agent deliberately edits — the agent changes `Case.Status`; the platform decides
what that means for `CaseMilestone`. `skills/apex/apex-stripinaccessible-and-fls-enforcement`
reinforces the same boundary from the other direction: its "Before Starting" checklist treats
internal trusted-context data (its own example: "trigger handler reading from the trigger context")
as not needing user-supplied-data enforcement in the first place, and its remediation tool
(`Security.stripInaccessible`) is for records built from **less-privileged, user-supplied** input —
`CaseMilestone` here is neither user-supplied nor being trimmed for degraded partial success; it is
fully platform-owned and the write is all-or-nothing per row. Granting the persona Edit on
`CaseMilestone` was rejected because it repeats, one object over, the exact anti-pattern
`skills/apex/test-class-standards` Gotcha 15 already named for this build's own test fixtures: widen
a persona to access nobody asked it to have, rather than drawing the boundary at what the persona's
job actually requires. A Tier 1 support agent's job is to work Cases; `CaseMilestone` is SLA
infrastructure no requirement in this build asks the agent to control directly, and `plan.json`
`steps[M4-S05].skills[]` cites `admin/entitlements-and-milestones`, whose own framing (the platform
computes and administers milestone state; Apex's one supported write is `CompletionDate`) does not
name the case-working agent as the intended writer either.

**A cross-skill tension worth naming, resolved by the more precise, docs-grounded reading.**
`skills/apex/apex-stripinaccessible-and-fls-enforcement`'s own "Before Starting" section states, in
passing, that "a trigger body runs in system mode... at every API version" and that "the 67.0
default-user-mode change does not reach it." Read literally and applied here, that line would imply
`CaseMilestoneTrigger` already ran in system mode and F-62 could not happen. It does not resolve the
tension in this class's favour: `CaseMilestoneService.completeMilestones` is not code inside the
literal `trigger CaseMilestoneTrigger on Case (...) { }` block — it is a regular method on a
separate `public with sharing class`, governed by its own `.cls-meta.xml` `apiVersion` (67.0), and
`skills/apex/apex-security-patterns` (grounded directly in the Apex Developer Guide, quoted in its
`references/well-architected.md`) states the finer-grained rule that actually applies: *"database
operations within trigger bodies... run in user mode unless system mode is explicitly specified"* at
67.0+, and that default reaches operations regardless of whether the calling code is literally the
trigger block or a class it calls. `skills/apex/entitlement-apex-hooks`'s own reference example
(`references/code-examples.md`, the "What `apiVersion` 67.0 changes" section) says the same thing
even more directly, and predicts this exact failure mode by name: *"A service-agent user who cannot
see a `CaseMilestone` row will not complete it through this trigger, and `Database.update(...,
false)` will hand you that row's error rather than throwing."* Per `standards/source-hierarchy.md`,
the docs-grounded skill governs; the looser line in
`apex-stripinaccessible-and-fls-enforcement` is flagged below as a skill-quality signal, not applied
here.

**Fixed:**

1. `classes/CaseMilestoneService.cls` — the `CaseMilestone` `SELECT` gained `WITH SYSTEM_MODE` in
   place of `WITH USER_MODE`, and `Database.update(openMilestones, false)` gained a third argument,
   `AccessLevel.SYSTEM_MODE`. Both carry a `// reason:` comment naming F-62, the absence of any
   `CaseMilestone` grant in this build, and the rejected alternative (widening the persona). The
   class-level doc comment gained a fourth paragraph recording this as the first shipped-code
   change in this step's repair history. **No other line in this class changed** — the query's
   `WHERE` clause, `MAX_MILESTONES`, the partial-success loop, and every other method are unchanged.
2. `classes/CaseMilestoneServiceTest.cls` — three new assertions close the silent gap the task
   named: after `skipsAMilestoneThatIsAlreadyCompleted`'s first `completeMilestones` call,
   `staysAtOneQueryAndOneDmlFor200Cases`'s one call, and `ignoresCasesWhoseStatusDidNotChange`'s one
   call, `Assert.areEqual(0, result.failures.size(), String.join(result.failures, ' | '))` (or the
   equivalent named variable) now runs. `skipsAMilestoneThatIsAlreadyCompleted`'s second-pass
   failures assertion already existed (§ 8) and is unchanged.
   `triggerWritesCompletionDateOnAnOpenMilestone` gained no new assertion — it never holds a
   `CompletionResult` to assert on; its existing `reloaded.CompletionDate != null` check is the
   correct proof for that method's real-`update` shape, and it is expected to pass once the service
   fix lands. The class-level doc comment gained a fourth repair paragraph naming F-62.

**The diff — both files, in full:**

```diff
--- CaseMilestoneService.cls (query)
-        // WITH USER_MODE is redundant at apiVersion 67.0 — user mode is the default — but
-        // it states the intent at the call site, where a future version downgrade would
-        // otherwise change behaviour silently. WITH SECURITY_ENFORCED is not used: it was
-        // removed at 67.0 and does not compile.
+        // reason: F-62 (reports/MOCK-DEPLOY-M5.md run 7) -- completing a milestone is a
+        // system-integrity write performed by a trigger on behalf of the platform, not an
+        // action the running user takes deliberately; no permission set in this build
+        // grants any access to CaseMilestone at all (artefacts/M2-S02/), by design. At
+        // apiVersion 67.0 the default is user mode, so this query previously returned zero
+        // rows for a persona holding no CaseMilestone access, hiding an open milestone the
+        // platform still needed completed. WITH SYSTEM_MODE opts this query into
+        // platform-level visibility instead of running-user visibility, per the
+        // integration/platform-utility guidance in skills/apex/apex-security-patterns and
+        // the graceful-degradation boundary in
+        // skills/apex/apex-stripinaccessible-and-fls-enforcement. Granting the persona Edit
+        // on CaseMilestone instead was considered and rejected -- see deploy-order.md
+        // section 11 for why narrowing to system mode, not widening the permission set, is
+        // the correct boundary here. WITH SECURITY_ENFORCED is not used: it was removed at
+        // 67.0 and does not compile.
         List<CaseMilestone> openMilestones = [
             SELECT Id, CaseId, CompletionDate
             FROM CaseMilestone
             WHERE CaseId IN :caseIds
               AND MilestoneType.Name = :milestoneTypeName
               AND CompletionDate = NULL
-            WITH USER_MODE
+            WITH SYSTEM_MODE
             LIMIT 10000
         ];

--- CaseMilestoneService.cls (DML)
-        List<Database.SaveResult> saveResults = Database.update(openMilestones, false);
+        // reason: AccessLevel.SYSTEM_MODE matches the query above (F-62) -- the milestone
+        // stamp is the platform completion signal, not a field the running user is expected
+        // to edit directly, and no permission set in this build grants CaseMilestone access.
+        // Narrowing to this one object and this one write, rather than granting the persona
+        // Edit on CaseMilestone, keeps the same discipline skills/apex/test-class-standards
+        // Gotcha 15 applies elsewhere in this build: a persona is not widened for access its
+        // job does not call for.
+        List<Database.SaveResult> saveResults = Database.update(
+            openMilestones, false, AccessLevel.SYSTEM_MODE
+        );

--- CaseMilestoneServiceTest.cls (three call sites)
             Assert.isTrue(first.attempted > 0, 'Set-up pass must complete at least one milestone.');
+            Assert.areEqual(0, first.failures.size(), String.join(first.failures, ' | '));
@@
             Assert.areEqual(
                 result.attempted,
                 result.completed + result.failures.size(),
                 'Every attempted milestone must be accounted for as a success or a failure.'
             );
+            Assert.areEqual(0, result.failures.size(), String.join(result.failures, ' | '));
@@
             Assert.areEqual(0, result.attempted, 'An unchanged Status must attempt nothing.');
             Assert.areEqual(0, queriesUsed, 'An unchanged Status must not reach the query.');
+            Assert.areEqual(0, result.failures.size(), String.join(result.failures, ' | '));
```

**Checked this run:**

```text
$ python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py \
    --manifest-dir artefacts/M4-S05 --strict
scanned 5 Apex file(s) under artefacts/M4-S05: 0 ERROR, 0 WARN

$ python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py \
    --manifest-dir artefacts/M4-S05/classes --strict
Scanned 4 Apex class file(s); audited 3 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
{"score": 100, "findings": []}
```

`check-outputs` is `ok` on all 8 declared paths — no path changed; content changed on
`CaseMilestoneService.cls` and `CaseMilestoneServiceTest.cls` only. `TestDataFactory.cls` and
`TestUserFactory.cls` remain diff-empty against their templates, untouched this run. All 5
`.cls`/`.trigger` files still balance braces/parens/brackets and all 5 `-meta.xml` files still
parse with `ElementTree`. `EAH005` (no `WITH SECURITY_ENFORCED`) still clears — `WITH SYSTEM_MODE`
is a different clause and the checker does not flag it; `EAH006` (every `CaseMilestone` query
filters `CompletionDate = NULL` or is pinned to held Ids) still clears, unaffected by the mode
keyword.

**Not part of this repair, and not touched:** `CaseMilestoneTrigger.trigger` (still the one-line
adapter calling `CaseMilestoneService.completeFirstResponseMilestone`), every `-meta.xml` file,
`classes/TestDataFactory.cls`, and `classes/TestUserFactory.cls`. `mintAgent()`, `entitlementFor`,
`caseInsideProcess`, `caseOverrides`, `requireActiveProcess()`, and every `Test.startTest`/
`Test.stopTest` boundary and pre-existing `Assert.*` call are unchanged from § 10 — F-62 added
assertions but changed none.

**Obligation on `M5-S05`, still not discharged here.** Unchanged from § 8, § 9 and § 10: `M5-S05`'s
`package.xml` still owes a fifth `ApexClass` member, `TestUserFactory`. This run adds no new Apex
file.

**Skill-quality signal, recorded rather than fixed here.**
`skills/apex/apex-stripinaccessible-and-fls-enforcement`'s "Before Starting" line — "a trigger body
runs in system mode... at every API version... [t]he 67.0 default-user-mode change does not reach
it" — is imprecise at 67.0+ for exactly the reason this section's cross-skill-tension paragraph
works through: it is true only of code literally inside the `trigger { }` block, and F-62 is
evidence a reader can apply it too broadly to a class the trigger merely calls. Flagged for
`build-doc-keeper` to carry forward as a skill-authoring follow-up, per
`standards/build-orchestration.md` § 8 — not corrected here, since fixing that skill's own wording
is that skill's concern, not this step's scope.

**Consequence for the milestone/build gates.** This step returns to `built` once this record is
written; `step-tester` and `build-doc-keeper` are the next commands. Because this repair changes
shipped code for the first time in this step's history, the M4 acceptance and the pending M5/G5
decision need re-signing not only against a passing dry run but against the fact that
`CaseMilestoneService.cls` itself is no longer byte-identical to what earlier milestone/gate
records certified — run 8 of `reports/MOCK-DEPLOY-M5.md` is the evidence for both.

---

## Sources

- `plan.json` `steps[M4-S05]` (`inputs{}`, `outputs[]`, `acceptance_tests[]`), `decisions[D8, D10]`,
  `assumptions[A27]`, `clarifications[Q16, Q50, Q53]`
- `artefacts/M4-S02/milestone-completion-decision.md` (D10 and the step binding);
  `artefacts/M4-S02/milestoneTypes/First Response.milestoneType-meta.xml`;
  `artefacts/M1-S01/objects/Case/businessProcesses/`;
  `artefacts/M3-S01/objects/Case/validationRules/`
- `skills/apex/entitlement-apex-hooks` — `SKILL.md`, `references/examples.md`,
  `references/code-examples.md`, `references/gotchas.md`, `scripts/check_entitlement_apex_hooks.py`
- `skills/admin/entitlements-and-milestones/references/metadata-examples.md` § 9
- `skills/apex/apex-design-patterns` — `SKILL.md`, `references/code-examples.md` (ApexTrigger meta shape)
- `templates/apex/TriggerHandler.cls`, `templates/apex/TriggerHandler.cls-meta.xml`,
  `templates/apex/tests/TestDataFactory.cls` (copied verbatim into this step's artefacts), `templates/README.md`
- `reports/MOCK-DEPLOY-M4.md` run 2 — F-37, the org error this step was rebuilt for
- `standards/decision-trees/automation-selection.md` (Q2 → Q13 → Q15, entitlement-milestones leaf)
- `agents/_shared/AGENT_CONTRACT.md` § Apex security idiom by API version, § Gate C;
  `agents/apex-builder/GATES.md` Gate B / C / D
- `reports/MOCK-DEPLOY-M5.md` run 4 — F-59, the failing test-execution evidence this repair (§ 8)
  responds to, and the operator's probe result on the scratch copy
- `skills/apex/test-class-standards/references/gotchas.md` Gotchas 13, 14 and 15;
  `references/examples.md` Example 5; `scripts/check_test_class_standards.py`
- `templates/apex/tests/TestUserFactory.cls` (copied verbatim into this step's artefacts, § 8);
  `templates/apex/tests/TestDataFactory.cls` as corrected at commit `5edcb3281` (replaces the
  step's earlier copy verbatim, § 8) and again at commit `be09a7bff` (adds `insertAsSystem`,
  replaces the step's § 8 copy verbatim, § 9)
- `reports/MOCK-DEPLOY-M5.md` run 5 — F-60, the failing fixture-insert evidence this repair (§ 9)
  responds to
- `envelopes/M4-S05/2026-09-12T17-06-24Z.json` — the § 8 repair's own envelope, the first § 4
  test-only repair this run builds on (its `.md` report was never written — see this run's own
  envelope, "what the playbook did not support")
- `reports/MOCK-DEPLOY-M5.md` run 6 — F-61, the failing milestone-lookup evidence § 10 responds to
- `artefacts/M4-S02/entitlementProcesses/First_Response_Premier.entitlementProcess-meta.xml`,
  `artefacts/M4-S02/entitlementProcesses/First_Response_Standard.entitlementProcess-meta.xml` —
  confirms which process names this build deploys, and that Standard is named explicitly per § 10
- `decisions.md` **D-M1S01-04** — `Account.Support_Tier__c` carries no field default; grounds why
  this fixture names Standard rather than asserting a tier the synthetic Account does not have
- `artefacts/M4-S02/deploy-order.md` § 4.1 — the `<name>` metadata attribute vs. `NameNorm`
  distinction that leaves whether `SlaProcess.Name` preserves the underscore form or a
  space-separated label form UNVERIFIED (§ 10)
- `reports/MOCK-DEPLOY-M5.md` run 7 — F-62, the failing milestone-behaviour evidence § 11 responds
  to, and the raw `summary.md` / `result.json` from the operator's probe
- `skills/apex/apex-security-patterns/SKILL.md` — the access-mode decision table (integration /
  batch / platform-utility code on a 67.0+ class → explicit `WITH SYSTEM_MODE` /
  `AccessLevel.SYSTEM_MODE`), grounding § 11's fix
- `skills/apex/apex-stripinaccessible-and-fls-enforcement/SKILL.md` — the "Before Starting"
  internal-trusted-context-data framing that supports treating `CaseMilestone` as not
  user-supplied data needing a strip pass, and the "trigger body runs in system mode... at every
  API version" line flagged in § 11 as imprecise at 67.0+ and not applied here
  (`skills/apex/apex-security-patterns/references/well-architected.md` and
  `skills/apex/entitlement-apex-hooks/references/code-examples.md` "What `apiVersion` 67.0
  changes" both ground the finer-grained rule this repair follows instead)
- `standards/source-hierarchy.md` — governs which of the two skills above wins where they disagree
- `artefacts/M2-S02/permissionsets/Case_Agent_Core.permissionset-meta.xml`,
  `Case_Tier1.permissionset-meta.xml`, `Case_Tier2.permissionset-meta.xml`,
  `Case_Billing.permissionset-meta.xml` — re-confirmed directly this run: none declares an
  `objectPermissions` block for `CaseMilestone`
- `skills/apex/test-class-standards/references/gotchas.md` Gotcha 15 — the same
  do-not-widen-the-persona discipline applied one object over, grounding why granting Edit on
  `CaseMilestone` was rejected in favour of narrowing to system mode
- `.sfskills/builds/tier2-webhook/artefacts/M1-S03/deploy-order.md` § 0b / § 0c — the accepted
  shape this repair follows (mixed-DML fence, `System.runAs` placement)
- `artefacts/M2-S02/permissionsets/Case_Agent_Core.permissionset-meta.xml`,
  `artefacts/M2-S02/permissionsets/Case_Tier1.permissionset-meta.xml`,
  `artefacts/M2-S02/permissionsetgroups/PSG_Tier1_Prod.permissionsetgroup-meta.xml`,
  `artefacts/M2-S02/deploy-order.md` — the permission-set choice and its grounding (§ 8)
- `artefacts/M2-S03/profiles/Acme Support Tier 1.profile-meta.xml` — the profile paired with the
  permission-set choice (§ 8)
- `artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml` — considered and
  rejected (§ 8)
- `artefacts/M5-S05/deploy-order.md` § 1, `artefacts/M5-S05/package.xml` — the manifest that owes
  `TestUserFactory` an `ApexClass` member (§ 8, obligation not discharged here)
- `standards/build-orchestration.md` § 4 (the `documented → running` rebuild path and borrowed-agent
  condition 2), § 5 *The Apex exception*
