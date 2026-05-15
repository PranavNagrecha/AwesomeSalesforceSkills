# Gotchas — Managed Package Installation And Upgrade

Non-obvious Salesforce platform behaviors that cause real production problems for subscriber admins.

## Gotcha 1: 48-hour data retention on uninstall is the only undo

**What happens:** After uninstall, Salesforce emails a CSV export of package-introduced records to the running admin and retains it server-side for 48 hours, then deletes it permanently. No support escalation recovers the data after that.

**When it occurs:** Any uninstall of a package that owns Custom Objects. The exported records include all rows in package-introduced Custom Objects; subscriber fields added to managed objects survive the uninstall.

**How to avoid:** Pre-export package object data via Data Loader or Bulk API to durable storage (S3, archive bucket, secured share). Treat the Salesforce-side 48-hour export as a sanity-check artifact, not a recovery mechanism. Document the export location in the uninstall change record.

---

## Gotcha 2: Push patches arrive without subscriber consent

**What happens:** A 1GP or 2GP-managed package patch version (the third number in `X.Y.Z`) can be pushed by the publisher into all subscriber orgs on a chosen date. Subscribers cannot defer the patch within the maintenance window the publisher selects.

**When it occurs:** Whenever a publisher schedules a push upgrade from their packaging org. The notification reaches subscribers via release notes or email, not the in-product Setup UI.

**How to avoid:** Subscribe to every installed publisher's release-notes channel. Check Setup → Installed Packages monthly to detect version drift after maintenance windows. Treat publisher-patch release notes as a release-train input: scan for Apex method renames, field requirement changes, and Flow version replacements that may break subscriber-written code.

---

## Gotcha 3: Install for All Users is hard to reverse

**What happens:** Choosing Install for All Users at install time updates the bundled profile settings on every standard and custom profile in the org. Subsequent upgrades preserve these grants; revoking them requires per-profile field-level edits across all affected profiles.

**When it occurs:** When the vendor's quickstart documentation says "Install for All Users" and the admin trusts it. The grant becomes part of the org's profile baseline and is no longer visibly attributed to the package.

**How to avoid:** Default to Install for Admins Only. Grant feature access via Permission Sets and Permission Set Groups the package ships. These grants are explicit, reversible (revoke = unassign), and auditable (Permission Set assignment history is queryable).

---

## Gotcha 4: Beta packages cannot install in production

**What happens:** A package version that has not been "Released" by the publisher (a beta version) installs successfully in sandboxes, Developer Edition orgs, and scratch orgs, but fails with a not-installable error in production.

**When it occurs:** When the vendor shares a beta install URL for early-access features and the subscriber attempts to install it in production after sandbox validation.

**How to avoid:** Confirm with the publisher in writing that the version ID is "Released," not "Beta," before any production install. The `04t...` ID itself does not reveal its state — only the publisher's packaging-org records show it.

---

## Gotcha 5: API name collisions on packaged-object fields

**What happens:** Subscribers can add fields to packaged Custom Objects. When the publisher pushes an upgrade that adds a field with the same API name (without the namespace prefix), the upgrade fails with a name conflict.

**When it occurs:** Subscriber added `Status__c` to a package-introduced object `pkg__Account_Plan__c`. Publisher upgrade adds `Status__c` to the same object. Field-level conflict — the upgrade fails partway through, leaving the org in an indeterminate state.

**How to avoid:** Inventory subscriber-added fields on packaged objects before each upgrade. Match the field API name list against the publisher's upgrade notes when available. Rename subscriber fields proactively (e.g., to `Custom_Status__c`) before installing the upgrade.

---

## Gotcha 6: InstallHandler runs as Automated Process, not the admin

**What happens:** The publisher's `InstallHandler` Apex executes during install with `UserInfo.getUserId()` returning the special "Automated Process" user, not the admin clicking the install URL. Any logic that depends on the running user — sharing rules, OWD enforcement, audit fields — sees the Automated Process user.

**When it occurs:** Anytime an `InstallHandler` calls `UserInfo.getUserId()`, `Database.getUserId()`, or queries `User` records expecting the install runner. Also when subscribers debug a failed install — `Setup → Apex Jobs` shows the Automated Process user as the executor.

**How to avoid:** Publisher-side concern primarily, but subscribers should know to look for the Automated Process user in Apex Jobs / debug logs when diagnosing install failures. If a post-install step requires user attribution, run it as a separate admin-initiated action after install completes.

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
