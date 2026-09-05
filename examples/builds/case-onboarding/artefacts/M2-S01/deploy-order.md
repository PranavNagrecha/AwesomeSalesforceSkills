# M2-S01 — deploy order

Written by `agents/metadata-builder` Step 7. Sourced from
`skills/admin/custom-permissions/references/metadata-examples.md` ("Retrieve and deploy", "Where the
files live", "package.xml"), `skills/admin/custom-permissions/references/gotchas.md` #1, #4, #8 and #9,
`skills/admin/permission-set-architecture/references/metadata-examples.md` § 5, and
`skills/admin/change-management-and-deployment/references/metadata-examples.md` § 1 and § 3.

This step declares `depends_on: []` and produces one `CustomPermission` and one `PermissionSet`.

## Order inside this step

| # | Component | Because |
|---|---|---|
| 1 | `CustomPermission:Bypass_Case_Intake_Validation` | "A `PermissionSet` naming a custom permission that does not yet exist fails the deploy" — `custom-permissions/references/metadata-examples.md`, "Retrieve and deploy". The definition ships before the grant. |
| 2 | `PermissionSet:Case_Intake_Integration` | Grants the permission above through `<customPermissions>`. Both are in this step's one `package.xml`, so a single manifest deploy satisfies the ordering; the split-source form is `customPermissions/` first, `permissionsets/` second. |

No `requiredPermission` is declared, so the "required permission and its parent in one package" constraint
in the same section does not apply here.

## Dependencies on components outside this step

- **Nothing outside this step must exist first.** The `CustomPermission` file has no `<connectedApp>` and no
  `<requiredPermission>`, and the permission set carries no `objectPermissions`, `fieldPermissions`,
  `recordTypeVisibilities`, `tabSettings`, `applicationVisibilities`, `classAccesses` or `flowAccesses`, so
  it references no object, field, record type, tab, app, class or flow. It can deploy into an org that has
  none of M1's metadata.
- **This step deploys before M3-S01, and that ordering is load-bearing.** M3-S01 writes
  `Case.Priority_Required_On_Agent_Save` and `Case.Origin_Must_Be_Known`, each carrying
  `NOT($Permission.Bypass_Case_Intake_Validation)` as its outer AND term (Q56;
  `templates/admin/validation-rule-patterns.md`, "The canonical VR shape"). A validation rule whose
  `$Permission.X` names a permission that does not exist does not fail the deploy — it evaluates to
  `false` silently (`custom-permissions/references/gotchas.md` #4), which means every API-created Case is
  blocked from the moment M3-S01 lands until this step lands. Deploy this step first, or deploy both in
  one request.
- **`check_custom_permissions.py` cannot see that dependency at this scope.** With no validation rule in
  the scanned tree the checker reports `Consumers: 0` and an INFO, and exits 0. The consumer
  cross-reference is carried by M3's milestone test, which runs the same checker at
  `--manifest-dir artefacts --strict` once M3-S01's rules exist. That is the plan's own wording on this
  step's first acceptance test, restated here so a deployer does not read exit 0 as proof of the link.

## Record types and page layouts: what this step does NOT carry

Recorded here because `reports/MILESTONE-M1-REPORT.md` finding F-01 names `M2-S01` as the step that
carries `layoutAssignments`, and in plan version 5 it is not.

- **`layoutAssignments` has no home on `PermissionSet`.** "No layout element on `PermissionSet` at all" —
  `skills/admin/permission-sets-vs-profiles/references/metadata-examples.md` (element comparison table).
  The same fact is recorded from the other side in `artefacts/M1-S02/deploy-order.md`:
  "`layoutAssignments` lives only on `Profile`, never on `PermissionSet`."
- **The step that carries them is `M2-S03`**, "Minimal base profiles carrying only default app, default
  record type and layout assignment", whose declared outputs are
  `artefacts/M2-S03/profiles/Acme Support Tier 1.profile-meta.xml`,
  `.../Acme Support Tier 2.profile-meta.xml` and `.../Acme Billing.profile-meta.xml`. Those profiles are
  where the F-01 assertion becomes checkable, and they must name the M1 components in exactly these forms:

  | What | Exact form | Recorded in |
  |---|---|---|
  | Record types | `Case.Support`, `Case.Billing` | `artefacts/M1-S01/objects/Case/recordTypes/` |
  | Layouts | `Case-Case Support Layout`, `Case-Case Billing Layout` | `artefacts/M1-S02/deploy-order.md`, "Manifest member forms used" |

- **`recordTypeVisibilities` is `M2-S02`'s** on the permission-set side (the element appears on
  `PermissionSet` — `permission-set-architecture/references/metadata-examples.md` § 1) and `M2-S03`'s on the
  profile side. It is deliberately absent from `Case_Intake_Integration`: the integration identity creates
  Cases through the API, where record-type visibility is not the gate, and the step's own manual acceptance
  test requires this permission set to grant the custom permission "and nothing else".
- **F-01's remedy is therefore an M2 concern, not an M1 one, and not this step's.** Until `M2-S03` deploys,
  `check_record_type_layouts.py` still has zero `layoutAssignments` to resolve anywhere under `artefacts/`
  and will still be silent about having made no cross-check.

## Post-deploy step the deploy does not perform

`PermissionSetAssignment` is record data, not metadata — `permission-set-architecture/references/metadata-examples.md`
§ 4 assigns through Apex or Data Loader, not through a manifest. Nothing in this build assigns anything.

- **Assign `Case_Intake_Integration` to the Email-to-Case / Web-to-Case automated-process identity only.**
  No human user receives it. A human holding it silently stops being subject to the Case intake validation
  rules, and a metadata diff cannot later prove the grant was removed
  (`custom-permissions/references/gotchas.md` #8).
- **Named owner for that assignment: the Security architect.** That is the `owner_role` recorded on both
  clarifications this step binds — Q56 ("Which users and integrations must be able to save a Case the rule
  would reject?") and Q10 ("Are we adding access, or taking it away?") — in `plan.json.clarifications`. The
  same string is written into the `description` of both files so the owner survives a retrieve, which is the
  only place it can live: `description` is the sole free-text field on either type.
- **Evidence, not a diff.** Capture the `SetupEntityAccess` → `PermissionSetAssignment` query in
  `custom-permissions/references/metadata-examples.md`, "Verification: who actually holds the permission",
  with a timestamp, and read `PermissionSet.IsOwnedByProfile` to catch a grant that arrived through a
  profile instead (gotcha #1).

## Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `CustomPermission` | `Bypass_Case_Intake_Validation` — the file-name stem, which *is* the API name (no `<fullName>` in source format) | `custom-permissions/references/metadata-examples.md`, "Where the files live" and its `package.xml` sample |
| `PermissionSet` | `Case_Intake_Integration` — the file-name stem | `permission-set-architecture/references/metadata-examples.md`, "Where the files live" and § 5 |

Both types accept the `*` wildcard (`CustomPermission`: `api_meta.txt` L46738, quoted in the cited
reference; `PermissionSet`: "wildcard `*` allowed" in the permission-set reference's table). Both members
are named explicitly anyway, so the manifest agrees with the files on disk in both directions.

## Elements this step could NOT ground, and what was written instead

- **No `<isLicensed>`.** Deliberate omission, not an oversight: the field is "Required. Read-only." and the
  guide's own sample omits it (`custom-permissions/references/gotchas.md` #7).
- **No `<license>` on the permission set.** Q8 answers "leave `LicenseId` empty on the permission sets".
  The cited reference's own note agrees: populating `license` is "a deliberate statement" about the
  population, and this set's population is one automated-process identity whose licence is not on file.
- **No `<userPermissions>`, and specifically no `ApiEnabled`.** The integration identity plainly needs API
  access, but nothing in `requirement.md` or the answered clarifications says whether it arrives through
  this permission set, another one, or the identity's own profile — and `ApiEnabled` is in
  `check_access_model.py`'s `DANGEROUS_PERMISSIONS` set, so adding it unasked would both widen the step past
  its own manual acceptance test and fail that test's checker. Left out; a human granting API access to the
  integration identity does it somewhere this build does not model.
- **Permission-set naming.** `templates/admin/permission-set-patterns.md` gives integration bundles the form
  `Integration_<System>_Bundle` and feature sets the form `Feat_<Feature>`. The plan declares the output path
  `permissionsets/Case_Intake_Integration.permissionset-meta.xml`, and a declared output path is not this
  agent's to rename (`standards/build-orchestration.md` § 5). Written as declared; the divergence from the
  template is recorded, not corrected. That template is not in this step's `templates[]` (which is empty).

## Validate-only command for the human

`agents/metadata-builder` never runs this. It is text to copy.

M1 report finding **F-08** asked that the sandbox target get the sandbox form. Two commands, matched to
their target:

```
# Sandbox / scratch / Developer Edition target — checkOnly deploy, nothing is written.
sf project deploy start --dry-run --target-org <your-sandbox-alias> --manifest .sfskills/builds/case-onboarding/artefacts/M2-S01/package.xml
```

```
# Production target — the validate → quick-deploy sequence.
sf project deploy validate --target-org <your-production-alias> --manifest .sfskills/builds/case-onboarding/artefacts/M2-S01/package.xml --test-level RunLocalTests
```

The `--dry-run` spelling is grounded in `skills/devops/deployment-error-troubleshooting/SKILL.md` lines 144
and 172, which name it as the `checkOnly` deploy; that skill is outside this step's `skills[]` and is cited
here only for the flag. `deploy validate` and `--test-level RunLocalTests` are grounded in
`change-management-and-deployment/references/metadata-examples.md` § 3, which carries its own
UNVERIFIED (2026-09-04) caveat on `sf` CLI flag spellings: if a flag is rejected, run
`sf project deploy start --help` rather than guessing a synonym.
