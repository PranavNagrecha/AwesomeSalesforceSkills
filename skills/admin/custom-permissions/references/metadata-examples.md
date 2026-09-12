# Metadata Examples — Custom Permissions

Deployable shapes for `CustomPermission` and the `PermissionSet` that grants it. Element names, field types, limits, and the base skeleton come from the Metadata API Developer Guide (v62 PDF, `CustomPermission` section, `api_meta.txt` L46625–46752) and the Object Reference (`CustomPermission`, `CustomPermissionDependency`, `SetupEntityAccess`). The worked examples extend the guide's own `Acme_Account_Full_Access` sample (L46688–46700) to a realistic feature-flag / bypass pair.

Lint the tree before you deploy:

```bash
python3 skills/admin/custom-permissions/scripts/check_custom_permissions.py --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Custom permission | `CustomPermission` (`<members>Bypass_Validation_Rules</members>` or `*`) | `customPermissions/Bypass_Validation_Rules.customPermission-meta.xml` | 31.0+ (`api_meta.txt` L46635) |
| Permission set that grants it | `PermissionSet` | `permissionsets/Integration_Bypass.permissionset-meta.xml` | `customPermissions` element 31.0+ (`api_meta.txt` L94780) |
| Profile that grants it | `Profile` | `profiles/Integration User.profile-meta.xml` | `customPermissions` element 31.0+ (`api_meta.txt` L97670) |

`CustomPermission` supports the `*` wildcard in package.xml (`api_meta.txt` L46738: "This metadata type supports the wildcard character * (asterisk) in the package.xml manifest file"). `PermissionSet` and `Profile` do not carry the permission's *definition* — only a grant of a permission that must already exist.

The file has no `<fullName>` element in DX source format: `CustomPermission` extends `Metadata` and inherits `fullName` (`api_meta.txt` L46626), which the CLI derives from the filename stem. The stem **is** the API name — rename the file and every `$Permission.X` reference breaks.

## 1. Feature-flag custom permission

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Grants access to the pilot Advanced Refund Workflow on Case. Consumers: RefundController.processRefund (Apex), c-refund-panel (LWC), Case_Refund_Panel visibility. Retire after Winter '27 GA.</description>
    <label>Advanced Refund Workflow</label>
</CustomPermission>
```

## 2. Bypass custom permission (description names the consumer)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Suppresses Account/Case data-quality validation rules for holders. Consumers: Account.Require_Industry_On_Customer, Case.Require_Resolution_On_Close. Held by MuleSoft integration and data-fix sets.</description>
    <label>Bypass Validation Rules</label>
</CustomPermission>
```

File: `customPermissions/Bypass_Validation_Rules.customPermission-meta.xml`.

Naming: `templates/admin/validation-rule-patterns.md` L41 uses the per-domain form `Bypass_Validation_<Domain>` so one integration can be exempted from Account rules without also being exempted from Case rules. Use the per-domain form for anything larger than a single-team org; `Bypass_Validation_Rules` above is the single-gate shape.

## 3. Dependent custom permission (`requiredPermission`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Full refund administration: issue, reverse, and re-issue refunds. Requires Advanced_Refund_Workflow.</description>
    <label>Refund Administration</label>
    <requiredPermission>
        <customPermission>Advanced_Refund_Workflow</customPermission>
        <dependency>true</dependency>
    </requiredPermission>
</CustomPermission>
```

`requiredPermission` is `CustomPermissionDependencyRequired[]` and is available in API version 32.0 and later (`api_meta.txt` L46671). The subtype has exactly two required fields — `customPermission` (the name) and `dependency` (boolean) — and "A required custom permission must be enabled when its parent is enabled" (`api_meta.txt` L46679–46687).

## 4. Licensed custom permission with a connected app

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <connectedApp>Acme_Field_Service</connectedApp>
    <description>Read and edit access for Acme accounts through the Acme Field Service connected app.</description>
    <label>Acme Account Full Access</label>
    <requiredPermission>
        <customPermission>Acme_Account_Read</customPermission>
        <dependency>true</dependency>
    </requiredPermission>
</CustomPermission>
```

`isLicensed` is deliberately absent. The guide marks it **"Required. Read-only."** (`api_meta.txt` L46654–46657) and the guide's own sample definition omits it (L46688–46700); the platform sets it, you do not. It reads `true` when "the appropriate Salesforce license is required before accessing the permission". The queryable counterpart `CustomPermission.IsLicensed` arrived in API 50.0 (`object_reference.txt` L88459–88467).

`connectedApp` is "The name of the connected app that's associated with this permission. Limit: 80 characters" (`api_meta.txt` L46647–46650). UNVERIFIED (2026-09-04): the Metadata API guide does not state what the association *does* at authorization time, and the `CustomPermission` sObject exposes no `ConnectedApplicationId` field to query it back (`object_reference.txt` L88414–88530 lists only Description, DeveloperName, IsLicensed, IsProtected, Language, MasterLabel, NamespacePrefix). Do not claim it blocks OAuth. The grounded mechanism for gating a connected app on permissions is the ConnectedApp `permissionSetName` field, API 46.0+, which requires `isAdminApproved` = `true` on the `ConnectedAppOauthConfig` subtype (`api_meta.txt` L35091–35103).

## 5. The permission set that grants it

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Integration — Validation Bypass</label>
    <description>Grants the validation-rule bypass to the MuleSoft integration user. Assignment is reviewed each release.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <customPermissions>
        <enabled>true</enabled>
        <name>Bypass_Validation_Rules</name>
    </customPermissions>
    <customPermissions>
        <enabled>true</enabled>
        <name>Advanced_Refund_Workflow</name>
    </customPermissions>
</PermissionSet>
```

How to read it:

- `PermissionSetCustomPermissions` has exactly two required fields, `enabled` and `name` (`api_meta.txt` L94943–94952). `name` is the custom permission's API name, never its label.
- "Only enabled custom permissions are retrieved" (same section). A retrieve will therefore never show you a `<customPermissions>` node with `<enabled>false</enabled>` — absence is the only representation of "not granted", so a diff between two orgs cannot distinguish "never granted" from "explicitly revoked".
- One permission may appear in many permission sets and permission set groups; holding any one of them makes it `true` for the user.
- `Profile` accepts the same shape through `ProfileCustomPermissions` (`api_meta.txt` L97670, L97961–97970). See `admin/permission-sets-vs-profiles` for why you should still grant through a permission set.
- Permission set design (naming, grouping, muting, expiration) belongs to `admin/permission-set-architecture` and `templates/admin/permission-set-patterns.md`, not here.

## 6. Consumer snippets — each owned by a sibling skill

Validation rule bypass — the outer `NOT()` is the contract in `templates/admin/validation-rule-patterns.md` L41; the canon lives in `admin/validation-rules`:

```
AND(
  NOT($Permission.Bypass_Validation_Rules),
  ISPICKVAL(Status, "Closed"),
  ISBLANK(Resolution__c)
)
```

Flow formula resource (Return Type: Boolean) — Flow specifics in `admin/flow-for-admins`:

```
$Permission.Bypass_Validation_Rules
```

Apex guard — the Apex-side patterns, tests, and namespace handling belong to `apex/apex-custom-permissions-check`:

```apex
if (!FeatureManagement.checkPermission('Bypass_Validation_Rules')) {
    throw new AuraHandledException('Bypass_Validation_Rules required.');
}
// FeatureManagement.checkPermission(String apiName) returns Boolean
// (apexrefguide.txt L215449-L215466)
```

LWC scoped module — owned by `apex/apex-custom-permissions-check`, which cites the Lightning Web Components Developer Guide (`create-get-permissions`) for the import path and the `true`/`undefined` evaluation rule:

```javascript
import hasBypass from '@salesforce/customPermission/Bypass_Validation_Rules';
// Evaluates to true or undefined — never false. Test truthiness, not === false.
```

FlexiPage / Dynamic Forms component visibility and In-App Guidance — note the extra `CustomPermission.` segment, which the formula syntax above does not have (`api_meta.txt` L67560–67562, L99375–99378, sample at L99472). Owned by `admin/dynamic-forms-and-actions` and `admin/in-app-guidance-and-walkthroughs`:

```xml
<criteria>
    <leftValue>{!$Permission.CustomPermission.Bypass_Validation_Rules}</leftValue>
    <operator>EQUAL</operator>
    <rightValue>TRUE</rightValue>
</criteria>
```

## 7. Description length

`CustomPermission.description` is capped at 255 characters — the Metadata API Developer Guide states it directly in the `CustomPermission` field table: "The custom permission description. Limit: 255 characters" (`api_meta.txt` L46651-46652).

**Where rationale goes instead.** The description is the only place the consumer list survives (Gotcha 9), so it fills up fast — `Bypass_Case_Intake_Validation` in `examples/builds/case-onboarding/artefacts/M2-S01` sits at 250 characters, six from the limit. Once the consumer list itself does not fit, split the permission (Gotcha with the "if the sentence needs an 'and'" test in `## Questions to Ask Before Configuring`) rather than compressing the list into unreadable abbreviations, and keep any narrative rationale — why the bypass exists, who approved it — in the build's `deploy-order.md` or the configuration workbook next to the component it explains.

`scripts/check_custom_permissions.py` enforces this: `CP-DESC-01` (ERROR) at 255+ characters on any `CustomPermission` file; `CP-DESC-02` (INFO) at 200+ characters as headroom — printed and counted, never affects the exit code, even under `--strict`.

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Advanced_Refund_Workflow</members>
        <members>Bypass_Validation_Rules</members>
        <members>Refund_Administration</members>
        <name>CustomPermission</name>
    </types>
    <types>
        <members>Integration_Bypass</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

The guide's own manifest sample lists the `ConnectedApp`, `CustomPermission`, and `PermissionSet` types together (`api_meta.txt` L46703–46733) because a connected-app-associated permission needs all three in one package.

## Retrieve and deploy

```bash
# Pull the org's current definitions and grants into source before editing
sf project retrieve start --metadata "CustomPermission" --target-org my-sandbox
sf project retrieve start --metadata "PermissionSet:Integration_Bypass" --target-org my-sandbox

# Lint, then validate without deploying
python3 skills/admin/custom-permissions/scripts/check_custom_permissions.py --manifest-dir force-app/main/default
sf project deploy validate --source-dir force-app/main/default --target-org my-sandbox

# Deploy definitions before grants and before any consumer that references them
sf project deploy start --source-dir force-app/main/default/customPermissions --target-org my-sandbox
sf project deploy start --source-dir force-app/main/default/permissionsets --target-org my-sandbox
```

Order matters twice. A `PermissionSet` naming a custom permission that does not yet exist fails the deploy, and a `requiredPermission` naming a permission not in the same package fails the same way — put the required permission and its parent in one deployment.

## Verification: who actually holds the permission

`SetupEntityAccess` is the join. `SetupEntityType = 'CustomPermission'` has been a valid value since API 31.0 (`object_reference.txt` L261686), and `ParentId` points at the `PermissionSet` (`object_reference.txt` L261648–261660).

Which permission sets grant one named permission — the Object Reference's own example, retargeted (`object_reference.txt` L88549–88556):

```sql
SELECT Id, DeveloperName,
       (SELECT Id, Parent.Name, Parent.Profile.Name FROM SetupEntityAccessItems)
FROM CustomPermission
WHERE DeveloperName = 'Bypass_Validation_Rules'
```

Which *users* hold it — the two-hop query, adapted from the guide's "all permission sets and profiles with custom permissions" sample (`object_reference.txt` L88557–88568) by narrowing the inner set to one permission:

```sql
SELECT Assignee.Name, Assignee.Username, PermissionSet.Label,
       PermissionSet.Profile.Name, PermissionSet.IsOwnedByProfile
FROM PermissionSetAssignment
WHERE PermissionSetId IN (
    SELECT ParentId FROM SetupEntityAccess
    WHERE SetupEntityType = 'CustomPermission'
      AND SetupEntityId IN (
          SELECT Id FROM CustomPermission WHERE DeveloperName = 'Bypass_Validation_Rules'
      )
)
```

Read `IsOwnedByProfile`: rows where it is `true` are the profile-owned permission set, meaning the grant came from a `Profile`, not from a permission set an admin can see in the Permission Sets list. `object_reference.txt` L88571–88578 shows the inverse filter (`isOwnedByProfile = false`) for listing only real permission sets.

Dependency chain — confirm a `requiredPermission` actually landed:

```sql
SELECT CustomPermission.DeveloperName, RequiredCustomPermission.DeveloperName
FROM CustomPermissionDependency
```

Both objects need setup access to query: `CustomPermission` requires View Setup and Configuration, Manage Session Permission Set Activations, or Assign Permission Sets (`object_reference.txt` L88405–88410); `CustomPermissionDependency` and `SetupEntityAccess` require View Setup and Configuration (`object_reference.txt` L88603, L261635).

Setup check, if you have no query access: **Setup > Custom Permissions >** the permission > **Permission Sets** related list.
