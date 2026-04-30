# Examples — Dynamic Forms Migration

## Example 1: Pre-Migration Inventory

```sql
-- Page Layouts and assignments per object (Tooling API)
SELECT Id, Name, EntityDefinition.QualifiedApiName
FROM Layout
WHERE EntityDefinition.QualifiedApiName = 'Account'

-- Layout assignments per profile and record type (Tooling API)
SELECT Layout.Name, Profile.Name, RecordTypeId
FROM ProfileLayout
WHERE Layout.EntityDefinition.QualifiedApiName = 'Account'
```

```bash
# Lightning Record Pages assigned to the object
sf data query --query "SELECT Id, MasterLabel, Type FROM FlexiPage WHERE EntityDefinitionId = '01I...AccountId'"
```

---

## Example 2: Custom Permission Pattern for Field Visibility

**Scenario:** Hide commission-related fields from regular Sales Reps; show to Sales Managers.

**Step 1 — Define a Custom Permission:**

```xml
<!-- force-app/main/default/customPermissions/View_Commission_Fields.customPermission-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <isLicensed>false</isLicensed>
    <label>View Commission Fields</label>
    <description>Allows the user to see commission-related fields on Opportunities and Accounts.</description>
</CustomPermission>
```

**Step 2 — Assign via Permission Set (typically to the "Sales Manager" permission set):**

```xml
<!-- force-app/main/default/permissionsets/Sales_Manager.permissionset-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Sales Manager</label>
    <customPermissions>
        <enabled>true</enabled>
        <name>View_Commission_Fields</name>
    </customPermissions>
</PermissionSet>
```

**Step 3 — Use in Dynamic Forms component visibility:**

In App Builder, on each commission-related Field component:

```
Set Component Visibility:
    Filter: $Permission.View_Commission_Fields equals true
```

**Why:** Stable identifier — renaming a profile doesn't break the rule. Permission Set assignments can be granted via Permission Set Groups for cleaner role-based access.

---

## Example 3: Record-Type-Driven Field Visibility

**Scenario:** Account record types `Customer`, `Partner`, and `Prospect`. Each has unique fields.

**Per-component visibility rules (configured in App Builder):**

| Field component | Visibility rule |
|---|---|
| `Customer_Tier__c` | `RecordType.DeveloperName equals 'Customer'` |
| `Partner_Discount_Level__c` | `RecordType.DeveloperName equals 'Partner'` |
| `Lead_Source__c` (only relevant for Prospects) | `RecordType.DeveloperName equals 'Prospect'` |
| `Account_Manager__c` (Customers and Partners only) | `RecordType.DeveloperName equals 'Customer' OR RecordType.DeveloperName equals 'Partner'` |
| `Industry` (all record types) | (no visibility rule — always shown) |

**Verification:**

```apex
// In a sandbox, switch the Account's RecordType and reload the page
Account a = [SELECT Id, RecordTypeId FROM Account WHERE Id = '001...' LIMIT 1];
a.RecordTypeId = [SELECT Id FROM RecordType WHERE DeveloperName = 'Partner' LIMIT 1].Id;
update a;
// Reload the record page; verify Partner_Discount_Level__c is visible
```

---

## Example 4: Field-Level Security Audit Pre-Migration

```apex
// Per-profile FLS report for an object
public with sharing class FlsAudit {
    public static void reportForAccount() {
        Map<String, Schema.SObjectField> fields = Schema.getGlobalDescribe().get('Account').getDescribe().fields.getMap();
        Map<String, Profile> profilesById = new Map<String, Profile>(
            [SELECT Id, Name FROM Profile WHERE UserType = 'Standard']
        );
        for (Profile p : profilesById.values()) {
            System.debug('=== Profile: ' + p.Name + ' ===');
            for (String fieldName : fields.keySet()) {
                Schema.DescribeFieldResult dfr = fields.get(fieldName).getDescribe();
                // FLS check via PermissionSetAssignment + ObjectPermissions / FieldPermissions queries
                // (Profile-level FLS via FieldPermissions WHERE ParentId = ProfilePermissionSetId)
                System.debug(fieldName + ' read=' + dfr.isAccessible() + ' edit=' + dfr.isUpdateable());
            }
        }
    }
}
```

The audit's purpose is to confirm "what FLS says" matches "what users actually need." Fix discrepancies BEFORE adding Dynamic Forms visibility rules. Otherwise, you have two layers of access controls and debugging "why can't user X see field Y" requires checking both.

---

## Example 5: User Impersonation Test Plan

```text
For each Profile:
    For each Record Type the Profile can access:
        - Login as a representative user from that Profile
        - Open a Record of that Record Type
        - Verify the visible field list matches the expected (per visibility rules)
        - Verify any user-attribute-based rules (e.g., $User.Department) work as expected
        - Test inline edit: change a field that triggers a visibility rule; confirm correct re-render
        - Test record type change (if user has the perm): verify visibility re-evaluates after page reload

Profiles to test for an Account migration:
    - Sales Rep (Customer record type only)
    - Sales Manager (all record types; sees commission fields)
    - Service Agent (Customer record type only; no commission fields)
    - System Admin (all record types; all fields)

Record Types: Customer, Partner, Prospect
```

---

## Example 6: Migrating to Dynamic Forms via Metadata API (declarative path is preferred)

The preferred migration mechanism is via the App Builder UI ("Upgrade Now"). Metadata-API direct edit of `FlexiPage` XML is possible but error-prone. If needed:

```xml
<!-- force-app/main/default/flexipages/Account_Record_Page.flexipage-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
    <flexiPageRegions>
        <itemInstances>
            <fieldInstance>
                <fieldItem>Record.Industry</fieldItem>
                <isRequired>false</isRequired>
                <uiBehavior>Edit</uiBehavior>
            </fieldInstance>
        </itemInstances>
        <itemInstances>
            <fieldInstance>
                <fieldItem>Record.Customer_Tier__c</fieldItem>
                <isRequired>false</isRequired>
                <uiBehavior>Edit</uiBehavior>
                <visibilityRule>
                    <criteria>
                        <leftValue>{!Record.RecordType.DeveloperName}</leftValue>
                        <operator>EQUAL</operator>
                        <rightValue>Customer</rightValue>
                    </criteria>
                </visibilityRule>
            </fieldInstance>
        </itemInstances>
        <name>Main</name>
        <type>Region</type>
    </flexiPageRegions>
    <masterLabel>Account Record Page</masterLabel>
    <sobjectType>Account</sobjectType>
    <type>RecordPage</type>
</FlexiPage>
```

**Why prefer the UI:** App Builder generates correct XML on "Upgrade Now"; direct XML editing risks malformed visibility-rule structures that fail validation at deploy time without clear errors.

---

## Example 7: Decommissioning Old Page Layouts (Selectively)

**Decision matrix:**

| Layout still required for | Action |
|---|---|
| Salesforce Classic users | KEEP — Classic doesn't see Lightning Record Pages |
| Quick Action input fields | KEEP — Quick Actions reference the Page Layout's Quick Action section |
| Print View | KEEP — Print View renders from the Page Layout |
| All of the above are not in use | RETIRE — set the layout assignment to a minimal "default" layout; eventually delete |

**Result for most orgs:** retain at least one minimal Page Layout per object permanently. Set its content to just the standard fields. Reduce to one layout per object (instead of one per record type). Don't try to "delete all Page Layouts" — Salesforce requires at least one per record type.

```sql
-- Verify which layouts are still assigned
SELECT Layout.Name, Profile.Name, RecordTypeId, COUNT(Id)
FROM ProfileLayout
WHERE Layout.EntityDefinition.QualifiedApiName = 'Account'
GROUP BY Layout.Name, Profile.Name, RecordTypeId
```
