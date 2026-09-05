# Metadata Examples — Managed Package Installation and Upgrade

Deployable metadata for the subscriber-org side of a managed package: installing and
upgrading via `InstalledPackage`, granting the package's surface through a subscriber-owned
Permission Set, reconciling licences, and verifying after install.

Package **authoring** (namespace registration, `postInstallClass`, uploading versions, scheduling
push upgrades) is `devops/managed-package-development` and `devops/second-generation-managed-packages`.
Nothing on this page runs in a packaging org.

---

## Where the files live

| Artefact | Source-format path | MDAPI path | Grounding |
|---|---|---|---|
| Package install directive | `force-app/main/default/installedPackages/<ns>.installedPackage-meta.xml` | `installedPackages/<ns>.installedPackage` | Metadata API Guide, `InstalledPackage` — "specified in the `installedPackages` directory, in a file named after the package's namespace prefix. The file extension is `.installedPackage`" (`api_meta.txt` L81397–81400); SDR registry `installedpackage` entry: `directoryName: installedPackages`, `suffix: installedPackage` |
| Subscriber access grant | `force-app/main/default/permissionsets/<Name>.permissionset-meta.xml` | `permissionsets/<Name>.permissionset` | `api_meta.txt` L94718–94722 |
| Pre-upgrade inventory (not Salesforce metadata) | `config/package-inventory.json` | — | Repo artefact; linted by this skill's checker |

The file's **base name is the namespace prefix**, not the package name and not the version ID.
A namespace prefix is a 1–15 character alphanumeric identifier and is case-insensitive
(`api_meta.txt` L22290–22294: "a one to 15-character alphanumeric identifier … Namespace prefixes
are case-insensitive. For example, ABC and abc aren't recognized as unique").

UNVERIFIED (2026-09-05): the guides available here say "alphanumeric" for a namespace prefix
without stating whether an underscore is permitted; the adjacent `Package.fullName` rule does
permit underscores — "can contain only underscores and alphanumeric characters. It must be unique,
begin with a letter, not include spaces, not end with an underscore, and not contain two
consecutive underscores" (`api_meta.txt` L94288–94294). The examples below use `acme_rev`, and this
skill's checker accepts `[A-Za-z][A-Za-z0-9_]{0,14}` on that basis. If a publisher's namespace
contains an underscore, take the publisher's spelling as authoritative.

---

## 1. `InstalledPackage` — the guide's own sample

Shipped verbatim in the Metadata API Developer Guide (`api_meta.txt` L81441–81448):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<InstalledPackage xmlns="http://soap.sforce.com/2006/04/metadata">
    <versionNumber>1.0</versionNumber>
    <password>optional_password</password>
    <securityType>AdminsOnly</securityType>
    <activateRSS>true</activateRSS>
</InstalledPackage>
```

Field semantics, all from `api_meta.txt` L81415–81439:

| Field | Required | Values / format | Note |
|---|---|---|---|
| `versionNumber` | **Required** | `majorNumber.minorNumber.patchNumber`, e.g. `2.1.3` | This is what makes a redeploy an *upgrade*: "Deploying a newer version of a currently installed package upgrades the package" (L81390–81391) |
| `activateRSS` | **Required** | `true` \| `false` | `true` keeps the `isActive` state of any Remote Site Setting or CSP Trusted Site in the package; `false` overrides them to `false`. **Default is `false`** — omit it and the package's remote sites arrive inactive. API 43.0+ |
| `securityType` | optional | `AdminsOnly` \| `AllUsers` | **"The default value is `AllUsers`."** API 57.0+ |
| `password` | optional | string | The installation key for a key-protected package |

---

## 2. Realistic subscriber install — one namespace, admins-only, remote sites live

`force-app/main/default/installedPackages/acme_rev.installedPackage-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<InstalledPackage xmlns="http://soap.sforce.com/2006/04/metadata">
    <versionNumber>4.2.1</versionNumber>
    <securityType>AdminsOnly</securityType>
    <activateRSS>true</activateRSS>
</InstalledPackage>
```

**How to read it:**

- `acme_rev` in the file name is the publisher's namespace prefix. Every packaged component in the
  org will be addressed as `acme_rev__Something__c` — two underscores (`api_meta.txt` L2343–2345).
- `4.2.1` names the exact version. Deploying this file into an org that already holds `4.1.0`
  performs the upgrade; deploying it into an org that already holds `4.2.1` is a no-op; there is no
  "latest" token.
- `securityType` is stated explicitly on purpose. Leaving it out selects `AllUsers`, which grants
  the package surface through profile settings across the org (see `references/gotchas.md`, Gotcha 9).
- `activateRSS` is stated explicitly on purpose. Its documented default is `false`, which would
  land the package's Remote Site Settings and CSP Trusted Sites inactive and break the package's
  callouts on first use.
- No `password` element: this package is not key-protected. If it is, the element carries the
  installation key the publisher gave you — treat that value as a secret and keep it out of
  version control (source it from a CI variable at build time).

---

## 3. `package.xml` for the install deploy — and why it holds nothing else

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>acme_rev</members>
        <name>InstalledPackage</name>
    </types>
    <version>62.0</version>
</Package>
```

Two hard constraints, both from `api_meta.txt` L81390–81395:

1. **"You can't deploy a package along with other metadata types. When you deploy
   `InstalledPackage`, it must be the only metadata type specified in the manifest file."**
   So the install is always its own deployment, never bundled with the Permission Set in §5.
2. **"You can install up to 20 first-generation managed packages in a single deployment."**

`InstalledPackage` supports the `*` wildcard in `package.xml` (`api_meta.txt` L81460–81462), which
is how you *retrieve* the current install state of an org:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>InstalledPackage</name>
    </types>
    <version>62.0</version>
</Package>
```

`InstalledPackage` is also on the list of metadata types that, in API 33.0 and earlier, forced all
local tests to run on a production deploy (`api_meta.txt` L2500–2520). Tests that originate from
installed managed packages are **not** executed by a production deploy by default
(`api_meta.txt` L2436–2439 and L2477–2480) — a package's own test suite is not your install gate.

---

## 4. Retrieve, deploy, and the CLI equivalent

Capture what is installed today, before you plan an upgrade:

```bash
# Current install state as metadata
sf project retrieve start --manifest manifest/installed-packages.xml --target-org prod

# Current install state as a table (namespace, version, package ID)
sf package installed list --target-org prod
sf package installed list --target-org prod --json > config/prod-installed.json
```

Deploy the install/upgrade — check first, then run:

```bash
sf project deploy start \
  --source-dir force-app/main/default/installedPackages \
  --target-org uat --dry-run

sf project deploy start \
  --source-dir force-app/main/default/installedPackages \
  --target-org uat
```

The CLI install path is equivalent for 1GP and is the **only** supported path for 2GP and unlocked
packages — the Metadata API type covers 1GP only: "Represents a first-generation managed package…
To install an unlocked or second-generation managed package, use the `sf package install`
Salesforce CLI command" (`api_meta.txt` L81390–81392).

```bash
sf package install \
  --package 04t8b000001abcdAAB \
  --target-org uat \
  --security-type AdminsOnly \
  --installation-key "$PKG_INSTALL_KEY" \
  --wait 20 \
  --publish-wait 10 \
  --no-prompt
```

Flags verified against `sf package install --help`, `@salesforce/cli/2.149.9`:

| Flag | Values | Default | Applies to |
|---|---|---|---|
| `-p, --package` | `04t…` ID or alias | — | required |
| `-s, --security-type` | `AllUsers` \| `AdminsOnly` | **`AdminsOnly`** | all packages |
| `-t, --upgrade-type` | `DeprecateOnly` \| `Mixed` \| `Delete` | `Mixed` | **unlocked packages only** |
| `-a, --apex-compile` | `all` \| `package` | `all` | **unlocked packages only** |
| `-k, --installation-key` | string | null | key-protected packages |
| `-w, --wait` | minutes | — | install status poll |
| `-b, --publish-wait` | minutes | — | wait for the `04t` to become available in the target org |

The CLI's `--security-type` default (`AdminsOnly`) is the **opposite** of the Metadata API
`securityType` default (`AllUsers`). Two paths to the same install, two different silent outcomes.

Uninstall is asymmetric, per `sf package uninstall --help` (same CLI version): the command
"Uninstall**s** a second-generation package from the target org" and its description states
"To uninstall a first-generation package, from Setup, enter Installed Packages in the Quick Find
box, then select Installed Packages." There is no `destructiveChanges.xml` recipe for
`InstalledPackage` in the Metadata API Developer Guide — the guide's `destructiveChanges` sections
(`api_meta.txt` L4615–4680) never name it.
UNVERIFIED (2026-09-05): whether `destructiveChanges.xml` with an `InstalledPackage` member
uninstalls a 1GP package is not stated either way in `api_meta.txt`; plan 1GP uninstall through
Setup and do not rely on a destructive deploy.

```bash
# 2GP / unlocked only
sf package uninstall --package 04t8b000001abcdAAB --target-org uat --wait 30
```

---

## 5. Subscriber-owned Permission Set granting the package surface

The package ships its own Permission Sets — those are managed components and disappear with the
package, taking their assignments (see `references/gotchas.md`, Gotcha 7). A subscriber-owned
Permission Set that names the packaged components survives, and is the stable assignment target for
a Permission Set Group.

`force-app/main/default/permissionsets/Revenue_Rec_User_Access.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Revenue Rec — User Access</label>
    <description>Subscriber-owned grant for the acme_rev managed package. Survives uninstall of the package's own permission sets.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>acme_rev__Revenue_Schedule__c</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>acme_rev__Revenue_Schedule__c.acme_rev__Recognized_Amount__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>false</editable>
        <field>Opportunity.acme_rev__Recognition_Method__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <classAccesses>
        <apexClass>acme_rev.RevenueScheduleService</apexClass>
        <enabled>true</enabled>
    </classAccesses>
    <tabSettings>
        <tab>acme_rev__Revenue_Schedule__c</tab>
        <visibility>Visible</visibility>
    </tabSettings>
</PermissionSet>
```

**How to read it:**

- Every packaged API name carries `namespace__`. "When retrieving and deploying managed component
  permissions, specify the namespace followed by two underscores. **Wildcards aren't supported.**"
  (`api_meta.txt` L2442–2443). You must enumerate each object and field by hand.
- Access settings for managed components in profiles and permission sets are retrievable and
  deployable from API 29.0 onward, and the supported list is exactly: Apex classes, apps, custom
  field permissions, custom object permissions, custom tab settings, external data sources, record
  types, Visualforce pages (`api_meta.txt` L2431–2440) — plus login flows in API 51.0+ (L2441).
  Anything the package ships that is not on that list cannot be granted this way.
- `Opportunity.acme_rev__Recognition_Method__c` is a packaged *field on a standard object* — the
  object has no prefix, the field does.
- `label` is required, limit 80 characters (`api_meta.txt` L94824). Omit `license` unless the
  package requires a specific permission set licence; `license` is "either the related permission
  set license or the user license associated with this permission set" (`api_meta.txt` L94826–94830)
  and pinning the wrong one blocks assignment.
- No `userLicense` element — it is deprecated and only available through API 37.0
  (`api_meta.txt` L94828–94830).

To **retrieve** this Permission Set you must also retrieve the packaged object it references —
"when retrieving object or field permissions, you must also retrieve the associated object"
(`api_meta.txt` L2466–2469):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>acme_rev__Revenue_Schedule__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Revenue_Rec_User_Access</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

---

## 6. Licence reconciliation — `PackageLicense` and `UserPackageLicense`

An install can succeed and still leave users locked out: package **licences** are separate from
object permissions. Both objects are API 31.0 and later (`object_reference.txt` L207541, L300773).

Org-level position, one row per licensed managed package:

```sql
SELECT NamespacePrefix, Status, AllowedLicenses, UsedLicenses, ExpirationDate
FROM PackageLicense
ORDER BY NamespacePrefix
```

`Status` is a restricted picklist with exactly four values — `Active`, `Expired`, `Free`, `Trial`
(`object_reference.txt` L207600–207605). `AllowedLicenses` is "the number of users allowed to use
the package"; `UsedLicenses` is "the number of users who have a license to the package"
(L207554–207559, L207607–207612). `PackageLicense` supports only `describeSObjects()`, `query()`,
`retrieve()` (L207544–207545) — you cannot buy or move seats through the API.

Who holds a seat, and who is entitled but unlicensed:

```sql
SELECT PackageLicense.NamespacePrefix, User.Username, User.IsActive
FROM UserPackageLicense
WHERE PackageLicense.NamespacePrefix = 'acme_rev'
ORDER BY User.Username
```

`UserPackageLicense` supports `create()`, `delete()`, `describeSObjects()`, `query()`,
`retrieve()`, `update()` (`object_reference.txt` L300776–300777) — assignment and revocation are
DML on this object, one row per user with `PackageLicenseId` + `UserId` (L300830–300866).

The Object Reference's own worked example bulk-assigns by profile and catches the seat ceiling as a
DML status code (`object_reference.txt` L207618–207684). Adapted to assign by Permission Set Group
membership instead of profile, and to report rather than throw:

```apex
public with sharing class PackageSeatReconciler {
    // Seats the org owns vs. seats it has handed out, for one namespace.
    public static void assignByPermissionSet(String namespacePrefix, Id permSetId) {
        PackageLicense pl = [
            SELECT Id, NamespacePrefix, AllowedLicenses, UsedLicenses, ExpirationDate, Status
            FROM PackageLicense
            WHERE NamespacePrefix = :namespacePrefix
            LIMIT 1
        ];

        Set<Id> licensed = new Set<Id>();
        for (UserPackageLicense upl : [
            SELECT UserId FROM UserPackageLicense WHERE PackageLicenseId = :pl.Id
        ]) {
            licensed.add(upl.UserId);
        }

        List<UserPackageLicense> toGrant = new List<UserPackageLicense>();
        for (PermissionSetAssignment psa : [
            SELECT AssigneeId FROM PermissionSetAssignment
            WHERE PermissionSetId = :permSetId AND Assignee.IsActive = true
        ]) {
            if (!licensed.contains(psa.AssigneeId)) {
                toGrant.add(new UserPackageLicense(
                    PackageLicenseId = pl.Id,
                    UserId = psa.AssigneeId
                ));
            }
        }

        Integer free = pl.AllowedLicenses - pl.UsedLicenses;
        if (toGrant.size() > free) {
            // Stop before the platform does. The Object Reference example catches this as
            // DmlException status code LICENSE_LIMIT_EXCEEDED after the fact.
            throw new IllegalArgumentException(
                'Need ' + toGrant.size() + ' seats for ' + namespacePrefix +
                ' but only ' + free + ' are free (allowed ' + pl.AllowedLicenses +
                ', used ' + pl.UsedLicenses + ').'
            );
        }
        insert toGrant;
    }
}
```

The `LICENSE_LIMIT_EXCEEDED` DML status code is documented in that same example
(`object_reference.txt` L207680–207684).

---

## 7. Pre-upgrade checklist artefact — `config/package-inventory.json`

The one file the checker in `scripts/check_managed_package_installation_and_upgrade.py` reads for
licence, drift, and ownership state. Keep it beside the manifest and refresh it from
`sf package installed list --json` plus the `PackageLicense` query in §6.

```json
{
  "generated": "2026-09-05",
  "environments": ["uat", "prod"],
  "packages": [
    {
      "namespace": "acme_rev",
      "name": "Acme Revenue Recognition",
      "generation": "1GP",
      "owner": "finance-systems@example.com",
      "versions": { "uat": "4.2.1", "prod": "4.2.1" },
      "securityType": "AdminsOnly",
      "licenses": {
        "allowed": 50,
        "used": 12,
        "status": "Active",
        "expirationDate": "2027-03-31"
      },
      "pushUpgradesBlocked": false,
      "subscriberCodeReferences": [
        "force-app/main/default/classes/RevenueSyncBatch.cls"
      ]
    },
    {
      "namespace": "mkt_pkg",
      "name": "Legacy Marketing Automation",
      "generation": "1GP",
      "owner": null,
      "versions": { "uat": "3.0.0", "prod": "2.8.4" },
      "securityType": "AllUsers",
      "licenses": {
        "allowed": 100,
        "used": 104,
        "status": "Expired",
        "expirationDate": "2026-06-30"
      },
      "pushUpgradesBlocked": false,
      "subscriberCodeReferences": []
    }
  ]
}
```

The second entry is what a bad row looks like and what the checker flags: no owner, an expired
licence, more seats used than allowed, a two-version drift between UAT and production, and
`AllUsers` security. Run it before writing the upgrade runbook:

```bash
python3 skills/admin/managed-package-installation-and-upgrade/scripts/check_managed_package_installation_and_upgrade.py \
  --manifest-dir .
```

---

## 8. Verify after the install

Three checks, in order. Nothing here requires the publisher's cooperation.

**a. The version that actually landed**

```bash
sf package installed list --target-org prod
```

Compare the reported version against the `versionNumber` you deployed. A silent no-op (the org was
already on that version) and a successful upgrade look identical in the deploy result.

**b. Seats are provisioned, not just permissions**

```sql
SELECT NamespacePrefix, Status, AllowedLicenses, UsedLicenses, ExpirationDate
FROM PackageLicense
WHERE NamespacePrefix = 'acme_rev'
```

Expect `Status = 'Active'`, an `ExpirationDate` beyond the next renewal, and `UsedLicenses`
matching the count of users you intended to enable. `UsedLicenses = 0` after a successful install
is the normal state and the normal support ticket — the install grants no seats.

**c. The grant reaches real users**

```sql
SELECT Assignee.Username, PermissionSet.Name
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'Revenue_Rec_User_Access'
```

Then, as one canary user, confirm the packaged tab renders and one packaged record saves. Setup →
Installed Packages → View Components lists everything the package added, for the footprint
inventory in `templates/managed-package-installation-and-upgrade-template.md`.

---

## Cross-references

- `devops/managed-package-development` — the publisher side: `postInstallClass`, `uninstallClass`,
  `apiAccessLevel`, and the version upload that produces the `04t` you install.
- `devops/second-generation-managed-packages` — why 2GP installs and uninstalls go through
  `sf package install` / `sf package uninstall` rather than `InstalledPackage`.
- `devops/packaging-dependency-graph` — resolving install order when packages depend on packages.
- `admin/permission-set-group-composition` — wrapping the Permission Set in §5 into a PSG.
