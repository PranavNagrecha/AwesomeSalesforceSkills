# Gotchas: Permission Sets vs Profiles

---

## FLS Grants Are Additive — Permission Sets Can Give MORE Access Than the Profile

**What happens:** An admin sets a field to Read-Only on the user's profile, thinking that locks it down. The user has a Permission Set that grants Edit on the same field. The user gets Edit. The profile restriction is overridden.

**When it bites you:** Security audits. "We restricted that field on the profile" — yes, but the Permission Set won. You need to check the combined effective access, not just the profile.

**How to avoid it:**
- Use the "View Summary" / "Effective Access" check on a specific user to see their actual combined access
- When restricting access, remove the grant from ALL Permission Sets, not just the profile
- Don't rely on Profile FLS to cap access when Permission Sets are in play

**The rule:** Permission Sets only add. They cannot restrict below what the Profile grants. But a Profile can set Read, and a Perm Set can elevate to Edit. Read: if you need a hard ceiling on access, do not use a Profile to set it — use sharing rules and record visibility, not field-level security via profile alone.

---

## Login Hours and IP Restrictions Live on the Profile — Forever

**What happens:** An org moves users to a "Minimum Access" profile and Permission Set Groups. Six months later, the security team asks: "Why can users log in from any IP at any time? We had IP restrictions before." The IP restrictions were on the old profile. The new profile doesn't have them configured.

**When it bites you:** During profile migration. Old profiles often have login hour restrictions (e.g. "business hours only") and IP allowlists. These do not exist in Permission Sets — they cannot be migrated to PSGs.

**How to avoid it:**
- Before decommissioning a profile, explicitly check and document:
  - Login Hours: `Setup → Profiles → [Profile] → Login Hours`
  - Login IP Ranges: `Setup → Profiles → [Profile] → Login IP Ranges`
- Transfer these settings to the replacement base profile before migrating users

**The rest of the list.** Login hours and IP ranges are the two people remember. Salesforce Help 003834041 (6 Jun 2026) names six settings it says belong in the profile, and each survives a migration only if you carry it across deliberately:

1. Default assigned apps
2. Default record types and page layouts
3. Login hours
4. Login IP ranges
5. Password policies
6. Session settings

Items 1 and 2 are the quiet ones, and read them precisely: the word is **default**. App visibility and record type *access* are both grantable from a permission set — the same article lists "assigned apps" and "record types" under what permission sets should manage. Only the default landing app and the default record type are profile-bound. So a user migrated to a bare Minimum Access profile keeps their record access but lands on the wrong app and the wrong layout, which reads to them as "the migration broke my screen." Check them in the same pass as the security settings.

Treat this as Salesforce's list, not an exhaustive one — the profile also fixes the user's license, which constrains everything above.

---

## Cloned Profiles Are Not Clean Slates

**What happens:** An admin clones "Standard User" to create a profile for a new team. Three years later, someone finds the profile has 47 custom object permissions, FLS grants on 200+ fields, and access to a deprecated AppExchange package. None of it was intentional — it all came from the original clone.

**When it bites you:** Every time. Cloned profiles inherit everything, including explicit denies, package grants, and legacy settings. People assume clones start "clean" because they haven't added anything — they haven't added anything, but they inherited everything.

**How to avoid it:**
- Audit any profile before using it as a migration base: use the Profile Comparison tool in Setup
- Better: start from the Minimum Access platform profile, not a cloned Standard User
- Document what was intentionally granted vs inherited

---

## The "Minimum Access" Base Profile Pattern

**Why it exists:** All users need a profile. The profile handles system-level settings (login hours, password policy, session settings). The goal is to put nothing else in the profile — no object access, no field access. All of that goes in Permission Sets.

**The pattern:**
1. Create a profile cloned from "Minimum Access — Salesforce" (a standard platform profile with almost nothing granted)
2. Set login hours, password policy, and session settings appropriate for your user population
3. Grant zero object access, zero FLS, zero custom permissions
4. Assign this profile to all internal users
5. All actual access comes from Permission Set Groups

**Gotcha:** Users with the Minimum Access profile cannot log in if they have no Permission Sets. Assign the base PSG before switching profiles. Don't leave users stranded.

---

## Permission Set Group Propagation Delay

**What happens:** An admin adds a Permission Set to a PSG and immediately gets a Slack message: "I still can't see the field." The admin checks, the assignment looks correct. The user isn't lying — the propagation just hasn't completed.

**When it bites you:** Any time you make PSG changes and immediately ask the user to verify.

**How to avoid it:**
- Allow up to 10 minutes for PSG changes to propagate (UNVERIFIED 2026-09-04: figure not in the official PDFs; observed, not documented)
- If urgency requires faster access, assign the Permission Set directly to the user (not via PSG) as a temporary measure
- Add this to your change management runbook: "PSG changes take up to 10 minutes"

---

## Profile-Only Retrieve Strips Object CRUD and Field Permissions From Source

**What happens:** `sf project retrieve start --metadata Profile:Admin` (or a package.xml with only `Profile`) writes a `.profile-meta.xml` that is **missing** `objectPermissions` / `fieldPermissions` the org actually has. Diffs look like "Admin has no CRUD." Deploying that file can **clear** org CRUD/FLS. Permission Set retrieves are the honest source for object/field grants.

**When it occurs:** DX workspaces that retrieve Profiles to "see access"; CI that deploys slim profile XML.

**How to avoid:** Do not treat a Profile retrieve as the access inventory. Retrieve Permission Sets (and the profile only for login hours, IP, default record type, tab vis). Never deploy a retrieved Profile without confirming object/field blocks are present if you intended to preserve them.

**Precision on the deploy half.** The clearing risk above is real but indirect, and the mechanism matters. Profile metadata deployment *overlays*: a block that is simply absent from the file leaves the target org's value untouched. What clears a permission is an explicit `false` — which is exactly what a round-trip through a UI editor, a diffing tool, or a script that "normalises" a profile can insert on your behalf. So the danger is not the missing block; it is the block that came back rewritten. See "Profile Deployment Overlays; It Does Not Replace" below, and "A Profile Retrieve Returns Only What the Rest of the Manifest Asked For" for the guide's exact wording on which elements always come back.

---

## A Profile's Permissions Physically Live in a Hidden Permission Set

**What happens:** You go looking for a profile's object permissions on the `Profile` object and find nothing but `Name`, `Description`, `UserLicenseId`, `UserType` and the `PermissionsXxx` booleans. The CRUD and FLS are not there. Since API version 25.0 every profile is associated with a `PermissionSet` row that stores the profile's user, object and field permissions plus setup entity access — flagged `IsOwnedByProfile = true`, with `ProfileId` pointing back at the profile.

**When it occurs:** Any time you audit access through SOQL rather than Setup. `ObjectPermissions` and `FieldPermissions` are children of `PermissionSet`, never of `Profile`, so a query filtered on the profile returns zero rows and reads as "this profile grants nothing".

**How to avoid:** Query through the profile-owned permission set — `WHERE Parent.IsOwnedByProfile = TRUE` on `ObjectPermissions` — and join back with `Parent.ProfileId`. Two constraints come with it. The Object Reference states you can query permission sets owned by profiles **but not modify them**, so this is a read path only; edits go through the `Profile` metadata type. And it warns not to depend on the `Name` or `Label` returned for those rows, because those values can change. Key on `ProfileId`.

UNVERIFIED (2026-09-04): the related claim that a `PermissionSetAssignment` cannot be created against a profile-owned permission set is not stated in the Object Reference's `PermissionSet` or `PermissionSetAssignment` sections, which say only that these rows cannot be modified. Do not assert the assignment restriction as documented behaviour.

---

## A Profile Retrieve Returns Only What the Rest of the Manifest Asked For

**What happens:** The retrieved `.profile-meta.xml` is short. It has `loginHours`, `loginIpRanges` and `userPermissions`, and almost nothing else — no object CRUD, no field permissions, no tab settings. Nothing is broken; the file is complete for the request that was made. The Metadata API Developer Guide states the rule twice: the content of a profile returned by Metadata API depends on the content requested in the `RetrieveRequest`, and the returned `.profile` files include security settings only for the *other* metadata types referenced in the same retrieve. User permissions, IP address ranges and login hours are the named exceptions that are always retrieved.

**When it occurs:** `sf project retrieve start --metadata Profile:Sales_User`, or any manifest whose `Profile` entry is not accompanied by the objects, fields, tabs, apps, record types, layouts and classes whose permissions you expected. It also occurs in reverse: the guide notes for `CustomObject`, `CustomField`, `CustomTab`, `CustomApplication`, `RecordType`, `Layout` and `NamedFilter` that *retrieving a component of that type makes the component appear in any Profile and PermissionSet components retrieved in the same package* — so adding one object to a manifest silently grows every profile file in the same retrieve.

**How to avoid:** Never read a profile retrieve as an access inventory, and never diff two profile files retrieved under different manifests. Build one manifest that names every component whose permissions are in scope, and reuse it for both the retrieve and the deploy. Permission sets do not share the problem: from API 40.0 onward a permission set retrieve includes all content exposed in Metadata API for that permission set — which is also why the guide warns that a permission set **deploy** must include all of its metadata or you overwrite what you omitted.

---

## Profile Deployment Overlays; It Does Not Replace

**What happens:** You remove `<objectPermissions>` for an object from a profile file, deploy, and the permission is still there in the target org. Nothing failed. The guide is direct about the design: Profile metadata deployment is built to *overlay* the existing profile settings in a target org, and disabled permission information isn't exported. Silence in the file means "leave whatever is there", not "revoke".

**When it occurs:** Every attempt to strip a profile by deleting XML blocks — which is exactly the last phase of a profile-to-permission-set migration. It is also why sandbox-to-production profile diffs drift one direction only: grants accumulate, revocations never travel.

**How to avoid:** To revoke through metadata, write the permission out explicitly as `false` rather than deleting the block — the guide's own instruction is to add code that explicitly indicates disabled permissions. And note the separate trap on the create path: deploy a profile that does not exist in the target org without specifying any permissions and the resulting profile inherits everything in the standard **Minimum Access - Salesforce** profile at API 60.0 and later, or the standard **Standard User** profile at 59.0 and earlier. A "blank" profile file is not a blank profile.

---

## Standard Profiles Are Editable Only in Part

**What happens:** A deploy that changes object permissions on a standard profile — `<custom>false</custom>` — either fails or silently keeps the org's values. In API version 50.0 and later, editing standard objects on standard profiles is disabled, and the same restriction is repeated in the `ProfileObjectPermissions` notes.

**When it occurs:** Teams that keep `Standard User` or `System Administrator` in version control and deploy the whole `profiles/` folder between environments. The custom profiles apply; the standard ones partially don't, and CI reports success either way.

**How to avoid:** Treat `<custom>false</custom>` as a read-only marker in source control. Clone to a custom profile before making any object-permission change you intend to deploy. Two related behaviours are worth knowing at the same time: since API 18.0 object permissions are disabled in new custom objects for any profile where View All Data or Modify All Data is off, and a profile that already has Modify All Data or View All Data ignores `modifyAllRecords` / `viewAllRecords` entries in Metadata API entirely without returning an error.

UNVERIFIED (2026-09-04): whether a standard profile can be deleted at all is not addressed in the Metadata API Developer Guide `Profile` section or the Object Reference `Profile` section. Do not claim "standard profiles cannot be deleted" as documented; verify in the target org.

---

## The License on a Permission Set Must Match the License on the Profile

**What happens:** The permission set is correct, the user is correct, and the assignment is rejected. The Object Reference states the rule for `PermissionSetAssignment`: if the `PermissionSet` has a `UserLicenseId`, that `UserLicenseId` and the `Profile`'s `UserLicenseId` must match for the assignment to succeed.

**When it occurs:** Mid-migration, when the base profile changes and the permission sets do not. It also occurs on any persona whose population spans licences — a permission set built while everyone held a Salesforce licence cannot then be assigned to Platform-licensed users on a Platform base profile.

**How to avoid:** If a permission set will be assigned across mixed licences, leave `LicenseId` empty — the Object Reference names this as the supported pattern. Scope `LicenseId` only when the permission set genuinely belongs to a single user licence or permission set licence. Before a migration, check the pairing: `SELECT Id, Profile.UserLicenseId FROM User` against `SELECT Id, LicenseId FROM PermissionSet`. And note the ceiling this implies — the user licence on the profile bounds what any permission set can grant, so a licence change is a bigger event than a permission change.

---

## Tab and App Elements Do Not Survive a Copy-Paste Between the Two Types

**What happens:** A block lifted from a profile into a permission set fails to deploy, or deploys with the wrong meaning. The element names and the enums differ: `Profile` uses `tabVisibilities` with `DefaultOff` / `DefaultOn` / `Hidden`; `PermissionSet` uses `tabSettings` with `Available` / `None` / `Visible`. Neither the tag nor a single enum value is shared.

**When it occurs:** Hand-migration, and any script that treats the two metadata types as the same schema. The same trap sits inside `applicationVisibilities` and `recordTypeVisibilities`: both types have those elements, but only the `Profile` variants carry `<default>` (and `<personAccountDefault>` for record types). Copying the profile's block into a permission set drops the `default` child, so the user keeps access and loses the preselection — the migration "worked" and the user lands on the wrong app with the wrong record type preselected.

**How to avoid:** Map the elements deliberately rather than copying blocks. `tabVisibilities`→`tabSettings` with `DefaultOn`→`Visible`, `DefaultOff`→`Available`, `Hidden`→`None`. Leave every `<default>` on the profile — it is residue by definition. `references/metadata-examples.md` carries the full profile-only / permission-set-only element table.

---

## `viewAllFields` Makes the Field List Disappear From the Retrieve

**What happens:** A permission set that clearly grants field access retrieves with no `fieldPermissions` blocks at all. The guide explains it: if the View All Fields object permission is enabled for an object in the permission set, the individual fields aren't returned under `fieldPermissions`. Disable it and the fields reappear, at which point access can be removed field by field.

**When it occurs:** Field-level audits, and any diff that counts `fieldPermissions` entries to measure how permissive a permission set is. An object with `viewAllFields` scores as the most restrictive one in the file while granting read on every field it has.

**How to avoid:** Read `<viewAllFields>` before reading the field list, and treat `viewAllFields=true` as a full-object read grant regardless of what `fieldPermissions` shows. Two adjacent retrieval limits belong in the same check: from API 30.0 onward permissions for **required** fields can be neither retrieved nor deployed, and from API 54.0 onward only field permissions that are *enabled* in the permission set are returned in queries — so absence of a field never means "explicitly denied", only "no record exists".

---

## `description` Over 255 Characters Fails The Deploy; PSGs Fail As A Cascade

**What happens:** The base profile or the receiving permission set carries a long rationale-style `description` — why the residue split was made, which persona this is for, what was deferred — and the deploy is rejected with `Description: data value too large … (max length=255)`. Any `PermissionSetGroup` that composes the failed permission set then fails too, with `permission set names are invalid`, which reads as an unrelated error.

**When it occurs:** Any deploy where `description` is used as a design note. The Metadata API guide states it directly for both types: "The profile description. Limit: 255 characters" and "The permission set description. Limit: 255 characters." Verified by `sf project deploy start --dry-run` against a Summer '26 developer org on 2026-09-11: four permission sets and three profiles were rejected on this exact error, and the permission set groups that referenced the rejected sets failed as a cascade (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md`, once exported).

**How to avoid:** Keep `description` to a one-line label and put the residue rationale in `templates/permission-set-design-template.md` or the build's `deploy-order.md`. `scripts/check_access_model.py` flags this before deploy: `PSVP-DESC-01` (ERROR) at 255+ characters, `PSVP-DESC-02` (INFO, headroom only — printed and counted, never fails the run even under `--strict`) at 200+.

---

## An Object Grant Without Field Grants Is A Persona That Cannot Fill In A Form

**What happens:** A permission-set-led decomposition ships a Tier 1 support persona as a metadata profile with zero object and field permissions — by design, "all access comes from the permission set group" — plus a core permission set granting Create and Edit on Case, with field permissions on exactly one custom field (`Severity__c`). Every checker passes. Five milestone verifications pass. Two org dry runs pass, because a validate-only deploy with no test execution never actually writes a record as that persona. Then an Apex test finally runs `System.runAs` a `TestUserFactory` user holding the shipped permission sets and inserts a fixture Case, and the deploy fails:

```
System.DmlException: Operation failed due to fields being inaccessible on Sobject Case,
check errors on Exception or Result! fieldNames: Subject,Origin,AccountId,Priority,EntitlementId
```

Five fields. Every one of them a **standard** Case field.

**When it occurs:** Standard fields carry field-level security exactly as custom fields do — the Metadata API Developer Guide's `fieldPermissions` entry on `PermissionSet` makes no standard/custom distinction (api_meta L94802-L94805: "Indicates which fields are accessible to a user assigned to this permission set"). Nothing in that sentence excludes `Case.Subject` or `Case.AccountId`. An LLM (and most humans) reach for field permissions only when a *custom* field is in scope — the field the requirement actually named — and assume standard fields "just work" because the object grant covers them. It does not. `allowCreate` on the object lets the persona create a `Case` row; it says nothing about which fields on that row the persona may populate. Each field needs its own `fieldPermissions` entry, standard or custom, or the field is not writable by that persona regardless of the object-level grant.

The profile side compounds it rather than rescuing it: a profile deployed from metadata grants nothing it does not explicitly list. "We designed Profile metadata deployment to overlay the existing Profile settings in a target org" (api_meta L97622-L97631) describes what happens to permissions already in the org — it is not a source of new grants. A profile with 32 lines of `layoutAssignments`, `recordTypeVisibilities` and `applicationVisibilities` and not one `objectPermissions` or `fieldPermissions` block grants exactly that: nothing. There is no implicit fallback where the profile "covers" what the permission set missed.

Root cause, concretely, from the `case-onboarding` build (F-60, M5 run 5 mock-deploy probe): `Case_Agent_Core` grants Create+Edit on Case with a single custom-field grant; `Case_Tier1` (the persona delta) adds record-type visibility and edit on `Severity__c`, nothing else; the shipped `Acme Support Tier 1` profile is 32 lines with zero object or field permissions. The Tier 1 persona can create a Case object and cannot write `Subject`, `Origin`, `Priority`, the `Account` lookup, or the `Entitlement` lookup — it cannot work a case. `getDmlFieldNames` on the caught `DmlException` turned the generic message into the five-field list above; every checker in the library and five milestone verifications had already passed the same shipped metadata, because nothing asserted that an object Create/Edit grant is accompanied by field grants for the fields the persona's own layouts and processes use, and no Apex test had run as the persona until that point.

**How to avoid:**
- Enumerate the standard fields a persona actually writes from the artifacts that already say so — the record's edit-mode **page layout**, its **compact layout**, and any **intake process** (trigger, Flow, integration) that populates fields on behalf of that persona — before writing the permission set. In `case-onboarding`, the Tier 1 Support page layout's `Edit`-behavior fields are `SuppliedEmail`, `Description`, `ContactId`, `Subject`, `Priority`, `Origin`, `Severity__c` (custom), plus `OwnerId`; the case-intake process additionally sets `AccountId` when it matches the sender to an Account. Grant `fieldPermissions` for all of those in the persona's core permission set.
- Do **not** grant `EntitlementId` to the persona on this evidence alone — it is populated by an admin-configured entitlement process, not by the agent, so a test fixture that needs it should seed it in system mode rather than justify handing the persona a field it does not use (`skills/apex/test-class-standards/references/gotchas.md` Gotcha 15 covers the test-side half of this fix).
- Treat "the profile carries the residue, the group carries the access" as a design that still needs the access half checked field by field — it is not self-verifying just because it deploys clean. A profile deploying with 0 errors and 0 object/field permissions is not evidence the persona has access; it is evidence the manifest didn't ask the org to check.
- Run `python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir <dir>` before considering an access-model step done. It now flags `PSVP-FLS-01` (WARN) on exactly this shape: a permission set granting `allowCreate`/`allowEdit` on an object with no standard-field `fieldPermissions` for that object.
- The gap survives object-CRUD review, PSG composition review, and a compile-only or metadata-only deploy validation. It only surfaces when something inserts a record **as the persona** — which is precisely why Apex tests must run inside `System.runAs` of a user holding the shipped permission sets (see `skills/apex/test-class-standards/references/gotchas.md` Gotcha 13), and why a validate-only deploy with `runTestsEnabled: false` proves nothing about field-level access.

**Where this came from:** `case-onboarding` build, F-60 (HIGH, design — "the most consequential finding of this build" per the mock-deploy log), `.sfskills/builds/case-onboarding/reports/MOCK-DEPLOY-M5.md` run 5.

---

## A Profile That Makes Record Types Visible And Names No Default Fails The Deploy

**What happens:** a profile fragment is written by hand (or generated) with one `recordTypeVisibilities` entry per new record type, each `visible=true`, and no `default` anywhere. The deploy comes back:

> No default record type specified for recordTypeVisibility: Opportunity. To make the '--master--' record type the default, set visible on all record types to false.

Org-verified 2026-09-19 against `sfskills-dev` (validate-only deploy at API 62.0, `.sfskills/builds/northwind-sales/reports/MOCK-DEPLOY-M2.md` run 1, `Profile Sales User`).

**When it bites you:** exactly when someone writes the block instead of retrieving it. The org's existing profile already names a default — often `--Master--`, often a record type that is not in your package at all — and a hand-written fragment silently drops it. The platform will not merge: the `recordTypeVisibilities` block you deploy is the whole story for that object.

**How to avoid it:**
- Retrieve the target profile first and merge into it, so the existing default survives.
- Or name a default yourself: exactly one `<default>true</default>` among the entries you make visible.
- Or make every listed entry `visible=false`, which hands the default back to `--Master--` — the second half of the org's own message.
- Or, better, do not put record-type visibility on the profile at all. Grant it from a permission set, where the element has no `default` child and this failure mode does not exist.
- `scripts/check_access_model.py` catches it as `PSVP-RT-DEFAULT-01` (ERROR, exit 1), per object, on `.profile-meta.xml` only. Fixtures: `scripts/fixtures/rt-default-positive/`, `scripts/fixtures/rt-default-negative/`.

