# Deploy order — M2-S01

Build: `northwind-sales` · Milestone: M2 (Guidance, guardrails and who may bypass them) · Step type: `access` · API version 62.0

This note is written by `agents/metadata-builder` Step 7 and is text for a human. Nothing in it is
executed by this agent or by any acceptance test.

Sourced from `skills/admin/custom-permissions/references/metadata-examples.md` ("Where the files live",
"5. The permission set that grants it", "package.xml", "Retrieve and deploy", "Verification: who
actually holds the permission"), `skills/admin/custom-permissions/references/gotchas.md` #1, #4, #7, #8,
#9 and #10, `skills/admin/permission-set-architecture/references/metadata-examples.md` §§ 1, 2, 4, 5
and 7, `skills/admin/permission-set-architecture/references/gotchas.md` ("Capability Bundles Break At
License Boundaries", "A Partial Permission Set File Is A Revocation", "Object And Field Permissions
Vanish From A Retrieve That Omits The Object"), `templates/admin/validation-rule-patterns.md` ("The
canonical VR shape", "Bypass contract"), and
`skills/admin/change-management-and-deployment/references/metadata-examples.md` §§ 1 and 3.

## 0. Why API version 62.0

`plan.json` carries no `api_version`, so `agents/metadata-builder/AGENT.md` ("Inputs") falls back to
`62.0`. That is also what M1 already shipped: `artefacts/M1-S01/package.xml` and
`artefacts/M1-S02/package.xml` both carry `<version>62.0</version>`, and
`artefacts/M1-S01/deploy-order.md` states it in its header line. Keeping 62.0 here means
`scripts/mock_deploy.py`'s `pick_api_version` (highest `<version>` across the selected steps) sees one
version across the whole build rather than a step that silently raises it.

## 1. Order inside this step

This step declares `depends_on: []` and produces one `CustomPermission` and one `PermissionSet`.

| # | Component | Because |
|---|---|---|
| 1 | `CustomPermission:Bypass_Opportunity_Sales_Validation` | "A `PermissionSet` naming a custom permission that does not yet exist fails the deploy" — `custom-permissions/references/metadata-examples.md`, "Retrieve and deploy". The definition ships before the grant. |
| 2 | `PermissionSet:Sales_Ops_Validation_Bypass` | Grants the permission above through its one `<customPermissions>` node. Both members are in this step's single `package.xml`, so one manifest deploy satisfies the ordering; a split-source deploy runs `customPermissions/` first, then `permissionsets/`. |

No `<requiredPermission>` is declared, so the "required permission and its parent in one package"
constraint in the same section does not apply here.

## 2. Dependencies on components outside this step

- **Nothing outside this step has to exist first.** The `CustomPermission` file carries no
  `<connectedApp>` and no `<requiredPermission>`; the permission set carries no `objectPermissions`,
  `fieldPermissions`, `recordTypeVisibilities`, `tabSettings`, `applicationVisibilities`,
  `classAccesses`, `flowAccesses` or `license`, so it references no object, field, record type, tab,
  app, class, flow or licence. It deploys into an org that holds none of M1's metadata.
- **This step must deploy before — or in the same request as — M2-S03 and M2-S04, and that ordering is
  load-bearing.** Both rules put `NOT($Permission.Bypass_Opportunity_Sales_Validation)` first inside
  their outer `AND`, which is the bypass-first contract in `templates/admin/validation-rule-patterns.md`
  ("The canonical VR shape"). A `$Permission.X` naming a permission the org does not hold does **not**
  fail the deploy — it evaluates to `false` silently (`custom-permissions/references/gotchas.md` #4).
  If M2-S03 lands before this step, the discount cap is live with no escape hatch for anyone, including
  the sales-ops admin, until this step lands.
- **The API name is the contract, character for character.** `Bypass_Opportunity_Sales_Validation` is
  the file-name stem (there is no `<fullName>` in source format — `custom-permissions/references/metadata-examples.md`,
  "Where the files live"), the `<name>` inside the permission set, and the token both M2-S03's and
  M2-S04's formulas resolve. Renaming any one of the three breaks the other two silently (gotcha #4).
  The name satisfies the stricter-than-folklore `DeveloperName` rules in gotcha #9 — begins with a
  letter, alphanumerics and single underscores only, no trailing underscore, no `__`, 35 of 80
  characters used.
- **`check_custom_permissions.py` cannot see the consumer link at step scope.** Run inside
  `artefacts/M2-S01` the tree holds no validation rule, so the coverage table reports `Consumers 0` and
  exits 0. The step's own first acceptance test is therefore declared `scope: build` with
  `--manifest-dir artefacts`, and milestone M2 runs the same checker across the whole tree. Do not read
  a green step-scope run as proof that the bypass is wired to anything.

## 3. Field-level security: which kind of permission set this is

Stated explicitly because the answer differs by set, and reading it off the file is what
`skills/admin/permission-sets-vs-profiles` (`references/gotchas.md`, `references/llm-anti-patterns.md`
`PSVP-FLS-01`) exists to stop people getting wrong:

- **This is a bypass/function set, not a persona set.** It grants exactly one custom permission and
  nothing else. It carries **no `objectPermissions` and no `fieldPermissions` at all**, which is the
  shape `permission-set-architecture/references/metadata-examples.md` § 2 documents for a function set
  ("No object rows — those belong in the object-access set").
- **So it needs no FLS rows, and that is a decision rather than an omission.** `PSVP-FLS-01` (WARN)
  fires on a set that grants `allowCreate`/`allowEdit` on an object with no standard-field
  `fieldPermissions` for it. This set grants no object access, so the rule does not apply. The rule
  that a persona set must list every field its users need — standard fields carry FLS too — governs
  M2-S02's record-type/layout work, not this file.
- **Where the sales-ops admin's field access actually comes from: their profile.** Q19 answers that the
  sales-ops admin holds **System Administrator**, and the 12 reps and 2 managers hold the standard Sales
  User profile with a Sales Cloud permission set. Nothing in this step widens or narrows that. If a
  future org ever assigns this set to a user without the underlying field access, the bypass will let
  them past the validation rules and FLS will still stop them editing `Discount__c` — two different
  gates, and this file is only the first.

## 4. Post-deploy steps the deploy does not perform

- **Assignment is record data, not metadata.** `PermissionSetAssignment` is inserted through Apex or
  Data Loader (`permission-set-architecture/references/metadata-examples.md` § 4); no manifest assigns
  anything, and nothing in this build assigns anything. Assign `Sales_Ops_Validation_Bypass` to the
  **sales-ops admin and to nobody else** (Q13: "Only the sales-ops admin may bypass … no integrations
  write Enterprise opportunities"; Q27: the rep submits the approval, and the sales-ops admin acts on a
  rep's behalf only through this exceptional path).
- **Expiry was considered and not applied.** `PermissionSetAssignment.ExpirationDate` (API 52.0+) is the
  platform's time-boxing mechanism (`permission-set-architecture/references/metadata-examples.md` § 4;
  `admin/permission-set-expiration`). No answered clarification puts an end date on this grant — it is a
  standing capability of the sales-ops admin role, not a migration window — so no expiry is recorded.
  If the grant is ever handed to a person for a data fix rather than to the role, use an expiring
  assignment instead of this set.
- **Q17's chatter-post record is a process instruction, not metadata.** "When a rule or approval is
  wrong for a deal, the sales-ops admin uses the bypass permission and records why in a chatter post on
  the record." Nothing in `CustomPermission` or `PermissionSet` can enforce that; the plan puts it in
  the cutover runbook at M4-S04, and this note repeats it so the deployer knows the control is human.
- **Evidence is a query, not a diff.** After deploy, capture the `SetupEntityAccess` →
  `PermissionSetAssignment` query in `custom-permissions/references/metadata-examples.md`
  ("Verification: who actually holds the permission") with a timestamp, and read
  `PermissionSet.IsOwnedByProfile` on the result: `true` means the grant arrived through a profile
  rather than through this set (gotcha #1). A metadata diff can never prove a revocation, because only
  enabled grants are ever retrieved (gotcha #8).
- **Never hand-merge this permission set file.** In API 40.0+ a permission omitted from a deployed
  permission set is disabled — "A Partial Permission Set File Is A Revocation"
  (`permission-set-architecture/references/gotchas.md`). If this set ever grows, retrieve the org's
  current file first and edit that.

## 5. Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `CustomPermission` | `Bypass_Opportunity_Sales_Validation` — the file-name stem, which *is* the API name | `custom-permissions/references/metadata-examples.md`, "Where the files live" and its `package.xml` sample |
| `PermissionSet` | `Sales_Ops_Validation_Bypass` — the file-name stem | `permission-set-architecture/references/metadata-examples.md`, "Where the files live" and § 5 |

Both types accept the `*` wildcard (`CustomPermission`: `api_meta.txt` L46738, quoted in the cited
reference; `PermissionSet`: "wildcard `*` allowed" in the permission-set table). Both members are named
explicitly anyway, so the manifest and the files on disk agree in both directions — which is what the
step's `manifest` acceptance test asserts, and what makes the deploy complete: "Metadata API references
the components listed in the manifest, not the directories in the .zip file"
(`change-management-and-deployment/references/metadata-examples.md` § 1).

## 6. Elements deliberately not written, and why

- **No `<isLicensed>`.** The Metadata API guide marks it "Required. Read-only." and its own sample omits
  it; deploying it does not make the permission licence-gated (`custom-permissions/references/gotchas.md`
  #7).
- **No `<license>` on the permission set.** Q19 names profiles, not licences, so the licence boundary of
  the holder population is not on file. The Object Reference's guidance, quoted in
  `permission-set-architecture/references/metadata-examples.md` § 2, is to leave `LicenseId` empty when a
  set may be held by users on different licences; populating it would be "a deliberate statement" this
  build cannot make. Recorded as an ambiguity, not a default.
- **No `<userPermissions>`.** Nothing in the answered clarifications asks this set to carry a system
  permission, and the step's own manual acceptance test requires that it grant "exactly one custom
  permission … no objectPermissions, no fieldPermissions and no userPermissions".
- **`<hasActivationRequired>false</hasActivationRequired>` is written explicitly.** Both cited references
  write it out at `false` on purpose (`permission-set-architecture/references/metadata-examples.md` §§ 1
  and 2; the `custom-permissions` § 5 sample carries the same line). A session-based set stops requiring
  activation once it is inside a permission set group — `permission-set-architecture/references/gotchas.md`,
  "A Session-Based Permission Set Stops Requiring Activation Inside A Group" — so `false` here is the
  honest statement that this bypass is not step-up-protected, rather than a silent default.
- **Naming divergence, recorded not corrected.** `templates/admin/validation-rule-patterns.md` ("Bypass
  contract") gives the per-domain form `Bypass_Validation_<Domain>`, which would be
  `Bypass_Validation_Opportunity`. `plan.json` declares the output path
  `customPermissions/Bypass_Opportunity_Sales_Validation.customPermission-meta.xml`, and a declared
  output path is not this agent's to rename (`standards/build-orchestration.md` § 5; `AGENT.md` Step 5
  rule 2). Written as declared. The same template also asks every rule to admit an
  `Integration_Bypass__c` hierarchy custom setting alongside the custom permission; Q13 answers that no
  integration writes Enterprise opportunities, so no custom setting is in this build's scope and none is
  written here.
- **Description lengths were sized to the checkers, not to the limits.** `CustomPermission.description`
  is 197 characters and `PermissionSet.description` is 181 — both under the 200-character headroom line
  (`CP-DESC-02`, `PSA-DESC-02`, both INFO-tier) and well under the 255-character deploy ceiling
  (`CP-DESC-01`, `PSA-DESC-01`, both ERROR). The step's own `inputs.note` asked for under 200 after a
  fixture run of a 237-character description raised `CP-DESC-02`. Everything that did not fit — the
  rationale, the owner's obligations, the assignment instruction — is in this file, which is exactly
  where both skills say to put it.

## 7. Validate-only command for a human

`agents/metadata-builder` never runs this. It is text to copy.

This build validates against an org through the repo's own script, which assembles the selected steps'
artefacts and hands them to `sf project deploy start --dry-run` (`checkOnly: true`). `--dry-run` is
hard-coded inside the script and there is no flag that can turn it off, so nothing about the dry run is
the operator's to pass or to forget:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <your-sandbox-alias> \
  --step M2-S01 \
  --mode manifest
```

`--mode manifest` matches how M1 was validated (`reports/MOCK-DEPLOY-M1.md`: `--mode manifest
--milestone M1`) and deploys exactly the two members in this step's `package.xml`. Results land under
`reports/mock-deploy/<UTC timestamp>/`.

Validating this step **together with M2-S03 and M2-S04** (`--milestone M2`, once those steps are built)
is the run that actually exercises the `$Permission` reference, because a validation rule whose token
resolves to nothing still validates green on its own (§ 2 above).

For a production target the sequence is different — `sf project deploy validate` returning a job id,
then `sf project deploy quick` — per `change-management-and-deployment/references/metadata-examples.md`
§ 3, which carries its own UNVERIFIED (2026-09-04) caveat on `sf` CLI flag spellings: if a flag is
rejected, run `sf project deploy validate --help` rather than guessing a synonym.
