# Configuration Workbook — Section 4

Per-step slice, written by the build doc keeper after `M1-S01` was tested. The compiled
ten-section workbook is `M5-S04`'s output.

**Why an `object-model` step writes a Sharing Settings row.**
`agents/build-doc-keeper/AGENT.md` Step 4 maps step type `object-model` to section 1, and its
Escalation table says a step whose artefacts straddle two sections "is split across both". Plan v5
note **B01** moved the Case org-wide default onto this step's
`objects/Case/Case.object-meta.xml`, and an OWD is section 4 by definition
(`skills/admin/configuration-workbook-authoring` Concept 2: "**Sharing Settings** — OWD, role
hierarchy adjustments, sharing rules, manual share, restriction rules"). Filing it in section 1
because of the step's type would hide the build's only OWD from the section a reviewer opens to
find it. The split is recorded here and in this run's Process Observations.

## Section 4 — Sharing Settings

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-SHARE-001 | `CustomObject:Case` org-wide default — `<sharingModel>Private</sharingModel>` and `<externalSharingModel>Private</externalSharingModel>`, both as direct children of `<CustomObject>` in `objects/Case/Case.object-meta.xml`. No separate settings file carries the OWD. | Security architect (role; the plan names no person) | REQ-010 | pending:M5-S03 | metadata-builder | admin/record-types-and-page-layouts; admin/object-creation-and-design; admin/record-type-id-management; admin/case-management-setup; admin/list-views-and-compact-layouts | executed | Decision tree: `standards/decision-trees/sharing-selection.md` branch **Q3** — plan decision **D5**, "Case org-wide default stays Private and Tier 2 reaches Support cases through a criteria-based sharing rule on record type". Deploy position 7 of 10 (sharing) in the M1 sequence; position 5 inside the step, on the object file (`artefacts/M1-S01/deploy-order.md`). Verified by: manual test `TC-M1S01-02`, ticked at the M1 gate; disk evidence already captured in `tests/M1-S01/manual-evidence.stdout` (both elements `Private`; no `*.settings-meta.xml` anywhere under `artefacts/`). **Gap named:** the machine assertion that the OWD is not looser than the sharing rule's grant is `M2-S05`'s build-scoped `check_sharing_model.py` test, which needs both files and has not run. Rests on assumption **A1** (`risk: high`), the conservative reading of deferred blocking question **Q13** — see `traceability.md` § "Assumption linkage". Two planner open items: `A1.steps[]` does not list `M1-S01` (verifier W03), and `admin/sharing-and-visibility` — the skill the step's own `inputs.note` cites for `sharingModel` placement and for `check_sharing_model.py`'s file-suffix list — is not in this step's `skills[]`, so `recommended_skills` above carries the step's five rather than the skill this row actually rests on. |
