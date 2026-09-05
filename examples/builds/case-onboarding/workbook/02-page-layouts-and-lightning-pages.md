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
| CWB-LAYOUT-001 | `Layout:Case-Case Support Layout` — two sections, both `TwoColumnsTopToBottom`. `Case Information` (`customLabel` true), left column `Subject`, `Priority`, `Origin`, `Severity__c`; right column `CaseNumber` (Readonly), `Status`, `OwnerId`, one `emptySpace`. `System Information` (`customLabel` false): `CreatedById`, `LastModifiedById`, both Readonly. `showEmailCheckbox` true, `showRunAssignmentRulesCheckbox` true, `showKnowledgeComponent` false. **No field carries `behavior=Required`.** Nine fields total. | CRM admin lead (role; the plan names no person) | REQ-011; REQ-013; REQ-014 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts | executed | Deploy position 5 of 10 (layouts) in the M1 sequence; position 1 inside the step — the two layouts have no ordering constraint between them and deploy in one request (`artefacts/M1-S02/deploy-order.md`). Upstream: `Case.Severity__c` (M1-S01) must exist first, or the layout fails the deploy. Verified by: `check_record_type_layouts.py --manifest-dir artefacts/M1-S02` exit 0, `score 100`, `2 layout(s); 2 finding(s)` — both `INFO`, both "marks no field behavior=Required", which is what **Q5's answer requires** and not a defect (`gotchas.md` #11); plus `manifest` two-way and `xml` parse. **Gap named:** 0 record types were in view, so the record-type-to-layout cross-reference is vacuous at this scope — M1's milestone test at `--manifest-dir artefacts` is the run that carries it. Manual test `TC-M1S02-01` covers the Q24 and A13 halves and is outstanding. The `Severity__c` placement (Support only) is `decisions.md` D-M1S02-02; the field set is a builder default, D-M1S02-01. |
| CWB-LAYOUT-002 | `Layout:Case-Case Billing Layout` — identical structure to CWB-LAYOUT-001 and identical `show*` element values, minus `Severity__c` and minus the `emptySpace`: `Case Information` left column `Subject`, `Priority`, `Origin`; right column `CaseNumber` (Readonly), `Status`, `OwnerId`. Eight fields total. **No field carries `behavior=Required`.** | CRM admin lead (role; the plan names no person) | REQ-012; REQ-013; REQ-014 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts | executed | Deploy position 5 of 10 (layouts); position 2 inside the step. Every field on this layout is a standard Case field, so it carries no upstream ordering constraint at all. Verified by: same checker run as CWB-LAYOUT-001 (same exit, its own `INFO`), `manifest` two-way, `xml` parse — and the same named cross-reference gap; manual `TC-M1S02-01` outstanding. **Carry-forward the M1 gate should see:** because `Severity__c` is absent here by design (D-M1S02-02), a Case validation rule in `M3-S01` that attaches its error to `Severity__c` would break assumption **A13** on this layout. Neither rule M3-S01 declares today targets that field. |
