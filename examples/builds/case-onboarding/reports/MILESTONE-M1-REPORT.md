# M1 — Case data model and record-type layouts · acceptance report

**Build:** `case-onboarding` · **plan version:** 5 · **plan status:** `approved` · **build_mode:** `design-only`
**Written by:** `agents/milestone-verifier/AGENT.md` (Step 9) — this document is *written*, not rendered
(`standards/build-orchestration.md` § 2).
**Date:** 2026-09-05 · **Verdict:** `ready-with-findings` · **Confidence:** MEDIUM

> This report is a recommendation. **G3 is the human's**, and this agent neither approved nor
> recorded it. The gate command is in § 9, unrun.

---

## 0. Blocked steps

**None.** Both M1 steps are `documented`. Nothing in this milestone rests on
`standards/build-orchestration.md` § 3's blocked-with-a-reason carve-out.

Precondition checks, both passed:

| Check | Result |
|---|---|
| Every step in M1 is `documented` | `M1-S01` documented, `M1-S02` documented |
| Preceding milestone gate `approved` | n/a — M1 is the first milestone; the `plan` gate is `approved` (2026-09-05T19:35:19Z) and `step:M1-S01` is `approved` (2026-09-05T19:35:41Z) |

---

## 1. The milestone and its artefacts

**Goal (from `plan.json`):** given a greenfield org with no existing Case records (Q4), when the Case
model is deployed, then two record types with their Support Processes, the three active Origin values
and one layout per record type exist, and every field the routing and SLA milestones reference resolves.

### M1-S01 — `object-model`, owner `metadata-builder`, `human_gate: true` (approved)

| Artefact | Type · member | Declared in `outputs[]` |
|---|---|---|
| `standardValueSets/CaseOrigin.standardValueSet-meta.xml` | StandardValueSet · `CaseOrigin` | yes |
| `objects/Case/Case.object-meta.xml` | CustomObject · `Case` | yes |
| `objects/Case/businessProcesses/Support_Process.businessProcess-meta.xml` | BusinessProcess · `Case.Support Process` | yes |
| `objects/Case/businessProcesses/Billing_Process.businessProcess-meta.xml` | BusinessProcess · `Case.Billing Process` | yes |
| `objects/Case/recordTypes/Support.recordType-meta.xml` | RecordType · `Case.Support` | yes |
| `objects/Case/recordTypes/Billing.recordType-meta.xml` | RecordType · `Case.Billing` | yes |
| `objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml` | CompactLayout · `Case_Intake` | yes |
| `objects/Case/fields/Severity__c.field-meta.xml` | CustomField · `Case.Severity__c` | yes |
| `objects/Account/fields/Region__c.field-meta.xml` | CustomField · `Account.Region__c` | yes |
| `objects/Account/fields/Support_Tier__c.field-meta.xml` | CustomField · `Account.Support_Tier__c` | yes |
| `record-type-decision.md` | — (document) | yes |
| `package.xml` | — (manifest) | yes |
| `deploy-order.md` | — (document) | **no — see F-04** |

### M1-S02 — `ui`, owner `metadata-builder`, `depends_on: [M1-S01]`, `human_gate: false`

| Artefact | Type · member | Declared in `outputs[]` |
|---|---|---|
| `layouts/Case-Case Support Layout.layout-meta.xml` | Layout · `Case-Case Support Layout` | yes |
| `layouts/Case-Case Billing Layout.layout-meta.xml` | Layout · `Case-Case Billing Layout` | yes |
| `package.xml` | — (manifest) | yes |
| `deploy-order.md` | — (document) | **no — see F-04** |

---

## 2. Symbol inventory (Step 2)

M1 is the first milestone, so there is no earlier-milestone inventory to inherit. Everything below is
defined *by this milestone*:

| Class | Symbols | Defined by |
|---|---|---|
| Objects | `Case` | M1-S01 |
| Fields | `Case.Severity__c`, `Account.Region__c`, `Account.Support_Tier__c` | M1-S01 |
| Picklist values | `Case.Severity__c`: `Severity 1` · `Account.Region__c`: `EMEA`, `US` · `Account.Support_Tier__c`: `Premier`, `Standard` | M1-S01 |
| Value sets | `StandardValueSet:CaseOrigin` → `Email-Support`, `Email-Billing`, `Web` (`Web` is `<default>true</default>`) | M1-S01 |
| Record types | `Case.Support`, `Case.Billing` (both `active`) | M1-S01 |
| Business processes | `Case.Support Process` (New/Escalated/Closed), `Case.Billing Process` (New/Closed), both `isActive` | M1-S01 |
| Compact layouts | `Case_Intake` | M1-S01 |
| Layouts | `Case-Case Support Layout`, `Case-Case Billing Layout` | M1-S02 |
| Queues, groups, permission sets, business hours, milestone types, entitlement processes, Flows | **none** | — |

`Account` itself is not in the inventory and is not a manifest member: two `CustomField` members are
object-qualified to it, and `Account` is a standard object that pre-exists in any target org. Checked,
not overlooked.

---

## 3. Reference resolution (Step 3)

The table below states which reference classes were resolved, so the boundary of the check is visible
rather than inferred from silence.

| Reference class | Read from | References found | Resolved in M1 | Resolved earlier | Unresolved | Unclassifiable |
|---|---|---|---|---|---|---|
| Validation rule field references | `.validationRule` `<errorConditionFormula>` / `<errorDisplayField>` | **0** — no ValidationRule metadata exists (M3-S01 is `pending`) | — | — | — | — |
| Assignment rule criteria | `<criteriaItems>/<field>`, `<assignedTo>` | **0** — no AssignmentRules in M1 (M3-S03/S04) | — | — | — | — |
| Permission set grants | `<fieldPermissions>/<field>`, `<objectPermissions>/<object>` | **0** — no PermissionSet or Profile in M1 (all of M2) | — | — | — | — |
| Flow field references | `<field>`, `<object>`, lookup/update filters, formula merge fields | **0** — no Flow in M1 (M4) | — | — | — | — |
| Entitlement process milestones | `<milestoneType>/<milestoneName>`, business hours named | **0** — no EntitlementProcess in M1 (M4) | — | — | — | — |
| **Layout and path assignments** — the fields and picklist values a layout or path step names | both `Layout` files, the `CompactLayout`, both `RecordType` `picklistValues` blocks, the object and record-type `compactLayoutAssignment` elements | **17** | **17** | 0 | **0** | 0 |

### The 17 resolved references, in full

| # | From | Reference | Resolves to |
|---|---|---|---|
| 1 | `Case-Case Support Layout` | field `Severity__c` | `Case.Severity__c` — M1-S01 |
| 2–8 | `Case-Case Support Layout` | `Subject`, `Priority`, `Origin`, `Status`, `OwnerId`, `CaseNumber`, `CreatedById`, `LastModifiedById` | standard Case fields; pre-exist in the target org |
| 9 | `CompactLayout:Case_Intake` | field `Severity__c` | `Case.Severity__c` — M1-S01 |
| 10 | `CustomObject:Case` | `compactLayoutAssignment` `Case_Intake` | `CompactLayout:Case_Intake` — M1-S01 |
| 11 | `RecordType:Case.Support` | `compactLayoutAssignment` `Case_Intake` | same |
| 12 | `RecordType:Case.Billing` | `compactLayoutAssignment` `Case_Intake` | same |
| 13 | `RecordType:Case.Support` | `businessProcess` `Support Process` (bare, correctly unqualified) | `BusinessProcess:Case.Support Process` — M1-S01 |
| 14 | `RecordType:Case.Billing` | `businessProcess` `Billing Process` (bare) | `BusinessProcess:Case.Billing Process` — M1-S01 |
| 15 | `RecordType:Case.Support` | Origin value `Email-Support` | `StandardValueSet:CaseOrigin` — M1-S01 |
| 16 | `RecordType:Case.Support` | Origin value `Web` | same |
| 17 | `RecordType:Case.Billing` | Origin value `Email-Billing` | same |

Every one of the three `CaseOrigin` values is exposed on at least one record type; none is orphaned.
Both layouts' standard-field lists are treated as pre-existing rather than as unresolved — that is a
stated assumption of this check, not a silent pass.

### Findings from Step 3

**F-01 · HIGH · The record-type ↔ layout binding is not asserted anywhere in M1, including by this
milestone's own acceptance test.**

`milestones[M1].acceptance_tests[0].description` states that at `--manifest-dir artefacts` the checker
"sees M1-S01's two record types and M1-S02's two layouts together, **which is where 'every layout
referenced by a record type exists and every field on it resolves' can actually be asserted**." The run
was made and that sentence is false. In `check_record_type_layouts.py`, every record-type-to-layout
check reads from `layoutAssignments`, and `collect()` populates `layout_assignments` **only** from
`Profile` and `PermissionSet` roots (script `collect()`, the `root_type in {"Profile", "PermissionSet"}`
branch). No Profile or PermissionSet metadata exists anywhere under `artefacts/` — `layoutAssignments`
lives only on `Profile`, which is `M2-S01`'s. So:

- check 1 (assignment naming an inactive record type) — no assignments, does not fire;
- check 3 (record type nobody can select) — gated on `model.visibility_entries`, empty, does not fire;
- check 6 (assignment naming a layout not in the tree) — no assignments, does not fire;
- check 7's "N reference(s) unresolvable at this scope" INFO — fires only when references *exist* and
  targets do not. Here there are zero references, so the checker is **silent** about having made no
  cross-check. Silence reads as clean.

Measured proof: the milestone run's finding set is byte-for-byte the union of the two step runs —
M1-S01 at step scope gave `2 record type(s), 0 layout(s); 0 finding(s)`, M1-S02 gave
`0 record type(s), 2 layout(s); 2 finding(s)`, and the build-scoped run gives
`2 record type(s), 2 layout(s); 2 finding(s)`, the same two INFOs. **The build-scoped run adds no
assertion the two step-scoped runs did not already make.**

What this agent could check without the linking metadata, and did: the naming correspondence is 1:1 —
`Case.Support` ↔ `Case-Case Support Layout`, `Case.Billing` ↔ `Case-Case Billing Layout`, two record
types and two layouts, each record type matching exactly one layout by the `<Object>-<Layout Name>`
file-name convention. That is a *convention* match, not a metadata binding.

*Deploy-time consequence, per `skills/devops/deployment-error-diagnosis`:* none at M1 deploy — both
layouts and both record types deploy cleanly on their own. The exposure is later: when M2-S01's
profile carries `layoutAssignments`, a name that does not match one of these two files produces
`INVALID_CROSS_REFERENCE_KEY` on that deploy, and the profile-delta pattern in the same skill
("Field-level security cannot be set on a non-existent field" / cross-reference on a profile naming
metadata not in the target) is the shape it will take. `artefacts/M1-S02/deploy-order.md` already
records the exact member forms M2-S01 must reuse, which is the mitigation.

*Consequence inside the build:* three `traceability.md` rows (REQ-001, REQ-011, REQ-012) and four
workbook rows (CWB-OBJ-004, CWB-OBJ-005, CWB-LAYOUT-001, CWB-LAYOUT-002) each name "M1's milestone test
at `--manifest-dir artefacts`" as the run that carries this cross-reference. Those seven statements are
now known to be wrong, and they were written in good faith from the plan's own description.

**Remedy for v6 (planner):** either (a) reword the milestone test's `description` to what the run
proves — that the two step trees are mutually consistent and that a record type's business process,
compact layout and Origin values all resolve — and move the record-type-to-layout binding assertion
onto an M2 milestone test running the same checker at `--manifest-dir artefacts` once the profiles
exist; or (b) leave the assertion in M1 and accept that it is a name-convention check performed by a
human at the gate. Option (a) matches `standards/build-orchestration.md` § 5's own rule that a
cross-referential checker belongs where both halves of the pair exist.

**F-02 · INFO · Business-process Status values are unresolvable in-tree by design.**

`Case.Support Process` selects `New`, `Escalated`, `Closed`; `Case.Billing Process` selects `New`,
`Closed`. All five references resolve against `StandardValueSet:CaseStatus`, which assumption **A28**
deliberately keeps out of this build ("no `StandardValueSet:CaseStatus` file is deployed"). There is
therefore nothing in the tree to resolve them against. Classified **unclassifiable-in-tree /
deferred-to-org**, not unresolved-and-broken.

*Deploy-time consequence:* if any of `New`, `Escalated` or `Closed` is not a live `CaseStatus` value in
the target org, the deploy fails **on the business processes**, presenting as
`Component error: 'Escalated' is not a valid value for type 'CaseStatus'` — the picklist-value-missing
row of `skills/devops/deployment-error-diagnosis`'s error table. `artefacts/M1-S01/deploy-order.md`
already names the pre-deploy step ("retrieve `StandardValueSet:CaseStatus` and reconcile before
deploying") and `record-type-decision.md` § 2 repeats it as an open item at MEDIUM confidence. Carried
into § 8 below as a go/no-go item, per `skills/devops/pre-deployment-checklist`'s dependency-
completeness gate.

**F-03 · MEDIUM · Assumption A13's stated verification route does not exist.**

`plan.json.assumptions[A13]` (risk `medium`) reads: "M1-S02's checker does not prove it at step scope
… so the assertion sits in M1-S02's manual test **and in M1's milestone checker at
`--manifest-dir artefacts`**." `check_record_type_layouts.py` reads no `ValidationRule` metadata at any
scope — `METADATA_SUFFIXES` carries no `.validationRule` entry — and no ValidationRule file exists in
the build yet (M3-S01 is `pending`). So the milestone checker does not and cannot carry A13. A13 is
unverified after M1 and stays unverified until M3-S01 lands. The step tester recorded exactly this
(`tests/M1-S02/manual-evidence.stdout`, half 2); this finding is that the *plan text* asserts a route
that does not exist.

---

## 4. Deployment order (Step 4)

The milestone sequence is: objects → fields → picklists → record types → layouts → permission sets →
sharing → automation → routing → SLA. Positions below are the ones `build-doc-keeper` recorded on each
workbook row; the "agrees with type" column is this agent's check.

| Artefact | Recorded position | Position by artefact type | Agrees | Workbook row |
|---|---|---|---|---|
| `CustomField:Case.Severity__c` | 2 of 10 (fields) | 2 (fields) | ✅ | CWB-OBJ-007 |
| `CustomField:Account.Region__c` | 2 of 10 (fields) | 2 | ✅ | CWB-OBJ-008 |
| `CustomField:Account.Support_Tier__c` | 2 of 10 (fields) | 2 | ✅ | CWB-OBJ-009 |
| `StandardValueSet:CaseOrigin` | 3 of 10 (picklists) | 3 | ✅ | CWB-OBJ-001 |
| `BusinessProcess:Case.Support Process` | 4 of 10, with record types | no slot of its own in the sequence | ✅ reported, not invented | CWB-OBJ-002 |
| `BusinessProcess:Case.Billing Process` | 4 of 10, with record types | no slot of its own | ✅ | CWB-OBJ-003 |
| `RecordType:Case.Support` | 4 of 10 (record types) | 4 | ✅ | CWB-OBJ-004 |
| `RecordType:Case.Billing` | 4 of 10 (record types) | 4 | ✅ | CWB-OBJ-005 |
| `CompactLayout:Case_Intake` | **cannot be placed** — reported | no slot: a compact layout is not a page layout | ✅ reported, not invented | CWB-OBJ-006 |
| `Layout:Case-Case Support Layout` | 5 of 10 (layouts) | 5 | ✅ | CWB-LAYOUT-001 |
| `Layout:Case-Case Billing Layout` | 5 of 10 (layouts) | 5 | ✅ | CWB-LAYOUT-002 |
| `CustomObject:Case` | **7 of 10 (sharing)** | **1 (objects)** | ⚠️ **divergence — F-05** | CWB-SHARE-001 |

### Backwards-dependency check

Every dependency runs forward through the sequence. Nothing runs backwards:

| Dependency | Direction |
|---|---|
| `Case-Case Support Layout` (5) → `Case.Severity__c` (2) | forward — the field lands before the layout that names it, so no "field does not exist" deploy failure |
| `RecordType` (4) → `BusinessProcess` (4, internal 3 before 5) | forward — a Case record type is rejected without its process |
| `RecordType` (4) → `CompactLayout` (internal 4 before 5) | forward |
| `CustomObject:Case` `compactLayoutAssignment` → `CompactLayout` | forward within the step |
| `RecordType` `picklistValues` (4) → `StandardValueSet:CaseOrigin` (3) | forward — a `picklistValues` block exposes values, it does not create them |

**Permission-set ordering** (`skills/devops/permission-set-deployment-ordering`): positions 6 and 7 are
empty in M1. There is no `fieldPermissions` entry anywhere in this milestone, so the failure that skill
exists to catch — a permission set granting a field that is not yet in the org — cannot occur here. It
becomes live at M2, where five `access` steps grant against the three fields M1 defines; the ordering
requirement is that M1 deploys first, which the milestone sequence already encodes.

**Flow / automation ordering** (`skills/devops/flow-deployment-activation-ordering`): positions 8–10 are
empty in M1. No Flow, no activation state, no paused-interview exposure. Not applicable this milestone.

### Findings from Step 4

**F-05 · LOW · `CustomObject:Case` is recorded at position 7 (sharing) and has no position-1 row.**

`objects/Case/Case.object-meta.xml` is one file carrying two concerns: the object-level
`compactLayoutAssignment` and the org-wide default (`sharingModel` / `externalSharingModel`). The
workbook gives it a single row, `CWB-SHARE-001` in § 4 Sharing settings, at position 7. By artefact type
a `CustomObject` belongs at position 1. There is no corresponding row in § 1 Objects and fields.

This is a divergence between the recorded position and the type, and it is reported rather than
corrected — but it does **not** break the deploy, for a reason worth stating explicitly: `Case` is a
**standard** object. It already exists in every target org, so its three `CustomField` members landing
at position 2, "before" the object file at position 7, creates no dependency that runs backwards. The
step's own internal order (`artefacts/M1-S01/deploy-order.md`) places the object file last, at position
5 of 5, on the same reasoning, and a single-manifest deploy is atomic in any case. If a future step adds
a *custom* object under the same pattern, the same row shape would be genuinely wrong.

*For the human at the gate:* nothing to fix before deploying M1. For v6, either split the object into
two workbook rows (object at 1, OWD at 7) or record on CWB-SHARE-001 that the position is the OWD's and
not the object's.

**F-04 · MEDIUM · `deploy-order.md` is undeclared in `outputs[]` on both M1 steps.**

Reported, not failed, exactly as `decisions.md` **O-M1S02-02** already records it. Both files exist and
are substantive (4.6 KB and 5.6 KB). Neither `artefacts/M1-S01/deploy-order.md` nor
`artefacts/M1-S02/deploy-order.md` appears in its step's `outputs[]`, so `check-outputs` never confirmed
either — it only ever confirms paths the plan declared — and the always-on `manifest` test skipped both
by name as non-metadata files. Two of two `metadata-builder` steps, which makes it a plan-wide pattern.
It matters beyond bookkeeping: `agents/build-doc-keeper/AGENT.md` Step 10 compiles `M5-S04`'s build-wide
deploy order from exactly these per-step files, so that compile depends on a file set no gate confirms.

**Remedy for v6:** declare `artefacts/<step-id>/deploy-order.md` in `outputs[]` on every
`metadata-builder`-owned step.

---

## 5. Merged manifest (Step 5)

**Path:** `reports/MILESTONE-M1-package.xml` — 7 `<types>` blocks, 12 members, members sorted within
each block, one `<version>`.

| Type | Members | From |
|---|---|---|
| `BusinessProcess` | `Case.Billing Process`, `Case.Support Process` | M1-S01 |
| `CompactLayout` | `Case_Intake` | M1-S01 |
| `CustomField` | `Account.Region__c`, `Account.Support_Tier__c`, `Case.Severity__c` | M1-S01 |
| `CustomObject` | `Case` | M1-S01 |
| `Layout` | `Case-Case Billing Layout`, `Case-Case Support Layout` | M1-S02 |
| `RecordType` | `Case.Billing`, `Case.Support` | M1-S01 |
| `StandardValueSet` | `CaseOrigin` | M1-S01 |

| Merge check | Result |
|---|---|
| API version agreement | **agree** — both step manifests carry `<version>62.0</version>`; one `<version>` element written, no conflict, no `REFUSAL_NEEDS_HUMAN_REVIEW` |
| Member appearing in two steps | **none** — the two step manifests are type-disjoint |
| Wildcard members | **none** — every member explicit, which is the CI-safe form `skills/devops/metadata-api-retrieve-deploy` prescribes |
| File under `artefacts/` reaching no `<types>` block | **4**: `M1-S01/deploy-order.md`, `M1-S01/record-type-decision.md`, `M1-S02/deploy-order.md` (documents, correctly carry no member — but see F-04), and the two step `package.xml` files, which are the manifests themselves |
| Merged manifest parses | yes |
| `<version>` present | yes, `62.0` |

**F-06 · INFO · The API version 62.0 was defaulted by the owning agent, twice.** `plan.json` carries no
`api_version` key; `metadata-builder` chose `62.0` on M1-S01 and again on M1-S02, and the two agree.
Recorded already in workbook rows CWB-OTHER-001 and CWB-OTHER-004. The merged manifest inherits it. Worth
a decision at v6 rather than a third default.

---

## 6. Acceptance-test results (Step 6)

Run from the build directory, at build scope — `standards/build-orchestration.md` § 5: "At milestone
level the scope is always `build`." Evidence under `tests/M1/`.

| # | Type | Command / runner | Exit | Expected | Result |
|---|---|---|---|---|---|
| 1 | `checker` | `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts` | **0** | `exit 0` | **PASS** |
| 2 | `manifest` | two-way member ↔ file over the merged milestone manifest | **0** | `consistent` | **PASS** — `verdict: consistent \| failures: 0` |
| 3 | `manual` | — | n/a | ticked at the gate | **deferred to § 7** |

Every declared milestone test exists and ran. No declared checker was missing.

Test 1 output, in full:

```json
{
  "score": 100,
  "findings": [
    {"severity": "INFO", "location": "artefacts/M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml",
     "message": "layout 'Case-Case Billing Layout' marks no field behavior=Required"},
    {"severity": "INFO", "location": "artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml",
     "message": "layout 'Case-Case Support Layout' marks no field behavior=Required"}
  ],
  "summary": "Scanned 7 metadata file(s): 2 record type(s), 2 layout(s); 2 finding(s) detected."
}
```
stderr: `WARN: 2 review/info finding(s) detected`.

**F-07 · LOW · The milestone test's `description` predicts `0 finding(s)`; the run produces 2.**

The file and component counts in the declared description are exactly right — 7 files, 2 record types,
2 layouts. The finding count is not: 2, both `INFO`, both "marks no field behavior=Required". **The
declared `expected: exit 0` still holds**, because `check_record_type_layouts.py` promotes `INFO` to a
non-zero exit only under `--strict`, which the plan does not declare. And both findings are check 4
firing exactly as **Q5's answer requires**: `Priority` and `Origin` are enforced at field or
validation-rule level rather than by layout, because Email-to-Case and Web-to-Case create through the
API where layout `Required` does not bind. Adding a layout-level `Required` to silence them would
contradict Q5. So the artefacts are right and the sentence is stale.

This is the same defect class `decisions.md` **O-M1S02-01** records against the *step* test's
description. It has now occurred on the milestone test too, and that instance is **not yet recorded
anywhere** — it is new to this report. **Remedy for v6:** reword to `2 finding(s), both INFO — check 4,
which Q5's answer predicts`.

---

## 7. Manual checklist for the human at G3 (Step 7)

Five lines. Each names the step it came from, what the human does, and what counts as a tick. No line is
ticked by this agent. Where the tester gathered disk evidence, it is quoted so the human is confirming a
reading rather than re-deriving it.

---

### ☐ 1 — M1 (milestone) · `record-type-decision.md` states its own provenance

**Do:** read `artefacts/M1-S01/record-type-decision.md`.
**Ticks when** all three clauses hold: (a) it states the record-type count was decided in the plan, not
by the builder; (b) it names D5's criteria-based sharing rule on `RecordTypeId` as what settled Q1's
conditional; (c) it shows the Status **and Reason** value sets for each of the two processes.

**Evidence already on disk:**
- (a) ✅ § 1: "Assumption **A26** resolves that conditional in favour of two" — A26 is a plan
  assumption, `steps: [M1-S01, M1-S02, M2-S03, M2-S05]`.
- (b) ✅ § 1, verbatim: "because decision D5's criteria-based sharing rule keys on `RecordTypeId`: with
  a single record type there is no record-level criterion that keeps Billing cases away from Tier 1."
- (c) ⚠️ **half.** Status is shown (§ 2 table: Support → New/Escalated/Closed; Billing → New/Closed).
  **Reason is not, and cannot be:** § 2 records "`Case.Reason` is named in Q1's answer and is **not**
  configured here — no clarification enumerates its values, so no `picklistValues` block for `Reason`
  was written."

> **This line is not fully tickable as worded.** The human either accepts the narrowing (Status shown,
> Reason absent and the absence documented) or rules that clause (c) asks for something the build was
> never given the input to produce. Workbook row CWB-OTHER-003 flags the same gap. A v6 reword would
> drop "and Reason" or add a clarification that enumerates `Case.Reason` values.

---

### ☐ 2 — M1-S01 · Business processes exist beside the record types, with the right name forms

**Do:** list `artefacts/M1-S01/`.
**Ticks when** two `businessProcess-meta.xml` files sit beside the two `recordType-meta.xml` files, each
record type's `<businessProcess>` carries the **bare** process name (not `Case.Support Process`), and
`package.xml` lists `BusinessProcess` with **object-qualified** members.

**Evidence already on disk** (`tests/M1-S01/manual-evidence.stdout`, re-confirmed by this agent):
- businessProcess files: `Billing_Process.businessProcess-meta.xml`, `Support_Process.businessProcess-meta.xml` ✅
- recordType files: `Billing.recordType-meta.xml`, `Support.recordType-meta.xml` ✅
- `Support.recordType` `businessProcess = 'Support Process'` — bare, no `Case.` prefix ✅
- `Billing.recordType` `businessProcess = 'Billing Process'` — bare ✅
- `package.xml` `BusinessProcess` members: `Case.Billing Process`, `Case.Support Process` — object-qualified ✅

All four clauses hold. This one is a straight tick.

---

### ☐ 3 — M1-S01 · The Case org-wide default is Private, and only the object file carries it

**Do:** read `artefacts/M1-S01/objects/Case/Case.object-meta.xml`.
**Ticks when** it carries `<sharingModel>Private</sharingModel>` and
`<externalSharingModel>Private</externalSharingModel>` as **direct children of `<CustomObject>`**, and
no separate settings file anywhere in the build claims to carry the OWD.

**Evidence already on disk** (`tests/M1-S01/manual-evidence.stdout`, re-confirmed by this agent):
- root tag `CustomObject`; direct children `{compactLayoutAssignment: Case_Intake, externalSharingModel: Private, sharingModel: Private}` ✅
- `*.settings-meta.xml` anywhere under `artefacts/`: **none** ✅
- other files containing the string `<sharingModel>`: only the two prose documents
  (`record-type-decision.md`, `deploy-order.md`) and the object file itself ✅

All clauses hold. **What the tick does *not* cover, and the human should know it:** the OWD is the
conservative reading of **deferred blocking question Q13** through assumption **A1**, whose `risk` is
`high`. The machine assertion that the OWD is not looser than the sharing rule's grant is `M2-S05`'s
build-scoped `check_sharing_model.py` test, which needs both files and has not run. Approving this line
approves the *artefact*, not the *policy*.

---

### ☐ 4 — M1-S02 · The assignment-rule checkbox is on both layouts (Q24)

**Do:** read both layout files.
**Ticks when** `<layoutSections>` is preceded by the assignment-rule checkbox, default set on.

**Evidence already on disk** (`tests/M1-S02/manual-evidence.stdout`), and this is the line that needs the
most from the human:

| Reading | Billing layout | Support layout |
|---|---|---|
| `<showRunAssignmentRulesCheckbox>` present, value `true` — **presence** | ✅ true | ✅ true |
| checkbox element precedes `<layoutSections>` — **positional, the test's literal words** | ❌ index 3 vs last `layoutSections` at index 1 | ❌ same |
| any element that **pre-checks** the box | none present | none present |

Both layouts' child order is `layoutSections, layoutSections, showEmailCheckbox,
showRunAssignmentRulesCheckbox, showKnowledgeComponent`.

Three things the human is being asked to accept:

1. **The positional reading fails on both layouts and should.** The cited skill's own example places
   every `show*` element after the final `</layoutSections>`, and both artefacts match that example
   exactly. The tester applied the **presence** reading and recorded why (`decisions.md` D-M1S02-03).
   The test's wording, not the artefacts, is what is off.
2. **Q24's "defaulted on" half is unproven and unprovable from the artefacts.**
   `<showRunAssignmentRulesCheckbox>` controls whether the checkbox is *shown*. No element in the cited
   skill's inventory pre-checks it. `artefacts/M1-S02/deploy-order.md` states this plainly: the
   select-by-default half "is **not written**, and is not inventable from the cited skill."
3. **So the gate must choose:** accept the narrowing (the checkbox is shown; agents tick it manually),
   or route the remainder to a recorded Setup step for a human, or deepen the skill so the element — if
   one exists — is documented. `standards/build-orchestration.md` § 8 names the third as the signal to
   deepen a skill rather than freestyle.

---

### ☐ 5 — M1-S02 · Every field a validation rule errors on is on both layouts (A13)

**Do:** read both layout files against the validation rules.
**Ticks when** every field a validation rule attaches its error to (assumption **A13**) is present on
both layouts.

**Evidence already on disk** (`tests/M1-S02/manual-evidence.stdout`, re-confirmed by this agent):
- `ValidationRule` files anywhere under `artefacts/`: **none**. `M3-S01` (type `validation`) is
  `pending`, so there is no `errorDisplayField` to resolve.
- Fields present on **both** layouts: `CaseNumber`, `CreatedById`, `LastModifiedById`, `Origin`,
  `OwnerId`, `Priority`, `Status`, `Subject`.
- On the **Support layout only**: `Severity__c`.

> **This line is not file-checkable at M1 and should not be ticked as verified.** `Priority` and
> `Origin` are on both layouts, which is what A13 needs for the two rules M3-S01 *declares*
> (`Priority_Required_On_Agent_Save`, `Origin_Must_Be_Known`) — but those rules do not exist yet, so
> that is a prediction, not a check. **Carry-forward the gate should see:** because `Severity__c` is on
> the Support layout only and absent from Billing by design (D-M1S02-02), a third Case validation rule
> attaching its error to `Severity__c` would break A13 on the Billing layout. A13's risk is `medium`
> and Q57 is deferred. See also **F-03**: the plan text claims this assertion is carried by M1's
> milestone checker, and it is not.

---

**Tick summary:** lines 2 and 3 are straight ticks against evidence already gathered. Line 1 is tickable
in two clauses of three. Line 4 needs a decision, not a tick. Line 5 is not verifiable in this milestone
at all and should be carried to M3.

---

## 8. Optional validate-only command — **for the human, and this agent did not run it**

`plan.json.build_mode` is `design-only` and no org alias is on file, so the alias below is a placeholder
the human replaces. The target is a **sandbox** — the requirement is explicit ("we must be able to prove
it works in a sandbox before customers see it") and M5's goal names the sandbox proof.

For a sandbox, the validate-only form is a **dry run of a deploy** — it compiles and validates without
saving:

```bash
sf project deploy start \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M1-package.xml \
  --dry-run --target-org <your-sandbox-alias>
```

**Optional. Human-run. `agents/milestone-verifier` never runs `sf`, and did not run this.**

For a **production** target — and only production — the command is instead
`sf project deploy validate` with the same manifest: Salesforce documents it as production-only, it
requires Apex tests, and it returns a job id redeemable by `sf project deploy quick` within 10 calendar
days.

**F-08 · MEDIUM · Both `deploy-order.md` files print the production form against a sandbox
placeholder.** `artefacts/M1-S01/deploy-order.md` and `artefacts/M1-S02/deploy-order.md` each close with
`sf project deploy validate --target-org <your-sandbox-alias> --manifest …`. That pairs the
production-only subcommand with an alias the same line names as a sandbox. A human copying it will hit
an error that has nothing to do with their build. **Remedy:** `metadata-builder` should emit the
`--dry-run` form when the target is a sandbox. Not fixed here — this agent does not edit artefacts
written by other agents in the loop.

### Go / no-go items before any deploy of this manifest

Per `skills/devops/pre-deployment-checklist`'s gate list, restricted to what this build can see:

- [ ] **Dependency completeness — `StandardValueSet:CaseStatus`.** Retrieve it from the target and
      confirm `New`, `Escalated` and `Closed` are live values. F-02: if any is missing, the deploy fails
      on the business processes. This is the one blocking pre-deploy check M1 carries.
- [ ] **`CompactLayout` member form.** `Case_Intake`, bare, is the thinnest-grounded member in the
      manifest — the cited skill states "compact layout name" in prose but its own sample manifest uses
      `*`, so no non-wildcard example existed to copy. Verify against a retrieve.
- [ ] **Pre-release backup.** Not applicable — greenfield Case model, no existing Case records (Q4), and
      `design-only` means nothing has been deployed. Recorded as checked-and-not-applicable rather than
      skipped.
- [ ] **Post-deploy manual steps.** Nothing in M1 makes record types selectable
      (`recordTypeVisibilities` is M2-S02's) or assigns either layout (`layoutAssignments` is M2-S01's).
      **M1 deploys cleanly and is not reachable by any user until M2 lands.** Expected at this point in
      the build; recorded so it is not mistaken for a defect.
- [ ] **Test level / coverage.** Not applicable — no Apex in M1.
- [ ] **Deployment window.** The human's call; nothing in the build can see it.

---

## 9. Requirement closure (Step 9)

From `traceability.md`, which uses the build-layer RTM schema of
`skills/admin/requirements-traceability-matrix` § "The Build-Layer RTM". M1 carries 14 rows,
`REQ-001`–`REQ-014`, and no requirement outside M1's steps.

**Closed by machine evidence in M1 — 8 rows** (`status: In Build` / `In UAT`, test type `checker` or
`manifest`, all passing):

| req_id | Requirement | Artefact | Proved by |
|---|---|---|---|
| REQ-001 | Support work is a case process of its own | `RecordType:Case.Support` | checker + manifest + xml |
| REQ-002 | Finance queries are a case process of their own | `RecordType:Case.Billing` | same run |
| REQ-005 | Each intake channel stamps an Origin value; no phone value | `StandardValueSet:CaseOrigin` | manifest two-way; values re-checked as exposed on the record types |
| REQ-006 | Case identity and state at a glance on every record type | `CompactLayout:Case_Intake` | `check_list_views_and_compact_layouts.py` exit 0, covering both assignment scopes |
| REQ-007 | A Severity 1 outage is identifiable on the Case | `CustomField:Case.Severity__c` | manifest two-way + xml; named by the compact layout |
| REQ-008 | SLA calendar resolvable from the account's region | `CustomField:Account.Region__c` | manifest two-way + xml |
| REQ-009 | First-response target selectable from contracted tier | `CustomField:Account.Support_Tier__c` | manifest two-way + xml |
| REQ-011 / REQ-012 | A page per record type, severity on Support only | both `Layout` files | checker exit 0 + manifest two-way + xml |

**Open at the gate — 6 rows** (`test_type: manual`, outstanding until a human ticks § 7):

| req_id | Requirement | Blocked on |
|---|---|---|
| REQ-003 | Support status ladder exposes `Escalated` | checklist line 2; Status values are a builder default (D-M1S01-01), not customer-confirmed |
| REQ-004 | Billing status ladder has no `Escalated` | checklist line 2, same |
| REQ-010 | A Tier 1 agent cannot open a Billing case | checklist line 3; rests on **A1** (risk `high`) from deferred **Q13** |
| REQ-013 | A hand-logged case runs the active assignment rule | checklist line 4; Q24 built in half (D-M1S02-03) |
| REQ-014 | Every field a validation rule errors on is visible | checklist line 5; **not checkable until M3-S01**; rests on **A13** (risk `medium`) from deferred **Q57** |

Requirements that reach into M1's artefacts but close in a later milestone: `Account.Support_Tier__c`
(M4-S02's entitlement process), `Account.Region__c` (M4-S03's calendar-stamping flow), `Case.Severity__c`
(M4-S04's 24/7 escalation entry), the `CaseOrigin` values (M3's Email-to-Case addresses and
`CaseSettings.webToCase.caseOrigin`), and `RecordTypeId` (M2-S05's criteria-based sharing rule). None is
asserted here, and none should be.

**Known gap in this section's own evidence:** `check_object_creation_and_design.py` exits 0 without
asserting anything about M1-S01's three fields — it returns before any assertion for a file stem not
ending `__c`, and `Case` is standard. So REQ-007, REQ-008 and REQ-009 are proved to *exist and be
manifest-consistent*, not to be *well-formed fields*. Recorded on workbook row CWB-OBJ-007 and repeated
here so the § 9 table is not read as stronger than it is.

---

## 10. Verdict, findings and confidence

### Verdict: `ready-with-findings`

| Verdict condition | Status |
|---|---|
| Unresolved reference | **none** — all 17 in-tree references resolved |
| Ordering contradiction | **none that breaks a deploy** — one recorded-position divergence (F-05), explained |
| Failing acceptance test | **none** — 2 of 2 executable tests exit 0, both matching their declared `expected` |
| Blocked step | **none** |

Eight findings, none blocking, all of which the human may accept at the gate:

| id | Severity | Finding | Fix owner |
|---|---|---|---|
| F-01 | HIGH | The record-type ↔ layout binding is asserted nowhere in M1, including by M1's own milestone test; 3 traceability rows and 4 workbook rows say otherwise | planner (v6) |
| F-03 | MEDIUM | Assumption A13's stated verification route (M1's milestone checker) does not exist | planner (v6) |
| F-04 | MEDIUM | `deploy-order.md` undeclared in `outputs[]` on both steps; feeds M5-S04's compile | planner (v6) — already `decisions.md` O-M1S02-02 |
| F-08 | MEDIUM | Both `deploy-order.md` files print `sf project deploy validate` against a sandbox alias | `metadata-builder` |
| F-05 | LOW | `CustomObject:Case` recorded at position 7 (sharing) with no position-1 row | doc keeper / planner (v6) |
| F-07 | LOW | The milestone test's `description` predicts `0 finding(s)`; the run gives 2 INFO | planner (v6) |
| F-02 | INFO | Business-process Status values resolve only against the target org's `CaseStatus` (A28, by design) | pre-deploy check, § 8 |
| F-06 | INFO | API version `62.0` defaulted by the owning agent twice; the plan carries no `api_version` | planner (v6) |

**F-01 is the finding the gate is really for.** Nothing is broken and nothing fails, but seven
statements across the plan, the traceability matrix and the workbook assert a cross-reference check
that was not made and could not have been made. A reader trusting those statements would believe M1
proved more than it did.

### Confidence: **MEDIUM**

Per the Step 10 table. Every step was documented, the merged manifest built with no conflict, and every
declared acceptance test existed and ran — which would support HIGH. It is MEDIUM because **the
reference class this milestone exists to close was not fully classifiable**: the record-type ↔ layout
binding had zero references to resolve (no `Profile` in the tree, F-01), and the business-process Status
references resolve only outside the tree (F-02). Neither is a failure; both mean a load-bearing check
was reported rather than made.

---

## 11. What the human decides at G3

1. **Accept F-01, or re-plan.** The milestone test does not carry the assertion its description claims.
   Accepting means accepting that record-type ↔ layout consistency in M1 rests on a naming convention
   (2 record types, 2 layouts, 1:1 by name) plus the member forms `M1-S02/deploy-order.md` records for
   M2-S01 to reuse.
2. **Checklist line 1, clause (c):** accept `Reason` value sets as absent-and-documented, or rule the
   clause unanswerable and reword it at v6.
3. **Checklist line 4:** accept Q24 built in half — the checkbox is *shown*, not *defaulted on* — or
   commission a recorded Setup step, or deepen the skill.
4. **Checklist line 5 / REQ-014:** accept that A13 (risk `medium`, from deferred Q57) is unverified and
   stays unverified until M3-S01 lands.
5. **REQ-010 / assumption A1 (risk `high`, from deferred blocking Q13):** the Private OWD is on disk and
   correct; the *policy* it encodes is still the conservative reading of a deferred question. The
   `step:M1-S01` gate note already says a real deployment needs the security owner's signature.
6. **Before any deploy:** the `StandardValueSet:CaseStatus` reconciliation in § 8 is the one blocking
   pre-deploy item M1 carries.

Approving `milestone:M1` accepts findings F-01 through F-08 as recorded, and accepts that the five
manual lines in § 7 were ticked on the readings § 7 states — not on their literal wording, in the case
of lines 1, 4 and 5.

---

## 12. Recorded verdict, and the gate command

The verdict and this report's path were recorded with the one plan write this agent makes:

```bash
python3 scripts/build_plan.py set-milestone \
  .sfskills/builds/case-onboarding/plan.json M1 \
  --status verified \
  --report-path reports/MILESTONE-M1-REPORT.md
```

`--status verified` is a statement about what the checks found, **not an approval**.
`milestones[].status` and `report_path` are plan bookkeeping; the gate record stays empty until a human
writes it.

The gate command — **for a human to run. This agent did not run it and will not.**

```bash
python3 scripts/build_plan.py gate \
  .sfskills/builds/case-onboarding/plan.json milestone:M1 approve \
  --by "<name>"
```

`standards/build-orchestration.md` § 3 refuses that command unless the `plan` gate is `approved` (it is)
and every step in M1 is `documented` or blocked with a recorded reason (both are `documented`). There is
no `milestone:M0`, so the predecessor condition is vacuous. No blocked step means approving accepts no
known gap of that kind — the gaps this milestone carries are the eight findings and the three narrowed
manual lines above.

To reject instead: `… gate .../plan.json milestone:M1 reject --by "<name>" --notes "<why>"`, which sets
M1's status to `rejected` and leaves the build at `building`.
