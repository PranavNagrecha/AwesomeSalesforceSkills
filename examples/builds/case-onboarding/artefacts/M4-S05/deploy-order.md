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
