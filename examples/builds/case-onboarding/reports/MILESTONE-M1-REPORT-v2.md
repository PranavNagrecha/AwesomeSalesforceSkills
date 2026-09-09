# M1 — Case data model and record-type layouts · acceptance report **v2 (re-verification)**

**Build:** `case-onboarding` · **plan version:** 5 · **plan status:** `building` · **build_mode:** `design-only`
**Written by:** `agents/milestone-verifier/AGENT.md` (Step 9) — this document is *written*, not rendered
(`standards/build-orchestration.md` § 2).
**Date:** 2026-09-09 · **Run:** `2026-09-09T20-19-00Z` · **Verdict:** `ready-with-findings` · **Confidence:** MEDIUM

> **This report does not replace v1.** `reports/MILESTONE-M1-REPORT.md` stays on disk exactly as
> written on 2026-09-05. It is the document the human read before approving `milestone:M1` at
> 2026-09-05T21:11:56Z, and overwriting it would erase the record of what that approval was taken
> against. This is a second report about the same milestone after its artefacts changed.

> **G3 is the human's.** This agent neither approved nor re-approved any gate, and did not deploy.
> The gate command is in § 12, unrun. The `milestone:M1` gate record in `plan.json.human_gates[]` is a
> written record of a human's decision and is not rewritable by any agent — this report corrects the
> record around it, never the record itself.

---

## 0. Why this report exists, and what changed under the accepted milestone

`milestone:M1` was approved on **2026-09-05** against **build #1**. Since then:

| When | What happened | Where it is recorded |
|---|---|---|
| 2026-09-05 | Mock deploy #1: the build #1 artefacts validated against `sfskills-dev` with `--dry-run`. **10 of 12 components passed**; seven runs of one-fix-at-a-time exposed **F-09, F-10, F-11** | `reports/MOCK-DEPLOY-M1.md` runs 1–7 |
| 2026-09-09 | Two skills fixed at the source: `admin/record-types-and-page-layouts` **v1.2.0** (rules **RL-REQ-01 / RL-REQ-02**) and `admin/case-management-setup` **v1.2.0** (rules **CMS-STEM-01 / CMS-STEM-02**) | `decisions.md` D-M1S02-05, D-M1S01-05 |
| 2026-09-09 | **Rebuild #2** of both M1 steps through the ordinary runner path (`documented → running → built → tested → documented`), re-tested and re-documented | `envelopes/M1-S01/2026-09-09T*`, `envelopes/M1-S02/2026-09-09T*`; `tests/M1-S01/`, `tests/M1-S02/` |
| 2026-09-09 | Mock deploy #2: the rebuilt artefacts, copied **unmodified**, validated **12 of 12 components**, `checkOnly: true`, 0 errors | `reports/MOCK-DEPLOY-M1.md` § "Mock deploy #2" |

`standards/build-orchestration.md` § 4 is explicit about the consequence: a rebuild "leaves the
milestone above it stale until `/verify-milestone` is re-run". That is this run.

### Precondition checks

| Check | Result |
|---|---|
| Every step in M1 is `documented` | `M1-S01` **documented**, `M1-S02` **documented** — both after rebuild #2 |
| Blocked steps | **none** — § 3's blocked-with-a-reason carve-out is not in play |
| Preceding milestone gate `approved` | n/a — M1 is the first milestone. The `plan` gate is `approved` (2026-09-05T19:35:19Z) and `step:M1-S01` is `approved` (2026-09-05T19:35:41Z) |
| M1's own gate | already `approved` (2026-09-05T21:11:56Z) — **against build #1**. See § 12 and finding **F-12** |

### What the artefacts on disk actually are now

Twelve files changed or stayed, and the split matters because it bounds how much of the v1 report
survives:

| File | Rebuild #2 | mtime |
|---|---|---|
| `M1-S01/.../businessProcesses/Support_Process.businessProcess-meta.xml` | `<fullName>` → `Support_Process` | 2026-09-09 |
| `M1-S01/.../businessProcesses/Billing_Process.businessProcess-meta.xml` | `<fullName>` → `Billing_Process` | 2026-09-09 |
| `M1-S01/.../recordTypes/Support.recordType-meta.xml` | `<businessProcess>` → `Support_Process` | 2026-09-09 |
| `M1-S01/.../recordTypes/Billing.recordType-meta.xml` | `<businessProcess>` → `Billing_Process` | 2026-09-09 |
| `M1-S01/package.xml` | `BusinessProcess` members → `Case.Support_Process`, `Case.Billing_Process` | 2026-09-09 |
| `M1-S01/deploy-order.md` | rewritten, gained a **Rebuild history** section | 2026-09-09 |
| `M1-S02/layouts/Case-Case Support Layout.layout-meta.xml` | `+ContactId +Description +SuppliedEmail`, `Status` → `behavior=Required` | 2026-09-09 |
| `M1-S02/layouts/Case-Case Billing Layout.layout-meta.xml` | same three fields, same `Status` change | 2026-09-09 |
| `M1-S02/deploy-order.md` | rewritten | 2026-09-09 |
| `M1-S01/objects/Case/Case.object-meta.xml`, the `CaseOrigin` value set, the compact layout, the three fields, `record-type-decision.md` | **unchanged, byte-identical to build #1** | 2026-09-05 |

The last row is where **F-14** lives: `record-type-decision.md` is a declared output and the document
manual checklist line 1 asks the human to read, and it was not touched by a rebuild that changed what
it describes.

---

## 1. The milestone and its artefacts

**Goal (from `plan.json`):** given a greenfield org with no existing Case records (Q4), when the Case
model is deployed, then two record types with their Support Processes, the three active Origin values
and one layout per record type exist, and every field the routing and SLA milestones reference resolves.

### M1-S01 — `object-model`, owner `metadata-builder`, `human_gate: true` (approved)

| Artefact | Type · member (post-rebuild) | Declared in `outputs[]` |
|---|---|---|
| `standardValueSets/CaseOrigin.standardValueSet-meta.xml` | StandardValueSet · `CaseOrigin` | yes |
| `objects/Case/Case.object-meta.xml` | CustomObject · `Case` | yes |
| `objects/Case/businessProcesses/Support_Process.businessProcess-meta.xml` | BusinessProcess · **`Case.Support_Process`** | yes |
| `objects/Case/businessProcesses/Billing_Process.businessProcess-meta.xml` | BusinessProcess · **`Case.Billing_Process`** | yes |
| `objects/Case/recordTypes/Support.recordType-meta.xml` | RecordType · `Case.Support` | yes |
| `objects/Case/recordTypes/Billing.recordType-meta.xml` | RecordType · `Case.Billing` | yes |
| `objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml` | CompactLayout · `Case_Intake` | yes |
| `objects/Case/fields/Severity__c.field-meta.xml` | CustomField · `Case.Severity__c` | yes |
| `objects/Account/fields/Region__c.field-meta.xml` | CustomField · `Account.Region__c` | yes |
| `objects/Account/fields/Support_Tier__c.field-meta.xml` | CustomField · `Account.Support_Tier__c` | yes |
| `record-type-decision.md` | — (document) | yes |
| `package.xml` | — (manifest) | yes |
| `deploy-order.md` | — (document) | **no — F-04, still open** |

### M1-S02 — `ui`, owner `metadata-builder`, `depends_on: [M1-S01]`, `human_gate: false`

| Artefact | Type · member | Declared in `outputs[]` |
|---|---|---|
| `layouts/Case-Case Support Layout.layout-meta.xml` | Layout · `Case-Case Support Layout` | yes |
| `layouts/Case-Case Billing Layout.layout-meta.xml` | Layout · `Case-Case Billing Layout` | yes |
| `package.xml` | — (manifest) | yes |
| `deploy-order.md` | — (document) | **no — F-04, still open** |

---

## 2. Symbol inventory (Step 2)

M1 is the first milestone, so there is no earlier-milestone inventory to inherit. Everything below is
defined *by this milestone*:

| Class | Symbols | Defined by |
|---|---|---|
| Objects | `Case` (standard — the file carries OWD + compact-layout assignment, it does not create the object) | M1-S01 |
| Fields | `Case.Severity__c`, `Account.Region__c`, `Account.Support_Tier__c` | M1-S01 |
| Picklist values | `Case.Severity__c`: `Severity 1` · `Account.Region__c`: `EMEA`, `US` · `Account.Support_Tier__c`: `Premier`, `Standard` | M1-S01 |
| Value sets | `StandardValueSet:CaseOrigin` → `Email-Support`, `Email-Billing`, `Web` (`Web` is `<default>true</default>`) | M1-S01 |
| Record types | `Case.Support`, `Case.Billing` (both `active`) | M1-S01 |
| Business processes | **`Support_Process`** (New/Escalated/Closed), **`Billing_Process`** (New/Closed), both `isActive` — stems, `fullName`s and record-type references now agree character-for-character | M1-S01 |
| Compact layouts | `Case_Intake` | M1-S01 |
| Layouts | `Case-Case Support Layout`, `Case-Case Billing Layout` | M1-S02 |
| Queues, groups, permission sets, business hours, milestone types, entitlement processes, Flows | **none in M1** | — |

Two boundary statements, made rather than assumed:

- `Account` is not in the inventory and is not a manifest member. Two `CustomField` members are
  object-qualified to it; `Account` is a standard object that pre-exists in any target org.
- One artefact from a **later** milestone now sits under `artefacts/` —
  `M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml`, plus its custom permission.
  Per Step 2 later milestones do **not** count as defining, so nothing in M1 resolves against them.
  They do change what the build-scoped checker sweeps; see **F-01** and **F-07**.

---

## 3. Reference resolution (Step 3)

The table states which reference classes were resolved, so the boundary of the check is visible rather
than inferred from silence.

| Reference class | Read from | Refs | Resolved in M1 | Resolved earlier | Unresolved | Unclassifiable |
|---|---|---|---|---|---|---|
| Validation rule field references | `.validationRule` `<errorConditionFormula>` / `<errorDisplayField>` | **0** — no ValidationRule metadata exists (M3-S01 `pending`) | — | — | — | — |
| Assignment rule criteria | `<criteriaItems>/<field>`, `<assignedTo>` | **0** — no AssignmentRules in M1 (M3-S03/S04) | — | — | — | — |
| Permission set grants | `<fieldPermissions>/<field>`, `<objectPermissions>/<object>` | **0** — M2-S01's permission set grants a **custom permission only**, no object or field permissions | — | — | — | — |
| Flow field references | `<field>`, `<object>`, lookup/update filters, formula merge fields | **0** — no Flow in M1 (M4) | — | — | — | — |
| Entitlement process milestones | `<milestoneType>/<milestoneName>`, business hours named | **0** — no EntitlementProcess in M1 (M4) | — | — | — | — |
| **Layout, compact-layout, record-type and business-process references** | both `Layout` files, the `CompactLayout`, both `RecordType` blocks, both `BusinessProcess` files, the object's `compactLayoutAssignment` | **43** | **10** | 0 | **0** | **5** (F-02) |

### The 43 references, in full

Counts were taken from the files, not from the v1 report — the rebuild added six layout field
references (three per layout), so v1's total of 17 no longer describes the tree.

| # | Class | Count | Where they point | Outcome |
|---|---|---|---|---|
| 1 | Layout field references | **23** (Support 12, Billing 11) | `Severity__c` ×1 (Support only); `SuppliedEmail`, `Description`, `ContactId`, `Subject`, `Priority`, `Origin`, `CaseNumber`, `Status`, `OwnerId`, `CreatedById`, `LastModifiedById` | 1 resolves to M1-S01; **22 standard, treated as pre-existing** |
| 2 | Compact-layout field references | **5** | `CaseNumber`, `Status`, `Priority`, `Origin`, `Severity__c` | 1 resolves to M1-S01; 4 standard |
| 3 | `<picklist>` names inside `picklistValues` | **2** | `Origin` on both record types | standard `Case.Origin` |
| 4 | `compactLayoutAssignment` | **3** | `Case_Intake` from `CustomObject:Case`, `RecordType:Case.Support`, `RecordType:Case.Billing` | **3 resolve in M1-S01** |
| 5 | `<businessProcess>` on record types | **2** | `Support_Process`, `Billing_Process` — bare file stems | **2 resolve in M1-S01**, and now enforced by **CMS-STEM-02** |
| 6 | Origin values exposed by record types | **3** | `Email-Support`, `Web` (Support); `Email-Billing` (Billing) | **3 resolve to `StandardValueSet:CaseOrigin`** |
| 7 | Business-process `Status` values | **5** | `New`, `Escalated`, `Closed`; `New`, `Closed` | **unclassifiable in-tree** — F-02 |

**Totals: 43 references · 10 resolved in M1 · 0 resolved in an earlier milestone · 28 standard-and-pre-existing · 5 unclassifiable-in-tree · 0 unresolved.**

Every one of the three `CaseOrigin` values is exposed on at least one record type; none is orphaned.
Treating the 28 standard-field references as pre-existing is a **stated assumption of this check**, not
a silent pass — and it is the assumption mock deploy #1 falsified in one direction and mock deploy #2
confirmed in the other: three of them (`ContactId`, `Description`, `SuppliedEmail`) are not merely
*allowed* on a Case layout, they are **required** on it, which no in-tree check could have known.

---

## 4. Deployment order (Step 4)

The milestone sequence is: objects → fields → picklists → record types → layouts → permission sets →
sharing → automation → routing → SLA. Positions are the ones `build-doc-keeper` recorded on each
workbook row; "agrees" is this agent's check.

| Artefact | Recorded position | Position by artefact type | Agrees | Workbook row |
|---|---|---|---|---|
| `CustomField:Case.Severity__c` | 2 of 10 (fields) | 2 | yes | CWB-OBJ-007 |
| `CustomField:Account.Region__c` | 2 of 10 | 2 | yes | CWB-OBJ-008 |
| `CustomField:Account.Support_Tier__c` | 2 of 10 | 2 | yes | CWB-OBJ-009 |
| `StandardValueSet:CaseOrigin` | 3 of 10 (picklists) | 3 | yes | CWB-OBJ-001 |
| `BusinessProcess:Case.Support_Process` | 4 of 10, with record types | no slot of its own in the sequence | yes — reported, not invented | CWB-OBJ-002 |
| `BusinessProcess:Case.Billing_Process` | 4 of 10, with record types | no slot of its own | yes | CWB-OBJ-003 |
| `RecordType:Case.Support` | 4 of 10 (record types) | 4 | yes | CWB-OBJ-004 |
| `RecordType:Case.Billing` | 4 of 10 (record types) | 4 | yes | CWB-OBJ-005 |
| `CompactLayout:Case_Intake` | **cannot be placed** — reported | no slot: a compact layout is not a page layout | yes — reported, not invented | CWB-OBJ-006 |
| `Layout:Case-Case Support Layout` | 5 of 10 (layouts) | 5 | yes | CWB-LAYOUT-001 |
| `Layout:Case-Case Billing Layout` | 5 of 10 (layouts) | 5 | yes | CWB-LAYOUT-002 |
| `CustomObject:Case` | **7 of 10 (sharing)** | **1 (objects)** | **divergence — F-05, unchanged** | CWB-SHARE-001 |

### Backwards-dependency check

Every dependency runs forward through the sequence. Nothing runs backwards:

| Dependency | Direction |
|---|---|
| both layouts (5) → `Case.Severity__c` (2) | forward — the field lands before the layout naming it |
| `RecordType` (4) → `BusinessProcess` (4, internal 3 before 5) | forward — a Case record type is rejected without its process |
| `RecordType` (4) → `CompactLayout` (internal 4 before 5) | forward |
| `CustomObject:Case` `compactLayoutAssignment` → `CompactLayout` | forward within the step |
| `RecordType` `picklistValues` (4) → `StandardValueSet:CaseOrigin` (3) | forward — a `picklistValues` block exposes values, it does not create them |

**Permission-set ordering** (`skills/devops/permission-set-deployment-ordering`): positions 6–7 are
empty in M1. There is no `fieldPermissions` entry anywhere in this milestone — including in M2-S01's
permission set, which grants a `customPermissions` entry and nothing else — so the failure that skill
exists to catch cannot occur here. It becomes live at M2-S02, which grants against the three fields M1
defines; the ordering requirement is that M1 deploys first, which the sequence already encodes.

**Flow / automation ordering** (`skills/devops/flow-deployment-activation-ordering`): positions 8–10 are
empty in M1. No Flow, no activation state, no paused-interview exposure. Not applicable this milestone.

**Ordering verdict: no contradiction that breaks a deploy.** One recorded-position divergence (F-05),
explained below and unchanged since v1. Corroborated externally: mock deploy #2 validated all 12
components in a single atomic request, which exercises the manifest's internal consistency but — being
one request — proves nothing about the *sequence* if the components were ever split across deploys.

---

## 5. Merged manifest (Step 5) — **regenerated, members changed**

**Path:** `reports/MILESTONE-M1-package.xml` — regenerated this run. 7 `<types>` blocks, 12 members,
members sorted within each block, one `<version>`.

**Two members changed** and the file on disk was stale before this run:

| Type | v1 members | v2 members |
|---|---|---|
| `BusinessProcess` | `Case.Billing Process`, `Case.Support Process` | **`Case.Billing_Process`, `Case.Support_Process`** |

Full member table:

| Type | Members | From |
|---|---|---|
| `BusinessProcess` | `Case.Billing_Process`, `Case.Support_Process` | M1-S01 |
| `CompactLayout` | `Case_Intake` | M1-S01 |
| `CustomField` | `Account.Region__c`, `Account.Support_Tier__c`, `Case.Severity__c` | M1-S01 |
| `CustomObject` | `Case` | M1-S01 |
| `Layout` | `Case-Case Billing Layout`, `Case-Case Support Layout` | M1-S02 |
| `RecordType` | `Case.Billing`, `Case.Support` | M1-S01 |
| `StandardValueSet` | `CaseOrigin` | M1-S01 |

| Merge check | Result |
|---|---|
| API version agreement | **agree** — both step manifests carry `<version>62.0</version>`; one `<version>` written, no conflict, no `REFUSAL_NEEDS_HUMAN_REVIEW` |
| Member appearing in two steps | **none** — the two step manifests are type-disjoint |
| Wildcard members | **none** — every member explicit, the CI-safe form `skills/devops/metadata-api-retrieve-deploy` prescribes |
| File under the milestone's artefacts reaching no `<types>` block | **4**: `M1-S01/deploy-order.md`, `M1-S01/record-type-decision.md`, `M1-S02/deploy-order.md` (documents, correctly carry no member — but see F-04), plus the two step `package.xml` files, which are the manifests themselves |
| Merged manifest parses | yes |
| `<version>` present | yes, `62.0` (F-06 — defaulted, never decided) |

Evidence: `tests/M1/manifest.v2.{stdout,stderr,exit}`.

---

## 6. Acceptance-test results (Step 6)

Run **from the build directory**, at build scope — `standards/build-orchestration.md` § 5: "At
milestone level the scope is always `build`." Commands run **verbatim** as the plan declares them; no
flag added, removed or re-ordered, and no path substituted. Evidence under `tests/M1/*.v2.*`, written
beside the v1 evidence rather than over it.

| # | Type | Command / runner | Exit | Expected | Result |
|---|---|---|---|---|---|
| 1 | `checker` | `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts` | **0** | `exit 0` | **PASS** |
| 2 | `manifest` | two-way member ↔ file over the merged milestone manifest | **0** | `consistent` | **PASS** — `verdict: consistent \| failures: 0` |
| 3 | `manual` | — | n/a | ticked at the gate | **deferred to § 7** |

Every declared milestone test exists and ran. **No declared checker was missing.**

Test 1 output, in full — and this is a change from v1:

```json
{
  "score": 100,
  "findings": [],
  "summary": "Scanned 8 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected."
}
```

stderr: empty. v1's run printed `2 finding(s)`, both `INFO` ("marks no field behavior=Required"). Both
are gone because rebuild #2 set `Status` to `behavior=Required` on both layouts — which the platform
requires anyway (**RL-REQ-02**). See **F-07**.

### Additional run — observation only, not a declared test

`python3 skills/admin/case-management-setup/scripts/check_case_management_setup.py --manifest-dir artefacts`
→ **exit 0**, `No case management setup issues found.`
(`tests/M1/OBSERVATION-check_case_management_setup.v2.{stdout,stderr,exit}`)

This carries rules **CMS-STEM-01 / CMS-STEM-02**, added 2026-09-09, which are the enforcement of F-11.
It is **not** one of M1's declared `acceptance_tests[]` and did not contribute to any pass verdict. Its
absence from the declared set is a v6 planner item — see § 10, carry-forward item 3.

### Negative controls — proving the green is earned, not fail-open

The lesson of **F-01** is that a checker can be silent about a check it never made, and silence reads
as clean. Both new rule families were therefore run against fixtures reverted to the pre-fix shape
(copies written outside the build directory; the build's own artefacts were not touched):

| Fixture | Checker | Result |
|---|---|---|
| Case layout with `ContactId` / `Description` / `SuppliedEmail` removed and `Status` set to `behavior=Edit` | `check_record_type_layouts.py` | **exit 1** — `RL-REQ-01 … has no layoutItems entry for ContactId, Description, SuppliedEmail`; `RL-REQ-02 … sets Status behavior='Edit'`; plus the old `marks no field behavior=Required` INFO |
| `Support_Process.businessProcess-meta.xml` whose `<fullName>` reads `Support Process`, with the record type referencing the spaced form | `check_case_management_setup.py` | **exit 1** — `CMS-STEM-01 … <fullName> is 'Support Process' but the file stem is 'Support_Process'`; `CMS-STEM-02 … names 'Support Process', which is not the stem of any *.businessProcess-meta.xml in this tree` |

Full output: `tests/M1/NEGATIVE-CONTROLS.v2.stdout`. **The two exit-0 runs above are therefore
statements, not silences.**

---

## 7. Manual checklist for the human (Step 7)

Five lines, from `tests/M1-S01/results.json` `skipped_manual[]` (2), `tests/M1-S02/results.json`
`skipped_manual[]` (1, two halves) and M1's own `manual` acceptance test (1). Each names the step it
came from, what the human does, and what counts as a tick. **No line is ticked by this agent.**

All five were already ticked or narrowed at the 2026-09-05 gate **against build #1**. The evidence
below is re-gathered from the artefacts on disk today, so a human re-reading them is confirming the
current tree rather than the one they saw.

---

### ☐ 1 — M1 (milestone) · `record-type-decision.md` states its own provenance

**Do:** read `artefacts/M1-S01/record-type-decision.md`.
**Ticks when** all three clauses hold: (a) it states the record-type count was decided in the plan, not
by the builder; (b) it names D5's criteria-based sharing rule on `RecordTypeId` as what settled Q1's
conditional; (c) it shows the Status **and Reason** value sets for each of the two processes.

**Evidence on disk (re-read this run; the file is byte-identical to build #1, mtime 2026-09-05):**
- (a) holds — § 1: "Assumption **A26** resolves that conditional in favour of two".
- (b) holds — § 1, verbatim: "because decision D5's criteria-based sharing rule keys on `RecordTypeId`".
- (c) **half.** Status is shown (§ 2 table). **Reason is not, and cannot be:** § 2 records that
  "`Case.Reason` is named in Q1's answer and is **not** configured here — no clarification enumerates
  its values".

> **Unchanged from v1: not fully tickable as worded.** Accept the narrowing, or rule clause (c) asks
> for something the build was never given the input to produce.
>
> **New at v2 — F-14.** § 2 of this document still spells the two processes `` `Support Process` ``
> and `` `Billing Process` `` in code formatting, which is the **pre-rebuild** form. The API names are
> now `Support_Process` and `Billing_Process`. The wording itself is defensible —
> `case-management-setup` v1.2.0 § 2.1 says the readable form belongs in `<description>`, and the
> builder raised exactly this — but nothing on the page tells the reader which of the two strings is
> the API name, and this is the one document the milestone's own manual test sends a human to read.

---

### ☐ 2 — M1-S01 · Business processes exist beside the record types, with the right name forms

**Do:** list `artefacts/M1-S01/`.
**Ticks when** two `businessProcess-meta.xml` files sit beside the two `recordType-meta.xml` files, each
record type's `<businessProcess>` carries the **bare** process name (not `Case.Support Process`), and
`package.xml` lists `BusinessProcess` with **object-qualified** members.

**Evidence on disk** (`tests/M1-S01/manual-evidence.stdout`, re-confirmed by this agent):
- businessProcess files: `Billing_Process.businessProcess-meta.xml`, `Support_Process.businessProcess-meta.xml` — present
- recordType files: `Billing.recordType-meta.xml`, `Support.recordType-meta.xml` — present
- `Support.recordType` → `<businessProcess>Support_Process</businessProcess>` — **bare stem**, no `Case.` prefix
- `Billing.recordType` → `<businessProcess>Billing_Process</businessProcess>` — bare stem
- `package.xml` `BusinessProcess` members: `Case.Billing_Process`, `Case.Support_Process` — object-qualified

**All four clauses hold. This is a straight tick — and it is now machine-backed as well:**
`CMS-STEM-01` and `CMS-STEM-02` assert exactly these two properties, exit 0 on this tree and exit 1 on
the reverted fixture (§ 6). A manual line that has acquired a checker is a candidate for promotion at v6.

> **Caveat the human should read before ticking (O-M1S01-02):** the parenthetical counter-example
> "(not `Case.Support Process`)" is stale. It was written to exclude one wrong shape —
> object-qualified where bare is required. After rebuild #2 that string is wrong on *two* counts at
> once, and the shape it meant to exclude is now spelled `Case.Support_Process`. The assertion holds;
> the example inside it names a string nobody would now write. This line was ticked at the 2026-09-05
> gate against the *old* reading.

---

### ☐ 3 — M1-S01 · The Case org-wide default is Private, and only the object file carries it

**Do:** read `artefacts/M1-S01/objects/Case/Case.object-meta.xml`.
**Ticks when** it carries `<sharingModel>Private</sharingModel>` and
`<externalSharingModel>Private</externalSharingModel>` as **direct children of `<CustomObject>`**, and
no separate settings file anywhere in the build claims to carry the OWD.

**Evidence on disk** (`tests/M1-S01/manual-evidence.stdout`, re-confirmed):
- root tag `CustomObject`; direct children `sharingModel: Private`, `externalSharingModel: Private`, plus `compactLayoutAssignment: Case_Intake`
- `*.settings-meta.xml` anywhere under `artefacts/`: **none**
- other files containing `<sharingModel>`: only the two prose documents and the object file itself

**All clauses hold — a straight tick. The file is byte-identical to build #1**, so the 2026-09-05 tick
still stands against the artefact on disk today.

> **What the tick does not cover, unchanged:** the OWD is the conservative reading of deferred
> **blocking** question **Q13** through assumption **A1** (`risk: high`). The machine assertion that
> the OWD is not looser than the sharing rule's grant is `M2-S05`'s build-scoped
> `check_sharing_model.py` test, which needs both files and has not run. Approving this line approves
> the *artefact*, not the *policy*.

---

### ☐ 4 — M1-S02 · The assignment-rule checkbox is on both layouts (Q24)

**Do:** read both layout files.
**Ticks when** `<layoutSections>` is preceded by the assignment-rule checkbox, default set on.

**Evidence on disk** (`tests/M1-S02/manual-evidence.stdout`, re-captured after rebuild #2):

| Reading | Billing layout | Support layout |
|---|---|---|
| `<showRunAssignmentRulesCheckbox>` present, value `true` — **presence** | true | true |
| checkbox precedes `<layoutSections>` — **positional, the test's literal words** | fails (index 3 vs last `layoutSections` at index 1) | fails, same |
| any element that **pre-checks** the box | none present | none present |

Both layouts' child order: `layoutSections, layoutSections, showEmailCheckbox,
showRunAssignmentRulesCheckbox, showKnowledgeComponent`.

**Unchanged by the rebuild, in both halves, and that is the point worth reading:**

1. **The positional reading fails on both layouts and should.** The cited skill's own example places
   every `show*` element after the final `</layoutSections>`, and both artefacts match it exactly. The
   tester applied the **presence** reading and recorded why (`decisions.md` D-M1S02-03). The test's
   wording, not the artefacts, is what is off.
2. **Q24's "defaulted on" half remains unproven and unprovable from the artefacts.**
   `<showRunAssignmentRulesCheckbox>` controls whether the checkbox is *shown*. `record-types-and-page-layouts`
   **v1.2.0** — the release that fixed F-09 and F-10 — **added no element that pre-checks it**
   (`decisions.md` D-M1S02-03, as amended 2026-09-09). So the skill deepening that closed two HIGH
   findings did not close this one, and there is now positive evidence that the element was looked for
   rather than merely not found.
3. **The gate must still choose:** accept the narrowing (the checkbox is shown; agents tick it
   manually), route the remainder to a recorded Setup step for a human, or deepen the skill further.

---

### ☐ 5 — M1-S02 · Every field a validation rule errors on is on both layouts (A13)

**Do:** read both layout files against the validation rules.
**Ticks when** every field a validation rule attaches its error to (assumption **A13**) is present on
both layouts.

**Evidence on disk** (`tests/M1-S02/manual-evidence.stdout`, re-captured after rebuild #2):
- `ValidationRule` files anywhere under `artefacts/`: **none**. `M3-S01` (type `validation`) is `pending`.
- Fields on **both** layouts: `CaseNumber`, `ContactId`, `CreatedById`, `Description`,
  `LastModifiedById`, `Origin`, `OwnerId`, `Priority`, `Status`, `Subject`, `SuppliedEmail` — **11, up
  from 8 before the rebuild**
- On the **Support layout only**: `Severity__c`

> **Still not file-checkable at M1, and should not be ticked as verified.** `Priority` and `Origin`
> are on both layouts, which is what A13 needs for the two rules M3-S01 *declares*
> (`Priority_Required_On_Agent_Save`, `Origin_Must_Be_Known`) — but those rules do not exist yet, so
> that is a prediction, not a check.
>
> **What the rebuild changed, in A13's favour:** `ContactId`, `Description` and `SuppliedEmail` are now
> on **both** layouts, so a future rule attaching its error to any of the three would satisfy A13 on
> both. The satisfied surface widened from 8 fields to 11.
>
> **Carry-forward, unchanged:** `Severity__c` is on the Support layout only, by design (D-M1S02-02), so
> a third Case validation rule attaching its error to `Severity__c` would break A13 on the Billing
> layout. A13's risk is `medium` and Q57 is deferred. See also **F-03**: the plan text claims this
> assertion is carried by M1's milestone checker, and it is not.

---

**Tick summary.** Lines 2 and 3 are straight ticks against evidence gathered from today's artefacts —
and line 2 is now additionally machine-asserted. Line 1 is tickable in two clauses of three, with a new
staleness caveat (F-14). Line 4 needs a decision, not a tick, and the skill fix that closed F-09/F-10
did not close it. Line 5 is not verifiable in this milestone at all and should be carried to M3.

---

## 8. Optional validate-only command — **for the human, and this agent did not run it**

`plan.json.build_mode` is `design-only` and no org alias is on file, so the alias below is a
placeholder the human replaces. The target is a **sandbox** — the requirement is explicit ("we must be
able to prove it works in a sandbox before customers see it") and M5's goal names the sandbox proof.

For a sandbox the validate-only form is a **dry run of a deploy** — it compiles and validates without
saving:

```bash
sf project deploy start \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M1-package.xml \
  --dry-run --target-org <your-sandbox-alias>
```

**Optional. Human-run. `agents/milestone-verifier` never runs `sf`, and did not run this.**

For a **production** target — and only production — the command is instead `sf project deploy validate`
with the same manifest: Salesforce documents it as production-only, it requires Apex tests, and it
returns a job id redeemable by `sf project deploy quick` within 10 calendar days.

> **This is not the command the two mock deploys ran.** Both used
> `sf project deploy start --source-dir force-app --dry-run`, which makes the CLI derive the components
> from a source tree and never open a `package.xml` at all. The `--manifest` form above has **never**
> been run against this build. That distinction is what **F-13** is about.

### Go / no-go items before any deploy of this manifest

Per `skills/devops/pre-deployment-checklist`'s gate list, restricted to what this build can see:

- [ ] **Dependency completeness — `StandardValueSet:CaseStatus`.** F-02. **Partly discharged:**
      both mock deploys validated the two business processes against `sfskills-dev`, so *that* org's
      `CaseStatus` carries `New`, `Escalated` and `Closed`. It says nothing about any other target.
      Re-check per target org.
- [ ] **`CompactLayout` member form.** `Case_Intake`, bare, in the merged manifest. The only deploys
      ever run derived the component from the source tree and named it **`Case.Case_Intake`**,
      object-qualified. Nothing has compared the two. **F-13** — this is the one member a
      `--manifest` deploy would exercise first.
- [ ] **Business-process member form.** `Case.Support_Process` / `Case.Billing_Process`. **Discharged
      by mock deploy #2** for the source-tree path; the manifest path shares F-13's caveat.
- [ ] **Pre-release backup.** Not applicable — greenfield Case model, no existing Case records (Q4),
      `design-only` means nothing has been deployed. Checked-and-not-applicable, not skipped.
- [ ] **Post-deploy manual steps.** Nothing in M1 makes record types selectable
      (`recordTypeVisibilities` is `M2-S02`'s) or assigns either layout (`layoutAssignments` is
      **`M2-S03`**'s — see F-01). **M1 deploys cleanly and is not reachable by any user until M2
      lands.** Expected; recorded so it is not mistaken for a defect.
- [ ] **Test level / coverage.** Not applicable — no Apex in M1.
- [ ] **Deployment window.** The human's call; nothing in the build can see it.

---

## 9. Requirement closure (Step 9)

From `traceability.md`, which uses the build-layer RTM schema of
`skills/admin/requirements-traceability-matrix` § "The Build-Layer RTM". M1 carries 14 rows,
`REQ-001`–`REQ-014`. (`REQ-015`/`REQ-016` are M2-S01's and are not asserted here.)

**Closed by machine evidence in M1 — 8 rows** (test type `checker` or `manifest`, all passing):

| req_id | Requirement | Artefact | Proved by |
|---|---|---|---|
| REQ-001 | Support work is a case process of its own | `RecordType:Case.Support` | checker + manifest + xml; `<businessProcess>` now additionally covered by CMS-STEM-02 |
| REQ-002 | Finance queries are a case process of their own | `RecordType:Case.Billing` | same run |
| REQ-005 | Each intake channel stamps an Origin value; no phone value | `StandardValueSet:CaseOrigin` | manifest two-way; values re-checked as exposed on the record types |
| REQ-006 | Case identity and state at a glance on every record type | `CompactLayout:Case_Intake` | `check_list_views_and_compact_layouts.py` exit 0, covering both assignment scopes |
| REQ-007 | A Severity 1 outage is identifiable on the Case | `CustomField:Case.Severity__c` | manifest two-way + xml; named by the compact layout and the Support layout |
| REQ-008 | SLA calendar resolvable from the account's region | `CustomField:Account.Region__c` | manifest two-way + xml |
| REQ-009 | First-response target selectable from contracted tier | `CustomField:Account.Support_Tier__c` | manifest two-way + xml |
| REQ-011 / REQ-012 | A page per record type, severity on Support only | both `Layout` files | checker exit 0 (now **0 findings**, and now carrying RL-REQ-01/02) + manifest two-way + xml |

**Open at the gate — 6 rows** (`test_type: manual`, outstanding until a human ticks § 7):

| req_id | Requirement | Blocked on |
|---|---|---|
| REQ-003 | Support status ladder exposes `Escalated` | checklist line 2; Status values are a builder default (D-M1S01-01), not customer-confirmed |
| REQ-004 | Billing status ladder has no `Escalated` | checklist line 2, same |
| REQ-010 | A Tier 1 agent cannot open a Billing case | checklist line 3; rests on **A1** (risk `high`) from deferred blocking **Q13** |
| REQ-013 | A hand-logged case runs the active assignment rule | checklist line 4; Q24 built in half (D-M1S02-03), and v1.2.0 added no pre-check element |
| REQ-014 | Every field a validation rule errors on is visible | checklist line 5; **not checkable until M3-S01**; rests on **A13** (risk `medium`) from deferred **Q57** |

Requirements reaching into M1's artefacts but closing later: `Account.Support_Tier__c` (M4-S02's
entitlement process), `Account.Region__c` (M4-S03's calendar-stamping flow), `Case.Severity__c`
(M4-S04's 24/7 escalation entry), the `CaseOrigin` values (M3's Email-to-Case addresses and
`CaseSettings.webToCase.caseOrigin`), and `RecordTypeId` (M2-S05's criteria-based sharing rule). None is
asserted here, and none should be.

**Known gap in this section's own evidence, unchanged:** `check_object_creation_and_design.py` exits 0
without asserting anything about M1-S01's three fields — it returns before any assertion for a file
stem not ending `__c`, and `Case` is standard. REQ-007, REQ-008 and REQ-009 are proved to *exist and be
manifest-consistent*, not to be *well-formed fields*. Recorded on workbook row CWB-OBJ-007 and repeated
here so the table is not read as stronger than it is.

---

## 10. Findings — F-01 … F-14 with current status

### 10.1 The v1 series, re-stated with today's status

**F-01 · HIGH · OPEN, and its remedy pointer was wrong in v1.**
*The record-type ↔ layout binding is asserted nowhere in M1, including by this milestone's own
acceptance test.*

Every record-type-to-layout check in `check_record_type_layouts.py` reads from `layoutAssignments`,
and `collect()` populates them **only** from `Profile` and `PermissionSet` roots. `layoutAssignments`
lives on `Profile`.

> **Correction of record.** v1 said "which is **`M2-S01`**'s", and repeated it in the § 11 go/no-go list.
> **In plan v5 it is `M2-S03`'s.** `M2-S01` declares one `CustomPermission`, one `PermissionSet`,
> `package.xml` and `deploy-order.md` — no `Profile`. `M2-S03` is "Minimal base profiles carrying only
> default app, default record type and **layout assignment**", with three `profile-meta.xml` outputs.
> The stale pointer was copied into two **gate records** in `plan.json.human_gates[]`, which are
> rendered into `PLAN.md`:
>
> - `milestone:M1` approval note — "F-01 (layout↔record-type assertion needs Profile layoutAssignments
>   — **M2-S01**) carried to M2";
> - `step:M2-S01` approval note — "**Profiles step.** Approved for the dry run so F-01 … can be closed
>   at M2 scope."
>
> **Neither note is rewritable by any agent** — a gate record is a written record of a human's
> decision. `decisions.md` **O-M2S01-01** concluded the same and directed the correction here. **This
> is that correction: wherever v1 or a gate note says `M2-S01` in connection with F-01, read
> `M2-S03`.** The step the `step:M2-S01` note approves builds no profile, so the reason recorded for
> approving it is not a reason about that step.

**Measured proof, re-run this milestone (the numbers changed; the conclusion did not):**

| Run | Result |
|---|---|
| M1-S01 at step scope | `5 metadata file(s): 2 record type(s), 0 layout(s); 0 finding(s)` |
| M1-S02 at step scope | `2 metadata file(s): 0 record type(s), 2 layout(s); 0 finding(s)` |
| **M1 at build scope** | `8 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s)` |

The build-scoped run is still the union of the two step runs and **adds no assertion neither step run
made**. It is now *sharper* evidence than v1's: the 8th file it sweeps is `M2-S01`'s
`Case_Intake_Integration.permissionset-meta.xml` — a `PermissionSet`, one of the two roots `collect()`
reads `layoutAssignments` from — and it still resolves **zero**, because that permission set carries a
`customPermissions` grant and nothing else. A `PermissionSet` has entered the tree and the check is
still vacuous.

*Deploy-time consequence, per `skills/devops/deployment-error-diagnosis`:* none at M1 deploy — both
layouts and both record types validated in mock deploy #2. The exposure is at **M2-S03**: a
`layoutAssignments` entry naming a layout that is not one of these two produces
`INVALID_CROSS_REFERENCE_KEY`. `artefacts/M2-S01/deploy-order.md` § "Record types and page layouts:
what this step does NOT carry" already records the exact member forms M2-S03 must reuse.

*Consequence inside the build, unchanged:* three `traceability.md` rows (REQ-001, REQ-011, REQ-012) and
four workbook rows (CWB-OBJ-004, CWB-OBJ-005, CWB-LAYOUT-001, CWB-LAYOUT-002) each name M1's milestone
test as the run that carries this cross-reference. Those seven statements remain wrong.

**Remedy for v6 (planner):** reword the milestone test's `description` to what the run proves, and move
the record-type-to-layout binding assertion onto an **M2** milestone test running the same checker at
`--manifest-dir artefacts` once **M2-S03**'s profiles exist. That matches
`standards/build-orchestration.md` § 5's own rule that a cross-referential checker belongs where both
halves of the pair exist.

---

**F-02 · INFO · OPEN by design, and partly discharged by evidence.**
*Business-process Status values are unresolvable in-tree.*

`Support_Process` selects `New`/`Escalated`/`Closed`, `Billing_Process` selects `New`/`Closed`. All five
resolve against `StandardValueSet:CaseStatus`, which assumption **A28** deliberately keeps out of this
build. Classified **unclassifiable-in-tree / deferred-to-org**, not unresolved-and-broken.

**New evidence:** mock deploy #1 runs 6–7 and mock deploy #2 both validated the two business processes
against `sfskills-dev`, so that org's `CaseStatus` value set carries all three values. The finding does
not close — it is a per-target-org precondition, and one org's answer is not another's. It moves from
"predicted risk" to "discharged on one target, open on every other". Still a § 8 go/no-go item.

---

**F-03 · MEDIUM · OPEN, unchanged.**
*Assumption A13's stated verification route does not exist.*

`plan.json.assumptions[A13]` says the assertion sits in M1-S02's manual test "**and in M1's milestone
checker at `--manifest-dir artefacts`**". `check_record_type_layouts.py` reads no `ValidationRule`
metadata at any scope — `METADATA_SUFFIXES` carries no `.validationRule` entry, and v1.2.0 did not add
one — and no ValidationRule file exists in the build (M3-S01 `pending`). A13 stays unverified until
M3-S01 lands. The *artefacts* moved in A13's favour (§ 7 line 5: 11 shared fields, up from 8); the
*plan text* still asserts a route that does not exist.

---

**F-04 · MEDIUM · OPEN on M1, fixed forward on M2.**
*`deploy-order.md` is undeclared in `outputs[]` on both M1 steps.*

Both files exist, both were **rewritten during rebuild #2**, and neither
`artefacts/M1-S01/deploy-order.md` nor `artefacts/M1-S02/deploy-order.md` appears in its step's
`outputs[]`. `check-outputs` therefore never confirmed either, on either build. It matters beyond
bookkeeping: `agents/build-doc-keeper/AGENT.md` Step 10 compiles `M5-S04`'s build-wide deploy order
from exactly these files.

**What changed:** `M2-S01` **does** declare `artefacts/M2-S01/deploy-order.md` in `outputs[]`. The
pattern is fixed on the newer step and not backported. Also `decisions.md` **O-M1S02-02**.
**Remedy for v6:** declare `artefacts/<step-id>/deploy-order.md` in `outputs[]` on every
`metadata-builder`-owned step, M1's two included.

---

**F-05 · LOW · OPEN, unchanged.**
*`CustomObject:Case` is recorded at position 7 (sharing) and has no position-1 row.*

`Case.object-meta.xml` carries two concerns — the object-level `compactLayoutAssignment` and the OWD.
The workbook gives it one row, `CWB-SHARE-001`, at position 7 of 10; by artefact type a `CustomObject`
belongs at 1. Reported, not corrected, and it does not break the deploy: `Case` is **standard**, it
pre-exists in every target org, and the three `CustomField` members landing at position 2 create no
backwards dependency. Mock deploy #2 validated all 12 components in one atomic request, which is
consistent with this and does not test it. **For v6:** split the object into two workbook rows (object
at 1, OWD at 7), or record on CWB-SHARE-001 that the position is the OWD's.

---

**F-06 · INFO · OPEN, and now defaulted three times.**
*API version `62.0` was chosen by the owning agent, never decided in the plan.*

`plan.json` carries no `api_version` key. `metadata-builder` chose `62.0` on M1-S01, again on M1-S02,
and a third time on M2-S01 (workbook `CWB-OTHER-007`). All three agree, and the merged manifest
inherits it. A fourth default is not better evidence than the first. Worth a decision at v6.

---

**F-07 · LOW · CLOSED on its stated defect; a smaller residue replaces it.**
*v1: the milestone test's `description` predicts `0 finding(s)`; the run produced 2.*

**Closed by the artefacts, not by a reword.** Both layouts now set `Status` to `behavior=Required`
(rebuild #2, **RL-REQ-02**), so check 4 no longer fires and the build-scoped run prints
`0 finding(s) detected.` — exactly what the description predicted. `decisions.md` records the step-level
twin **O-M1S02-01** as "now moot", and this is its milestone-level twin, moot for the same reason. The
entry should close at v6 as *observed-correct*, not as *reworded*.

> **Residue, new at v2.** The same description also predicts `Scanned 7 metadata file(s)`. The run
> scanned **8** — `M2-S01`'s permission set joined `artefacts/` after v1 was written. A **build-scoped**
> test whose description quotes a whole-tree file count is perishable by construction: every future
> step that writes a file the checker's suffix list matches invalidates it, with no defect anywhere in
> M1. **For v6:** state what the run must *find* (2 record types, 2 layouts, 0 findings), not how many
> files it walked past.

---

**F-08 · MEDIUM · OPEN — and it survived a rebuild that rewrote the files carrying it.**
*Both M1 `deploy-order.md` files print the production form against a sandbox placeholder.*

`artefacts/M1-S01/deploy-order.md:103` and `artefacts/M1-S02/deploy-order.md:135` each read:

```text
sf project deploy validate --target-org <your-sandbox-alias> --manifest …
```

`deploy validate` is the **production-only** subcommand, paired with an alias the same line names as a
sandbox. A human copying it hits an error that has nothing to do with their build.

**What is new and worth the human's attention:** both files were **rewritten on 2026-09-09** during
rebuild #2 (mtimes 15:40:58 and 15:41:51) and the wrong command line survived both rewrites — while the
*newer* step got it right. `artefacts/M2-S01/deploy-order.md:129` emits
`sf project deploy start --dry-run --target-org <your-sandbox-alias>` for the sandbox and a **separate**
`deploy validate --target-org <your-production-alias> --test-level RunLocalTests` line for production,
with both spellings grounded in a cited skill. So `metadata-builder` knows the correct form and applies
it to new work; a rebuild of an older step did not revisit it. **Fix owner:** `metadata-builder`. Not
fixed here — this agent does not edit artefacts written by other agents in the loop.

### 10.2 The mock-deploy series

**F-09 · HIGH · CLOSED at the skill, and proven.**
*Case page layouts must carry `ContactId` or the deploy fails.*

**F-10 · HIGH · CLOSED at the skill, and proven.**
*Case page layouts must also carry `Description` and `SuppliedEmail`, and `Status` must be
`behavior=Required`.*

Both closed by the same change. `skills/admin/record-types-and-page-layouts` **v1.2.0** carries a
deployable Case layout example, a `## Layout-required standard fields` section, gotchas #12/#13, and
two ERROR rules:

- **RL-REQ-01** — a `Case` layout with no `layoutItems/field` entry for `ContactId`, `Description` or
  `SuppliedEmail`. Deploy message: *"Layout must contain an item for required layout field: `<F>`"*.
- **RL-REQ-02** — a `Case` layout whose `Status` item is missing or whose behavior is anything other
  than `Required`. Deploy message: *"Field:Status must be Required"*.

Three independent lines of evidence, all re-established this run rather than quoted:

1. The declared milestone checker command exits **0** with **0 findings** on the rebuilt artefacts (§ 6).
2. The **negative control** (§ 6) reverts one layout to the pre-fix shape and the same command exits
   **1** with both rules firing by name. The checker is not silent on the failing shape.
3. **Mock deploy #2** validated the rebuilt artefacts, copied **unmodified**, at **12/12 components,
   `checkOnly: true`, 0 errors** — where run 1 failed both layouts.

The rules are marked in the skill as verified by a dry run against a Summer '26 developer org on
2026-09-05 and explicitly **not** documented in the Metadata API guide, with `RL-REQ-03` (other
objects) carried as `ADVISORY` and marked `UNVERIFIED`. That is the honest scope: **the Case set is
exercised; no other object's is.** `decisions.md` D-M1S02-05, O-M1S02-03. **Nothing is left open on
either finding at the artefact or the skill.**

**F-11 · HIGH · CLOSED at the skill and in the artefacts; its planner half is OPEN.**
*A `BusinessProcess` file's stem must equal its `<fullName>`.*

`skills/admin/case-management-setup` **v1.2.0** states the rule at
`references/metadata-examples.md` § 2.1 and enforces it as **CMS-STEM-01** (stem must equal
`<fullName>`; no `<fullName>` may hold a space) and **CMS-STEM-02** (a record type's
`<businessProcess>` must name an existing process file stem). Same three lines of evidence: exit 0 on
the tree (§ 6), exit 1 with both rules firing on the reverted fixture (§ 6), and 12/12 in mock deploy
#2. Six files changed; `decisions.md` **D-M1S01-05** supersedes **D-M1S01-03** on its `fullName` row.

**Open (planner):** `steps[M1-S01].inputs.business_processes` still reads
`["Support Process", "Billing Process"]` while the outputs, the six rebuilt files and the manifest are
all stem form — a divergence between a step's inputs and its own outputs, which **nothing detects**
because no test reads that string. See § 10.3.

### 10.3 New at v2

**F-12 · MEDIUM · `set-milestone` overwrites an `accepted` milestone without the guard the rest of the
CLI carries — and this run triggered it.**

`scripts/build_plan.py` deliberately protects a human's G3 in one place and not in the other:

| Command | Behaviour on an `accepted` milestone |
|---|---|
| `set-status <step> running` | leaves it alone. The code comment says so in as many words: *"An 'accepted' milestone is left alone: only the human undoes their own G3."* Its guard set is `{pending, rejected, verified}` |
| `set-milestone <Mk> --status verified` | **unconditional** — `milestone["status"] = args.status` |

M1 was `accepted`. `agents/milestone-verifier/AGENT.md` Step 9 requires this agent to record its
verdict with `set-milestone`, and it did (§ 12). The result is that `milestones[M1].status` has moved
`accepted → verified` while `human_gates[milestone:M1].status` remains `approved`. **The two records
now disagree, and only a human can reconcile them:** no agent writes a gate.

This is not an error in this run — it is the prescribed Step 9 command doing what it is defined to do —
but it means **the plan no longer says M1 is accepted**, and a reader who checks only
`milestones[].status` will conclude the G3 was withdrawn. It was not. **For v6 / the tooling owner:**
either give `set-milestone` the same `accepted`-is-the-human's guard `set-status` has, or add an
explicit re-verification status so the second verdict does not have to overwrite the first.

---

**F-13 · MEDIUM · The merged milestone manifest has never been read by a deploy, and one member in it
is spelled differently by the only tool that has ever named it.**

(The milestone-level form of `decisions.md` **O-M1S01-03**, which raised it at step level.)

- `reports/MILESTONE-M1-package.xml` — regenerated this run — declares the bare member `Case_Intake`
  under `CompactLayout`. That form comes from
  `skills/admin/list-views-and-compact-layouts/references/metadata-examples.md`, whose "Where the files
  live" table says "compact layout name" in prose while its own sample manifest uses `*`. No
  non-wildcard example existed to copy. `artefacts/M1-S01/deploy-order.md` calls it "the thinnest
  grounding in this manifest" in its own words.
- **Neither mock deploy tested it.** Both ran `--source-dir force-app --dry-run`, so the CLI derived
  the components from the source tree and never opened a `package.xml`. What it derived was the
  **object-qualified** `CompactLayout Case.Case_Intake` (`reports/MOCK-DEPLOY-M1.md` § "Mock deploy
  #2", component list). **The build's manifest says one thing, the only deploy ever run said another,
  and nothing has compared them.**
- **This is the same shape as F-11, one metadata type over.** F-11 was a member the CLI could not
  resolve, found only by a real validation. The always-on `manifest` test cannot catch either: it
  checks the manifest against the files in the build, and both sides agree with each other. A test
  that compares a document to itself is exactly the class of check F-01 is about.
- **Remedy:** one `sf project deploy start --manifest reports/MILESTONE-M1-package.xml --dry-run
  --target-org <sandbox>` — the § 8 command — or a retrieve showing the member form the org emits.
  **Not this agent's to run: no agent in this loop contacts an org.** Until then the member form is
  unverified, and workbook row `CWB-OTHER-001` says so.

---

**F-14 · LOW · `record-type-decision.md` describes the pre-rebuild artefacts, and it is the document
manual checklist line 1 sends the human to read.**

The file is byte-identical to build #1 (mtime 2026-09-05). Its § 2 table names the two processes
`` `Support Process` `` and `` `Billing Process` `` — in code formatting — while the API names are now
`Support_Process` and `Billing_Process`.

The wording is **defensible**: `case-management-setup` v1.2.0 § 2.1 puts the readable form in
`<description>`, and both files' `<description>` elements do carry it. `metadata-builder` raised the
ambiguity itself during rebuild #2, and `build-doc-keeper` recorded the decision not to amend
`CWB-OTHER-003` with the reason. **What makes it a finding rather than a note** is where it lands: this
is the one document M1's own `manual` acceptance test requires a human to read and judge, and the code
formatting reads as an API name to anyone who has not read § 2.1. **For v6 or the next rebuild of
M1-S01:** mark the two strings as display wording in that table, or give the table an API-name column.

### 10.4 Planner carry-forward items (not findings of this run)

Open in `decisions.md`, restated here because the gate should see them in one place:

| id | Item | Where |
|---|---|---|
| **O-M1S01-01** | `steps[M1-S01].inputs.business_processes` still `["Support Process", "Billing Process"]`; the step's `inputs.note` (B01) still says members are object-qualified as `Case.Support Process`. Nothing reads either string, so nothing fails. Remedy: stem form, which F-11 itself names | F-11's planner half |
| **O-M1S01-02** | Manual test 1's counter-example "(not `Case.Support Process`)" is stale; the shape it excludes is now `Case.Support_Process`. Copied verbatim into `tests/M1-S01/results.json`, which is where a tester reads it | § 7 line 2 |
| **O-M1S01-03** | The bare `CompactLayout Case_Intake` manifest member has never been read by a manifest-reading deploy | **F-13** |
| **O-M1S02-01** | Step-test description predicting `0 finding(s)` — now moot; close as observed-correct | **F-07** |
| **O-M1S02-02** | `deploy-order.md` undeclared on both M1 steps | **F-04** |
| **O-M1S02-03** | The M1 report and gate notes predate the rebuild | **this report** |
| **O-M2S01-01** | F-01's remedy names `M2-S01`; `layoutAssignments` is `M2-S03`'s | **corrected in F-01** |
| **W01 / W02 / W03** | Plan-verifier v5 non-blocking warnings: stale "no fenced XML" claim on M3-S04 / M5-S05; stale "does not recurse" claim on M3-S05 / M5-S01; `A1.steps[]` does not list `M1-S01` | `decisions.md` |
| **Q24 narrowing** | Q24's "defaulted on" half is unproven and unprovable from the artefacts; v1.2.0 added no element that pre-checks the box | § 7 line 4 |
| **A13 carry-forward** | A13 stays unverified until M3-S01 lands; `Severity__c` on the Support layout only would break it for a rule targeting that field | § 7 line 5, **F-03** |
| **`check_case_management_setup.py`** | Cited in `steps[M1-S01].skills[]` and now carrying the two rules that enforce F-11, but **never a declared acceptance test** on that step or on M1. Its exit code contributed to no pass verdict, here or at step level — it is run observation-only. Remedy: declare it, at `--manifest-dir artefacts/M1-S01` for the step or `--manifest-dir artefacts` for the milestone | § 6 |

---

## 11. Verdict, confidence, and what the human decides

### Verdict: `ready-with-findings`

| Verdict condition | Status |
|---|---|
| Unresolved reference | **none** — 10 of 10 in-tree references resolve; 28 standard treated as pre-existing; 5 unclassifiable-in-tree (F-02) |
| Ordering contradiction | **none that breaks a deploy** — one recorded-position divergence (F-05), explained |
| Failing acceptance test | **none** — 2 of 2 executable tests exit 0, both matching their declared `expected`; the observation run also exits 0 |
| Blocked step | **none** — both steps `documented` after rebuild #2 |

### Findings summary

| id | Severity | Status | Finding |
|---|---|---|---|
| F-01 | HIGH | **open** (pointer corrected: **M2-S03**, not M2-S01) | The record-type ↔ layout binding is asserted nowhere in M1 |
| F-02 | INFO | open by design; discharged on `sfskills-dev` only | Business-process Status values resolve only against the target org's `CaseStatus` |
| F-03 | MEDIUM | open | A13's stated verification route (M1's milestone checker) does not exist |
| F-04 | MEDIUM | open on M1; fixed forward on M2-S01 | `deploy-order.md` undeclared in `outputs[]` on both M1 steps |
| F-05 | LOW | open | `CustomObject:Case` recorded at position 7 with no position-1 row |
| F-06 | INFO | open, now defaulted 3× | API version `62.0` defaulted by the owning agent; the plan carries no `api_version` |
| F-07 | LOW | **closed** (artefacts), small residue | Milestone test description predicted `0 finding(s)`; the run now gives 0. File count `7` is now `8` |
| F-08 | MEDIUM | open — **survived the rebuild** | Both M1 `deploy-order.md` files print `deploy validate` against a sandbox alias |
| F-09 | HIGH | **closed at the skill, proven** | Case layouts must carry `ContactId` — now **RL-REQ-01** |
| F-10 | HIGH | **closed at the skill, proven** | `Description`, `SuppliedEmail`, `Status` Required — **RL-REQ-01 / RL-REQ-02** |
| F-11 | HIGH | **closed at the skill and in the artefacts**; planner half open | BusinessProcess stem must equal `<fullName>` — **CMS-STEM-01 / CMS-STEM-02** |
| F-12 | MEDIUM | **new** | `set-milestone` moved M1 `accepted → verified` with no guard; the gate record still says `approved` |
| F-13 | MEDIUM | **new** (= O-M1S01-03) | The merged manifest has never been read by a deploy; `CompactLayout` member form disputed by the only deploy run |
| F-14 | LOW | **new** | `record-type-decision.md` names the pre-rebuild process spellings, and manual line 1 sends a human to read it |

**The three HIGH findings the 2026-09-05 gate did not know about are all closed, and closed at the
source** — a rule the library now enforces, not a footnote in a report. The finding the gate was
really for, **F-01, is unchanged**, and its remedy pointer was wrong in both the v1 report and the two
gate notes.

### Confidence: **MEDIUM**

Per the Step 10 table. Every step was documented, the merged manifest built with no conflict, and every
declared acceptance test existed and ran — which would support HIGH. It is **MEDIUM** because the
reference class this milestone exists to close was still not fully classifiable: the record-type ↔
layout binding had **zero** references to resolve (F-01), and the five business-process Status
references resolve only outside the tree (F-02). Neither is a failure; both mean a load-bearing check
was reported rather than made.

Two things deliberately **did not** raise it:

- **The org validation is not in the rubric.** 12/12 components validating against `sfskills-dev` is
  strong external corroboration and it is why F-09/F-10/F-11 are closed — but the Step 10 rubric scores
  what *this agent's* checks could classify, and an org run this agent did not make is not one of them.
- **Passing checkers were treated as claims until tested.** The two new rule families were run against
  reverted fixtures before their exit-0 was reported as meaning anything (§ 6).

### What the human decides

1. **M1 is already `accepted`, and the artefacts under it changed.** Decide which: (a) the 2026-09-05
   approval stands and this report is the recorded delta; (b) re-approve `milestone:M1` against these
   artefacts, using the § 12 command; or (c) reject and re-plan. **This agent takes no position and
   approved nothing.** Note **F-12**: `milestones[M1].status` now reads `verified` while the gate
   record still reads `approved` — whichever you choose, those two need reconciling.
2. **Accept F-01, or re-plan.** The milestone test does not carry the assertion its description claims,
   and the remedy lives at **M2-S03**, not M2-S01. Accepting means accepting that record-type ↔ layout
   consistency in M1 rests on a naming convention (2 record types, 2 layouts, 1:1 by name) plus the
   member forms `M1-S02/deploy-order.md` and `M2-S01/deploy-order.md` record for M2-S03 to reuse.
3. **Checklist line 1, clause (c):** accept `Reason` value sets as absent-and-documented, or rule the
   clause unanswerable and reword at v6. Plus **F-14** — the document that line sends you to still
   names the old process spellings.
4. **Checklist line 4:** accept Q24 built in half — the checkbox is *shown*, not *defaulted on*. The
   skill deepening that closed F-09/F-10 explicitly did not add a pre-checking element, so "deepen the
   skill" has now been tried once and did not close it.
5. **Checklist line 5 / REQ-014:** accept that A13 (risk `medium`, deferred Q57) stays unverified until
   M3-S01 lands. The rebuild widened its satisfied surface from 8 shared fields to 11.
6. **REQ-010 / assumption A1 (risk `high`, deferred blocking Q13):** the Private OWD is on disk,
   byte-identical to what was approved, and correct. The *policy* it encodes is still the conservative
   reading of a deferred question; the `step:M1-S01` gate note already says a real deployment needs the
   security owner's signature.
7. **Before any deploy:** **F-13** — run the § 8 `--manifest --dry-run` command once. It is the only
   check that reads `reports/MILESTONE-M1-package.xml`, and the one member whose form is disputed
   (`CompactLayout`) is in it. F-02's `CaseStatus` reconciliation is discharged for `sfskills-dev` and
   open for any other target.
8. **F-08 before handing anyone a runbook:** both M1 `deploy-order.md` files print the production-only
   `deploy validate` against a sandbox alias.

Approving `milestone:M1` against these artefacts accepts F-01 through F-08 as recorded here (F-07
closed), the three closed mock-deploy findings as closed, F-12 through F-14 as new and open, and the
five manual lines in § 7 on the readings § 7 states — not on their literal wording, in the case of
lines 1, 2, 4 and 5.

---

## 12. Recorded verdict, and the gate command

The verdict and this report's path were recorded with the one plan write this agent makes — a
subcommand, never a hand edit:

```bash
python3 scripts/build_plan.py set-milestone \
  .sfskills/builds/case-onboarding/plan.json M1 \
  --status verified \
  --report-path reports/MILESTONE-M1-REPORT-v2.md
```

`--status verified` is a statement about what the checks found, **not an approval**.
`milestones[].status` and `report_path` are plan bookkeeping; a gate record is written only by a human.
See **F-12** for what this command did to the previously `accepted` status.

The gate command — **for a human to run. This agent did not run it and will not.**

```bash
python3 scripts/build_plan.py gate \
  .sfskills/builds/case-onboarding/plan.json milestone:M1 approve \
  --by "<name>"
```

`standards/build-orchestration.md` § 3 refuses that command unless the `plan` gate is `approved` (it is)
and every step in M1 is `documented` or blocked with a recorded reason (both are `documented`). There is
no `milestone:M0`, so the predecessor condition is vacuous. **No blocked step**, so approving accepts no
known gap of that kind — the gaps this milestone carries are the findings in § 10 and the narrowed
manual lines in § 7.

To reject instead: `… gate .../plan.json milestone:M1 reject --by "<name>" --notes "<why>"`, which sets
M1's status to `rejected` and leaves the build at `building`.

---

## Provenance of this report

| Output | Path |
|---|---|
| This acceptance report | `reports/MILESTONE-M1-REPORT-v2.md` |
| The v1 report it supplements (**not** replaced) | `reports/MILESTONE-M1-REPORT.md` |
| Merged milestone manifest (**regenerated this run**) | `reports/MILESTONE-M1-package.xml` |
| Milestone test evidence, this run | `tests/M1/*.v2.{stdout,stderr,exit}`, `tests/M1/NEGATIVE-CONTROLS.v2.stdout` |
| Milestone test evidence, v1 (untouched) | `tests/M1/check_record_type_layouts.{stdout,stderr,exit}`, `tests/M1/manifest.*` |
| This run's envelope | `envelopes/M1/2026-09-09T20-19-00Z.json` / `.md` |

Nothing outside `.sfskills/builds/case-onboarding/` was written. No `sf` command was run. No gate was
approved.
