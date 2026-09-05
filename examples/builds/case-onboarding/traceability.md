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
| REQ-001 | Q1 | Support work from support@, the web form and manual agent entry is a case process of its own | M1-S01 | `RecordType:Case.Support` | metadata-builder | — | M1-S01-T1 | checker | In Build | `artefacts/M1-S01/objects/Case/recordTypes/Support.recordType-meta.xml` | pass — `check_record_type_layouts.py --manifest-dir artefacts/M1-S01` exit 0, `2 record type(s), 0 layout(s); 0 finding(s) detected.` Also covered by `xml` (parsed) and `manifest` (member ↔ file, both directions). Record-type-to-layout cross-reference is NOT asserted at this scope — 0 layouts were in view; M1's milestone test at `--manifest-dir artefacts` carries it once M1-S02 lands. |
| REQ-002 | Q1 | Finance queries arriving at billing@ are a case process of their own, worked by Finance | M1-S01 | `RecordType:Case.Billing` | metadata-builder | — | M1-S01-T1 | checker | In Build | `artefacts/M1-S01/objects/Case/recordTypes/Billing.recordType-meta.xml` | pass — same run as REQ-001. |
| REQ-003 | Q2 | The support status ladder exposes an Escalated state, because untouched support cases hand off to Tier 2 | M1-S01 | `BusinessProcess:Case.Support Process` | metadata-builder | — | TC-M1S01-01 | manual | In UAT | `artefacts/M1-S01/objects/Case/businessProcesses/Support_Process.businessProcess-meta.xml` | outstanding — manual, ticked at the M1 gate. Machine coverage so far: `xml` parsed; `manifest` resolved `BusinessProcess:Case.Support Process` ↔ file in both directions. Status values (New/Escalated/Closed) are a builder default, not a customer-confirmed set — see `decisions.md` D-M1S01-01. |
| REQ-004 | Q2 | The billing status ladder has no Escalated state: Tier 2 engineering is not the escalation target for a finance query | M1-S01 | `BusinessProcess:Case.Billing Process` | metadata-builder | — | TC-M1S01-01 | manual | In UAT | `artefacts/M1-S01/objects/Case/businessProcesses/Billing_Process.businessProcess-meta.xml` | outstanding — manual, ticked at the M1 gate. Same machine coverage as REQ-003. |
| REQ-005 | Q19 | Each intake channel stamps a Case Origin value that routing can filter on; there is no phone value | M1-S01 | `StandardValueSet:CaseOrigin` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml` | pass — `manifest` two-way, `StandardValueSet:CaseOrigin` ↔ file, 0 findings, no wildcards; `xml` parsed. The three values (Email-Support, Email-Billing, Web) are exposed on the record types and checked there by `check_record_type_layouts.py` exit 0. Downstream consumers (`CaseSettings.webToCase.caseOrigin`, the Email-to-Case addresses) are M3 and are not asserted here. |
| REQ-006 | Q83 | Agents on Lightning desktop see case identity and state at a glance on every Case record type | M1-S01 | `CompactLayout:Case_Intake` | metadata-builder | — | M1-S01-T2 | checker | In UAT | `artefacts/M1-S01/objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml` | pass — `check_list_views_and_compact_layouts.py --manifest-dir artefacts/M1-S01` exit 0, `No issues found.` That exit covers the compact layout, its `compactLayoutAssignment` on the CustomObject and on both record types, and the field-type lookup against `objects/Case/fields/`. |
| REQ-007 | Q38 | A Severity 1 outage is identifiable on the Case so it can run on the 24/7 calendar and never pause | M1-S01 | `CustomField:Case.Severity__c` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml` | pass — `manifest` two-way, `CustomField:Case.Severity__c` ↔ file; `xml` parsed; the field is named by the compact layout, which `check_list_views_and_compact_layouts.py` resolved. **Field content was not machine-checked**: `check_object_creation_and_design.py` returns before any assertion for a file stem not ending `__c` (script L146–148), so its exit 0 says nothing about `Case` or its fields. The single value `Severity 1` is a recorded open item — `decisions.md` D-M1S01-02. |
| REQ-008 | Q40 | A case's SLA calendar is resolvable at creation from the account's region | M1-S01 | `CustomField:Account.Region__c` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/objects/Account/fields/Region__c.field-meta.xml` | pass — `manifest` two-way, `CustomField:Account.Region__c` ↔ file; `xml` parsed. Same field-content gap as REQ-007. The deliberate absence of a field default is recorded in `decisions.md` D-M1S01-04; the US fallback for unknown accounts is M4-S03's flow, not this field. |
| REQ-009 | Q38 | The first-response target (4 business hours vs 1 business day) is selectable from the account's contracted tier | M1-S01 | `CustomField:Account.Support_Tier__c` | metadata-builder | — | M1-S01-T6 | manifest | In UAT | `artefacts/M1-S01/objects/Account/fields/Support_Tier__c.field-meta.xml` | pass — `manifest` two-way, `CustomField:Account.Support_Tier__c` ↔ file; `xml` parsed. Same field-content gap as REQ-007. Consumed by M4-S02's entitlement process, which is not asserted here. |
| REQ-010 | Q13 | A Tier 1 agent cannot open a Billing case at all — record-level restriction, not a hidden field | M1-S01 | `CustomObject:Case` | metadata-builder | D5 | TC-M1S01-02 | manual | In UAT | `artefacts/M1-S01/objects/Case/Case.object-meta.xml` | outstanding — manual, ticked at the M1 gate; `tests/M1-S01/manual-evidence.stdout` records the disk evidence (`sharingModel=Private`, `externalSharingModel=Private`, no `*.settings-meta.xml` anywhere under `artefacts/`). The machine assertion that the OWD is not looser than the sharing rule's grant is M2-S05's build-scoped `check_sharing_model.py` test, which needs both files and has not run. |
| REQ-011 | Q5 | A support agent works a support case on a Case page of its own, carrying the severity flag a 24/7 outage needs | M1-S02 | `Layout:Case-Case Support Layout` | metadata-builder | — | M1-S02-T1 | checker | In UAT | `artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml` | pass — `check_record_type_layouts.py --manifest-dir artefacts/M1-S02` exit 0, `score 100`, `Scanned 2 metadata file(s): 0 record type(s), 2 layout(s); 2 finding(s) detected.` Both findings `INFO` ("marks no field behavior=Required"), which is Q5's answer being honoured rather than a defect; the checker promotes `INFO` to a non-zero exit only under `--strict`, which the plan does not declare. Also `xml` (3 of 3 parsed) and `manifest` (2 members ↔ 2 files, both directions, 0 failures). **Record-type-to-layout cross-reference NOT asserted at this scope** — 0 record types were in view, the mirror image of M1-S01's 0 layouts; M1's milestone test at `--manifest-dir artefacts` is the only run that sees both. `Severity__c` is on this layout and not on Billing: `decisions.md` D-M1S02-02. Manual half outstanding — see REQ-013 and REQ-014. |
| REQ-012 | Q5 | Finance work a billing case on a page of its own, with no severity concept on it | M1-S02 | `Layout:Case-Case Billing Layout` | metadata-builder | — | M1-S02-T1 | checker | In UAT | `artefacts/M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml` | pass — same run as REQ-011, same exit, its own `INFO` finding, and the same named cross-reference gap. Eight fields, identical to the Support layout minus `Severity__c` and the `emptySpace`. Neither layout is assigned to anyone yet: `layoutAssignments` lives only on `Profile`, which is M2-S01's, so both deploy and neither is reachable — recorded in `artefacts/M1-S02/deploy-order.md` and in workbook Section 2's preamble. |
| REQ-013 | Q24 | A case logged by hand goes through the active assignment rule from the page the agent uses | M1-S02 | `Layout:Case-Case Support Layout` | metadata-builder | — | TC-M1S02-01 | manual | In UAT | `artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml` \| `artefacts/M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml` | outstanding — manual, ticked at the M1 gate, and **tickable only in part**. Machine coverage: `xml` parsed, `manifest` resolved both members ↔ both files. Disk evidence in `tests/M1-S02/manual-evidence.stdout`: `<showRunAssignmentRulesCheckbox>` present and `true` on both layouts, so the **presence** reading passes; the test's literal **positional** reading ("`<layoutSections>` is preceded by the checkbox") fails on both, because the cited skill's own example places every `show*` element after the final `</layoutSections>` and both artefacts match it exactly. The tester applied the presence reading and recorded why. Q24's "defaulted on" half is **unproven and unprovable from the artefacts** — no element in the cited skill's inventory pre-checks the box (`decisions.md` D-M1S02-03). The gate must either accept the narrowing or route the remainder to a recorded Setup step. **Why `artefact` names one layout and `artefact_paths` names two:** `check_rtm.py` applies its pipe-delimited multi-value split to the story and test id columns only — `artefact` is read as a single value (script L626 versus L592–593) — so the column names the layout the requirement carries the most traffic on (support intake is ~460 cases a day against billing's share of the rest) and both files stay in `artefact_paths`. The element is identical on both. |
| REQ-014 | Q57 | Every field a validation rule attaches its error to is visible on the page where that error appears | M1-S02 | `Layout:Case-Case Billing Layout` | metadata-builder | — | TC-M1S02-01 | manual | In UAT | `artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml` \| `artefacts/M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml` | outstanding — manual, and **not file-checkable at M1-S02 time**. `Priority` and `Origin` are present on both layouts, which is what assumption **A13** needs for the two rules `M3-S01` declares (`Priority_Required_On_Agent_Save`, `Origin_Must_Be_Known`). But no `ValidationRule` metadata exists anywhere under `artefacts/` yet — `M3-S01` is `pending` — so there is no `errorDisplayField` to resolve and nothing to check against. Carry-forward the M1 gate should see: `Severity__c` is on the Support layout only, so a third Case rule attaching its error to that field would fail A13 on the Billing layout. Q57 is **deferred**; A13 is the standing assumption at `risk: medium`. **Why `artefact` names the Billing layout:** same single-value column as REQ-013, and this is the layout the assumption is at risk on — it is the one missing `Severity__c`. Both files are in `artefact_paths`. |

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
