# Gotchas — Permission Set Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Permission Set Group Recalculation Delays Effective Access

**What happens:** Admins update a PSG or muting definition, assign it, and expect the user to have the new access immediately.

**When it occurs:** After editing or deploying permission set groups, especially in larger orgs where recalculation takes time.

**How to avoid:** Check recalculation status, plan deployments with validation time, and verify effective access with a real user after the group finishes processing. `PermissionSetGroup.Status` is a restricted picklist with four values — `Updated`, `Outdated`, `Updating`, `Failed` — so poll it rather than testing for a boolean, and treat `Failed` as an incident: the metadata deploy already returned success.

---

## Capability Bundles Break At License Boundaries

**What happens:** A beautifully designed permission set or PSG cannot be assigned to a subset of users because their licenses do not support one or more contained permissions.

**When it occurs:** In mixed-license orgs using Salesforce, Platform, Partner, or managed-package-specific user licenses.

**How to avoid:** Design bundle families around license boundaries first, then persona composition second. Validate with representative users from each license type. The `license` element (API 38.0+, replacing the deprecated `userLicense`) pins the set to one user license or permission set license; the Object Reference's own guidance is to leave `LicenseId` empty when a set will be assigned to users on different licenses.

---

## Moving Object Access But Forgetting Apex Class Access Creates False Migrations

**What happens:** Teams migrate object and field permissions into permission sets, but controllers, invocable Apex, tabs, or apps still depend on old profile access.

**When it occurs:** Profile-minimization projects that focus only on CRUD/FLS exports and ignore other setup entity access.

**How to avoid:** Review object, field, tab, app, Apex class, and custom permission access together for each persona before declaring the migration complete. The full element list on `PermissionSet` also includes `flowAccesses`, `pageAccesses`, `customMetadataTypeAccesses`, `customSettingAccesses`, and `externalCredentialPrincipalAccesses` — each one a separate migration surface.

---

## Muting Is Not A Cleanup Tool For Bad Bundle Design

**What happens:** Every exception gets handled with more muting, and the effective access model becomes harder to reason about than the profiles it replaced.

**When it occurs:** Teams skip capability design and jump straight to one giant PSG plus many muted variants.

**How to avoid:** Split oversized bundles into smaller capability-based permission sets before reaching for muting. Remember that a muting file reads inverted — it has the same fields as `PermissionSet`, but per the Metadata API guide, "settings enabled by MutingPermissionSet are turned off for the permission set group that it's a component of". A muting entry for a permission that no member set grants is a no-op that looks, on the page, like a grant.

---

## A Session-Based Permission Set Stops Requiring Activation Inside A Group

**What happens:** A set built for step-up access — `hasActivationRequired` true, activated per session through `SessionPermSetActivation` — is added to a persona PSG as a convenience. Everyone assigned the group now holds the permission continuously, with no activation event and no session scoping.

**When it occurs:** During PSG consolidation, when someone folds "one more set" into the persona bundle without reading its `hasActivationRequired` flag. The Object Reference states it plainly: if you include session-based permission sets in a permission set group, the permissions in them don't require session-based activation for users assigned to the group.

**How to avoid:** Keep session-based sets out of persona PSGs and assign them directly. `PermissionSetGroup` has its own `hasActivationRequired` field (API 53.0+) — that is the group-level control, and it is not inherited from a member.

---

## Field Permissions Silently Collapse When Read Is Missing

**What happens:** An FLS row written as edit-only does not produce an edit-only field. Either the deploy is rejected, or the record is removed and the field ends up with no access at all.

**When it occurs:** Generated or spreadsheet-driven FLS, where someone maps a "can edit" column to `editable` and leaves `readable` at its default. The Object Reference is explicit for `FieldPermissions.PermissionsEdit`: it requires `PermissionsRead` for the same field to be true, and a `FieldPermissions` record must have at minimum `PermissionsRead` true "or it will be deleted".

**How to avoid:** Treat `readable` as the floor for every FLS row and let the checker script reject the shape. The same dependency exists one level up on the object: create and edit require read, delete requires read plus edit, and a field grant on an object the set does not read grants nothing.

---

## Modify All Data Grants Object Access That Object Queries Cannot See Normally

**What happens:** An access audit queries `ObjectPermissions` for everything with full access, gets a clean result, and misses the permission sets that hold `Modify All Data` — or gets rows whose Id begins with `000` and cannot update or delete them.

**When it occurs:** Any org-wide "who can modify everything" sweep. Per the Object Reference, `Modify All Data` enables all object permissions without physically storing object permission records; the query still returns the permission set, but the row carries an invalid `000` Id that signals implicit full access. Removing the access means disabling `Modify All Data` first, then deleting the resulting record.

**How to avoid:** Audit `PermissionSet.PermissionsModifyAllData` and `PermissionsViewAllData` as user permissions in their own right, separately from the per-object `modifyAllRecords` / `viewAllRecords` sweep. Architecturally, keep both in a named override set that is never composed into a persona PSG.

---

## A Partial Permission Set File Is A Revocation

**What happens:** Someone hand-edits or hand-writes a `.permissionset-meta.xml` containing only the two permissions they wanted to add, deploys it, and wipes everything else the set held.

**When it occurs:** API version 40.0 and later. The Metadata API guide's warning on `PermissionSet`: when you retrieve permission set metadata, all content exposed in Metadata API is included, and when you deploy a permission set you must include all of its metadata "to avoid accidentally overwriting the permission set's contents". The same guide notes that in API 40.0+, a user permission not specified in a deployment is disabled.

**How to avoid:** Always retrieve the current file before editing it, and never construct a permission set file from a diff. This is also why permission sets are poor candidates for hand-merged pull requests — two people editing different halves of the same set produce a file that silently drops one half.

---

## Object And Field Permissions Vanish From A Retrieve That Omits The Object

**What happens:** A retrieve returns a permission set file whose `objectPermissions` and `fieldPermissions` blocks are much shorter than the org's real access, and a subsequent deploy of that file removes the missing rows.

**When it occurs:** When `package.xml` names `PermissionSet` but not the `CustomObject`, `RecordType`, `CustomTab`, or `CustomApplication` the permissions refer to. The Metadata API guide states the requirement directly: when retrieving object or field permissions, you must also retrieve the associated object; the same applies to app visibilities and to retrieving a `PermissionSetGroup` without its member `PermissionSet` components.

**How to avoid:** Build the manifest from the permission set outward — objects, record types, tabs, apps, custom permissions, then the sets, then the groups. Two further silent trimmers: `recordTypeVisibilities` is never retrieved or deployed for inactive record types, and enabling the object-level `viewAllFields` (API 63.0+) stops individual fields being returned under `fieldPermissions` at all.

---

## Absence Of A Permission Row Is Not A Queryable State

**What happens:** A governance query written as "find every permission set without read on this object" returns zero rows, and the reviewer concludes that no such set exists.

**When it occurs:** Any `ObjectPermissions` or `FieldPermissions` query filtering on a false value. Access is stored as a record and the absence of a record means no access, so `WHERE PermissionsRead = False` cannot match anything — the Object Reference gives this exact query as the example of what does not work. Setting every permission on a row to false also deletes the row, so a later query for that record Id returns nothing and a new record must be created to grant access again.

**How to avoid:** Express negative questions as set differences in the reporting layer: query the sets that *do* have access and subtract from the full inventory. Conditional filters only work once read is present — "read but not edit" is answerable, "no access at all" is not.

---

## The Profile You Are Migrating Away From Is Itself A Permission Set

**What happens:** An inventory script counts permission sets and reports a number far higher than the admin sees in Setup, or a "which sets grant X" query returns profile-shaped names that nobody created.

**When it occurs:** API version 25.0 and later, where every profile is associated with a permission set holding its user, object, and field permissions, exposed as `PermissionSet.IsOwnedByProfile = true` with a populated `ProfileId`. Those sets are queryable but not modifiable.

**How to avoid:** Filter on `IsOwnedByProfile = false` for anything that counts or audits real permission sets, and use `IsOwnedByProfile = true` deliberately when the question is "what does this profile still carry". The Object Reference also warns not to rely on the `Name` and `Label` returned for profile-owned sets, because those values can change.

---

## A `description` Over 255 Characters Fails The Deploy, And Takes The Group With It

**What happens:** A permission set, muting permission set, or profile carries a long rationale-style `description` — who owns it, why it exists, what it composes into — and the deploy is rejected with `Description: data value too large … (max length=255)`. Every `PermissionSetGroup` that lists the failed set among its `permissionSets` then fails too, with the unrelated-looking `permission set names are invalid`, because the member it depends on never landed.

**When it occurs:** Any deploy where `description` reads like a design note instead of a label. The Metadata API guide states the limit directly for `PermissionSet` and `Profile`: "Limit: 255 characters" on both. `MutingPermissionSet` shares `PermissionSet`'s field table. Verified by `sf project deploy start --dry-run` against a Summer '26 developer org on 2026-09-11: four permission sets and three profiles were rejected on this exact error, and the three permission set groups that referenced the rejected sets failed as a cascade (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md`, once exported).

**How to avoid:** Keep `description` to a one-line capability/owner statement and move the rationale to `deploy-order.md` or the configuration workbook. `scripts/check_permission_set_architecture.py` flags this before deploy: `PSA-DESC-01` (ERROR) at 255+ characters, `PSA-DESC-02` (INFO, headroom only — never fails the run) at 200+.

---

## A Platform Event Is An Object For Permission Purposes, And Its Persona Bundle Rarely Grants It

**What happens:** A persona's automation is wired to publish a Platform Event — a case-escalation webhook, an order-approved signal — and the permission set built for that persona lists the standard and custom sObjects the automation touches, but never the `__e` object itself. The bundle deploys clean, the `CustomObject` deploys clean, the Apex deploys clean; the gap only shows up when the persona's own user actually triggers the publish.

**When it occurs:** Any capability bundle for a persona whose automation calls `EventBus.publish`, built for an org on API 67.0 or later. `ObjectPermissions` and `FieldPermissions` are child records of `PermissionSet` regardless of what kind of object they name (see "Profiles Are The Base Layer" above) — a platform event is stored as a `CustomObject` and is subject to the same `objectPermissions` mechanism as any other sObject. At the API 67.0 user-mode default, Apex enforces the running user's object permissions, and that now includes Create on a published `__e` object where, before 67.0, it did not (`apex/platform-events-apex` references/gotchas.md, "API 67.0 Silently Moves Publishing Into User Mode"). Confirmed in a mock deploy: `.sfskills/builds/tier2-webhook/reports/MOCK-DEPLOY-M1.md` run 8, S2-F-13 — a Standard User holding the build's permission set had every escalation-event publish rejected with `"Tier2_Escalation__e publish rejected: Access to entity 'Tier2_Escalation__e' denied"`, because no permission set in the build granted Create on the event.

**How to avoid:** When slicing entitlements for a persona whose capability set publishes a Platform Event (step 1 of `## Recommended Workflow`), add an `objectPermissions` block for the `__e` object — `allowCreate` true, `allowRead` true is enough for a pure publisher — to that persona's permission set, exactly as you would for any other object the capability touches. Do not assume the event is covered because "it's not a real object" or because it worked before a version bump. `apex/platform-events-apex`'s checker (`scripts/check_platform_events_apex.py`, rule R9) flags an `EventBus.publish` with no Create grant anywhere in the scanned tree — run it alongside this skill's own checker when a bundle composes for an event-publishing persona.
