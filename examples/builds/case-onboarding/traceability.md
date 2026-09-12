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
| REQ-017 | Q9 | Every Case-working persona shares one baseline object/field/tab access footprint before any persona-specific grant is layered on | M2-S02 | `PermissionSet:Case_Agent_Core` | metadata-builder | — | M2-S02-T3 | checker | In UAT | `artefacts/M2-S02/permissionsets/Case_Agent_Core.permissionset-meta.xml` | pass — `check_access_model.py --manifest-dir artefacts/M2-S02` exit 0, `score 100`, `Scanned 7 access-model metadata file(s); 0 finding(s)` (this file is 1 of the 7 scanned); `check_permission_set_architecture.py --manifest-dir artefacts` exit 0, `No issues found.` (build scope, cross-referential per `standards/build-orchestration.md` § 5). Also `manifest` (part of the 4-member `PermissionSet` block, both directions consistent) and `xml` parsed. **CRUD levels were read from `requirement.md`, not from an answered clarification** — Q9 answers the object list only; `decisions.md` D-M2S02-01. No `viewAllRecords`/`modifyAllRecords`, no `userPermissions`, no `viewAllFields`: `decisions.md` D-M2S02-02, D-M2S02-03, D-M2S02-04. Composed into all three PSGs (`REQ-018`, `REQ-019`, `REQ-020`). **Re-tested after rebuild #2 (F-15), run `2026-09-12T01-26-00Z`:** `<description>` trimmed 419→192 chars for the Metadata API's 255-char ceiling; every grant-bearing element unchanged. `check_access_model.py --manifest-dir artefacts/M2-S02` exit 0 (score 100, 0 findings) and `check_permission_set_architecture.py --manifest-dir artefacts` exit 0 (build scope), both now enforcing the new PSA-DESC-01/02 / PSVP-DESC-01 length rules with no DESC finding on this file. `decisions.md` D-M2S02-07. |
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
