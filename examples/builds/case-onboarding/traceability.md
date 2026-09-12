# Traceability — REQ → step → artefact → test

Written by the build doc keeper.

Format: the build-layer RTM defined by `skills/admin/requirements-traceability-matrix`
(SKILL.md § "The Build-Layer RTM: `traceability.md`", worked through in
`references/worked-examples.md` § 4). The ten canonical build columns come first;
`artefact_paths` and `test_result` follow them because `agents/build-doc-keeper/AGENT.md`
Step 7 requires those two cells and the canonical set has no column for either.
Lint with:

```bash
python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py \
  --file traceability.md --manifest-dir artefacts/M1-S01 --repo-root ../../..
```

---

## Matrix

| req_id | source | requirement | step_id | artefact | agent | decision_ref | test_id | test_type | status | artefact_paths | test_result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | Q1 | Support work from support@, the web form and manual agent entry is a case process of its own | M1-S01 | `RecordType:Case.Support` | metadata-builder | — | M1-S01-T1 | checker | In Build | `artefacts/M1-S01/objects/Case/recordTypes/Support.recordType-meta.xml` | pass — `check_record_type_layouts.py --manifest-dir artefacts/M1-S01` exit 0, `2 record type(s), 0 layout(s); 0 finding(s) detected.` Also covered by `xml` (parsed) and `manifest` (member ↔ file, both directions). Record-type-to-layout cross-reference is NOT asserted at this scope — 0 layouts were in view; M1's milestone test at `--manifest-dir artefacts` carries it once M1-S02 lands. **Re-tested after rebuild #2 (F-11), run `2026-09-09T19-52-47Z`:** same command, exit 0, `score 100`, 0 findings. Both record-type files were rewritten in that rebuild — `<businessProcess>` now names the process **file stem** (`Support_Process` / `Billing_Process`) rather than the spaced display name — and `check_case_management_setup.py` rule CMS-STEM-02 exits 0 on them, run observation-only because the step declares no such test. `decisions.md` D-M1S01-05. |
| REQ-002 | Q1 | Finance queries arriving at billing@ are a case process of their own, worked by Finance | M1-S01 | `RecordType:Case.Billing` | metadata-builder | — | M1-S01-T1 | checker | In Build | `artefacts/M1-S01/objects/Case/recordTypes/Billing.recordType-meta.xml` | pass — same run as REQ-001, before and after rebuild #2; this file's `<businessProcess>` reads `Billing_Process`. |
| REQ-003 | Q2 | The support status ladder exposes an Escalated state, because untouched support cases hand off to Tier 2 | M1-S01 | `BusinessProcess:Case.Support_Process` | metadata-builder | — | TC-M1S01-01 | manual | In UAT | `artefacts/M1-S01/objects/Case/businessProcesses/Support_Process.businessProcess-meta.xml` | outstanding — manual, ticked at the M1 gate. Machine coverage so far: `xml` parsed; `manifest` resolved `BusinessProcess:Case.Support_Process` ↔ file in both directions (member name changed by rebuild #2; the file stem did not). **Rebuild #2 (F-11):** `<fullName>` `Support Process` → `Support_Process`, so stem and `fullName` now agree and the source-format deploy resolves the member — validated by the 12/12 dry run in `reports/MOCK-DEPLOY-M1.md` § "Mock deploy #2" and enforced going forward by `check_case_management_setup.py` CMS-STEM-01 (observation-only here, exit 0). `decisions.md` D-M1S01-05. Status values (New/Escalated/Closed) are a builder default, not a customer-confirmed set — see `decisions.md` D-M1S01-01. |
| REQ-004 | Q2 | The billing status ladder has no Escalated state: Tier 2 engineering is not the escalation target for a finance query | M1-S01 | `BusinessProcess:Case.Billing_Process` | metadata-builder | — | TC-M1S01-01 | manual | In UAT | `artefacts/M1-S01/objects/Case/businessProcesses/Billing_Process.businessProcess-meta.xml` | outstanding — manual, ticked at the M1 gate. Same machine coverage as REQ-003, and the same rebuild #2 change: `<fullName>` `Billing Process` → `Billing_Process`, manifest member `Case.Billing_Process`. `decisions.md` D-M1S01-05. |
| REQ-005 | Q19 | Each intake channel stamps a Case Origin value that routing can filter on; there is no phone value | M1-S01 | `StandardValueSet:CaseOrigin` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml` | pass — `manifest` two-way, `StandardValueSet:CaseOrigin` ↔ file, 0 findings, no wildcards; `xml` parsed. The three values (Email-Support, Email-Billing, Web) are exposed on the record types and checked there by `check_record_type_layouts.py` exit 0. Downstream consumers (`CaseSettings.webToCase.caseOrigin`, the Email-to-Case addresses) are M3 and are not asserted here. |
| REQ-006 | Q83 | Agents on Lightning desktop see case identity and state at a glance on every Case record type | M1-S01 | `CompactLayout:Case.Case_Intake` | metadata-builder | — | M1-S01-T2 | checker | In UAT | `artefacts/M1-S01/objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml` | pass — `check_list_views_and_compact_layouts.py --manifest-dir artefacts/M1-S01` exit 0, `No issues found.` That exit covers the compact layout, its `compactLayoutAssignment` on the CustomObject and on both record types, and the field-type lookup against `objects/Case/fields/`. **Re-tested after rebuild #3 (F-13), run `2026-09-12T00-21-00Z`:** same command, exit 0, CL-MEM-01 clean. `artefact` changed from the bare `CompactLayout:Case_Intake` to the object-qualified form shown here — `package.xml`'s `CompactLayout` member was rewritten to match, closing the resolution failure this row carried while the manifest and the row disagreed (§ "Linter result — after M2-S02"). `decisions.md` D-M1S01-06; `O-M1S01-03` closed. |
| REQ-007 | Q38 | A Severity 1 outage is identifiable on the Case so it can run on the 24/7 calendar and never pause | M1-S01 | `CustomField:Case.Severity__c` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml` | pass — `manifest` two-way, `CustomField:Case.Severity__c` ↔ file; `xml` parsed; the field is named by the compact layout, which `check_list_views_and_compact_layouts.py` resolved. **Field content was not machine-checked**: `check_object_creation_and_design.py` returns before any assertion for a file stem not ending `__c` (script L146–148), so its exit 0 says nothing about `Case` or its fields. The single value `Severity 1` is a recorded open item — `decisions.md` D-M1S01-02. |
| REQ-008 | Q40 | A case's SLA calendar is resolvable at creation from the account's region | M1-S01 | `CustomField:Account.Region__c` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/objects/Account/fields/Region__c.field-meta.xml` | pass — `manifest` two-way, `CustomField:Account.Region__c` ↔ file; `xml` parsed. Same field-content gap as REQ-007. The deliberate absence of a field default is recorded in `decisions.md` D-M1S01-04; the US fallback for unknown accounts is M4-S03's flow, not this field. |
| REQ-009 | Q38 | The first-response target (4 business hours vs 1 business day) is selectable from the account's contracted tier | M1-S01 | `CustomField:Account.Support_Tier__c` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/objects/Account/fields/Support_Tier__c.field-meta.xml` | pass — `manifest` two-way, `CustomField:Account.Support_Tier__c` ↔ file; `xml` parsed. Same field-content gap as REQ-007. Consumed by M4-S02's entitlement process, which is not asserted here. |
| REQ-010 | Q13 | A Tier 1 agent cannot open a Billing case at all — record-level restriction, not a hidden field | M1-S01 | `CustomObject:Case` | metadata-builder | D5 | TC-M1S01-02 | manual | In UAT | `artefacts/M1-S01/objects/Case/Case.object-meta.xml` | outstanding — manual, ticked at the M1 gate; `tests/M1-S01/manual-evidence.stdout` records the disk evidence (`sharingModel=Private`, `externalSharingModel=Private`, no `*.settings-meta.xml` anywhere under `artefacts/`). The machine assertion that the OWD is not looser than the sharing rule's grant is M2-S05's build-scoped `check_sharing_model.py` test, which needs both files and has not run. |
| REQ-011 | Q5 | A support agent works a support case on a Case page of its own, carrying the severity flag a 24/7 outage needs | M1-S02 | `Layout:Case-Case Support Layout` | metadata-builder | — | M1-S02-T1 | checker | In UAT | `artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml` | pass — **re-tested after rebuild #2** (`step-tester` run `2026-09-09T19-50-27Z`). `check_record_type_layouts.py --manifest-dir artefacts/M1-S02` exit 0, `score 100`, `Scanned 2 metadata file(s): 0 record type(s), 2 layout(s); 0 finding(s) detected.` The two `INFO` lines build #1 produced are gone because both layouts now mark `Status` `behavior=Required`, and this exit 0 asserts strictly more than build #1's identical exit 0: the checker gained ERROR rules **RL-REQ-01** and **RL-REQ-02** at skill v1.2.0, and against build #1's layouts the same command exits **1** with four RL-REQ ERRORs. Also `xml` (3 of 3 parsed) and `manifest` (2 members ↔ 2 files, both directions, 0 failures) — `package.xml` is unchanged, because the rebuild added items inside two existing components rather than a component. **What changed in the artefact:** `SuppliedEmail`, `Description` and `ContactId` added as `layoutItems`; `Status` moved from `Edit` to `Required`; twelve fields now, nine before — `decisions.md` D-M1S02-05, driven by `reports/MOCK-DEPLOY-M1.md` F-09/F-10. **Independent evidence:** mock deploy #2 validated 12 of 12 components with this file copied unmodified. **Record-type-to-layout cross-reference still NOT asserted at this scope** — 0 record types were in view, the mirror image of M1-S01's 0 layouts; M1's milestone test at `--manifest-dir artefacts` is the only run that sees both. `Severity__c` is on this layout and not on Billing: `decisions.md` D-M1S02-02. Manual half outstanding — see REQ-013 and REQ-014. **Stale downstream:** `reports/MILESTONE-M1-REPORT.md` and the `milestone:M1` gate note describe build #1 (O-M1S02-03). |
| REQ-012 | Q5 | Finance work a billing case on a page of its own, with no severity concept on it | M1-S02 | `Layout:Case-Case Billing Layout` | metadata-builder | — | M1-S02-T1 | checker | In UAT | `artefacts/M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml` | pass — same re-tested run as REQ-011, same exit 0 with `0 finding(s)`, and the same named cross-reference gap. Eleven fields now, eight before: identical to the Support layout minus `Severity__c` and the `emptySpace`, with the same three fields added and the same `Status` behavior change (`decisions.md` D-M1S02-05; `reports/MOCK-DEPLOY-M1.md` F-09/F-10). Neither layout is assigned to anyone yet: `layoutAssignments` lives only on `Profile`, which is M2-S03's in plan v5 (`decisions.md` O-M2S01-01), so both deploy and neither is reachable — recorded in `artefacts/M1-S02/deploy-order.md` and in workbook Section 2's preamble. Mock deploy #2 validated this file unmodified as 1 of the 12. **Stale downstream:** the M1 report and the `milestone:M1` gate note predate the rebuild (O-M1S02-03). |
| REQ-013 | Q24 | A case logged by hand goes through the active assignment rule from the page the agent uses | M1-S02 | `Layout:Case-Case Support Layout` | metadata-builder | — | TC-M1S02-01 | manual | In UAT | `artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml` \| `artefacts/M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml` | outstanding — manual, ticked at the M1 gate, and **tickable only in part**. Unchanged by rebuild #2: the rebuild added three fields and one `behavior` and touched no `show*` element. Machine coverage: `xml` parsed, `manifest` resolved both members ↔ both files. Disk evidence **re-captured after the rebuild** in `tests/M1-S02/manual-evidence.stdout` and identical to the 2026-09-06 capture on this half: `<showRunAssignmentRulesCheckbox>` present and `true` on both layouts, so the **presence** reading passes; the test's literal **positional** reading ("`<layoutSections>` is preceded by the checkbox") still fails on both, because the cited skill's own example places every `show*` element after the final `</layoutSections>` and both artefacts match it exactly. The tester applied the presence reading and recorded why. Q24's "defaulted on" half is **unproven and unprovable from the artefacts** — no element in the cited skill's inventory pre-checks the box, and skill v1.2.0 did not add one; it addressed F-09/F-10 only (`decisions.md` D-M1S02-03, D-M1S02-05). The gate must either accept the narrowing or route the remainder to a recorded Setup step. **Why `artefact` names one layout and `artefact_paths` names two:** `check_rtm.py` applies its pipe-delimited multi-value split to the story and test id columns only — `artefact` is read as a single value (script L626 versus L592–593) — so the column names the layout the requirement carries the most traffic on (support intake is ~460 cases a day against billing's share of the rest) and both files stay in `artefact_paths`. The element is identical on both. |
| REQ-014 | Q57 | Every field a validation rule attaches its error to is visible on the page where that error appears | M1-S02 | `Layout:Case-Case Billing Layout` | metadata-builder | — | TC-M1S02-01 | manual | In UAT | `artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml` \| `artefacts/M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml` | outstanding — manual, and **still not file-checkable at M1-S02 time**. `Priority` and `Origin` are present on both layouts, which is what assumption **A13** needs for the two rules `M3-S01` declares (`Priority_Required_On_Agent_Save`, `Origin_Must_Be_Known`). Rebuild #2 widened the satisfied surface rather than narrowing it: `ContactId`, `Description` and `SuppliedEmail` are now on **both** layouts (`decisions.md` D-M1S02-05), so a rule attaching its error to any of the three would satisfy A13 on both. But no `ValidationRule` metadata exists anywhere under `artefacts/` yet — `M3-S01` is `pending` — so there is no `errorDisplayField` to resolve and nothing to check against; re-capturing the evidence after the rebuild returned the same `ValidationRule files anywhere under artefacts/: none`. Carry-forward the M1 gate should see: `Severity__c` is on the Support layout only, so a third Case rule attaching its error to that field would fail A13 on the Billing layout. Q57 is **deferred**; A13 is the standing assumption at `risk: medium`. **Why `artefact` names the Billing layout:** same single-value column as REQ-013, and this is the layout the assumption is at risk on — it is the one missing `Severity__c`. Both files are in `artefact_paths`. |
| REQ-015 | Q56 | Cases created by the email and web intake channels are never blocked by a Case validation rule written for agent-entered cases | M2-S01 | `CustomPermission:Bypass_Case_Intake_Validation` | metadata-builder | — | M2-S01-T1 | checker | In Build | `artefacts/M2-S01/customPermissions/Bypass_Case_Intake_Validation.customPermission-meta.xml` | pass — `check_custom_permissions.py --manifest-dir artefacts/M2-S01` exit 0: `Custom permissions defined: 1 / Permission sets / profiles parsed: 1 / Distinct permissions referenced: 0`, coverage row `Bypass_Case_Intake_Validation  0  permission set 'Case_Intake_Integration'`, `0 error(s), 0 warning(s), 0 info`. Also `xml` (3 of 3 parsed) and `manifest` (2 members ↔ 2 files, both directions). **What that exit proves:** the grant is not dangling — the permission set names a permission a file in the tree defines. **What it does not:** the consumer side. `Consumers` is 0 because no validation rule is in scope, and deleting the grant entirely would still exit 0 (the plan's own test description says so). The consumer cross-reference is M3's milestone test, which runs the same checker at `--manifest-dir artefacts --strict` once `M3-S01` writes `Priority_Required_On_Agent_Save` and `Origin_Must_Be_Known` — each carrying `NOT($Permission.Bypass_Case_Intake_Validation)` as its outer AND term. **Status is `In Build`, not `In UAT`:** `M3-S01` is `pending` and depends on this step, so a step that serves this requirement remains. The consumer names written into the permission's `<description>` come from `plan.json` `steps[M3-S01].outputs[]`, not from any clarification — `decisions.md` D-M2S01-01. |
| REQ-016 | Q56 | The intake bypass is held by an integration-only grant that carries nothing else and reaches no human user | M2-S01 | `PermissionSet:Case_Intake_Integration` | metadata-builder | — | TC-M2S01-01 | manual | In UAT | `artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml` \| `artefacts/M2-S01/deploy-order.md` | machine half **pass**, manual half **outstanding**. Machine: `check_access_model.py --manifest-dir artefacts/M2-S01` exit 0, `score 100`, `Scanned 1 access-model metadata file(s); 0 finding(s)` — no dangerous system permission rides along; the checker returns 1 on any finding and exits 1 on an empty directory (W09, confirmed from source), so exit 0 stands for a file actually scanned. Plus `check_permission_set_architecture.py` exit 0 (`No issues found.`, the builder's self-check, not a declared test), `manifest` two-way and `xml` parse. Manual: **`TC-M2S01-01`**, ticked at the M2 gate. The file-checkable half is already evidenced — `tests/M2-S01/manual-evidence.stdout.txt` records four top-level elements, one grant-bearing element present (`customPermissions`), thirteen absent, `ASSERTION 'grants the bypass and nothing else': HOLDS`, and both the post-deploy instruction and the named owner `PRESENT` in `deploy-order.md`. **The residue is not evidenceable in this build at all:** whether the assignment was made to the integration identity and to no human user is `PermissionSetAssignment` record data, not metadata, which is why plan-verifier blocker **B01** rewrote this test as an assertion over the artefacts rather than over an org. Two recorded absences the gate should see: `ApiEnabled` is deliberately not granted (`decisions.md` D-M2S01-02) and the grant carries no expiry (D-M2S01-03). Q10 (additive, no strip phase) and Q8 (LicenseId left empty) are the two answers that shape what this set does **not** carry. |
| REQ-017 | Q9 | Every Case-working persona shares one baseline object/field/tab access footprint before any persona-specific grant is layered on | M2-S02 | `PermissionSet:Case_Agent_Core` | metadata-builder | — | M2-S02-T3 | checker | In UAT | `artefacts/M2-S02/permissionsets/Case_Agent_Core.permissionset-meta.xml` | pass — `check_access_model.py --manifest-dir artefacts/M2-S02` exit 0, `score 100`, `Scanned 7 access-model metadata file(s); 0 finding(s)` (this file is 1 of the 7 scanned); `check_permission_set_architecture.py --manifest-dir artefacts` exit 0, `No issues found.` (build scope, cross-referential per `standards/build-orchestration.md` § 5). Also `manifest` (part of the 4-member `PermissionSet` block, both directions consistent) and `xml` parsed. **CRUD levels were read from `requirement.md`, not from an answered clarification** — Q9 answers the object list only; `decisions.md` D-M2S02-01. No `viewAllRecords`/`modifyAllRecords`, no `userPermissions`, no `viewAllFields`: `decisions.md` D-M2S02-02, D-M2S02-03, D-M2S02-04. Composed into all three PSGs (`REQ-018`, `REQ-019`, `REQ-020`). **Re-tested after rebuild #2 (F-15), run `2026-09-12T01-26-00Z`:** `<description>` trimmed 419→192 chars for the Metadata API's 255-char ceiling; every grant-bearing element unchanged. `check_access_model.py --manifest-dir artefacts/M2-S02` exit 0 (score 100, 0 findings) and `check_permission_set_architecture.py --manifest-dir artefacts` exit 0 (build scope), both now enforcing the new PSA-DESC-01/02 / PSVP-DESC-01 length rules with no DESC finding on this file. `decisions.md` D-M2S02-07. **Re-tested after rebuild #3 (F-60, `reports/MOCK-DEPLOY-M5.md` run 5), run `2026-09-12T17-46-35Z`:** seven `fieldPermissions` added to this file for the standard Case fields the persona writes (`Case.AccountId`, `Case.ContactId`, `Case.Description`, `Case.Origin`, `Case.Priority`, `Case.Subject`, `Case.SuppliedEmail`, each grounded in a layout or a milestone finding; `EntitlementId`/`Type`/`Reason` deliberately excluded — `decisions.md` D-M2S02-08); `<description>` reworded (193 chars). `check_access_model.py --manifest-dir artefacts/M2-S02` exit 0, score 97, 1 finding (down from 2 pre-edit) — the Case-object PSVP-FLS-01 WARN this repair targeted is gone; one non-blocking PSVP-FLS-01 WARN remains on this file's `EmailMessage` grant, left as a named ambiguity for the human gate because no layout, workbook row or decision names which standard `EmailMessage` fields a reply populates (`decisions.md` O-M2S02-02). `check_permission_set_architecture.py --manifest-dir artefacts` and `check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02` both still exit 0; `manifest` and `xml` unchanged (`package.xml` untouched). Org evidence: `reports/MOCK-DEPLOY-M5.md` run 6 — the persona test now creates and updates the Case (F-59/F-60 closed by the org); `decisions.md` O-M2S02-03. |
| REQ-018 | Q13 | Tier 1 agents work Support cases and set the severity flag when triaging an outage | M2-S02 | `PermissionSet:Case_Tier1` | metadata-builder | — | M2-S02-T2 | checker | In Build | `artefacts/M2-S02/permissionsets/Case_Tier1.permissionset-meta.xml` \| `artefacts/M2-S02/permissionsetgroups/PSG_Tier1_Prod.permissionsetgroup-meta.xml` | pass — `check_access_model.py` (1 of 7 files scanned, 0 findings), `check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02` exit 0 (`GOOD: reuse: permission set 'Case_Agent_Core' is referenced by 3 PSGs`), `manifest` two-way, `xml` parsed. **`recordTypeVisibilities` grants `Case.Support`** — which record types each persona may pick is Q13's answer_shape, answered here as a **record type** grant even though Q13 itself is **deferred** on the record-**access** question; the conservative reading (assumption A1) is what makes `Case_Billing` withhold this same record type (`REQ-020`). **Status is `In Build`, not `In UAT`:** whether a Tier 1 agent can actually *open* a Support case is the Private OWD (M1-S01, built) plus the M2-S05 criteria-based sharing rule, which is `pending` and depends on neither this step nor A1 naming it (see "What M2-S02 rests on" below) — a step that serves this requirement remains. `Case_Tier2`'s grant is byte-identical: `decisions.md` D-M2S02-05. **Re-tested after rebuild #2 (F-15), run `2026-09-12T01-26-00Z`:** `<description>` trimmed 290→193 chars; grant set unchanged. `check_access_model.py` (1 of 7 files, 0 findings) and `check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02` exit 0 (`GOOD: reuse`), both now enforcing PSA-DESC-01/02 / PSGC-DESC-01/02 with no DESC finding. `decisions.md` D-M2S02-07. |
| REQ-019 | Q13 | Tier 2 engineers who take escalated Support cases need the same working footprint as Tier 1 | M2-S02 | `PermissionSet:Case_Tier2` | metadata-builder | — | M2-S02-T2 | checker | In Build | `artefacts/M2-S02/permissionsets/Case_Tier2.permissionset-meta.xml` \| `artefacts/M2-S02/permissionsetgroups/PSG_Tier2_Prod.permissionsetgroup-meta.xml` | pass — same composition-checker run as `REQ-018` (1 of 3 PSG files, part of the reuse-GOOD finding), `check_access_model.py` (1 of 7 files, 0 findings), `manifest` two-way, `xml` parsed. **No answered clarification distinguishes Tier 2's access from Tier 1's** — the requirement's Tier 1/Tier 2 split is routing (pushed vs pulled work) and escalation (untouched 8 business hours), both later-milestone concerns (M2-S04, M3, M4), not access; two sets exist because `outputs[]` declares two. Same `In Build` reasoning as `REQ-018`: M2-S05 remains pending. `decisions.md` D-M2S02-05 (the identical-grant open item). **Re-tested after rebuild #2 (F-15), run `2026-09-12T01-26-00Z`:** `<description>` trimmed 456→199 chars; grant set unchanged. `check_access_model.py` (1 of 7 files, 0 findings) and `check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02` exit 0, both now enforcing PSA-DESC-01/02 / PSGC-DESC-01/02 with no DESC finding. `decisions.md` D-M2S02-07. |
| REQ-020 | Q13 | Finance sees only Billing cases and has no need to edit Case severity | M2-S02 | `PermissionSet:Case_Billing` | metadata-builder | — | M2-S02-T2 | checker | In Build | `artefacts/M2-S02/permissionsets/Case_Billing.permissionset-meta.xml` \| `artefacts/M2-S02/permissionsetgroups/PSG_Billing_Prod.permissionsetgroup-meta.xml` | pass — same composition-checker run (1 of 3 PSG files), `check_access_model.py` (1 of 7 files, 0 findings), `check_permission_set_architecture.py` (build scope, `No issues found.`), `manifest` two-way, `xml` parsed. **Q13, deferred → assumption A1, conservative reading:** `recordTypeVisibilities` grants `Case.Billing` only — the Support record type is deliberately withheld, the mirror image of `REQ-018`/`REQ-019`. **`Severity__c` read-only for Billing is a builder reading of the requirement, not a hardcoded assumption:** this file carries **no `fieldPermissions` element at all** for `Severity__c`; the read-only access Billing ends up with is inherited entirely from `Case_Agent_Core` through `PSG_Billing_Prod`, and nothing in `Case_Billing` itself grants edit. Grounded in `requirement.md` L18 ("Severity 1 outages are 24/7 and never pause" — the only source naming a severity, and it names an outage, not a finance query) and the builder's own decision record ("everyone reads `Case.Severity__c` … the two support tiers also edit `Severity__c`" — `envelopes/M2-S02/2026-09-12T00-05-00Z.json` → `extensions.decision_record[12]`). `decisions.md` D-M2S02-06. **Status is `In Build`, same reasoning as `REQ-018`/`REQ-019`:** the record-level restriction A1 stands for is M2-S05's, not this step's, and M2-S05 is `pending`. **Re-tested after rebuild #2 (F-15), run `2026-09-12T01-26-00Z`:** `<description>` trimmed 380→183 chars; grant set unchanged, including the absent `fieldPermissions` block for `Severity__c`. `check_access_model.py` (1 of 7 files, 0 findings) and `check_permission_set_architecture.py` (build scope) exit 0, both now enforcing PSA-DESC-01/02 / PSVP-DESC-01 with no DESC finding. `decisions.md` D-M2S02-07. |
| REQ-021 | Q26 | Within the first minute of a case being created it must have an owner; a case matching no assignment-rule entry must resolve to an explicit fall-through queue, never fall through silently | M2-S04 | `Queue:Tier_1_General` | metadata-builder | — | M2-S04-T1 | checker | In Build | `artefacts/M2-S04/queues/Tier_1_General.queue-meta.xml` \| `artefacts/M2-S04/deploy-order.md` | pass — `check_queues.py --manifest-dir artefacts/M2-S04` exit 0, listing `Tier_1_General` with `Objects : Case`, one of the two documented WARNs (`No <email> configured` — Q88, Omni-Channel push instead). Also `xml` (7 of 7 parsed) and `manifest` (6 members ↔ 6 files, both directions, 0 findings). Manual test `M2-S04-T2` (below) additionally confirms this file's `sobjectType=Case` and presence. **`M2-S04-T1`'s own `description` is stale on the WARN count** — it predicts `Warnings found (1)`, the real run prints `Warnings found (2)` — `decisions.md` O-M2S04-01; not a defect in this row's pass condition. **Status is `In Build`, not `In UAT`:** the catch-all only routes cases once `M3-S04`'s assignment rule names it as the final entry, and `M3-S04` is `pending` — a step serving this requirement remains, the same reasoning `REQ-015`'s row states for `M3-S01`. `<queueMembers>` names no `<roles>` member though Q29 answers "by role and public group" — `decisions.md` D-M2S04-03. |
| REQ-022 | Q29 | Tier 1 (12 agents across EMEA and the US, membership changes monthly) should get work pushed to them when they are available, and that roster must not require a metadata deploy to change | M2-S04 | `Queue:Tier_1_General` | metadata-builder | — | M2-S04-T4 | manual | In Build | `artefacts/M2-S04/queues/Tier_1_General.queue-meta.xml` \| `artefacts/M2-S04/groups/Support_Tier_1.group-meta.xml` | machine half **pass**, manual half **outstanding**. Machine: `check_queues.py` exit 0 (queue + group both listed); `manifest` two-way; `xml` parsed. Manual `M2-S04-T4` (`W02 2 of 3`): **PASS on the file-checkable half** — no `<users>` element in either file; `Tier_1_General`'s `queueMembers/publicGroups/publicGroup` names exactly `Support_Tier_1` (`tests/M2-S04/results.json` skipped_manual[2]). **The roster-confirmation half — "a support manager confirms the … memberships match the current rosters" — is not file-checkable in a design-only build** and is ticked at the M2 gate. **`<doesIncludeBosses>` and roles:** `Support_Tier_1` carries `true` as a skill DEFAULT, not an answered decision; the group carries no members in this deploy (`GroupMember` is post-deploy data) — `decisions.md` D-M2S04-01. **Status is `In Build`:** "work pushed to them" is `M3-S05`'s Omni-Channel routing configuration, which is `blocked` in `plan.json` as of this run, not merely `pending` — the queue and its membership source exist, the push mechanism does not yet. |
| REQ-023 | Q13 | Tier 2 (4 engineers) pick work from a list, and receive Support cases that go untouched for 8 business hours | M2-S04 | `Queue:Tier_2_Engineering` | metadata-builder | — | M2-S04-T2 | manual | In Build | `artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml` \| `artefacts/M2-S04/groups/Support_Tier_2.group-meta.xml` | machine half **pass**, manual half **outstanding, and one criterion is a known mismatch.** Machine: `check_queues.py` exit 0, `Objects : Case`, the *second* documented WARN (`No <email> configured`); `manifest` two-way; `xml` parsed. Manual `M2-S04-T2` (six-component presence + `sobjectType=Case`): PASS. **`M2-S04-T3` (`W02 1 of 3`, email posture) does NOT hold on this artefact** — the criterion asserts `Tier_2_Engineering` "carries the Tier 2 shared mailbox"; the file carries **no `<email>` element at all**, because Q88 names only a posture with no address anywhere on file. Recorded as a mismatch, not ticked (`tests/M2-S04/results.json` skipped_manual[1]; `decisions.md` D-M2S04-02, O-M2S04-02). **Status is `In Build`:** the "pick from a list" UI is `M5-S01`'s pull list view (`pending`), and the 8-business-hour escalation target is `M4-S04`'s escalation rule (`pending`) — the queue and its membership source exist, neither downstream mechanism does yet. |
| REQ-024 | Q1 | Finance queries arrive at billing@acme.example and should be worked by Finance, through a dedicated work pool whose assignment notification goes to a monitored address | M2-S04 | `Queue:Billing` | metadata-builder | — | M2-S04-T3 | manual | In Build | `artefacts/M2-S04/queues/Billing.queue-meta.xml` \| `artefacts/M2-S04/groups/Billing_Team.group-meta.xml` | machine half **pass**, manual half **outstanding**. Machine: `check_queues.py` exit 0, `Objects : Case`, no WARN on this file (the only queue with an `<email>`); `manifest` two-way; `xml` parsed. Manual `M2-S04-T3` (`W02 1 of 3`): **PASS on Billing's half** — `<email>billing@acme.example</email>` present, matching Q88 and `requirement.md` L8 (`tests/M2-S04/results.json` skipped_manual[1]). **Risk named, not a defect:** `billing@acme.example` is also the address `M3-S03` (pending) will configure as the Email-to-Case intake address — a queue-assignment notification and a fresh inbound case can chain through the same mailbox. `decisions.md` D-M2S04-04; must be exercised by Q68's sandbox loop test before go-live. **Status is `In Build`:** `M3-S03` (Email-to-Case routing for `billing@`, `pending`) and `M5-S01` (Billing's pull list view, `pending`) both remain. |
| REQ-025 | Q89 | Queue-owned records must not be orphaned when a queue is retired: open Cases are reassigned to the surviving queue first | M2-S04 | `setup-only: queue-retirement-runbook.md` | metadata-builder | — | M2-S04-T5 | manual | In UAT | `artefacts/M2-S04/queue-retirement-runbook.md` | machine half **pass** (`check-outputs` confirms the declared file is present, non-empty), manual half **outstanding**. Manual `M2-S04-T5` (`W02 3 of 3` and S4): **PASS** — the tester confirmed all four sub-claims present: the 10,000-record ownership-skew threshold with its `skills/admin/data-skew-and-sharing-performance` SKILL.md:88 citation (§1), the named monitor (CRM admin lead) and weekly-then-monthly cadence with SOQL queries (§2), the split-into-ownership-buckets remedy (§3), and the reassign-before-delete retirement order naming `Tier_1_General` as the fall-through survivor (§4) (`tests/M2-S04/results.json` skipped_manual[3]). **Status is `In UAT`, not `In Build`:** no further step in `plan.json` depends on this artefact — it is a standalone operating note, so only the gate tick remains. |
| REQ-026 | Q7 | Tier 1 agents (12, EMEA+US) work Support cases from a base profile carrying only the default app, default record type and layout assignments — every object/field/tab grant lives in the `PSG_Tier1_Prod` permission sets | M2-S03 | `Profile:Acme Support Tier 1` | metadata-builder | — | M2-S03-T2 | checker | In Build | `artefacts/M2-S03/profiles/Acme Support Tier 1.profile-meta.xml` \| `artefacts/M2-S03/deploy-order.md` | pass — `check_record_type_layouts.py --manifest-dir artefacts --strict` exit 0, `Scanned 15 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected` — the first build-scope run to resolve any `layoutAssignments` at all (9 references) and any `Profile`-sourced record-type reference (12), closing M1 finding **F-01** (`decisions.md` D-M2S03-07); a negative fixture with one dangling reference exits 1 under the same flag. Also `check_access_model.py --manifest-dir artefacts/M2-S03` exit 0, `score 100`, `0 finding(s)` (1 of 3 files scanned — no `objectPermissions`/`fieldPermissions`/`userPermissions` element anywhere), `xml` (4 of 4 parsed) and `manifest` (3 members ↔ 3 files, both directions). **Rebuilt once** for mock-deploy finding F-15 — `<description>` trimmed from 280 to 152 characters, every other element byte-identical, SHA-256-verified (`decisions.md` D-M2S03-06). **Two elements the deploy-order note called ungrounded are now settled positively by `reports/MOCK-DEPLOY-M2.md` Run 2** rather than by either cited skill: the `Case.Billing` `layoutAssignments` entry paired with `<visible>false</visible>` on that same record type (`decisions.md` D-M2S03-01), and the alphabetical element order inside `<Profile>` (D-M2S03-02). **Status is `In Build`, not `In UAT`:** `<recordTypeVisibilities>` here controls which record type this persona may *select*, not whether it may *open* an existing record of a type it lacks — the mechanism that actually decides that is the Private OWD (`M1-S01`, built) plus `M2-S05`'s criteria-based sharing rule, `pending` — the same reasoning `REQ-018`'s row states for the equivalent `Case_Tier1` permission set one layer up the access stack. Q13, deferred → assumption **A1**, conservative reading, is why `Case.Billing` is withheld as default/visible here; Q11's "clone Standard User" is superseded at API 62.0 by Minimum-Access seeding, and a same-named org profile would be overlaid rather than replaced (`decisions.md` D-M2S03-04, D-M2S03-05). Q12 (employees only, 18 people total) is the population this file and its siblings serve. |
| REQ-027 | Q7 | Tier 2 engineers (4) who take escalated Support cases need the same base-profile footprint as Tier 1 — default app, default record type and layout assignments, with every object/field/tab grant in `PSG_Tier2_Prod` | M2-S03 | `Profile:Acme Support Tier 2` | metadata-builder | — | M2-S03-T2 | checker | In Build | `artefacts/M2-S03/profiles/Acme Support Tier 2.profile-meta.xml` \| `artefacts/M2-S03/deploy-order.md` | pass — same build-scope `check_record_type_layouts.py --strict` run as `REQ-026` (this file is 1 of the 15 files scanned, one of the two `Profile`-sourced record types resolved), same `check_access_model.py` run (1 of 3 files, 0 findings), `xml` and `manifest` as above. **Byte-identical to `Acme Support Tier 1` in every grant-bearing element** — the same shape `decisions.md` D-M2S02-05 already records for `Case_Tier1`/`Case_Tier2` one layer up the access stack; two files exist because `outputs[]` declares two, not because any answered clarification distinguishes Tier 2's profile residue from Tier 1's. Same Rebuild #2 description fix (279 → 152 chars) and the same two mock-deploy-settled elements as `REQ-026` (`decisions.md` D-M2S03-01, D-M2S03-02) — not repeated here. **Status is `In Build`,** same reasoning as `REQ-026`: `M2-S05` remains pending, and no clarification distinguishes Tier 2's profile access from Tier 1's (the Tier 1/Tier 2 split is routing and escalation, `M2-S04`/`M3`/`M4`, not access). |
| REQ-028 | Q7 | Finance (2 Billing staff) work Billing cases from a base profile carrying only the default app, default record type and layout assignments, with the Support record type deliberately withheld as default/visible — every object/field/tab grant lives in `PSG_Billing_Prod` | M2-S03 | `Profile:Acme Billing` | metadata-builder | — | M2-S03-T2 | checker | In Build | `artefacts/M2-S03/profiles/Acme Billing.profile-meta.xml` \| `artefacts/M2-S03/deploy-order.md` | pass — same build-scope `check_record_type_layouts.py --strict` run as `REQ-026`/`027` (1 of 15 files, the third `Profile`-sourced record type resolved), same `check_access_model.py` run (1 of 3 files, 0 findings), `xml` and `manifest` as above. **`Case.Support` carries a `layoutAssignments` entry while `<visible>false</visible>` on the same record type** — the exact ungrounded pairing `decisions.md` D-M2S03-01 records as settled positively by the M2 mock deploy; mirrors `Case_Billing`'s own withheld `Case.Support` visibility (`REQ-020`) and plan assumption **A1** (Q13 deferred, conservative reading), per `artefacts/M2-S03/deploy-order.md` § "Decisions worth reading before deploy", item 2. Same Rebuild #2 description fix (407 → 147 characters, the largest cut of the three — `decisions.md` D-M2S03-06). **Status is `In Build`,** same `M2-S05`-pending reasoning as `REQ-026`/`027`; Billing is the mirror image, withholding `Case.Support` where the two Support profiles withhold `Case.Billing`. |
| REQ-029 | Q13 | Tier 2 engineers must be able to work every Support-record-type case whoever owns it, and nothing may extend Billing-case access to Tier 1 | M2-S05 | `SharingRules:Case` | metadata-builder | D5 | M2-S05-T2 | manual | In Build | `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` \| `artefacts/M2-S05/case-visibility-model.md` | machine half **pass**, manual half **outstanding**. Machine: `check_sharing_model.py --manifest-dir artefacts` (build scope, per `standards/build-orchestration.md` § 5) exit 0, `1 object OWD(s) resolved`, `0 finding(s)` — resolves `M1-S01`'s OWD and this step's grant together, unlike the vacuous 0-resolved step-scope reading (`M2-S05-T1`); `xml` 2/2 parsed; `manifest` consistent (`SharingRules:Case` ↔ file, both directions). Manual **B01+B04** (`tests/M2-S05/results.json` `skipped_manual[0]`): the tester's grep evidence (`envelopes/M2-S05/2026-09-12T01-41-33Z.md`) confirms exactly one `<sharingCriteriaRules>` block, `sharedTo` group `Support_Tier_2` only, no `Billing`/`Billing_Team` string outside the free-text `<description>`, `Case.object-meta.xml` (`M1-S01`) carrying `<sharingModel>Private</sharingModel>`, and no `*.settings-meta.xml` file anywhere under `artefacts/` — compiled into `TC-M2S05-01` (Tier 2 grant half, `AC-029.1`) and `TC-M2S05-02` (Billing negative half, `AC-029.2`) in the session scratchpad, both linted clean by `check_uat_case.py` (`OK — 2 case(s) ... 2 criterion id(s) cross-checked`) and their criteria by `check_ac_format.py` (`0 error(s), 0 warning(s)`). **See also `REQ-010`** — `M1-S01`'s OWD row, same Q13→A1 lineage, a different artefact; that row's own "Gap named" sentence ("the machine assertion... has not run") is now stale now that this build-scope test has run and passed, corrected in `decisions.md` **O-M2S05-02** rather than by editing `REQ-010` itself, which is not this run's row to touch. **Status is `In Build`, not `In UAT`:** `M5-S02` lists this step in `depends_on`, though `M5-S02` is currently `blocked` for a reason unrelated to this row (missing sandbox-strategy inputs, `blocked_reason` on the step) — a step nominally serving this requirement remains on the books, the same reasoning `REQ-021`'s row applies to a pending dependent step. `Q80`'s answer ("Tier 1 must not see billing cases") is the restriction half this row also proves; `Q13` is recorded alone in `source` per the single-clarification-id convention `REQ-010` already sets, with `Q80` named here in prose rather than added as a second `source` value. |
| REQ-030 | Q5 | Priority must be set before an agent-created Case saves, because the first-response SLA and the 8-business-hour escalation clock both read it | M3-S01 | `ValidationRule:Case.Priority_Required_On_Agent_Save` | metadata-builder | — | TC-M3S01-01 | manual | In UAT | `artefacts/M3-S01/objects/Case/validationRules/Priority_Required_On_Agent_Save.validationRule-meta.xml` | machine half **pass**, manual half **outstanding**. Machine: `check_validation_rules.py --manifest-dir artefacts/M3-S01 --strict` exit 0, score 100, `Scanned 2 validation rule(s) across 2 file(s); 0 finding(s) detected.` (`tests/M3-S01/checker_stdout.txt`) — under `--strict` this also asserts the blank-guard shape (a fixture with `ISPICKVAL(Priority, "")` alone reproduced one REVIEW finding and exit 1, per `plan.json` `steps[M3-S01].inputs.note`); `xml` 3/3 parsed; `manifest` (`Case.Priority_Required_On_Agent_Save` two-way consistent). **What the exit does not prove** (`decisions.md` **D-M3S01-06**): that `Priority` or `$Permission.Bypass_Case_Intake_Validation` resolve to real components — the checker has no field inventory; both were checked by hand against `M1-S01` and `M2-S01`. Manual **W01** (`tests/M3-S01/results.json` `skipped_manual[0]`): the tester's on-disk evidence (`tests/M3-S01/summary.md` table "Manual test — checked against disk, not ticked") confirms the bypass clause opens the formula, the blank test is `ISBLANK(TEXT(Priority))` not `ISPICKVAL` alone, `errorMessage` is 218 of 255 characters, and `active` is `true` — compiled into `TC-M3S01-01` (positive, `AC-030.1`) and `TC-M3S01-02` (negative, bypass suppresses the rule, `AC-030.2`) in the session scratchpad, both linted clean by `check_uat_case.py` (`OK — 4 case(s) ... 4 criterion id(s) cross-checked`, covering both this row and `REQ-031`) and by `check_ac_format.py` (`0 error(s), 0 warning(s)`). **See also `REQ-014`** — `M1-S02`'s layout-visibility requirement for assumption A13; its own note that "no `ValidationRule` metadata exists anywhere under `artefacts/` yet" is now stale, corrected in `decisions.md` **O-M3S01-04** rather than by editing `REQ-014` itself. **See also `REQ-015`/`REQ-016`** — `M2-S01`'s bypass *grant*, a different pair of artefacts this rule depends on and consumes; `REQ-015`'s own "has not run" note on the consumer cross-reference is addressed in `decisions.md` **O-M3S01-03**. **Status is `In UAT`, not `In Build`:** `M3-S01` is now `documented` and its only dependency (`M1-S01`, `M2-S01`) is `documented` too, so the machine half is complete; the manual half (**W01**) is outstanding at the M3 gate. |
| REQ-031 | Q5 | Origin must carry a known value before a Case saves, because assignment routing and the customer acknowledgement both read it | M3-S01 | `ValidationRule:Case.Origin_Must_Be_Known` | metadata-builder | — | TC-M3S01-03 | manual | In UAT | `artefacts/M3-S01/objects/Case/validationRules/Origin_Must_Be_Known.validationRule-meta.xml` | machine half **pass**, manual half **outstanding**. Machine: same declared checker run as `REQ-030` (one command scans both files) exit 0, score 100, 0 findings; `xml` 3/3 parsed; `manifest` (`Case.Origin_Must_Be_Known` two-way consistent). **What the exit does not prove** (`decisions.md` **D-M3S01-06**, same gap as `REQ-030`): that `Origin` or the `$Permission` name resolve to real components. **What is genuinely unresolved, not merely unchecked** (`decisions.md` **D-M3S01-04**): whether a value outside the three tested `CaseOrigin` values can reach `Origin` at all is undocumented in both cited skills; the enumerated clause may be redundant, which is the safe direction. Manual **W01**, same declared test as `REQ-030`: the tester's on-disk evidence additionally confirms the formula names only `Origin` component values, never a compound address field (Q59) — compiled into `TC-M3S01-03` (positive, `AC-031.1`) and `TC-M3S01-04` (negative, bypass, `AC-031.2`). **See also `REQ-014`, `REQ-015`/`REQ-016`** — same cross-references as `REQ-030`, `decisions.md` **O-M3S01-04**/**O-M3S01-03**. `Q24`'s answer (assignment rules read `Origin` per channel) is the routing half of why this field must carry a known value; recorded here in prose rather than added as a second `source` value, per the single-clarification-id convention `REQ-029` already sets for `Q80`. **Status is `In UAT`,** same reasoning as `REQ-030`. |
| REQ-032 | Q22 | The customer receives an acknowledgement carrying the case number, sent from a live org-wide address on both the email and web intake channels, within the first minute of the Case being created | M3-S02 | `EmailTemplate:case_intake/Case_Acknowledgement` | metadata-builder | — | TC-M3S02-01 | manual | In UAT | `artefacts/M3-S02/email/case_intake.emailFolder-meta.xml` \| `artefacts/M3-S02/email/case_intake/Case_Acknowledgement.email` \| `artefacts/M3-S02/email/case_intake/Case_Acknowledgement.email-meta.xml` \| `artefacts/M3-S02/sender-identity-note.md` | machine half **pass**, manual half **outstanding**. Machine: `check_email_templates.py --manifest-dir artefacts/M3-S02 --strict` exit 0, score 100, `Scanned 4 email template file(s); 0 finding(s) detected.` (`tests/M3-S02/checker1_stdout.txt`); `check_email_deliverability_strategy.py --manifest-dir artefacts/M3-S02` exit 0 with 3 WARNs that assert nothing — this step declares none of the three files that checker reads (`tests/M3-S02/checker2_stdout.txt`; `decisions.md` **O-M3S02-02**); `xml` 4/4 parsed; `manifest` (`EmailFolder:case_intake` and `EmailTemplate:case_intake/Case_Acknowledgement` both two-way consistent). **What the machine half does not touch:** `EmailTemplate` carries no sender element, so no exit code here asserts anything about `senderEmail` — that element belongs to `M3-S04`, not this row (`sender-identity-note.md` § "The sender that actually gets set"). Manual **B06** (`tests/M3-S02/results.json` `skipped_manual[0]`): the tester's on-disk evidence (`tests/M3-S02/summary.md` § "B06 (manual)") confirms neither `.email` body contains an email address (`grep -n @`, 0 matches on both), `sender-identity-note.md` § 1 names `support@acme.example` for both channels and `billing@acme.example` for finance replies, and § 2 states the self-addressed-loop risk with both qualifications of the named control — compiled into `TC-M3S02-01` (positive, `AC-032.1`) and `TC-M3S02-02` (negative — neither body hardcodes an address, `AC-032.2`) in the session scratchpad, both linted clean by `check_uat_case.py` (`OK — 2 case(s) ... 2 criterion id(s) cross-checked`) and by `check_ac_format.py` (`0 error(s), 0 warning(s)`). **The load-bearing gap this row carries forward, not resolves:** `plan.json` Q22's answer states `support@acme.example` — a live Email-to-Case routing address — itself sends this acknowledgement; `answers-key.md`'s "Acknowledgement" row states the opposite, that the sender is "never the Email-to-Case routing address itself." Both cited skills' mail-loop prohibition (`skills/admin/email-templates-and-alerts/references/metadata-and-sender-identity.md`; `skills/admin/email-to-case-configuration/references/gotchas.md` Gotcha 3) bites under Q22's reading and not the answer key's, and no artefact of this step sets a sender, so nothing here settles it. `decisions.md` **D-M3S02-04** records it as an M3 milestone-gate decision that `M3-S04` — the step that actually writes `senderEmail` — must not pre-empt on its own; `decisions.md` **O-M3S02-01** records the contradiction itself as a clarification-record defect for the planner. Q63's answer (one acknowledgement per case, auto-response only, no parallel Flow alert) is why exactly one template exists for this row rather than an auto-response template plus a Workflow Alert; Q68's answer (a sandbox test with real inbound email, a clock test and a loop test before go-live) is the detection mechanism named in § 2 that the M3 gate decision defers to — both cited here in prose rather than as a second `source` value, per the single-clarification-id convention `REQ-029` already sets for `Q80`. **Status is `In UAT`, not `In Build`:** `M3-S02` is now `documented` and its only dependency (`M1-S01`) is `documented` too, so the machine half is complete; the manual half (**B06**) is outstanding at the M3 gate. |
| REQ-033 | Q63 | Tier 2 receives a named handover notice, distinct from the customer acknowledgement, when a Case is reassigned to it by the 8-business-hour escalation action | M3-S02 | `EmailTemplate:case_intake/Case_Escalated_To_Tier2` | metadata-builder | — | M3-S02-T1 | checker | In Build | `artefacts/M3-S02/email/case_intake/Case_Escalated_To_Tier2.email` \| `artefacts/M3-S02/email/case_intake/Case_Escalated_To_Tier2.email-meta.xml` | pass — same declared checker run as `REQ-032` (one command scans both templates) exit 0, score 100, 0 findings (`tests/M3-S02/checker1_stdout.txt`); `xml` 4/4 parsed (shared with `REQ-032`); `manifest` (`EmailTemplate:case_intake/Case_Escalated_To_Tier2` two-way consistent). **No manual test targets this row:** B06 names only the acknowledgement path, so this requirement carries no compiled UAT case and no `test_case_ids` value — per `skills/admin/requirements-traceability-matrix` the status stays `In Build`, the same shape `REQ-001` already establishes for a checker-only row whose step is nonetheless `documented`. Internal, not customer-facing: the body carries no thread token by design (Q64/assumption A3 bind customer-facing templates only) and `EscalationAction` carries no sender element in its own reference, so none was invented here or in `M4-S04` (`sender-identity-note.md` § 3). **Cross-reference a reader should not conflate:** `Q88`'s answer (`M2-S04`) already gives the Tier 2 queue a queue-level notification default (a shared mailbox, applied since the answer key does not address Tier 2); this template is a separate, case-level handover notice the escalation action's reassignment fires, not a re-implementation of that queue-level control — `decisions.md` **O-M3S02-04** names the distinction so `M4-S04` does not wire the two together as if they were one mechanism. `Q63`'s "one event, one email" discipline is carried to this template as well: no parallel Workflow Alert is built alongside the escalation action either (`decisions.md` **D-M3S02-03**). |
| REQ-034 | Q17 | Two public routing addresses — support@acme.example and billing@acme.example — accept inbound mail and create Cases, each stamped with its own Case Origin so channel-level routing and the customer acknowledgement can both read it | M3-S03 | `Settings:Case` | metadata-builder | — | TC-M3S03-01 | manual | In UAT | `artefacts/M3-S03/settings/Case.settings-meta.xml` \| `artefacts/M3-S03/email-to-case-routing-addresses.md` \| `artefacts/M3-S03/package.xml` | machine half **pass**, manual half **outstanding**. Machine: declared build-scope `check_case_management_setup.py --manifest-dir artefacts` exit 0, `No case management setup issues found.` (`tests/M3-S03/check_case_management_setup.stdout.txt`); step-scope control (`--manifest-dir artefacts/M3-S03 --verbose`) also exit 0; `xml` 2/2 parsed; `manifest` (`Settings:Case` ↔ file, two-way, no wildcard — feature settings do not accept one). **Rebuilt once (run `2026-09-12T04-39-20Z`) after the operator's validate-only run against the org failed the as-built file** (`reports/MOCK-DEPLOY-M3.md` Run 3: `CaseSettings Case: Enter the system user's email address`). Three elements were added and nothing else changed: **F-25** `systemUserEmail` = `support-noreply@acme.example` (`decisions.md` **D-M3S03-01** — deliberately not either routing address, so `decisions.md` **D-M3S02-04** stays open, unresolved by this change); **F-26** `newEntityRecordType` = `Case.Support` / `Case.Billing`, object-qualified (the bare developer name does not resolve) and gated at API ≥ 64.0, so `package.xml` moved `62.0` → `67.0` (`decisions.md` **O-M3S03-01** — a build-wide API-version drift this raises, not a defect in this row); **F-27** `casePriority` `Medium` on both addresses, required by the org though the guide does not say so (`decisions.md` **D-M3S03-02** — an M3-gate decision affecting `M4-S03`, not pre-empted here). Manual **TC-M3S03-01** (`tests/M3-S03/results.json` `skipped_manual[0]`), deferred to the M3 gate: "...both routing addresses carry their own `caseOrigin` (Email-Support, Email-Billing) and no `caseOwner`, `unauthorizedSenderAction` is Bounce, `overEmailLimitAction` is Requeue, `saveEmailHeaders` is true on both..." — every element the sentence names is present and matches on disk; its clause about the `webToCase` block belongs to `REQ-035` below, and the sentence's own wording ("exactly its three documented children") is itself the defect `decisions.md` **O-M3S03-02** records, not a fact about this row's file. `caseOwner` is deliberately unset on both addresses per **Q18** — ownership is expressed once, in `M3-S04`'s assignment rule, not twice. **See also `REQ-005`** — `M1-S01`'s `StandardValueSet:CaseOrigin` row anticipated this step by name ("Downstream consumers ... are M3 and are not asserted here"); this row is that consumer, and `REQ-005`'s own row is left byte-identical per Step 8. **See also `REQ-021`** — `M2-S04`'s `Queue:Tier_1_General` row; this file's `defaultCaseOwner`/`defaultCaseOwnerType` (`Tier_1_General`/`Queue`) is the fall-through owner that requirement names, now actually wired into `CaseSettings` rather than existing only as a queue. Q20 (threading mode) is **deferred** — assumption **A3** (Lightning Threading) is what this file implements (`useEmailHeadersForThreading` `true`; the legacy pair `enableThreadIDInBody`/`enableThreadIDInSubject` omitted); rebuild this step if Setup shows legacy threading. **Status is `In UAT`, not `In Build`:** `M3-S03` is now `documented` and its three `depends_on` (`M1-S01`, `M2-S04`, `M3-S02`) are `documented` too, so the machine half is complete; the manual half (**TC-M3S03-01**) is outstanding at the M3 gate. |
| REQ-035 | Q66 | Web-to-Case intake is enabled for the website form (~60 cases a day) and stamps a Web Case Origin; the HTML form itself is authored and hosted outside this build | M3-S03 | `Settings:Case` | metadata-builder | — | TC-M3S03-02 | manual | In UAT | `artefacts/M3-S03/settings/Case.settings-meta.xml` \| `artefacts/M3-S03/web-to-case-form-contract.md` \| `artefacts/M3-S03/package.xml` | machine half **pass**, manual half **outstanding**. Machine: same declared checker run as `REQ-034` (one command scans the same file) exit 0, 0 findings; `xml` 2/2 parsed (shared); `manifest` (`Settings:Case` two-way, shared). `webToCase` carries exactly two of its three documented children — `enableWebToCase` `true` and `caseOrigin` `Web` — `defaultResponseTemplate` deliberately unset because the guide scopes it to Self-Service portal responses rather than to the customer acknowledgement, which is `M3-S04`'s `AutoResponseRules` element (`web-to-case-form-contract.md` § 1). Manual **TC-M3S03-02** (`tests/M3-S03/results.json` `skipped_manual[1]`), deferred to the M3 gate: confirms `web-to-case-form-contract.md` states whether the form posts directly or through middleware, the `Origin` value each path stamps, and that the HTML form itself is not metadata — all three are present in the file (§§ 1–2), but **Q66 itself is not settled**: the file specifies both posting paths (§ 2) and recommends Path A (direct post) without a confirmed answer from the website owner, so the manual test's own precondition ("given Q66's answer itself says to confirm...") remains open past this step, not merely past this test. **The fallback owner for unrouted web cases** — `defaultCaseOwner` `Tier_1_General` / `defaultCaseOwnerType` `Queue` — is the same `CaseSettings` field `REQ-034`'s row documents; see that row rather than a second citation here. `Case.Origin` value `Web` is a live entry in `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml` (**Q19**, `REQ-005`). No record type is stamped on a web case — `WebToCaseSettings` has no record-type element (`web-to-case-form-contract.md` § 1) — so a web case lands on the object's default record type rather than `Case.Support`/`Case.Billing` the way an email case now does (**F-26**). **Status is `In UAT`, not `In Build`:** same dependency reasoning as `REQ-034` — `M3-S03` and its three `depends_on` are all `documented`; the manual half (**TC-M3S03-02**) and Q66's own open confirmation are both outstanding at the M3 gate. |
| REQ-036 | Q25 | Within the first minute of a case being created it must have an owner — the assignment rule is the authoritative mechanism, routing support@ (`Email-Support`) to Tier 1 and billing@ (`Email-Billing`) to Finance, with an explicit fall-through, not the queue alone | M3-S04 | `AssignmentRules:Case` | metadata-builder | D3 | M3-S04-T2 | manual | In UAT | `artefacts/M3-S04/assignmentRules/Case.assignmentRules-meta.xml` \| `artefacts/M3-S04/owner-writer-map.md` | machine half **pass**, manual half **outstanding and not tickable as written**. Machine: declared build-scope `check_case_management_setup.py --manifest-dir artefacts` exit 0, `No case management setup issues found.` (`tests/M3-S04/checker_check_case_management_setup.stdout.txt`); `xml` 3/3 parsed; `manifest` (`AssignmentRules:Case` ↔ file, two-way, member named explicitly though the cited skill documents that all three rule types accept `*`). Undeclared, informational `check_assignment_rules.py --manifest-dir artefacts` exits 1 on `target 'Tier_1_General' appears in multiple rule entries` — deliberate by construction (Q18 routes support@ to Tier 1, Q26 sends every unmatched case to the same catch-all queue), reproducing `deploy-order.md` § 7's prediction word for word at both scopes (`tests/M3-S04/OBSERVATION-check_assignment_rules.*.stdout.txt`); its `AR-LOOP-01` mail-loop rule does **not** fire at build scope — positive evidence no `senderEmail` in this build matches a routing address. **Manual `M3-S04-T2` (`W02`):** given Q25 and Q26, the active rule's entries route on `Case.Origin` **and the Account support tier**; the built file routes on `Case.Origin` **only** — the order/catch-all half (most-specific-first, criteria-less catch-all last, assigned to `Tier_1_General`) matches the artefact; the tier clause does not, and the test cannot be ticked as written (`tests/M3-S04/summary.md` § "Ambiguity recorded verbatim"; `decisions.md` **D-M3S04-02** — two independent blockers: no answer names a `Premier` tier→queue mapping, and no skill grounds a related-object `criteriaItems/field` on a Case rule). Carried to the M3 gate: either an answer names the mapping and a live org confirms the notation, or the step's title and `W02` are corrected to Origin-only. `owner-writer-map.md` (this row's second artefact) records the three by-design `OwnerId` writers in fire order and the still-open Q24 layout-default gap (`decisions.md` **O-M3S04-01**) — without that default, ~20 hand-logged cases a day never reach this rule at all. **Status is `In UAT`, not `In Build`:** `M3-S04` is now `documented` and its three `depends_on` (`M2-S04`, `M3-S02`, `M3-S03`) are `documented` too, so the machine half is complete; the manual half is outstanding at the M3 gate, carrying the mismatch above rather than a plain sign-off. |
| REQ-037 | Q28 | The customer must receive an acknowledgement with the case number within the first minute — fired by the auto-response rule only when the assignment rule fires, exactly once per case, on both intake channels | M3-S04 | `AutoResponseRules:Case` | metadata-builder | — | M3-S04-T3 | manual | In UAT | `artefacts/M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml` | machine half **pass** (with one org-validation caveat below), manual half **outstanding, on-disk consistent, not ticked**. Machine: same declared build-scope `check_case_management_setup.py --manifest-dir artefacts` run as `REQ-036` (one command scans both rule files) exit 0; `xml` 3/3 parsed (shared); `manifest` (`AutoResponseRules:Case` ↔ file, two-way, member named explicitly). **`reports/MOCK-DEPLOY-M3.md` Run 6 (F-28):** a real `sf project deploy start --dry-run` against `sfskills-dev` rejected this exact component — `AutoResponseRule Case.Case_Acknowledgement: support-noreply@acme.example is an invalid From email address` — because the org carries no verified `OrgWideEmailAddress` for it. Not a metadata defect: the value is the operator's pre-gate resolution of `decisions.md` **D-M3S02-04** (`decisions.md` **D-M3S04-01**), and the address's absence is recorded as a **G3 deploy prerequisite** (`decisions.md` **D-M3S04-03**), not a rebuild — the sibling `AssignmentRules:Case` component validated cleanly in the same run. **Manual `M3-S04-T3`:** given Q28 and Q63, exactly one acknowledgement entry can match any case (structurally true — one `ruleEntry`) and its template names `M3-S02`'s folder-qualified Classic template (`case_intake/Case_Acknowledgement`), confirmed on disk; deferred to the M3 gate, on-disk evidence consistent, not a mismatch. **`replyToEmail` mirrors `senderEmail`:** a customer's *Reply* does not thread onto the case (`decisions.md` **D-M3S04-04**) — carried to the same gate item as `D-M3S02-04`. **See also `REQ-032`** — `M3-S02`'s `EmailTemplate:case_intake/Case_Acknowledgement` row is the template *content* this rule's `<template>` element names; this row is the delivery *mechanism*, a different artefact serving the same acknowledgement requirement. **Status is `In UAT`, not `In Build`:** same dependency reasoning as `REQ-036` — the machine half is complete; the manual half and F-28's org prerequisite are both outstanding at the M3 gate. |
| REQ-038 | Q39 | SLA clocks must run on the right calendar: EMEA works London 08:00–18:00, the US works New York 08:00–20:00, clocks pause on weekends and regional holidays, and Severity 1 outages run on a 24/7 calendar that never pauses | M4-S01 | `Settings:BusinessHours` | metadata-builder | — | M4-S01-T4 | manual | In UAT | `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml` | machine half **pass** (with one checker-policy history below), manual half **pass, deferred to the M4 gate**. Machine: declared `check_business_hours_and_holidays.py --manifest-dir artefacts/M4-S01` — first run exit **1** on the `Severity 1 24x7` calendar's shipped-24/7 shape (`decisions.md` **D-M4S01-01**), re-run exit **0** against the byte-identical file after skill v1.0.1 scoped the rule (one INFO line, does not affect exit code); `xml` 2/2 parsed; `manifest` two-way (`Settings:BusinessHours` named explicitly, feature settings reject the wildcard). **Manual `M4-S01-T4`** (`tests/M4-S01/results.json` `skipped_manual[0]`): given the step claims to have built the calendars, when the settings file is read, then all three are present and named — EMEA Support (Europe/London 08:00–18:00 Mon–Fri), US Support (America/New_York 08:00–20:00 Mon–Fri, the org default) and Severity 1 24x7 — confirmed true on disk by `step-tester`, deferred to the milestone gate per the test's own wording. **Two items named, not asserted machine-checked:** the 14 holidays attached to `US Support`/`EMEA Support` are a seeded placeholder, not Acme's list (`decisions.md` **D-M4S01-02**); the midnight-to-midnight pair on `Severity 1 24x7` is UNVERIFIED without an org (`decisions.md` **O-M4S01-02**). **Status is `In UAT`, not `In Build`:** `M4-S01` is `documented` and has no `depends_on`, so the machine half is complete; the manual half above is outstanding at the M4 gate. `Severity 1 24x7` is presently read by no other step in this build (`decisions.md` **O-M4S01-01**) — a placeholder for a Severity 1 entitlement process that does not yet exist; `M4-S04`'s Severity 1 entry carries the same 24/7 promise operationally through `businessHoursSource = None`. |
| REQ-039 | Q90 | Holidays expire; the calendars need a named owner and a yearly maintenance cadence so they do not silently stop pausing | M4-S01 | `setup-only: holiday-maintenance-runbook.md` | metadata-builder | — | M4-S01-T1 | checker | In UAT | `artefacts/M4-S01/holiday-maintenance-runbook.md` | **Presence only, not content.** The declared checker scans metadata, not `.md`, so `M4-S01-T1`'s exit 0 says only that `check-outputs` (`tests/M4-S01/check-outputs.json`, ok) confirmed this file on disk and non-empty before the checker ran, and the checker itself excludes it from its scan — no runner in this step asserts what the file says. The step's one manual test (`M4-S01-T4`, cited on `REQ-038`) covers the settings file's calendar names, not this runbook. **Two items named as open at the M4 gate, not ticked:** the accountable team and cadence are answered (Service Operations, yearly Q4 deploy), but the named individual is explicitly left OPEN in the runbook's own owner row; the 14-entry holiday table it documents is a seeded placeholder, not Acme's confirmed list (`decisions.md` **D-M4S01-02** covers both). **Status is `In UAT`, not `In Build`:** same dependency reasoning as `REQ-038` — the file is written and present; the two open items above are outstanding at the M4 gate rather than a step remaining. |
| REQ-040 | Q38 | Premier accounts get a first response within 4 business hours | M4-S02 | `EntitlementProcess:First_Response_Premier` | metadata-builder | — | M4-S02-T4 | manual | In Build | `artefacts/M4-S02/entitlementProcesses/First_Response_Premier.entitlementProcess-meta.xml` | machine half **pass**, manual half **pass, deferred to the M4 gate**. Machine: declared `check_entitlements_and_milestones.py --manifest-dir artefacts --strict` — first run exit **1** on this file's milestone override (2× W4, `decisions.md` **D-M4S02-01**), re-run exit **0** against the byte-identical file after skill v1.1.2 moved W4 to INFO (`0 error(s), 0 warning(s), 2 info note(s)`); checker rule E1 confirms `minutesToComplete` is present and numeric, not that 240 is the correct value; `xml` parsed; `manifest` two-way (`EntitlementProcess:First_Response_Premier` named explicitly, part of the 3 ↔ 3 build-scope check). **Manual `M4-S02-T4`** (`tests/M4-S02/results.json` `skipped_manual[0]`): given assumption A27, `artefacts/M4-S02/` holds exactly two `entitlementProcesses` files and one `milestoneTypes` file, the Premier process carries `minutesToComplete` 240, and both processes name a `businessHours` resolving against `M4-S01`'s settings file — confirmed true on disk, deferred to the milestone gate per the test's own wording. **Status is `In Build`, not `In UAT`:** `M4-S03` (`EntitlementId` stamp, `pending`) and `M4-S05` (`CompletionDate` writer, D10, `pending`) both serve this requirement's functional completion — until they land this process is tracking-only (`milestone-completion-decision.md` § 4). |
| REQ-041 | Q38 | Standard accounts get a first response within 1 business day | M4-S02 | `EntitlementProcess:First_Response_Standard` | metadata-builder | — | M4-S02-T1 | checker | In Build | `artefacts/M4-S02/entitlementProcesses/First_Response_Standard.entitlementProcess-meta.xml` | machine half **pass, but does not confirm the value**, no manual half touches this file. Machine: same declared checker run as `REQ-040`, same exit 1 → exit 0 history; `xml` parsed; `manifest` two-way. **`minutesToComplete` 720 is DERIVED, not answered** (`decisions.md` **D-M4S02-02**) — nothing in this build converts "1 business day" into minutes directly; 720 is the `US Support` calendar's 12-open-hour day. **No test, machine or manual, asserts 720 is correct**: the checker's E1 rule confirms the field is present and numeric only, and `M4-S02-T4`'s manual wording (cited on `REQ-040`) pins Premier's 240 but names no value for Standard. Carried to the M4 gate as an UNCONFIRMED placeholder, the same shape as `M4-S01`'s holiday seed. **Status is `In Build`, not `In UAT`:** same `M4-S03`/`M4-S05` dependency as `REQ-040`. |
| REQ-042 | Q53 | One shared "First Response" milestone identity serves both SLA tiers; completion is driven by an after-update Apex trigger, not a workflow action | M4-S02 | `MilestoneType:First Response` | metadata-builder | D10 | M4-S02-T4 | manual | In Build | `artefacts/M4-S02/milestoneTypes/First Response.milestoneType-meta.xml` \| `artefacts/M4-S02/milestone-completion-decision.md` | machine half **pass**, manual half **pass, deferred to the M4 gate**. Machine: same declared checker run as `REQ-040`/`REQ-041` — the two surviving INFO `W4` notes on both processes ("no warning or completion action is configured … confirm that is the design") are this milestone type's action-less shape, and `milestone-completion-decision.md` is the on-disk confirmation the note asks for: **D10** routes `CompletionDate` to `M4-S05`'s after-update Apex trigger, not a workflow action, because no completion-criteria element is documented on the entitlement process and no clarification names a milestone notification; `xml` parsed; `manifest` two-way (`MilestoneType:First Response` named explicitly). **Manual `M4-S02-T4`** (cited on `REQ-040`): "exactly one `milestoneTypes` file (`First Response`)" — confirmed true on disk. **File name is mixed case against the guide's lowercase `NameNorm` derivation rule — UNVERIFIED against a real retrieve**, no org exists in this build to confirm (`deploy-order.md` § 4.1). **Status is `In Build`, not `In UAT`:** `M4-S05` (the `CompletionDate` writer this milestone type's whole design rests on, D10) is `pending` — until it lands, every First Response milestone opens and never closes (`milestone-completion-decision.md` § 4). |
| REQ-043 | Q45 | Anything untouched for 8 business hours escalates to Tier 2, with a 24/7 exception for a Severity 1 outage; cut over deploy-inactive-then-activate to avoid a wave of instant escalations | M4-S04 | `EscalationRules:Case` | metadata-builder | D7 | M4-S04-T1 | checker | In UAT | `artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml` \| `artefacts/M4-S04/escalation-activation-runbook.md` \| `artefacts/M4-S04/escalation-monitoring-note.md` | machine half **pass across two builds**, manual half **outstanding, deferred to the M4 gate**. Machine: declared build-scope `check_escalation_rules.py --manifest-dir artefacts` — first build exit **0** (`W1` no-rule-active expected under Q47, 2× `I3` 480=8h) on `2026-09-12T07-22-10Z`'s file, then that file was **rejected by the org**: `reports/MOCK-DEPLOY-M4.md` run 1, `EscalationRules Case: notifyToTemplate is required` (**F-36**). Closed at the skill, not the artefact — commit `9ae71856d` (`admin/escalation-rules` v1.1.2) adds rule **E10**, which then failed the byte-identical file with 2× `ERROR E10`; the rebuild (`2026-09-12T07-58-40Z`) added one folder-qualified `<notifyToTemplate>` per action and the declared checker exited **0** again (`W1` + 2× `I3`, no `I4`) — confirmed independently by `step-tester`'s post-rebuild run (`2026-09-12T07-51-46Z`), `tests/M4-S04/results.json` `"passed": true`. `xml` 2/2 parsed both builds; `manifest` two-way, `EscalationRules:Case` named explicitly — the container form, which also resolves the per-rule `EscalationRule:Case.Case_SLA_Escalation` key `check_rtm.py` derives from inside the file (§ "Linter result — after M4-S04" below). **Two manual tests deferred to the M4 gate**, both Given/When/Then-shaped and usable, neither ticked: `M4-S04-T4` (activation sign-off inside an agreed comparison window) and `M4-S04-T5` (the 480-minute / `businessHoursSource` / queue-developer-name assertion — `check_business_hours_and_holidays.py` is not declared on this step and prints vacuously at step scope; M4's milestone test runs it at `--manifest-dir artefacts`, where the calendars are visible). **Full record of the rebuild:** `decisions.md` **D-M4S04-01** (F-36, the second flywheel record in M4, paralleling `D-M4S01-01`). **Three items carried to the M4 gate, none resolved by this row:** the Billing-queue mail-loop exposure is confirmed real, not latent (`decisions.md` **O-M4S04-01**, closing **O-M3S04-02**'s open check) — the rule ships `<active>false</active>` so nothing loops on deploy, but activation needs one of three named remedies; Severity 1's 480-minute threshold is a composed reading of `requirement.md`, not an answered value (`decisions.md` **D-M4S04-02**); the `CaseCreation` clock start is narrower than the requirement's own word "untouched" (`decisions.md` **D-M4S04-03**, Q42). **U6, recorded not fixed:** one escalation template (`case_intake/Case_Escalated_To_Tier2`) serves both `notifyToTemplate` and `assignedToTemplate`, where the cited skill's worked example uses two (`decisions.md` **D-M4S04-04**) — this build declares exactly one escalation template (`M3-S02`), and inventing a second was rejected as the same class of invention `D-M2S04-02` already refused. Five further UNVERIFIED items (U1–U5) in `deploy-order.md` § 3, none covered by a declared test. **Status is `In UAT`, not `In Build`:** `M4-S04` is now `documented` and all four `depends_on` steps (`M4-S01`, `M2-S04`, `M3-S02`, `M3-S04`) are `documented` too, so the machine half is complete; both manual tests are outstanding at the M4 gate. |
| REQ-044 | Q50 | The First Response milestone is marked complete by an after-update Apex trigger on Case, per D10's mechanism; Q50's own answer named the first outbound EmailMessage as the completion signal, but this delivery implements a narrower Case-only proxy — the Case leaving Status New (`decisions.md` D-M4S05-02) | M4-S05 | `ApexTrigger:CaseMilestoneTrigger` | apex-builder | D10 | M4-S05-T1 | checker | In UAT | `artefacts/M4-S05/triggers/CaseMilestoneTrigger.trigger` \| `artefacts/M4-S05/classes/CaseMilestoneService.cls` \| `artefacts/M4-S05/classes/CaseMilestoneServiceTest.cls` \| `artefacts/M4-S05/classes/TestDataFactory.cls` \| `artefacts/M4-S05/classes/TestUserFactory.cls` | machine half **pass across five builds (the F-37 rebuild plus four same-day repairs)**, manual half **outstanding, deferred to the M4 gate**. Machine: declared `check_entitlement_apex_hooks.py --manifest-dir artefacts/M4-S05` — first build exit **0** on 3 Apex files, rejected by the org (`reports/MOCK-DEPLOY-M4.md` run 2, F-37, `decisions.md` **D-M4S05-01**), rebuild exit **0** on 4 files; then four org-executed repairs on the same documented step, each triggered by `reports/MOCK-DEPLOY-M5.md` (runs 4–7) and each re-passing the declared checker at `--strict`: **F-59** (`decisions.md` **D-M4S05-06**) — no test ran as a permissioned user; `TestUserFactory.cls` added and every method's action/assertions wrapped in `System.runAs` of a Tier 1 agent; checker exit 0 on 5 files. **F-60** (`decisions.md` **D-M4S05-07**) — the fixture insert itself failed FLS as the persona; every fixture seed moved to `TestDataFactory.insertAsSystem`; checker exit 0. **F-61** (`decisions.md` **D-M4S05-08**) — `requireActiveProcess()`'s unfiltered `LIMIT 1` returned the wrong org process; query now filters by name; checker exit 0. **F-62** (`decisions.md` **D-M4S05-09**) — the first repair to touch shipped code: `CaseMilestoneService`'s `CaseMilestone` query and DML now run `WITH SYSTEM_MODE`/`AccessLevel.SYSTEM_MODE` because no permission set in this build grants any `CaseMilestone` access; checker exit 0 on 5 files (0 ERROR, 0 WARN). Re-tested by `step-tester` (run `2026-09-12T18-12-57Z`) against the post-F-62 tree: `xml` 5/5 parsed, `manifest` still **skipped-not-applicable** (Apex exception unchanged), declared checker exit 0; `tests/M4-S05/results.json` `"passed": true`. **Org-side test execution, the acceptance evidence for all four repairs:** `reports/MOCK-DEPLOY-M5.md` run 8 — Succeeded, `--test-level RunSpecifiedTests --tests CaseMilestoneServiceTest`, **4/4 tests, 84.4% coverage** — the first run every method of `CaseMilestoneServiceTest` passes. **One manual test deferred to the M4 gate**, Given/When/Then-shaped and usable, not ticked: every non-platform identifier is quoted from the cited skill or template, and `CaseMilestoneServiceTest` asserts `CompletionDate` non-null after the trigger runs. **Items carried to the M4 gate, none resolved by this row:** the completion signal is a proxy, not Q50's literal answer (`decisions.md` **D-M4S05-02**); the two-file trigger shape ships with no recursion guard or `TriggerControl` kill switch (`decisions.md` **D-M4S05-03**); `CaseMilestoneServiceTest` is forced to `@IsTest(SeeAllData=true)` (`decisions.md` **D-M4S05-04**); `TestDataFactory` ships as a step-local copy (`decisions.md` **D-M4S05-05**); the system-mode boundary F-62 drew, and the wider-persona-grant alternative it rejected (`decisions.md` **D-M4S05-09**). Six further UNVERIFIED items in `deploy-order.md` § 5, none covered by a declared test. **`TestUserFactory.cls` is undeclared in this step's `outputs[]`** (added by F-59, not amended in, unlike `TestDataFactory` at the F-37 rebuild) — `M5-S05`'s build-level manifest owes it a fifth `ApexClass` member, carried as an open obligation rather than resolved here (`decisions.md` **O-M4S05-01**). **Status is `In UAT`, not `In Build`:** `M4-S05` is now `documented` again after this second documentation pass and its one `depends_on` step (`M4-S02`) is `documented` too, so the machine half is complete; the manual test above is outstanding at the M4 gate. **Note for the gate, not this row's to resolve:** `REQ-040`/`REQ-041`/`REQ-042` (`M4-S02`'s rows) may still read a stale `Status: In Build` from before this pass — their own note names both `M4-S03` and `M4-S05` as the steps their functional completion rests on, and this pass touches only `M4-S05`'s own row. |
| REQ-045 | Q48 | Within the first minute, a Case's SLA clock and (where resolvable) its Entitlement are attached automatically before save, and Priority is derived where the intake channel supplies no structured value (`requirement.md` L9–11) | M4-S03 | `Flow:Case_BeforeSave_StampEntitlementAndCalendar` | metadata-builder | D2 | M4-S03-T6 | manual | In UAT | `artefacts/M4-S03/flows/Case_BeforeSave_StampEntitlementAndCalendar.flow-meta.xml` \| `artefacts/M4-S03/no-account-fallback-note.md` | machine half **pass across three builds**, manual half **outstanding, deferred to the M4 gate**. Machine: declared `check_record_triggered_flow_patterns.py --manifest-dir artefacts/M4-S03` exit 0, "No issues found." — unchanged across all three builds; the rule-3 entry-criteria check now scopes to `RecordAfterSave` only, which is what clears the v2 blocker for this create-context flow. `check_flow_decision_element_patterns.py` (not a declared test, run anyway per `metadata-builder` Step 8) exit 0 with five WARNs, all design-not-defect (`artefacts/M4-S03/deploy-order.md` § 5). `xml` parsed; `manifest` two-way, `Flow` named explicitly. **Priority mechanism:** `Decision_Derive_Priority` overwrites the Email-to-Case intake default on `Email-Support`/`Email-Billing` per G3 gate decision (2); assumption A2's null guard holds everywhere else (`decisions.md` **D-M4S03-02**). **Priority VALUES** (Severity 1/Premier → `High`, else `Medium`) are derived, not answered — carried to the M4 gate (`decisions.md` **D-M4S03-03**). **Fault paths:** four `faultConnector`s route to the next `Decision` rather than to a `LogFault_<Parent>` target, because neither cited skill documents a before-save fault-path shape and a `RecordBeforeSave` flow may carry no `recordCreates` at all — a library gap, not a defect (`decisions.md` **O-M4S03-01**). **Manual test deferred to the M4 gate:** the three-field stamp, the no-match fallback, and the four `check_flow_governance.py` policy fields on the flow's own `<description>`/`<interviewLabel>`/`<apiVersion>`/`<runInMode>`. |
| REQ-046 | Q48 | The `FlowTest` proving the before-save stamp supplies exactly the test-point parameters a `Create`-triggered flow accepts | M4-S03 | `FlowTest:Case_BeforeSave_StampEntitlementAndCalendar_Test` | metadata-builder | — | M4-S03-T5 | manifest | In UAT | `artefacts/M4-S03/flowtests/Case_BeforeSave_StampEntitlementAndCalendar_Test.flowtest-meta.xml` | machine half **pass, over two rebuilds and two org rejections**, no manual half touches this file directly. Machine: `manifest` two-way, `FlowTest` named explicitly; `xml` parsed; `check_flow_governance.py --manifest-dir artefacts/M4-S03` exit 0 confirms an `<status>Active</status>` flow has a `FlowTest` naming it in the manifest (a checker ERROR otherwise). **This is the one file that changed across all three builds** — build 1 shipped `InputTriggeringRecordUpdated` only and was org-rejected (*"missing … InputTriggeringRecordInitial"*); rebuild 1 added `Initial` alongside `Updated` and was rejected again, the mirror error (*"contains the incompatible parameter value … InputTriggeringRecordUpdated. Remove the parameter or change the record trigger type"*); rebuild 2 removed `Updated`, leaving `Initial` alone, and validated. Settled rule: `recordTriggerType Create` → `Initial` only; `Update`/`CreateAndUpdate` → both — proven live by the org, not by any skill file, which is still unedited (`decisions.md` **D-M4S03-01**, the fourth flywheel-adjacent record in this build and the first the skill fix has not yet closed). No declared checker inspects `FlowTest` parameters directly; the org's own two rejections are the only assertion this file has ever had. |
| REQ-047 | Q40 | `Settings:Flow`'s `enableFlowDeployAsActiveEnabled` is the org-level switch that decides whether the before-save flow deploys `Active` or silently lands `Draft` | M4-S03 | `Settings:Flow` | metadata-builder | — | M4-S03-T3 | checker | In UAT | `artefacts/M4-S03/settings/Flow.settings-meta.xml` | machine half **pass with one documented advisory**, no manual half touches this file directly. Machine: declared `check_flow_governance.py --manifest-dir artefacts/M4-S03` exit 0, "0 error(s), 2 advisory" — one of the two advisories is this file's own naming gap: the checker globs the metadata-format name `Flow.settings`, this build uses DX `-meta.xml` naming throughout, so it reports the settings file missing even though it is present — a documented, expected outcome, not a defect (`artefacts/M4-S03/deploy-order.md` § 4). `xml` parsed; `manifest` two-way, `Settings:Flow` named explicitly (feature settings reject the `package.xml` wildcard). **Production-deploy risk, not resolved by this row:** `enableFlowDeployAsActiveEnabled true` means a production deploy of this step runs the org's Apex tests and can be rolled back for a reason unrelated to this flow if the required active-automation launch percentage is not met — this build's only Apex is `M4-S05`, sequenced separately (`decisions.md` **O-M4S03-02**). UNVERIFIED: whether this one-field file resets the org's other twelve `FlowSettings` values or leaves them untouched. |
| REQ-048 | Q31 | Billing and Tier 2 pick their cases from a list, so their queue list views are the working surface Q31's answer promises, not a nicety | M5-S01 | `ListView:Case.Tier_2_Queue` | metadata-builder | D4 | M5-S01-T5 | manual | In UAT | `artefacts/M5-S01/objects/Case/listViews/Tier_2_Queue.listView-meta.xml` | machine half **pass**, manual half **outstanding, deferred to the M5 gate**. Machine: declared build-scope `check_list_views_and_compact_layouts.py --manifest-dir artefacts` exit 0, `No issues found.` — proves the filter/column shape well-formed AND that `Case`'s compact layout (`M1-S01`) is assigned, the cross-reference this checker exists for (run at step scope alone it fires one INFO and exits 1, because the compact layout is out of view — the build-scope command is the one the plan declares and the one that passes); `xml` parsed; `manifest` two-way (`ListView:Case.Tier_2_Queue` named explicitly, part of the 5-member build-scope check). **Manual `M5-S01-T5`** (`tests/M5-S01/results.json` `skipped_manual[0]`): given the three views are Queue-scoped, when each `listView` file is read, then its `<queue>` names a queue developer name that exists under `artefacts/M2-S04/queues/` — `Tier_2_Engineering` confirmed present on disk, not ticked, deferred to the milestone gate per the test's own wording. **Every queue already auto-creates a list view** (`decisions.md` reference: `artefacts/M5-S01/deploy-order.md` § 5 decision 2) — expect two views per queue in the org after deploy. **Status is `In UAT`, not `In Build`:** `M5-S01` is now `documented` and both `depends_on` steps (`M2-S04`, `M4-S04`) are `documented` too, so the machine half is complete; the manual test above is outstanding at the M5 gate. |
| REQ-049 | Q31 | Billing picks its cases from a list, the same working-surface requirement as `REQ-048`, for a different queue and a different team (2 finance staff, `requirement.md` L12–L14) | M5-S01 | `ListView:Case.Billing_Queue` | metadata-builder | D4 | M5-S01-T5 | manual | In UAT | `artefacts/M5-S01/objects/Case/listViews/Billing_Queue.listView-meta.xml` | machine half **pass**, manual half **outstanding, deferred to the M5 gate**, same shape as `REQ-048`. Machine: same declared build-scope checker run as `REQ-048` (one command scans all three views), exit 0; `xml` parsed; `manifest` two-way (`ListView:Case.Billing_Queue` named explicitly). **Manual `M5-S01-T5`** (same test as `REQ-048`, covering all three views in one Given/When/Then): `Billing` queue developer name confirmed present under `artefacts/M2-S04/queues/`, not ticked. **Status is `In UAT`, not `In Build`:** same dependency reasoning as `REQ-048` — both `depends_on` steps documented, manual test outstanding at the M5 gate. |
| REQ-050 | A7 | Tier 1 needs a working surface to see its own queue's cases while `M3-S05` (the step that would configure Q31's Omni-Channel push for Tier 1) stays blocked on Q32–Q35 | M5-S01 | `ListView:Case.Tier_1_General_Queue` | metadata-builder | D4 | M5-S01-T5 | manual | In UAT | `artefacts/M5-S01/objects/Case/listViews/Tier_1_General_Queue.listView-meta.xml` | machine half **pass**, manual half **outstanding, deferred to the M5 gate**. Machine: same declared build-scope checker run as `REQ-048`/`REQ-049`, exit 0; `xml` parsed; `manifest` two-way (`ListView:Case.Tier_1_General_Queue` named explicitly). **Manual `M5-S01-T5`** (the same Given/When/Then as `REQ-048`/`REQ-049`, whose second clause names this row specifically): `Tier_1_General` queue developer name confirmed present under `artefacts/M2-S04/queues/` **and** this view confirmed present as Tier 1's interim pull surface while `M3-S05` is blocked, not ticked. **This row is deliberately NOT `REQ-048`/`REQ-049`'s requirement restated a third time** — `Q31`'s own answer says Tier 1's work is *pushed*, not pulled; this view exists under assumption `A7` as an interim substitute for the push `M3-S05` has not yet built, which is a different requirement from the one `REQ-048`/`REQ-049` satisfy directly (`decisions.md` **D-M5S01-03**, carried to the M5 gate: when `M3-S05` ships, a human decides whether this view stays as an overflow surface or is retired). **Status is `In UAT`, not `In Build`:** same dependency reasoning as `REQ-048`. |
| REQ-051 | Q91 | A saved report on escalated, still-open Cases, reviewed weekly by the Tier 2 lead, so the escalation rule's `IsEscalated` write can be confirmed still firing next month | M5-S01 | `Report:Support_Operations/Escalated_Open_Cases` | metadata-builder | — | M5-S01-T2 | checker | In Build | `artefacts/M5-S01/reports/Support_Operations/Escalated_Open_Cases.report-meta.xml` \| `artefacts/M5-S01/reports/Support_Operations-meta.xml` | machine half **pass, but proves less than it looks like**, no manual test targets this row. Machine: declared step-scope `check_report_inventory.py --manifest-dir artefacts/M5-S01` exit 0, score 100, `Scanned 1 report/dashboard file(s); 0 finding(s) detected.` — scored **identically** on the pre-rebuild file `reports/MOCK-DEPLOY-M5.md` run 1 rejected (`>255`-char `<description>`, invalid `reportType`, an invalid grouping) and on the rebuilt, org-validated file; the checker asserts nothing about any of the three fields that changed (`decisions.md` **O-M5S01-01**); `xml` parsed (both files); `manifest` two-way — the bare `Support_Operations` member (filed under `<name>Report</name>`, no separate `ReportFolder` entry in `describeMetadata()`) and `Support_Operations/Escalated_Open_Cases` both present, both with a matching member. **The folder is bundled into this row's `artefact_paths` rather than minted its own requirement** — one report-and-its-folder mechanism, the same one-mechanism shape `REQ-032` gives the acknowledgement template and its `EmailFolder`. **`<description>` length and the `reportType`/grouping values (F-49/F-50) were proven live by two org round-trips, not by any declared test** (`decisions.md` **D-M5S01-01**); the folder's declared filename is invisible to `check_report_inventory.py`'s recognition list even though the org accepts it (`decisions.md` **O-M5S01-02**). **What this row does NOT prove:** the report ships without its `Escalated = True` criterion — no cited skill carries the `Case.IsEscalated` column code, five probed candidates were all rejected, and the gap is now a post-deploy runbook step rather than a rebuild target (`decisions.md` **D-M5S01-02**, finding F-51). **No manual test targets this row** — `acceptance_tests[4]` covers the three list views only — so, per `skills/admin/requirements-traceability-matrix`, the status stays `In Build`, the same shape `REQ-001`/`REQ-033` already establish for a checker-only row whose step is nonetheless `documented`. |
| REQ-052 | Q77 | Every tester persona named in the M5 sandbox proof holds the real Profile plus Permission Set Group for their team, never the administrator | M5-S03 | `setup-only: story-backlog.md` | story-drafter | — | M5-S03-T1 | checker | In UAT | `artefacts/M5-S03/story-backlog.md` | pass — `check_invest.py --manifest-dir artefacts/M5-S03` exit 0 (`Summary: 11/11 stories passed`) enforces a persona that is not "user" or "admin" on all 11 stories (`plan.json` `steps[M5-S03].acceptance_tests[0].description`). Every `As a` stem additionally names the real profile (`Acme Support Tier 1` / `Acme Support Tier 2` / `Acme Billing`) and PSG (`PSG_Tier1_Prod` / `PSG_Tier2_Prod` / `PSG_Billing_Prod`), each resolving to a file this build wrote (`artefacts/M2-S03/profiles/`, `artefacts/M2-S02/permissionsetgroups/`) per `story-backlog.md` § Persona anchors. **Minted here, not inherited:** `decisions.md` **O-M5S03-01** records that no writer owns the `REQ-` sequence for this build; `REQ-052`–`REQ-058` continue from `REQ-051`, the highest id on file before this step, so no collision exists. Manual `M5-S03-T2` (below) also touches this requirement's channel-and-persona clause and is outstanding at the M5 gate. |
| REQ-053 | Q84 | Each of the three intake channels — email, web and manual UI — is tested separately, by its own story, rather than proving the easy half once | M5-S03 | `setup-only: story-backlog.md` | story-drafter | — | M5-S03-T2 | manual | In UAT | `artefacts/M5-S03/story-backlog.md` | outstanding — manual, deferred to the M5 gate (`tests/M5-S03/results.json` `skipped_manual[0]`). Epic A carries one story per channel (`US-CASE-001` email/support, `US-CASE-003` web, `US-CASE-004` manual), plus `US-CASE-002` as a fourth story splitting the email channel by data variation — Billing gets its own named tester (Q77) and a story cannot carry two `As a` clauses — not a fourth channel. That split is recorded as an ambiguous backlog-shape call rather than assumed acceptable: `decisions.md` **O-M5S03-05**. `check_invest.py` does not itself assert one-story-per-channel; that is this manual test's own clause, not the checker's. |
| REQ-054 | Q80 | Every story carries at least one criterion that is a restriction rather than a capability — the deny cases (an unauthorised sender's mail bounces; a Tier 1 agent cannot open a Billing case) are first-class, not an afterthought | M5-S03 | `setup-only: story-backlog.md` | story-drafter | — | M5-S03-T1 | checker | In UAT | `artefacts/M5-S03/story-backlog.md` | pass — `check_invest.py` exit 0 enforces at least one sad-path criterion per story (same acceptance-test description as `REQ-052`), named explicitly in: `US-CASE-001` AC-3 (bounce), `US-CASE-002` AC-3, `US-CASE-003` AC-3/AC-4, `US-CASE-005` (the whole story), `US-CASE-006` AC-3, `US-CASE-010` AC-2. Manual `M5-S03-T2`'s third clause (a permission-denial path) also targets this requirement and is outstanding at the M5 gate, the same test named on `REQ-053`. |
| REQ-055 | Q78 | Sandbox deliverability is raised above System Email Only, with Contact emails scrubbed first, before any email-channel story can be run | M5-S03 | `setup-only: story-backlog.md` | story-drafter | — | — | — | Draft | `artefacts/M5-S03/story-backlog.md` | no test, machine or manual, evidences this requirement directly — it is carried as a named deploy prerequisite (**P6**) in the `dependencies[]` of `US-CASE-001`, `US-CASE-002` and `US-CASE-003`, and as a Background bullet ("the sandbox is UNVERIFIED", `story-backlog.md` § Persona anchors). The gap is waived under `check_rtm.py`'s `Draft`-status coverage rule rather than hidden behind a fabricated test id: raising deliverability is an environment action no plan step performs, tracked at the M5 gate instead. |
| REQ-056 | Q96 | Before every UAT session, the triager confirms each Permission Set Group's recalculation is finished, so a stale group reports as Blocked rather than as a build defect | M5-S03 | `setup-only: story-backlog.md` | story-drafter | — | — | — | Draft | `artefacts/M5-S03/story-backlog.md` | no dedicated story or test — Q96's answer is a recurring pre-session gate query, not a one-time acceptance criterion, so it is carried in the shared Background block (`story-backlog.md` § Persona anchors, bullet 6) rather than written as its own story. `story-backlog.md` § Process Observations names this as one of three requirements deliberately carrying no story; recorded here as `decisions.md` **O-M5S03-01** and waived under `Draft`, not treated as an oversight. |
| REQ-057 | Q97 | When a UAT criterion's precondition has not been met (an inactive escalation rule, an unmet deploy prerequisite), the named triager records it as Blocked, not Failed | M5-S03 | `setup-only: story-backlog.md` | story-drafter | — | — | — | Draft | `artefacts/M5-S03/story-backlog.md` | no dedicated story or test — illustrated in `US-CASE-008`'s notes ("that distinction is Q97's whole point and the triager decides it") rather than asserted as its own criterion. Same deliberate-no-story treatment as `REQ-056`, same `decisions.md` **O-M5S03-01** entry, waived under `Draft`. |
| REQ-058 | Q94 | The sandbox this backlog is proven in has a named environment owner and a named refresh approver | M5-S03 | — | story-drafter | — | — | — | Draft | — | outstanding, unbuilt — `M5-S02` (the sandbox-strategy design step that would name an owner and approver) is `blocked` on four inputs (`team_size`, `concurrent_workstreams`, `release_cadence`, `data_sensitivity`); no story in this backlog can name a sandbox at all, because Q75 is deferred. This row is a placeholder a future step must satisfy, not evidence of anything delivered — `story-backlog.md`'s own internal matrix names the same three ids (`REQ-056`–`REQ-058`) as having no story, and this is the one of the three with no artefact at all. Waived under `Draft`; not an orphan, because no manifest component and no artefact exist for `check_rtm.py` to flag as unlinked. |

---

## Requirement id derivation

This build minted no `REQ-XXX` ids during intake: `plan.json` carries `clarifications[]`
and `assumptions[]` but no requirement register, and `requirement.md` is prose. The ids
below are therefore **assigned here and anchored**, not inherited — each one names the
`requirement.md` line that states the need and the clarification that settled it, so the
key is auditable rather than invented. Ids are stable and are never reused.

| req_id | Anchored to `requirement.md` | Settled by |
|---|---|---|
| REQ-001 | L6–L8 — email/web/manual intake for support work | Q1 (answered), A26 |
| REQ-002 | L8 — "Finance queries arrive at billing@… should be worked by Finance" | Q1 (answered), A26 |
| REQ-003 | L13–L16 — "Anything untouched for 8 business hours escalates to Tier 2" | Q2 (answered), A28 |
| REQ-004 | L8 — finance queries are worked by 2 finance staff, not by engineering | Q2 (answered), A28 |
| REQ-005 | L6–L8 — three named intake channels, "There is no phone channel" | Q19 (answered) |
| REQ-006 | — (no requirement line; see the note under the matrix) | Q83 (answered); plan v5 note B02/B03 |
| REQ-007 | L18 — "Severity 1 outages are 24/7 and never pause" | Q38 (answered) |
| REQ-008 | L17–L18 — "EMEA works London 08:00–18:00, the US works New York 08:00–20:00" | Q40 (answered) |
| REQ-009 | L15–L16 — "Premier accounts get a first response within 4 business hours, standard accounts within 1 business day" | Q38 (answered) |
| REQ-010 | L8 — finance queries "should be worked by Finance" | Q13 (**deferred**) → assumption A1 |
| REQ-011 | L6–L8 — support intake by email, web form and ~20 hand-logged cases a day; L18 — "Severity 1 outages are 24/7 and never pause" | Q5 (answered), Q83 (answered), A26 |
| REQ-012 | L8 — "Finance queries arrive at billing@acme.example and should be worked by Finance" | Q5 (answered), Q83 (answered), A26 |
| REQ-013 | L7 — "Agents also log about 20 cases a day by hand"; L9 — "Within the first minute of a case being created it must have an owner" | Q24 (answered; built in half — D-M1S02-03) |
| REQ-014 | L9–L11 — "priority must be set from what the form or email tells us" (the error has to be visible to the person setting it) | Q5 (answered) + Q57 (**deferred**) → assumption A13 |
| REQ-015 | L6–L8 — ~400 email and ~60 web cases a day arrive without a human at the keyboard; L9–L11 — every one of them must land complete within the first minute | Q56 (answered) |
| REQ-016 | L6–L8 — the same two automated channels, which are the only population that needs the bypass; L8 — Finance work is a separate population, and neither it nor Tier 1 is in scope for this grant | Q56 (answered) + Q10 (answered — additive, no strip phase) + Q8 (answered — LicenseId left empty) |
| REQ-017 | L7 — "Agents also log about 20 cases a day by hand"; L19 — "Replies to customers go from support@ … and from billing@" (the object list every persona touches to do either) | Q9 (answered — objects in scope) + Q8 (answered — population/licence) + Q10 (answered — additive) |
| REQ-018 | L12–L14 — "Tier 1 (12 agents … membership changes monthly) … should get work pushed to them"; L18 — "Severity 1 outages are 24/7 and never pause" | Q13 (**deferred**) → assumption A1, for the record-type half only; Q8, Q9, Q10 as background |
| REQ-019 | L12–L13 — "Tier 2 (4 engineers) … pick from a list"; L16 — "Anything untouched for 8 business hours escalates to Tier 2" | Q13 (**deferred**) → assumption A1; no clarification distinguishes Tier 2's access from Tier 1's |
| REQ-020 | L8 — "Finance queries arrive at billing@acme.example and should be worked by Finance"; L18 — the only severity mention in the requirement, and it names an outage, not a finance query | Q13 (**deferred**) → assumption A1 |
| REQ-021 | L9–L11 — "Within the first minute of a case being created it must have an owner" | Q26 (answered) |
| REQ-022 | L12–L14 — "Tier 1 (12 agents across EMEA and the US, membership changes monthly) … should get work pushed to them when they are available" | Q29 (answered) |
| REQ-023 | L12–L14 — "Billing and Tier 2 pick from a list"; L15–L16 — "Anything untouched for 8 business hours escalates to Tier 2" | Q13 (**deferred**) → assumption A1, for the record-type half only; the queue/group infrastructure itself rests on requirement text, not on Q13 |
| REQ-024 | L8 — "Finance queries arrive at billing@acme.example and should be worked by Finance"; L19 — "Replies to customers go from … billing@ for finance cases" | Q1 (answered — the queue and group infrastructure serving the same population REQ-002's record type serves) |
| REQ-025 | — (no requirement line; a platform-behaviour risk the requirement never anticipates) | Q89 (answered) |
| REQ-026 | L12–L14 — "Tier 1 (12 agents across EMEA and the US, membership changes monthly) … should get work pushed to them" | Q7 (answered — minimal base profile per team); Q13 (**deferred**) → assumption A1, for the record-type default half; Q11, Q12 as background |
| REQ-027 | L12–L13 — "Tier 2 (4 engineers) … pick from a list"; L16 — "Anything untouched for 8 business hours escalates to Tier 2" | Q7 (answered); Q13 (**deferred**) → assumption A1; no clarification distinguishes Tier 2's profile access from Tier 1's |
| REQ-028 | L8 — "Finance queries arrive at billing@acme.example and should be worked by Finance" | Q7 (answered); Q13 (**deferred**) → assumption A1 |
| REQ-029 | L12–L16 — Tier 2 receives escalated Support cases and picks from a list; L8 — "Finance queries … should be worked by Finance" (the Billing half, mirroring `REQ-010`) | Q13 (**deferred**) → assumption A1; Q80 (answered — the "must be blocked" restriction) |
| REQ-030 | L9–L11 — "priority must be set from what the form or email tells us" | Q5 (answered — enforce at field/validation level, because Web-to-Case and Email-to-Case create Cases through the API, not a layout) |
| REQ-031 | L6–L8 — three named intake channels, each stamping a different `Origin`; L9 — "Within the first minute of a case being created it must have an owner" (routing reads `Origin` to decide) | Q5 (answered, same citation as REQ-030); Q24 (answered — only the web/email channels invoke the assignment rule by default, which is what makes a known `Origin` load-bearing for routing) |
| REQ-032 | L9–L11 — "the customer must receive an acknowledgement with the case number" | Q22 (answered — who sends it, and the loop question it opens); Q63 (answered — one acknowledgement per case, no parallel Flow alert); Q68 (answered — the sandbox proof gate the loop question is deferred to) |
| REQ-033 | L15–L16 — "Anything untouched for 8 business hours escalates to Tier 2" (the handover notice half, distinct from `REQ-023`/`REQ-027`'s access half) | Q63 (answered, same one-event-one-email citation as REQ-032); Q88 (answered — the Tier 2 queue-level notification default this template is distinct from, cited in prose only) |
| REQ-034 | L6–L8 — "Cases arrive by email to support@acme.example (roughly 400 a day)… Finance queries arrive at billing@acme.example" | Q17 (answered — the two addresses and their forwarding); Q15 (answered — volumes, cited in prose); Q18 (answered — ownership expressed as `caseOrigin` per address, `caseOwner` left unset); Q21 (answered — bounce/requeue); Q23 (answered — `saveEmailHeaders`); Q74 (answered — sandbox re-pointing) |
| REQ-035 | L6–L8 — "and from a form on our website (roughly 60 a day)" | Q66 (answered — the form is the only named external producer; posting path unconfirmed); Q15 (answered — volume, cited in prose) |
| REQ-036 | L9–L11 — "Within the first minute of a case being created it must have an owner" (+ L6–L8 support@/billing@ split) | Q25 (answered — the routing fields); Q18, Q24, Q26, Q27 (all answered, cited in prose) |
| REQ-037 | L9–L11 — "the customer must receive an acknowledgement with the case number" (+ L19 "Replies to customers go from support@ for general cases and from billing@ for finance cases") | Q28 (answered — the per-channel acknowledgement decision); Q63 (answered, cited in prose — one-event-one-email); Q22 (answered, cited in prose — sender identity, still open per D-M3S02-04) |
| REQ-038 | L15–L18 — "SLA: Premier accounts get a first response within 4 business hours, standard accounts within 1 business day. … Clocks pause on weekends and regional holidays. EMEA works London 08:00–18:00, the US works New York 08:00–20:00. Severity 1 outages are 24/7 and never pause." | Q39 (answered — the calendar list); Q38 (answered, cited in prose — which SLA promise each calendar serves); Q40 (answered, cited in prose — region resolution, `M4-S03`'s flow) |
| REQ-039 | — (no requirement line; Q90 is informational, not tied to a requirement bullet) | Q90 (answered — owner + cadence, individual left OPEN) |
| REQ-040 | L15 — "Premier accounts get a first response within 4 business hours" | Q38 (answered) |
| REQ-041 | L15 — "standard accounts within 1 business day" | Q38 (answered — no minute conversion; `decisions.md` D-M4S02-02) |
| REQ-042 | — (no requirement line; the shared milestone identity and its completion mechanism are a plan-level decision, not a requirement bullet) | Q53 (answered — one shared type, timing per process); D10 (the completion mechanism) |
| REQ-043 | L15–L16 — "Anything untouched for 8 business hours escalates to Tier 2"; L18 — "Severity 1 outages are 24/7 and never pause" (the escalation *rule* itself, distinct from `REQ-023`/`REQ-027`'s access half and `REQ-033`'s handover-notice half) | Q45 (answered — reassign and notify); Q42, Q43, Q46, Q47, Q91 (all answered, cited in prose); D7 (why a rule and not a Flow) |
| REQ-044 | — (no requirement line naming Apex directly; the mechanism is a plan-level decision reached from L15–L16's SLA promise, the same shape `REQ-042` already carries for the milestone identity it completes) | Q50 (answered — the completion criteria question, honoured only in part: the answer names the first outbound EmailMessage, this delivery a Case-status proxy, `decisions.md` D-M4S05-02); Q16, Q53 (answered, cited in prose); D10 (the completion mechanism) |
| REQ-045 | L9–L11 — "Within the first minute of a case being created … the SLA clock must be running on the right calendar, and priority must be set from what the form or email tells us" | Q48 (answered — per-channel entitlement automation + no-account fallback); Q16, Q40 (answered, cited in prose); Q14 (DEFERRED — assumption A2, the null-guard default); D1, D2 (the before-save Flow choice) |
| REQ-046 | — (no requirement line naming test metadata directly; the `FlowTest` is a deploy-time consequence of `REQ-045`'s `<status>Active</status>` flow, not its own requirement bullet) | Q48 (answered, cited in prose — same source as `REQ-045`) |
| REQ-047 | L15–L18 — "SLA: Premier accounts get a first response within 4 business hours … Severity 1 outages are 24/7 and never pause" (the org-level switch that lets `REQ-045`'s flow deploy `Active` rather than `Draft`, the same shape `REQ-039` already carries for a non-functional-requirement enabler) | Q40 (answered, cited in prose — same source as `REQ-045`) |
| REQ-048 | L12–L14 — "Billing and Tier 2 pick from a list" | Q31 (answered — the working-surface half, for Tier 2); D4 (the decision resolving the mechanism) |
| REQ-049 | L12–L14 — "Billing and Tier 2 pick from a list" (the same requirement line as `REQ-048`, for Billing's own queue and team) | Q31 (answered, same citation as `REQ-048`); D4 |
| REQ-050 | — (no requirement line naming a Tier 1 pull view; `requirement.md` L12–L13 says the opposite — work pushed to Tier 1 — this row exists because the step `M3-S05` would build is blocked) | Q31 (answered — cited in prose only, as the requirement this row is deliberately NOT satisfying); A7 (the assumption that licenses the interim view); D4 (cited in prose — the decision this row's own existence appears to contradict and does not) |
| REQ-051 | — (no requirement line; `admin/escalation-rules`'s own monitoring gap is what asks for this report, not a `requirement.md` bullet, the same shape `REQ-042`/`REQ-044` already carry for a plan-level need) | Q91 (answered — a saved report, reviewed weekly by the Tier 2 lead) |
| REQ-052 | — (no requirement line; a UAT-discipline requirement about tester identity, not a business rule — the same "no requirement line" shape `REQ-006`/`REQ-025`/`REQ-039`/`REQ-042`/`REQ-044`/`REQ-046`/`REQ-047`/`REQ-050`/`REQ-051` already carry) | Q77 (answered — one named tester per team, real profile + PSG, never admin) |
| REQ-053 | — (no requirement line; Q84 governs *how* the existing channel requirements are proven, not what they are) | Q84 (answered — each of the three channels tested separately) |
| REQ-054 | — (no requirement line; a testing-discipline requirement that the deny requirements already on file — `REQ-010`, `REQ-015`, `REQ-020`, `REQ-029` — must each be demonstrated by a testable restriction criterion, not itself a new restriction) | Q80 (answered — restriction criteria are first-class) |
| REQ-055 | — (no requirement line; an environment precondition, not a business requirement) | Q78 (answered — raise sandbox deliverability, scrub Contact emails first) |
| REQ-056 | — (no requirement line; a UAT programme control) | Q96 (answered — pre-session PSG recalculation gate) |
| REQ-057 | — (no requirement line; a UAT programme control) | Q97 (answered — named triager, Fail vs Blocked) |
| REQ-058 | — (no requirement line; an environment-ownership control) | Q94 (answered — named owner + named refresh approver); blocked on `M5-S02` |

---

## Assumption linkage — A1 now reaches M1-S01 (plan-verifier W03)

`plan.json.assumptions[]` records **A1** — "Billing-case confidentiality is a record-level
restriction: a Tier 1 agent cannot open a Billing case at all" — as the conservative reading of
deferred blocking question **Q13**, at `risk: high`. Its `steps[]` names only `M2-S05`.

**Since plan v5 note B01, M1-S01 carries A1's restriction.** The Case org-wide default
(`sharingModel` / `externalSharingModel` = `Private`) is the element that makes A1 true, and it
lives on `artefacts/M1-S01/objects/Case/Case.object-meta.xml`. Row **REQ-010** above is where that
is recorded: `source` is `Q13`, and the row's step is `M1-S01`.

This is recorded here rather than fixed at source. `agents/build-doc-keeper/AGENT.md` ("Does not
touch `plan.json` beyond the single status transition and run record it sets through the CLI") and
`standards/build-orchestration.md` § 2 ("No agent hand-edits `plan.json`"; every field has a
subcommand that writes it, and there is no subcommand for `assumptions[]` outside the planner's
`set-plan`) both forbid this agent editing `assumptions[].steps[]`.

**Open item for the planner, at v6:** add `M1-S01` to `A1.steps[]` and record Q13 in M1-S01's
`inputs{}`. Until that lands, `M5-S04`'s `acceptance_tests[4]` — which compiles the assumptions
section from `assumptions[].steps[]` "rather than from step-note prose" — will not name M1-S01 as a
carrier of A1, and this file is the only place the linkage exists.

## Coverage, as far as this step

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M1-S01`:

- **Requirements with no step:** not yet computable — only one of twenty-two steps is documented.
- **Steps with no requirement:** 0 of the documented set. Every one of M1-S01's ten manifest
  members is named by a row above.
- **Manual tests outstanding:** 2 — `TC-M1S01-01` and `TC-M1S01-02`, both ticked at the M1 gate.
  Compiled into the UAT case shape in this step's doc-keeper envelope
  (`envelopes/M1-S01/2026-09-06T03-15-00Z.md` § "Manual tests as UAT cases"); the pack itself is
  `M5-S04`'s declared output and is not written on a per-step run.

## Linter result

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M1-S01 --repo-root ../../..
traceability.md: 10 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

The three orphans are `BusinessProcess:Support_Process`, `BusinessProcess:Billing_Process` and
`CompactLayout:Case.Case_Intake` — the **file-stem** keys. `index_manifest` indexes every component
twice, once from `package.xml` (the member form) and once from the file name, and these are the
three components whose two forms differ. The rows above name the `fullName` / manifest form, which
is what the RTM skill's reading rules require ("the API name is the Metadata API `fullName`") and
what deploys. Renaming the rows to clear the warning would put a name in the matrix that neither the
metadata nor `package.xml` uses. Recorded as `decisions.md` D-M1S01-03.

## Notes on two cells

- **REQ-006 has no `requirement.md` anchor.** The compact layout is not asked for anywhere in the
  requirement or in any clarification answer; it entered the build through plan v5 notes B02/B03,
  which moved it from M1-S02 to M1-S01 on checker-topology grounds. `Q83` is the nearest
  clarification (it fixes Lightning desktop as the form factor for all three teams) and is recorded
  as the row's `source` for that reason, not because Q83 asked for a compact layout.
- **`decision_ref` is empty on nine of ten rows.** `plan.json.decisions[]` holds D1–D10, and only
  D5 (`sharing-selection.md` Q3 — Case OWD Private plus a criteria-based sharing rule) bears on
  this step. The other nine rows rest on clarification answers and on assumptions A26 / A28, which
  are not `D<n>` records. An empty cell here is data, not an omission.

---

## Assumption linkage after M1-S02 — A13 and A26 both already name this step

Unlike A1 (above), neither assumption this step rests on needs a planner fix:

- **A13** — "Every field a validation rule attaches its error to is present on both Case layouts",
  `risk: medium`, the conservative reading of deferred **Q57**. Its `steps[]` is
  `["M1-S02", "M3-S01"]`, which is exactly the pair that has to agree: this step places the fields,
  M3-S01 writes the rules that point at them. Row **REQ-014** is where the M1-S02 half is recorded,
  and it records that the half cannot be checked until M3-S01 exists.
- **A26** — "Case carries exactly two record types", `risk: low`. Its `steps[]` already lists
  `M1-S02` alongside `M1-S01`, `M2-S03` and `M2-S05`. It is what makes two layouts rather than one
  the right artefact count, and what puts `Severity__c` on the Support layout alone
  (`decisions.md` D-M1S02-02).

## Coverage, as far as M1-S02

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M1-S02` — two of
twenty-two steps documented:

- **Requirements with no step:** not yet computable. Fourteen `REQ-XXX` ids exist and all fourteen
  have a step; the requirement lines that no documented step serves yet (routing, SLA, email,
  sandbox proof) have not been minted as ids, because ids are minted when a step delivers them.
- **Steps with no requirement:** 0 of the documented set. Both of M1-S02's manifest members are
  named by a row above, as were all ten of M1-S01's.
- **Manual tests outstanding:** 3 — `TC-M1S01-01`, `TC-M1S01-02` and `TC-M1S02-01`, all ticked at
  the M1 gate, plus M1's own milestone manual test on `record-type-decision.md`. `TC-M1S02-01` is
  the one case in the build so far that is **only partly tickable**: half of it (A13) is not
  file-checkable until `M3-S01` runs. Compiled into the UAT case shape in this step's doc-keeper
  envelope (`envelopes/M1-S02/2026-09-06T05-10-00Z.md`); the pack itself is `M5-S04`'s declared
  output and is not written on a per-step run.

## Linter result — after M1-S02

Run twice, because the two scopes answer different questions and the M1-S01 run above used only the
narrow one.

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 14 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

This is the run that matters now: at `--manifest-dir artefacts` **every one of the fourteen rows
resolves its artefact against a real component**, and the three orphans are the same three
file-stem keys M1-S01 recorded — `BusinessProcess:Support_Process`, `BusinessProcess:Billing_Process`
and `CompactLayout:Case.Case_Intake` — carried forward unchanged and explained under "Linter result"
above (`decisions.md` D-M1S01-03). **M1-S02 adds no orphan of its own:** the `Layout` member form
`Case-Case Support Layout` is byte-identical to its file stem, so the checker's two index keys agree
and there is nothing to diverge.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M1-S02 --repo-root ../../..
traceability.md: 14 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 10 warning(s)
exit 0
```

The step-scoped run is recorded for symmetry with M1-S01's, and its ten warnings are an artefact of
the scope, not a finding: they are the ten M1-S01 rows whose components are not under
`artefacts/M1-S02/`. Both of M1-S02's own rows resolve. A matrix that spans steps has no single
correct `--manifest-dir` below the build root, which is worth knowing before `M5-S04` compiles it.

## Note on the `source` cell of REQ-014

`source` is `Q57`, a **deferred** clarification, where every other row in the matrix names an
answered one or `Q13` (also deferred, on REQ-010). The requirement is real and the assumption
standing in for it is recorded — A13, `risk: medium` — but a reader should see that the row rests on
a question nobody answered rather than on a decision somebody made. The same is true of the
`Q24` cell on REQ-013 in a different way: Q24 **is** answered, and only half of the answer could be
built.

---

## What M2-S01 rests on — one answered clarification, one verifier blocker, one forward reference

Unlike `A1` on `M1-S01`, this step needs no assumption at all and therefore no planner fix on
`assumptions[].steps[]`. Three linkages instead, and all three are already on file:

- **Q56, answered and blocking** — "Which users and integrations must be able to save a Case the rule
  would reject?" Its `answer_shape` is literally "The Custom Permission name and the Permission Set
  that carries it", which is this step's two artefacts. Both rows above name it as `source`. **Q10**
  (additive grant model) and **Q8** (LicenseId left empty) are the second-order answers, recorded on
  `REQ-016` because they decide what the permission set does *not* carry rather than what it does.
- **Plan-verifier blocker B01** — the reason this step's `manual` acceptance test is an assertion over
  `permissionsets/Case_Intake_Integration.permissionset-meta.xml` and `deploy-order.md` rather than
  over an org. `PermissionSetAssignment` is record data, so the original wording could never have been
  ticked in a `design-only` build. The rewrite is what makes `TC-M2S01-01` executable at the M2 gate,
  and it is why `REQ-016`'s manual half has file evidence already captured while its residue has none.
- **`M3-S01`, forward** — `depends_on: ["M1-S01", "M2-S01"]`, and its two validation rules are the
  only consumers this permission will ever have. That direction matters twice over: the consumer names
  in the permission's `<description>` are read from `M3-S01`'s declared `outputs[]` (D-M2S01-01), and
  the deploy ordering is load-bearing in the opposite direction — a validation rule naming a
  `$Permission` that does not exist does **not** fail the deploy, it evaluates to `false` silently, so
  every API-created Case would be blocked from the moment `M3-S01` landed until this step did
  (`custom-permissions/references/gotchas.md` #4, restated in `artefacts/M2-S01/deploy-order.md`).

## Coverage, as far as M2-S01

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M2-S01` — three of
twenty-two steps documented:

- **Requirements with no step:** not yet computable. Sixteen `REQ-XXX` ids exist and all sixteen have a
  step; ids are minted when a step delivers them, so the requirement lines no documented step serves
  yet (routing, SLA, email, sandbox proof) carry no id.
- **Steps with no requirement:** 0 of the documented set. Both of M2-S01's manifest members are named
  by a row above, as were both of M1-S02's and all ten of M1-S01's.
- **Manual tests outstanding:** 4 — `TC-M1S01-01`, `TC-M1S01-02` and `TC-M1S02-01` at the M1 gate
  (which is now `approved`, with those three ticked on the readings the M1 report states), and
  **`TC-M2S01-01`** at the M2 gate. `TC-M2S01-01` is the first case in the build whose residue is not
  merely deferred but **unevidenceable in this build class**: `PermissionSetAssignment` is record data.
  Compiled into the UAT case shape in this step's doc-keeper envelope
  (`envelopes/M2-S01/2026-09-06T08-15-00Z.md`); the pack itself is `M5-S04`'s declared output and is
  not written on a per-step run.

## Linter result — after M2-S01

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 16 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Every one of the sixteen rows resolves its artefact against a real component at build scope. The three
orphans are unchanged and are M1-S01's file-stem keys — `BusinessProcess:Support_Process`,
`BusinessProcess:Billing_Process`, `CompactLayout:Case.Case_Intake` — explained under "Linter result"
above (`decisions.md` D-M1S01-03). **M2-S01 adds no orphan:** both member forms
(`Bypass_Case_Intake_Validation`, `Case_Intake_Integration`) are byte-identical to their file stems, so
the checker's two index keys agree, as they did for M1-S02's layouts.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M2-S01 --repo-root ../../..
traceability.md: 16 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 14 warning(s)
exit 0
```

The step-scoped run is recorded for symmetry with the two M1 runs. Its fourteen warnings are the scope,
not a finding: the fourteen M1 rows name components that are not under `artefacts/M2-S01/`. A matrix
spanning steps has no single correct `--manifest-dir` below the build root — the third consecutive step
at which that is true, and worth knowing before `M5-S04` compiles it.

---

## Update pass — M1-S02 rebuild #2 (2026-09-09)

`M1-S02` was rebuilt after `reports/MOCK-DEPLOY-M1.md` findings **F-09** and **F-10**, re-tested, and
re-documented. This section is that second documentation run's record; the three sections above it
record what was true after the first, and are left byte-identical.

**Rows amended — four, and only three cells each.** `REQ-011`, `REQ-012`, `REQ-013` and `REQ-014`
kept `req_id`, `source`, `requirement`, `step_id`, `artefact`, `agent`, `decision_ref`, `test_id`,
`test_type`, `status` and `artefact_paths` byte-identical; only `test_result` was rewritten. Nothing
in the other twelve rows was touched. The artefact paths did not change because the rebuild added
`layoutItems` inside two existing files rather than producing new ones, and `package.xml` is
unchanged for the same reason.

**`decision_ref` was tried and reverted.** `D-M1S02-05` was written into `REQ-011` and `REQ-012`,
and `check_rtm.py` warned `decision_ref 'D-M1S02-05' is not the build-plan shape D<n>` on both — the
column carries `plan.json` `decisions[]` ids (`REQ-010` carries `D5`), not `decisions.md` log ids.
Both cells were returned to `—` and the reference lives in `test_result`, where it reads as prose
rather than as a key. Recorded so the next run does not re-derive it.

**Status cells stay `In UAT`.** Every executable test on this step passes and its one manual test is
still outstanding, which is what `In UAT` means. The rebuild changed the evidence behind the status,
not the status.

## Linter result — after the M1-S02 rebuild

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 16 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Zero errors, the same three M1-S01 orphans, and the single orphan warning that has stood since
M1-S01 — unchanged from the run after `M2-S01`.

**Two warnings appeared and were gone again inside this run, and they were not this step's.** Run
mid-pass, `check_rtm.py` reported:

```
WARN: row 4 (REQ-003): artefact 'BusinessProcess:Case.Support Process' not found under the manifest dir
WARN: row 5 (REQ-004): artefact 'BusinessProcess:Case.Billing Process' not found under the manifest dir
```

That is the F-11 remediation surfacing in this document: `M1-S01` was rebuilt the same day to make
each `BusinessProcess` file stem equal its `<fullName>` (`Support_Process`, `Billing_Process`), and
its rows still named the spaced form. They were **not** amended here —
`agents/build-doc-keeper/AGENT.md` Step 8 rule 4 leaves another step's rows byte-identical. Between
that run and the final one both cells were rewritten to `BusinessProcess:Case.Support_Process` /
`…Billing_Process` **by a concurrent `M1-S01` documentation pass in another session**, which is why
the count returned to 1. Recorded rather than quietly dropped: a linter figure in this document is
a reading of a shared directory at a moment, and on this build two sessions were writing it.
`M1-S01` was still at `tested` when this run finished, so that pass had not yet set its status.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M1-S02 --repo-root ../../..
traceability.md: 16 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 12 warning(s)
exit 0
```

Twelve warnings, all scope: the twelve rows whose components sit outside `artefacts/M1-S02/`. Both
of this step's own rows resolve, exactly as they did on the first pass. (A mid-pass run of this same
command reported 14 — the extra two were the `decision_ref` warnings described above, before those
cells were returned to `—`.)

**Manual tests outstanding — still 4, and `TC-M1S02-01` is unchanged by the rebuild.** The case's
Q24 half turns on `<showRunAssignmentRulesCheckbox>`, which the rebuild did not touch, and its A13
half is still waiting on `M3-S01`. The case record was re-staged and re-linted in this run's
doc-keeper envelope (`envelopes/M1-S02/2026-09-09T20-12-00Z.md`) with the field counts and the
seed-data reference brought up to rebuild #2; the pack itself remains `M5-S04`'s declared output.

**One carry-forward for the M1 gate that this document cannot settle.** `milestone:M1` was approved
on 2026-09-06 against build #1's layouts, and `reports/MILESTONE-M1-REPORT.md` describes them. The
rows above now describe rebuild #2's. That divergence is recorded as `decisions.md` **O-M1S02-03**
and is a re-verification, not a documentation, fix.

---

## M1-S01 re-documented after rebuild #2 (finding F-11) — 2026-09-09

This is an **update pass on an existing step**, not a new step's rows. `M1-S01` went
`documented → running → built → tested` a second time (`envelopes/M1-S01/2026-09-09T19-45-00Z.md`,
`…19-52-47Z.md`) because `reports/MOCK-DEPLOY-M1.md` finding **F-11** showed the step's business
processes could not deploy in source format. Four of its ten rows carried a name the rebuild changed.

**Rows amended, and the cell in each:**

| Row | Cell | Before | After |
|---|---|---|---|
| REQ-001 | `test_result` | (no rebuild record) | re-test verdict after rebuild #2; both record types' `<businessProcess>` now stem form |
| REQ-002 | `test_result` | "same run as REQ-001" | same, plus the `Billing_Process` reference |
| REQ-003 | `artefact`, `test_result` | `BusinessProcess:Case.Support Process` | `BusinessProcess:Case.Support_Process` |
| REQ-004 | `artefact`, `test_result` | `BusinessProcess:Case.Billing Process` | `BusinessProcess:Case.Billing_Process` |

**Rows left byte-identical, and why.** REQ-005 through REQ-010 name components the rebuild did not
touch — `StandardValueSet:CaseOrigin`, `CompactLayout:Case_Intake`, the three `CustomField`s and
`CustomObject:Case`, all still carrying their 2026-09-05 mtimes
(`envelopes/M1-S01/2026-09-09T19-45-00Z.md` § Artefacts). Their verdicts were re-earned rather than
carried over: the tester re-ran all six runnable tests on the whole step directory and every one
exited 0, so no cell in those six rows is stale. Rows REQ-011 onward belong to other steps and were
not read for writing in this pass.

**Row keys are unchanged.** `req_id` + `step_id` is the traceability key per
`agents/build-doc-keeper/AGENT.md` Step 8, so a re-documentation run replaces the four rows in place
and the matrix still holds one row per requirement rather than a rebuild-#1 row beside a rebuild-#2
row.

### Coverage, after M1-S01 rebuild #2

Unchanged in count from the M2-S01 pass — a rebuild changes what a row says, not how many there are:

- **Requirements with no step:** not yet computable. Sixteen `REQ-XXX` ids exist and all sixteen have
  a step.
- **Steps with no requirement:** 0 of the documented set. All ten of M1-S01's manifest members are
  still named by a row, and the two whose member names changed were renamed in place.
- **Manual tests outstanding:** 4 — `TC-M1S01-01`, `TC-M1S01-02`, `TC-M1S02-01`, `TC-M2S01-01`.
  **`TC-M1S01-01` needs re-reading before it is ticked again**: it was ticked at the M1 gate against
  rebuild #1, and the M1 gate predates these artefacts. Its assertion still holds on disk — bare
  process name inside each record type, object-qualified members in `package.xml` — but its
  parenthetical counter-example, "(not `Case.Support Process`)", now names a string that is wrong on
  two counts at once and no longer describes the failure it was written to exclude. The plan owns
  that text; see `decisions.md` § "Open items for the planner — raised by the M1-S01 rebuild #2
  documentation run", **O-M1S01-02**.

### Linter result — after M1-S01 rebuild #2

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 16 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M1-S01 --repo-root ../../..
traceability.md: 16 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 7 warning(s)
exit 0
```

The step-scoped run's six extra warnings are the scope, as on every previous pass: they are the six
rows whose components live under `artefacts/M1-S02/` and `artefacts/M2-S01/`. All ten M1-S01 rows
resolve at both scopes.

**The three orphans survive the rebuild, but for half the reason they had before.** They are still
`BusinessProcess:Support_Process`, `BusinessProcess:Billing_Process` and
`CompactLayout:Case.Case_Intake` — the **file-stem** index keys, which `check_rtm.py` derives
alongside the `package.xml` member keys. Before rebuild #2 the stem key and the member key differed
on two axes at once: the space (`Support Process` vs `Support_Process`) **and** the object
qualification (`Case.` vs no prefix). F-11 removed the first; only the second remains, and it is
required — `package.xml` names a `BusinessProcess` member object-qualified and the file stem cannot
carry a dot. So the WARN is now a pure manifest-convention artefact rather than the surfacing of a
real naming divergence, and `decisions.md` **D-M1S01-03**'s three-spellings table is superseded on
its `fullName` row by **D-M1S01-05** while its manifest row stands.

---

## What M2-S02 rests on — Q8/Q9/Q10 for the baseline, Q13 → A1 for the persona split

Four clarifications ground this step's four new rows, and one of them needs the same kind of
planner note `traceability.md` already carries for M1-S01 and A1:

- **Q9, answered** — "Which objects, fields, tabs, apps, record types, layouts and classes are in
  scope?" Its `answer_shape` — "the package.xml that makes the retrieve honest, reused for the
  deploy" — is the object list `Case_Agent_Core` grants. `REQ-017`.
- **Q8, answered** — the licence/population split (18 users, 12/4/2) that decided LicenseId stays
  empty on all four sets. Background on every row; not a `req_id` source of its own, because no
  requirement line asks for a licence policy — it is a design input, not a need.
- **Q10, answered** — additive, no strip phase. Same standing as Q8: it shapes what the builder
  did NOT write (no `MutingPermissionSet`) rather than serving a requirement line.
- **Q13, deferred → assumption A1, conservative reading** — "can others not open the record at
  all, or can they open it but should not see a field on it?" `A1`'s text is the record-level
  reading: a Tier 1 agent cannot open a Billing case at all. `REQ-018`, `REQ-019` and `REQ-020` all
  cite it, for the **recordTypeVisibilities** half of that reading — `Case_Tier1`/`Case_Tier2`
  see `Case.Support` only, `Case_Billing` sees `Case.Billing` only.

**`recordTypeVisibilities` is not what makes A1 true, and this step's rows say so rather than
implying otherwise.** `A1`'s actual mechanism is the Private OWD (`M1-S01`, built) plus the
criteria-based sharing rule `M2-S05` has not built yet. `recordTypeVisibilities` controls which
record type a user may **select when creating or editing** a Case, not whether they can **open**
one that already exists — a Tier 1 agent denied `Case.Billing` visibility here could still open an
existing Billing case today if `M2-S05`'s sharing rule doesn't yet exist to stop them, and the
Private OWD is the layer actually doing that job in the interval. This is why `REQ-018`–`REQ-020`
are `In Build`, not `In UAT`: a step that serves the requirement (`M2-S05`) remains, the same rule
`REQ-015`'s row states for `M3-S01`.

**Same planner gap `traceability.md`'s M1-S01 section already names for A1, one step further.**
`plan.json` → `assumptions[A1].steps[]` reads `["M2-S05"]` only. It does not name `M1-S01` (recorded
above, `decisions.md` W03) and it does not name `M2-S02` either, even though this step's
`recordTypeVisibilities` grants are themselves shaped by A1's conservative reading — `deploy-order.md`
says so in as many words ("The Support record type is deliberately not granted: Q13 was deferred
and the plan takes the conservative reading (assumption A1)"). `M5-S04`'s compile run reads
`assumptions[].steps[]` to build the assumptions section "rather than from step-note prose"
(per its own acceptance test), so as things stand it will not name `M2-S02` as a step A1 reaches
either — the same class of gap, one step further down the list. Recorded here rather than fixed
here, for the same reason as before: `standards/build-orchestration.md` § 2 gives `set-plan` sole
authority over `assumptions[].steps[]`, and this agent does not touch `plan.json` beyond its own
status transition.

## Coverage, as far as M2-S02

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M2-S02` — four of
twenty-two steps documented:

- **Requirements with no step:** not yet computable. Twenty `REQ-XXX` ids exist and all twenty have
  a step; ids are minted when a step delivers them, so the requirement lines no documented step
  serves yet (routing, SLA, email, sandbox proof, the base profiles) carry no id.
- **Steps with no requirement:** 0 of the documented set. All seven of M2-S02's `PermissionSet` /
  `PermissionSetGroup` manifest members are named by a row above, as were both of M2-S01's, both of
  M1-S02's and all ten of M1-S01's.
- **Manual tests outstanding:** unchanged at 4 — `TC-M1S01-01`, `TC-M1S01-02`, `TC-M1S02-01` and
  `TC-M2S01-01`. **`M2-S02` declares no `manual` acceptance test at all** — `tests/M2-S02/results.json`
  → `"skipped_manual": []` — so it adds nothing to this count. Its four new rows are `checker`-typed
  and all pass; three of the four are `In Build` rather than `In UAT` for the reason given above, and
  none of the four is waiting on a tick at a gate.

## Linter result — after M2-S02

This section was written and re-run twice in the course of one documentation pass, because a
second session was rebuilding `M1-S01` for finding F-13 concurrently with this run, and the two
readings genuinely differ. Both are recorded, in order, rather than only the final one, because the
intermediate reading is what explains `REQ-006`'s own `test_result` cell above.

**First reading, mid-pass:**

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 20 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 2 warning(s)
exit 0
```

Not the 3-orphan / 1-warning figure every earlier run in this file recorded, and the change was not
`M2-S02`'s: `artefacts/M1-S01/package.xml`'s `CompactLayout` member had just changed from the bare
`Case_Intake` to the object-qualified `Case.Case_Intake` (mtime 2026-09-11 20:12, against
`reports/MOCK-DEPLOY-M1.md`'s mtime 20:17 the same evening) — **O-M1S01-03 resolving**, mid-flight.
One of the three long-standing orphans dropped out of the orphan report (the manifest's
`CompactLayout` member and its file stem no longer disagreed), while `REQ-006`'s own row — which
still named `artefact` as the bare `CompactLayout:Case_Intake` at that moment — became a
**resolution failure** instead (`row 7 (REQ-006): artefact 'CompactLayout:Case_Intake' not found
under the manifest dir`), the same divergence-then-stale-row shape `BusinessProcess`'s `fullName`
went through after F-11.

**Second reading, after the concurrent `M1-S01` pass amended `REQ-006`:**

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 20 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

The resolution failure is gone: `REQ-006`'s `artefact` cell now reads `CompactLayout:Case.Case_Intake`,
matching the manifest, and its own `test_result` cell records the rebuild #3 re-test — not this
run's row to write, and not rewritten here. The orphan count stands at **2**, both
`BusinessProcess:Support_Process` and `BusinessProcess:Billing_Process`, unchanged and explained
under "Linter result" above (`decisions.md` D-M1S01-03). This is the state to read as current;
the first reading is kept above only because it is the reading `REQ-006`'s own cell points back to.

`M2-S02` itself adds no orphan and no warning of its own in either reading: all seven of its
manifest members (four `PermissionSet`, three `PermissionSetGroup`) are byte-identical to their
file stems, the same shape `M1-S02`'s `Layout` members and `M2-S01`'s two members already showed.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M2-S02 --repo-root ../../..
traceability.md: 20 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 16 warning(s)
exit 0
```

The step-scoped run is recorded for symmetry with every prior step's. Its sixteen warnings are the
scope, not a finding: the sixteen rows belonging to `M1-S01`, `M1-S02` and `M2-S01` whose components
are not under `artefacts/M2-S02/`. Both of `PermissionSet:Case_Agent_Core`'s and `PermissionSet:
Case_Tier1`/`Case_Tier2`/`Case_Billing`'s rows resolve, as do the three `PermissionSetGroup` rows'
`artefact_paths` cells (the group files are the second half of each `artefact_paths` pipe pair, and
`check_rtm.py` reads `artefact` as a single value — see the REQ-013 note above for why the column
names one component when two are relevant).

## Linter result — after `M1-S01` rebuild #3 (F-13), 2026-09-12

The prior section named exactly this as an open item — "whichever session is currently rebuilding
`M1-S01` for F-13 should document `REQ-006`'s `artefact` cell … once it reaches `tested`." This is
that documentation pass. `REQ-006`'s `artefact` cell was rewritten from the bare `CompactLayout:
Case_Intake` to the object-qualified `CompactLayout:Case.Case_Intake`, matching `artefacts/M1-S01/
package.xml`'s rebuilt `CompactLayout` member.

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 20 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

One fewer warning than the `M2-S02` run recorded (2 → 1): the **resolution failure** on `REQ-006`
("artefact 'CompactLayout:Case_Intake' not found under the manifest dir") is gone, because the row
now names the form the manifest actually carries. The two orphans are unchanged from every run since
rebuild #2 — `BusinessProcess:Support_Process` and `BusinessProcess:Billing_Process`, the file-stem
keys that disagree with `check_rtm.py`'s object-qualified manifest-member keys because
`businessProcesses` is not one of the object-child directories the tool re-qualifies by parent
folder (`decisions.md` D-M1S01-03). `CompactLayout` is not among them: its file lives under
`compactLayouts/`, which the tool does re-qualify, so once the manifest member and the file-derived
key agree — as they now do — the two collapse into one index entry and there is nothing left to
orphan.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M1-S01 --repo-root ../../..
traceability.md: 20 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 11 warning(s)
exit 0
```

The step-scoped run's eleven warnings are the ten rows belonging to `M1-S02`, `M2-S01` and `M2-S02`
whose components are not under `artefacts/M1-S01/`, plus the same orphan warning. All ten of
`M1-S01`'s own rows — `REQ-006` included — resolve at this scope.

---

## What M2-S04 rests on — five clarifications, one deferred assumption, and three requirements with no dedicated manual test of their own

Five new rows, five new requirements, and — unlike every access step so far — the requirements they
serve are almost all still `In Build` after this step, because queue/group existence is
infrastructure other steps route through rather than a requirement this step alone completes:

- **Q26, answered and blocking** — "Queue or person, and what happens when nobody matches?" Its
  answer names `Tier_1_General` as the fall-through owner. `REQ-021`. The mechanism that actually
  routes a case there is `M3-S04`'s assignment rule (`pending`), so this row is `In Build`.
- **Q29, answered and blocking** — "Who works each pool, and how does that membership list change?"
  Its answer — role and public group, no named users, because Tier 1's roster changes monthly — is
  what `REQ-022` serves and what the `W02 (2/3)` manual test checks. The role half of the answer is
  unwritten (`decisions.md` D-M2S04-03).
- **Q30, answered and blocking** — "Which objects will each queue own?" Answered "Case only, on all
  three queues." This is not a `req_id` of its own — it is a cross-cutting constraint every one of
  `REQ-021`–`024`'s rows asserts (`queueSobject/sobjectType = Case`), the same way `D-M2S02-01`'s Q9
  answer is background on four M2-S02 rows rather than a `req_id` source of its own.
- **Q88, answered, informational** — "Who should be notified of a new record?" Answered per queue:
  Tier 1 none (Omni push), Billing the queue address, Tier 2 a shared mailbox with **no address
  named**. `REQ-024` (Billing's half holds); `REQ-023` carries the Tier 2 half, which does **not**
  hold on the artefact — `decisions.md` D-M2S04-02, O-M2S04-02.
- **Q89, answered, informational** — "What happens to queue-owned records when a queue is retired?"
  Answered with a reassign-before-delete runbook step. `REQ-025`, the only row of the five with no
  further step remaining — `In UAT` rather than `In Build`.
- **Q13, deferred → assumption A1** — reaches `REQ-023` for the same reason it reaches `REQ-018`–`020`
  on `M2-S02`: the record-type / access split those rows carry is A1's conservative reading, and this
  step's queue/group infrastructure for Tier 2 is what that access eventually routes work into. **Same
  planner gap as `M1-S01` and `M2-S02`:** `plan.json` → `assumptions[A1].steps[]` reads
  `["M2-S05"]` only, and does not name `M2-S04` either, though `REQ-023`'s row states the A1
  connection explicitly. Recorded here as the third instance of the same open item `traceability.md`
  already carries for `M1-S01` (`decisions.md` W03) and `M2-S02` (`decisions.md` O-M2S02-03).
- **`M3-S04`, `M3-S05`, `M3-S03`, `M4-S04`, `M5-S01`, `M2-S05`, forward** — six steps `depends_on`
  `M2-S04`, more than any prior step in this build. That is why four of the five new rows are
  `In Build`: the queue and group metadata exists and is tested, but the requirement each row states
  (routing, push, escalation target, pull-list access, notification) is only completed once its
  dependent step lands. Only `REQ-025` (retirement) has no dependent step and is `In UAT`.

## Coverage, as far as M2-S04

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M2-S04` — five of
twenty-two steps documented (`M2-S03` is mid-rebuild in a concurrent session and is not counted
here; its rows are not this run's to write):

- **Requirements with no step:** not yet computable. Twenty-five `REQ-XXX` ids exist and all
  twenty-five have a step; ids are minted when a step delivers them.
- **Steps with no requirement:** 0 of the documented set. All six of `M2-S04`'s manifest members
  (three `Queue`, three `Group`) are named by a row above, as were every prior documented step's.
  `M2-S04`'s `package.xml`, `deploy-order.md` and `queue-retirement-runbook.md` are workbook rows
  (`CWB-OTHER-010`–`012`), not traceability rows — the RTM's `artefact` column names Metadata API
  components (or `setup-only:` documents), and `package.xml`/`deploy-order.md` are neither; they are
  the manifest and the deploy note *for* the six components, not components of their own.
- **Manual tests outstanding:** 8 — the 4 already outstanding at the M1/M2 gates (`TC-M1S01-01`,
  `TC-M1S01-02`, `TC-M1S02-01`, `TC-M2S01-01`) plus this step's four (`M2-S04-T2` through `-T5`,
  staged as `TC-M2S04-01`–`04` in this run's UAT draft — see this envelope's `extensions.uat_staging`).
  **One of the four is not a plain tick:** `M2-S04-T3`'s Tier 2 half is a documented criterion/
  artefact mismatch (`decisions.md` O-M2S04-02), staged as `TC-M2S04-02`'s `known_mismatch` field
  rather than presented as tickable. `M2-S02` declared no manual test at all, so this is the first
  new manual-test volume added since `M2-S01`.
- **Orphan artefacts, build scope:** 5 — unchanged in kind from the pattern already on file
  (`BusinessProcess:Support_Process`, `BusinessProcess:Billing_Process`, both `decisions.md`
  D-M1S01-03) plus three `Profile:*` members from `M2-S03`'s `package.xml`. **The three `Profile`
  orphans are not this step's to close:** `M2-S03` is `pending` documentation in a concurrent
  session per this run's own instructions, and its rows are not written here — see the orphan report
  below. None of `M2-S04`'s own six members orphan.

## Linter result — after M2-S04

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 25 row(s), build schema, 0 coverage gap(s), 5 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

The single warning is the orphan-count summary line; the five orphans are the two `M1-S01`
`BusinessProcess` file-stem keys (unchanged, `decisions.md` D-M1S01-03) and three `M2-S03` `Profile`
members with no row yet, because that step is mid-rebuild in a concurrent session, per this run's
own scope instructions. **`M2-S04` adds no orphan and no error of its own:** all six of its manifest
members resolve against `REQ-021`–`024`'s rows. Two warnings surfaced and were fixed inside this same
documentation pass rather than left standing: `source 'Q1 (L8, L19)'` on `REQ-024` did not match the
build-plan `Q<n>` shape (fixed by dropping the parenthetical — the `source` column names a
clarification id, not a citation), and `artefact 'queue-retirement-runbook.md'` on `REQ-025` had no
metadata-type prefix and did not resolve under the manifest dir, because it is a markdown runbook the
Metadata API cannot carry — fixed by prefixing it `setup-only:`, exactly as the checker's own message
suggests.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M2-S04 --repo-root ../../..
traceability.md: 25 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 20 warning(s)
exit 0
```

The step-scoped run's twenty warnings are the twenty rows belonging to every earlier step whose
components are not under `artefacts/M2-S04/`. All five of `M2-S04`'s own rows resolve at this scope,
and the `setup-only:` row (`REQ-025`) draws no warning here — the checker skips existence resolution
entirely for a row marked that way, at either scope.

---

## Linter result — after M2-S02 rebuild #2 (F-15), 2026-09-12

`REQ-017`–`020`'s `test_result` cells were amended with the rebuild #2 retest evidence
(`<description>` trimmed to ≤200 chars on the four `PermissionSet` files, `step-tester` run
`2026-09-12T01-26-00Z`, all three cited checkers exit 0 with the new DESC-01/02 rules firing clean —
`decisions.md` D-M2S02-07). No `req_id`, `artefact`, `step_id` or `status` cell changed; the artefact
paths named in these four rows are unaffected by a description-only edit.

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 25 row(s), build schema, 0 coverage gap(s), 6 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Six orphans at build scope, up from the two `M1-S01` rebuild #3 left standing (`BusinessProcess:
Support_Process` / `Billing_Process`, unchanged by this run — `decisions.md` D-M1S01-03). The other
four are `Profile:Acme Support Tier 1` / `Acme Support Tier 2` / `Acme Billing` and one further
manifest member under `artefacts/M2-S03/`, none of which this run wrote or amended — `M2-S03` was
mid-rebuild in a concurrent session at the time of this reading, per that step's own doc-keeper pass
landing `REQ-026`–`028` (`workbook/03-profiles-permission-sets-and-psgs.md` `CWB-PERM-010`–`012`)
after this run's own edits. Not this run's rows to fix.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M2-S02 --repo-root ../../..
traceability.md: 25 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 20 warning(s)
exit 0
```

The step-scoped run's twenty warnings are the twenty rows belonging to every other step, unchanged in
shape from the `M2-S04` run above (one fewer row now in scope at the twenty-row count only because
the comparison point moved). All four of `M2-S02`'s amended rows — `REQ-017`–`020` — resolve at this
scope with the rebuild's own artefact paths, which this run did not change.

---

## What M2-S03 rests on — Q7 for the residue shape, Q13 → A1 for the record-type default split, Q11/Q12 as background

Three new rows, three new requirements, minted after re-reading this file immediately before
writing — the concurrent `M2-S02` session's own rebuild-#2 pass (§ "Linter result — after M2-S02
rebuild #2 (F-15)" above) had already anticipated these ids and this file's row count; only its own
`M2-S02` rows were amended by that pass, and only `M2-S03`'s rows are written here:

- **Q7, answered** — "What is on the current profile that has no permission-set equivalent?" Its
  answer is, almost verbatim, what all three profiles are: "a minimal base profile per team carrying
  only layout assignments, default app and default record type; every object, field and tab grant
  lives in permission sets." `REQ-026`–`028` all cite it as `source`, the same way `D-M2S02-01`'s Q9
  answer is the shared background for four `M2-S02` rows.
- **Q13, deferred → assumption A1, conservative reading** — reaches these three rows exactly as it
  reaches `Case_Tier1`/`Case_Tier2`/`Case_Billing` on `M2-S02` (`REQ-018`–`020`), one layer up the
  access stack: `recordTypeVisibilities` on each profile grants the persona's own record type as
  default/visible and withholds the other. **Same planner gap, a third time:** `plan.json` →
  `assumptions[A1].steps[]` reads `["M2-S05"]` only and does not name `M1-S01`, `M2-S02` or `M2-S03`,
  though all three carry artefacts A1 shapes — `decisions.md` **W03** (M1-S01), **O-M2S02-03**
  (M2-S02) and now **O-M2S03-03** (this step) record the identical open item three times.
- **Q11, answered, background** — "Clone Standard User into custom profiles before any deploy is
  attempted." Superseded at this manifest's API version (62.0) by Minimum-Access seeding
  (`decisions.md` **D-M2S03-04**); `<custom>true</custom>` is what the answer actually turns on, and
  all three files carry it.
- **Q12, answered, background** — employees only, 18 people total, no customer portal in this phase.
  Not a `req_id` source of its own — it bounds the population these three profiles serve, the same
  standing Q8/Q10 have as background on the `M2-S02` rows.

**`recordTypeVisibilities` is not what makes A1 true here either**, the same caveat this file's
M1-S01 and M2-S02 sections both already state: the mechanism is the Private OWD (`M1-S01`, built)
plus `M2-S05`'s sharing rule (`built`, not yet `tested` or `documented` as of this pass — its
`package.xml` is on disk, which is why `check_rtm.py`'s orphan report below names a `SharingRules`
orphan that is not this step's to resolve). `recordTypeVisibilities` and `layoutAssignments` govern
which record type a user may *select* and which layout they see, never whether they may *open* a
record of a type they lack — which is why `REQ-026`–`028` are `In Build`, not `In UAT`.

**This step closes M1 finding F-01.** Full record: `decisions.md` **D-M2S03-07**. Before this run,
`check_record_type_layouts.py --manifest-dir artefacts --strict` had zero `layoutAssignments`
anywhere in the tree to resolve; with these three files present it resolves 9 `layoutAssignments`
and 12 record-type references and exits 0 on 0 findings — the assertion both M1 milestone reports
said was never made anywhere in M1 is now made, by this step, and it passes.

## Coverage, as far as M2-S03

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M2-S03` — six of
twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`):

- **Requirements with no step:** not yet computable. Twenty-eight `REQ-XXX` ids exist and all
  twenty-eight have a step; ids are minted when a step delivers them, so the requirement lines no
  documented step serves yet (the two remaining M2 steps, all of M3/M4/M5) carry no id.
- **Steps with no requirement:** 0 of the documented set. All three of `M2-S03`'s `Profile` manifest
  members are named by a row above, as were every prior documented step's. `M2-S03`'s `package.xml`
  and `deploy-order.md` are workbook rows (`CWB-OTHER-013`, `-014`), not traceability rows, the same
  convention `M2-S04`'s manifest/deploy-order/runbook rows already established.
- **Manual tests outstanding:** unchanged at 8 (the four from M1/M2-S01, plus `M2-S04`'s four staged
  as `TC-M2S04-01`–`04`). **`M2-S03` declares no `manual` acceptance test at all** —
  `tests/M2-S03/results.json` → `"skipped_manual": []`, both before and after Rebuild #2 — so it adds
  nothing to this count, the same shape `M2-S02` recorded.
- **Orphan artefacts, build scope:** 3 — down from the 6 the concurrent `M2-S02` pass's reading
  recorded, because this run's three rows resolve the `Profile:Acme Support Tier 1` /
  `Acme Support Tier 2` / `Acme Billing` orphans that reading named. The three that remain are the
  two `M1-S01` `BusinessProcess` file-stem keys (unchanged, `decisions.md` D-M1S01-03) and one
  `SharingRules:Case` orphan from `artefacts/M2-S05/package.xml` — `M2-S05` is `built` but not yet
  `tested`/`documented`, and its row is not this run's to write.

## Linter result — after M2-S03

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 28 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Zero errors. The three orphans are exactly the two named above under "Coverage" plus the `M2-S05`
one — none of them `M2-S03`'s. `M2-S03` adds no orphan and no error of its own: all three `Profile`
manifest members are byte-identical to their file stems (`Profile` fullName carries the literal
display name with spaces, and the file stem does too — the same non-divergence `M1-S02`'s `Layout`
members and `M2-S02`'s `PermissionSet`/`PermissionSetGroup` members already showed).

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M2-S03 --repo-root ../../..
traceability.md: 28 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 24 warning(s)
exit 0
```

The step-scoped run's twenty-four warnings are the twenty-four rows belonging to every other
documented and undocumented step whose components are not under `artefacts/M2-S03/` — the scope, not
a finding, the same shape every prior step-scoped run in this file has produced. All three of
`M2-S03`'s own rows resolve at this scope.

## What M2-S05 rests on — Q13 → A1 for the Billing restriction, Q80 for the "must be blocked" half, D5 for the mechanism

One new row, one new requirement, minted after re-reading this file immediately before writing (no
concurrent session was writing here at the time — `M2-S03` finished documenting before this pass
started, confirmed by `plan.json` reading `documented` for it):

- **Q13, deferred → assumption A1, conservative reading** — reaches `REQ-029` a third time at the
  access-mechanism layer, after `REQ-010` (the OWD, `M1-S01`) and `REQ-018`–`020`/`026`–`028` (record
  type default/visibility, `M2-S02`/`M2-S03`). This is the layer where the restriction is actually
  enforced: the OWD sets the default and the profiles decide which record type a persona may *pick*,
  but only the sharing rule (or its absence) decides who may *open* a record they do not own. **The
  same planner gap, a fourth time:** `plan.json` → `assumptions[A1].steps[]` reads `["M2-S05"]`
  only — this is the one step A1 already names, so there is nothing to add here, unlike the open item
  `decisions.md` **W03** / **O-M2S02-03** / **O-M2S03-03** record for the other three.
- **Q80, answered** — "At minimum: Tier 1 must not see billing cases if that is the intent." This is
  the restriction half of `D5`'s two-answer citation (`decisions[D5].answers = ["Q13", "Q80"]`) and
  is why `REQ-029`'s requirement sentence states the Billing negative explicitly rather than leaving
  it as a silent absence.
- **D5, the mechanism** — `standards/decision-trees/sharing-selection.md` branch **Q3**: "the access
  is exactly 'the Tier 2 group should see cases whose RecordType is Support', and `RecordTypeId` is
  on the record itself" → criteria-based sharing rule. `D5.consequences` already states the re-plan
  condition if Q13 resolves to field-level masking instead of record-level.

**`REQ-029` does not replace `REQ-010`.** Both trace to the same deferred question and the same
assumption, at two different artefacts: `REQ-010` is `M1-S01`'s OWD (`Case.object-meta.xml`),
`REQ-029` is `M2-S05`'s sharing rule (`Case.sharingRules-meta.xml`) plus the visibility-model document
that narrates both. `REQ-010`'s row is not amended by this pass — `agents/build-doc-keeper/AGENT.md`
Step 8 restricts this run to `M2-S05`'s own rows — but its notes are now stale in one place: the
sentence "the machine assertion ... has not run" no longer holds, since this run's build-scope
`check_sharing_model.py` pass is exactly that assertion, and it passed. Recorded as **O-M2S05-02**
in `decisions.md` rather than silently left to look current.

**Billing's own access is not this row's concern, and the workbook says so explicitly
(`CWB-SHARE-002`'s gap list, item 4).** No sharing rule targets `Billing_Team` or the Billing record
type. Billing reaches its own cases as **queue owner**, through the `Billing` queue `M2-S04` built —
a different access mechanism than the one this row documents. The two mechanisms are correct
together (queue ownership for Billing, sharing rule for Tier 2) but nobody has reconciled them
against the requirement's Billing sentences (L8, L19) in one place — flagged as **O-M2S05-01** below
and in the workbook's Section 4 preamble, for the planner to close before the G3 gate.

## Coverage, as far as M2-S05

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M2-S05` — seven of
twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`, `M2-S05`):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Twenty-nine `REQ-XXX` ids exist and all
  twenty-nine have a step.
- **Steps with no requirement:** 0 of the documented set. `M2-S05`'s one manifest member
  (`SharingRules:Case`) is named by `REQ-029` above. `M2-S05`'s `package.xml` and `deploy-order.md`
  are workbook rows (`CWB-OTHER-015`, `-016`), not traceability rows, the same convention every
  prior step's manifest/deploy-order pair already established.
- **Manual tests outstanding:** 10 — the 8 already outstanding after `M2-S04` (`TC-M1S01-01`,
  `TC-M1S01-02`, `TC-M1S02-01`, `TC-M2S01-01`, `TC-M2S04-01`–`04`) plus this step's manual test,
  staged as two cases (`TC-M2S05-01`, `TC-M2S05-02`, the grant half and the Billing-negative half) —
  `M2-S03` declared no manual test at all, so it added none.
- **Orphan artefacts, build scope:** 2 — down from the 3 the `M2-S03` reading recorded, because this
  run's row resolves the `SharingRules:Case` orphan `M2-S03`'s own coverage section named as
  belonging to a step that was `built` but not yet documented. The two that remain are the
  `M1-S01` `BusinessProcess` file-stem keys, unchanged (`decisions.md` D-M1S01-03).

## Linter result — after M2-S05

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 29 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Zero errors. The two orphans are exactly the `BusinessProcess` pair named above — `M2-S05` adds no
orphan and no error of its own: its single manifest member (`SharingRules:Case`) resolves against
`REQ-029`'s row.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M2-S05 --repo-root ../../..
traceability.md: 29 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 26 warning(s)
exit 0
```

The step-scoped run's twenty-six warnings are the twenty-six rows belonging to every other step
whose components are not under `artefacts/M2-S05/` — scope, not a finding, the same shape every
prior step-scoped run in this file has produced. `REQ-029`'s own row resolves at this scope.

## What M3-S01 rests on — Q5 for both rules, Q24 for Origin's routing half, the M2-S01 bypass grant as a forward dependency

Two new rows, two new requirements, minted after re-reading this file immediately before writing
(`M3-S02` is `running` concurrently but is a `ui` step touching layouts, not this file's Section 5
or Other Configuration rows):

- **Q5, answered** — "Priority and Origin enforced at field or validation-rule level, because
  Web-to-Case and Email-to-Case create Cases through the API, not through a layout." This is the
  reason both rules exist at all rather than a Layout Required checkbox, and it is the `source`
  cell for both `REQ-030` and `REQ-031` — the same single-clarification-id convention every other
  row in this file follows, with the field each rule targets (`Priority`/`Origin`) split into two
  requirements because they answer two different downstream needs.
- **Q24, answered, cited in prose on `REQ-031` only** — "Email-to-Case and Web-to-Case invoke [the
  assignment rule] by default; manual UI creation ... needs the checkbox defaulted on." Assignment
  rules read `Case.Origin` to decide which channel a case arrived through
  (`Origin_Must_Be_Known.validationRule-meta.xml`'s own `errorMessage`: "Assignment ... read[s]
  Origin"), so a Case with an unknown `Origin` is a case the routing layer (`M3-S04`, not yet
  built) cannot reliably route. `REQ-031` is the first row in this file to cite Q24 outside
  `REQ-013` (`M1-S02`, the layout checkbox itself).
- **`M2-S01`, backward** — `depends_on: ["M1-S01", "M2-S01"]`. Both rules reference
  `$Permission.Bypass_Case_Intake_Validation`, built in `M2-S01` and already documented under
  `REQ-015`/`REQ-016`. That row's own forward reference ("the only consumers this permission will
  ever have") now resolves: this step is the consumer, and `decisions.md` **O-M3S01-03** records
  what does and does not close on `REQ-015`'s side of that link.
- **`M1-S02`, backward, through assumption A13** — both `errorDisplayField` values (`Priority`,
  `Origin`) must be visible on the page where the error appears, or the error surfaces at "Top of
  Page" instead. `REQ-014` (`M1-S02`) is the row that carries this requirement and assumption
  A13; its own note is now stale in one place, corrected in `decisions.md` **O-M3S01-04** rather
  than by editing `REQ-014` itself, which is not this run's row to touch.

**`REQ-030`/`REQ-031` do not reuse `REQ-014`, `REQ-015` or `REQ-016`.** `REQ-014` is the layout
*visibility* requirement A13 rests on; `REQ-015`/`REQ-016` are the bypass *grant* these two rules
consume; `REQ-030`/`REQ-031` are the two rules themselves — four different artefacts, at three
different layers of the same mechanism, minted at the layer that built each one.

## Coverage, as far as M3-S01

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M3-S01` — eight
of twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`,
`M2-S05`, `M3-S01`):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Thirty-one `REQ-XXX` ids exist and all
  thirty-one have a step.
- **Steps with no requirement:** 0 of the documented set. Both of `M3-S01`'s `ValidationRule`
  manifest members are named by a row above. `M3-S01`'s `package.xml` and `deploy-order.md` are
  workbook rows (`CWB-OTHER-017`, `-018`), not traceability rows, the same convention every prior
  step's manifest/deploy-order pair already established; `validation-bypass-note.md` is a
  workbook row (`CWB-VR-003`) for the same reason.
- **Manual tests outstanding:** 14 — the 10 already outstanding after `M2-S05`
  (`TC-M1S01-01`, `TC-M1S01-02`, `TC-M1S02-01`, `TC-M2S01-01`, `TC-M2S04-01`–`04`,
  `TC-M2S05-01`–`02`) plus this step's manual test **W01**, staged as four cases
  (`TC-M3S01-01`–`04`: the two positive per-rule proofs and the two bypass-negative proofs).
- **Orphan artefacts, build scope:** 7 at the moment of this run's linter pass, up from 2 after
  `M2-S05` — **5 of the increase belong to `M3-S02`, running concurrently with this
  documentation pass**, not to `M3-S01`: `M3-S02` (`ui`, building the intake email templates) has
  written `EmailFolder:case_intake` and two `EmailTemplate` components to `artefacts/M3-S02/`
  ahead of being `tested`/documented, so they are legitimately orphaned right now and are that
  step's own doc-keeper pass to resolve, not this run's. `M3-S01` itself adds no orphan: both
  `ValidationRule` members are byte-identical to their file stems. The two `M1-S01`
  `BusinessProcess` file-stem keys are unchanged (`decisions.md` D-M1S01-03). See "Concurrency"
  below.

## Linter result — after M3-S01

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
```
traceability.md: 31 row(s), build schema, 0 coverage gap(s), 7 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Zero errors. Of the 7 orphans, 5 are `M3-S02`'s in-flight artefacts (`EmailFolder:case_intake`
and two `EmailTemplate` components, both raw and manifest-member forms — `M3-S02` is `running`,
not yet `tested`), and 2 are the pre-existing `M1-S01` `BusinessProcess` file-stem keys
(`decisions.md` D-M1S01-03). `M3-S01` adds zero: both `ValidationRule` members resolve against
`REQ-030`/`REQ-031` above.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M3-S01 --repo-root ../../..
traceability.md: 31 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 29 warning(s)
exit 0
```

The step-scoped run's twenty-nine warnings are the twenty-nine rows belonging to every other
step whose components are not under `artefacts/M3-S01/` — scope, not a finding, the same shape
every prior step-scoped run in this file has produced. Both of `M3-S01`'s own rows resolve at
this scope.

## Concurrency — `M3-S02` was writing its own artefacts while this run documented `M3-S01`

`M3-S02` (`ui`, the intake email templates) is `running` concurrently, owned by a separate
`metadata-builder` invocation. This run touched no `M3-S02` row, no `M3-S02` artefact, and no
`M3-S02` line in `decisions.md` or `workbook/`:

1. **`traceability.md`** — re-read immediately before every write in this run. The build-scope
   linter run above picked up `M3-S02`'s new manifest members as orphans (see "Coverage" above)
   because they exist on disk, not because this run wrote anything about them. Nothing in that
   fact is this run's to resolve; `M3-S02`'s own doc-keeper pass, once it is `tested`, is where
   those rows land.
2. **`decisions.md`** — re-read immediately before this run's append (tail matched the
   `M2-S05` open-items block, with no `M3-S02` content yet). This run's six decisions and four
   open items were appended after that point.
3. **`workbook/99-other-configuration.md`** — re-read immediately before appending; the tail
   matched the `M2-S05` closing paragraph, with nothing new added since. `workbook/05-validation-rules.md`
   is a new file this run created; `M3-S02`'s own rows, when it documents, will land in
   `workbook/02-page-layouts-and-lightning-pages.md` (layouts) and wherever Step 4's map sends
   the email templates — not a file this run touched.

No row or file belonging to `M3-S02` was written by this run at any point.

## What M3-S02 rests on — Q22 for the sender identity and the loop question it opens, Q63 for the one-event-one-email discipline on both templates, Q68 for the sandbox proof gate, Q88 in prose only

Two new rows, two new requirements, minted after re-reading this file immediately before writing
(no other step is `running` concurrently — `M3-S01` documented before this run started):

- **Q22, answered** — "who sends the acknowledgement, and does that address forward back to us?"
  This is the `source` cell for `REQ-032`, and it is also this row's central unresolved fact: the
  answer states `support@acme.example` — a live routing address — itself sends the
  acknowledgement, which is the reading `sender-identity-note.md` § 2 and `decisions.md`
  **D-M3S02-04** carry forward as an M3 gate decision rather than settle.
- **Q63, answered, cited on both `REQ-032` and `REQ-033`** — "one acknowledgement per case
  creation: auto-response only, with no parallel Flow email alert on the same event." Applied to
  `REQ-032` as the reason exactly one customer-facing template exists; applied to `REQ-033` as the
  same one-event-one-email discipline carried to the internal handover notice, recorded in
  `decisions.md` **D-M3S02-03**.
- **Q68, answered, cited in prose on `REQ-032` only** — "a sandbox test with real inbound email, a
  clock test, and a loop test, before go-live." This is the detection mechanism `sender-identity-note.md`
  § 2 names as what actually stands between this build and the Q22 loop risk, and it is the gate
  `decisions.md` **D-M3S02-04** defers the sender question to rather than resolving it here.
- **Q88, answered, cited in prose on `REQ-033` only** — "Tier 1 uses Omni-Channel push, so no
  queue email; Billing wants the queue address emailed" (Tier 2 not addressed by the answer key;
  the proposed default — a shared mailbox per queue — was accepted for it). This is `M2-S04`'s
  queue-level notification control, not this step's; cited here only so a reader does not conflate
  it with `REQ-033`'s case-level handover notice — `decisions.md` **O-M3S02-04** names the
  distinction.
- **`M1-S01`, backward** — `depends_on: ["M1-S01"]`. Both templates' merge fields resolve against
  `Case` fields (`{!Case.Subject}`, `{!Case.CaseNumber}`, `{!Case.Priority}`, `{!Case.Origin}`),
  and `{!Case.Origin}`'s *values* are the `CaseOrigin` standard value set `M1-S01` built
  (`REQ-005`) — a send-time dependency, not a deploy-time one, per
  `artefacts/M3-S02/deploy-order.md` § "Needed at send time, not at deploy time".
- **`M3-S01`, sibling, not a dependency** — both steps mint requirement ids in the same
  milestone; `REQ-032`/`REQ-033` do not reuse `REQ-030`/`REQ-031`, which are the two `Priority`/`Origin`
  validation rules, a different mechanism entirely.
- **`M3-S04`, forward reference** — the step that actually writes `senderEmail`,
  `<template>case_intake/Case_Acknowledgement</template>` and
  `<assignedToTemplate>case_intake/Case_Escalated_To_Tier2</assignedToTemplate>` (the last on
  `M4-S04`). `decisions.md` **D-M3S02-04** binds `M3-S04` not to pre-empt the Q22-vs-answers-key
  sender decision on its own.

**`REQ-032`/`REQ-033` do not reuse any existing id.** No prior row names an email template, a
customer acknowledgement, or a Tier 2 handover notice — the closest neighbours, `REQ-023`/`REQ-027`
(Tier 2's *access* to escalated cases) and `REQ-029` (Tier 2's *sharing* grant), are about who can
open the case, not about the notice that tells them one landed.

## Coverage, as far as M3-S02

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M3-S02` — nine
of twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`,
`M2-S05`, `M3-S01`, `M3-S02`):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Thirty-three `REQ-XXX` ids exist and all
  thirty-three have a step.
- **Steps with no requirement:** 0 of the documented set. All three of `M3-S02`'s manifest
  members are named by `REQ-032` or `REQ-033` above. `M3-S02`'s `package.xml` and
  `deploy-order.md` are workbook rows (`CWB-OTHER-019`, `-020`), not traceability rows, the same
  convention every prior step's manifest/deploy-order pair already established;
  `sender-identity-note.md` is a workbook row (`CWB-LAYOUT-006`) for the same reason.
- **Manual tests outstanding:** 15 — the 14 already outstanding after `M3-S01`
  (`TC-M1S01-01`, `TC-M1S01-02`, `TC-M1S02-01`, `TC-M2S01-01`, `TC-M2S04-01`–`04`,
  `TC-M2S05-01`–`02`, `TC-M3S01-01`–`04`) plus this step's manual test **B06**, staged as two
  cases (`TC-M3S02-01`–`02`: the positive sender-facts proof and the negative
  no-hardcoded-address proof). `REQ-033` carries no manual test and adds none to this count.
- **Orphan artefacts, build scope:** 4 at the moment of this run's linter pass, down from 7 after
  `M3-S01` — the 5 `M3-S02` components that were legitimately orphaned while the step was
  `running`/`tested` are now covered by `REQ-032`/`REQ-033`, **except two**, which stay orphaned
  for a reason internal to the checker rather than to this row: `check_rtm.py`'s file-to-component
  deriver keys an `.email` file as `EmailTemplate:<file stem>` (script `SUFFIX_TYPE`), with no
  folder-qualification logic for `EmailFolder`-nested templates the way `OBJECT_CHILD_DIR` folds a
  `Case/fields/` file into `CustomField:Case.<stem>` for a `CustomObject` child. So it derives
  `EmailTemplate:Case_Acknowledgement` and `EmailTemplate:Case_Escalated_To_Tier2` from the two
  `.email` files, while this file's rows correctly name the deployable, folder-qualified members
  `EmailTemplate:case_intake/Case_Acknowledgement` and `EmailTemplate:case_intake/Case_Escalated_To_Tier2`
  (`artefacts/M3-S02/package.xml`; `artefacts/M3-S02/deploy-order.md` § "`package.xml` member
  forms"). The two forms do not string-match, so the checker reports two orphans that are not
  real coverage gaps — recorded as a skill-depth signal in `decisions.md` **O-M3S02-05**, not
  fixed by renaming the row to the checker's cruder key, which would make the traceability row
  wrong to make the linter quiet. The two remaining orphans are the pre-existing `M1-S01`
  `BusinessProcess` file-stem keys, unchanged (`decisions.md` D-M1S01-03).

## Linter result — after M3-S02

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root ../../..
traceability.md: 33 row(s), build schema, 0 coverage gap(s), 4 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Zero errors. Of the 4 orphans, 2 are the `check_rtm.py` component-key mismatch on
folder-qualified `EmailTemplate` naming described above (`decisions.md` **O-M3S02-05**), and 2 are
the pre-existing `M1-S01` `BusinessProcess` file-stem keys (`decisions.md` D-M1S01-03). `M3-S02`
adds zero real orphans: both manifest members resolve against `REQ-032`/`REQ-033` above under
their correct, folder-qualified names.

```
check_rtm.py --file traceability.md --manifest-dir artefacts/M3-S02 --repo-root ../../..
traceability.md: 33 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 31 warning(s)
exit 0
```

The step-scoped run's thirty-one warnings are the thirty-one rows belonging to every other step
whose components are not under `artefacts/M3-S02/` — scope, not a finding, the same shape every
prior step-scoped run in this file has produced. Both of `M3-S02`'s own rows resolve at this
scope; the 2 orphans at this scope are the same `check_rtm.py` key-derivation mismatch named
above, not a real gap specific to this narrower scope.

## Linter result — after M3-S04

```
check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root <repo root>
WARN: orphan artefacts: 2 component(s) in the manifest are named by no requirement — see the orphan report
traceability.md: 37 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 1 warning(s)
exit 0
```

Zero errors, zero coverage gaps: `REQ-036` and `REQ-037` above both carry an artefact and a test,
and every other row is unchanged. The 2 orphans are `AssignmentRule:Case.Case_Intake_Routing` and
`AutoResponseRule:Case.Case_Acknowledgement` — a **new** kind of key-derivation mismatch, distinct
from `M3-S02`'s (`decisions.md` **O-M3S02-05**): `check_rtm.py`'s `RULE_CONTAINERS` map derives a
second, singular, rule-named key by reading inside `AssignmentRules`/`AutoResponseRules` files, in
addition to the container-level key (`AssignmentRules:Case`, `AutoResponseRules:Case`) that
`package.xml` actually declares and that `REQ-036`/`REQ-037` name, matching `package.xml` and
`workbook/06-automation.md` `CWB-AUT-010`/`-011`. The two keys carry different evidencing paths
(`package.xml` versus the rule file itself), so naming the deployable member — the form every
other row in this build uses — cannot also satisfy the derived sub-key. Recorded as a skill-depth
signal, not fixed by renaming the row to the checker's finer-grained key: `decisions.md`
**O-M3S04-03**.

## What M4-S01 rests on — Q39 for the calendar list, Q90 for the maintenance runbook, both new requirements

Two new rows, two new requirements, minted after re-reading this file immediately before writing:

- **Q39, answered** — "two regional calendars plus a 24/7 exception … clocks pause on weekends and
  regional holidays for both; Severity 1 is 24/7 and never pauses." This is the `source` cell for
  `REQ-038` and the reason three `businessHours` entries exist in one file rather than one calendar
  with conditional hours.
- **Q38, answered, cited in prose on `REQ-038` only** — "Premier accounts get a first response
  within 4 business hours; standard accounts within 1 business day … Severity 1 outages are 24/7
  calendar time." This is *why* business time is needed at all, not which calendars exist — `M4-S02`
  (entitlement processes, `pending`) is where the promise itself is configured; this step builds only
  the clocks it reads.
- **Q40, answered, cited in prose on `REQ-038` only** — "from the account's `Region__c`; unknown
  accounts default to US." Grounds `<default>true</default>` on `US Support` and is the reason
  `M4-S03`'s not-yet-built Flow can resolve a region to a calendar name at all.
- **Q90, answered** — "a named owner in Service Operations, with a yearly holiday deploy booked …
  each Q4." This is the `source` cell for `REQ-039`, a wholly separate deliverable
  (`holiday-maintenance-runbook.md`) from `REQ-038`'s settings file, minted as its own requirement
  because it is its own declared `outputs[]` path with no deployable metadata component behind it —
  `setup-only:`, the same convention `REQ-025` already established for
  `queue-retirement-runbook.md`.
- **`M1-S01`, backward** — `REQ-007`/`REQ-008`/`REQ-009` (Q38/Q40, `Severity__c`, `Region__c`,
  `Support_Tier__c`) are the fields this step's calendars and holidays are consumed against by
  later steps; `REQ-038`/`REQ-039` do not reuse those ids because they name a different artefact
  layer — the calendars themselves, not the fields that will select one.

**`REQ-038`/`REQ-039` do not reuse `REQ-007`, `REQ-008` or `REQ-009`.** Those rows are the Case/Account
*fields* the SLA promise depends on, minted at `M1-S01`; `REQ-038`/`REQ-039` are the *calendars and
their maintenance process*, minted at the step that actually builds them — two different artefacts at
two different layers of the same requirement, the same reasoning `M3-S01`'s note gives for not reusing
`REQ-014`/`REQ-015`/`REQ-016`.

## Coverage, as far as M4-S01

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M4-S01` — thirteen
of twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`…`M2-S05`, `M3-S01`…`M3-S04`, `M4-S01`):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Thirty-nine `REQ-XXX` ids exist and all
  thirty-nine have a step.
- **Steps with no requirement:** 0 of the documented set. `M4-S01`'s one `Settings` manifest member
  is named by `REQ-038` above. `M4-S01`'s `package.xml` and `deploy-order.md` are workbook rows
  (`CWB-OTHER-025`, `-026`), not traceability rows, the same convention every prior step's
  manifest/deploy-order pair has established since `M2-S01`.
- **Manual tests outstanding:** 11 — the 10 already outstanding after `M3-S04`
  (`TC-M1S01-01`, `TC-M1S01-02`, `TC-M1S02-01`, `TC-M2S01-01`, plus the M2/M3 manual tests carried
  forward in each step's own row) plus this step's one manual test, **already ticked** —
  `M4-S01-T4` PASSED (`tests/M4-S01/results.json` `skipped_manual[0]`, confirmed true on disk by
  `step-tester`), deferred to the milestone gate for sign-off rather than outstanding for content.
  Counted here because the M4 gate has not yet run, not because the artefact is in doubt.
- **Orphan artefacts, build scope:** 3, all new at this run and all belonging to `M4-S01` — the
  `SETTINGS_ENTRIES` per-calendar key mismatch this run's linter pass surfaces (`decisions.md`
  **O-M4S01-03**). The two pre-existing `M1-S01` `BusinessProcess` file-stem keys (`decisions.md`
  D-M1S01-03) do not appear in this run's orphan report — a fact noted here rather than
  investigated further, because closing or reopening that entry is not this run's row to touch.

## Linter result — after M4-S01

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
WARN: orphan artefacts: 3 component(s) in the manifest are named by no requirement — see the orphan report
traceability.md: 39 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
```

Zero errors, zero coverage gaps: `REQ-038` and `REQ-039` above both carry an artefact and a test, and
every other row is unchanged. The 3 orphans are `BusinessHoursEntry:US Support`,
`BusinessHoursEntry:EMEA Support` and `BusinessHoursEntry:Severity 1 24x7`, all evidenced by
`artefacts/M4-S01/settings/BusinessHours.settings-meta.xml` — a **new** kind of key-derivation
mismatch, the third of its shape in this build (`decisions.md` **O-M3S02-05**, **O-M3S04-03**): the
`SETTINGS_ENTRIES` deriver reads a per-calendar key from inside the settings file, in addition to the
container-level key (`Settings:BusinessHours`) that `package.xml` actually declares and that
`REQ-038` names, matching `package.xml` and `workbook/06-automation.md` `CWB-AUT-013`. Recorded as a
skill-depth signal, not fixed by renaming the row to the checker's finer-grained key: `decisions.md`
**O-M4S01-03**.

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts/M4-S01 --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
WARN: orphan artefacts: 3 component(s) in the manifest are named by no requirement — see the orphan report
traceability.md: 39 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 37 warning(s)
```

The step-scoped run's thirty-seven warnings are the thirty-seven rows belonging to every other step
whose components are not under `artefacts/M4-S01/`, plus the same 3-orphan finding as the build-wide
run (`SETTINGS_ENTRIES` does not depend on scope). Both of `M4-S01`'s own rows resolve at this scope:
`REQ-038`'s `Settings:BusinessHours` and `REQ-039`'s `setup-only:` marker both draw no unresolved-artefact
warning of their own.

## What M4-S02 rests on — Q38 for the two SLA targets, Q53 for the shared milestone identity, D10 for completion — three new requirements

Three new rows, three new requirements, minted after re-reading this file immediately before
writing, one per manifest member the step's `package.xml` declares:

- **Q38, answered, split across two rows** — "Premier accounts get a first response within 4
  business hours, standard accounts within 1 business day." `REQ-040` (Premier,
  `minutesToComplete` 240 — exact, `4 × 60`) and `REQ-041` (Standard, `minutesToComplete` 720 —
  **derived**, not answered, `decisions.md` **D-M4S02-02**) are two rows rather than one for the
  same reason `REQ-018`/`REQ-019`/`REQ-020` mint one id per `PermissionSet` member even though all
  three trace to `Q13`: `check_rtm.py`'s `resolve_artefact()` matches one `EntitlementProcess`
  member per row, and these are two separate manifest members.
- **Q51, answered, cited in prose only** — "the Case's calendar is the authority … set the process
  and milestone calendars to match it explicitly." Grounds `<businessHours>US Support</businessHours>`
  on both `REQ-040`/`REQ-041`'s files and on `REQ-042`'s milestone override, and is also why it
  cannot be fully honoured — `decisions.md` **O-M4S02-02** records the EMEA-calendar divergence
  this creates against `M4-S04`'s escalation timer.
- **Q53, answered** — one shared milestone type serves both tiers, timing lives on the two
  processes. This is the `source` cell for `REQ-042`, the `MilestoneType:First Response` component
  both `EntitlementProcess` files reference by `milestoneName` — its own manifest member and its
  own artefact layer, not a duplicate of `REQ-040`/`REQ-041`.
- **D10, cited on `REQ-042` only** — the plan decision that the First Response milestone is
  completed by `M4-S05`'s after-update Apex trigger, not by entitlement-process completion
  criteria (no such element exists in the cited skill's metadata reference) and not by a Flow (the
  skill's Flow path wraps the same Apex). `milestone-completion-decision.md` is this row's second
  artefact — the on-disk record of that decision, and the confirmation the checker's surviving INFO
  `W4` note asks for.
- **`M1-S01`, backward** — `REQ-007`/`REQ-008`/`REQ-009` (Q38/Q40, `Severity__c`, `Region__c`,
  `Support_Tier__c`) are the Case/Account fields this step's processes are selected against;
  `REQ-038` (`M4-S01`) is the calendar layer these processes read by name. None are reused here for
  the same layering reason `M4-S01`'s own note gives against reusing `REQ-007`–`REQ-009`: each
  layer is its own artefact, minted at the step that actually builds it.

**A checker-policy block was closed at the skill, not the artefact, before this step reached
`built`.** The declared checker rejected both entitlement processes on two `W4` findings (missing
`<timeTriggers>`/`<successActions>`) that this step's own inputs could not clear without inventing
a `WorkflowAlert` no clarification names. Commit `a18f9164d` (`admin/entitlements-and-milestones`
v1.1.2) moved that finding from WARN to INFO on documented grounds, and the re-run — against the
byte-identical file — exited 0. `decisions.md` **D-M4S02-01** is the flywheel record, the same
shape as `D-M4S01-01`. Every field in the three rows above traces to the plan, the envelope, or the
test results from that closed run — nothing here restates the narrative of the block itself.

## Coverage, as far as M4-S02

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M4-S02` —
fourteen of twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`…`M2-S05`, `M3-S01`…`M3-S04`,
`M4-S01`, `M4-S02`):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Forty-two `REQ-XXX` ids exist and all
  forty-two have a step.
- **Steps with no requirement:** 0 of the documented set. `M4-S02`'s three manifest members are
  named by `REQ-040`/`REQ-041`/`REQ-042` above. `M4-S02`'s `package.xml` and `deploy-order.md` are
  workbook rows (`CWB-OTHER-027`, `-028`), not traceability rows, the same convention every prior
  step's manifest/deploy-order pair has established since `M2-S01`.
- **Manual tests outstanding:** 12 — the 11 already outstanding after `M4-S01` plus this step's one
  manual test, **already ticked** — `M4-S02-T4` PASSED (`tests/M4-S02/results.json`
  `skipped_manual[0]`, confirmed true on disk by `step-tester`), deferred to the milestone gate for
  sign-off rather than outstanding for content. Counted here because the M4 gate has not yet run,
  not because the artefact is in doubt. Note the asymmetry `REQ-041`'s row names: `M4-S02-T4`'s
  wording pins Premier's 240 but names no value for Standard, so the derived 720 is untested by
  either half.
- **Orphan artefacts, build scope:** 2, both belonging to `M4-S04` (`EscalationRule:Case.Case_SLA_
  Escalation`, `EscalationRules:Case`) — down from 5 before this run, the other 3 being exactly
  this step's own manifest members, now named by `REQ-040`/`REQ-041`/`REQ-042`. `M4-S04`'s two
  orphans are outside this step's scope and are left exactly as found, for that step's own
  documentation pass to close.

## Linter result — after M4-S02

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
WARN: orphan artefacts: 2 component(s) in the manifest are named by no requirement — see the orphan report
traceability.md: 42 row(s), build schema, 0 coverage gap(s), 2 orphan(s), 0 error(s), 1 warning(s)
```

Zero errors, zero coverage gaps: `REQ-040`, `REQ-041` and `REQ-042` above all carry an artefact and
a test, and every other row is unchanged. The 2 remaining orphans are `EscalationRule:Case.Case_SLA_
Escalation` and `EscalationRules:Case`, both evidenced by `M4-S04/`'s artefacts — pre-existing,
outside this step's scope, and unchanged by this run; they belong to `M4-S04`'s own documentation
pass, not this one.

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts/M4-S02 --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 42 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 37 warning(s)
```

The step-scoped run's thirty-seven warnings are the thirty-seven rows belonging to every other step
whose components are not under `artefacts/M4-S02/` (unresolved-at-this-scope, not a defect); 0
orphans at this scope because `M4-S04`'s two components are simply absent from this narrower tree,
not resolved. All three of `M4-S02`'s own rows resolve at this scope with no warning of their own.

## Coverage, as far as M4-S04

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M4-S04` —
fifteen of twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`…`M2-S05`, `M3-S01`…`M3-S04`,
`M4-S01`, `M4-S02`, `M4-S04`):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Forty-three `REQ-XXX` ids exist and all
  forty-three have a step.
- **Steps with no requirement:** 0 of the documented set. `M4-S04`'s one manifest member
  (`EscalationRules:Case`) is named by `REQ-043` above. `M4-S04`'s `package.xml` and
  `deploy-order.md` are workbook rows (`CWB-OTHER-029`, `-030`), not traceability rows, the same
  convention every prior step's manifest/deploy-order pair has established since `M2-S01`.
- **Manual tests outstanding:** 14 — the 12 already outstanding after `M4-S02` plus this step's two
  manual tests, neither ticked: `M4-S04-T4` (activation sign-off) and `M4-S04-T5` (the
  480-minute / `businessHoursSource` / queue-developer-name assertion), both deferred to the M4
  gate. Unlike `M4-S02`'s `M4-S02-T4` (confirmed true on disk and only awaiting sign-off), these
  two genuinely cannot be ticked before activation — the first names an event (the first hour's
  escalation count) that has not happened, and the second's calendar half needs `M4-S01`'s
  settings file in view, which only the milestone-scoped run provides.
- **Orphan artefacts, build scope:** 0 — down from 2 before this run. `EscalationRules:Case` (this
  step's row, above) and, via the same `RULE_CONTAINERS` coverage that already closed
  `O-M3S04-03`/`O-M4S01-03`, the per-rule key `EscalationRule:Case.Case_SLA_Escalation` the checker
  derives from inside the same file are both now referenced. No skill-depth signal to record for
  this step — the container-coverage fix landed (commits `ef8e10141`, `cf9dde917`) before this
  documentation pass, so naming the deployable container was sufficient on the first row, unlike
  the two- and three-orphan cases `O-M3S04-03`/`O-M4S01-03` recorded before that fix existed.

## Linter result — after M4-S04

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 43 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 0 warning(s)
```

Zero errors, zero coverage gaps, **zero orphans and zero warnings** — the first fully clean build-
scope run recorded in this file. `REQ-043` above carries an artefact and a test, and every other
row is unchanged. The 2 orphans this run inherited from `M4-S02`'s documentation pass
(`EscalationRule:Case.Case_SLA_Escalation`, `EscalationRules:Case`) are both resolved by the one
row this step adds — naming the container form (`EscalationRules:Case`, matching `package.xml`
and `workbook/06-automation.md` `CWB-AUT-019`) is sufficient under `check_rtm.py`'s
`RULE_CONTAINERS` coverage, the same mechanism that already closed the `AssignmentRules`/
`AutoResponseRules` case (`decisions.md` **O-M3S04-03**) and, generalised, the `Settings:
BusinessHours` case (`decisions.md` **O-M4S01-03**). No new skill-depth signal is recorded here:
the remedy those two entries asked for was already shipped (commit `ef8e10141` for rule
containers, `cf9dde917` generalising it to settings entries), so this step is the first to benefit
from the fix rather than the one that needed it written down.

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts/M4-S04 --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 43 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 34 warning(s)
```

The step-scoped run's thirty-four warnings are the thirty-four rows belonging to every other step
whose components are not under `artefacts/M4-S04/` (unresolved-at-this-scope, not a defect,
identified individually in the command's own output — e.g. `REQ-001`'s `RecordType:Case.Support`,
`REQ-038`'s `Settings:BusinessHours`); 0 orphans at this scope because there is nothing else under
this narrower tree to be orphaned. `M4-S04`'s own row (`REQ-043`) resolves at this scope with no
warning of its own, and its `EscalationRules:Case` container key satisfies the per-rule child key
this same narrower run also derives.

## What M4-S05 rests on — Q50 for the completion signal (honoured only in part), D10 for the mechanism, one new requirement

One new row, minted after re-reading this file immediately before writing, covering all four of
this step's `outputs[]` (the trigger, the service, the test class and the F-37 rebuild's
`TestDataFactory` copy) as one requirement rather than four, per `agents/build-doc-
keeper/AGENT.md` Step 7's "one row per requirement, never one per artefact":

- **D10, the mechanism** — an after-update Apex trigger on `Case` stamps
  `CaseMilestone.CompletionDate`; not entitlement-process completion criteria (no such element is
  documented on the metadata type) and not a Flow (the cited skill's Flow path wraps the same
  Apex). `REQ-042` (`M4-S02`) already cites `D10` for the milestone identity this mechanism
  completes; `REQ-044` cites it again for the mechanism itself, the same shared-decision-two-rows
  shape `REQ-040`/`REQ-041` already carry for `Q38`.
- **Q50, answered, honoured only in part** — the recorded answer names the first outbound
  `EmailMessage` as the completion signal. This step implements a narrower, Case-only proxy — the
  Case leaving `Status = New` — because the literal signal is a different artefact (an
  `EmailMessage` trigger) this step's `outputs[]` does not declare. `decisions.md` **D-M4S05-02**
  is the full record; the `source` cell above cites `Q50` rather than `D10` because the gap between
  what was asked and what was built belongs to the requirement, not the mechanism.
- **Q16, cited in prose only** — the first-minute-of-a-case answer (owner, acknowledgement,
  calendar, priority) is an **auto**-acknowledgement, not an agent's first response, and is what
  rules out treating `M3-S04`'s auto-response rule as satisfying this requirement on its own.
- **Q53, cited in prose only** — the shared milestone identity `REQ-042` already establishes;
  `REQ-044` completes it rather than duplicating it.
- **F-37, a rebuild, not a new requirement.** The org's rejection of the unshipped
  `TestDataFactory` reference (`decisions.md` **D-M4S05-01**) changed this step's `outputs[]` from
  six paths to eight; it did not change what requirement the step serves, so no new `REQ-XXX` id
  was minted for the factory class — it is `REQ-044`'s fourth `artefact_paths` entry, the same
  bundled-support-artefact treatment `REQ-044`'s own row gives the test class.
- **Backward, not reused:** `REQ-007`/`REQ-009` (`Severity__c`, `Support_Tier__c`, both `M1-S01`)
  and `REQ-040`–`REQ-042` (`M4-S02`) are the fields and the entitlement layer this step's test data
  and completion logic read; none are reused here for the same layering reason every prior step's
  "rests on" section gives — each layer is its own artefact, minted at the step that actually
  builds it.

**A real org caught what no local check could.** The first build passed all four declared
acceptance tests and `check-outputs` cleanly, then failed `reports/MOCK-DEPLOY-M4.md` run 2 on a
symbol no acceptance-test type in `standards/build-orchestration.md` § 5 resolves across files.
`decisions.md` **D-M4S05-01** records the closure; `D-M4S05-03`–`D-M4S05-05` record three further
items carried to the M4 gate rather than fixed here. Every field in `REQ-044`'s row traces to the
plan, the two builder envelopes, the two step-tester envelopes, or `reports/MOCK-DEPLOY-M4.md` —
nothing here restates the narrative of the rebuild itself.

## Coverage, as far as M4-S05

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M4-S05` —
sixteen of twenty-two steps documented (`M1-S01`, `M1-S02`, `M2-S01`…`M2-S05`, `M3-S01`…`M3-S04`,
`M4-S01`, `M4-S02`, `M4-S04`, `M4-S05`; `M4-S03` is `tested`, not yet `documented`, under a
concurrent doc-keeper pass this run does not touch):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Forty-four `REQ-XXX` ids exist and all
  forty-four have a step.
- **Steps with no requirement:** 0 of the documented set. `M4-S05`'s four `outputs[]` paths are
  named by `REQ-044` above. `M4-S05` declares no `package.xml` at all — the Apex exception,
  `standards/build-orchestration.md` § 5 — so unlike every prior step there is no manifest workbook
  row to pair with the deploy-order one; only `workbook/99-other-configuration.md`
  `CWB-OTHER-031` (the deploy-order note) is not a traceability row, the same convention every
  prior step's non-manifest artefacts have followed.
- **Manual tests outstanding:** 15 — the 14 already outstanding after `M4-S04` plus this step's one
  manual test, not ticked: given no offline Apex compiler exists in the `sf` CLI, when the step is
  accepted, the reviewer confirms every non-platform identifier is quoted from the cited skill or
  template and that `CaseMilestoneServiceTest` asserts `CompletionDate` non-null after the trigger
  runs. Both halves are true on disk (`tests/M4-S05/results.json`
  `skipped_manual[0]`; every identifier in `deploy-order.md` traces to the skill, the template, or
  a plan-cited decision) but deferred to the M4 gate rather than ticked here, the same restraint
  every manual test in this build has been given.
- **Orphan artefacts, build scope:** 5, up from 0 after `M4-S04`'s clean run — 3 belong to this
  step (`ApexClass:CaseMilestoneService`, `ApexClass:CaseMilestoneServiceTest`,
  `ApexClass:TestDataFactory`), and 2 belong to `M4-S03` (`Flow:Case_BeforeSave_
  StampEntitlementAndCalendar`, `FlowTest:Case_BeforeSave_StampEntitlementAndCalendar_Test`),
  reported by `/tmp/rtm-report/rtm-orphan-report.md`'s disposition column as `REVIEW` on all five.
  **This step's own three are not a gap — they are a known shape of `check_rtm.py`'s
  `resolve_artefact()`, which matches one component per row's single-valued `artefact` cell.**
  `REQ-044`'s `artefact` column names `ApexTrigger:CaseMilestoneTrigger` only, per Step 7's own
  one-row-per-requirement rule; the other three components are present in `artefact_paths`
  (multi-valued) and in `workbook/06-automation.md` (`CWB-AUT-023`–`025`, each an addressable row
  of its own), but `artefact_paths` is not what the orphan check resolves against — the same
  single-column-vs-multi-value gap `REQ-013`'s own note already names for a layout pair. Documented
  as a dependency (the RTM skill's own third disposition option) rather than adopted (a fifth
  `REQ-XXX` id per Apex file, which Step 7 forbids) or removed (the components are real and
  deployed). `M4-S03`'s two orphans are outside this step's scope and are left exactly as found,
  for that step's own concurrent documentation pass to close — the same "left exactly as found"
  treatment `M4-S02`'s Coverage section gave `M4-S04`'s orphans before `M4-S04` was documented.

## Linter result — after M4-S05

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
WARN: orphan artefacts: 5 component(s) in the manifest are named by no requirement — see the orphan report
traceability.md: 44 row(s), build schema, 0 coverage gap(s), 5 orphan(s), 0 error(s), 1 warning(s)
```

Zero errors, zero coverage gaps: `REQ-044` above carries an artefact and a test, and every other
row is unchanged. The 5 orphans are exactly the ones named in "Coverage, as far as M4-S05" above —
3 this step's own (`ApexClass:CaseMilestoneService`, `ApexClass:CaseMilestoneServiceTest`,
`ApexClass:TestDataFactory`, all `REVIEW`-dispositioned and documented as dependencies rather than
adopted or removed) and 2 `M4-S03`'s (`Flow:Case_BeforeSave_StampEntitlementAndCalendar`,
`FlowTest:Case_BeforeSave_StampEntitlementAndCalendar_Test`), pre-existing, outside this step's
scope, and unchanged by this run — reported honestly rather than left for a reader to notice: an
Apex file with no `package.xml` of its own (the Apex exception) is not automatically indexed by
this checker's manifest walk in the same shape a metadata-type step's members are, and whether a
future `check_rtm.py` revision resolves multi-valued `artefact_paths` the same way it resolves
`artefact` is exactly the kind of skill-depth signal `decisions.md` **O-M3S01-02**/**O-M3S02-05**
already record for other checker gaps, though no new decision entry is minted here for it.

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts/M4-S05 --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 44 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 42 warning(s)
```

The step-scoped run's forty-one artefact warnings are the forty-one rows belonging to every other
step whose components are not under `artefacts/M4-S05/` (unresolved-at-this-scope, not a defect,
identified individually in the command's own output — e.g. `REQ-001`'s `RecordType:Case.Support`,
`REQ-043`'s `EscalationRules:Case`), plus one orphan-summary warning, forty-two in total. The 3
orphans at this scope are this step's own three unnamed-in-`artefact` components, the same three
named at build scope above — nothing else under this narrower tree resolves or fails to resolve,
because nothing else is present in it. `M4-S05`'s own row (`REQ-044`) resolves at this scope with
no warning of its own.

## Linter result — after M4-S03

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
WARN: orphan artefacts: 3 component(s) in the manifest are named by no requirement — see the orphan report
traceability.md: 47 row(s), build schema, 0 coverage gap(s), 3 orphan(s), 0 error(s), 1 warning(s)
```

Zero errors, zero coverage gaps. This step's own three manifest members — `Flow:Case_
BeforeSave_StampEntitlementAndCalendar`, `FlowTest:Case_BeforeSave_StampEntitlementAndCalendar_
Test` and `Settings:Flow` — are named on `REQ-045`/`REQ-046`/`REQ-047` respectively, one row per
member (the same `resolve_artefact()`-driven split `REQ-040`/`REQ-041`/`REQ-042` already use for
`M4-S02`'s three components), and resolve cleanly. The **2** orphans `M4-S05`'s documentation pass
inherited from this step (`Flow:Case_BeforeSave_StampEntitlementAndCalendar`, `FlowTest:Case_
BeforeSave_StampEntitlementAndCalendar_Test` — see "Linter result — after M4-S05" above) are both
now resolved by these rows, exactly as that entry anticipated ("pre-existing, outside this step's
scope"). The **3** orphans that remain are all `M4-S05`'s own Apex classes (`ApexClass:
CaseMilestoneService`, `ApexClass:CaseMilestoneServiceTest`, `ApexClass:TestDataFactory`,
all `REVIEW`-dispositioned in `rtm-orphan-report.md`), unrelated to this step and unchanged by
this run.

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts/M4-S03 --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 47 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 42 warning(s)
```

The step-scoped run's forty-two warnings are the forty-two rows belonging to every other step whose
components are not under `artefacts/M4-S03/` (unresolved-at-this-scope, not a defect, identified
individually in the command's own output — e.g. `REQ-001`'s `RecordType:Case.Support`, `REQ-044`'s
`ApexTrigger:CaseMilestoneTrigger`); 0 orphans at this scope because nothing else under this
narrower tree is present to be orphaned. This step's own three rows (`REQ-045`, `REQ-046`,
`REQ-047`) resolve at this scope with no warning of their own — `REQ-045`'s `decision_ref` was
initially written as the multi-value `D1; D2` and the linter correctly rejected it (`decision_ref
'D1; D2' is not the build-plan shape D<n>`); it now carries `D2` alone (the flow-pattern-selector
branch this step actually implements), and `D1` (the Flow-over-Apex automation-selection branch) is
carried in the coverage table's prose instead, where it is not schema-validated.

## What M5-S01 rests on — Q31 for the two pull working surfaces, A7 for the Tier 1 interim, D4 for the mechanism, Q91 for the report, one bundled requirement

Four new rows, minted after re-reading this file immediately before writing:

- **`REQ-048`/`REQ-049`, Q31 answered.** "Billing and Tier 2 pick from a list" is one requirement
  line (`requirement.md` L12–L14) serving two teams and two queues, the same one-line-two-rows shape
  `REQ-001`/`REQ-002` already establish for the two business processes on one requirement bullet.
  `D4` (`plan.json` `decisions[]`) is cited on both — it is the decision-tree branch (`Q13`,
  `standards/decision-trees/automation-selection.md`) that resolves *how* Tier 2 and Billing reach
  their cases (queue list view, not Assignment-Rules-only or Omni-Channel), the same mechanism
  `REQ-042`'s two rows already share `D10` for.
- **`REQ-050`, a harder case: cited against the requirement it does NOT satisfy.** `Q31`'s answer
  is that Tier 1's work is *pushed*; `M3-S05`, the step that would configure that push, is
  `blocked` on `Q32`–`Q35`. `M5-S01` still builds a Tier 1 queue list view, under assumption `A7`,
  so Tier 1 has some way to work its queue in the interim. This is not `REQ-048`/`REQ-049` restated
  a third time — it is a distinct, assumption-grounded need — so it gets its own id rather than
  being folded into either. `decisions.md` **D-M5S01-03** is the full record of why this does not
  contradict `D4`.
- **`Q91`, informational, answered — one new requirement, two files.** "A saved report on
  escalated, still-open Cases, reviewed weekly by the Tier 2 lead" has no `requirement.md` line of
  its own — like `REQ-042`/`REQ-044`, it is a need the plan derived from a skill's own monitoring
  guidance (`admin/escalation-rules`), not a bullet in the intake document. `REQ-051` bundles the
  report and its folder as one mechanism, the same one-mechanism treatment `REQ-032` gives the
  acknowledgement template and its `EmailFolder`.
- **Backward, not reused:** `REQ-021`–`REQ-025` (`M2-S04`'s queues and groups) are what every
  `<queue>`/`<sharedTo>` element in this step's three list views names by developer name; none are
  reused here for the same layering reason every prior step's "rests on" section gives — the queue
  layer is its own artefact, minted at the step that actually built it. `REQ-043` (`M4-S04`'s
  escalation rule) is the mechanism this step's report exists to monitor, cited in prose only.

**A real org caught what no local check could, twice.** The first build (`09-34-00Z`) passed both
declared checkers and `check-outputs` cleanly, then failed `reports/MOCK-DEPLOY-M5.md` run 1 on a
field neither declared checker asserts anything about (F-49), and the operator's follow-on probes
then disproved two values straight out of the cited skill's own worked example (F-50).
`decisions.md` **D-M5S01-01** records the closure — in the artefact, not yet at the skill;
**D-M5S01-02** records F-51, the one fact the org could not settle by probing, as a post-deploy
runbook step rather than a rebuild target; **O-M5S01-01** records that both declared checkers score
the rejected file and the fixed file identically; **O-M5S01-02** downgrades the folder-filename
finding from a possible deploy defect to a checker-recognition gap, now that run 1 has validated
the folder at its declared filename. Every field in `REQ-048`–`REQ-051`'s rows traces to the plan,
the two builder envelopes, the two step-tester envelopes, or `reports/MOCK-DEPLOY-M5.md` — nothing
here restates the narrative of the rebuild itself.

## Coverage, as far as M5-S01

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M5-S01` —
seventeen of twenty-three documented steps (every M1–M4 step through `M4-S03`, plus `M5-S01`):

- **Requirements with no step:** not yet computable, same reasoning as every prior "Coverage"
  section — ids are minted when a step delivers them. Fifty-one `REQ-XXX` ids exist and all
  fifty-one have a step.
- **Steps with no requirement:** 0 of the documented set. `M5-S01`'s six `outputs[]` paths (three
  list views, the report, the folder, `package.xml`) are named across `REQ-048`–`REQ-051` above
  and `workbook/99-other-configuration.md` `CWB-OTHER-034` (the manifest); the deploy-order note
  is `CWB-OTHER-035`, not a traceability row, the same convention every prior step's non-manifest
  artefact has followed.
- **Manual tests outstanding:** 18 — the 15 already outstanding after `M4-S05` plus this step's one
  manual test (`M5-S01-T5`), which covers all three list views' queue-name existence and the Tier 1
  interim-surface disposition in one Given/When/Then; not ticked, deferred to the M5 gate. No manual
  test targets `REQ-051` (the report) directly.
- **Orphan artefacts, build scope:** 0. `check_rtm.py` reported 0 orphans both before and after this
  step's rows were added — every manifest member in `artefacts/` currently resolves to some row's
  `artefact` cell or is bundled into a row's `artefact_paths` and not independently orphaned; the
  report's folder is the one component in this step that follows the bundled-not-orphaned shape
  (inside `REQ-051`, per the same treatment `REQ-032` gives `EmailFolder:case_intake`).

## Linter result — after M5-S01

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 51 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 0 warning(s)
```

Zero errors, zero coverage gaps, zero orphans, zero warnings at build scope: `REQ-048`–`REQ-051`
above each carry an artefact and a test, every other row is unchanged, and every manifest member
under `artefacts/` resolves to some row.

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts/M5-S01 --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 51 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 111 warning(s)
```

`REQ-048`–`REQ-051` resolve their own `artefact` cell cleanly at this narrower scope, with no
"artefact not found" warning of their own — the same clean-resolution shape every prior step's own
rows get at their own step scope. The 111 warnings are two per unresolved row rather than one: each
of the other 47 rows' `artefact` column is (correctly) not found under `artefacts/M5-S01/`, **and**
this checker's `artefact_paths` existence check also fires per path, because every row's
`artefact_paths` entries are written build-root-relative (`artefacts/M4-S05/classes/...`) rather
than relative to the narrower `--manifest-dir` passed here — a path-resolution shape that applies
to every row in this file alike at any scope narrower than the full build, not something this
step's own four new rows introduced (`REQ-048`–`REQ-051`'s own `artefact_paths` entries show the
identical pattern in the raw output). Unresolved-at-this-scope, not a defect, per the same reading
every prior "Linter result" section in this file gives the narrower-scope run.

## What M5-S03 rests on — Q77 for the persona convention, Q84 for the per-channel split, Q80 for the deny-case discipline; three requirements carry no story at all

`M5-S03` is the first `docs`-type step in this build owned by a borrowed Tier-2 agent
(`story-drafter`) rather than by `metadata-builder`, and it produces one markdown document —
`artefacts/M5-S03/story-backlog.md` — carrying 11 INVEST stories across 4 epics, not a metadata
component. Seven new requirement ids are minted here (`REQ-052`–`REQ-058`), continuing from
`REQ-051`, because the testing-and-environment questions Q77–Q97 answer are their own layer of
requirement, not a restatement of `REQ-001`–`REQ-051`'s configuration requirements.

**No collision, so the ids are adopted as minted.** `story-backlog.md`'s own internal
Requirements Traceability Matrix minted `REQ-052`–`REQ-058` itself, without a build-wide owner of
the `REQ-` sequence — recorded as an ambiguous gap in the story-drafter envelope
(`envelopes/M5-S03/2026-09-12T10-25-00Z.json` → `process_observations[9]`, category `ambiguous`,
domain `traceability`) and carried into `decisions.md` **O-M5S03-01**. `REQ-051` was the highest
id in this file before this step ran, so `REQ-052`–`REQ-058` collide with nothing already on file
and are adopted here unchanged rather than re-minted — a re-map would have discarded a working,
non-colliding id space for no benefit and would have left `story-backlog.md`'s own matrix
disagreeing with this file's ids.

**Four of the seven serve a story directly; three do not, deliberately.** `REQ-052` (Q77),
`REQ-053` (Q84) and `REQ-054` (Q80) are each evidenced by the declared checker, the declared
manual test, or both, across the story set. `REQ-055` (Q78) is a named deploy prerequisite (P6)
with no dedicated test. `REQ-056` (Q96) and `REQ-057` (Q97) are UAT programme controls —
carried in the shared Background block and in `US-CASE-008`'s notes rather than as their own
story — because a story that dramatizes "confirm the PSG finished recalculating" or "the triager
decides Fail vs Blocked" is exactly the undemoable-story shape
`admin/user-story-writing-for-salesforce` LLM anti-pattern 5 warns against. `REQ-058` (Q94) has no
artefact at all: `M5-S02`, the sandbox-strategy step that would name an environment owner and
refresh approver, is `blocked` on four inputs, and no story here can name a sandbox in its stead.

**Why `Draft`, not `In Build`, for the four requirements with no test.** `REQ-055`–`REQ-058` are
not steps this plan will revisit — `M5-S03` is `documented` and no other pending step is scoped to
close any of the four — so `In Build`'s "a step remains" reading does not fit. `Draft` is the
closest enum member to "recorded, not yet actioned or testable by a plan step," and
`check_rtm.py`'s own rule treats a `Draft` row's missing artefact/test as a waived gap (WARN) once
`Draft` itself does not require a `decision_ref` (`check_rtm.py` line ~855: only `Deferred` and
`Dropped` require one). Marking these `In UAT` instead would have manufactured a coverage
appearance neither test suite provides — the choice a fabricated `test_id` would have made falsely.

**The three-way `docs` distinction for this step.** `standards/build-orchestration.md` § 4's
"docs" row names three different owners for three different documents in a design-only build:
`metadata-builder` for `package.xml`, `story-drafter` for the story backlog, `build-doc-keeper`
for the workbook/traceability/deploy-order/UAT-pack/acceptance-criteria set. `M5-S03` is the
`story-drafter` instance — it has no `package.xml` and no `deploy-order.md`, because that agent's
Output Contract names neither (§ 4 "Borrowing a roster agent" condition 2, `decisions.md`
**O-M5S03-02**) — so this run's traceability contribution is the seven rows above and nothing in
`workbook/99-other-configuration.md` beyond the single row for the story backlog itself.

## Coverage, as far as M5-S03

Full coverage counts are compiled at `M5-S04`, over every documented step. As of `M5-S03` —
eighteen of twenty-four documented steps (every M1–M4 step through `M4-S03`, plus `M5-S01` and
now `M5-S03`; `M5-S02` remains `blocked`):

- **Requirements with no step:** 0. Fifty-eight `REQ-XXX` ids now exist (`REQ-001`–`REQ-058`) and
  every one has a `step_id`, including the four (`REQ-055`–`REQ-058`) whose row carries no
  artefact or test — a `step_id` is not the same claim as delivered coverage, and the four
  `Draft` rows say so in their own `test_result` cells rather than by omission here.
- **Steps with no requirement:** 0 of the documented set. `M5-S03`'s one declared output
  (`artefacts/M5-S03/story-backlog.md`) is named across `REQ-052`–`REQ-058` above and
  `workbook/99-other-configuration.md` `CWB-OTHER-036`.
- **Manual tests outstanding:** 19 — the 18 already outstanding after `M5-S01` plus this step's
  one manual test (`M5-S03-T2`), which covers the channel/persona/deny-path clause named on
  `REQ-052`–`REQ-054`; not ticked, deferred to the M5 gate.
- **Coverage gaps (new at this step):** 4 — `REQ-055`, `REQ-056`, `REQ-057`, `REQ-058`, all
  `Draft`, all **WAIVED** rather than **BLOCKER** per `check_rtm.py`'s disposition rule (missing
  artefact and/or test while status is in `{Draft, Deferred, Dropped}` is a WARN, not an ERROR).
  None of the fifty-four prior requirements carried a coverage gap; this is the first step in the
  build to record one, and it is recorded as a gap rather than closed with an invented test.
- **Orphan artefacts, build scope:** 0 expected. `story-backlog.md` is a markdown document, not
  source-format metadata — it derives no `<types>`/`<members>` entry and defines no component
  the Metadata API could deploy, so `--manifest-dir artefacts` finds nothing under
  `artefacts/M5-S03/` for the orphan check to reconcile against any row, the same
  "docs that produces no manifest" treatment `standards/build-orchestration.md` § 4/§ 5 gives
  `M1-S01`'s and every prior step's `deploy-order.md` note, and the same reading `step-tester`
  already applied when it marked this step's own `manifest` acceptance test
  skipped-not-applicable (`tests/M5-S03/results.json`).

## Linter result — after M5-S03

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
WARN: row 56: coverage gap: REQ-055 has no test id (status 'Draft') — waived by decision NONE
WARN: row 57: coverage gap: REQ-056 has no test id (status 'Draft') — waived by decision NONE
WARN: row 58: coverage gap: REQ-057 has no test id (status 'Draft') — waived by decision NONE
WARN: row 59: coverage gap: REQ-058 has no artefact and no test id (status 'Draft') — waived by decision NONE
traceability.md: 58 row(s), build schema, 4 coverage gap(s), 0 orphan(s), 0 error(s), 4 warning(s)
```

Zero errors, zero orphans. The four `WARN`s are the four `Draft` rows named in "Coverage, as far as
M5-S03" above (`REQ-055`–`REQ-058`) — each one **WAIVED**, not **BLOCKER**, because `Draft` is a
terminal status under `check_rtm.py`'s coverage rule; "waived by decision NONE" is the checker's own
wording for a `Draft` row that carries no `decision_ref`, which is correct here — only `Deferred` and
`Dropped` require one, per the same rule that let `REQ-055`–`REQ-058` skip a `D<n>` citation that
would otherwise have to be invented. This is the first run in the build to report a non-zero
`coverage gap(s)` count; every prior step's run reported zero, because every prior row either carried
a test or was never written until it did. Reporting four rather than hiding them behind a fabricated
`test_id` or a status this step did not earn is the point of the `Draft` convention this run
introduces to the file.

## Coverage note — `M5-S05` mints no requirement; every REQ artefact is now carried by a member of `M5-S05`

`M5-S05` (`docs`, `metadata-builder`, `depends_on` `M5-S04` and `M4-S05`) is the second step in this
build's own `traceability.md` to add no new `req_id` row, the same treatment `M5-S04` received: a
build-level `package.xml` and its deploy-order note aggregate what every other step already built,
so they satisfy no requirement of their own to add here — the same "mints no requirement" reading
`workbook/99-other-configuration.md`'s `CWB-OTHER-042`/`-043` give the pair. What changed at this
step, and what the fifty-eight existing rows above do not otherwise say: every one of the fifty-four
requirements whose row names an `artefact` (`REQ-001`–`REQ-054`, excluding the four `Draft` rows
`REQ-055`–`REQ-058` that name no artefact by design) is now, for the first time, carried by a
**named member of one build-level manifest** — `artefacts/M5-S05/package.xml`, 29 types, 57
members — rather than only by its own step's manifest under `artefacts/<step-id>/package.xml`. The
two-way check `step-tester` ran over the whole `artefacts/` tree (`tests/M5-S05/manifest_check_wholetree.txt`)
confirms both directions: all 57 members resolve to a file, and all 64 deployable files (57 named
members plus 7 `-meta.xml` siblings that travel with a body file and name no member of their own)
are covered by a member — 0 missing either direction. This is not a new coverage claim this file's
own rows did not already carry (every artefact cell above already names the file the member
resolves to); it is the first point in the build where a single manifest, rather than seventeen
separate ones, can be checked against the whole tree in one pass — which is what closes **F-43**
(`decisions.md` **D-M5S05-01**) and is what `reports/MOCK-DEPLOY-M5.md` Run 3's manifest-mode dry
run validated end to end. `M3-S05` and `M5-S02` (both `blocked`) contribute no member, matching
their rows' own `artefact` cells above, which already name no component for either.

**Amended after `M5-S05`'s F-59/F-60 rebuild, 2026-09-12.** The member count above was 56 at this
note's first writing (`envelopes/M5-S05/2026-09-12T12-38-43Z.json`); the operator's `documented →
running` rebuild (`envelopes/M5-S05/2026-09-12T18-29-36Z.json`, retested at
`2026-09-12T18-36-34Z.json`) added one `ApexClass` member, `TestUserFactory`, that `M4-S05` shipped
for its F-59 test-only repair — `decisions.md` **D-M5S05-06**, which also discharges `decisions.md`
**O-M4S05-01**. No `req_id` this note already carries changes which artefact it names: `TestUserFactory`
is test-support code with no `REQ-XXX` of its own, so this amendment is a member-count and
evidence update to prose, not a new or moved table row, per `agents/build-doc-keeper/AGENT.md`
Step 8. The evidence for the fifty-four requirements' Apex members also strengthened: the org has
now actually *executed* `CaseMilestoneServiceTest` rather than only compiled it —
`reports/MOCK-DEPLOY-M5.md` run 8 (probe, source mode) passed 4/4 methods at 84.4% coverage, closing
F-59/F-60/F-61/F-62; run 9 (manifest mode, this rebuilt 57-member manifest as shipped) found 61/61
components ok with F-28 (the unverified sender address) the sole remaining error, tests not executed
because the org stops at the component stage on that error.

## Linter result — after M5-S05

```
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md \
    --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
WARN: row 56: coverage gap: REQ-055 has no test id (status 'Draft') — waived by decision NONE
WARN: row 57: coverage gap: REQ-056 has no test id (status 'Draft') — waived by decision NONE
WARN: row 58: coverage gap: REQ-057 has no test id (status 'Draft') — waived by decision NONE
WARN: row 59: coverage gap: REQ-058 has no artefact and no test id (status 'Draft') — waived by decision NONE
traceability.md: 58 row(s), build schema, 4 coverage gap(s), 0 orphan(s), 0 error(s), 4 warning(s)
```

Unchanged from the "Linter result — after `M5-S03`" run: still 58 rows, still 0 orphans, still the
same 4 `Draft`-row coverage-gap `WARN`s on `REQ-055`–`REQ-058`. `M5-S05` adds no row and closes no
`Draft`, so an identical result is the correct outcome, not a stale re-run — `--manifest-dir
artefacts` now also sees `artefacts/M5-S05/package.xml` on disk, and the orphan check still reports
zero, confirming the new build-level manifest introduces no member this file's fifty-eight rows do
not already account for. **Re-run unchanged after the F-59/F-60 rebuild** (this pass): same command,
same 58 rows / 0 orphans / 4 warnings — the rebuild changed `package.xml`'s member count, not the
requirement rows this linter checks, so an identical result is again the correct outcome.
