# Mock deploy — milestone M5 in progress (validation only, nothing deployed)

## Run 1 — 2026-09-12, source mode, every built step M1-S01 … M4-S05 + M5-S01 (API 67.0)

**Failed — 60 components, 59 ok, 2 errors.** All three list views and the `ReportFolder Support_Operations` validated
(the folder's declared filename `Support_Operations-meta.xml` is accepted by the org — the step's F-B is a checker
recognition gap only). F-28 unchanged. New:

| Component | Error |
|---|---|
| `Report Support_Operations/Escalated_Open_Cases` | `Value too long for field: Description maximum length is:255` |

**F-49 (HIGH, build + skill).** The builder put its UNVERIFIED note into the report's `<description>`; the limit is 255.
`admin/reports-and-dashboards` has no description-length rule (the DESC rule family covers PermissionSet/Profile/
CustomPermission/CustomObject; Report needs one). Rebuild: description ≤ 255, notes stay in deploy-order.md.

## Operator probes on a scratch copy (nothing in the build changed)

With the description shortened, the org moved on to the report body:

| Probe | Result |
|---|---|
| `<reportType>Cases</reportType>` (the skill's UNVERIFIED value) | `invalid report type` |
| `<reportType>CaseList</reportType>` | accepted — validation moved to the grouping |
| grouping `USERS.NAME` (from the skill's example) | `Grouping: Invalid value specified: USERS.NAME` |
| grouping `OWNER` | accepted — validation moved to `You can't include groupings in the selected columns list: PRIORITY` (PRIORITY is both a column and a grouping in the built file — structural, fix by dropping one) |
| grouping `OWNER_NAME` | invalid |
| escalated filter column `ESCALATED`, `IS_ESCALATED`, `CASES.ESCALATED`, `ISESCALATED`, `CASE_ESCALATED` | all `filters-criteriaItems-column: Invalid value specified` |

**F-50 (HIGH, build + skill).** The standard Case report type's API name is `CaseList`, not `Cases`; the owner grouping
column is `OWNER`, not `USERS.NAME`; a field cannot be both a `<columns>` entry and a grouping. All three came from the
skill's example (marked UNVERIFIED there) and are now proven live.

**F-51 (MEDIUM, unresolved).** The `Case.IsEscalated` report column code could not be found by probing (five candidates
rejected). Per the skill's own rule, column codes are harvested from an org retrieve of an existing report — the honest
path is a deploy runbook step: deploy the report without the criterion, add "Escalated = True" in the report builder
(or retrieve one saved Case report to harvest the code), then re-export. Recorded, not guessed.

## Run 2 — 2026-09-12, source mode, every built step M1-S01 … M5-S01 after the F-49/F-50 rebuild (API 67.0)

**60 components, 60 ok, 1 error — F-28 only.** `Report Support_Operations/Escalated_Open_Cases` (`CaseList`, grouping
`OWNER` then `PRIORITY`, 219-char description, Escalated criterion deferred to the runbook per F-51) and its folder
validate. F-49 and F-50 closed in the build; the skill-side rules follow. Output: `reports/mock-deploy/2026-09-12T09-54-56Z/`.

## Run 3 — 2026-09-12, MANIFEST mode, every built step M1-S01 … M5-S05 (the merged package.xml, incl. the build-level M5-S05 manifest; API 67.0)

**Failed — 60 total, 60 ok, 1 error(s).**

| Component | Error |
|---|---|
| AutoResponseRule | Case.Case_Acknowledgement | FAIL — support-noreply@acme.example is an invalid From email address.: Email Address |

This is the first validation in the build that reads a manifest carrying the Apex (M4-S05's trigger and classes) — F-43 closed.

Still to validate for M5: nothing after this run; M5-S02 stays blocked.
