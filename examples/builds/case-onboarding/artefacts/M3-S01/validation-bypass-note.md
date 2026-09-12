# M3-S01 — the Case intake validation bypass

Two validation rules, one bypass. This note is the step's declared record of the bypass
contract: which permission suppresses the rules, who holds it, what breaks without it, and
how a human proves both halves work. The rules themselves are under
`objects/Case/validationRules/`.

## The two rules

| Rule (`fullName`) | Fires when | `errorDisplayField` | `active` |
|---|---|---|---|
| `Priority_Required_On_Agent_Save` | `Priority` is blank and the saver does not hold the bypass | `Priority` | `true` |
| `Origin_Must_Be_Known` | `Origin` is blank, or is not one of `Email-Support` / `Email-Billing` / `Web`, and the saver does not hold the bypass | `Origin` | `true` |

Both formulas open with the bypass clause, so the whole rule short-circuits for a holder:

```
AND(
  NOT($Permission.Bypass_Case_Intake_Validation),
  ...
)
```

The clause order — bypass, then relevance gate, then business condition — is the canonical
order in `skills/admin/validation-rules/references/metadata-examples.md` ("Bypass clause is
first inside the `AND`") and in that skill's `templates/validation-rule-template.md`.

## The bypass

| Thing | Value | Where it lives |
|---|---|---|
| Custom Permission | `Bypass_Case_Intake_Validation` | `artefacts/M2-S01/customPermissions/Bypass_Case_Intake_Validation.customPermission-meta.xml` |
| Permission Set that carries it | `Case_Intake_Integration` | `artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml` |
| Who holds it | the Email-to-Case and Web-to-Case intake identities only (Q56) | assignment is an org action, outside this build |
| Formula reference form | `$Permission.Bypass_Case_Intake_Validation` | `skills/admin/custom-permissions/references/metadata-examples.md` L115, L124 |

The custom permission file carries no `<fullName>` element: in DX source format
`CustomPermission` inherits `fullName` and the CLI derives it from the file stem, so **the stem
is the API name**. Renaming that file breaks both `$Permission.` references here silently —
the formula evaluates a missing permission as false for everyone, the bypass stops working,
and every API-created Case starts failing on Priority
(`skills/admin/custom-permissions/references/metadata-examples.md` L21).

## Why the bypass exists at all

Q5 settled that Priority and Origin are enforced at validation-rule level rather than by
Layout Required, because Email-to-Case and Web-to-Case create Cases through the API and the
API ignores layout requiredness. Q56 settled the consequence: a rule aimed at agents blocks
those two channels unless the intake identities are exempt. Roughly 460 of the ~480 Cases a
day arrive that way (requirement.md), so a rule with no bypass would reject most of the day's
intake at the door rather than improve its data quality.

`references/gotchas.md` in the validation-rules skill states the same rule from the other
direction: never deactivate rules in production to get a load through — bypass with a Custom
Permission granted by a Permission Set, and revoke the assignment when the load is done.

## What a human still has to prove

The step's checkers prove the XML is well-formed and the formulas are clean. Neither half of
the bypass contract is provable without an org, so both are listed here for the sandbox proof
the requirement asks for ("We must be able to prove it works in a sandbox before customers
see it"):

| Scenario | Expected | Proves |
|---|---|---|
| Agent saves a Case with `Priority` blank | error, inline on `Priority` | the rule fires, and `errorDisplayField` did not relocate to Top of Page |
| Agent saves a Case with `Origin` blank | error, inline on `Origin` | same, for the second rule |
| Intake identity (holding `Case_Intake_Integration`) creates a Case with `Priority` and `Origin` blank through the API | saves | the bypass suppresses both rules |
| Same identity after the Permission Set is unassigned | fails | the bypass is what is doing the work, not something else |

The last two are the pair that `skills/admin/validation-rules/references/metadata-examples.md`
Test 2 exists for: an edit that drops the `NOT($Permission...)` clause, or a rename of the
custom permission, leaves the first two scenarios green and only these two red.

## Open items this note does not close

- **A11 / Q54** — both rules guard fields the user edits on the Case itself, so the
  child-record blind spot in the gotchas does not apply here. Recorded, not proven.
- **A12 / Q55** — if any automation writes `Priority` or `Origin` *after* save, neither rule is
  a database invariant: custom validation rules are not re-run after a workflow field update
  re-saves the record. M4-S03's before-save stamping flow is the assumed only writer.
- **A13 / Q57** — `Priority` and `Origin` both appear in `layoutItems` on both Case layouts in
  `artefacts/M1-S02/layouts/`, which is the strongest evidence available without an org; layout
  *visibility* per profile is not readable from the artefacts.
