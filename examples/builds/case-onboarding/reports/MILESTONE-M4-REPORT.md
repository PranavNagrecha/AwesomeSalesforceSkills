# Milestone acceptance report — M4: SLA clocks, entitlements and escalation

**Build:** `case-onboarding` · **Milestone:** `M4` · **Verifier run:** `2026-09-12T09-08-11Z`
**Agent:** `milestone-verifier` (`agents/milestone-verifier/AGENT.md`, v1.0.0, `status: beta`)
**Scale:** `project` (`plan.json.scale` absent → `project` per `standards/build-orchestration.md` § 3.1)
**Written, not rendered** — § 2. Its path is recorded with `set-milestone`; no other writer touches it.

---

## Verdict

> ### `ready-with-findings`
>
> No step is blocked. No declared acceptance test fails. No recorded deploy-order position
> contradicts its artefact's type. The merged manifest built with no member collision and no
> version conflict. **Ten findings (F-39 … F-48) are open, two of them HIGH, and one of the two
> says plainly that the milestone's own goal statement is not met by the artefacts this milestone
> produced.** That is a decision for the human at the gate, which is what `ready-with-findings`
> means — a recommendation, never an approval.

**Confidence: MEDIUM.** Step 10 rubric, MEDIUM branch, on its first trigger: *some references were
unclassifiable.* Two reference classes could not be closed against this build's own symbol
inventory — the flow's `Priority` values (F-42) and the Entitlement feature the whole milestone
stands on (F-39). Everything else resolved. MEDIUM measures what the checks could *see*, not how
well M4 is built: all five steps are `documented`, all five runnable acceptance tests pass, and the
operator's mock deploy run 4 validated 55 of 55 components against a live org.

### Why not `not-ready`

Step 9 lists four triggers for `not-ready`: an unresolved reference, an ordering contradiction, a
failing acceptance test, or a blocked step. **None of the four is present.** In particular F-42 is
*not* an unresolved reference: `High` and `Medium` are values of the platform's standard
`CasePriority` value set, which this build never modifies and therefore never needed to declare —
the same reason `M1-S01` *did* declare `CaseOrigin` (it changed it) is the reason `CasePriority` is
legitimately absent. F-42 is an **unassertable** reference, not an unresolved one: no checker in
this build can prove the target org still carries `High`. That distinction is what keeps the verdict
at `ready-with-findings`, and it is stated here rather than left to be inferred.

### Why not `ready-for-gate`

`ready-for-gate` requires no findings the human must weigh. F-40 and F-39 are both such findings,
and F-40 in particular contradicts the milestone's own `goal` field. A verdict of `ready-for-gate`
would tell the human there is nothing to decide. There is.

---

## 1. Precondition (Step 1)

| Check | Result |
|---|---|
| Every step in `M4` is `documented` | **Yes** — `M4-S01`, `M4-S02`, `M4-S03`, `M4-S04`, `M4-S05`, all five `documented` |
| Any step `pending` / `running` / `built` / `tested` / `failed` | None |
| Any step `blocked` | **None.** Two steps *were* blocked mid-build and both blocks were closed at source, not at the artefact — `M4-S01` (`checker-policy`, closed by `admin/business-hours-and-holidays` v1.0.1, commit `5b206697a`) and `M4-S02` (`ambiguity`, closed by `admin/entitlements-and-milestones` v1.1.2, commit `a18f9164d`). Neither is a blocked step at verification time. |
| Preceding milestone gate `milestone:M3` | **`approved`** — 2026-09-12T06:24:17Z, by the dry-run operator, on `reports/MILESTONE-M3-REPORT.md` with six recorded decisions |
| `milestone:M4` gate | `pending` — unwritten, and this agent does not write it |

`M4`'s own `milestones[].status` is `building`. This run records `verified`.

### Rebuild history, because it is the evidence the artefacts were proven and not merely produced

| Step | Builds | What forced each rebuild |
|---|---|---|
| `M4-S01` | 2 | checker-policy block on the `Severity 1 24x7` always-open shape → closed at the **skill** (v1.0.1); the byte-identical file passed on re-run |
| `M4-S02` | 2 | ambiguity block on the milestones' missing `<timeTriggers>`/`<successActions>` → closed at the **skill** (v1.1.2, W4 → INFO, W7 split out); byte-identical file passed on re-run |
| `M4-S03` | 3 | **F-38** over two org round-trips: `Updated`-only rejected → `Initial`+`Updated` rejected with the mirror error → `Initial` alone validated. Skill fix still **pending** (D-M4S03-01) |
| `M4-S04` | 2 | **F-36** `notifyToTemplate is required` → closed at the skill (checker rule) and the artefact rebuilt |
| `M4-S05` | 2 | **F-37** `Variable does not exist: TestDataFactory` → `outputs[]` amended from 6 to 8 paths, the template shipped as a step-local class |

Three of the five blocks/rejections were closed at a **skill**, not at an artefact. That is the
flywheel working, and it is worth the gate reader's attention: the artefacts that were rejected are
the artefacts that now pass, byte-identical, in two of the three cases.

---

## 2. Steps and artefacts

| Step | Type | Agent | Status | Artefacts (deployable) | Notes/runbooks |
|---|---|---|---|---|---|
| `M4-S01` | `sla` | `metadata-builder` | documented | `settings/BusinessHours.settings-meta.xml` (3 calendars, 14 holidays) | `holiday-maintenance-runbook.md`, `deploy-order.md` |
| `M4-S02` | `sla` | `metadata-builder` | documented | `entitlementProcesses/First_Response_Premier`, `…_Standard`, `milestoneTypes/First Response` | `milestone-completion-decision.md`, `deploy-order.md` |
| `M4-S03` | `automation` | `metadata-builder` | documented | `flows/Case_BeforeSave_StampEntitlementAndCalendar`, `flowtests/…_Test`, `settings/Flow.settings-meta.xml` | `flow-governance-policy.yaml`, `no-account-fallback-note.md`, `deploy-order.md` |
| `M4-S04` | `sla` | `metadata-builder` | documented | `escalationRules/Case.escalationRules-meta.xml` | `escalation-activation-runbook.md`, `escalation-monitoring-note.md`, `deploy-order.md` |
| `M4-S05` | `automation` | `apex-builder` | documented | `triggers/CaseMilestoneTrigger.trigger` (+meta), `classes/CaseMilestoneService.cls`, `CaseMilestoneServiceTest.cls`, `TestDataFactory.cls` (+3 meta) | `deploy-order.md`. **No `package.xml`** — the Apex exception, § 4 |

11 deployable metadata files, 5 deployable component types plus 2 `Settings` members, 12 supporting
`.md`/`.yaml` notes. 16 XML files, **16/16 parse**.

---

## 3. Reference resolution (Step 3)

**35 references resolved, 2 unassertable, 0 unresolved.** Every reference class in the AGENT.md
Step 3 table that has instances in M4 is listed. A class with no instances is named as such, so the
reader knows the boundary of this check rather than inferring completeness from silence.

### 3.1 The seven cross-step checks this gate was asked for, taken one at a time

| # | The check | Result |
|---|---|---|
| 1 | **M4-S02's processes reference calendars that exist in M4-S01** | **PASS.** Four references, all `US Support`: `<businessHours>` on both processes and on both `<milestones>` blocks. `US Support` is a `<name>` in `M4-S01/settings/BusinessHours.settings-meta.xml`, carrying `<default>true</default>`. Asserted mechanically too: milestone test 2 (`check_entitlements_and_milestones.py --strict`) W3 fires on a calendar name absent from the settings file. **But see F-40** — resolving is not the same as being right. |
| 2a | **M4-S03 stamps calendar names that exist in M4-S01** | **PASS.** The flow's two `BusinessHours` Get Records filter `Name EqualTo "EMEA Support"` and `Name EqualTo "US Support"`. Both are `<name>`s in M4-S01. |
| 2b | **M4-S03 stamps an entitlement that exists in M4-S02** | **NO METADATA REFERENCE EXISTS.** The flow does not name an `EntitlementProcess`. `Get_Active_Entitlement` queries `Entitlement WHERE AccountId = … AND Status = 'Active'`, `getFirstRecordOnly true`, and assigns `.Id` to `$Record.EntitlementId`. The link from that `Entitlement` to `First_Response_Premier` or `First_Response_Standard` is a **data** binding (`Entitlement.SlaProcessId`) that **no step in this build creates**. → **F-41.** |
| 2c | **M4-S03's Priority values are in the CasePriority set** | **UNASSERTABLE.** `High` and `Medium` are written as `<stringValue>`. No `standardValueSets/CasePriority` exists anywhere under `artefacts/` — confirmed by an exhaustive grep, and already recorded from the other side by D-M4S03-03 and by `M3-S03`'s `web-to-case-form-contract.md` § 7. They resolve against the platform default; nothing in this build proves the target org still carries them. → **F-42.** |
| 3 | **M4-S04's queue resolves** | **PASS.** `<assignedTo>Tier_2_Engineering</assignedTo>`, `<assignedToType>Queue</assignedToType>`, twice. `artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml` exists (M2 accepted). The **developer-name** form is the one `check_escalation_rules.py` E7 requires, and E7 fires only at build scope — which is why this test is declared `scope: build`. |
| 3b | **M4-S04's templates resolve** | **PASS.** `case_intake/Case_Escalated_To_Tier2` appears four times (`assignedToTemplate` ×2, `notifyToTemplate` ×2). `artefacts/M3-S02/email/case_intake.emailFolder-meta.xml` + `case_intake/Case_Escalated_To_Tier2.email(-meta.xml)` exist, and M3-S02's `package.xml` names both the `EmailFolder` and the folder-qualified `EmailTemplate` members. M3 accepted. |
| 4 | **M4-S05's milestone name matches M4-S02's MilestoneType** | **PASS, exactly.** `CaseMilestoneService.MILESTONE_TYPE_NAME = 'First Response'` and `CaseMilestoneServiceTest.MILESTONE_TYPE = 'First Response'`; the `MilestoneType` component's `fullName` is derived from the file name `First Response.milestoneType-meta.xml` and the merged manifest's member is `First Response`. Three independent spellings, byte-identical including the space. The service's own comment names the file it was copied from. |
| 5 | **The flow and the trigger share a Case save** | **They do not contend — and that is the design.** See § 3.3. |
| 6 | **No `senderEmail` equals a routing address** | **PASS.** The build's only `senderEmail` is `support-noreply@acme.example` (`M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml`), as is its `replyToEmail`. The two Email-to-Case routing addresses are `support@acme.example` and `billing@acme.example`. Neither equals either. This is D-M3S02-04's decision holding, and the M3 gate's rejection of the `replyToEmail = support@` alternative still stands. **A different address collision is live, and it is M4's own** — see F-47 / decision item 1. |

### 3.2 Reference classes, by the AGENT.md Step 3 table

| Reference class | Instances in M4 | Read from | Resolves against | Outcome |
|---|---|---|---|---|
| Validation rule field references | 0 | — | — | No `.validationRule` in M4 (M3-S01 owns them) |
| Assignment rule criteria | 0 | — | — | No `.assignmentRules` in M4 (M3-S04 owns them) |
| Permission set grants | 0 | — | — | No `PermissionSet`/`Profile` in M4 (M2 owns them) |
| **Flow field references** | **17** | `<object>`, `<field>`, `<queriedFields>`, `assignToReference`, `leftValueReference`, `<stringValue>` in `Decision_*` | field/object/picklist inventory | **15 resolved in M1-S01 (earlier milestone), 2 unassertable (F-42)** |
| **Entitlement process milestones** | **6** | `<milestoneName>` ×2, `<businessHours>` ×4 | milestone-type + business-hours inventory | **All 6 resolved — 2 in M4-S02 itself, 4 in M4-S01** |
| Layout and path assignments | 0 | — | — | No `Layout`/`PathAssistant` in M4 (M1-S02 owns them) |
| **Escalation rule criteria + actions** *(not in the Step 3 table; added because M4 is the first milestone to carry the type)* | **10** | `<criteriaItems><field>`, `<value>`, `<assignedTo>`, `<assignedToTemplate>`, `<notifyToTemplate>` | field/picklist/queue/template inventory | **All 10 resolved — 3 in M1-S01, 1 in M2-S04, 4 in M3-S02, 2 platform (`Case.Status`)** |
| **Apex symbol references** *(not in the Step 3 table; added for the same reason)* | **4** | `MILESTONE_TYPE_NAME`, `OPENING_STATUS`, `MilestoneType.Name` SOQL bind, `CaseMilestone.CompletionDate` | milestone-type + picklist inventory + platform | **All 4 resolved** |

Flow field detail, since it is the largest class:

| Symbol | Resolves to | Where |
|---|---|---|
| `Account.Region__c` + values `EMEA`, `US` | `CustomField` + restricted value set | M1-S01 ✓ |
| `Account.Support_Tier__c` + value `Premier` | `CustomField` + restricted value set | M1-S01 ✓ |
| `Case.Severity__c` + value `Severity 1` | `CustomField` + restricted value set (one value defined, deliberately) | M1-S01 ✓ |
| `Case.Origin` values `Email-Support`, `Email-Billing` | `standardValueSets/CaseOrigin` | M1-S01 ✓ |
| `Case.AccountId`, `Case.EntitlementId`, `Case.BusinessHoursId`, `Case.Priority` | platform standard fields | platform — **`EntitlementId` exists only when Entitlement Management is on, F-39** |
| objects `Account`, `Entitlement`, `BusinessHours` | platform standard objects | platform — **`Entitlement` likewise, F-39** |
| `Case.Priority` values `High`, `Medium` | *nothing in this build* | **unassertable, F-42** |

Escalation criteria detail: `Case.Severity__c = "Severity 1"` ✓ M1-S01; `Case.Status != "Closed"`
✓ — `Closed` is a `<fullName>` in **both** `Support_Process` and `Billing_Process`
(M1-S01), so the criterion is record-type-independent, which matters because the rule has no record-type
filter. Same for the Apex's `OPENING_STATUS = 'New'`: present in both ladders
(`New → Escalated → Closed` and `New → Closed`), which is the whole basis of D-M4S05-02's proxy.

### 3.3 The order-of-execution implication (cross-step check 5), stated in full

`M4-S03`'s flow and `M4-S05`'s trigger both hang off a Case save, and the two **never run in the
same save**:

- The flow is `<triggerType>RecordBeforeSave</triggerType>` with `<recordTriggerType>Create</recordTriggerType>` — **insert only**.
- The trigger is `trigger CaseMilestoneTrigger on Case (after update)` — **update only**.

So there is no contention, no double-write, and `<triggerOrder>10</triggerOrder>` on the flow has
nothing to order against (it is the build's only record-triggered flow on Case; the checker's rule 8
is satisfied by its presence, not by a conflict).

**What actually matters is the sequence across two saves, and it is correct:**

1. **INSERT.** The before-save flow runs ahead of Apex before-triggers and ahead of custom
   validation rules. It stamps `EntitlementId`, `BusinessHoursId` and `Priority`. Two consequences
   the build depends on:
   - `Priority_Required_On_Agent_Save` (M3-S01) evaluates *after* the stamp, so a web case with no
     Priority is rescued rather than rejected. This is the closure of **F-32** that the M3 gate's
     decision (2) anticipated and could not yet prove, because M4-S03 did not exist. **It is now
     proven at the artefact level** — the flow writes Priority on the null-guarded path, and the
     `FlowTest` asserts `Priority = High` for exactly that case.
   - Entitlement rules run near the **end** of the insert's order of execution — after all before
     *and* after triggers — so `CaseMilestone` rows created by this save are invisible to any
     trigger inside it. The trigger's own header comment records this, and it is why `after update`
     is a correctness requirement here, not a style choice.
2. **FIRST UPDATE that takes Status out of `New`.** The after-update trigger fires, the
   `CaseMilestone` rows created by the insert already exist, the three-clause `WHERE` (case Ids ∧
   milestone type ∧ `CompletionDate = NULL`) finds the open one, one DML writes `CompletionDate`.
3. **Idempotency.** `CompletionDate = NULL` in the same `WHERE` makes a second pass a no-op, which
   is the guard that substitutes for the recursion control the two-file shape does not have
   (D-M4S05-03).

One real interaction remains, and it runs in the safe direction: the escalation rule's entry 2 uses
`<businessHoursSource>Case</businessHoursSource>`, reading `Case.BusinessHoursId` — the field the
flow stamped during the *same* insert, before the escalation engine sees the record. Forwards, not
backwards. ✓

---

## 4. Deployment order (Step 4)

The canonical sequence is objects → fields → picklists → record types → layouts → permission sets →
sharing → automation → routing → SLA. Every M4 deployable component carries a recorded position on
its workbook row, and **every recorded position agrees with its artefact's own type**:

| Position | Bucket | M4 components | Workbook rows |
|---|---|---|---|
| 8 of 10 | automation | `Settings:Flow` → `Flow` → `FlowTest` (M4-S03); `ApexClass:TestDataFactory` → `ApexClass:CaseMilestoneService` → `ApexTrigger:CaseMilestoneTrigger` → `ApexClass:CaseMilestoneServiceTest` (M4-S05) | CWB-AUT-022 … 028 |
| 10 of 10 | SLA | `Settings:BusinessHours` (M4-S01) → `MilestoneType` → `EntitlementProcess` ×2 (M4-S02) → `EscalationRules:Case` (M4-S04) | CWB-AUT-013, 015–017, 019 |

**Verdict: no contradiction.** No permission set grants a field defined later; no routing component
precedes what it triggers. Within position 10 the intra-step order is right and is stated on the
rows: `MilestoneType` before `EntitlementProcess` (the `<milestoneName>` reference must bind, same
request), `Settings:BusinessHours` before both (the `<businessHours>` name must bind), and
`EscalationRules` last of everything it names.

**Two sequence observations that are not contradictions, recorded because a reader would otherwise
have to re-derive them:**

1. **Automation (8) reads SLA (10) — at run time only.** The position-8 flow looks up
   `BusinessHours` records by `Name` that the position-10 settings file creates, and stamps an
   `EntitlementId` from processes deployed at position 10. No *metadata* reference crosses
   backwards, which is why nothing fails at deploy and why `CWB-AUT-026` records the direction
   explicitly. The consequence is a **run-time** one across a multi-request deploy → **F-46**.
2. **The active-flow / Apex-test coupling.** `Settings:Flow`'s `enableFlowDeployAsActiveEnabled` is
   `true` and the flow is `<status>Active</status>`, so a **production** deploy runs the org's Apex
   tests (O-M4S03-02). The only Apex test in the build is `CaseMilestoneServiceTest`, which is
   `@IsTest(SeeAllData=true)` and asserts on org state — an active `SlaProcess`, and a Case that
   actually enters it (D-M4S05-04). Those come from position 10. Inside one Metadata API request
   all components land before tests run, so the single-request path is sound; a **split** deploy
   that ships position 8 ahead of position 10 will fail its own tests and roll back. → **F-45.**

---

## 5. Merged manifest (Step 5)

**`reports/MILESTONE-M4-package.xml`** — 6 `<types>` blocks, 8 members, `<version>67.0</version>`.

| Type | Members | From |
|---|---|---|
| `EntitlementProcess` | `First_Response_Premier`, `First_Response_Standard` | M4-S02 |
| `EscalationRules` | `Case` | M4-S04 |
| `Flow` | `Case_BeforeSave_StampEntitlementAndCalendar` | M4-S03 |
| `FlowTest` | `Case_BeforeSave_StampEntitlementAndCalendar_Test` | M4-S03 |
| `MilestoneType` | `First Response` | M4-S02 |
| `Settings` | `BusinessHours`, `Flow` | M4-S01, M4-S03 |

- **Version conflict: none.** All four step manifests declare `67.0`. (The build carries two API
  versions overall — M1/M2/M3-S02 manifests sit at 62.0 — but that is O-M3S03-01/F-31, decided at
  the M3 gate and out of M4's scope. The merged M4 manifest is uniformly 67.0, so there is nothing
  for this agent to escalate under `REFUSAL_NEEDS_HUMAN_REVIEW`.)
- **Member collisions: none.** No member appears in two steps. The two `Settings` members come from
  different steps but are different members, so they union into one block rather than colliding.
- **Files reaching no `<types>` block: 10, all of them Apex, all deliberate.**

### How this merged manifest treats the M4-S05 Apex members — say it plainly

**It does not carry them.** `artefacts/M4-S05/` holds `CaseMilestoneTrigger.trigger`,
`CaseMilestoneService.cls`, `CaseMilestoneServiceTest.cls` and `TestDataFactory.cls` with their four
meta siblings. None of them appears in `MILESTONE-M4-package.xml`, because **M4-S05 declares no
`package.xml` at all** and this merged manifest is the union of the step manifests in the milestone.

That is correct, and it is the contract, not an oversight: `standards/build-orchestration.md` § 4
borrowed-agent condition 2 forbids declaring an output the owning agent's Output Contract does not
name, and `apex-builder`'s nine numbered outputs include no manifest; § 5 **The Apex exception**
settles the collision by assigning the `ApexClass` and `ApexTrigger` members to the **build-level**
manifest step `M5-S05` (type `docs`, owned by `metadata-builder`, `depends_on M4-S05`). The step's
own always-on `manifest` check correctly recorded *skipped-not-applicable* naming M5-S05, rather
than failing.

**M4-S03 carries no Apex** — its three members (`Flow`, `FlowTest`, `Settings:Flow`) are all in the
manifest. The Apex exception applies to M4-S05 alone.

**The consequence, which the contract does not state and which the gate should:** `M5-S05` is
`pending`. Until it runs, **no manifest anywhere in this build carries the Apex**, so a
`--mode manifest` validation of `MILESTONE-M4-package.xml` deploys the entitlement processes, the
milestone type and the before-save flow **without the trigger that completes their milestones** —
precisely the half-build the milestone goal's second sentence warns against ("`CompletionDate` is
written by the M4-S05 trigger rather than the milestone reporting violated on a case that was
answered"). Mock deploy runs 1–4 used **source** mode, which copies the whole tree and therefore
*did* include the Apex; that is why run 4 reached 55 components. A manifest-mode run of this file
would deploy 8 members and no Apex. → **F-43.**

---

## 6. Acceptance tests (Step 6)

Six declared. Five runnable, **5/5 pass**. One `manual`, carried to § 7. Every command was run
**verbatim from the build directory** (`skills` symlink present); none was rewritten, no flag added
or removed, no path substituted. Every declared checker exists on disk — none was reported missing.

| # | Type | Command / assertion | Exit | Result |
|---|---|---|---|---|
| M4-T1 | `checker` | `python3 skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py --manifest-dir artefacts` | **0** | **PASS.** One INFO: the always-open `Severity 1 24x7` calendar — *"confirm it is not attached to entitlements that expect business-hour pauses."* This is the documented expected outcome after v1.0.1 scoped the rule (D-M4S01-01); it does not affect the exit code. **Answered:** no entitlement process names it — both name `US Support` (§ 3.1 check 1), which is O-M4S01-01's finding restated as a verified fact. Exactly one `<default>true</default>` calendar (`US Support`). |
| M4-T2 | `checker` | `python3 skills/admin/entitlements-and-milestones/scripts/check_entitlements_and_milestones.py --manifest-dir artefacts --strict` | **0** | **PASS.** `0 error(s), 0 warning(s), 2 info note(s)`. Both INFOs are W4 (no `<timeTriggers>`/`<successActions>`), which is the *intended* shape here — completion is driven by the M4-S05 trigger. The assertion `--strict` exists for is live: W3 (a `<businessHours>` name absent from the settings file) is a WARN that `--strict` promotes to a failure, and it did not fire — so the calendar cross-reference is genuinely asserted, not merely quiet. |
| M4-T3 | `checker` | `python3 skills/admin/escalation-rules/scripts/check_escalation_rules.py --manifest-dir artefacts` | **0** | **PASS.** `W1` (no rule in this file is active) — the *intended* state under Q47, not a defect. `2× I2`, `2× I3` (`minutesToEscalation 480 = 8h`). No ERROR: E2 (a `<businessHours>` child under a non-`Static` source) and E7 (an `assignedTo` that is not a queue developer name in the manifest) both clear, and E7 can only clear at build scope because the queue is M2-S04's. |
| M4-T4 | `checker` | `python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py --manifest-dir artefacts` | **0** | **PASS.** `scanned 4 Apex file(s) under artefacts: 0 ERROR, 0 WARN`. Asserts what the description claims: `CompletionDate` is written rather than `IsCompleted`, the DML is bulk-safe (one query, one DML), and a test class ships with it. |
| M4-T5 | `manifest` | Every `BusinessHours`, `EntitlementProcess`, `MilestoneType`, `Flow` and `EscalationRules` component in M4 appears in the milestone `package.xml` with a file behind it | — | **PASS.** All 8 merged members have a file; all 6 non-Apex deployable files have a member. The 10 Apex files are the documented Apex-exception carve-out (§ 5). 16/16 XML files parse. |
| M4-T6 | `manual` | Q27's two by-design post-save `OwnerId` writers described and non-contradicting | — | **Deferred to the checklist, § 7 line 7.** Not ticked by this agent. |

**Note on what a green checker does and does not mean here.** Four of these five run at
`--manifest-dir artefacts`, and each of the four prints a benign line and exits 0 against an *empty*
tree (the W09 class of vacuity the plan's own test descriptions document). Their exit codes carry an
assertion only because `check-outputs` confirmed the declared artefacts exist and are non-empty
before the tests ran, and because this run re-confirmed all 11 deployable files are on disk. That is
stated so the gate reader does not read "exit 0" as "something was checked" without the
precondition.

### Org-facing evidence already on file (not run by this agent)

`reports/MOCK-DEPLOY-M4.md` — four `checkOnly` runs by the operator against `sfskills-dev`. **Run 4:
55 components, 55 ok, 1 error** — the single failure being **F-28**, `support-noreply@acme.example is
an invalid From email address`, the known org-wide-address prerequisite already accepted as a named
deploy prerequisite at the M3 gate, and outside this build's power to fix. F-36, F-37 and F-38 are
closed at source and proven by the org. **This agent ran no `sf` command and no `mock_deploy.py`.**

---

## 7. Manual checklist for the gate (Step 7)

Seven lines: six from `tests/<step>/results.json` `skipped_manual[]` (one each from M4-S01, S02,
S03, S05; two from M4-S04) plus the milestone's own manual test. Each names its step, what the human
does, and what counts as a tick. **This agent ticks none of them.**

| # | From | What the human does | Ticks when |
|---|---|---|---|
| 1 | M4-S01 | Read `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml` | All three calendars are present and named: `EMEA Support` (Europe/London 08:00–18:00 Mon–Fri), `US Support` (America/New_York 08:00–20:00 Mon–Fri, org default) and `Severity 1 24x7`. *(Verifier note: all three are present and so named. The tick is the human's confirmation that they are the right three.)* |
| 2 | M4-S02 | List `artefacts/M4-S02/` | Exactly two `entitlementProcesses` files and exactly one `milestoneTypes` file (assumption A27); Premier carries `minutesToComplete` 240; both processes name a `<businessHours>` that is a `<name>` in M4-S01's settings file. *(Verifier note: all four sub-clauses hold as built. **Read it alongside decision item 3** — the clause is satisfied and the design behind it is still in question.)* |
| 3 | M4-S03 | Read the flow XML | It sets `Case.EntitlementId`, `Case.BusinessHoursId` and `Case.Priority`; the first two are null-guarded (A2) and **Priority is deliberately not**, on the two email origins, per the M3 gate's decision (2); the no-matching-account path is the documented fallback, not a fault. Plus the four `check_flow_governance.py` policy fields the checker reports by file rather than by field: `<description>` carries the `Owner:` marker and ≥ 60 characters, `<interviewLabel>` is present, `<apiVersion>` ≥ 59, `<runInMode>` is `DefaultMode`. *(Verifier note: all four policy fields confirmed present — `Owner: Service Operations`, interview label present, 67.0, `DefaultMode`.)* |
| 4 | M4-S04 | Sign off activation | A named owner activates the rule inside an agreed comparison window and records the first hour's escalation count. The checker's `W1` is the expected state, not a defect. **This line cannot be ticked at this gate** — it requires a sandbox and a named owner, neither of which exists yet. Sign it *outstanding*, with an owner and a date, as `standards/build-orchestration.md` § 3 permits. |
| 5 | M4-S04 | Read `Case.escalationRules-meta.xml` | The Tier 2 entry's `minutesToEscalation` is **480** (8 × 60), not 8; `businessHoursSource` is `Case` with **no** `<businessHours>` child; it reassigns to the queue developer name `Tier_2_Engineering`; the Severity 1 entry's `businessHoursSource` is `None`. *(Verifier note: all four confirmed as built. Weigh it with decision item 4 — the same 480 also sits on the Severity 1 entry, and that number is composed, not answered.)* |
| 6 | M4-S05 | Confirm identifier provenance | Every non-platform identifier in the emitted Apex is quoted from `skills/apex/entitlement-apex-hooks/references/examples.md` or the cited template, **and** `CaseMilestoneServiceTest` asserts `CompletionDate` is non-null after the trigger runs. *(Verifier note: the org compiled all four classes and the trigger clean at mock-deploy run 4, which settles the provenance half far more strongly than a read can. The assertion half is a read of the test body and remains the human's.)* |
| 7 | M4 (milestone) | Read `artefacts/M3-S04/owner-writer-map.md` alongside `artefacts/M4-S04/escalation-activation-runbook.md` | Q27's two by-design post-save `OwnerId` writers (Omni-Channel and the escalation rule) are both described and neither contradicts the assignment rule. *(Verifier note: Omni-Channel is M3-S05, which is **blocked** and accepted as a known gap at the M3 gate — so one of the two writers named in this line does not exist in the build. Tick the escalation half; record the Omni-Channel half as not-applicable-this-phase rather than ticked.)* |

No line states an unobservable outcome; every one names something a reader can check or a named
owner can sign as outstanding.

---

## 8. Findings (F-39 … F-48)

Ids continue from F-38. Severity follows the build's convention: HIGH = a human must decide before
deploy; MEDIUM = decide before go-live; LOW = record and revisit.

---

### F-39 — HIGH — The merged M4 manifest cannot deploy itself into an org that does not already have Entitlement Management enabled

**Composed from:** O-M4S02-01 (step scope) + the merged manifest (milestone scope) + mock-deploy run 4.

`settings/Entitlement.settings-meta.xml` carrying `enableEntitlements` is declared in **no step's**
`outputs[]` anywhere in `plan.json` — O-M4S02-01 established that at M4-S02's scope and named it a
gate item. What no step could see, and what this merged manifest makes concrete, is that the
dependency is **wider than M4-S02's own two files**:

| Component | What it needs `enableEntitlements` for |
|---|---|
| `EntitlementProcess` ×2, `MilestoneType` | The components themselves — inert or rejected without it |
| `Flow:Case_BeforeSave_StampEntitlementAndCalendar` | `$Record.EntitlementId` and the `Entitlement` object in `Get_Active_Entitlement` |
| `ApexClass:CaseMilestoneService`, `…Test`, `ApexTrigger:CaseMilestoneTrigger` | The `CaseMilestone` and `SlaProcess` sObjects |

Three of M4's five steps, not one. **Predicted deploy-time error** per
`skills/devops/deployment-error-diagnosis`: `INVALID_TYPE: sObject type 'Entitlement' is not
supported` on the flow's record lookup, and a feature-not-enabled rejection on the
`EntitlementProcess` components — a failure whose message points at the flow rather than at the
missing switch, which is exactly the class of error that costs an afternoon.

**Why mock deploy run 4's 55/55 does not clear this.** `sfskills-dev` already has the feature on.
Run 4 proves the artefacts are correct; it does not prove the manifest is self-sufficient. A clean
target org fails.

**Remedy (a human's choice, not this agent's):** (a) amend some M4 step's `outputs[]` to declare
`settings/Entitlement.settings-meta.xml` and rebuild, or (b) record enabling Entitlement Management
in Setup as a named deploy prerequisite alongside F-28, with an owner and a date. Option (b) is the
cheaper and is the same shape the M3 gate already used for F-28. `enableMilestoneStoppedTime` rides
in the same unowned file and, per `gotchas.md` #10, wants turning on *before* go-live rather than
after the first dispute — so option (b) should name both switches, not one.

---

### F-40 — HIGH — Milestone M4's own `goal` is not met: a Premier EMEA case's first-response clock runs on **US Support** hours, not EMEA

**Composed from:** O-M4S02-02 (which records the divergence) + `plan.json.milestones[M4].goal` (which no step reads).

`plan.json` states M4's goal as:

> *"Given a Premier case created at 17:00 London time on a Friday (Q39), when the first-response
> clock is read, then it is running on the **EMEA calendar**, shows 4 business hours remaining, does
> not tick over the weekend…"*

As built, `First_Response_Premier` carries `<businessHours>US Support</businessHours>` on the
process **and** on its `<milestones>` block, and a milestone's own `<businessHours>` is the most
specific of the three sources the engine consults. So the EMEA calendar M4-S03's flow stamps onto
`Case.BusinessHoursId` is **overridden for milestone timing** and reaches only the escalation clock,
whose `businessHoursSource` is `Case`.

Worked against the goal's own scenario: 17:00 Friday London is 12:00 New York. `US Support` is
08:00–20:00 New York, so 240 business minutes expire at **16:00 New York = 21:00 the same Friday
London** — after EMEA close, on the day of arrival, weekend untouched. The goal's three clauses
("running on the EMEA calendar", "4 business hours remaining", "does not tick over the weekend") are
not what the artefacts produce.

`business-hours-and-holidays/references/gotchas.md` #5 names this exact failure as the one it exists
to prevent: *"a Case with a regional calendar can escalate on the regional clock while its
first-response milestone counts on the process calendar."* The build reproduces it.

**Why this is a finding and not a defect anyone failed to notice.** O-M4S02-02 records it precisely
and names three remedies; M4-S02's `deploy-order.md` § 4.4 calls it "a real tension". What no step
could do is compare it to the milestone's own acceptance goal, because a step does not read
`milestones[].goal`. That comparison is this agent's job, and the answer is that the goal is not
met. Nothing downstream — not a checker, not the mock deploy — will ever say so.

**Remedies, from O-M4S02-02, unchanged and none of them this agent's:** (a) accept the divergence
and record at the gate that EMEA Premier cases have two clocks on different calendars; (b) split
each tier into a US and an EMEA process — four processes, contradicting A27's fixed count of two, a
re-plan; (c) re-point M4-S04's entry 2 to `businessHoursSource = Static` on `US Support` so both
clocks agree — contradicting Q43's answered value, and making every EMEA case escalate on New York
hours. **A fourth, not in O-M4S02-02 and cheaper than (b):** amend `plan.json`'s M4 goal to state
what the build actually promises, if (a) is chosen — a goal that describes a behaviour nobody built
will mis-set every later reader's expectation, including M5's UAT script.

---

### F-41 — MEDIUM — Nothing in the build selects `First_Response_Premier` over `First_Response_Standard`

The two processes differ only in `minutesToComplete` (240 vs 720). Which one a case enters is
decided by the `SlaProcessId` on the `Entitlement` record its Account holds — and **no step in this
build creates an `Entitlement`, an `EntitlementTemplate`, or anything that binds
`Account.Support_Tier__c` to one process rather than the other.** The flow's `Get_Active_Entitlement`
filters on `AccountId` and `Status = 'Active'` with `getFirstRecordOnly true` and **no tier filter**;
an Account with two active entitlements gets whichever the query returns first.

`workbook/01-objects-and-fields.md` CWB-OBJ-009 asserts the binding ("`Support_Tier__c` … is what
selects *which* of these two processes an account's entitlement points at") and M4-S02's
`deploy-order.md` § 5 records that `EntitlementTemplate` is "not in this phase" — so both halves are
written down, in two different files, and neither says the binding is unimplemented.

**Consequence:** REQ-040 ("Premier accounts get a first response within 4 business hours") is
delivered as *metadata that can express the promise*, not as a mechanism that applies it. It holds
only once a human has created each Account's `Entitlement` pointing at the right process.

**Remedy:** record entitlement creation as a data/Setup prerequisite with an owner (cheapest, and
honest), or scope an `EntitlementTemplate` + a tier-aware assignment in a later phase.

---

### F-42 — MEDIUM — The flow's `Priority` values resolve against nothing in this build

`Assignment_Priority_High` writes `<stringValue>High</stringValue>` and `Assignment_Priority_Medium`
writes `Medium`. **No `standardValueSets/CasePriority` exists anywhere under `artefacts/`** —
verified by exhaustive grep, and independently recorded by D-M4S03-03 and `M3-S03`'s
`web-to-case-form-contract.md` § 7.

The contrast with `CaseOrigin` is the point: M1-S01 *did* ship
`standardValueSets/CaseOrigin.standardValueSet-meta.xml`, because the build changes it. It did not
ship `CasePriority`, because the build does not — which is legitimate, and is why this is classed
**unassertable** rather than **unresolved**. But it means four separate places in the build now
depend on the target org's untouched `CasePriority` values and **nothing can assert them**: this
flow's two writes, M3-S03's two `<casePriority>Medium</casePriority>` intake defaults, M3-S01's
`Priority_Required_On_Agent_Save`, and `CaseMilestoneServiceTest.caseOverrides`' `'Priority' =>
'Medium'`. If a target org has restricted or renamed `CasePriority` — a common hardening step — the
flow writes an invalid value and the insert fails.

**Remedy:** either declare `standardValueSets/CasePriority` as an M5 output so the build asserts the
three values it relies on, or record "the target org's `CasePriority` still carries `High` and
`Medium`" as a one-line pre-deploy check. **This is also decision item 6** — the value *mapping*
(which case gets which value) is a separate, unanswered question.

---

### F-43 — MEDIUM — Between now and M5-S05, no manifest in this build carries M4-S05's Apex

See § 5. The Apex exception is correctly applied and M4-S05's `manifest` check correctly recorded
*skipped-not-applicable*. The gap is one of **timing**: `M5-S05` is `pending`, so a manifest-mode
validation today deploys the SLA clocks without the trigger that stops them. Source-mode mock
deploys hid this, correctly, by copying the tree whole.

Same shape as **F-18** (M2's stale merged manifest before any manifest-mode deploy), and it should
be read alongside it: this build has now twice produced a merged manifest whose coverage differs
from what the operator actually validated.

**Remedy:** none required for the gate. State on the merged manifest, and in M5's plan, that
`MILESTONE-M4-package.xml` is deliberately Apex-free and that `M5-S05` is the step that closes it.
If anyone wants a manifest-mode dry run of M4 *before* M5-S05, they must hand-add the four
`ApexClass` and one `ApexTrigger` members — which this agent did **not** do, because inventing
members the contract assigns to another step is exactly what § 4 condition 2 forbids.

---

### F-44 — MEDIUM — The escalation's `assignedToTemplate` notification may reach nobody

**Composed from:** M4-S04 `deploy-order.md` § 3 **U3** (which asks the question) + `artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml` (which answers it).

Both escalation actions set `<assignedTo>Tier_2_Engineering</assignedTo>` with
`<assignedToTemplate>case_intake/Case_Escalated_To_Tier2</assignedToTemplate>`. That template mails
the **new owner** — the Tier 2 queue. But:

```xml
<Queue>
    <doesSendEmailToMembers>false</doesSendEmailToMembers>
    <name>Tier 2 Engineering</name>          <!-- no <email> element -->
```

No queue email address, and member notification off. U3 records this as UNVERIFIED at M4-S04's
scope; the queue is M2-S04's artefact, so only a milestone-or-wider read can close it — and the
answer is that the queue has no mailbox. The M2 gate already noted this from the other side
("checklist line 4 (Tier 2 mailbox) NOT ticked — artefact has no `<email>`"), and D-M2S04-02
deliberately refused to invent an address. **Nobody has composed the two.** As built, REQ-023's
"Tier 2 … receive Support cases that go untouched for 8 business hours" is delivered as an
**ownership change Tier 2 must discover from a list view**, not as a notification — which is
consistent with REQ-023's own wording ("pick work from a list") but not with REQ-033's ("Tier 2
receives a **named handover notice**").

**Remedy:** name a Tier 2 mailbox and add `<email>` to the queue (a one-line M2 amendment, which
re-opens an accepted milestone — weigh that), or accept that the handover notice reaches only the
outgoing owner and record REQ-033 as half-delivered.

---

### F-45 — MEDIUM — A split deploy that ships position 8 before position 10 will fail its own Apex tests

See § 4 observation 2. `Settings:Flow` sets `enableFlowDeployAsActiveEnabled true`, the flow is
`Active`, and a **production** deploy of an active flow runs the org's Apex tests. The build's only
test, `CaseMilestoneServiceTest`, is `@IsTest(SeeAllData=true)`; its `requireActiveProcess()` asserts
an active `SlaProcess` exists and its first test method asserts an open `First Response`
`CaseMilestone` was generated for a Case it inserts. Both depend on the position-10 entitlement
process being in the org and active.

O-M4S03-02 records the active-flow/Apex-test coupling; D-M4S05-04 records the test's org
prerequisites. **Neither composes them with the deploy-order buckets**, and the composition is where
the risk lives: inside one Metadata API request everything lands before tests run and the path is
sound; across two requests ordered by the ten-slot sequence, position 8 runs tests that position 10
has not yet satisfied, and the deploy rolls back for a reason that names the Apex rather than the
ordering.

*(A smaller observation inside the same class, not raised to its own finding:
`requireActiveProcess()`'s SOQL is `SELECT Id, Name FROM SlaProcess WHERE IsActive = true LIMIT 1` —
it does **not** filter on the process carrying a `First Response` milestone, though its assertion
message says a process "with a `First Response` milestone must exist". The over-claim is caught one
assertion later by the `before.isEmpty()` check, so the test still fails loudly rather than
silently; the message is imprecise, not the logic.)*

**Remedy:** deploy M4 as one request, or state in the deploy-order note that positions 8 and 10 of
this milestone must travel together to production.

---

### F-46 — LOW — The position-8 flow reads by name the `BusinessHours` records position 10 creates

No metadata reference crosses backwards (§ 4 observation 1), so nothing fails at deploy. But
`Get_EMEA_Support_Calendar` and `Get_US_Support_Calendar` filter on `Name` at **run time**. In a
split deploy, any Case created between request 8 and request 10 gets **no** `BusinessHoursId`
stamped — and the escalation rule's entry 2 (`businessHoursSource = Case`) then falls back to the
org default for those cases, silently. M4-S04's `deploy-order.md` **U2** asks exactly this question
("what entry 2 does when `Case.BusinessHoursId` is null") and leaves it UNVERIFIED.

**Remedy:** the same as F-45 — one request, or an explicit statement that 8 and 10 travel together.
The two findings share one remedy and should be decided once.

---

### F-47 — LOW (as deployed) / HIGH (on activation) — The Billing-queue mail loop

This is **decision item 1** and is documented in full at O-M4S04-01; it is listed here so the
finding register is complete. `notifyCaseOwner` is `true` on both escalation actions; the case owner
at escalation time is whichever queue M3-S04's assignment rule chose; the `Billing` queue's `<email>`
is `billing@acme.example`; and M3-S03 configures that same address as a live Email-to-Case routing
address. An escalation notification to a Billing-owned case therefore posts into an intake address,
creating a new case that escalates 480 minutes later and posts again.

**Severity is split deliberately.** The rule ships `<active>false</active>`, so **nothing loops on
deploy** — as deployed this is LOW. It becomes HIGH the moment checklist line 4 is signed. F-36's
fix is what made it real: before `notifyToTemplate` was added, `notifyCaseOwner` could not send mail
at all.

Three remedies, verbatim from O-M4S04-01, at decision item 1.

---

### F-48 — LOW — Documentation staleness: `traceability.md` still reports 3 RTM orphans; there are now 0

`traceability.md` § "Linter result — after M4-S05" states: *"The **3** orphans that remain are all
`M4-S05`'s own Apex classes."* Re-run by this agent, verbatim, from the build directory:

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md --manifest-dir artefacts
traceability.md: 47 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 0 warning(s)
EXIT=0
```

**0 orphans.** The fix landed today as `0c585e185` — `check_rtm.py` v1.1.5, *"a row's
`artefact_paths` entries cover the components their files produce (Apex classes shipped by a
one-row-per-requirement step; M4-S05 doc-keeper: 3 false orphans → 0; live build 47 rows, 0
orphans)"*, gotcha 19. This is the fourth instalment of the same skill-depth fix
(v1.1.2 → v1.1.3 → v1.1.4 → v1.1.5), each closing false orphans this build's doc keeper reported.

**This closes decision item 9: there is nothing for the gate to decide.** The prose in
`traceability.md` is now the only thing stale, and it is a rendered-by-hand section the doc keeper
will rewrite at its next touch. No rebuild, no amendment.

---

## 9. The nine decision items for the `milestone:M4` gate

Presented together, as asked. Each carries this agent's recommendation. **A recommendation is not a
decision** — every one of these needs a human, and several need a *named* human this build does not
have.

---

### 1. O-M4S04-01 — the R2 Billing-queue mail loop, with its three remedies

**The exposure is confirmed real** (F-47), and it is an **activation** prerequisite, not a
deployment defect — the rule ships inactive.

| Option | What it needs | This agent's read |
|---|---|---|
| **a.** Exclude Billing-owned cases from escalation (a third entry, or a criterion on entry 2) | An answer saying finance cases do *not* escalate to Tier 2 Engineering. `requirement.md` L16 says "anything untouched", unqualified | The cleanest technically, the most likely to be *wrong* — it silently drops a whole queue out of the SLA the requirement states without qualification |
| **b.** Drop `notifyCaseOwner`, rely on `assignedToTemplate` alone | Accepting that the notify half of Q45 may reach nobody | **Weakened by F-44**: the `assignedToTemplate` recipient is the Tier 2 queue, which has no mailbox. Choosing (b) today means *neither* notification reaches anyone |
| **c.** Give the `Billing` queue a notification address that is not an intake address | A Finance mailbox nobody has named | Smallest blast radius, one `<email>` element, no behaviour change to the SLA |

**Recommendation: (c), paired with F-44's Tier 2 mailbox, as one decision.** Both are the same
question — *which mailboxes do these queues notify?* — and both were deferred for the same reason
(D-M2S04-02 refused to invent an address, correctly). Decide them together, get two addresses from
the support manager, and amend M2-S04 once. If no address is forthcoming, choose **(b)** and record
explicitly that escalation is a silent ownership change this phase, so M5's UAT script tests for a
list-view handover rather than an email.

---

### 2. O-M4S02-01 — Entitlement settings owned by no step

`enableEntitlements` (and `enableMilestoneStoppedTime`, and `enableEntitlementVersioning`) live in
`settings/Entitlement.settings-meta.xml`, which **no step's `outputs[]` declares**. F-39 widens the
blast radius from M4-S02's two files to three of M4's five steps.

**Recommendation: option (b) — record it as a named deploy prerequisite, not a plan amendment.**
Three reasons. It is the same shape the M3 gate already accepted for F-28, so the build has a
precedent and a place to keep it. Enabling Entitlement Management in Setup is a one-time,
org-lifetime action that does not belong in a per-release manifest. And amending an M4 step's
`outputs[]` now would force a rebuild of a `documented` step for a file that changes nothing about
the artefacts already proven.

**What the gate must record if it takes this option:** a named owner, a date, and **both** switches —
`enableEntitlements` before anything in M4 deploys, and `enableMilestoneStoppedTime` before go-live
rather than after the first SLA dispute (`gotchas.md` #10).

---

### 3. O-M4S02-02 — the Q51 calendar divergence

The one that matters most, because it is the one the milestone's own goal contradicts (F-40). An
EMEA case's first-response milestone counts on `US Support` (New York 08:00–20:00) while its
escalation timer counts on `EMEA Support` (London 08:00–18:00). Two SLA clocks on one case, pausing
on different holidays, disagreeing about elapsed time.

**Recommendation: (a) accept the divergence for this phase, and amend M4's `goal` to match.** The
reasoning: (b) is a re-plan that contradicts A27 and quadruples the process count for a two-tier
promise; (c) contradicts Q43's answered value and would make every EMEA case escalate on New York
hours, which is worse than the divergence it fixes. (a) costs nothing to build and everything to
*forget* — which is precisely why the goal text must change with it. A goal that promises an EMEA
clock nobody built will mis-set M5's UAT script, the release note, and the first support manager who
reads it.

**If the Process Owner says EMEA Premier must genuinely count on London hours, this is a re-plan**,
and it is better discovered at this gate than in UAT.

---

### 4. D-M4S02-02 (720) and D-M4S04-02 (480) — the two placeholder numbers

Two numbers nobody answered, derived by different routes:

| Number | Where | How it was derived | What it would take to confirm |
|---|---|---|---|
| **720** | `First_Response_Standard.minutesToComplete` | Q38 says "1 business day"; nothing converts a business day to minutes; `US Support` is 08:00–20:00 = 12 open hours = 720. Two rival readings were named and rejected as equally unsourced: 480 (a conventional 8-hour day, which would also collide numerically with the escalation threshold) and "by the end of the next business day" (not expressible — the model carries an integer minute target, no calendar-date element) | One integer, one file. The Process Owner says what "1 business day" means contractually |
| **480** | `minutesToEscalation` on **both** escalation entries | Q46 binds 480 for the **Tier 2** entry only. `requirement.md` L16 gives one threshold; L18 says only that Severity 1 "never pauses" — it gives Severity 1 no *faster* threshold, and no clarification asks for one. Entry 1 therefore carries the same 480; the difference between the entries is the **clock**, not the number | One integer, one file. Does a Severity 1 outage escalate sooner than 8 hours? |

**Recommendation: confirm both at the gate; neither is a blocker.** The builder was right to refuse
to invent either — a builder-composed number reads as a customer commitment nobody made. Two things
worth putting in front of the Process Owner in the same breath: the 720 derivation is **coupled to
the `US Support` calendar's 12-hour day**, so if decision item 3 ever moves Standard onto EMEA hours
(10 open hours) the "1 business day" figure becomes 600, not 720 — one decision silently changes the
other. And a Severity 1 outage escalating on the *same* 480 as a routine case is the reading most
likely to surprise a support manager reading the rule for the first time.

---

### 5. D-M4S01-02 — the seeded holidays and the Q90 owner

Two halves, both open:

- **The 14-holiday seed** (6 on `US Support`, 9 on `EMEA Support`, computed for the 12 months from
  2026-09-12) is a **placeholder marked UNCONFIRMED**. No clarification anywhere supplies Acme's
  actual dates — Q39 established only that each region observes its own set. Every weekday was
  computed rather than recalled, which is the right restraint, and it is still not Acme's list.
- **Q90's owner** answered *who is accountable* (Service Operations) and *how often* (one deploy per
  year, each Q4) but **not which named individual**. The runbook's owner row is explicitly `OPEN`.

**Recommendation: the owner half is the one to close at this gate; the holiday list can follow.**
An unnamed owner is the more corrosive of the two — a calendar with wrong holidays fails visibly on
a known date, while a calendar with no owner silently stops pausing in a year and nobody is
accountable for noticing. Name the individual at this gate; give them the runbook's § 4 yearly
procedure and a date to replace the seed with Acme's real list before production.

**Do not let the seed deploy to production as-is.** It is the right shape and the wrong data, and it
is convincing enough to be mistaken for confirmed by anyone who reads the calendar rather than the
runbook. This is the same restraint D-M4S01-02 exercised in refusing to invent a name — carry it one
step further and refuse to let a placeholder cross into production unlabelled.

---

### 6. D-M4S03-03 — the Priority mapping

`Severity 1 → High`, `Premier → High`, everything else → `Medium`. No answered clarification states
any of the three rows. Their grounding, weakest last:

| Row | Grounding | Strength |
|---|---|---|
| `Severity__c = Severity 1` → `High` | `requirement.md` L18, the only unconditional urgency statement in the requirement; `Severity__c` has exactly one value | Strong |
| everything writable → `Medium` | Matches M3-S03's own intake default | Strong, by consistency |
| `Support_Tier__c = Premier` → `High` | Q38's 4-hour-vs-1-day promise, plus the M3 gate's decision (2) naming `Support_Tier__c` as a derivation input — a rule that never read it would not implement the approved option | **Weakest.** Nothing says a Premier case is *urgent*; only that it is contractually *faster*. The builder says so itself |

**Recommendation: confirm the first two, and put the Premier row specifically to the Process Owner.**
Conflating "contractually faster" with "more urgent" is a real design claim: it means a routine
Premier question outranks a Standard customer's production problem in every priority-sorted list
view and every report M5 builds. If the answer is that tier should not drive Priority, the fix is to
delete one `<rules>` condition — and the SLA difference still lands, because it comes from the
entitlement process, not from Priority.

**Decide this together with F-42.** Item 6 is *which value*; F-42 is *whether the target org still
carries that value at all*. Answering one without the other leaves the flow half-proven.

---

### 7. D-M4S05-02 — the completion-signal proxy

D10 settled the **mechanism** (an after-update Apex trigger stamping `CompletionDate`). No
clarification settles the **event**. Q50's recorded answer names *"the first outbound
`EmailMessage`"*. What was built is narrower and Case-only: the milestone completes when a Case
**leaves `Status = New`** — the one transition both business processes share, and the transition the
cited skill's Example 1 documents.

The gap, stated honestly by the builder: *a case can leave `New` without a customer-facing reply (an
agent triaging and escalating it untouched), and an agent can reply without leaving `New`.* Both
error directions are live, and the first one — escalation to Tier 2 marks first response complete —
is the one that will happen constantly, because M4-S04's escalation *changes ownership* and an agent
handling that case will move it off `New`.

**Recommendation: raise this above the other eight.** It is the only item where the built behaviour
can make a *false SLA claim* — a milestone reported met on a case no customer heard from. Every
other item is a value to confirm or a prerequisite to name.

Two things make it cheap to fix if the Process Owner wants Q50's literal signal: the rule lives in
one `@TestVisible` constant (`OPENING_STATUS`), so changing *which status* is a one-line edit; but
moving to the first outbound `EmailMessage` is a **different artefact** — an after-insert trigger on
`EmailMessage` filtered to `Incoming = false` — which this step's `outputs[]` does not declare and
which is therefore a plan amendment plus a rebuild, not an edit.

**If the answer is "accept the proxy this phase"**, record it as an explicit, dated acceptance with
the false-positive direction named, and put a line in M5's UAT script that watches for milestones
completed on cases with no outbound email.

---

### 8. D-M4S05-03 — the two-file trigger shape

The trigger calls `CaseMilestoneService` directly rather than through a `TriggerHandler` subclass.
The builder's reasoning is sound and mechanically verified: a plan-wide search found
`TriggerControl = 0`, `ApplicationLogger = 0`, `Trigger_Setting__mdt = 0`, `TriggerHandler = 1` — the
one occurrence being this step's own `templates[]` citation, which is an instruction to *read* the
file, not to deploy it. A handler extending `TriggerHandler` **would not compile** in the org this
build produces.

What the shape costs, named rather than left implicit: no recursion guard, no depth counter, no
`skipOnce()`, no `TriggerControl` kill switch to disable the trigger from Setup without a deploy.
What is **not** missing is the guard that matters in this domain: `CompletionDate = NULL` in the
query means a second pass finds nothing, and `skipsAMilestoneThatIsAlreadyCompleted` asserts it.

**Recommendation: accept for this phase. This is the weakest of the nine items and should take the
least gate time.** The idempotency guard is domain-correct and arguably stronger than a recursion
counter for a trigger that fires once in a Case's life; the trigger does no DML on `Case`, so it
cannot re-enter itself; and the alternative — shipping four framework classes nobody asked for —
enlarges the deploy for a benefit the build cannot use. Record it as a **planner v6 backlog item**
(a shared "Apex foundations" step owning `TestDataFactory`, `TriggerHandler`, `TriggerControl` and
`ApplicationLogger`, with every Apex step depending on it) rather than as an M4 remedy. D-M4S05-05
already names that step for a different reason (the factory would collide if a second Apex step
shipped its own copy) — **one backlog item closes both.**

---

### 9. The RTM's three residual orphans — **CLOSED; nothing to decide**

See F-48. `check_rtm.py` v1.1.5 landed today (`0c585e185`) and the build-scope run now reports
**47 rows, 0 coverage gaps, 0 orphans, 0 errors, 0 warnings**, exit 0. The three `ApexClass` orphans
(`CaseMilestoneService`, `CaseMilestoneServiceTest`, `TestDataFactory`) were a checker limitation,
they were correctly dispositioned `REVIEW` rather than papered over, and the fix went into the skill
rather than into the matrix.

**Recommendation: record the closure and move on.** The only residue is stale prose in
`traceability.md`, which the doc keeper rewrites at its next touch. Worth one sentence at the gate,
because it is the fourth instalment of one skill-depth fix (v1.1.2 → v1.1.5) driven entirely by this
build's doc-keeper runs, and that is the flywheel producing exactly what it is for.

---

## 10. Requirement closure (Step 7 / traceability)

M4 closes **ten** requirements. Ids and status as `traceability.md` carries them:

| REQ | Step | Artefact | RTM status | Verifier note |
|---|---|---|---|---|
| REQ-038 | M4-S01 | `Settings:BusinessHours` | In UAT | Closed as metadata. The "Severity 1 runs 24/7" half is carried operationally by M4-S04's `businessHoursSource None`; the calendar itself is unconsumed (O-M4S01-01) |
| REQ-039 | M4-S01 | `holiday-maintenance-runbook.md` | In UAT | **Presence only, not content** — the RTM says so itself. Decision item 5 |
| REQ-040 | M4-S02 | `EntitlementProcess:First_Response_Premier` | In Build | Metadata complete; **F-40** (wrong calendar for EMEA) and **F-41** (no selection mechanism) both bear on it |
| REQ-041 | M4-S02 | `EntitlementProcess:First_Response_Standard` | In Build | As above, plus the 720 placeholder (decision item 4) |
| REQ-042 | M4-S02 | `MilestoneType:First Response` | In Build | Closed. One shared identity serving both tiers, as A27 fixed |
| REQ-043 | M4-S04 | `EscalationRules:Case` | In UAT | Closed as metadata, **inactive by design** (Q47). Decision item 1 and F-44 both bear on it |
| REQ-044 | M4-S05 | `ApexTrigger:CaseMilestoneTrigger` | In UAT | Closed as mechanism; **decision item 7** questions the signal it fires on. The RTM row itself records Q50's divergence |
| REQ-045 | M4-S03 | `Flow:Case_BeforeSave_StampEntitlementAndCalendar` | In UAT | Closed. Also closes **F-32** from M3 (§ 3.3) |
| REQ-046 | M4-S03 | `FlowTest:…_Test` | In UAT | Closed, over two org round-trips (D-M4S03-01). **The skill fix is still pending** — this is the one flywheel record in M4 that cannot cite a closing commit |
| REQ-047 | M4-S03 | `Settings:Flow` | In UAT | Closed. F-45 and O-M4S03-02 bear on *when* it deploys |

**Consumed from earlier, accepted milestones:** REQ-008 / REQ-009 (`Account.Region__c`,
`Support_Tier__c`, M1-S01), REQ-023 (`Queue:Tier_2_Engineering`, M2-S04), REQ-033
(`EmailTemplate:case_intake/Case_Escalated_To_Tier2`, M3-S02), REQ-034 (the two routing addresses,
M3-S03). All resolve.

**Still open across the build, unchanged by M4:** REQ-022's push half (M3-S05 blocked on Q32–Q35,
accepted as a known gap at the M3 gate), and the 25 deferred clarifications whose owners and dates
M5's gate will ask for.

---

## 11. Optional validate-only command — **for the human, and this agent did not run it**

This agent ran **no** `sf` command, **no** `mock_deploy.py`, and made **no** org contact of any kind.

The build is `design-only` with no org on file. The operator's own dry runs used
`scripts/mock_deploy.py` against the alias `sfskills-dev`; that script is the layer's sanctioned
org-facing check and it is the **human's** to run (`standards/build-orchestration.md` § 5). For a
**sandbox** target the validate-only form is:

```bash
# OPTIONAL — human-run. This agent did not run it and will not.
sf project deploy start \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M4-package.xml \
  --dry-run --target-org <sandbox-alias>
```

For a **production** target the command is different and naming the right one matters — offering the
sandbox form for production sends the human into an error that has nothing to do with their build:

```bash
# OPTIONAL — human-run. Production only. Requires Apex tests; returns a job id for a later quick deploy.
sf project deploy validate \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M4-package.xml \
  --target-org <production-alias>
```

**Three things to know before running either, none of which the command will tell you:**

1. This manifest **carries no Apex** (§ 5, F-43). A manifest-mode run deploys the SLA clocks without
   the trigger that stops them.
2. The target org must already have **Entitlement Management enabled** (F-39). A clean org fails,
   and the error will point at the flow.
3. The production form runs Apex tests, and this build's only test needs an **active `SlaProcess`**
   the same deploy is creating (F-45).

---

## 12. The `set-milestone` invocation

```bash
python3 scripts/build_plan.py set-milestone \
  .sfskills/builds/case-onboarding/plan.json M4 \
  --status verified \
  --report-path reports/MILESTONE-M4-REPORT.md
```

`verified` is the recording for both `ready-for-gate` and `ready-with-findings`. **It is a statement
about what the checks found, not an approval.** `milestones[].status` and `report_path` are plan
bookkeeping; the gate record stays empty until a human writes it. This is the only write this agent
made to `plan.json`, it was made through the subcommand, and no JSON was hand-edited.

---

## 13. The gate line — printed, never run

```bash
python3 scripts/build_plan.py gate \
  .sfskills/builds/case-onboarding/plan.json milestone:M4 approve \
  --by "<name>"
```

Reject, on the same terms:

```bash
python3 scripts/build_plan.py gate \
  .sfskills/builds/case-onboarding/plan.json milestone:M4 reject \
  --by "<name>" --notes "<why>"
```

**`gate` is the only writer of a gate decision and a human is the only decider.** § 3 will check
this command against three conditions, all of which hold today:

| Condition | State |
|---|---|
| `plan` gate approved | ✓ 2026-09-05T19:35:19Z |
| `milestone:M3` approved | ✓ 2026-09-12T06:24:17Z |
| Every step in M4 `documented`, or `blocked` with a recorded reason | ✓ all five `documented`; **no blocked step, so approving accepts no step-level gap** |

The gaps this gate accepts are the ten findings and the nine decision items above, not a missing
step. That distinction is worth stating: M3's gate was signed over a blocked step; M4's is not.

---

## 14. Files this run wrote, and nothing else

| Path | What |
|---|---|
| `reports/MILESTONE-M4-REPORT.md` | this report — written, not rendered |
| `reports/MILESTONE-M4-package.xml` | the merged milestone manifest |
| `envelopes/M4/2026-09-12T09-08-11Z.json` / `.md` | this run's own envelope and its markdown twin |
| `plan.json` | `milestones[M4].status` and `.report_path`, via `set-milestone` only |

**Not touched:** any artefact, any `tests/<step>/results.json`, any step status, any gate record,
`decisions.md`, `traceability.md`, the workbook, `PLAN.md`, `CLARIFICATIONS.md`, or any file outside
this build directory.

**Declared persistence deviation.** `agents/_shared/DELIVERABLE_CONTRACT.md` also calls for a
markdown/JSON pair at `docs/reports/milestone-verifier/<run_id>.{md,json}`. This invocation scoped
writes to the build directory, which is the `--no-persist` case: the build-scoped envelope under
`envelopes/M4/` and its markdown twin carry the same content, and the structured envelope is
returned in the run output. Recorded here rather than left as a silent omission.

---

## 15. Process Observations

### Healthy

- **Three of five blocks were closed at a skill, not at an artefact** — D-M4S01-01 (`admin/business-hours-and-holidays` v1.0.1), D-M4S02-01 (`admin/entitlements-and-milestones` v1.1.2), D-M4S04-01 (`admin/escalation-rules`, the F-36 rule). In two of the three, the file that was rejected is the file that now passes, **byte-identical, SHA-256 confirmed**. That is the flywheel doing what it is for, and it is rare enough to name.
- **The builders refused to invent, repeatedly and consistently.** No fabricated holiday owner (D-M4S01-02), no invented Severity 1 threshold (D-M4S04-02), no second email template (D-M4S04-04), no Tier 2 mailbox address (D-M2S04-02, held across milestones), no `WorkflowAlert` that exists in no step (D-M4S02-01's rejected repair A). Each refusal is recorded with its reasoning and its rejected alternatives. The build's placeholders are all *labelled* placeholders.
- **The two rejected repairs in D-M4S01-01 were verified on scratch copies outside the build directory and never applied.** Proving a repair would pass and declining to apply it is the discipline the block exists to enforce.
- **`CaseMilestoneService` is genuinely good Apex**: one query, one DML, the three-clause `WHERE` doing selection and idempotency at once, `Database.update(…, false)` with the results loop actually iterated, `WITH USER_MODE` stated at 67.0 where it is redundant precisely so a version downgrade cannot change behaviour silently, and a comment explaining why `after update` is a correctness requirement rather than a style choice. `check_entitlement_apex_hooks.py` reports 0 ERROR / 0 WARN, and so it should.
- **Cross-referential checkers are declared at the scope where they can actually assert.** `check_escalation_rules.py` at `scope: build` (E7 needs M2-S04's queue) and `check_entitlements_and_milestones.py --strict` at `scope: build` (W3 needs M4-S01's settings file) — both with the fixture evidence for *why* in the test description. § 5's cross-referential-checker rule is being followed rather than merely cited.

### Concerning

- **`plan.json` carries no `scale`, so the build is `project` by default — and nobody printed a sizing line.** § 3.1 requires `requirements-clarifier` to print `scale: <tier> (D=… S=… O=… integration=…)` and to re-check once after the answers land. Neither line appears in `plan.json`, `CLARIFICATIONS.md` or the clarify envelopes. The tier is almost certainly right — 5 milestones, 22 steps, ~15 metadata types, 3 objects — so no re-tier is implied, and the AGENT.md asks this to be flagged whenever `scale` disagrees with the printed counts. **Here the concern is that there are no counts to disagree with.** This build predates § 3.1 and is the canonical example the section was written against; the observation is for the *layer*, not for this build.
- **A checker fix landed mid-verification.** `check_rtm.py` v1.1.5 (`0c585e185`) went in today and changed a result this milestone's own documentation asserts (3 orphans → 0, F-48). This is the fourth such fix in four milestones. Each was correct, each was driven by a real doc-keeper finding, and the cumulative effect is that **a build document's recorded checker output has a shelf life measured in hours**. Worth a convention: record the checker version alongside the output, so a reader can tell a stale result from a wrong one.
- **Findings are recorded thoroughly at step scope and composed nowhere.** Six of this run's ten findings (F-39, F-40, F-41, F-44, F-45, F-46) are not new facts — every component fact was already written down, accurately, by a builder or the doc keeper. What was missing was the *join*: U3 asks whether the Tier 2 queue has a mailbox and M2-S04's artefact answers it; O-M4S03-02 names the active-flow Apex-test coupling and D-M4S05-04 names the test's org prerequisites; `plan.json` states M4's goal and O-M4S02-02 states why it cannot be met. Each pair sits in two files and nothing reads both. That is exactly the gap this agent exists to fill, and the volume of it in one milestone suggests the step-level agents should be asked, at minimum, to name the file they expect the other half of a UNVERIFIED item to be answered in.
- **`plan.json`'s M4 `goal` was never re-read after the design diverged from it** (F-40). No step reads `milestones[].goal`, no checker asserts against it, and the doc keeper's rows trace to `REQ-*` ids rather than to the milestone goal. A milestone goal that nothing verifies is a comment.
- **`steps[M4-S04].runs[]` carries two malformed `started` timestamps** — `"2026-09-12T07-35-25Z"` and, in M4-S05, `"2026-09-12T08-12-19Z"` / `"2026-09-12T08-24-48Z"` — using the filesystem-safe dash form where the field wants ISO `hh:mm:ss`. Cosmetic, schema-passing, and it makes `runs[]` unsortable by time against the correctly-formed entries beside it.

### Ambiguous

- **Whether `00:00:00.000Z`–`00:00:00.000Z` on all seven days means "open all day" or "closed"** (O-M4S01-02) cannot be settled from documents. Three sources now point one way — `gotchas.md` #1, `examples.md` Example 1 since `5b206697a`, and the Metadata API guide documenting the value as "midnight" — and `gotchas.md` #6 still marks the *pair* UNVERIFIED, with the skill's own prescribed resolution being an org round-trip, not a document. The build is design-only. **This is the right call and it is still unresolved**; the runbook's § 5 clock test is the remedy and it needs a sandbox.
- **Whether the `EntitlementProcess` file names and manifest members survive a retrieve** (M4-S02 `deploy-order.md` § 4.1/4.2). The guide says the file name is `slaProcess.NameNorm` — *lowercased* — so a real org would return `first_response_premier.entitlementProcess-meta.xml`, not the mixed-case name the plan declared and this merged manifest carries. Mock deploy run 4 accepted the mixed-case members, which is evidence but not proof (a deploy is not a retrieve). **The merged manifest inherits this uncertainty**, and the remedy is one retrieve after the first deploy.
- **Whether a one-element `FlowSettings` file leaves the org's other twelve values untouched or resets them** (O-M4S03-02). Not stated in either cited skill. `Settings:Flow` is a member of the merged manifest, so this is the merged manifest's uncertainty too.
- **Whether the `CreateAndUpdate` half of the F-38 rule holds** (D-M4S03-01). `Create → Initial only` is proven over two org rejections; `CreateAndUpdate → both` is inferred from the guide's sample and run 3's error text, never observed. No flow in this build is `CreateAndUpdate`, so it costs nothing here and will cost the next build that hits it — and the skill fix that would close it is **still pending**, the only flywheel record in M4 with no closing commit.

### Suggested follow-up agents — recommendations only; this agent invoked neither

- **`deployment-risk-scorer`** — once a human has an org to score `reports/MILESTONE-M4-package.xml` against. It is the agent that would have caught F-39 mechanically (a manifest whose components need a feature switch the manifest does not carry), and it would put a number on the active-flow Apex-test coupling in F-45.
- **`release-readiness-reviewer`** — not yet. M4 is not the last milestone before a release; M5 is, and it carries the sandbox proof, the UAT pack and the build-level manifest that closes F-43. Run it after M5, not now.

---

## 16. Citations

| Type | Id / path | Used for |
|---|---|---|
| standard | `AGENT_RULES.md` | run-time rules: no org write, no auto-chain |
| standard | `agents/_shared/AGENT_CONTRACT.md` | 8-section shape, Process Observations, confidence rubric, Apex security idiom by API version (§ 3.3, F-45) |
| standard | `agents/_shared/DELIVERABLE_CONTRACT.md` | persistence, atomic write, the declared deviation in § 14 |
| standard | `agents/_shared/REFUSAL_CODES.md` | the refusal enum — none raised this run |
| standard | `standards/build-orchestration.md` | § 2 (report written not rendered; `set-milestone`), § 3 (gate conditions, blocked-step rule), § 3.1 (scale, the sizing-line observation), § 4 (borrowed-agent conditions, agent eligibility), § 5 (acceptance-test types, checker scope, cross-referential checkers, **The Apex exception**), § 7 (this agent runs last and returns) |
| schema | `agents/_shared/schemas/build-plan.schema.json` | milestone and gate fields read |
| schema | `agents/_shared/schemas/output-envelope.schema.json` | envelope shape, validated before return |
| skill | `skills/devops/metadata-api-retrieve-deploy` | manifest grammar; one `<version>` per package; what one deploy does and does not carry across (§ 5) |
| skill | `skills/devops/permission-set-deployment-ordering` | the objects-before-permission-sets constraint — checked, **no instance in M4** (§ 4) |
| skill | `skills/devops/flow-deployment-activation-ordering` | where automation sits in the order and what a Flow's active state means on arrival (§ 4 observation 2, F-45) |
| skill | `skills/devops/deployment-error-diagnosis` | the deploy-time error each unresolved reference predicts (F-39) |
| skill | `skills/devops/pre-deployment-checklist` | the go/no-go items § 11 and § 13 must cover |
| skill | `skills/admin/uat-and-acceptance-criteria` | the tickable form of every line in § 7 |
| skill | `skills/admin/requirements-traceability-matrix` | § 10's closure statement in the ids `traceability.md` carries; `check_rtm.py` v1.1.5 re-run for F-48 |
| checker | `skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py` | milestone test M4-T1, run verbatim |
| checker | `skills/admin/entitlements-and-milestones/scripts/check_entitlements_and_milestones.py` | milestone test M4-T2, run verbatim |
| checker | `skills/admin/escalation-rules/scripts/check_escalation_rules.py` | milestone test M4-T3, run verbatim |
| checker | `skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py` | milestone test M4-T4, run verbatim |

**Decision-tree branches:** none consulted. This agent designs nothing and chose no technology; the
trees M4 rests on (`automation-selection.md` for D1/D10, `flow-pattern-selector.md` for D2) were
cited by the steps that made those choices, and re-litigating them at verification would be this
agent exceeding its scope.

---

*Written by `milestone-verifier` per `agents/milestone-verifier/AGENT.md`. No org was contacted, no
gate was written, no manual test was ticked, and nothing was deployed. G4 is the human's.*
