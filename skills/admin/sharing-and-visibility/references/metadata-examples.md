# Metadata Examples: Sharing and Visibility

One worked record-access layer for a custom object `Deal_Room__c`, expressed as deployable metadata: the OWD that sets the baseline, the role that carries the hierarchy, the public group that receives grants, the two sharing rules that broaden, the sharing set that covers Experience Cloud, and the two queries that prove the access exists.

This is the hub view — one deployable example of each layer, in deploy order. For the full `SharingRules` field reference (`accountSettings` cascade, `SharingGuestRule`, the `FilterOperation` enumeration) read `admin/sharing-rules`. For the role hierarchy's own design rules read `admin/role-hierarchy-design`.

---

## 1. OWD — the baseline, on the object file

`sharingModel` is the internal org-wide default; `externalSharingModel` is the one for external users. Both live on the `CustomObject` file, not in a separate settings file.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/Deal_Room__c/Deal_Room__c.object-meta.xml -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Deal room. Private by default; access is granted in layers, never by widening this file.</description>
    <enableActivities>true</enableActivities>
    <enableHistory>true</enableHistory>
    <label>Deal Room</label>
    <nameField>
        <label>Deal Room Name</label>
        <type>Text</type>
    </nameField>
    <pluralLabel>Deal Rooms</pluralLabel>
    <sharingModel>Private</sharingModel>
    <externalSharingModel>Private</externalSharingModel>
</CustomObject>
```

**How to read it**

- `sharingModel` takes a value from the `SharingModel` enumeration: `Private`, `Read`, `ReadWrite`, `ReadWriteTransfer`, `FullAccess`, `ControlledByParent`, `ControlledByCampaign`, `ControlledByLeadOrContact`. The guide narrows it per object: "Accounts, opportunities, and custom objects support `Private`, `Read` and `ReadWrite` values." `Read` is the API name for Public Read Only — there is no `PublicReadOnly` or `PublicReadWriteTransfer` value.
- Using API version 29.0 and earlier `sharingModel` is read-only in the Metadata API. From API version 30.0 you can set it for internal users through the API; `externalSharingModel` arrived in API version 31.0.
- `ControlledByParent` is what a master-detail child gets. The Object Reference is explicit about the consequence: "Custom objects on the detail side of a master-detail relationship can't have sharing rules, manual sharing, or queues, because these elements require the Owner field," and "The detail record inherits the sharing and security settings of its master record." A `Deal_Room__Share` object exists only because this object is *not* a master-detail child — "A sharing rule object is created for each custom object that doesn't have a master-detail relationship to another object."
- Deploy the OWD first. Every layer below assumes it. Once the OWD is `Read` or wider, a `Read` grant on the same object is no longer more permissive than the default — see "A Grant At Or Below the OWD Adds Nothing" in `references/gotchas.md`.
- UNVERIFIED (2026-09-04): the guides state the more-permissive-than-OWD requirement only for share rows written by Apex managed sharing (Apex Developer Guide: "Access level must be more permissive than the object's default"). The extension to declaratively created rules and manual shares is consistent with that and with the Setup UI, but no source in the v62 PDFs states it for sharing rules. Confirm in a scratch org before promising it to a stakeholder.
- UNVERIFIED (2026-09-04): `externalSharingModel` is widely held not to be settable more permissively than `sharingModel`. The Metadata API guide documents both fields but states no such constraint, so `scripts/check_sharing_model.py` reports the combination for review rather than calling it invalid.

---

## 2. Role — the hierarchy layer

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/roles/Deal_Desk_Manager.role-meta.xml -->
<Role xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Deal Desk Manager</name>
    <description>Manages the deal desk. Sits under Sales Operations Director.</description>
    <parentRole>Sales_Operations_Director</parentRole>
    <caseAccessLevel>None</caseAccessLevel>
    <contactAccessLevel>Read</contactAccessLevel>
    <opportunityAccessLevel>Read</opportunityAccessLevel>
    <mayForecastManagerShare>false</mayForecastManagerShare>
</Role>
```

**How to read it**

- `name` is required and is the UI label; `fullName` is the file name (`Deal_Desk_Manager`) and is the API identifier — it "must be unique, begin with a letter, not include spaces, not end with an underscore, and not contain two consecutive underscores."
- `parentRole` is "the role above this role in the hierarchy." The file carries its own parent, so the hierarchy's shape is distributed across every role file and no single file shows it. A role with no `parentRole` is a root. UNVERIFIED (2026-09-04): the guide does not document deployment ordering for `Role`; deploying parents and children in one package is the safe default, not a documented requirement.
- `caseAccessLevel`, `contactAccessLevel`, and `opportunityAccessLevel` (`Read` / `Edit` / `None`) do not control this role's own records. They specify "whether a user can access **other users'** cases / contacts / opportunities that are associated with accounts the user owns." Each is hidden in the UI when the matching object's sharing model is already Public Read/Write (and `contactAccessLevel` also when Contact is Controlled by Parent), and "If no value is set for this field, this field value uses the default access level that is specified in the Manage Territory page in Setup" — so omitting them is not the same as setting `None`.

---

## 3. Public group — the recipient

Grant to a group, not to a role, so the grant survives a reorg.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/groups/Deal_Desk_Reviewers.group-meta.xml -->
<Group xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Deal_Desk_Reviewers</fullName>
    <name>Deal Desk Reviewers</name>
    <description>Receives deal-room grants. Membership is managed in the target org, not in this file.</description>
    <doesIncludeBosses>false</doesIncludeBosses>
</Group>
```

**How to read it**

- `doesIncludeBosses` is required and "indicates whether records shared with users in this group are also shared with users higher in the role hierarchy (true) or not (false). This field corresponds to the **Grant Access Using Hierarchies** checkbox on the group's detail page." It is set per group, and it silently widens every grant that group ever receives. The same field exists on `Queue` from API version 67.0.
- The guide carries a note that changes how you deploy this file: "Members of the public group aren't migrated when you deploy the group type." The group arrives empty. Every sharing rule pointing at it deploys green and grants nothing until membership exists in the target org.

---

## 4. Sharing rules — one owner-based, one criteria-based

All rules for one object live in one file. Retrieve the object's existing file and add to it; a retrieved file already carries the element order the API validates against.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/sharingRules/Deal_Room__c.sharingRules-meta.xml -->
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <sharingOwnerRules>
        <fullName>Deal_Desk_Owned_To_Legal</fullName>
        <accessLevel>Read</accessLevel>
        <description>Legal reads every deal room owned by the deal desk branch.</description>
        <label>Deal Desk Owned to Legal</label>
        <sharedFrom>
            <roleAndSubordinatesInternal>Deal_Desk_Manager</roleAndSubordinatesInternal>
        </sharedFrom>
        <sharedTo>
            <group>Legal_Deal_Reviewers</group>
        </sharedTo>
    </sharingOwnerRules>
    <sharingCriteriaRules>
        <fullName>High_Value_Rooms_To_Deal_Desk</fullName>
        <accessLevel>Edit</accessLevel>
        <description>Deal desk edits every open room over the review threshold.</description>
        <label>High Value Rooms to Deal Desk</label>
        <booleanFilter>1 AND 2</booleanFilter>
        <criteriaItems>
            <field>Stage__c</field>
            <operation>notEqual</operation>
            <value>Closed</value>
        </criteriaItems>
        <criteriaItems>
            <field>Contract_Value__c</field>
            <operation>greaterThan</operation>
            <value>500000</value>
        </criteriaItems>
        <includeRecordsOwnedByAll>true</includeRecordsOwnedByAll>
        <sharedTo>
            <group>Deal_Desk_Reviewers</group>
        </sharedTo>
    </sharingCriteriaRules>
</SharingRules>
```

**How to read it**

- Both rule types extend `SharingBaseRule`, whose required fields are `accessLevel`, `label`, and `sharedTo`; `description` is optional with a maximum of 1,000 characters. `accountSettings` (the cascade to case, contact, and opportunity) applies to Account rules only and is absent here.
- `sharedFrom` is required on `SharingOwnerRule` and "specifies the record owners." A criteria rule has no `sharedFrom` — it matches on field values, not on ownership.
- `includeRecordsOwnedByAll` is **required** on every criteria rule: it "indicates whether records owned by users who can't have an assigned role are included in the records shared (`true`) or not (`false`). Examples of users who can't have an assigned role are high-volume users and system users such as automated process users." The guide adds "You can't edit this field after the sharing rule is created," so getting it wrong means deleting and recreating the rule. Set it `true` whenever an integration user or automated process user can own the record.
- `sharedTo` and `sharedFrom` are both the `SharedTo` type. Its documented elements are `group`, `role`, `roleAndSubordinates`, `roleAndSubordinatesInternal`, `roles`, `rolesAndSubordinates`, `groups`, `queue`, `territory`, `territoryAndSubordinates`, `territories`, `territoriesAndSubordinates`, `managers`, `managerSubordinates`, `portalRole`, `portalRoleandSubordinates`, `channelProgramGroup`, `channelProgramGroups`, `guestUser`, `allInternalUsers`, `allCustomerPortalUsers`, `allPartnerUsers`. **There is no `user` element.** A sharing rule cannot target one named individual; that is what manual sharing and Apex managed sharing are for. `groups`, `roles`, `rolesAndSubordinates`, `territories`, and `territoriesAndSubordinates` are the pre-22.0 spellings — use the singular forms.
- `queue` "applies only to lead, case, and CustomObject sharing rules," and `guestUser` "can be used only with `SharingGuestRule`."
- `accessLevel` on a rule is `Read` or `Edit` in practice. The share row's third value, `All`, is documented on `AccountShare` as "This value isn't valid for create or update calls."

---

## 5. Sharing set — the Experience Cloud layer

External users do not inherit through the role hierarchy. A sharing set "defines an access mapping that grants portal or community users access to objects that are associated with their accounts or contacts."

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/sharingSets/Partner_Deal_Rooms.sharingSet-meta.xml -->
<SharingSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Partner_Deal_Rooms</name>
    <description>Partner users read the deal rooms hanging off their own account.</description>
    <profiles>Partner Community User</profiles>
    <accessMappings>
        <accessLevel>Read</accessLevel>
        <objectField>Account__c</objectField>
        <object>Deal_Room__c</object>
        <userField>Account</userField>
    </accessMappings>
</SharingSet>
```

**How to read it**

- `name` is required and "corresponds to Sharing Set Name on the user interface"; `description` is limited to 255 characters.
- `profiles` names "the profiles of users that are granted access to the target objects. Profiles must be associated with a license that can use sharing sets" — the guide lists Authenticated Website, Customer Community Login, Customer Community Plus, Partner Community, Customer Community User, High Volume Customer Portal, High Volume Portal, Overage Authenticated Website User, and Overage High Volume Customer Portal User.
- Inside `accessMappings`: `objectField` is "a lookup to the target object" on the record side, `userField` is "the user's lookup to an account, contact, or a standard or custom field derived from an account or contact" (valid values `Account`, `Account.Field`, `Contact`, `Contact.Field`, `Contact.RelatedAccount`, `Manager.Account`, `Manager.Contact`), and `accessLevel` is `Read` or `Edit` only.
- Creating or updating a sharing set needs the Customize Application permission on top of Manage Sharing.
- A sharing set grant is **not** a share row you can query — see step 7.

---

## 6. package.xml, retrieve, and deploy

`SharingRules` itself does not support the wildcard and is not what you address. Manifest the concrete rule types: `SharingCriteriaRule` and `SharingOwnerRule`, with members shaped `Object.RuleName`, `Object.*`, or `*`. `CustomObject`, `Role`, `Group`, and `SharingSet` all support the wildcard.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Deal_Room__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Deal_Desk_Manager</members>
        <name>Role</name>
    </types>
    <types>
        <members>Deal_Desk_Reviewers</members>
        <members>Legal_Deal_Reviewers</members>
        <name>Group</name>
    </types>
    <types>
        <members>Deal_Room__c.High_Value_Rooms_To_Deal_Desk</members>
        <name>SharingCriteriaRule</name>
    </types>
    <types>
        <members>Deal_Room__c.Deal_Desk_Owned_To_Legal</members>
        <name>SharingOwnerRule</name>
    </types>
    <types>
        <members>Partner_Deal_Rooms</members>
        <name>SharingSet</name>
    </types>
    <version>62.0</version>
</Package>
```

Retrieve the current state before editing anything — hand-authored sharing metadata is the usual source of deploy failures:

```bash
# Pull the whole record-access layer for one object
sf project retrieve start \
  --metadata "CustomObject:Deal_Room__c" \
  --metadata "SharingOwnerRule:Deal_Room__c.*" \
  --metadata "SharingCriteriaRule:Deal_Room__c.*" \
  --metadata "Role" \
  --metadata "Group" \
  --target-org myDevOrg

# Check the shapes before you send them
python3 skills/admin/sharing-and-visibility/scripts/check_sharing_model.py \
  --manifest-dir force-app/main/default

# Validate, then deploy
sf project deploy start --manifest manifest/package.xml --dry-run --target-org myUatOrg
sf project deploy start --manifest manifest/package.xml --target-org myUatOrg
```

Deploy order matters: OWD and roles first, then groups, then the rules that reference them. A rule whose group exists but is empty deploys green and grants nothing — that half is documented (see step 3). UNVERIFIED (2026-09-04): the guide does not state what happens when a rule's `sharedTo` group is absent from the target org; treat a missing referent as a likely deployment failure and ship the group in the same package rather than testing the assumption in production.

---

## 7. Verification — prove the access, do not assume it

**Step 1 — ask the platform what one user can do with one record.** `UserRecordAccess` "represents a user's access to a set of records," is read-only, and is available from API version 24.0.

```soql
SELECT RecordId, HasReadAccess, HasEditAccess, HasDeleteAccess, HasTransferAccess, MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = '005XX0000012ABC'
  AND RecordId = 'a01XX000003GHIj'
```

`MaxAccessLevel` returns `None`, `Read`, `Edit`, `Delete`, `Transfer`, or `All`. Four constraints from the Object Reference decide whether your query is even legal:

- "You can only query records of objects listed on the Sharing Settings Setup page."
- "Up to 200 record IDs can be queried."
- "When filtering by `UserId` and `RecordId` only, you must use `SELECT RecordId` and optionally one or more of the access level fields" plus `MaxAccessLevel` — as above.
- "When filtering by `UserId`, `RecordId`, **and** an access level field, you must use `SELECT RecordId` only." So this is the legal shape of a filtered query:

```soql
SELECT RecordId
FROM UserRecordAccess
WHERE UserId = '005XX0000012ABC'
  AND RecordId IN ('a01XX000003GHIj', 'a01XX000003GHIk')
  AND HasEditAccess = true
```

From API version 30.0 `UserRecordAccess` is also a foreign key on the record itself, evaluated for the running user, which is the form to use inside a Lightning page or a report-shaped query:

```soql
SELECT Id, Name, UserRecordAccess.HasEditAccess, UserRecordAccess.MaxAccessLevel
FROM Deal_Room__c
```

**Step 2 — find out *why* the access exists.** Query the share table. `RowCause` names the mechanism.

```soql
-- Custom object: the share table is <Object>__Share, ParentId + AccessLevel
SELECT Id, ParentId, UserOrGroupId, AccessLevel, RowCause
FROM Deal_Room__Share
WHERE ParentId = 'a01XX000003GHIj'

-- Standard object: the columns are object-named
SELECT Id, AccountId, UserOrGroupId, AccountAccessLevel, OpportunityAccessLevel, RowCause
FROM AccountShare
WHERE AccountId = '001XX000003DHPh'
```

`RowCause` is a restricted picklist. The documented values include `Owner`, `Manual`, `Rule` (Sharing Rule), `Team`, `ImplicitChild`, `ImplicitParent`, `ImplicitPerson`, `GuestRule`, `GuestParentImplicit`, `GuestPersonImplicit`, `Territory`, `TerritoryRule`, `TerritoryManual`, `Territory2AssociationManual`, `Territory2Forecast`, `CompliantDataSharing`, and `SharingRecordCollection`. On the rule you just deployed, expect `Rule`.

Two limits on this evidence, both from the Object Reference and both easy to mistake for a bug:

- "You can only create, edit, and delete sharing entries for standard objects whose `RowCause` field is set to `Manual`." Everything else is read-only. Deleting a `Rule` row is not how you revoke a rule.
- "For some sharing mechanisms, such as sharing sets, sharing entries aren't stored at all," and after faster account sharing recalculation is enabled, `ImplicitChild` rows "aren't returned when you query this object." An empty share table therefore does not prove no access. Step 1 is the authority; step 2 only explains it.

**Step 3 — Setup check.** Setup → Security → Sharing Settings shows the deployed OWD and the rule list for `Deal_Room__c`, and is where a recalculation still in progress is visible. Confirm `Deal Room` reads *Private / Private* and that both rules appear before you tell anyone the change has landed.

---

## Sources

- Metadata API Developer Guide (v62 PDF) — `CustomObject` (`sharingModel`, `externalSharingModel`), `SharingModel` enumeration, `SharingRules` / `SharingBaseRule` / `SharingCriteriaRule` / `SharingOwnerRule`, `SharedTo`, `Role` / `RoleOrTerritory`, `Group`, `Queue`, `SharingSet` / `AccessMapping`, "Sample package.xml Manifest Files → Sharing Rules": https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform (v62 PDF) — `UserRecordAccess`, `AccountShare`, `CaseShare` usage note, "Sharing and Custom Objects", master-detail relationship behaviour: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
