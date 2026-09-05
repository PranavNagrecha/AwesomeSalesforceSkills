# Metadata Examples — User Access Policies

Deployable shapes for `UserAccessPolicy`. Element names, enum values, and the skeleton come from the Metadata API Developer Guide (v62 PDF, `UserAccessPolicy` section, including its two sample definitions and sample package.xml); the worked example below extends those samples to a realistic multi-action policy. Validate before deploying:

```bash
python3 skills/admin/user-access-policies/scripts/check_user_access_policies.py --manifest-dir force-app/main/default
```

## Where the files live

| Item | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| A user access policy | `UserAccessPolicy` (`*` wildcard supported) | `useraccesspolicies/Sales_Rep_Onboarding.useraccesspolicy-meta.xml` | 57.0+ |
| The org-level feature flag | `Settings` (`<members>UserManagement</members>`) | `settings/UserManagement.settings-meta.xml` | 58.0+ |

The suffix is `.useraccesspolicy` and the folder is `useraccesspolicies` (Metadata API guide, `UserAccessPolicy` → File Suffix and Directory Location). In a `sf` DX project the retrieved file carries the usual `-meta.xml` tail.

## A policy with OR filter logic and four actions

```xml
<?xml version="1.0" encoding="UTF-8"?>
<UserAccessPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Sales Rep Onboarding</masterLabel>
    <description>Grants the Sales Rep seat to active users on either sales profile, and clears the old inside-sales group.</description>
    <booleanFilter>(1 OR 2) AND 3</booleanFilter>
    <order>10</order>
    <status>Design</status>
    <triggerType>CreateAndUpdate</triggerType>

    <!-- Filter 1: a named profile -->
    <userAccessPolicyFilters>
        <operation>equals</operation>
        <sortOrder>1</sortOrder>
        <target>SalesRepCustomProfile</target>
        <type>Profile</type>
    </userAccessPolicyFilters>

    <!-- Filter 2: two roles in ONE row, via the in operator (v58.0+) -->
    <userAccessPolicyFilters>
        <operation>in</operation>
        <sortOrder>2</sortOrder>
        <target>SalesOps,InsideSalesRep</target>
        <type>UserRole</type>
    </userAccessPolicyFilters>

    <!-- Filter 3: a raw User field. target is literally "User". -->
    <userAccessPolicyFilters>
        <columnName>IsActive</columnName>
        <operation>equals</operation>
        <sortOrder>3</sortOrder>
        <target>User</target>
        <type>User</type>
        <value>true</value>
    </userAccessPolicyFilters>

    <!-- Grant a permission set group -->
    <userAccessPolicyActions>
        <action>Grant</action>
        <target>SalesRepPSG</target>
        <type>PermissionSetGroup</type>
    </userAccessPolicyActions>

    <!-- Grant a permission set licence the group's contents depend on -->
    <userAccessPolicyActions>
        <action>Grant</action>
        <target>SalesConsoleUser</target>
        <type>PermissionSetLicense</type>
    </userAccessPolicyActions>

    <!-- Add the user to a public group -->
    <userAccessPolicyActions>
        <action>Grant</action>
        <target>AMERSalesPublicGroup</target>
        <type>Group</type>
    </userAccessPolicyActions>

    <!-- Revoke, in the SAME policy, on the same event -->
    <userAccessPolicyActions>
        <action>Revoke</action>
        <target>InsideSales_Legacy_PS</target>
        <type>PermissionSet</type>
    </userAccessPolicyActions>
</UserAccessPolicy>
```

How to read it:

- `booleanFilter` is **required** and numbers the filter rows by their `sortOrder`. The guide's own wording is that it "can be `1 AND 2` or `1 OR 2`" — OR is supported. A single-row policy still needs `<booleanFilter>1</booleanFilter>`.
- Filter 2 shows the *other* way to express alternatives: `operation` `in` with comma-separated developer names in `target`, "to reference multiple profiles or roles in the same user criteria filter". Available in API version 58.0 and later.
- Filter 3 shows the `User` shape: when `type` is `User`, set `target` to the string `User`, name the field in `columnName`, and put the compared value in `value`. `columnName` and `value` are ignored for every other `type`.
- `action` is `Grant` or `Revoke` per action element — they are not policy types. One policy can do both, and both run when that policy is the winner.
- `type` on an action is one of `Group`, `PackageLicense`, `PermissionSet`, `PermissionSetGroup`, `PermissionSetLicense`, `Queue`. On a filter it is one of those six plus `Profile`, `User`, `UserRole`.
- `order` is an integer 0–10,000 (v61.0+), required only when `status` is `Active`. When a user matches several active policies, only the one with the lowest `order` is applied.
- `status` is deployed as `Design` here on purpose: deploying `Active` is downgraded — "If you deploy a policy with a status of Active, the status is changed to Design."
- `triggerType` is `Create`, `Update`, or `CreateAndUpdate`. `CreateAndUpdate` is what makes the revoke fire on a transfer rather than only at hire.

## A second, narrower policy — and why `order` decides between them

```xml
<?xml version="1.0" encoding="UTF-8"?>
<UserAccessPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Sales Rep Onboarding EMEA</masterLabel>
    <description>EMEA reps get the regional group instead of the AMER one.</description>
    <booleanFilter>1 AND 2</booleanFilter>
    <order>5</order>
    <status>Design</status>
    <triggerType>CreateAndUpdate</triggerType>
    <userAccessPolicyFilters>
        <operation>equals</operation>
        <sortOrder>1</sortOrder>
        <target>SalesRepCustomProfile</target>
        <type>Profile</type>
    </userAccessPolicyFilters>
    <userAccessPolicyFilters>
        <columnName>Country</columnName>
        <operation>in</operation>
        <sortOrder>2</sortOrder>
        <target>User</target>
        <type>User</type>
        <value>Germany,France,United Kingdom</value>
    </userAccessPolicyFilters>
    <userAccessPolicyActions>
        <action>Grant</action>
        <target>SalesRepPSG</target>
        <type>PermissionSetGroup</type>
    </userAccessPolicyActions>
    <userAccessPolicyActions>
        <action>Grant</action>
        <target>EMEASalesPublicGroup</target>
        <type>Group</type>
    </userAccessPolicyActions>
</UserAccessPolicy>
```

A German sales rep matches both policies. Because `order` 5 beats `order` 10, **only** the EMEA policy runs — the AMER policy's licence grant and its revoke never execute for that user. If the licence grant is needed for everyone, it has to be repeated in every policy that could win, or moved to a policy no other policy outranks for that population.

## Turning the feature on

```xml
<?xml version="1.0" encoding="UTF-8"?>
<UserManagementSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <userAccessPoliciesEnabled>true</userAccessPoliciesEnabled>
    <enableEnhcUiUserAccessPolicies>true</enableEnhcUiUserAccessPolicies>
</UserManagementSettings>
```

`userAccessPoliciesEnabled` (v58.0+) is the master switch. `enableEnhcUiUserAccessPolicies` (v60.0+) selects the improved authoring UI; the guide notes it "is automatically set to true" once user access policies are enabled, "but you can change it to false", and that it has no effect while the feature is off.

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>UserManagement</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Sales_Rep_Onboarding</members>
        <members>Sales_Rep_Onboarding_EMEA</members>
        <name>UserAccessPolicy</name>
    </types>
    <version>61.0</version>
</Package>
```

`UserAccessPolicy` supports the `*` wildcard in the manifest, so `<members>*</members>` retrieves every policy — useful for taking a baseline of an org you did not build. Use `61.0` or later if the policies carry an `order`.

## Retrieve and deploy

```bash
# Baseline every policy in the org before changing anything
sf project retrieve start --metadata "UserAccessPolicy" --target-org prod-ro

# Retrieve one named policy plus the settings
sf project retrieve start \
  --metadata "UserAccessPolicy:Sales_Rep_Onboarding" \
  --metadata "Settings:UserManagement" \
  --target-org sandbox

# Validate-only against production first
sf project deploy validate --manifest manifest/package.xml --target-org prod

# Deploy
sf project deploy start --manifest manifest/package.xml --target-org prod
```

**Deploy order.** Within one release, in this sequence:

1. `Settings:UserManagement` with `userAccessPoliciesEnabled` — until it is on, the UAP-gated fields on `PermissionSetAssignment` do not exist and the verification queries below will not compile.
2. The access mechanisms every action's `target` names: permission sets, permission set groups, permission set licence assignments' prerequisites, public groups, queues. `target` is resolved at deploy time, so a missing one fails the deployment.
3. The `UserAccessPolicy` files.
4. **Manual, in Setup:** set each policy's status to `Active`. This cannot be done by the deployment — a policy deployed as `Active` lands as `Design`.
5. Deactivate any Apex trigger that wrote the same assignments, in the same release.

## Verify

Config as it actually landed — note that `Status` will read `Design` until someone activates it, and that `Order` is the tiebreak you are checking:

```sql
SELECT DeveloperName, MasterLabel, Status, Order, TriggerType, BooleanFilter
FROM UserAccessPolicy
ORDER BY Order NULLS LAST
```

`UserAccessPolicy` supports only `describeSObjects()`, `query()`, and `retrieve()` — there is no create, update, or delete over the API, so this query is a read of deployed state, not a way to fix it. Reading it requires **Manage User Access Policies**.

What the policy actually did to a specific user — this is the audit trail, and it only exists when the feature is enabled:

```sql
SELECT Id, AssigneeId, PermissionSetId, PermissionSetGroupId, IsRevoked,
       LastCreatedByChangeId, LastCreatedByChange.Source,
       LastDeletedByChangeId, LastDeletedByChange.Source
FROM PermissionSetAssignment
WHERE AssigneeId = '005xx000001Sv1AAAS'
```

`LastCreatedByChange.Source` records where the change came from — the Object Reference gives `UserAccessPolicyId` as its example value. A row whose `Source` is empty was written by a person or by Apex, not by a policy. `IsRevoked` distinguishes a UAP revocation from a deleted assignment.

The change records themselves are queryable directly, and reading them needs **View Setup and Configuration**:

```sql
SELECT Id, Source FROM UserAccessChange
```

`UserAccessChange` supports `describeSObjects()`, `getDeleted()`, `getUpdated()`, `query()`, and `retrieve()` — no create, update, or delete. Only `Source` is documented in the Object Reference field table; describe the object in the target org before relying on any other field.

Setup check: **Setup → User Access Policies** shows each policy's status and order, and is the only place the `Design` → `Active` transition can be made.
