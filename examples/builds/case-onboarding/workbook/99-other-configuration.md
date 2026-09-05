# Configuration Workbook — Other configuration

Per-step slice, written by the build doc keeper after `M1-S01` was tested.

**Why these three rows are here and not in a numbered section.**
`agents/build-doc-keeper/AGENT.md` Step 4 routes `package.xml` and the deploy-order note to
"10 — Data + Migration only when they are a migration artefact, otherwise to **Other
configuration**". Neither is a migration artefact — `M1-S01` loads no data — so they land in the
default section, and the decision record lands with them because it is a document about the step
rather than a configurable value. The step's own **type** (`object-model`) is in Step 4's map, so
this is not the "unmapped step type" case; it is the artefact-level default the same paragraph
defines.

**One thing a reader should know about this file.** `check_workbook.py` recognises a section only
from a heading matching `^#{2,3}\s+Section\s+(\d+)\s*[—-]\s*(.+)$`, so rows under the heading
**Other configuration** are parsed into no section and are invisible to that linter. Numbering it
"Section 11" would make it visible and would also invent an eleventh canonical section, which
`skills/admin/configuration-workbook-authoring` Concept 2 forbids ("The workbook is fixed at ten
sections. Authors do not invent new sections"). The heading is left as the AGENT.md specifies and
the linter gap is reported instead.

## Other configuration

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-OTHER-001 | `artefacts/M1-S01/package.xml` — step-level deploy manifest, API version `62.0`, six type blocks: `StandardValueSet` (1 member), `CustomObject` (1), `CustomField` (3), `BusinessProcess` (2), `RecordType` (2), `CompactLayout` (1). No wildcard members. | CRM admin lead (role; the plan names no person) | REQ-001 \| REQ-002 \| REQ-003 \| REQ-004 \| REQ-005 \| REQ-006 \| REQ-007 \| REQ-008 \| REQ-009 \| REQ-010 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts; admin/object-creation-and-design; admin/record-type-id-management; admin/case-management-setup; admin/list-views-and-compact-layouts | executed | Deploy position: not a component — it is the manifest the other ten rows deploy through, so it has no slot in the sequence. Verified by: the always-on `manifest` test, two-way, 10 members ↔ 10 metadata files, 0 findings, no wildcards, no orphans in either direction (`tests/M1-S01/manifest.stdout`); `xml` parse. `api_version 62.0` was **defaulted** by the owning agent — `plan.json` carries no `api_version` key (`envelopes/M1-S01/2026-09-05T19-40-00Z.json` → `inputs_received`). The `CompactLayout` member form (`Case_Intake`, bare) is the thinnest-grounded member in the file: the cited skill states "compact layout name" in prose but its own sample manifest uses `*`, so no non-wildcard example existed to copy. Verify against a retrieve before deploying. |
| CWB-OTHER-002 | `artefacts/M1-S01/deploy-order.md` — the step's five-position internal deploy order (fields → CaseOrigin value set → business processes → compact layout → object + record types), its upstream/downstream dependency list, the manifest member forms used, and the validate-only command for the human. | CRM admin lead (role; the plan names no person) | REQ-001 \| REQ-005 \| REQ-010 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts; admin/object-creation-and-design; admin/record-type-id-management; admin/case-management-setup; admin/list-views-and-compact-layouts | executed | Deploy position: not a component. Verified by: **nothing** — this file is **not** in the step's `outputs[]`, so `check-outputs` never confirmed it and the `manifest` test skipped it as a non-metadata file. The owning agent raised the same gap (`process_observations[3]`, `extensions.undeclared_artefacts`). Open item for the planner: declare `artefacts/M1-S01/deploy-order.md` in `outputs[]` at v6. Contents feed `M5-S04`'s build-wide deploy order. |
| CWB-OTHER-003 | `artefacts/M1-S01/record-type-decision.md` — the record-type decision record: why two record types (Q1, A26), the Support Processes and their Status subsets (Q2, A28), the Origin value set (Q19, W01), the compact layout (B02/B03), the org-wide default (B01, A1, Q13) and the three fields, each with its grounding and its open items. | CRM admin lead (role; the plan names no person) | REQ-001 \| REQ-002 \| REQ-003 \| REQ-004 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts; admin/object-creation-and-design; admin/record-type-id-management; admin/case-management-setup; admin/list-views-and-compact-layouts | executed | Deploy position: not a component. Verified by: `check-outputs` (declared output, present, non-empty) and **M1's milestone manual test**, which reads this file and requires it to state that the record-type count was decided in the plan rather than by the builder, to name D5's criteria-based sharing rule on `RecordTypeId` as what settled Q1's conditional, and to show the Status and Reason value sets for each process. That third clause is only partly satisfiable: the file shows the Status subsets but records that no Reason values exist in any source — see `decisions.md` D-M1S01-01. Flagged for the human at the M1 gate. |
| CWB-OTHER-004 | `artefacts/M1-S02/package.xml` — step-level deploy manifest, API version `62.0`, one type block: `Layout` (2 members, `Case-Case Support Layout` and `Case-Case Billing Layout`). No wildcard members, although the "Where the files live" table records that `Layout` supports `*`. | CRM admin lead (role; the plan names no person) | REQ-011; REQ-012; REQ-013; REQ-014 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts | executed | Deploy position: not a component — it is the manifest the two layout rows deploy through, so it has no slot in the sequence. Verified by: the always-on `manifest` test, two-way, 2 members ↔ 2 layout files, `verdict: consistent \| failures: 0`, no wildcards, no orphans in either direction (`tests/M1-S02/manifest.stdout`); `xml` parse; and `check_deployment_manifest.py --manifest-dir artefacts/M1-S02` exit 0, `score 100`, 0 findings — which the owning agent ran as its own self-check rather than as a declared acceptance test. `api_version 62.0` was **defaulted** by the owning agent for the second time in this build — `plan.json` still carries no `api_version` key — and matches M1-S01's manifest. Member form: object, hyphen, layout name, literal space, per the guide's own `Idea-Idea Layout` example. |
| CWB-OTHER-005 | `artefacts/M1-S02/deploy-order.md` — the step's two-position internal order, the `Case.Severity__c` upstream dependency, the layout file-name forms the M2 profile step must reuse, the retrieve-time warning from `gotchas.md` #7, the four elements the step could not ground, and the validate-only command for the human. | CRM admin lead (role; the plan names no person) | REQ-011; REQ-012; REQ-013; REQ-014 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts | executed | Deploy position: not a component. Verified by: **nothing** — the file is **not** in the step's `outputs[]`, so `check-outputs` never confirmed it and the `manifest` test excluded it by name ("not a source-format metadata file"). Identical to `CWB-OTHER-002` on M1-S01, which makes it a plan-wide pattern rather than a one-step slip: `decisions.md` § "Open items for the planner — raised by the M1-S02 build and test runs", **O-M1S02-02**. Contents feed `M5-S04`'s build-wide deploy order, which is compiled from exactly these per-step files. |

**The two rows added after `M1-S02` (`CWB-OTHER-004`, `CWB-OTHER-005`).** Same routing as the three
above and for the same reason: `agents/build-doc-keeper/AGENT.md` Step 4 sends `package.xml` and the
deploy-order note to "10 — Data + Migration only when they are a migration artefact, otherwise to
**Other configuration**", and `M1-S02` loads no data. The step's own **type** (`ui`) is in Step 4's
map — it produced the two Section 2 rows in
`workbook/02-page-layouts-and-lightning-pages.md` — so again this is the artefact-level default, not
the unmapped-step-type case. The `check_workbook.py` blindness described above applies to these two
rows identically.

**And why these two rows delimit `source_req_id` with `;` while the three above use `\|`.**
`check_workbook.py` splits a row on every bare `|` (L330) with no escape handling, so `\|` inside a
cell shifts every later column. It does not bite the three M1-S01 rows only because the parser skips
this whole file — **Other configuration** is not a canonical section heading — and it would bite all
five the moment they are read anywhere a section heading is recognised. The two new rows use `;`,
the delimiter `recommended_skills` already documents; the three existing rows are left
byte-identical, because rows belonging to another step are not this run's to rewrite. Flagged for
`M5-S04`, which is the run that compiles them.
