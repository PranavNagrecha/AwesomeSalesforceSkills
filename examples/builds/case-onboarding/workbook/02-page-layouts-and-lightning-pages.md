# Configuration Workbook — Section 2

Per-step slice, written by the build doc keeper after `M1-S02` was tested. The compiled
ten-section workbook is `M5-S04`'s output; this file is one of its sources and is not the
finished document.

Row schema and section list: `skills/admin/configuration-workbook-authoring` SKILL.md
Concepts 1–3.

**Why `recommended_agent` is not the section default.** Concept 3's table gives Section 2 the
default `audit-router --domain=lightning_record_page`, which audits an existing Lightning record
page in a live org. `agents/build-doc-keeper/AGENT.md` Step 4 binds `recommended_agent` to "the
step's owning agent id, which is the agent that actually built it", and this build is
`build_mode: design-only`, where `standards/build-orchestration.md` § 4 routes every `ui` step to
`metadata-builder`. Both rows therefore name `metadata-builder`, as `M1-S01`'s Section 1 rows do
for the same reason.

**One thing a reader should know about these two rows.** Neither layout is assigned to anyone.
`layoutAssignments` lives only on `Profile`, never on `PermissionSet`
(`record-types-and-page-layouts/references/metadata-examples.md`, "Making the record type visible
and assigning the page"), and the profiles are M2's. Both layouts deploy and neither is reachable
by a user until `M2-S01` lands. That is expected at this point in the build, and it is also why
this step's checker had no `layoutAssignments` to resolve.

**This file was amended on 2026-09-09 after rebuild #2 of `M1-S02`.** Both rows' `target_value` and `notes` cells were rewritten; every other cell in them, and every row belonging to another step, is byte-identical to the 2026-09-06 documentation run. The rebuild added three `layoutItems` per layout and changed one `behavior`, for reasons no cited source carried when the rows were first written — `decisions.md` **D-M1S02-05** is the entry, `reports/MOCK-DEPLOY-M1.md` findings F-09 and F-10 are the proof, and `skills/admin/record-types-and-page-layouts` v1.2.0 is where the gap was closed.

**Why these cells use `;` and not the RTM's `|` for multi-value.** `check_workbook.py` splits a
table row on every bare `|` with no escape handling (`check_workbook.py` L330), so a `\|` written
inside a cell shifts every column after it and the linter then reads `source_req_id` as
`recommended_agent`. `recommended_skills` is documented as `;`-delimited for the same reason, so
`;` is used for `source_req_id` here too. `M1-S01`'s rows in `workbook/99-other-configuration.md`
use `\|` and are not caught by this, because the **Other configuration** heading is not a canonical
section and the parser skips its rows entirely — a latent break that surfaces the moment those rows
are compiled anywhere the parser reads them. Reported, not fixed here: rows belonging to another
step are left byte-identical.

## Section 2 — Page Layouts + Lightning Pages

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-LAYOUT-001 | `Layout:Case-Case Support Layout` — two sections, both `TwoColumnsTopToBottom`. `Case Information` (`customLabel` true), left column `SuppliedEmail`, `Description`, `ContactId`, `Subject`, `Priority`, `Origin`, `Severity__c`; right column `CaseNumber` (Readonly), `Status` (**Required**), `OwnerId`, one `emptySpace`. `System Information` (`customLabel` false): `CreatedById`, `LastModifiedById`, both Readonly. `showEmailCheckbox` true, `showRunAssignmentRulesCheckbox` true, `showKnowledgeComponent` false. **`Status` is the only item carrying `behavior=Required`; every other item is `Edit` or `Readonly`.** Twelve fields total. **Amended after rebuild #2 (2026-09-09):** `SuppliedEmail`, `Description` and `ContactId` were added as `layoutItems` and `Status` moved from `Edit` to `Required` — four platform deploy preconditions, not design changes (`decisions.md` D-M1S02-05). The row as first written described build #1's nine-field layout, which the mock deploy proved undeployable. | CRM admin lead (role; the plan names no person) | REQ-011; REQ-013; REQ-014 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts | executed | Deploy position 5 of 10 (layouts) in the M1 sequence; position 1 inside the step — the two layouts have no ordering constraint between them and deploy in one request (`artefacts/M1-S02/deploy-order.md`). Upstream: `Case.Severity__c` (M1-S01) must exist first, or the layout fails the deploy. Verified by: `check_record_type_layouts.py --manifest-dir artefacts/M1-S02` exit 0, `score 100`, `Scanned 2 metadata file(s): 0 record type(s), 2 layout(s); 0 finding(s) detected.` — and this exit 0 asserts strictly more than build #1's identical exit 0 did, because the checker gained two ERROR rules at skill v1.2.0: **RL-REQ-01** (a Case layout with no `layoutItems` entry for `ContactId` / `Description` / `SuppliedEmail`) and **RL-REQ-02** (`Status` missing or not `behavior=Required`). Run against build #1's layouts the same command exits **1** with four RL-REQ ERRORs. Plus `manifest` two-way and `xml` parse (3 of 3). **Independent evidence:** mock deploy #2 (`reports/MOCK-DEPLOY-M1.md`) validated 12 of 12 components with these artefacts copied unmodified, where run 1 failed both layouts. The two `INFO` lines build #1 produced ("marks no field behavior=Required") are gone, which makes the plan's own acceptance-test description accurate — open item **O-M1S02-01** is now moot rather than outstanding. **Gap named:** 0 record types were in view, so the record-type-to-layout cross-reference is vacuous at this scope — M1's milestone test at `--manifest-dir artefacts` is the run that carries it. Manual test `TC-M1S02-01` covers the Q24 and A13 halves and is outstanding; its disk evidence was re-captured after the rebuild and both readings are unchanged (`tests/M1-S02/manual-evidence.stdout`). Q5 still governs `Priority`, `Origin` and `Subject`, which stay `Edit` (`gotchas.md` #11); `Status` is outside that question (`gotchas.md` #13). The `Severity__c` placement (Support only) is `decisions.md` D-M1S02-02; the field set is a builder default, D-M1S02-01, amended by D-M1S02-05. **Stale above this row:** `reports/MILESTONE-M1-REPORT.md` and the `milestone:M1` gate note describe build #1's layouts (`decisions.md` O-M1S02-03). |
| CWB-LAYOUT-002 | `Layout:Case-Case Billing Layout` — identical structure to CWB-LAYOUT-001 and identical `show*` element values, minus `Severity__c` and minus the `emptySpace`: `Case Information` left column `SuppliedEmail`, `Description`, `ContactId`, `Subject`, `Priority`, `Origin`; right column `CaseNumber` (Readonly), `Status` (**Required**), `OwnerId`. Eleven fields total. **`Status` is the only item carrying `behavior=Required`.** **Amended after rebuild #2 (2026-09-09):** the same three `layoutItems` added and the same `Status` behavior change as CWB-LAYOUT-001 (`decisions.md` D-M1S02-05); the row as first written described build #1's eight-field layout. | CRM admin lead (role; the plan names no person) | REQ-012; REQ-013; REQ-014 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts | executed | Deploy position 5 of 10 (layouts); position 2 inside the step. Every field on this layout is a standard Case field, so it carries no upstream ordering constraint at all. Verified by: same checker run as CWB-LAYOUT-001 (same exit 0, `0 finding(s)`, the same newly-in-force RL-REQ-01/02 rules), `manifest` two-way, `xml` parse — and the same named cross-reference gap; manual `TC-M1S02-01` outstanding. Same mock-deploy #2 evidence: 12 of 12 components validated with this file copied unmodified. **Carry-forward the M1 gate should see:** because `Severity__c` is absent here by design (D-M1S02-02), a Case validation rule in `M3-S01` that attaches its error to `Severity__c` would break assumption **A13** on this layout. Neither rule M3-S01 declares today targets that field. Rebuild #2 widened A13's satisfied surface rather than narrowing it: `ContactId`, `Description` and `SuppliedEmail` are now on **both** layouts, so a rule attaching its error to any of the three would satisfy A13 on both. **Stale above this row:** the M1 report and the `milestone:M1` gate note predate the rebuild (`decisions.md` O-M1S02-03). |
