# M3-S01 — deploy order and grounding notes

Two `ValidationRule` components on `Case`. Nothing here deploys anything; the validate-only
command at the bottom is text for a human to run.

## Order

| # | Component | Where it is built | Why it must precede the rules |
|---|---|---|---|
| 1 | `CustomObject Case`, `RecordType Case.Support` / `Case.Billing`, `StandardValueSet CaseOrigin`, `CustomField Case.Severity__c` | M1-S01 | `Origin_Must_Be_Known` names three `CaseOrigin` values by `fullName`; a formula compiles against the field, and the values it tests are the ones that value set defines |
| 2 | `Layout Case-Case Support Layout` / `Case-Case Billing Layout` | M1-S02 | `errorDisplayField` silently becomes Top of Page when the named field is not visible on the layout. Both rules name a field (`Priority`, `Origin`) that appears in `layoutItems` on both layouts |
| 3 | `CustomPermission Bypass_Case_Intake_Validation` | M2-S01 | Both `errorConditionFormula` values reference `$Permission.Bypass_Case_Intake_Validation`. A formula referencing a permission that does not exist yet evaluates it as false for everyone, so the rules would block the intake channels from the moment they land |
| 4 | `PermissionSet Case_Intake_Integration` | M2-S01 | Carries the permission. It can deploy with or after the rules, but nothing bypasses anything until it is *assigned*, which is an org action outside this build |
| 5 | **`ValidationRule Case.Origin_Must_Be_Known`, `ValidationRule Case.Priority_Required_On_Agent_Save`** | **this step** | — |

Within this step the two rules are independent: they guard different fields, neither reads the
other's outcome, and validation-rule evaluation order is undefined by design
(`skills/admin/validation-rules/references/gotchas.md`, "Validation Rules Fire in Undefined
Order"). One rule per concern is what keeps that harmless.

Both ship `active=true`. Q58: there are no existing Cases — support runs from a shared mailbox
today — so no record can be blocked by a rule that is live on arrival. The `active=false`
caveat in that answer applies to rules aimed at migrated Accounts or Contacts; neither of these
is.

## Source-format layout

```text
artefacts/M3-S01/
├── objects/Case/validationRules/Origin_Must_Be_Known.validationRule-meta.xml
├── objects/Case/validationRules/Priority_Required_On_Agent_Save.validationRule-meta.xml
├── package.xml
├── validation-bypass-note.md   (declared output)
└── deploy-order.md             (this file — written on every metadata-builder run)
```

Each file stem equals its rule's `fullName`, and a `ValidationRule` stem is the rule name
without the object prefix — the object comes from the enclosing `objects/Case/` directory, and
only the `package.xml` member carries the `Case.` prefix. The same file in metadata format
would be a `<validationRules>` element inside `objects/Case.object`; both shapes carry
identical children and `sf project deploy` converts one to the other.

`ValidationRule` does not support `*` in a manifest, so both members are named explicitly
(`skills/admin/validation-rules/references/gotchas.md`, "ValidationRule Does Not Support the
Wildcard in package.xml"). A wildcard here retrieves nothing and reports success.

## Marked as ungrounded

Each item below is something this step's artefacts depend on that the cited skills do **not**
confirm. They are recorded rather than resolved, per `standards/build-orchestration.md` § 8.

1. **The DX file suffix and directory.** `skills/admin/validation-rules/references/metadata-examples.md`
   carries its own marker: "UNVERIFIED (2026-09-04): the Metadata API Developer Guide documents
   only the metadata-format `.object` layout; the string `validationRule-meta` does not appear
   anywhere in it." The **element names and semantics** used here (`fullName`, `active`,
   `description`, `errorConditionFormula`, `errorDisplayField`, `errorMessage`) *are* confirmed
   by the guide's own field table, and are identical in both shapes. This build declares the DX
   path in `plan.json`, so the shape is the plan's choice, not this step's.
2. **The `Object.RuleName` manifest member form.** Marked UNVERIFIED in the same reference: the
   guide prints that form for the `CustomField` and `ListView` sub-components of CustomObject
   and shows no `ValidationRule` manifest sample. `Case.Priority_Required_On_Agent_Save` follows
   the documented sub-component pattern by analogy. M1-S01's manifest already uses the same form
   for `RecordType` and `CustomField` members and validated against an org
   (`reports/MOCK-DEPLOY-M2.md` run 2, 30 components, 0 errors), which is evidence for the
   pattern but not for this type.
3. **No documented cap on `ValidationRule.description`.** The skill's element table gives
   `errorMessage` an explicit 255-character ceiling and says only "free text" for `description`.
   Both descriptions here are held under 200 characters anyway, as a precaution inferred from
   `reports/MOCK-DEPLOY-M2.md` F-15, where `PermissionSet.description` and `Profile.description`
   failed an org validate at over 255. **That is a cross-type inference, not a documented
   `ValidationRule` limit** — the rationale those descriptions would otherwise carry is in this
   file instead, which is the remedy F-15 itself prescribes.
4. **The unrecognised-value half of `Origin_Must_Be_Known`.** The blank test is plainly
   grounded. Whether a value *outside* the `CaseOrigin` standard value set can reach `Origin`
   at all — through the API, or as a retained inactive standard value — is documented in neither
   cited skill. The three values tested are read off
   `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml`, so the clause is
   correct about what is allowed; it may be redundant if the platform already rejects the rest.
   Redundant is the safe direction here, and `NOT(OR(ISPICKVAL(...)))` is the documented shape
   for a picklist inequality (`references/llm-anti-patterns.md`, Anti-Pattern 6).
5. **A12 is the assumption that decides whether these rules are invariants.** Q55 was deferred.
   If any automation writes `Priority` or `Origin` after save, a committed Case can violate an
   active rule: custom validation rules are not re-run after a workflow field update re-saves
   the record (`references/gotchas.md`). The rules are correct either way; what is unproven is
   that they are *unbypassable*. M4-S03's before-save flow is the assumed sole writer.
6. **What the step's declared checker does not check.** The `acceptance_tests[0].description`
   in `plan.json` says the checker verifies "every field token in every formula resolves" and
   "an `errorDisplayField` that resolves". `check_validation_rules.py` does neither — it has no
   field inventory. `Priority`, `Origin` and the `$Permission` name were checked against
   M1-S01, M1-S02 and M2-S01 by hand while writing this step; the exit code does not carry that.

## Validate-only command for a human

Nothing in this build runs it. `checkOnly` validates and commits nothing:

```bash
sf project deploy start --dry-run \
  --source-dir .sfskills/builds/case-onboarding/artefacts/M3-S01/objects \
  --target-org <sandbox-alias>
```

Deploy M2-S01's custom permission first, or in the same request — a dry run of these two files
alone cannot resolve `$Permission.Bypass_Case_Intake_Validation` unless the org already has it.
The repo's own harness does the same assembly across steps:

```bash
python3 scripts/mock_deploy.py plan.json --org-alias <alias> --step M1-S01 --step M2-S01 --step M3-S01
```
