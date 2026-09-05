# Configuration Workbook — Section 3

Per-step slice, written by the build doc keeper after `M2-S01` was tested. The compiled
ten-section workbook is `M5-S04`'s output; this file is one of its sources and is not the
finished document.

Row schema and section list: `skills/admin/configuration-workbook-authoring` SKILL.md
Concepts 1–3. This is the first Section 3 file in the build — `M2-S02` (permission sets and
PSGs for the three personas) and `M2-S03` (the base profiles) add to it.

**Why `recommended_agent` is not the section default.** Concept 3's table gives Section 3 the
default `permission-set-architect`, which declares `requires_org: true`. This build is
`build_mode: design-only`, where `standards/build-orchestration.md` § 4 routes every `access`
step to `metadata-builder`, and `agents/build-doc-keeper/AGENT.md` Step 4 binds
`recommended_agent` to "the step's owning agent id, which is the agent that actually built it".
Both rows therefore name `metadata-builder`, as M1-S01's Section 1 and M1-S02's Section 2 rows
do for the same reason.

**Why a `CustomPermission` is filed in Section 3 rather than Section 5.**
`agents/build-doc-keeper/AGENT.md` Step 4 maps step type `access` to "3 — Profiles + Permission
Sets + PSGs, and 4 — Sharing Settings for sharing artefacts". This step produces no sharing
artefact, so both rows land in Section 3. The tension worth naming: Concept 2 describes Section 5
as carrying the validation rule's "bypass reference (Custom Permission + Custom Setting)", and
`skills/admin/configuration-workbook-authoring` SKILL.md lists `admin/custom-permissions` among
the Section 5 skills. That is the **reference from the rule to the permission** — an
`M3-S01` row, on the two rules whose `errorConditionFormula` carries
`NOT($Permission.Bypass_Case_Intake_Validation)`. The permission's own definition and the grant
that carries it are access artefacts, and Section 3 is where a reviewer asking "what does this
permission set grant" opens. `M3-S01`'s Section 5 rows will cite `CWB-PERM-001` back.

**Why these cells use `;` and not `|` for multi-value.** `check_workbook.py` splits a table row
on every bare `|` with no escape handling (L330), so an escaped `\|` inside a cell shifts every
column after it and the linter then reads `source_req_id` as `recommended_agent`. Same
convention as `workbook/02-page-layouts-and-lightning-pages.md`.

## Section 3 — Profiles + Permission Sets + PSGs

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-PERM-001 | `CustomPermission:Bypass_Case_Intake_Validation` — `<label>Bypass Case Intake Validation</label>` plus a `<description>` that names what holding it does (save a Case the intake validation rules would reject, because it was created through the API), both consumer rules by API name (`Case.Priority_Required_On_Agent_Save`; `Case.Origin_Must_Be_Known`, M3-S01), the one permission set that grants it, and the owning role. Two elements in the file and no others: no `<connectedApp>`, no `<requiredPermission>`, no `<isLicensed>`. | Security architect (role; the plan names no person) | REQ-015 | pending:M5-S03 | metadata-builder | admin/custom-permissions; admin/permission-set-architecture; admin/validation-rules | executed | **Deploy position: not placeable in the ten-position milestone sequence** — objects, fields, picklists, record types, layouts, permission sets, sharing, automation, routing, SLA has no slot for a `CustomPermission`. Reported here rather than given a number, per `agents/build-doc-keeper/AGENT.md` Step 5. Its real constraint is local and absolute: position **1 inside the step**, because "a `PermissionSet` naming a custom permission that does not yet exist fails the deploy" (`artefacts/M2-S01/deploy-order.md`, order table). Verified by: `check_custom_permissions.py --manifest-dir artefacts/M2-S01` exit 0, `Custom permissions defined: 1`, coverage row `Bypass_Case_Intake_Validation  0  permission set 'Case_Intake_Integration'`, `0 error(s), 0 warning(s), 0 info`; plus `manifest` two-way and `xml` parse. **Gap named:** the `Consumers: 0` column is vacuous — no validation rule is in scope at this manifest dir, so removing the grant entirely would still exit 0. The consumer cross-reference is M3's milestone test, which runs the same checker at `--manifest-dir artefacts --strict` once M3-S01's two rules exist. The consumer names in the description are read from `plan.json` `steps[M3-S01].outputs[]`, not from a clarification: `decisions.md` D-M2S01-01. `<isLicensed>` is omitted deliberately (read-only field, `custom-permissions/references/gotchas.md` #7), not overlooked. |
| CWB-PERM-002 | `PermissionSet:Case_Intake_Integration` — `<label>Case Intake Integration</label>`, `<hasActivationRequired>false</hasActivationRequired>`, and exactly one grant-bearing element: `<customPermissions>` carrying `<enabled>true</enabled>` and `<name>Bypass_Case_Intake_Validation</name>`. Thirteen other grant-bearing elements are absent by design — `objectPermissions`; `fieldPermissions`; `userPermissions`; `classAccesses`; `pageAccesses`; `recordTypeVisibilities`; `tabSettings`; `applicationVisibilities`; `flowAccesses`; `customSettingAccesses`; `customMetadataTypeAccesses`; `externalDataSourceAccesses`; `externalCredentialPrincipalAccesses`. No `<license>` element (Q8: leave LicenseId empty). The `<description>` records the population (the Email-to-Case / Web-to-Case automated-process identity, never a human user), that it grants nothing else, and the owning role. | Security architect (role; the plan names no person) | REQ-016 | pending:M5-S03 | metadata-builder | admin/custom-permissions; admin/permission-set-architecture; admin/validation-rules | executed | Deploy position **6 of 10 (permission sets)** in the M2 sequence; position 2 inside the step, after CWB-PERM-001. It references no object, field, record type, tab, app, class or flow, so it can deploy into an org holding none of M1's metadata (`artefacts/M2-S01/deploy-order.md`). Verified by: `check_access_model.py --manifest-dir artefacts/M2-S01` exit 0, `score 100`, `Scanned 1 access-model metadata file(s); 0 finding(s)` — and that exit is a strong statement rather than a threshold, because the checker returns 1 on **any** finding (`check_access_model.py` emit_result, L152–160), and W09 confirmed an empty directory exits 1, so exit 0 stands for a file that was actually scanned. Also `check_permission_set_architecture.py` exit 0, `No issues found.` — run by the owning agent as a self-check, **not** a declared acceptance test. Plus `manifest` two-way and `xml` parse. Manual test `TC-M2S01-01` is outstanding, ticked at the M2 gate; the tester already captured the full element evidence (`tests/M2-S01/manual-evidence.stdout.txt`, `ASSERTION 'grants the bypass and nothing else': HOLDS`). **Gap named:** whether the assignment is actually made to the integration identity and to no human is **not evidenceable in this build at all** — `PermissionSetAssignment` is record data, not metadata. **Two recorded absences a reviewer should see:** `ApiEnabled` is deliberately not granted (`decisions.md` D-M2S01-02) and the grant carries no expiry (D-M2S01-03). The name diverges from `templates/admin/permission-set-patterns.md`'s `Integration_<System>_Bundle` form and was written as the plan declared it (D-M2S01-04). `recommended_skills` carries the step's three; the skill this row's second checker actually belongs to — `admin/permission-sets-vs-profiles`, which also supplies the Q8 and Q10 answers — is **not** in the step's `skills[]`, the same shape M1-S01's `CWB-SHARE-001` recorded for `admin/sharing-and-visibility`. |
