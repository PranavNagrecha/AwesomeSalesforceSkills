# Deploy Order — Acme Software Case Onboarding on Service Cloud (build-wide)

Compiled by `agents/build-doc-keeper`'s `M5-S04` compile run, built from the per-step `deploy-order.md` files `metadata-builder` wrote and the milestone order in `plan.json`, per `agents/build-doc-keeper/AGENT.md` Step 10. Rather than re-quoting all seventeen per-step files in full, this document collates the one fact every workbook row already carries in its own `notes` cell — its position in the ten-slot canonical deployment sequence (`agents/build-doc-keeper/AGENT.md` Step 5: objects, fields, picklists, record types, layouts, permission sets, sharing, automation, routing, SLA) — and points at the per-step file for the full intra-step chain and its dependency prose.

## Milestone order (plan.json)

- **M1** — Case data model and record-type layouts — status `accepted` — steps: `M1-S01`, `M1-S02`
- **M2** — Access, work pools and Case visibility — status `accepted` — steps: `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`, `M2-S05`
- **M3** — Validation, intake and routing — status `accepted` — steps: `M3-S01`, `M3-S02`, `M3-S03`, `M3-S04`, `M3-S05`
- **M4** — SLA clocks, entitlements and escalation — status `accepted` — steps: `M4-S01`, `M4-S02`, `M4-S03`, `M4-S04`, `M4-S05`
- **M5** — Agent surfaces, sandbox proof and the deploy package — status `building` — steps: `M5-S01`, `M5-S02`, `M5-S03`, `M5-S04`, `M5-S05`

Two steps ship nothing in this phase and are named here rather than silently absent, per `M5-S04`'s own `acceptance_tests[5]`:
- `M3-S05` — **blocked** — `deferred: Q32, Q33, Q34, Q35` (Omni-Channel push routing; REQ-022's push half undelivered).
- `M5-S02` — **blocked** — `borrowed agent requires team_size, concurrent_workstreams, release_cadence, data_sensitivity` (sandbox-strategy design).

## The ten-slot canonical sequence, build-wide

Every row below cites its own per-step `deploy-order.md` for the full intra-step chain and cross-step dependency prose (`artefacts/<step-id>/deploy-order.md`); this table is the cross-step skeleton, not a replacement for those files.

| Slot | Name | Row id | Component (from `target_value`) |
|---|---|---|---|
| 2 | fields | `CWB-OBJ-007` | `CustomField:Case.Severity__c` |
| 2 | fields | `CWB-OBJ-008` | `CustomField:Account.Region__c` |
| 2 | fields | `CWB-OBJ-009` | `CustomField:Account.Support_Tier__c` |
| 3 | picklists | `CWB-OBJ-001` | `StandardValueSet:CaseOrigin` |
| 4 | record types | `CWB-OBJ-002` | `BusinessProcess:Case.Support_Process` |
| 4 | record types | `CWB-OBJ-003` | `BusinessProcess:Case.Billing_Process` |
| 4 | record types | `CWB-OBJ-004` | `RecordType:Case.Support` |
| 4 | record types | `CWB-OBJ-005` | `RecordType:Case.Billing` |
| 5 | layouts | `CWB-LAYOUT-001` | `Layout:Case-Case Support Layout` |
| 5 | layouts | `CWB-LAYOUT-002` | `Layout:Case-Case Billing Layout` |
| 6 | permission sets | `CWB-PERM-002` | `PermissionSet:Case_Intake_Integration` |
| 6 | permission sets | `CWB-PERM-003` | `PermissionSet:Case_Agent_Core` |
| 6 | permission sets | `CWB-PERM-004` | `PermissionSet:Case_Tier1` |
| 6 | permission sets | `CWB-PERM-005` | `PermissionSet:Case_Tier2` |
| 6 | permission sets | `CWB-PERM-006` | `PermissionSet:Case_Billing` |
| 6 | permission sets | `CWB-PERM-007` | `PermissionSetGroup:PSG_Tier1_Prod` |
| 6 | permission sets | `CWB-PERM-008` | `PermissionSetGroup:PSG_Tier2_Prod` |
| 6 | permission sets | `CWB-PERM-009` | `PermissionSetGroup:PSG_Billing_Prod` |
| 6 | permission sets | `CWB-PERM-010` | `Profile:Acme Support Tier 1` |
| 6 | permission sets | `CWB-PERM-011` | `Profile:Acme Support Tier 2` |
| 6 | permission sets | `CWB-PERM-012` | `Profile:Acme Billing` |
| 7 | sharing | `CWB-LAYOUT-007` | `ListView:Case.Tier_2_Queue` |
| 7 | sharing | `CWB-LAYOUT-008` | `ListView:Case.Billing_Queue` |
| 7 | sharing | `CWB-LAYOUT-009` | `ListView:Case.Tier_1_General_Queue` |
| 7 | sharing | `CWB-SHARE-001` | `CustomObject:Case` org-wide default |
| 7 | sharing | `CWB-SHARE-002` | `SharingRules:Case` |
| 8 | automation | `CWB-AUT-022` | `ApexTrigger:CaseMilestoneTrigger` |
| 8 | automation | `CWB-AUT-023` | `ApexClass:CaseMilestoneService` |
| 8 | automation | `CWB-AUT-024` | `ApexClass:CaseMilestoneServiceTest` |
| 8 | automation | `CWB-AUT-025` | `ApexClass:TestDataFactory` |
| 8 | automation | `CWB-AUT-026` | `Flow:Case_BeforeSave_StampEntitlementAndCalendar` |
| 8 | automation | `CWB-AUT-027` | `FlowTest:Case_BeforeSave_StampEntitlementAndCalendar_Test` |
| 8 | automation | `CWB-AUT-028` | `Settings:Flow` |
| 8 | automation | `CWB-LAYOUT-010` | `ReportFolder:Support_Operations` (`reports/Support_Operations-meta.xml`) |
| 8 | automation | `CWB-LAYOUT-011` | `Report:Support_Operations/Escalated_Open_Cases` |
| 9 | routing | `CWB-AUT-001` | `Group:Support_Tier_1` |
| 9 | routing | `CWB-AUT-002` | `Group:Support_Tier_2` |
| 9 | routing | `CWB-AUT-003` | `Group:Billing_Team` |
| 9 | routing | `CWB-AUT-004` | `Queue:Tier_1_General` |
| 9 | routing | `CWB-AUT-005` | `Queue:Tier_2_Engineering` |
| 9 | routing | `CWB-AUT-006` | `Queue:Billing` |
| 9 | routing | `CWB-AUT-007` | `Settings:Case` |
| 9 | routing | `CWB-AUT-010` | `AssignmentRules:Case` |
| 9 | routing | `CWB-AUT-011` | `AutoResponseRules:Case` |
| 10 | SLA | `CWB-AUT-013` | `Settings:BusinessHours` |
| 10 | SLA | `CWB-AUT-015` | `EntitlementProcess:First_Response_Premier` |
| 10 | SLA | `CWB-AUT-016` | `EntitlementProcess:First_Response_Standard` |
| 10 | SLA | `CWB-AUT-017` | `MilestoneType:First Response` |
| 10 | SLA | `CWB-AUT-019` | `EscalationRules:Case` |

*49 row(s) carry an explicit slot position. 48 more are manifests, per-step deploy-order notes, and other documentation artefacts explicitly marked "not a component" in their own row (they travel with the components above them, never as a separately-sequenced deploy item) — listed below rather than folded silently into the table. 6 are components the ten-slot sequence itself has no slot for (CustomPermission, BusinessProcess, CompactLayout, EmailFolder/EmailTemplate, ValidationRule) — each one's own row names its real constraint as a position *inside its own step* instead, per `agents/build-doc-keeper/AGENT.md` Step 5's own acknowledgement that the ten-slot sequence does not cover every deployable type.*

## Not a component (manifests, deploy-order notes, decision records)

| Row id | Artefact |
|---|---|
| `CWB-AUT-008` | `email-to-case-routing-addresses.md` in `artefacts/M3-S03/` |
| `CWB-AUT-009` | `web-to-case-form-contract.md` in `artefacts/M3-S03/` |
| `CWB-AUT-012` | `owner-writer-map.md` in `artefacts/M3-S04/` |
| `CWB-AUT-014` | `holiday-maintenance-runbook.md` in `artefacts/M4-S01/` |
| `CWB-AUT-018` | `milestone-completion-decision.md` in `artefacts/M4-S02/` |
| `CWB-AUT-020` | `escalation-activation-runbook.md` in `artefacts/M4-S04/` |
| `CWB-AUT-021` | `escalation-monitoring-note.md` in `artefacts/M4-S04/` |
| `CWB-AUT-029` | `flow-governance-policy.yaml` in `artefacts/M4-S03/` |
| `CWB-AUT-030` | `no-account-fallback-note.md` in `artefacts/M4-S03/` |
| `CWB-LAYOUT-006` | `sender-identity-note.md` in `artefacts/M3-S02/` |
| `CWB-OTHER-001` | `artefacts/M1-S01/package.xml` |
| `CWB-OTHER-002` | `artefacts/M1-S01/deploy-order.md` |
| `CWB-OTHER-003` | `artefacts/M1-S01/record-type-decision.md` |
| `CWB-OTHER-004` | `artefacts/M1-S02/package.xml` |
| `CWB-OTHER-005` | `artefacts/M1-S02/deploy-order.md` |
| `CWB-OTHER-006` | `artefacts/M2-S01/package.xml` |
| `CWB-OTHER-007` | `artefacts/M2-S01/deploy-order.md` |
| `CWB-OTHER-008` | `artefacts/M2-S02/package.xml` |
| `CWB-OTHER-009` | `artefacts/M2-S02/deploy-order.md` |
| `CWB-OTHER-010` | `artefacts/M2-S04/package.xml` |
| `CWB-OTHER-011` | `artefacts/M2-S04/deploy-order.md` |
| `CWB-OTHER-012` | `artefacts/M2-S04/queue-retirement-runbook.md` |
| `CWB-OTHER-013` | `artefacts/M2-S03/package.xml` |
| `CWB-OTHER-014` | `artefacts/M2-S03/deploy-order.md` |
| `CWB-OTHER-015` | `artefacts/M2-S05/package.xml` |
| `CWB-OTHER-016` | `artefacts/M2-S05/deploy-order.md` |
| `CWB-OTHER-017` | `artefacts/M3-S01/package.xml` |
| `CWB-OTHER-018` | `artefacts/M3-S01/deploy-order.md` |
| `CWB-OTHER-019` | `artefacts/M3-S02/package.xml` |
| `CWB-OTHER-020` | `artefacts/M3-S02/deploy-order.md` |
| `CWB-OTHER-021` | `artefacts/M3-S03/package.xml` |
| `CWB-OTHER-022` | `artefacts/M3-S03/deploy-order.md` |
| `CWB-OTHER-023` | `artefacts/M3-S04/package.xml` |
| `CWB-OTHER-024` | `artefacts/M3-S04/deploy-order.md` |
| `CWB-OTHER-025` | `artefacts/M4-S01/package.xml` |
| `CWB-OTHER-026` | `artefacts/M4-S01/deploy-order.md` |
| `CWB-OTHER-027` | `artefacts/M4-S02/package.xml` |
| `CWB-OTHER-028` | `artefacts/M4-S02/deploy-order.md` |
| `CWB-OTHER-029` | `artefacts/M4-S04/package.xml` |
| `CWB-OTHER-030` | `artefacts/M4-S04/deploy-order.md` |
| `CWB-OTHER-031` | `artefacts/M4-S05/deploy-order.md` |
| `CWB-OTHER-032` | `artefacts/M4-S03/package.xml` |
| `CWB-OTHER-033` | `artefacts/M4-S03/deploy-order.md` |
| `CWB-OTHER-034` | `artefacts/M5-S01/package.xml` |
| `CWB-OTHER-035` | `artefacts/M5-S01/deploy-order.md` |
| `CWB-OTHER-036` | `artefacts/M5-S03/story-backlog.md` |
| `CWB-SHARE-003` | `case-visibility-model.md` in `artefacts/M2-S05/` |
| `CWB-VR-003` | `validation-bypass-note.md` in `artefacts/M3-S01/` |

## No slot in the ten-position sequence (positioned inside their own step instead)

| Row id | Artefact |
|---|---|
| `CWB-LAYOUT-003` | `EmailFolder:case_intake` in `artefacts/M3-S02/email/case_intake.emailFolder-met |
| `CWB-LAYOUT-004` | `EmailTemplate:case_intake/Case_Acknowledgement` |
| `CWB-LAYOUT-005` | `EmailTemplate:case_intake/Case_Escalated_To_Tier2` |
| `CWB-OBJ-006` | `CompactLayout:Case.Case_Intake` |
| `CWB-PERM-001` | `CustomPermission:Bypass_Case_Intake_Validation` |
| `CWB-VR-001` | `ValidationRule:Case.Priority_Required_On_Agent_Save` in `artefacts/M3-S01/objec |

## Cross-step sequencing hazards named in the sources

Collated from workbook row notes rather than re-derived — each one is quoted, not resolved, per Step 10's "a conflict between two steps' notes is reported rather than silently resolved":

- **`M3-S03` before `M3-S04`, in the wrong direction for safety.** `CWB-AUT-007`'s notes: "before `M3-S04`'s `AssignmentRules`/`AutoResponseRules`, per `deploy-order.md` §§ 2-3's safe-sequence warning (enabling the channels before the rules exist means live traffic lands unrouted)." The plan deploys `M3-S03` (Email/Web-to-Case channels) ahead of `M3-S04` (the routing rules) in step order; the safe sequence the source itself names is the reverse.
- **`M3-S04` cites `M2-S04` queues and `M1-S01`'s `CaseOrigin` value set as deploy-time predecessors** (`CWB-AUT-010` notes) — already satisfied by milestone order (M2, M1 both precede M3), named here because the per-step file states it as a hard precondition rather than an ordering nicety.
- **`M4-S04`'s escalation rule depends on `M3-S02`'s email template, `M2-S04`'s Tier 2 queue and `M1-S01`'s `Severity__c` field** (`CWB-AUT-019` notes) — again satisfied by milestone order, named because the source states it as absolute ("last in the ten-slot sequence and last of everything it names").
- **`M4-S02`'s two `EntitlementProcess` files need `MilestoneType` deployed first, in the same request** (`CWB-AUT-015`/`016`/`017` notes) — an intra-step ordering constraint, not cross-step, reproduced here because it is the one case in the build where deploying the step's own manifest in file order rather than dependency order would fail.
- **`M2-S04`'s three groups must deploy before their queues, and before `M3-S04`'s assignment rules, `M3-S05`'s (blocked) Omni-Channel push and `M4`'s escalation rules all of which name these queues by developer name** (`CWB-OTHER-011` notes).

**Undeclared `deploy-order.md` pattern.** Nine consecutive steps from `M3-S02` onward (through `M5-S01`) never declared their own `deploy-order.md` in `outputs[]`, per the running count `workbook/99-other-configuration.md` keeps in each step's row notes (`decisions.md` **O-M3S02-03**) — `check-outputs` still confirmed the file exists on disk each time (`check-outputs` reads the filesystem, not `outputs[]`, for this check), so no step failed on it, but the plan's own declared surface understates what each step actually produced. `M1-S01` and `M1-S02` are the two earliest, still-open instances of the same gap. Recorded here rather than re-opened per step, per that same decision entry.


---

## Org prerequisites (reconciled, F-56)

Added at this re-run to close `reports/MILESTONE-M5-REPORT.md` finding **F-56** (MEDIUM):
`artefacts/M5-S05/deploy-order.md` § 5.2 numbers six org prerequisites 1-6; `artefacts/M5-S03/story-backlog.md`
numbers overlapping prerequisites P1-P6 inline in its stories' `Dependencies`; the two lists were
numbered independently, cross-referenced each other nowhere, and did not hold the same items. This
table adopts `M5-S05` § 5.2's numbering as canonical — per the report's recommendation, because it
is the document a release owner deploys from — extends it with the one item only the backlog
carried (sandbox deliverability, P6), and cites both numberings side by side so neither reader is
stranded.

| # | Prerequisite | `M5-S05` § 5.2 | Backlog P-label | Status |
|---|---|---|---|---|
| 1 | `support-noreply@acme.example` verified `OrgWideEmailAddress` before `AutoResponseRules:Case` deploys (F-28) | #1 | P4 | Open |
| 2 | `enableEntitlements` + `enableMilestoneStoppedTime` before go-live (F-39) | #2 | P1 | Open |
| 3 | Non-routing mailboxes on the Billing / Tier 2 Engineering queues before the escalation rule is activated (F-44) | #3 | P2 | Open |
| 4 | An `Entitlement` record per Account, pointing at the right process (F-41) | #4 | absent from the backlog | **Open — see `CWB-DATA-001` below** |
| 5 | The report's "Escalated = True" criterion, added in the report builder after deploy (F-51) | #5 | present as prose, no P-number | Open by design |
| 6 | An active `SlaProcess` carrying a First Response milestone, for `M4-S05`'s `SeeAllData=true` test (G4 decision 9) | #6 | P5 | Open |
| 7 | Sandbox deliverability raised above System Email Only, Contact emails scrubbed first (Q78) | not in `M5-S05` § 5.2 | P6 | Open |

Row 4's status is bolded because it is the one this compile run actually changes: **`CWB-DATA-001`**,
added to `workbook/`'s Section 10 at this same re-run (`artefacts/M5-S04/configuration-workbook.md`),
is the first appearance of the `Entitlement`-per-Account prerequisite in any compiled document —
before this run it lived only in `M5-S05`'s deploy-order note and the M4 milestone report, appearing
in the compiled configuration workbook zero times (F-56's own measurement). Rows 1, 2, 3, 5 and 6
are unchanged by this run: they already existed as `M5-S05` § 5.2's own numbered list, cited here
rather than duplicated.

**Not done here, and named as an open obligation rather than silently left:** the report's second
recommendation — renumbering `story-backlog.md`'s P-labels to match, or dropping them for explicit
names, and adding F-41 to `US-CASE-007`'s `dependencies[]` — touches `artefacts/M5-S03/story-backlog.md`,
which `M5-S03` (`story-drafter`) owns. `agents/build-doc-keeper/AGENT.md`'s compile-run Scope
Guardrails permit this run to write only under `artefacts/M5-S04/`, so the backlog itself is
unchanged. A human, or a future `story-drafter` touch, still needs to make that edit.
