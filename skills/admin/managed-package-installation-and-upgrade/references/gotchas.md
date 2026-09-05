# Gotchas — Managed Package Installation And Upgrade

Non-obvious Salesforce platform behaviors that cause real production problems for subscriber admins.

## Gotcha 1: 48-hour data retention on uninstall is the only undo

**What happens:** After uninstall, Salesforce emails a CSV export of package-introduced records to the running admin and retains it server-side for 48 hours, then deletes it permanently. No support escalation recovers the data after that.

**When it occurs:** Any uninstall of a package that owns Custom Objects. The exported records include all rows in package-introduced Custom Objects; subscriber fields added to managed objects survive the uninstall.

**How to avoid:** Pre-export package object data via Data Loader or Bulk API to durable storage (S3, archive bucket, secured share). Treat the Salesforce-side 48-hour export as a sanity-check artifact, not a recovery mechanism. Document the export location in the uninstall change record.

UNVERIFIED (2026-09-05): the 48-hour figure is not stated in any Metadata API, Object Reference, or Apex guide extract available here — it rests on the First-Generation Managed Packaging Developer Guide's uninstall page, which could not be fetched to re-confirm. The pre-export step above is what makes the uninstall safe regardless of the true retention window; do not let the runbook depend on the number without re-checking it against current documentation.

---

## Gotcha 2: Push upgrades arrive without a subscriber click — but the block switch is real and off by default

**What happens:** A publisher schedules a push upgrade from their packaging org by creating a `PackagePushRequest` with a `ScheduledStartTime`; Salesforce fans it out into one `PackagePushJob` per eligible subscriber org. Nobody in the subscriber org clicks anything. The subscriber org *can* refuse: `PackageSubscriber.HasRestrictionEnabled` "Indicates whether the subscriber org has blocked push upgrades" and its default value is `false`, and `CustomUpgradeType` carries the value `BlockedBySubscriber` (Object Reference, `PackageSubscriber`, `object_reference.txt` L208252–208279). So the correct statement is not "subscribers cannot defer" — it is "subscribers have not blocked, because blocking is opt-in and nobody turned it on."

**When it occurs:** Push upgrade is available only to 1GP and 2GP managed packages that have passed AppExchange security review, and to unlocked packages — where it is **enabled by default** (`object_reference.txt` L208025–208029, L208245–208249). Timing is not a promise: "Scheduled push upgrades begin as soon as resources are available on the Salesforce instance, which is either at or after the start time you specify. In certain scenarios, the push upgrade could start a few hours after the scheduled start time" (`object_reference.txt` L208087–208090). Orgs with `OrgStatus = 'Inactive'` are skipped entirely (L208352).

**How to avoid:** Decide the block posture per package rather than per incident, and record it in `config/package-inventory.json` as `pushUpgradesBlocked` so the checker can see it. Ask each publisher, in writing, whether push upgrades are enabled for your org and whether they honour a block request — the switch lives on their `PackageSubscriber` record, not in your Setup. Then subscribe to the publisher's release-notes channel and check Setup → Installed Packages monthly for version drift; a push that lands is indistinguishable from an install nobody logged.

---

## Gotcha 3: Install for All Users is hard to reverse

**What happens:** Choosing Install for All Users at install time updates the bundled profile settings on every standard and custom profile in the org. Subsequent upgrades preserve these grants; revoking them requires per-profile field-level edits across all affected profiles.

**When it occurs:** When the vendor's quickstart documentation says "Install for All Users" and the admin trusts it. The grant becomes part of the org's profile baseline and is no longer visibly attributed to the package.

**How to avoid:** Default to Install for Admins Only. Grant feature access via Permission Sets and Permission Set Groups the package ships. These grants are explicit, reversible (revoke = unassign), and auditable (Permission Set assignment history is queryable).

---

## Gotcha 4: Beta packages cannot install in production

**What happens:** A package version that has not been "Released" by the publisher (a beta version) installs successfully in sandboxes, Developer Edition orgs, and scratch orgs, but fails with a not-installable error in production.

**When it occurs:** When the vendor shares a beta install URL for early-access features and the subscriber attempts to install it in production after sandbox validation.

**How to avoid:** Confirm with the publisher in writing that the version ID is "Released," not "Beta," before any production install. The `04t...` ID itself does not reveal its state; the state lives in `MetadataPackageVersion.ReleaseState`, whose valid values are `Beta` and `Released`, on an object that "represents a package version … that has been uploaded from the org you're logged in to" — that is the publisher's packaging org, not yours (`object_reference.txt` L182729–182730, L182821–182825). A push upgrade cannot carry a beta either: `PackagePushRequest.PackageVersionId` is documented as "the non-beta, non-deprecated package version" (`object_reference.txt` L208071–208073).

UNVERIFIED (2026-09-05): the specific claim that a beta version *fails* to install in production is not stated in the extracts available here — what is grounded is that beta is a distinct, publisher-visible release state that push upgrades refuse. Ask the publisher for the state rather than relying on the install to refuse.

---

## Gotcha 5: API name collisions on packaged-object fields

**What happens:** Subscribers can add fields to packaged Custom Objects. When the publisher pushes an upgrade that adds a field with the same API name (without the namespace prefix), the upgrade fails with a name conflict.

**When it occurs:** Subscriber added `Status__c` to a package-introduced object `pkg__Account_Plan__c`. Publisher upgrade adds `Status__c` to the same object. Field-level conflict — the upgrade fails partway through, leaving the org in an indeterminate state.

**How to avoid:** Inventory subscriber-added fields on packaged objects before each upgrade. Match the field API name list against the publisher's upgrade notes when available. Rename subscriber fields proactively (e.g., to `Custom_Status__c`) before installing the upgrade.

---

## Gotcha 6: The post-install script runs as the package's own system user, and its records are not attributed to the installing admin

**What happens:** The publisher's `InstallHandler` runs during install as "a special system user that represents your package, so all operations performed by the script appear to be done by your package. You can access this user by using `UserInfo`. You only see this user at runtime, not while running tests" (Apex Reference Guide, `InstallHandler` Interface, `apexrefguide.txt` L217791–217793). Every `CreatedById` the script writes points at that package user, not at the admin who ran the install — so field history, audit trails, and any sharing or OWD evaluation inside the script resolve against a user your org does not own. The installing admin *is* available, but only through the context object: `InstallContext.installerId()` (`apexrefguide.txt` L217816–217825).

**When it occurs:** On every install and upgrade of a package that declares a `postInstallClass`. It surfaces when an admin searches audit history for "who created these 400 config records" and finds a user that does not appear in the user list, or when a data-quality rule keyed on `CreatedBy` skips the package's seeded rows.

**How to avoid:** When reconciling post-install state, filter by `CreatedDate` inside the install window rather than by `CreatedById`. Do not build subscriber automation that assumes package-seeded records carry a real user. The script also cannot access session IDs and can only make callouts asynchronously, after the install has committed (`apexrefguide.txt` L217796–217800) — so an install that "succeeded" may still have a callout in flight that fails minutes later, outside the install result.

---

## Gotcha 7: Permission Sets bundled with the package are deleted on uninstall

**What happens:** Permission Sets the package ships are managed components — they're deleted along with the package on uninstall, taking all user assignments with them. Subscriber-org Permission Sets that grant access to the same managed objects survive.

**When it occurs:** Uninstalling a package without first migrating user grants to subscriber-org Permission Sets. The admin completes the uninstall, then realizes Permission-Set-Group composition needs to be rebuilt.

**How to avoid:** For long-lived installs, build subscriber-org Permission Sets that mirror the access surface of the package's bundled Permission Sets. This survives the uninstall and provides a stable assignment target for Permission Set Groups.

---

## Gotcha 8: Package install duration is unbounded by SLA

**What happens:** A package install can take 5 minutes or 90 minutes depending on metadata count, Apex compile time, and field-backfill DML on existing data. There is no per-package SLA from Salesforce.

**When it occurs:** Especially long for upgrades that add new required fields on objects with millions of records (the upgrade includes a DML-bound backfill step) and for packages with thousands of Apex classes.

**How to avoid:** Measure install duration in the Full Sandbox refresh that mirrors production volumes. Schedule production install with at least 2x the sandbox duration as a buffer. Avoid Friday-evening installs and any window adjacent to a Salesforce release maintenance event.

---

## Gotcha 9: The two install paths ship opposite security defaults

**What happens:** The same install performed two ways grants two different audiences. Deploying an `InstalledPackage` file that omits `securityType`, the Metadata API Developer Guide states: "The `securityType` field is optional. If it's not specified, the default security type is `AllUsers`" (`api_meta.txt` L81450; the field table at L81428–81432 repeats "The default value is `AllUsers`"). Installing the same `04t` through the CLI, `sf package install --help` reports `-s, --security-type` as "[default: AdminsOnly]" (verified against `@salesforce/cli/2.149.9`). One path grants the package surface org-wide through profile settings; the other grants it to System Administrator only. Neither prints a warning.

**When it occurs:** Whenever the install is scripted rather than clicked — a CI job that deploys an `installedPackages/` directory, or an `InstalledPackage` file copied from a sandbox retrieve, where `securityType` is frequently absent because the retrieve did not populate it.

**How to avoid:** Never let `securityType` be implicit. Write it into every `installedPackage` file, and pass `--security-type` explicitly on every CLI install even when you want the default. The checker in this skill's `scripts/` directory flags an `installedPackage` file with no `securityType` element for exactly this reason.

---

## Gotcha 10: `activateRSS` defaults to false, so the package's remote sites arrive switched off

**What happens:** `activateRSS` is a **required** field on `InstalledPackage` that "determines the state of Remote Site Settings (RSS) and Content Security Policy (CSP) at the time of installing the package": `true` keeps the `isActive` state of any RSS or CSP in the package, `false` overrides that state and sets it to `false`. "The default value is `false`" (`api_meta.txt` L81416–81426). A package whose features call an external endpoint installs cleanly and then fails at first use with an unauthorized-endpoint error.

**When it occurs:** On any package that ships Remote Site Settings or CSP Trusted Sites — integration connectors, payment processors, address-validation add-ons. The failure appears hours or days after the install, during the first real user transaction, which decouples it from the install in everyone's memory.

**How to avoid:** Set `activateRSS` explicitly in the file and treat the value as a security decision, not a formality — `true` accepts the publisher's endpoint list as-is, `false` means you intend to review and enable each endpoint by hand in Setup → Remote Site Settings. Whichever you choose, add "confirm every packaged Remote Site Setting and CSP Trusted Site is in the intended state" to the post-install checklist, because a UI-driven install does not surface this choice at all.

---

## Gotcha 11: An install deployment cannot carry anything else, and caps at 20 packages

**What happens:** "You can't deploy a package along with other metadata types. When you deploy `InstalledPackage`, it must be the only metadata type specified in the manifest file," and "You can install up to 20 first-generation managed packages in a single deployment" (`api_meta.txt` L81390–81395). A manifest that mixes `InstalledPackage` with the Permission Sets that grant the package's surface fails as a whole — the install and the grant cannot be atomic.

**When it occurs:** When an org's deployment pipeline treats `installedPackages/` as just another source directory and a full-org `package.xml` sweeps it in alongside classes, objects, and permission sets.

**How to avoid:** Give the install its own manifest and its own pipeline stage, sequenced before the stage that deploys the subscriber-owned Permission Sets referencing the packaged components. Exclude `installedPackages/**` from the general deploy manifest. For 2GP and unlocked packages the type does not apply at all — those install through `sf package install` (`api_meta.txt` L81391–81392), which is a separate pipeline step again.

---

## Gotcha 12: Certified packages get their own governor limits; non-certified ones eat yours

**What happens:** "Certified managed packages — managed packages that have passed the security review for AppExchange — get their own set of limits for most per-transaction limits" (Salesforce Developer Limits and Allocations Quick Reference, `salesforce_app_limits_cheatsheet.txt` L189–192). Install a certified package and its Apex gets its own 150 DML statements and its own 100 synchronous SOQL queries **in addition** to your org's (L194–200). Install a package that is *not* certified and you get the opposite: "Namespaces in non-certified packages don't have their own separate governor limits. The resources that they use continue to count against the same governor limits used by the org's custom code" (L213–215). The same package code is either free or a tax on your own automation depending on a review status you cannot see from the install screen.

**When it occurs:** In a transaction where the package's trigger and your trigger both fire on the same object. With a certified package the two budgets are independent; with a non-certified one, the package's queries consume the 100 your code was counting on, and your code throws the limit exception.

**How to avoid:** Confirm the certification status before install and record it in `config/package-inventory.json` — a direct install URL from an ISV is not evidence of certification, and the certified/non-certified distinction also decides whether push upgrades are even possible for that package (`object_reference.txt` L208025–208029). Know the ceilings that no certification lifts: the cumulative cross-namespace limit is 11× the per-namespace limit — 1,100 SOQL queries, 1,650 DML statements, 1,100 callouts, 220 SOSL queries, 110 `sendEmail` calls, 110,000 `Database.getQueryLocator` records (L230–240) — and total heap size, maximum CPU time, maximum transaction execution time, and maximum number of unique namespaces count for the entire transaction regardless of how many certified packages are running (L243–249). CPU time is the one that actually bites: a certified package cannot buy you more of it.

---

## Gotcha 13: A failed install script aborts the install; a failed uninstall script does not stop the uninstall

**What happens:** The two handlers fail in opposite directions. For `InstallHandler`: "If the script fails, the install or upgrade is aborted" (`apexrefguide.txt` L217794). For `UninstallHandler`: "If the script fails, the uninstall continues but none of the changes performed by the script are committed" (`apexrefguide.txt` L242376–242377). So a broken uninstall script leaves the package gone and its cleanup — external-system deregistration, licence release, notification — silently not done. In both cases "any errors in the script are emailed to the user specified in the **Notify on Apex Error** field of the package. If no user is specified, the [install or uninstall] details are unavailable" — that field belongs to the publisher's package, so the error mail goes to the publisher, and the subscriber admin may see only a bare failure.

**When it occurs:** On any install or uninstall of a package declaring `postInstallClass` or `uninstallClass` (`api_meta.txt` L94303–94326). Most visible when an install aborts with no explanation the subscriber can act on.

**How to avoid:** When an install aborts and the org shows nothing useful, stop and raise it with the publisher rather than retrying — the diagnostic went to their Notify on Apex Error address, and a retry reproduces the same failure. Before an uninstall, ask the publisher what the uninstall script is supposed to do externally and verify that side independently afterwards (seat released in their console, webhook deregistered); the uninstall completing is not evidence the script ran.

---

## Gotcha 14: Permission grants on packaged components cannot use wildcards

**What happens:** Access settings for managed components in profiles and permission sets are retrievable and deployable from API 29.0 onward, but only for a closed list — Apex classes, apps, custom field permissions, custom object permissions, custom tab settings, external data sources, record types, Visualforce pages, plus login flows in API 51.0+ — and "when retrieving and deploying managed component permissions, specify the namespace followed by two underscores. **Wildcards aren't supported**" (`api_meta.txt` L2431–2443). Every packaged object, every packaged field must be enumerated by hand in the Permission Set XML, and a retrieve of the Permission Set silently returns nothing for the packaged components unless the packaged object is *also* named in the same manifest (L2466–2469).

**When it occurs:** On the upgrade after the one where you built the grant. The publisher adds fields; your Permission Set does not know about them; users get the new tab and an empty column. It also occurs on the first retrieve — an admin retrieves the Permission Set to check the grant, sees no packaged fields, and concludes the grant is empty.

**How to avoid:** Regenerate the field list from the package's current footprint at every minor and major upgrade rather than hand-maintaining it; Setup → Installed Packages → View Components is the authoritative list of what the version added. Keep the packaged object in the same `package.xml` as the Permission Set so retrieves round-trip. Anything the package ships that is not on the eight-item list above cannot be granted through a permission set at all — that gap belongs on the post-install checklist as a manual Setup step.
