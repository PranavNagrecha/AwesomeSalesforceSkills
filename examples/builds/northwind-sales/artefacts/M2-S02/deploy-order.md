# Deploy order — M2-S02

Build: `northwind-sales` · Milestone: M2 (access, validation and guidance) · Step type: `access` · API version 62.0 (defaulted — `plan.json` carries no `api_version`, so the `<version>` in this step's `package.xml` is the agent default that M1-S01, M1-S02 and M2-S01 also carry)

This note is written by `metadata-builder` and is text for a human. Nothing here is executed by this
agent or by any acceptance test. Nothing in this build deploys to an org.

Two components ship in this step:

| Component | Metadata type | File |
|---|---|---|
| `Enterprise_Sales_Record_Types` | `PermissionSet` | `permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml` |
| `Sales User` | `Profile` (overlay) | `profiles/Sales User.profile-meta.xml` |

---

## 0. The question this note has to answer first: does the permission set grant field access?

**No. `Enterprise_Sales_Record_Types` grants record-type visibility and nothing else** — two
`recordTypeVisibilities` entries, no `objectPermissions`, no `fieldPermissions`, no `tabSettings`,
no `userPermissions`, no `customPermissions`.

That is a decision, not an oversight, and here is what it rests on:

1. **The persona's access source is a permission set this build does not own.** Q19's answer names
   it: *"Reps and managers: the standard Sales User profile with a Sales Cloud permission set; the
   sales-ops admin: System Administrator."* The Sales Cloud permission set already carries the
   Opportunity CRUD and the standard-field FLS those 14 people work with today; it is not an
   artefact of this build and no step declares it. `Enterprise_Sales_Record_Types` is layered on
   top of it to add the two new record types, which is the one thing it is named for and the one
   thing the step's title states.
2. **The step's `inputs{}` name no field.** They name `permission_set`, `profile`, two
   `record_types` and two `layout_assignments`. Per `agents/metadata-builder/AGENT.md` Step 4 the
   planner's explicit binding wins over every other source, and it binds no field list.
3. **The shape the checker warns about is not present.** `PSVP-FLS-01` fires on *"a permission set
   that grants `allowCreate` or `allowEdit` on an object but carries zero `fieldPermissions` on any
   standard field of that object"* (`skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py`,
   check 7 — the live `case-onboarding` F-60 failure). This set grants no object permissions at
   all, so it is not a persona's access source and the rule has nothing to attach to. The checker
   agrees: the step-scope run exits 0 with `PSVP-FLS-01` silent.

### What that leaves open, and it is a real deploy-time gap

Field-level security for the two fields M1-S01 created — `Opportunity.Discount__c` and
`Opportunity.Approval_Status__c` — **is granted by no file in this build.** Three access files exist
across all sixteen steps (`M2-S01`'s `Sales_Ops_Validation_Bypass`, and this step's two), and none
of them carries a `fieldPermissions` block. `reports/MILESTONE-M1-REPORT.md` records the same fact
from the other side: *"Permission set grants (`fieldPermissions` / `objectPermissions`) | 0 | Not
present — access is M2-S01 / M2-S02."* M2-S01's own manual acceptance test then forbids field
permissions on its set, and this step's inputs bind none. So the chain ends here with nobody
holding it.

Why that matters on the day of the deploy, rather than as a tidiness point:

- **A new custom field deploys with FLS granted to nobody.** Both layouts built in M1-S02 place
  `Discount__c` and `Approval_Status__c`, but a layout placement is not an access grant. Reps open
  the Enterprise layout and the two fields are simply absent from it.
- **The deploying admin is not exempt.** The step gate's own note (approved 2026-09-19T14:22Z)
  states it: *"the deploying user has no FLS on fields shipped in the same package, so field grants
  ship with the set."* An admin who deploys and then eyeballs the record will not see the fields
  either, which is how this gap gets mistaken for a layout bug.
- **M2-S03's validation rule and M3-S02's approval process both write `Approval_Status__c`.**
  A field the persona cannot read is a field the persona cannot be shown an error about.

**Remedy, for a human — not actionable inside this step.** One of two, and it is the planner's call,
not this agent's:

- Add the two `fieldPermissions` blocks to the org's existing **Sales Cloud permission set** as a
  cutover runbook item in M4-S04 (the retrieve-then-amend shape M1-S01 and M1-S02 already use for
  `OpportunityStage` and the Opportunity Products related list). This is the option consistent with
  Q19 and with keeping one persona access source.
- Or `build_plan.py amend-step` this step to declare a field-grant output and rebuild it. That
  widens a human-gated step after its gate was signed, so the gate is rejected and re-signed first
  (`standards/build-orchestration.md` § 2, `amend-step`).

Doing it silently inside `Enterprise_Sales_Record_Types` is the option this agent declined: it would
put field grants in a set whose name, label and description all say "record types", and no answered
clarification asks for it.

---

## 1. Order inside this step

Both files may ship in one request. If they are split, the order is:

1. `PermissionSet` `Enterprise_Sales_Record_Types`
2. `Profile` `Sales User`

The permission set first is not arbitrary. A permission set can grant record-type *visibility* only;
the default record type and the page-layout assignment exist solely on `Profile`
(`skills/admin/record-types-and-page-layouts/references/metadata-examples.md`, "Making the record
type visible and assigning the page"). Shipping the visibility grant first means that if the profile
half fails, the two record types are selectable-but-unassigned rather than assigned-but-invisible.

## 2. Order against earlier steps — both are hard dependencies

| This step references | Built by | Rule |
|---|---|---|
| `Opportunity.Enterprise`, `Opportunity.Renewal` (in **both** files) | **M1-S01** | Deploy **after** M1-S01. `recordType` is object-qualified in both the `PermissionSet` and the `Profile` form. A record type absent from the org at deploy time is an `INVALID_CROSS_REFERENCE_KEY`, not a warning. |
| `Opportunity-Opportunity Enterprise Layout`, `Opportunity-Opportunity Renewal Layout` (in the **profile** only) | **M1-S02** | Deploy **after** M1-S02. `layoutAssignments/layout` names the layout in its **file-name form** — object, hyphen, layout name — and M1-S02's own deploy-order note records that a character-for-character mismatch is an `INVALID_CROSS_REFERENCE_KEY`. The two strings above were copied from the M1-S02 file names, not retyped. |

Both M1 record types carry `<active>true</active>`. That is a precondition, not a detail: neither
`Profile` nor `PermissionSet` retrieves or deploys record-type visibilities for an **inactive**
record type, so deactivating either one upstream makes both of this step's files silently lose half
their content on the next round trip (`check_record_type_layouts.py` check 1;
`skills/admin/record-types-and-page-layouts/references/gotchas.md` #8).

**Nothing later in the build depends on this step's files.** M2-S05's Paths, M3's automation and
M4's reports reference the record types themselves (M1-S01), not these grants.

## 3. The profile file is an overlay, and its emptiness is the design

`profiles/Sales User.profile-meta.xml` contains exactly four blocks: two `layoutAssignments` and two
`recordTypeVisibilities`. It carries no `objectPermissions`, no `fieldPermissions`, no
`userPermissions`, no `applicationVisibilities`, no `classAccesses`, no `tabVisibilities`, no
`description` and no `custom` flag.

That is safe **because profile deployment overlays rather than replaces**: the Metadata API guide,
quoted in `skills/admin/permission-sets-vs-profiles/references/metadata-examples.md`, states that
disabled permissions are not exported and that *"a deploy that is silent about a permission leaves
whatever the target org already had. Removing a permission through metadata requires writing it out
explicitly as `false`."* Everything the 14 Sales User holders have today survives this deploy
untouched, which is the specific mechanism behind Q4's *"The generic process stays untouched."*

Three consequences of that rule worth stating before someone "completes" the file:

- **`<default>false</default>` on both `recordTypeVisibilities` is load-bearing.** Exactly one entry
  per profile per object may be `true`. Both new entries are `false`, so the org's existing default
  Opportunity record type — the generic one the SMB team creates on — is left as it is. Setting
  either to `true` changes what every Sales User holder gets when they click New, including the SMB
  team, and that is a Q4 violation, not a preference.
- **There is deliberately no `layoutAssignments` entry without a `recordType`.** That form is the
  fallback assignment "that applies when no record type matches"
  (`record-types-and-page-layouts/references/metadata-examples.md`). Writing one here would overwrite
  the layout the Sales User profile already assigns to the generic record type, which is the layout
  the SMB team and their two list views and one pipeline report (Q9) use today.
- **There is no `personAccountDefault`.** Assumption **A6**: Person Accounts are not enabled, so the
  element is not needed. It is inert when the feature is off, but an overlay states only what it
  changes.

**Confirm the profile's exact name in the target org before deploying.** The member and the file
stem must both be the profile's `Name` including its space — `Sales User` — and the two must match
each other (`permission-sets-vs-profiles/references/metadata-examples.md` "Where the files live"
pairs member `Minimum_Access_Base` with `profiles/Minimum_Access_Base.profile-meta.xml`).
<!-- UNVERIFIED (2026-09-19): the documented example uses an underscored name; that a space-carrying
profile name is written with the space in both places follows from the stem-equals-member rule, and
no cited file shows a space-carrying profile member. --> Q19's answer calls it "the standard Sales
User profile"; if the org's profile is actually named something else, this is an
`INVALID_CROSS_REFERENCE_KEY` on the profile half, and the permission set half still deploys.

## 4. This `package.xml` is a deploy manifest, not a retrieve manifest

It names two members, one per type, and every member has a file behind it — which is what the step's
`manifest` acceptance test asserts. Do **not** reuse it to *retrieve* these two components. The
guide's rule, quoted in `permission-sets-vs-profiles/references/metadata-examples.md`: a retrieved
`.profile` includes security settings **only for the other metadata types named in the same retrieve
request**. A retrieve driven by this file returns a profile that looks empty, and committing that
result is how an org's real grants get deleted by the next deploy. A retrieve manifest for this
profile additionally names `RecordType` (`Opportunity.Enterprise`, `Opportunity.Renewal`) and
`Layout` (both layout names), and `RecordType` must be listed member by member because that type
does not accept `*`.

## 5. Checker findings carried into the M2 gate

Both are advisory, both exit 0, and neither is fixed by editing this step's files:

- **`PSVP-FLS-02` (WARN)**, on `profiles/Sales User.profile-meta.xml`: *"profile carries zero
  objectPermissions and zero fieldPermissions, and no PermissionSetGroup exists anywhere in the
  scanned tree."* Expected. The checker's own docstring calls this check "deliberately simplified" —
  it asserts only that *some* group exists to be the claimed access source, and this build designs
  no permission set group (the access source is the pre-existing Sales Cloud permission set, § 0).
  It is not a reason to add a group.
- **`RTL-MERGE-01` (REVIEW)**, on M1-S02's two layouts being identical after normalisation. A
  pre-existing M1 finding, already adjudicated at the M1 gate as open item **O-M1S02-03** ("identical
  layouts stay separate; the record types differ in process, the layouts will diverge in M3"). It is
  reported here only because this step's declared checker runs at build scope.

## 6. Repair after run 1

Mock deploy run 1 (`reports/MOCK-DEPLOY-M2.md`; org artefacts under
`reports/mock-deploy/2026-09-19T14-56-10Z/`) refused this step's `Profile Sales User` member with
`N3-F-05`: *"No default record type specified for recordTypeVisibility: Opportunity. To make the
'--master--' record type the default, set visible on all record types to false."* Two findings from
that one org message, both repaired here.

### 6.1 The profile's `recordTypeVisibilities` blocks are removed, not fixed in place

The overlay as it deployed stated two `recordTypeVisibilities` for Opportunity — `Enterprise` and
`Renewal` — both `visible=true`, `default=false`, and named no default. The platform's rule (stated
back at us verbatim in `N3-F-05`) is that a profile's record-type block for an object must either
name exactly one `default=true` entry or make every listed type invisible; a block that lists two
visible types and no default satisfies neither, so the org rejects the whole block rather than
guessing.

Neither of the platform's own two ways to satisfy that rule is available here without breaking Q4:

- **Naming a default among the two new types** would make `Enterprise` or `Renewal` the default
  record type for every one of the 14 Sales User holders, including the SMB team who create on the
  org's existing generic record type today. That is exactly the "generic process stays untouched"
  guarantee Q4 states, and § 3 above already named `<default>false</default>` as load-bearing for it.
- **Making every listed type invisible** would undo the one thing this step exists to do.

The repair is neither: **the profile overlay states no `recordTypeVisibilities` block at all** — both
entries are deleted, and `profiles/Sales User.profile-meta.xml` now carries only its two
`layoutAssignments` blocks, byte-identical to what run 1 deployed. This works because of the same
overlay mechanism § 3 already documents: a deploy that is silent about a permission leaves whatever
the org already has, and the org has never been asked to change anything about the profile's
record-type block. Visibility for `Opportunity.Enterprise` and `Opportunity.Renewal` is carried
entirely by `permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml`'s two
`recordTypeVisibilities` entries — a `PermissionSet` `recordTypeVisibilities` element has no `default`
field at all (`skills/admin/record-types-and-page-layouts/references/metadata-examples.md`; § 0
above), so a permission set literally cannot move anyone's default record type. A block this overlay
never states cannot move anyone's default record type either — the profile's silence is itself the
guarantee, not a gap in one.

**Production alternative, for the deployer, not this build.** If the org's admins want the `Sales
User` profile itself to carry Opportunity record-type visibility (rather than relying solely on the
permission set), the safe sequence is retrieve-then-merge, the same shape M1-S01 and M1-S02 already
use for `OpportunityStage` and the Opportunity Products related list: retrieve the org's current
`Sales User` `recordTypeVisibilities` for Opportunity, keep its existing `default=true` entry exactly
as retrieved, and append the two new entries at `default=false` before redeploying. Do **not**
construct that block from this build's files alone — this build has never seen the org's default
entry and has no way to state it correctly.

**Library gap, recorded and not fixed here.** No cited skill or checker holds the rule the org just
enforced: `skills/admin/permission-sets-vs-profiles/references/gotchas.md` documents that the default
record type is profile-bound, but nothing in that file or in
`skills/admin/record-types-and-page-layouts` states that a profile's *stated* `recordTypeVisibilities`
block must itself name a default or mark every entry invisible — the gap `check_permission_set_architecture.py`
and `check_record_type_layouts.py` both missed at build time, since neither ran against an org. Queued
as **PSVP-RT-DEFAULT-01** (Cursor task 18) for the library; this step does not attempt to write that
checker rule, per `agents/metadata-builder/AGENT.md`'s scope (this agent builds metadata, it does not
author checkers).

### 6.2 `Enterprise_Sales_Record_Types` now grants FLS on the two M1-S01 fields — closing O-M2S02-01

Separately from the org refusal, the requester decided at this repair pass to close **O-M2S02-01**
(`decisions.md` lines 677–699): the HIGH open item that no file in this build granted field-level
security on `Opportunity.Discount__c` or `Opportunity.Approval_Status__c`, even though both fields
ship in the same package (`M1-S01`) and both M1-S02 layouts place them.

`permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml` now carries two
`fieldPermissions` blocks, shaped on
`skills/admin/permission-set-architecture/references/metadata-examples.md` lines 36–50 (`editable`,
`field`, `readable`, in that order):

| Field | `readable` | `editable` | Why |
|---|---|---|---|
| `Opportunity.Discount__c` | `true` | `true` | The header field the 14 reps and managers work with directly (Q19's persona). |
| `Opportunity.Approval_Status__c` | `true` | `false` | Read-only to this persona: the M1-S02 layouts already place it read-only, and `M3-S02`'s approval process — not a person — is the writer. |

This is the persona's own build-owned home for the grant, not a workaround: the two fields are new in
this same build (`M1-S01`), so the deploying admin needs this grant to see them on first deploy just
as much as the 14 end users do — the scenario-1 org fact `deploy-order.md` § 0 already named ("a new
custom field deploys with FLS granted to nobody... the deploying admin is not exempt"). Closing the
gap in `Enterprise_Sales_Record_Types` rather than by amending the org's Sales Cloud set keeps the
grant inside this build's own artefacts, where `check_permission_set_architecture.py` and
`check_access_model.py` can see it.

**What this does not change: Q19's existing Sales Cloud permission set is untouched.** Object CRUD on
Opportunity — `create`, `edit`, `view` — still comes from the `Sales User` profile plus the org's
pre-existing Sales Cloud permission set, exactly as Q19 states and exactly as § 0 above still holds
for object permissions: `Enterprise_Sales_Record_Types` declares no `objectPermissions` element before
or after this repair. `check_access_model.py`'s `PSVP-FLS-01` rule — a permission set granting object
CRUD with zero field permissions — has nothing to attach to for the same reason § 0 gives: this set
still grants no object permissions at all, so adding these two `fieldPermissions` blocks does not
create the shape that rule fires on. **`PSVP-FLS-01` must stay silent** on the step-scope re-run below;
a fired `PSVP-FLS-01` here would mean an object-permissions element was accidentally introduced, not
that the field grant itself is wrong.

The set's `description` element was updated in the same edit to state its widened scope (was:
"Record-type visibility only... No object, field, tab or system permissions"; is: "Record-type
visibility... plus FLS on Discount__c and Approval_Status__c. No object, tab or system permissions"),
195 characters, under the 200-character ceiling `agents/metadata-builder/AGENT.md`'s invoking
instructions set for this repair. **§ 0 above is superseded on this one point** — it was written
against the pre-repair file and its "grants record-type visibility and nothing else" / "no
`fieldPermissions`" characterization is now accurate only for object and tab/system permissions, not
for fields; § 0's `PSVP-FLS-01` reasoning still holds, per the paragraph above, because the object-CRUD
condition that rule tests for is unchanged.

This closes `decisions.md` **O-M2S02-01**. `traceability.md` REQ-013 and REQ-014 remain
`build-doc-keeper`'s to re-mark once this step is re-tested and re-documented — this repair pass does
not touch `traceability.md`.

## 7. Validate-only command — text for a human, never run by this agent

Against a sandbox, from a source-format project that contains all four steps' artefacts:

```bash
sf project deploy start --manifest manifest/package.xml --target-org <alias> --dry-run
```

`--dry-run` is *"Validate deploy and run Apex tests but don't save to the org"*
(`agents/_shared/AGENT_CONTRACT.md`, Gate C). Against **production** the validate-only form is
`sf project deploy validate`, which requires Apex tests and returns a job id for a later
`sf project deploy quick`; Salesforce documents it as not for sandboxes.

Inside this repo the equivalent is:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json --org-alias <alias> --step M2-S02
```

That script assembles the step's artefacts and runs the `sf` validation itself. Its own help text is
explicit that it is *"Validation only … There is no flag to disable `--dry-run` and no `--deploy`
option; that is by design"* — so a human passes no such flag to it, and there is none to pass. It
needs an org alias; this build is `design-only` and has none on file.

Run either one **only** with M1-S01, M1-S02 and this step's artefacts together. Validating this step
alone reports the record types and both layouts as missing, which is the dependency in § 2 being
correctly detected, not a defect in these two files.

## 8. Who verifies afterwards, and against what

Both cited access skills ask this before any XML is written, and "it deployed" is not the answer.
After the deploy, against **one real rep and one real manager**:

- **Setup → Users → the user → View Summary.** This shows effective access as the union of the
  profile and every assigned permission set, which is the only place the layered design in § 0 is
  visible as one picture (`skills/admin/permission-sets-vs-profiles/references/metadata-examples.md`,
  "Setup check").
- **Click New on Opportunity.** Both `Enterprise` and `Renewal` must appear as choices, and the
  pre-existing generic record type must still be the preselected default (§ 3).
- **Open one Enterprise opportunity.** If `Discount__c` and `Approval_Status__c` are missing from a
  layout that places them, that is the FLS gap in § 0, not a layout defect.
- **Assignment count**, to confirm the population actually landed:

```soql
SELECT PermissionSet.Name, PermissionSet.Label, COUNT(Id) Assignments
FROM PermissionSetAssignment
WHERE PermissionSet.IsOwnedByProfile = false
  AND Assignee.IsActive = true
GROUP BY PermissionSet.Name, PermissionSet.Label
ORDER BY COUNT(Id) DESC
```

`Enterprise_Sales_Record_Types` should show **14** assignments — 12 reps plus 2 managers (Q19). The
sales-ops admin is a System Administrator and needs no row in either of this step's files (A39).
Assigning the set is a human action outside this build; nothing here assigns it.
