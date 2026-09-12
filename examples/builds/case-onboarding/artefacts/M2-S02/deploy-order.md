# Deploy order — M2-S02 (permission sets and permission set groups)

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was deployed.

## Order inside this step

| # | Component | Type | Why it must come at this point |
|---|---|---|---|
| 1 | `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2`, `Case_Billing` | `PermissionSet` | A group's `<permissionSets>` entries reference member sets by API name, and `skills/admin/permission-set-architecture/references/metadata-examples.md` § 3 states every member "must exist in the org or in the same deploy". |
| 2 | `PSG_Tier1_Prod`, `PSG_Tier2_Prod`, `PSG_Billing_Prod` | `PermissionSetGroup` | Composition only. The group file is "a membership list plus a label" (same reference), so it is deployable the moment its members are. |

`templates/admin/permission-set-patterns.md` states the same sequence as house style:
object-access PS → feature PS → PSG → muting PS → assignment. There is no muting
permission set in this step (see below), so step 3 of that sequence is the last one here.

A single `sf project deploy start --manifest artefacts/M2-S02/package.xml` satisfies both
rows in one request — the ordering matters only if the two types are split across requests.

## Dependencies on components OUTSIDE this step

Every one of these is deployed by an earlier step and must be present in the target org
before this manifest is validated, or the deploy fails on a dangling reference:

| Needed | Built by | Referenced from |
|---|---|---|
| `CustomObject` Case (Private OWD) | M1-S01 `objects/Case/Case.object-meta.xml` | `objectPermissions.object` = `Case` |
| `CustomField` `Case.Severity__c` | M1-S01 | `fieldPermissions` in `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2` |
| `CustomField` `Account.Region__c`, `Account.Support_Tier__c` | M1-S01 | `fieldPermissions` in `Case_Agent_Core` |
| `RecordType` `Case.Support` | M1-S01 `objects/Case/recordTypes/Support.recordType-meta.xml` | `recordTypeVisibilities` in `Case_Tier1`, `Case_Tier2` |
| `RecordType` `Case.Billing` | M1-S01 `objects/Case/recordTypes/Billing.recordType-meta.xml` | `recordTypeVisibilities` in `Case_Billing` |

Standard objects (`Account`, `Contact`, `EmailMessage`, `Entitlement`), the standard tabs
`standard-Case` / `standard-Account` / `standard-Contact` and the standard app
`standard__Service` are platform-provided and are not deployed by this build. Entitlement
Management must be enabled in the org before `Entitlement` resolves as an object — that is a
M4 prerequisite, recorded here because it is an ordering fact for this manifest too.

**Not a member of this step's `package.xml`.** The Metadata API guide's rule that "when
retrieving object or field permissions, you must also retrieve the associated object" is a
*retrieve* rule. Adding `CustomObject`/`CustomField`/`RecordType` members here would declare
members with no backing file in `artefacts/M2-S02/`, which the always-on manifest acceptance
test fails in the other direction. The objects travel in M1-S01's manifest; a merged
milestone manifest that carries both is `build-doc-keeper`'s to compile.

## Downstream, not here

`PermissionSetAssignment` is data, not metadata: no user, group or role assignment is written
by this step. Q8 puts 18 users behind the three PSGs (12 / 4 / 2); assigning them is a
post-deploy action. Q96's gate applies before UAT — poll
`SELECT Id, DeveloperName, Status FROM PermissionSetGroup` and treat anything other than
`Updated` as not-yet-provisioned.

## Decisions worth reading before deploy

1. **`license` is absent from all four sets.** Q8 answered "leave LicenseId empty". The
   permission-set-architecture reference quotes the Object Reference: leave `LicenseId` empty
   where a set may be assigned across licences. Absence is the encoding of that answer.
2. **`viewAllFields` is not written on any `objectPermissions` block.** The cited reference
   dates it API 63.0+; this manifest is `62.0`, and the reference's own object-access example
   omits it. The six `PermissionSetObjectPermissions` fields the guide marks Required are all
   present explicitly on every block.
3. **`<fullName>` is written on the three PSG files and not on the four permission sets.**
   That is exactly the shape `permission-set-architecture/references/metadata-examples.md` § 3
   shows. Where `<fullName>` is present it equals the file stem — the rule mock deploy M1 F-11
   established when a `BusinessProcess` stem and `<fullName>` disagreed.
4. **No sharing bypass anywhere.** `viewAllRecords` and `modifyAllRecords` are `false` on
   every block. Record access to a Case is decided by the Private OWD (M1-S01) and the
   criteria-based sharing rule (M2-S05), never by these sets.
5. **No muting permission set.** Billing is granted less rather than muted down from more, so
   the subtract-only mute mechanic in `admin/permission-set-group-composition` is not needed;
   its `MutingPermissionSet` shape stays unused rather than used decoratively.
6. **`Case_Billing` does not grant the Support record type.** Q13 is DEFERRED; the plan's
   assumption A1 takes the conservative reading. If the answer turns out to be field-level
   masking rather than record-level separation, this file changes and so does M2-S05.

## Elements this step could NOT ground

Recorded rather than invented, per `standards/build-orchestration.md` § 8.

- **No `userPermissions` on any set.** The only Case-related system permission named in the
  cited skills is `TransferAnyCase`, and `permission-set-architecture/references/metadata-examples.md`
  marks it `UNVERIFIED (2026-09-04)` — the guide's worked example is `TransferAnyLead`. No
  clarification asks for a system permission either, so none is written. If Tier 2 turns out
  to need case transfer beyond ownership, that is a new grant to design, not a guess to make.
- **`Case_Tier1` and `Case_Tier2` carry identical grants.** The requirement separates the two
  teams by *routing* (Tier 1 is pushed work, Tier 2 pulls from a list) and by *escalation*
  (untouched for 8 business hours), both of which are Omni-Channel, queue and EscalationRules
  concerns in M2-S04 / M3 / M4. No answered clarification gives Tier 2 an access the Tier 1
  agents lack. Two sets are written because `outputs[]` declares two; a human who wants them
  consolidated should re-plan rather than have the builder collapse a declared output. The
  composition checker's near-clone heuristic needs 4+ shared sets to fire, so it stays silent
  on a pair this small — this note is the signal, not the checker.
- **No tab setting for Entitlement.** `standard-<Object>` is a documented form, but nothing in
  the requirement or the answers says agents reach Entitlements from a tab rather than from the
  Case related list, so no tab was granted for it. `standard-Case`, `standard-Account` and
  `standard-Contact` are written because Q9 puts those objects in scope for day-to-day work.
- **`Case.Severity__c` edit for Tier 1 and Tier 2, read-only for Billing** is a builder
  reading of the requirement ("Severity 1 outages are 24/7"), not an answered question.
  Confirm it at the M2 gate.

## Validate-only command for a human to run

Never run by an agent in this loop. Copy the artefacts into a DX source tree first — the
paths below are relative to that tree, not to the build directory.

```bash
sf project deploy start \
    --manifest manifest/package.xml \
    --dry-run \
    --target-org <your-sandbox-alias>
```

Then verify, per Q87 and Q96:

```sql
SELECT Id, DeveloperName, Status FROM PermissionSetGroup
WHERE DeveloperName IN ('PSG_Tier1_Prod','PSG_Tier2_Prod','PSG_Billing_Prod')
```

## Rebuild #2 — descriptions

Triggered by `reports/MOCK-DEPLOY-M2.md` run 1 (2026-09-11), finding **F-15 (HIGH, new)**:
the org rejected all four `PermissionSet` files in this step with
`Description: data value too large … (max length=255)`, and the three PSGs in this step
cascaded (`permission set names are invalid`) as a consequence of the four failed member
sets, not because any PSG description was itself too long. `PermissionSet.description` and
`Profile.description` are limited to 255 characters (api_meta L94788/L95328); the first pass
wrote 290–456-character rationales into the description element, following the cited skills'
own worked examples, which at the time carried long descriptions and no length rule.

The cited skills were fixed before this rebuild: `admin/permission-set-architecture` v1.2.0
adds PSA-DESC-01 (ERROR, `description` > 255 chars) and PSA-DESC-02 (WARN, > 200 chars);
`admin/permission-set-group-composition` v1.1.0 adds the matching PSGC-DESC-01 / PSGC-DESC-02;
`admin/permission-sets-vs-profiles` v1.2.0 carries the same PSVP-DESC-01 check. This rebuild
re-runs those three checkers, plus `check_access_model.py`, against the same four files.

**What changed.** Only the `<description>` element of the four permission sets. Every other
element — `label`, `hasActivationRequired`, `applicationVisibilities`, `objectPermissions`,
`fieldPermissions`, `tabSettings`, `recordTypeVisibilities` — is byte-identical to the first
pass; the three PSG files are untouched (none of their descriptions exceeds 200 characters:
`PSG_Billing_Prod` 187, `PSG_Tier1_Prod` 194, `PSG_Tier2_Prod` 132 — none crossed the WARN
line either, so no PSG edit was in scope).

| File | Description length before | Description length after |
|---|---|---|
| `permissionsets/Case_Agent_Core.permissionset-meta.xml` | 419 | 192 |
| `permissionsets/Case_Billing.permissionset-meta.xml` | 380 | 183 |
| `permissionsets/Case_Tier1.permissionset-meta.xml` | 290 | 193 |
| `permissionsets/Case_Tier2.permissionset-meta.xml` | 456 | 199 |

**Rationale moved here from the trimmed descriptions** (previously inline, now stated once,
per component, so nothing that made the first pass reviewable is lost):

- **`Case_Agent_Core`** — composed into `PSG_Tier1_Prod`, `PSG_Tier2_Prod` and
  `PSG_Billing_Prod` (see "Order inside this step" above). `licenseId` is deliberately unset:
  Q8 says all 18 users hold Salesforce licences today, and an empty `licenseId` keeps the set
  assignable if that ever stops being true. See "Decisions worth reading before deploy" item 1
  for the general rule this follows.
- **`Case_Billing`** — `Case.Severity__c` stays read-only for Billing because the requirement
  scopes severity to outages, which Finance does not triage. The Support record type is
  deliberately not granted: Q13 was deferred and the plan takes the conservative reading
  (assumption A1) — see "Decisions worth reading before deploy" item 6. `licenseId` unset per
  Q8, as above.
- **`Case_Tier1`** — record *access* to a Case (as opposed to the field- and record-type-level
  grants in this set) is decided by the Private OWD (M1-S01) and the M2-S05 criteria-based
  sharing rule, never by this permission set — see "Decisions worth reading before deploy"
  item 4. `licenseId` unset per Q8.
- **`Case_Tier2`** — Tier 2 works Support cases escalated to it after 8 business hours; that
  escalation is an `EscalationRules` and queue concern (M2-S04, M4), so the permission
  footprint is currently identical to `Case_Tier1` by design — see "Elements this step could
  NOT ground" below for why the two sets were not consolidated into one. `licenseId` unset per
  Q8.

**Verification (this rebuild, from the build directory via the `skills` symlink).**

Pre-edit, all three checkers reported the four DESC-01/PSVP-DESC-01 errors and (for the PSG
checker) the cascading `PSGC-DESC-01` errors on the same four files, all exit 1:

```text
$ python3 skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py --manifest-dir artefacts
ERROR: PSA-DESC-01 artefacts/M2-S02/permissionsets/Case_Agent_Core.permissionset-meta.xml: PermissionSet description is 419 characters, over the 255-character limit; move rationale to deploy-order.md or the configuration workbook.
ERROR: PSA-DESC-01 artefacts/M2-S02/permissionsets/Case_Billing.permissionset-meta.xml: PermissionSet description is 380 characters, over the 255-character limit; ...
ERROR: PSA-DESC-01 artefacts/M2-S02/permissionsets/Case_Tier1.permissionset-meta.xml: PermissionSet description is 290 characters, over the 255-character limit; ...
ERROR: PSA-DESC-01 artefacts/M2-S02/permissionsets/Case_Tier2.permissionset-meta.xml: PermissionSet description is 456 characters, over the 255-character limit; ...
(plus 3 ERROR PSA-DESC-01 on M2-S03 profiles, and 1 WARN PSA-DESC-02 on M2-S01 — both outside this step's scope)
EXIT=1

$ python3 skills/admin/permission-set-group-composition/scripts/check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02
ERROR ×4 PSGC-DESC-01 (same four files)
GOOD: reuse: permission set 'Case_Agent_Core' is referenced by 3 PSGs
Summary: 1 good, 4 error, 0 warn, 0 info, scanned 3 PSG file(s).
EXIT=1

$ python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir artefacts/M2-S02
ERROR ×4 PSVP-DESC-01 (same four files); score 40
EXIT=1
```

Post-edit, all three exit 0 with no DESC finding on any M2-S02 file:

```text
$ python3 skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py --manifest-dir artefacts
WARN: PSA-DESC-02 artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml: ... 244 characters ... (pre-existing, outside this step)
EXIT=0

$ python3 skills/admin/permission-set-group-composition/scripts/check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02
GOOD: reuse: permission set 'Case_Agent_Core' is referenced by 3 PSGs (PSG_Billing_Prod, PSG_Tier1_Prod, PSG_Tier2_Prod)
Summary: 1 good, 0 error, 0 warn, 0 info, scanned 3 PSG file(s).
EXIT=0

$ python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir artefacts/M2-S02
{"score": 100, "findings": [], "summary": "Scanned 7 access-model metadata file(s); 0 finding(s) detected."}
EXIT=0
```

`Case_Agent_Core`'s post-edit `label`, permission blocks and tab settings, and every element
of the other three sets besides `description`, are unchanged from the first pass — this is a
description-only rebuild, not a re-author.

**Stale records.** M2-S02's earlier `tested` and `documented` run records (step-tester
2026-09-12T00-14-33Z, build-doc-keeper 2026-09-12T00:30:00Z) and the M2 milestone verdict
built on them predate this rebuild and predate F-15. They reflected files that mock deploy
run 1 then rejected at the org boundary; the milestone verdict is stale until M2-S02 (this
step), M2-S03 (profiles, rebuilding concurrently in `artefacts/M2-S03/` under a different
runner) and a second mock-deploy run all reconfirm.
