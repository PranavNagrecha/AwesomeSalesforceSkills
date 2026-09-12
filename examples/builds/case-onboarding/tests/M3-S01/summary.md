# M3-S01 — test summary

Step type `validation`, agent `metadata-builder`, status at entry `built`.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `xml` | always-on | pass (3/3 parsed) | — |
| `manifest` | always-on | pass (consistent) | — |
| `skills/admin/validation-rules/scripts/check_validation_rules.py --manifest-dir artefacts/M3-S01 --strict` | checker | pass (exit 0) | — |
| `check-outputs` | precondition | ok | — |
| W01 manual (bypass clause / blank-guard / component-field / message-quality) | manual | deferred to M3 gate — Given/When/Then shape present, observable outcomes named, checked against disk, not ticked | — |

Raw captures: `checker_stdout.txt`, `checker_stderr.txt` (empty), `check_outputs.json`, `xml_result.json`.

## Manifest derivation (Step 3)

`artefacts/M3-S01/package.xml` declares one `ValidationRule` types block with two explicit
members, no wildcard:

- `Case.Origin_Must_Be_Known`
- `Case.Priority_Required_On_Agent_Save`

Per `skills/devops/salesforce-dx-project-structure`, each file under
`objects/Case/validationRules/*.validationRule-meta.xml` derives a member `Case.<stem>` (object
from the enclosing `objects/Case/` directory, rule name from the file stem). Both derived
members appear in the manifest; both explicit members have a matching file. No excluded types
apply (`skills/devops/metadata-api-coverage-gaps` — `ValidationRule` has a standalone source
file). Two-way check: consistent.

## Manual test — checked against disk, not ticked

Grepped directly from the artefact files rather than inferred:

| Assertion | File | Result |
|---|---|---|
| `errorConditionFormula` opens with `NOT($Permission.Bypass_Case_Intake_Validation)` | both `.validationRule-meta.xml` | present in both |
| Blank test uses `ISBLANK(TEXT(<picklist>))`, not `ISPICKVAL(<picklist>, "")` alone | both | `Priority_Required_On_Agent_Save`: `ISBLANK(TEXT(Priority))`; `Origin_Must_Be_Known`: `ISBLANK(TEXT(Origin))` gates the blank case, `ISPICKVAL` is used only to enumerate the three valid values, never as the blank test |
| Custom permission `Bypass_Case_Intake_Validation` exists | `artefacts/M2-S01/customPermissions/Bypass_Case_Intake_Validation.customPermission-meta.xml` | exists |
| `errorMessage` <= 255 chars | both | `Origin_Must_Be_Known`: 218; `Priority_Required_On_Agent_Save`: 218 |
| `active` is `true` | both | `true` / `true` |
| No compound address field named (Q59) | both | formulas reference only `Priority` / `Origin`, no `BillingAddress`/etc. |

All six hold. This is a report of what the files say, not a tick — ticking is a human act at
the M3 milestone gate.
