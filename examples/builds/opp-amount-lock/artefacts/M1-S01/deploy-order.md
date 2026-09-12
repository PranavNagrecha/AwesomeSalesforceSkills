# Deploy order — M1-S01 (Amount_Locked_After_Closed_Won)

Build: `opp-amount-lock` · Step: `M1-S01` · Manifest: `package.xml` (`<version>67.0</version>`)
**Rebuild**: run `2026-09-12T07-45-00Z` replaces run `2026-09-12T07-15-00Z`. See "Why this step was rebuilt" below.

## The three components

| # | Type | Member | File |
|---|---|---|---|
| 1 | `CustomPermission` | `Bypass_Opp_Amount_Lock` | `customPermissions/Bypass_Opp_Amount_Lock.customPermission-meta.xml` |
| 2 | `PermissionSet` | `Opp_Amount_Lock_Bypass` | `permissionsets/Opp_Amount_Lock_Bypass.permissionset-meta.xml` |
| 3 | `ValidationRule` | `Opportunity.Amount_Locked_After_Closed_Won` | `objects/Opportunity/validationRules/Amount_Locked_After_Closed_Won.validationRule-meta.xml` |

Components 1 and 2 are byte-identical to the previous run. Only component 3 changed.

## Why this step was rebuilt

The previous run emitted a four-clause formula, omitting the blank guard, because the invoking brief
restated the plan input in a shortened form. `plan.json` is the single authority for a step's inputs, so the
step was reset (`built` → `failed` → `pending`) and amended rather than accepted.

The amendment did not simply restore the old guard. `plan.json.steps[].amendments[0]` records an operator
dry-run probe against a scratch org at API 67.0:

- `NOT(ISBLANK(StageName))` — the form the plan previously carried, copied from the "GOOD" block in
  `skills/admin/validation-rules/SKILL.md` § Formula Best Practices — **does not compile**:
  *"Field StageName is a picklist field. Picklist fields are only supported in certain functions."*
- `NOT(ISBLANK(TEXT(StageName)))` — the form the plan now carries — **validates 3/3**.

So the skill's headline guidance was wrong and its own `references/llm-anti-patterns.md` was right:
Anti-Pattern 6, "With null handling", prints `NOT(ISBLANK(TEXT(Status)))` — the same shape, on a different
field — and states the rule directly: *"Use TEXT() to convert picklist to text."* The skill is being
corrected in parallel, and a new checker rule `VR-PICK-01` will flag `ISBLANK` applied to a raw picklist.
Acceptance test 0's description already asserts that `VR-PICK-01` must not fire against this artefact.

This artefact is now generated from `plan.json.steps[].inputs` directly: the emitted
`errorConditionFormula`, parsed back out with ElementTree, is byte-identical to the plan's string.

## Ordering constraints

1. **`CustomPermission` before `PermissionSet`.** The permission set carries a *grant*, not the
   definition: `PermissionSet` and `Profile` "do not carry the permission's definition — only a grant
   of a permission that must already exist", and "A `PermissionSet` naming a custom permission that
   does not yet exist fails the deploy"
   (`skills/admin/custom-permissions/references/metadata-examples.md`, "Where the files live" and
   "Retrieve and deploy").

2. **`CustomPermission` before `ValidationRule`.** The rule's formula reads
   `$Permission.Bypass_Opp_Amount_Lock`. The same reference section states the rule: deploy
   definitions "before any consumer that references them". The consumer here is the validation rule's
   `errorConditionFormula`.

3. **`PermissionSet` and `ValidationRule` are siblings** — neither references the other, so their
   relative order does not matter once (1) and (2) hold.

4. **One request is the safe shape.** All three members are in this step's `package.xml`, so a single
   `sf project deploy` request resolves 1–3 internally. Splitting the deploy is only necessary if the
   org already holds part of the set. `skills/devops/metadata-api-retrieve-deploy/references/gotchas.md`
   (L124) names `PermissionSet` ↔ `CustomPermission` ↔ custom-field cycles as a known
   "validation passes / deploy fails" hazard when cross-type references are split across requests —
   another reason to keep these three together.

5. **Dependency-driven sequence, if this step is folded into a larger release.**
   `skills/admin/change-management-and-deployment/references/llm-anti-patterns.md` (Anti-Pattern 4)
   orders a release: data model → code → flows → layouts/record types → **permission sets and
   profiles** → sharing rules → reports. This step contributes only to the "permission sets" band plus
   the object-embedded validation rule, so it deploys after any field or record-type change in the same
   release and before nothing.

## Dependencies on components outside this step

**None.** All three fields the formula touches — `Amount` (Currency), `StageName` (Picklist), and
`StageName` again through `TEXT()` — are standard Opportunity fields already present in every target org;
no step in this build creates them. The rule is not scoped to a record type, so no `RecordType` is a
prerequisite. `depends_on` for `M1-S01` is empty in `plan.json`, and this note confirms that is correct
rather than an omission.

## Values not supplied by the plan

The `<label>` element on the `CustomPermission` and on the `PermissionSet` is **derived**, not answered.
Neither cited skill has a `## Questions to Ask Before Configuring` row covering a label, and no step input,
clarification answer, upstream artefact or line of `requirement.md` supplies one. Both were produced by
de-underscoring the API name — the same transform the skill's own examples use
(`Bypass_Validation_Rules` → "Bypass Validation Rules"):

| File | API name (authoritative — it is the filename stem) | `<label>` (derived) |
|---|---|---|
| `customPermissions/Bypass_Opp_Amount_Lock.customPermission-meta.xml` | `Bypass_Opp_Amount_Lock` | Bypass Opportunity Amount Lock |
| `permissionsets/Opp_Amount_Lock_Bypass.permissionset-meta.xml` | `Opp_Amount_Lock_Bypass` | Opportunity Amount Lock Bypass |

Change either label freely before deploy — a label is display text and nothing references it. The API names
are load-bearing and must not change: the custom permission's stem **is** its API name, and
`$Permission.Bypass_Opp_Amount_Lock` in the rule plus `<name>Bypass_Opp_Amount_Lock</name>` in the
permission set both resolve against it.

## Post-deploy, not part of the deploy

- Assign `Opp_Amount_Lock_Bypass` to the **two named Sales Ops users** (clarification Q3). The
  permission set deploys empty of assignees; an unassigned bypass is a bypass nobody holds.
- Assumption **A1** (`PLAN.md`): `Amount` is on the Opportunity page layout(s) in scope. If it is not,
  `errorDisplayField` "changes automatically to Top of Page"
  (`skills/admin/validation-rules/references/metadata-examples.md`, element table) and the error
  silently relocates. Confirm on the layout after deploy.
- Decision **D2** (`PLAN.md`): the rule deploys `active=true` against data that already contains a
  handful of lowered Closed Won Amounts. The delta check (`Amount < PRIORVALUE(Amount)`) means those
  records are not re-blocked on unrelated edits, but they stay non-conforming by design.

## Validate-only command — the human runs this, no agent does

```bash
sf project deploy validate \
  --manifest .sfskills/builds/opp-amount-lock/artefacts/M1-S01/package.xml \
  --source-dir .sfskills/builds/opp-amount-lock/artefacts/M1-S01 \
  --target-org <alias>
```

`sf project deploy validate` is documented for a **production** target and requires Apex tests; against
a sandbox use `sf project deploy start --dry-run` instead
(`agents/_shared/AGENT_CONTRACT.md`, Gate C). A validate-only deploy proves the XML parses and the
formula compiles — which is exactly the check that caught the previous guard form, and exactly the reason
this step was rebuilt. It does **not** prove the bypass works: that needs the two Apex tests in
`skills/admin/validation-rules/references/metadata-examples.md` ("Apex tests", Test 1 and Test 2), or the
manual acceptance line on milestone `M1`.

Nothing in this build deploys. This file is text for a human to copy.
