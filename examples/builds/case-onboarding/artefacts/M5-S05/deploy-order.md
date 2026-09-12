# Deploy order — the build-level manifest, Acme case onboarding (M1–M5)

Written by `agents/metadata-builder` for step `M5-S05`, beside `package.xml` in this directory.
It is the deploy-order note for **one** artefact — the build-level manifest — and it covers the
whole build because that manifest does.

**Nothing in this file deploys.** The only command it carries is a validation (§ 7), it is written
as text for a human to copy, and no agent in this loop runs it. There is no `sf project deploy
start` here and no destructive manifest anywhere in this build (§ 2.3).

Division of labour, per `standards/build-orchestration.md` § 4: this file and `package.xml` are
`metadata-builder`'s; the workbook, the traceability matrix and the **compiled build-wide deploy
order** (`artefacts/M5-S04/deploy-order.md`) are `build-doc-keeper`'s. Where this file and
M5-S04's disagree, § 3.3 says so rather than quietly picking one.

---

## 0. Rebuild record — F-59/F-60: TestUserFactory joins the manifest, Case_Agent_Core content changed

This step was `documented`; the operator moved it `documented -> running` because two of its
inputs changed after G5 was signed: **M4-S05** shipped a fifth Apex file, `classes/TestUserFactory.cls`
(+ `-meta.xml`, apiVersion 67.0) — the permissioned test-running user F-59's repair introduced,
`artefacts/M4-S05/deploy-order.md` § 8 — and **M2-S02**'s `Case_Agent_Core` permission set had
`fieldPermissions` added to it (F-60, `artefacts/M4-S05/deploy-order.md` § 9). Both are read as
this run's inputs, per `standards/build-orchestration.md` § 4 (Step 4's four input sources) and
this agent's own AGENT.md Step 4.

**Member diff.**

| Type | Change | Detail |
|---|---|---|
| `ApexClass` | **+1 member** | `TestUserFactory` added — file exists at `artefacts/M4-S05/classes/TestUserFactory.cls` (+ `-meta.xml`), verbatim from `templates/apex/tests/TestUserFactory.cls` per M4-S05 § 8. Alphabetically last in the block (`CaseMilestoneService`, `CaseMilestoneServiceTest`, `TestDataFactory`, `TestUserFactory`) |
| `PermissionSet` | **0 members changed** | `Case_Agent_Core` is unchanged as a member name — F-60 changed the file's *content* only (`fieldPermissions` added; `artefacts/M2-S02/package.xml` already declared this member and still does, at its own step's manifest) |
| Every other type | **0 members changed** | No other step's outputs changed since the last build of this manifest |

Net: **29 types (unchanged), 57 members (was 56)**. No type added or removed, no member removed,
no member renamed. This is the only diff a whole-tree two-way check (file → member and member →
file, over every non-blocked step's artefacts) found — see § 5.1.

**Evidence this rebuild rests on.** `reports/MOCK-DEPLOY-M5.md` runs 4–8, read in full for this
rebuild:

- **Run 4** (MANIFEST mode, `--tests CaseMilestoneServiceTest`) first executed the Apex rather than
  only compiling it, and found **F-59**: no test method ran inside a permissioned `System.runAs`,
  so `CaseMilestoneServiceTest` failed 3/3 on FLS the moment a real user context applied.
- **Run 5** (probe, after the M4-S05 test-only repair) found **F-60**: the Tier 1 persona as shipped
  could create a Case but not write `Subject`, `Origin`, `Priority`, the `Account` or the
  `Entitlement` lookup — `Case_Agent_Core` granted Create on Case with field permissions on exactly
  one field. Fixed in M2-S02, not here.
- **Run 6** (probe, after the M2-S02 field-permission repair) closed F-59 and F-60; two failures
  remained on a test-grounding defect, **F-61** (a `SeeAllData` test selecting "any active
  entitlement process" picked up the org's own process instead of the deployed one).
- **Run 7** (probe, after the F-61 named-process fix) closed F-61; two failures remained on
  shipped-code behaviour, **F-62** (the milestone-completion query/update needed an explicit
  system-mode boundary once the service ran under the Tier 1 persona's user-mode default).
- **Run 8** (probe, after the F-62 system-mode boundary): **succeeded** — 60/60 components ok,
  tests **run 4 · passed 4 · failed 0 · coverage 84.4%**, no coverage warnings. F-59, F-60, F-61
  and F-62 all closed by the org. The only remaining component error against `sfskills-dev` is
  **F-28** — `support-noreply@acme.example` not yet a verified `OrgWideEmailAddress` — the same
  named org prerequisite carried since `MOCK-DEPLOY-M3.md` run 6 (§ 5.2 item 1). No new component
  error was introduced by TestUserFactory joining the manifest or by the Case_Agent_Core content
  change.

None of runs 4–8 read the build-level `package.xml` this rebuild produces (run 4 was the last to
read a merged manifest, and it predates F-59's fix); they are source-mode probes on the same tree
this manifest now describes plus the one member this rebuild adds. § 5.1 restates this distinction
for the manifest-mode record.

**M3-S05 and M5-S02 remain blocked and ship nothing** — unchanged by this rebuild; see § 2.1.

---

## 1. What the manifest contains

| | |
|---|---|
| Types | 29 |
| Members | 57 |
| `<version>` | `67.0` |
| Wildcards | none — every member is named |
| Source | the 16 step manifests under `artefacts/*/package.xml`, plus M4-S05's five Apex members |
| Backing files | every one of the 57 members resolves to a file under `artefacts/`; every deployable file under `artefacts/` is covered by a member (§ 5.1) |

Members per type, and the step whose artefacts hold the file:

| Type | Members | From |
|---|---|---|
| `StandardValueSet` | `CaseOrigin` | M1-S01 |
| `CustomObject` | `Case` | M1-S01 |
| `CustomField` | `Account.Region__c`, `Account.Support_Tier__c`, `Case.Severity__c` | M1-S01 |
| `BusinessProcess` | `Case.Billing_Process`, `Case.Support_Process` | M1-S01 |
| `RecordType` | `Case.Billing`, `Case.Support` | M1-S01 |
| `CompactLayout` | `Case.Case_Intake` | M1-S01 |
| `Layout` | `Case-Case Billing Layout`, `Case-Case Support Layout` | M1-S02 |
| `CustomPermission` | `Bypass_Case_Intake_Validation` | M2-S01 |
| `PermissionSet` | `Case_Intake_Integration` (M2-S01); `Case_Agent_Core`, `Case_Billing`, `Case_Tier1`, `Case_Tier2` (M2-S02) | M2-S01, M2-S02 |
| `PermissionSetGroup` | `PSG_Billing_Prod`, `PSG_Tier1_Prod`, `PSG_Tier2_Prod` | M2-S02 |
| `Profile` | `Acme Billing`, `Acme Support Tier 1`, `Acme Support Tier 2` | M2-S03 |
| `Group` | `Billing_Team`, `Support_Tier_1`, `Support_Tier_2` | M2-S04 |
| `Queue` | `Billing`, `Tier_1_General`, `Tier_2_Engineering` | M2-S04 |
| `SharingRules` | `Case` | M2-S05 |
| `ValidationRule` | `Case.Origin_Must_Be_Known`, `Case.Priority_Required_On_Agent_Save` | M3-S01 |
| `EmailFolder` | `case_intake` | M3-S02 |
| `EmailTemplate` | `case_intake/Case_Acknowledgement`, `case_intake/Case_Escalated_To_Tier2` | M3-S02 |
| `Settings` | `Case` (M3-S03), `BusinessHours` (M4-S01), `Flow` (M4-S03) | M3-S03, M4-S01, M4-S03 |
| `AssignmentRules` | `Case` | M3-S04 |
| `AutoResponseRules` | `Case` | M3-S04 |
| `EntitlementProcess` | `First_Response_Premier`, `First_Response_Standard` | M4-S02 |
| `MilestoneType` | `First Response` | M4-S02 |
| `Flow` | `Case_BeforeSave_StampEntitlementAndCalendar` | M4-S03 |
| `FlowTest` | `Case_BeforeSave_StampEntitlementAndCalendar_Test` | M4-S03 |
| `EscalationRules` | `Case` | M4-S04 |
| `ApexTrigger` | `CaseMilestoneTrigger` | M4-S05 |
| `ApexClass` | `CaseMilestoneService`, `CaseMilestoneServiceTest`, `TestDataFactory`, `TestUserFactory` | M4-S05 |
| `ListView` | `Case.Billing_Queue`, `Case.Tier_1_General_Queue`, `Case.Tier_2_Queue` | M5-S01 |
| `Report` | `Support_Operations` (the folder), `Support_Operations/Escalated_Open_Cases` | M5-S01 |

### 1.1 Member forms that are not the obvious one

- **Object-qualified** because the Metadata API names the component that way:
  `CustomField` (`objectName.field`, api_meta L2265–L2287), `ListView`
  (`objectName.listViewUniqueName`, api_meta L2318), and — on the same
  `objectName.componentName` pattern — `BusinessProcess`, `RecordType`, `ValidationRule` and
  `CompactLayout`. `admin/change-management-and-deployment/references/metadata-examples.md` § 1
  marks the `ValidationRule` member form **UNVERIFIED** (the guide ships no `ValidationRule`
  manifest sample); it is carried here unchanged because M3-S01 declared it and the org accepted
  it in every source-mode validation from `MOCK-DEPLOY-M3.md` run 2 onward.
- **`CompactLayout` is `Case.Case_Intake`, not `Case_Intake`.** The bare form is what
  `MOCK-DEPLOY-M1.md` mock deploy #3 rejected — *"An object 'Case_Intake' of type CompactLayout was
  named in package.xml, but was not found in zipped directory"* — and it is the one defect in this
  build that **only** a manifest-mode validation has ever caught (F-13). `reports/MILESTONE-M1-package.xml`
  still carries the bare form and predates the fix; this manifest does not.
- **Folder-qualified**: `EmailTemplate` members carry their folder (`case_intake/…`), the
  `EmailFolder` is its own member, and the report folder `Support_Operations` is a `Report` member
  in its own right alongside `Support_Operations/Escalated_Open_Cases`.
- **`Layout` joins object and label with a hyphen and keeps the literal spaces** —
  `Case-Case Support Layout`, the guide's own `Idea-Idea Layout` shape (api_meta L82285–L82289).
  Do not URL-encode.
- **`Settings` is named explicitly, three times.** Feature settings take no wildcard: *"The
  wildcard character `*` … doesn't apply to metadata types for feature settings"*
  (`admin/case-management-setup/references/metadata-examples.md` § 5, quoting `CaseSettings` →
  Wildcard Support in the Manifest File). `Case`, `BusinessHours` and `Flow` are three separate
  members of one `Settings` block.
- **`SharingRules` carries the object name `Case`**, which is the form M2-S05 declared and the file
  `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` produces. The granular
  `SharingCriteriaRule Case.Support_Cases_To_Tier_2` inside it is not separately named: the plan's
  step manifest is the authority for member form, and the container form is what validated in
  `MOCK-DEPLOY-M2.md` run 3 (32 components, 0 errors).
- **No wildcards at all.** Beyond the settings rule, `StandardValueSet` and `ValidationRule` do not
  support `*` (api_meta L45447–L45449), `BusinessProcess` supports it *"only when a `RecordType` is
  specified"*, and `EmailTemplate` takes none. Naming every member sidesteps the question and is
  what makes the two-way file check in § 5.1 possible.

### 1.2 The `<version>` split, and why 67.0

The step manifests disagree, and the disagreement is real rather than sloppy:

| `<version>` | Steps |
|---|---|
| `62.0` | M1-S01, M1-S02, M2-S01, M2-S02, M2-S03, M2-S04, M2-S05, M3-S01, M3-S02 (nine) |
| `67.0` | M3-S03, M3-S04, M4-S01, M4-S02, M4-S03, M4-S04, M5-S01 (seven) |

`67.0` is written here on two grounds, neither of them this agent's own judgement:

1. **G3 decision 6** (`plan.json.human_gates`, `milestone:M3`): *"build API version = 67.0 accepted;
   accepted M1/M2 manifests are not rewritten; `scripts/mock_deploy.py` deploys at the highest step
   version (a7dbdf018); planner v6 adds a plan-level `api_version`."* The G4 note carries the same
   choice forward.
2. **The org proved the floor.** `MOCK-DEPLOY-M3.md` run 4 probes a–c: `newEntityRecordType` on the
   Email-to-Case routing addresses is *"not valid in version 62.0"* and *"not valid in version
   63.0"*, and resolves from 64.0. M3-S03's `Settings:Case` therefore cannot deploy at 62.0 at all.
   Runs 5 and 6, and every run in `MOCK-DEPLOY-M4.md` and `MOCK-DEPLOY-M5.md`, validated at 67.0.

The nine 62.0 step manifests are **left as they are**, per the same gate decision. A merged
manifest at 67.0 and a step manifest at 62.0 are not in conflict: the step file records what that
step was built and accepted at; this file records what the build deploys at.

---

## 2. What is deliberately absent

### 2.1 Two blocked steps, named rather than silently missing

- **`M3-S05`** — status `blocked`, blocked reason verbatim: **`deferred: Q32, Q33, Q34, Q35`**.
  Omni-Channel push routing for Tier 1. No `ServiceChannel`, `QueueRoutingConfig`,
  `ServicePresenceStatus`, `PresenceUserConfig` or `PresenceDeclineReason` member appears in this
  manifest, and no such file exists under `artefacts/`. REQ-022's push half is undelivered this
  phase (G3 gate note, "Accepted explicitly").
- **`M5-S02`** — status `blocked`, blocked reason verbatim: **`borrowed agent requires team_size,
  concurrent_workstreams, release_cadence, data_sensitivity`**. The sandbox proof plan. Its declared
  output was a markdown plan, never metadata, so its absence removes no member from this manifest —
  but it does mean the build carries **no sandbox strategy document**, which matters to § 7 and to
  Q74's refresh rule.

### 2.2 Three steps that produce documents, not components

`M5-S03` (story backlog), `M5-S04` (workbook, traceability, build-wide deploy order, UAT pack,
acceptance criteria) and `M5-S05` (this file and `package.xml`) contribute no manifest member. Nor
do the per-step `deploy-order.md` notes, runbooks and decision records under
`artefacts/*/*.md` — `artefacts/M5-S04/deploy-order.md` lists all 48 of them under "Not a component".

### 2.3 No deletions

No step in this build retires a component, so there is no `destructiveChangesPre.xml` or
`destructiveChangesPost.xml` beside this manifest, and none is wanted. Worth stating rather than
leaving implicit, because a destructive manifest that ships without a companion `package.xml` is
inert (`admin/change-management-and-deployment/references/gotchas.md`, *"A Destructive Manifest Is
Inert Without a Companion `package.xml`"*, api_meta L4630–L4637), and the check that catches it is
per-directory — this directory has one manifest and no destructive sibling, which is the correct
shape for an additive release.

---

## 3. The order

### 3.1 The sequence

The build-wide order is the milestone order — object model and layouts, then access, then
validation and intake routing, then SLA, then UI and docs — refined by the two sources that
document *why* each position is where it is:
`admin/case-management-setup/references/metadata-examples.md` § 5 (rows 1–6 below) and
`agents/build-doc-keeper/AGENT.md`'s ten-slot canonical sequence as compiled in
`artefacts/M5-S04/deploy-order.md`.

| # | Deploy | Because |
|---|---|---|
| 1 | `CustomField` ×3 (`Case.Severity__c`, `Account.Region__c`, `Account.Support_Tier__c`) | a `picklistValues` block, a rule criterion or a sharing criterion on a field that does not exist fails the deploy (§ 5 row 1) |
| 2 | `StandardValueSet:CaseOrigin` | the business processes' `Status` values and the intake channels' origin both reference values that must already exist (§ 5 row 2). `CasePriority` and `CaseStatus` are **not** in this build — see § 5.3 |
| 3 | `CustomObject:Case`, then `BusinessProcess` ×2, `RecordType` ×2, `CompactLayout` | *"a record type is rejected without its support process, and the process is rejected without its Status values"* (§ 5 row 3). A `BusinessProcess` member must equal its file stem, or the deploy reports "not found in zipped directory" (F-11, `MOCK-DEPLOY-M1.md` runs 5–7) |
| 4 | `Layout` ×2 | layouts assign to record types; both carry the platform-required `ContactId`, `Description`, `SuppliedEmail` and `Status` (F-09/F-10, closed) |
| 5 | `CustomPermission`, then `PermissionSet` ×5, `PermissionSetGroup` ×3, `Profile` ×3 | the bypass permission is referenced by M3-S01's validation rules through `$Permission`; a PSG naming a permission set that is not in the same request fails with *"permission set names are invalid"* (`MOCK-DEPLOY-M2.md` run 1) |
| 6 | `Group` ×3, then `Queue` ×3 | a queue's membership names its public groups; the groups must exist first (`artefacts/M2-S04/deploy-order.md`, carried into M5-S04's hazard list) |
| 7 | `SharingRules:Case`, `ListView` ×3 | the sharing rule's criteria name the Case record types from slot 3 and share **to** the groups from slot 6; the queue list views filter on the queues |
| 8 | `ValidationRule` ×2 | they reference `Case.Severity__c`, the `CaseOrigin` values and the bypass custom permission — everything above them |
| 9 | `EmailFolder:case_intake`, then `EmailTemplate` ×2 | *"`defaultCaseOwner` and the four `case*NotificationTemplate` fields resolve by name at deploy time"* (§ 5 row 4) — the templates must exist before the rules that name them |
| 10 | `AssignmentRules:Case`, then `AutoResponseRules:Case` | *"the auto-response fires only when the assignment rule fires"* (§ 5 row 6). Both name the slot-6 queues and the slot-9 acknowledgement template |
| 11 | `Settings:Case` | turning the channels on *after* their origin, owner, templates and rules exist (§ 5 row 5, and § 3.3 below) |
| 12 | `Settings:BusinessHours` | the SLA clocks and the escalation timers both read the calendars; nothing above needs them |
| 13 | `MilestoneType:First Response`, **then** `EntitlementProcess` ×2 | *the one intra-step ordering constraint in this build where deploying a step's own files in filename order rather than dependency order would fail* — the processes' milestones resolve the type by name (`artefacts/M4-S02/deploy-order.md`, quoted in M5-S04's hazard list) |
| 14 | `Settings:Flow`, `Flow`, `FlowTest` | the before-save flow reads `$Record.EntitlementId` and the `Entitlement` object, so it needs slot 13 — and the org switch in § 4.2 |
| 15 | `ApexTrigger:CaseMilestoneTrigger` + `ApexClass` ×4 | the trigger completes the First Response milestone: it needs the milestone type, the entitlement processes and the flow that stamps the entitlement. `TestDataFactory` ships alongside the test class rather than being assumed present (F-37); `TestUserFactory` ships alongside it too, the permissioned test-running user F-59's repair added (`artefacts/M4-S05/deploy-order.md` § 8) |
| 16 | `EscalationRules:Case` | last of everything it names: `Severity__c` (slot 1), the Tier 2 queue (slot 6), the escalation template (slot 9) and the business hours (slot 12). Ships **inactive** — § 4.1 |
| 17 | `Report` folder `Support_Operations`, then `Support_Operations/Escalated_Open_Cases` | the folder before the report in it; the report's own "Escalated" criterion is deferred to a post-deploy runbook step — § 5.2 |

### 3.2 One request, and what the order is actually for

All 57 members are in one manifest and would land in one `deploy()` call, where the platform
resolves component dependencies itself. Two sources speak to whether the manifest's own order
matters, and they do not agree; both are reproduced rather than resolved:

- `admin/case-management-setup/references/metadata-examples.md` § 5 says, in the comment on its
  deploy command, *"Deploy in the order above; the manifest preserves it within one deployment."*
- `admin/change-management-and-deployment/references/metadata-examples.md` § 1 quotes the guide
  only on membership — *"Metadata API references the components listed in the manifest, not the
  directories in the .zip file"* (api_meta L2054–L2056) — and says nothing about intra-request
  ordering.

What the order above is unambiguously for: **splitting the release**. If the window is broken into
more than one deploy — and § 3.3's hazard is a reason to consider exactly that — this table is the
split order. The `<types>` blocks in `package.xml` itself are sorted alphabetically, matching the
four merged milestone manifests under `reports/` and `scripts/mock_deploy.py`'s own
`merge_package_xml`, so that a manifest-mode re-merge produces no drift.

### 3.3 Where this file differs from `artefacts/M5-S04/deploy-order.md`

M5-S04's ten-slot table and this one agree on every component's relative position with **one**
exception, and it is the hazard M5-S04 itself flags first:

> **"`M3-S03` before `M3-S04`, in the wrong direction for safety."** M5-S04's slot 9 lists
> `Settings:Case` (`CWB-AUT-007`) ahead of `AssignmentRules:Case` (`CWB-AUT-010`) and
> `AutoResponseRules:Case` (`CWB-AUT-011`), following plan step order.

`artefacts/M3-S03/deploy-order.md` § 3 states the opposite for any org that will receive real mail:

> 1. `StandardValueSet:CaseOrigin` and `CustomObject:Case` (M1-S01), then the queues (M2-S04).
> 2. `AssignmentRules:Case` and `AutoResponseRules:Case` (M3-S04) — **before** this file, not after.
> 3. `Settings:Case` (this file).
> 4. Only then point the mail-server forwarding rules at the Salesforce-generated
>    `emailServicesAddress` values, and only then publish the web form.

**This file follows M3-S03's safe sequence** — rules at slot 10, `Settings:Case` at slot 11 — and
names the difference here rather than silently re-ordering M5-S04's table. Three things make the
difference smaller than it looks, and they are worth reading before anyone treats it as a defect:

- The failure mode is not a deploy error. It is *"live traffic into an org with no active
  assignment rule"* — cases created unrouted, falling to `defaultCaseOwner` (`Tier_1_General`) with
  no acknowledgement sent.
- The real switch is step 4 above, which is **outside the deploy**: Email-to-Case receives nothing
  until mail-server forwarding is live and the address is verified, and Web-to-Case receives
  nothing until the form is published. That is the build's actual safety margin, and it is a human
  action.
- `M3-S03/deploy-order.md` also records that the switch is one-way: *"After Email-to-Case is
  enabled, it can't be disabled."*

The other four cross-step hazards M5-S04 collates — M3-S04's dependency on the M2-S04 queues and
the `CaseOrigin` value set; M4-S04's on the M3-S02 template, the Tier 2 queue and `Severity__c`;
M4-S02's `MilestoneType`-before-`EntitlementProcess` rule; M2-S04's groups-before-queues — are all
satisfied by the table in § 3.1, at slots 10, 16, 13 and 6 respectively.

---

## 4. Components that arrive needing a human to flip something

The skill's Questions-to-Ask row — *"Which components arrive in a state a user can see, and which
need a switch flipped?"* — with the answers this plan actually binds.

### 4.1 Shipped inactive on purpose

| Component | State as built | Why |
|---|---|---|
| `EscalationRules:Case` | `<active>false</active>` (`artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml` line 17) | **Q47**: *"Deploy the rule inactive, then activate inside a defined comparison window once the sandbox proof is signed off."* Cases already past their threshold escalate on the first pass after activation, so activation is a separate, scheduled decision — see `artefacts/M4-S04/escalation-activation-runbook.md` |

**Q58** is the other inactive-shipping answer and it resolves the other way for this build: *"No
existing Cases — per requirement, support currently runs from a shared mailbox (no Case data exists
yet), so the data is clean by construction; still deploy any rule aimed at migrated Accounts or
Contacts inactive until a count proves it."* Both validation rules are therefore `<active>true</active>`,
correctly: they target Case, and there is no Case data to violate them. **The caveat still stands
for any future rule on Account or Contact** — this build ships none, and the next one that does
must ship it inactive until a count proves the data clean.

For contrast, the components that arrive **live**: `AssignmentRules:Case` and `AutoResponseRules:Case`
(`<active>true</active>`), both validation rules, both entitlement processes, and the flow
(`<status>Active</status>`).

### 4.2 Post-deploy switches, assignments and data — none of which this manifest carries

| Switch | Who / where | Consequence if skipped |
|---|---|---|
| Permission-set and PSG assignment to users | Setup or a data load; no metadata assigns them | The three profiles land, the five permission sets land, and nobody has the access |
| `enableEntitlements` (and `enableMilestoneStoppedTime`) in `settings/Entitlement.settings-meta.xml` | **No step's `outputs[]` declares this file** — G4 decision 2 accepted it as a named deploy prerequisite rather than a plan amendment | Three of M4's five steps depend on it (F-39): the entitlement processes and milestone type, the flow's `Entitlement` lookup, and the Apex trigger's `CaseMilestone` / `SlaProcess` references. Predicted error is `INVALID_TYPE: sObject type 'Entitlement' is not supported` on the *flow*, which points at the wrong thing. `sfskills-dev` already has the feature on, which is why every mock deploy passed without it |
| Mail-server forwarding → the Salesforce `emailServicesAddress` values; publishing the web form | Human, after slot 11 | § 3.3 step 4 — the build's actual safety margin |
| Escalation-rule activation, inside the Q47 comparison window | Release manager | § 4.1 |

---

## 5. Prerequisites and open items no manifest can carry

### 5.1 What was checked here, and what was not

Checked, this run, over the whole `artefacts/` tree (re-run after the F-59/F-60 rebuild, § 0):

- **Manifest → file.** All 57 members resolve to a file. `CaseMilestoneService` →
  `artefacts/M4-S05/classes/CaseMilestoneService.cls`, `TestUserFactory` →
  `artefacts/M4-S05/classes/TestUserFactory.cls` (new this run), `Case.Case_Intake` →
  `artefacts/M1-S01/objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml`, and so on for
  the rest.
- **File → manifest.** All 64 deployable files under `artefacts/` are covered by a member, counting
  the seven `-meta.xml` siblings (`*.cls-meta.xml` ×4, `*.trigger-meta.xml`, `*.email-meta.xml` ×2)
  that travel with their bodies. Nothing is orphaned. `M4-S03/flow-governance-policy.yaml` and
  `M5-S04/uat-test-cases.yaml`, like the `*.md` notes throughout `artefacts/`, are not deployable
  metadata and are not counted on either side of this check, consistent with every prior run of it.

**Not checked, and not checkable here:** that the 57 members deploy as one manifest. Only an org
says that, and manifest mode has been run exactly once against this file (`MOCK-DEPLOY-M1.md` mock
deploy #4, milestone M1 only, and once more at run 3 below) — but the Apex itself has now actually
*executed* in the org, which is stronger evidence than either manifest-mode run offers on its own:

- `MOCK-DEPLOY-M5.md` run 3 — manifest mode, every built step, the pre-rebuild 56-member manifest:
  60 components, 60 ok, 1 error (F-28 only). First validation in the build to read a manifest
  carrying the Apex; F-43 closed.
- `MOCK-DEPLOY-M5.md` run 4 — manifest mode, `--test-level RunSpecifiedTests --tests
  CaseMilestoneServiceTest`, the pre-rebuild manifest: 60/60 components ok, but this was the run
  that found **F-59** — 0 tests passed, all three failing on FLS, because the deploying user (not
  a permissioned persona) ran them. G4/G5 had rested on compile-only evidence (`runTestsEnabled:
  false`) until this run.
- `MOCK-DEPLOY-M5.md` runs 5–7 — source-mode probes, tracing F-59 (run 5) into **F-60** (the
  Tier 1 persona's missing field permissions, fixed in M2-S02), then **F-61** (a `SeeAllData` test
  picking up the org's own entitlement process instead of the deployed one, run 6), then **F-62**
  (the milestone-completion service needed an explicit system-mode boundary once it ran under the
  persona's user-mode default, run 7).
- `MOCK-DEPLOY-M5.md` run 8 — source-mode, after the F-62 fix: **60/60 components ok, tests run 4 ·
  passed 4 · failed 0 · coverage 84.4%, no coverage warnings.** F-59, F-60, F-61 and F-62 all
  closed by the org. **F-28** — the unverified `support-noreply@acme.example` sender — is the only
  remaining component error, unchanged from every prior run since `MOCK-DEPLOY-M3.md` run 6 (§ 5.2
  item 1).

Run 8 is source mode, not manifest mode, so it does not by itself confirm the *rebuilt* 57-member
manifest deploys as one request — that confirmation is still § 7's command, run once against this
file. What run 8 does confirm is that the Apex this manifest's new member belongs to (`TestUserFactory`,
plus the classes and trigger already present) compiles, deploys and now *passes* under the org's
enforcement, closing the compile-only-evidence gap `F-43` and G4/G5 were signed against. Per G4's
F-43 note, *"no manifest in the build carries the Apex until M5-S05 is built — manifest-mode
validation of M4 must wait for M5-S05"*; that wait ended at run 3, and run 8 is the test-execution
evidence the F-43 note did not yet have.

### 5.2 Org prerequisites carried forward from the milestone gates

| # | Prerequisite | Source | Status |
|---|---|---|---|
| 1 | `support-noreply@acme.example` provisioned and **verified** as an `OrgWideEmailAddress` before `AutoResponseRules:Case` deploys | **F-28**, `MOCK-DEPLOY-M3.md` run 6; G3 decision 4 (owner: dry-run operator, due before any real deploy) | **Open.** The org validates `senderEmail` against its verified addresses *at deploy time*, not at send time. There is no metadata type for an org-wide address, so no build can ship one. **Confirmed by `MOCK-DEPLOY-M5.md` run 8 as the only remaining component error** — with F-59/F-60/F-61/F-62 all closed by the org (4/4 tests passed, 84.4% coverage), this is now the single named blocker between this build and a clean validation as shipped. The same provisioning also serves M3-S03's `systemUserEmail` |
| 2 | Entitlement Management enabled (`enableEntitlements`), plus `enableMilestoneStoppedTime` before go-live | **F-39** / O-M4S02-01; G4 decision 2 | **Open**, and wider than it looks — § 4.2 |
| 3 | Non-routing mailboxes on the `Billing` and `Tier_2_Engineering` queues (`billing-queue@acme.example`, `tier2-queue@acme.example`) **before the escalation rule is activated** | **F-44** + O-M4S04-01; G4 decision 1, taken as one decision | **Open.** Activation prerequisite, not a deploy prerequisite — the rule ships inactive (§ 4.1). Without them the escalation notification reaches nobody, and a routing address on the Billing queue would create a mail loop. M2-S04's queue metadata is corrected at its next touch or in Setup |
| 4 | An `Entitlement` record per Account, pointing at the right process | **F-41**; G4 | **Open.** `Support_Tier__c` is documented as selecting between `First_Response_Premier` and `First_Response_Standard`, and nothing in this build implements the binding: the flow's `Get_Active_Entitlement` filters on `AccountId` and `Status = 'Active'` with no tier filter. REQ-040 ships as metadata that can express the promise, not as a mechanism that applies it |
| 5 | The report's **"Escalated = True"** criterion added in the report builder after deploy | **F-51**, `MOCK-DEPLOY-M5.md` | **Open by design.** Five candidate column codes were probed and all five rejected; column codes are harvested from an org retrieve. Recorded, not guessed. The report deploys without the criterion |
| 6 | An active `SlaProcess` carrying a First Response milestone, for M4-S05's `SeeAllData=true` test | G4 decision 9 | **Open**, for the deploy runbook |

### 5.3 Values this build depends on and does not declare

`StandardValueSet:CasePriority` and `CaseStatus` are **not** members of this manifest — M1-S01
shipped `CaseOrigin` only, because the build changes only that one. Four things depend on the
target org's untouched values anyway (**F-42**): the flow's two `Priority` writes (`High`,
`Medium`), M3-S03's two `<casePriority>Medium</casePriority>` intake defaults, and M3-S01's
priority rule. `MOCK-DEPLOY-M1.md` records that `sfskills-dev`'s `CaseStatus` already carries
New / Escalated / Closed — *"Reconcile again against any other target."*

---

## 6. Release options to decide before the window

From `admin/change-management-and-deployment`'s Questions-to-Ask table. **None of these is answered
by the plan**, and none of them is this agent's to choose — they are recorded so the release owner
decides them in advance rather than defaulting them at runtime.

| Question | What the skill says | What this build makes of it |
|---|---|---|
| `rollbackOnError` set explicitly? | Production *"must be set to `true`"* (api_meta L4256–L4260); the guide contradicts itself on the default (`DeployOptions` says false, `DeployResult` says true). Treat `SucceededPartial` as a failure in the release gate | Set it explicitly in every environment. A half-landed sandbox is the rehearsal you were using to prove the release safe |
| Which `testLevel`, and how long? | `RunLocalTests` is *"the default for production deployments that include Apex classes or triggers"*; a package with no Apex runs **no** tests by default at API 34.0+ | This manifest **does** carry Apex (one trigger, three classes), so a production deploy defaults to `RunLocalTests` — every local test, serially, inside the window. Measure it in the sandbox first |
| Validation timing relative to the window? | Quick deploy is licensed by a validation *against that target* within **10 days** | Validate close to the window, not early "to be safe" |
| Anything deleted? | Deletions need a second manifest and an ordering decision | Nothing. § 2.3 |
| What arrives needing a switch? | Activation, assignment and data repair are post-deploy work with owners | § 4 — and the six prerequisites in § 5.2 |
| If it behaves badly at 09:00? | There is no undo for a completed deploy. Deactivate-don't-delete is *"cheapest and fastest; usually the right first move"* | For this build that is: deactivate the two validation rules and the assignment rule, and set the flow's active version back. The escalation rule is already inactive |
| Did it change records? | Metadata rollback leaves data edits in place | No data load in this build. But the before-save flow and the trigger write to Cases from the moment they are active, so a backout after real traffic needs a data decision, not just a metadata one |

**Q68** answers what has to happen before any of this reaches customers: *"a sandbox test with real
inbound email, a clock test, and a loop test, before go-live."* **Q74** governs every refresh after
it: *"The Email-to-Case routing addresses and the website form endpoint must be re-pointed on every
refresh, or the sandbox will answer real customer mail."* The build has no sandbox strategy document
to hang either on — M5-S02 is blocked (§ 2.1).

---

## 7. The validate-only command a human may choose to run

Text to copy. **This agent does not run it, and nothing in the orchestration loop runs it.** It is a
validation: `checkOnly: true`, nothing is written to the org.

```bash
# From the repo root. Manifest mode is the only check that reads a merged package.xml.
python3 scripts/mock_deploy.py .sfskills/builds/case-onboarding/plan.json \
  --org-alias <your-alias> \
  --mode manifest
```

`--mode manifest` freshly merges the selected steps' manifests by type; with every step selected
(the default is every step at `built`, `tested` or `documented`) that merge is the union this file
describes, so a drift WARN against it would itself be the finding. `mock_deploy.py` hard-codes
`--dry-run` and has no deploy option.

The equivalent through the CLI directly, for a reviewer who wants to see the shape:

```bash
sf project deploy validate \
  --manifest artefacts/M5-S05/package.xml \
  --test-level RunLocalTests \
  --target-org <your-alias> \
  --wait 60
```

Two caveats on that second form, both from the skill: `sf project deploy validate` is documented
for a **production** target and returns a job id for a later `sf project deploy quick` inside the
ten-day clock; against a sandbox, `sf project deploy start --dry-run` is the validation form — which
is what `mock_deploy.py` runs. And § 5.2 item 1 means a validation against any org without a
verified `support-noreply@acme.example` will fail on `AutoResponseRule Case.Case_Acknowledgement`
and nothing else. That single expected failure is not a reason to stop reading the result.

---

## 8. Sources

| Source | Used for |
|---|---|
| `skills/admin/change-management-and-deployment/SKILL.md` | the Questions-to-Ask rows in § 6 |
| `skills/admin/change-management-and-deployment/references/metadata-examples.md` § 1 | the `package.xml` shape, member forms, the wildcard rules, the `Layout` hyphen form |
| `…/references/metadata-examples.md` § 2, § 3, § 6 | the destructive-manifest rule in § 2.3, the validate → quick deploy sequence in § 7, the backout table in § 6 |
| `…/references/gotchas.md` | `rollbackOnError` / `SucceededPartial`, the test-level defaults, the ten-day quick-deploy clock, the companion-manifest rule |
| `skills/admin/case-management-setup/references/metadata-examples.md` § 5 | the deploy-order rows 1–6 in § 3.1 and the feature-settings wildcard rule (read as guidance; this skill carries no manifest this step copies) |
| `artefacts/M5-S04/deploy-order.md` | the compiled build-wide order this file agrees with, and the one divergence in § 3.3 |
| `artefacts/M3-S03/deploy-order.md` § 3 | the safe sequence quoted in § 3.3 |
| `artefacts/*/package.xml` (16 files), `artefacts/M4-S05/classes/`, `artefacts/M4-S05/triggers/` | every member in the manifest |
| `reports/MOCK-DEPLOY-M1..M5.md` | F-11, F-13, F-28, F-37, F-39, F-42, F-49, F-50, F-51 and the version floor |
| `plan.json.human_gates` (`milestone:M3`, `milestone:M4`) | G3 decision 6 (API 67.0) and G4 decisions 1, 2, 9 and the F-43 note |
| `plan.json.clarifications` Q47, Q58, Q68, Q74 | § 4.1 and § 6 |
