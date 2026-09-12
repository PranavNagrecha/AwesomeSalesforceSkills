# Deploy order — M2-S03 (minimal base profiles)

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was deployed.

Three `Profile` files carrying only what a profile alone can hold — the default app, the
default record type, and the page layout assignments (Q7, Q3). Every object, field and tab
grant for these three personas lives in the M2-S02 permission sets.

**This step closes M1 finding F-01.** Until now no `layoutAssignments` element existed
anywhere in `artefacts/`, so `check_record_type_layouts.py --manifest-dir artefacts` had
nothing to cross-check and its layout assertion was never actually made. With these three
files present the build-scope run resolves 9 layout-assignment references and 12 record-type
references against M1-S01's record types and M1-S02's layouts, and exits 0 on 0 findings.
A negative fixture (one `Case-Ghost Layout`, one `Case.Nonexistent`) exits 1 under `--strict`
with both dangling references named — so the exit code now carries the cross-reference the
acceptance test's description claims it does.

## Order inside this step

| # | Component | Type | Why it must come at this point |
|---|---|---|---|
| 1 | `Acme Support Tier 1`, `Acme Support Tier 2`, `Acme Billing` | `Profile` | Single type, no intra-step ordering. All three are deployed by one `package.xml`. |

## Dependencies on components OUTSIDE this step

Every reference below must exist in the target org (or travel in the same request) before
this manifest validates, or the deploy fails on a dangling reference:

| Needed | Built by | Referenced from |
|---|---|---|
| `Layout` `Case-Case Support Layout` | M1-S02 `layouts/Case-Case Support Layout.layout-meta.xml` | `layoutAssignments.layout` in all three profiles (master + `Case.Support`) |
| `Layout` `Case-Case Billing Layout` | M1-S02 `layouts/Case-Case Billing Layout.layout-meta.xml` | `layoutAssignments.layout` in all three profiles (`Case.Billing`; master on Acme Billing) |
| `RecordType` `Case.Support` | M1-S01 `objects/Case/recordTypes/Support.recordType-meta.xml` | `layoutAssignments.recordType` and `recordTypeVisibilities.recordType` in all three |
| `RecordType` `Case.Billing` | M1-S01 `objects/Case/recordTypes/Billing.recordType-meta.xml` | `layoutAssignments.recordType` and `recordTypeVisibilities.recordType` in all three |
| `CustomObject` Case | M1-S01 `objects/Case/Case.object-meta.xml` | Carries the record types the two elements above name |

So the deploy order across the build is **M1-S01 → M1-S02 → M2-S03**. M2-S02's permission
sets are a `depends_on` of this step in the plan but not a *deploy* prerequisite of it:
nothing in these three files names a permission set. The dependency is a design one — the
profiles are minimal only because the permission sets already carry the grants — and the
operational ordering rule from `skills/admin/permission-sets-vs-profiles/references/gotchas.md`
("The 'Minimum Access' Base Profile Pattern") points the same way: assign the base PSG
*before* switching users onto a stripped profile, or they are stranded with no access at all.

The standard app `standard__Service` is platform-provided and is not deployed by this build.
It is the same app `Case_Agent_Core` already makes visible in M2-S02; this step adds only the
`<default>true</default>` marker, which has no permission-set equivalent.

**Not a member of this step's `package.xml`.** The Metadata API rule that a profile retrieve
returns security settings only for the other types in the same manifest is a *retrieve* rule
(`permission-sets-vs-profiles/references/gotchas.md`, "A Profile Retrieve Returns Only What
the Rest of the Manifest Asked For"). Adding `RecordType`, `Layout` or `CustomObject` members
here would declare members with no backing file in `artefacts/M2-S03/`, which the always-on
manifest acceptance test fails in the other direction. A human who later *retrieves* these
profiles must use a manifest that names the Case object, both record types and both layouts —
retrieve them narrowly and the committed profiles lose assignments they actually have
(record-types gotcha #7).

## Decisions worth reading before deploy

1. **Every profile carries a layout assignment for BOTH record types plus the master.**
   Three `layoutAssignments` blocks each: one with no `recordType` (the fall-through
   assignment, which `record-types-and-page-layouts/references/metadata-examples.md` documents
   as "omit it for the assignment that applies when no record type matches"), one for
   `Case.Support`, one for `Case.Billing`. Record-types gotcha #3 is the reason: a profile with
   no record-type assignments leaves its users unable to select any record type, and nothing
   alerts on it.
2. **Layout assignment and record-type visibility are deliberately not the same matrix.**
   Acme Billing is assigned the Support layout for `Case.Support` but `<visible>false</visible>`
   on it — matching `Case_Billing`'s permission set and plan assumption A1 while Q13 stays
   deferred. If Q13 later says Billing should see Support cases, flipping `visible` is the only
   edit needed; the layout assignment is already correct. The mirror applies to the two Support
   profiles and `Case.Billing`.
3. **Exactly one `<default>true</default>` record type per profile** — Tier 1 and Tier 2 default
   to `Case.Support`, Billing to `Case.Billing`. The skill states the constraint directly:
   "Exactly one `recordTypeVisibilities` entry per profile per object may carry
   `<default>true</default>`."
4. **`<default>true</default>` on `applicationVisibilities` for `standard__Service`.** Only one
   app per profile may be default; this is the whole reason Q7's residue list names the default
   app. The permission set grants app *visibility*; only the profile marks the landing app.
5. **No `<fullName>` element.** Source format carries the name in the file stem, which is how
   M1-S02's layouts and M2-S02's permission sets are written, and how both cited skills' Profile
   examples are written. Where a stem and a `<fullName>` do both appear in this build they are
   equal — the rule mock deploy M1 F-11 established. The stems here contain spaces because the
   Profile *fullName* contains spaces; that is the same rule, not an exception to it.
6. **Profile members are bare in `package.xml`** (`Acme Support Tier 1`, not
   `Case.Acme Support Tier 1`). `Profile` is not an object-scoped type. The object-qualified
   form belongs to `RecordType` and `CustomField` members, which this manifest does not carry.
7. **No `loginHours`, no `loginIpRanges`, no `tabVisibilities`, no `objectPermissions`, no
   `fieldPermissions`, no `userPermissions`.** Q7's answer names three things and only three:
   layout assignments, default app, default record type. Login-window and IP restrictions are
   profile-only residue the skill documents, but no clarification asks for them, and writing a
   login window nobody requested would lock 18 users out on the first out-of-hours page.
   `check_access_model.py` confirms the split held: 0 findings over the three files.
8. **No `viewAllRecords`, `modifyAllRecords`, `ViewAllData` or `ModifyAllData` anywhere.**
   There are no `objectPermissions` or `userPermissions` blocks at all, so there is nothing to
   grant them on. Record access to a Case stays with the Private OWD (M1-S01) and the M2-S05
   sharing rule.

## Elements this step could NOT ground

Recorded rather than invented, per `standards/build-orchestration.md` § 8.

- **`personAccountDefault` is omitted.** Both cited skills document the element, but the
  record-types skill's own Questions-to-Ask row — "Are Person Accounts enabled on this org?" —
  is unanswered by any clarification in `plan.json`, and that skill calls Person Account record
  types "a separate model". The element is documented as inert when Person Accounts is off, so
  omitting it is the reading that asserts least. **UNGROUNDED:** if Person Accounts turns out to
  be enabled, these three files need review, not just this element.
- **Element ordering inside the `Profile` root is alphabetical, and that choice is not sourced
  from either skill.** The two cited examples disagree: the record-types example is alphabetical
  (`custom`, `layoutAssignments`, `recordTypeVisibilities`), the permission-sets-vs-profiles
  example is not (`custom`, `description`, `userLicense`, `applicationVisibilities`,
  `recordTypeVisibilities`, `layoutAssignments`). Alphabetical was chosen because it is the shape
  a Metadata API retrieve returns. **UNGROUNDED:** neither skill states whether the Profile
  deploy enforces element sequence, and no mock deploy in this build has exercised a Profile.
  If the M2 mock deploy rejects one of these files on ordering, this is the line to read first.
- **Whether a `layoutAssignments` entry is accepted for a record type the same profile marks
  `<visible>false</visible>`.** Decision 2 depends on it. Neither cited skill addresses the
  pairing, and the guide text quoted in the skills covers only the inactive-record-type case
  (gotcha #8), which is different — both record types here are active. **UNGROUNDED, and the
  highest-value thing for the M2 mock deploy to settle.** If the deploy rejects it, the remedy
  is to drop the non-persona record type's `layoutAssignments` block from that profile and
  accept the fall-through assignment instead.
- **Q11's answer is arguably moot at API 62.0, and the grounded behaviour is better than the
  answer.** Q11 says "clone Standard User into custom profiles before any deploy is attempted."
  But `permission-sets-vs-profiles/references/gotchas.md` ("Profile Deployment Overlays; It Does
  Not Replace") states that deploying a profile that does not exist in the target org without
  specifying permissions produces a profile inheriting the standard **Minimum Access -
  Salesforce** profile at API 60.0 and later — Standard User only at 59.0 and earlier. This
  manifest is 62.0. So these three files, deployed into an org that does not already have them,
  create profiles seeded from Minimum Access, which is the intended end state for a
  permission-set-led model and is *cleaner* than the Standard User clone Q11 asked for (that
  skill's "Cloned Profiles Are Not Clean Slates" gotcha is the reason). `<custom>true</custom>`
  is written either way, which is what Q11 actually turns on. **Flag for the M2 gate:** if the
  org already carries profiles by these names, the deploy overlays them instead, and whatever
  those profiles grant today survives silently — a deploy is not a strip.

## Validate-only command for a human to run

Never run by an agent in this loop. Copy the artefacts into a DX source tree first — the paths
below are relative to that tree, not to the build directory.

```bash
sf project deploy start \
    --manifest manifest/package.xml \
    --dry-run \
    --target-org <your-sandbox-alias>
```

Then verify the matrix the Metadata API cannot show you, per the record-types skill:
Setup → Object Manager → Case → Page Layouts → **Page Layout Assignment**. That grid is the
profile × record type × layout matrix these three files encode; a blank cell means the profile
fell through to the assignment with no `recordType`.

```sql
-- Which profile defaults to which record type, after the deploy
SELECT Id, Name, DeveloperName, SobjectType, IsActive FROM RecordType WHERE SobjectType = 'Case'
```

## Rebuild #2 — descriptions

**F-15 evidence (mock deploy #1, `reports/MOCK-DEPLOY-M2.md`).** All three
`Profile` files were rejected by the org with `Description: data value too
large … (max length=255)`. `check_access_model.py --manifest-dir
artefacts/M2-S03` had exited 0 on the prior run — the checker at that time
carried no description-length rule, so a correctly-split profile still failed
at the org because nothing in the build layer enforced the Metadata API's
255-character `Profile.description` / `PermissionSet.description` ceiling
(*Metadata API Developer Guide*, `api_meta` L97678 / L94788, both stating
"Limit: 255 characters"). This is closed today at the skill:
`skills/admin/permission-sets-vs-profiles` v1.2.0 adds the ceiling to
`references/metadata-examples.md` § "Description length" and the checker gains
`PSVP-DESC-01` (ERROR, ≥255 chars) and `PSVP-DESC-02` (WARN, ≥200 chars, kept
as headroom below the hard limit).

**Reproduced before editing.** Running the now-fixed checker against the
rebuild #2 originals (the exact three files mock deploy #1 rejected)
reproduces the org's rejection as a build-time ERROR instead of a deploy-time
one:

```json
{
  "score": 55,
  "findings": [
    {"severity": "ERROR", "location": ".../Acme Billing.profile-meta.xml",
     "message": "PSVP-DESC-01 Profile description is 407 characters, over the 255-character limit; move rationale to deploy-order.md or the configuration workbook."},
    {"severity": "ERROR", "location": ".../Acme Support Tier 1.profile-meta.xml",
     "message": "PSVP-DESC-01 Profile description is 280 characters, over the 255-character limit; move rationale to deploy-order.md or the configuration workbook."},
    {"severity": "ERROR", "location": ".../Acme Support Tier 2.profile-meta.xml",
     "message": "PSVP-DESC-01 Profile description is 279 characters, over the 255-character limit; move rationale to deploy-order.md or the configuration workbook."}
  ],
  "summary": "Scanned 3 access-model metadata file(s); 3 finding(s) detected."
}
```

exit code 1.

**The fix.** Only the `<description>` element of each of the three profiles
was rewritten, to ≤200 characters (headroom under the DESC-02 warning, not
just under the DESC-01 error). Every other element in all three files is
byte-identical before and after — verified by SHA-256 of the whole file before
and after the edit, and by a line diff showing the `<description>` line as the
only change:

| File | SHA-256 before | SHA-256 after | Old len | New len |
|---|---|---|---|---|
| `Acme Support Tier 1.profile-meta.xml` | `b6253d609dd5572c442ab12d5050562757057854b02cacdf3728656935f4eca5` | `52bfdc3a2327efed2dd910e44d7573c8840cd17e9310df5ea200f06358712255` | 280 | 152 |
| `Acme Support Tier 2.profile-meta.xml` | `bb834a1e5dbf598bf3dbbddf80ba18d6f7a7234c7c3b0cc026262b354fc2c29e` | `b941eedef44c47dfbcbdd262b3f5697e71aaf1563e4b048c65ae2aaf8e1923fe` | 279 | 152 |
| `Acme Billing.profile-meta.xml` | `6889ae2463b1aca832362771e7655f8a2bfb7cf3515b248d5f7ffafd80ae0f1d` | `2d62df1f26f30ebd54553e06e3657e7a4eae634d5a84b29eaa5a837e116830c6` | 407 | 147 |

New description text, one line a Setup user can scan, per the skill's "Where
rationale goes instead" rule:

- **Acme Support Tier 1:** "Base profile: Tier 1 support. Holds only default
  app, default record type and layout assignments. All object/field/tab
  access comes from PSG_Tier1_Prod." (152 chars)
- **Acme Support Tier 2:** "Base profile: Tier 2 support. Holds only default
  app, default record type and layout assignments. All object/field/tab
  access comes from PSG_Tier2_Prod." (152 chars)
- **Acme Billing:** "Base profile: Billing. Holds only default app, default
  record type and layout assignments. All object/field/tab access comes from
  PSG_Billing_Prod." (147 chars)

**Where the removed rationale now lives** — the exact prose each old
description carried, preserved here rather than discarded:

- **Acme Support Tier 1 (12 users).** "Carries only the residue a profile
  alone can hold: the default app, the default record type and the page
  layout assignments. Every object, field and tab grant lives in the M2-S02
  permission sets behind PSG_Tier1_Prod (Q7, Q11)." — the user count and the
  Q7/Q11 citation are covered above under "Order inside this step" and
  Decisions 1–8; PSG_Tier1_Prod is named in the new short description itself.
- **Acme Support Tier 2 (4 users).** Same rationale, `PSG_Tier2_Prod`, same
  coverage above.
- **Acme Billing (2 users).** "Carries only the residue a profile alone can
  hold: the default app, the default record type and the page layout
  assignments. Every object, field and tab grant lives in the M2-S02
  permission sets behind PSG_Billing_Prod (Q7, Q11). The Support record type
  is assigned a layout but left not visible, matching Case_Billing and
  assumption A1 while Q13 stays deferred." — the Support-layout-but-not-visible
  point is Decision 2 above verbatim; the Q13/assumption-A1 deferral is also
  Decision 2. Nothing from this description was lost; it was already
  duplicated in Decisions 1–8 and is now stated once, here, instead of twice.

**Post-edit verification** (this rebuild, from the build directory):

- `python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir artefacts/M2-S03` → `{"score": 100, "findings": [], "summary": "Scanned 3 access-model metadata file(s); 0 finding(s) detected."}`, exit 0.
- `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts --strict` → `{"score": 100, "findings": [], "summary": "Scanned 15 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected."}`, exit 0.
- All four `*.xml` under `artefacts/M2-S03/` still parse with `ElementTree`.
- `python3 scripts/build_plan.py check-outputs plan.json M2-S03` → `{"ok": true, "missing": [], "empty": [], "malformed": []}`.

**Stale record above this step.** Per `standards/build-orchestration.md` § 4,
this rebuild drops the step back through `built` — the tester and doc-keeper
run again — and leaves the M2 milestone verdict stale until
`/verify-milestone` is re-run. The `step-tester` run recorded above
(`2026-09-12T00-59-34Z`) and the M1 milestone-level notes predate this fix and
should not be read as covering the description-length rule.
