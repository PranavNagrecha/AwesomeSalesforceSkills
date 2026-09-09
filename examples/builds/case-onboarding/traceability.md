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
| REQ-006 | Q83 | Agents on Lightning desktop see case identity and state at a glance on every Case record type | M1-S01 | `CompactLayout:Case_Intake` | metadata-builder | — | M1-S01-T2 | checker | In UAT | `artefacts/M1-S01/objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml` | pass — `check_list_views_and_compact_layouts.py --manifest-dir artefacts/M1-S01` exit 0, `No issues found.` That exit covers the compact layout, its `compactLayoutAssignment` on the CustomObject and on both record types, and the field-type lookup against `objects/Case/fields/`. |
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
