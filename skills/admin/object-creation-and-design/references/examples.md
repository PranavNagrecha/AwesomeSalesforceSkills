# Examples — Object Creation and Design

## Example 1: Creating a "Project Request" Object for Internal Intake

**Context:** A professional services firm needs to track internal project requests submitted by employees. Requests are owned by the submitting employee, reviewed by a project manager, and then either approved or declined. The firm uses Salesforce Enterprise Edition.

**Problem:** The admin creates the object using the default settings, including the default Private OWD. However, project managers (who are not in the record owner's role hierarchy) cannot see any of the submitted requests. They report that the object appears empty.

**Solution:**

1. The admin reviews the business requirement: project managers need to read all requests, but only the submitting employee should edit their own. This maps to **Public Read Only** OWD.
2. Setup → Security → Sharing Settings → Custom Object Defaults → Edit the Project Request object → Set OWD to **Public Read Only**.
3. Project managers can now see all records. The submitter (owner) retains exclusive edit access.

Do not take "they can see them now" from a screenshare. Prove it with `UserRecordAccess`, which "represents a user's access to a set of records" and is read-only (object_reference.txt L303129–303131):

```sql
SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = '005xx000001Sv1AAAS'
  AND RecordId IN ('a01xx000003DGXtAAO', 'a01xx000003DGXuAAO')
```

Run it as an admin, with `UserId` set to the project manager who reported the empty list and `RecordId` set to requests owned by someone else. `HasReadAccess = true` with `MaxAccessLevel` of `Read` is the OWD doing its job; `MaxAccessLevel` is a restricted picklist of `None`, `Read`, `Edit`, `Delete`, `Transfer`, `All` (object_reference.txt L303185–303197), so anything above `Read` means something other than the OWD — a sharing rule, the role hierarchy, or ownership — is also granting access, which is a finding of its own.

Three constraints on the query, from the guide's Usage notes (object_reference.txt L303224–303231): you can only query objects listed on the Sharing Settings Setup page, at most 200 record IDs per query, and the results ignore restriction rules — "if a user's access is blocked even though query results state that they should have access, check to see if a restriction rule on the object prevents the user's access."

If the OWD had been set correctly at object creation, the sharing recalculation would have been minimal (no existing records). Changing it after records exist still triggers a recalculation but is manageable at low volumes.

**Why it works:** Public Read Only OWD grants all internal users read access. Owners and their role hierarchy superiors retain edit access. No sharing rules are needed for the read use case because the OWD already grants it baseline.

---

## Example 2: Creating an "Inspection" Child Object With Auto Number Record Names

**Context:** A field service company adds a custom `Inspection__c` object as a child of the standard `Account` object via a Master-Detail relationship. Each inspection record must have a unique, traceable ID (e.g. `INSP-00042`) that support teams can reference in emails without disclosing the Salesforce record ID.

**Problem:** The admin creates the object with a Text-type Record Name. Technicians in the field enter inconsistent names ("April inspection", "insp 42", blank). Reports and support tickets cannot reliably reference records.

**Solution:**

1. When creating the `Inspection__c` object, the admin selects **Auto Number** for the Record Name type.
2. Display Format: `INSP-{00000}` (produces INSP-00001, INSP-00042, etc.)
3. Starting Number: `1`
4. The OWD is set to **Controlled by Parent** because every inspection must be tied to an Account and access should follow Account access.

As metadata, that is two files. The object:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Field inspection carried out at a customer site. Numbered INSP-nnnnn for use in support correspondence. Access follows the Account.</description>
    <enableActivities>true</enableActivities>
    <enableReports>true</enableReports>
    <enableSearch>true</enableSearch>
    <label>Inspection</label>
    <nameField>
        <displayFormat>INSP-{00000}</displayFormat>
        <label>Inspection Number</label>
        <startingNumber>1</startingNumber>
        <type>AutoNumber</type>
    </nameField>
    <pluralLabel>Inspections</pluralLabel>
    <sharingModel>ControlledByParent</sharingModel>
</CustomObject>
```

And the relationship that forces that sharing model — note `writeRequiresMasterRead`, set to `true` here so a technician with only Read on the Account can still log an inspection:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Account__c</fullName>
    <label>Account</label>
    <referenceTo>Account</referenceTo>
    <relationshipLabel>Inspections</relationshipLabel>
    <relationshipName>Inspections</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <required>true</required>
    <type>MasterDetail</type>
    <writeRequiresMasterRead>true</writeRequiresMasterRead>
</CustomField>
```

`Account` is one of the standard objects that may be the master in a master-detail relationship with a custom object (object_reference.txt L3041–3060). `writeRequiresMasterRead` `true` "allows users with Read access to the primary record permission to create, edit, or delete child records"; the default `false` demands Read/Write on the Account (api_meta.txt L43725–43738). Getting this wrong is the usual cause of "the technician can see the Account but cannot save an inspection". Element-by-element commentary on both files is in `references/metadata-examples.md`.

After save:
- Every new inspection record is automatically assigned a sequential name (INSP-00001, INSP-00002, …).
- Support teams use the Auto Number in emails and case comments.
- No more blank or duplicate names.

**Why it works:** Auto Number Record Names are system-generated at record creation. They are unique, sequential, and cannot be blanked or duplicated by user input. Controlled by Parent OWD ensures that a user who can access the Account automatically accesses its child Inspections — no separate sharing configuration needed.

---

## Anti-Pattern: Enabling All Features "Just in Case"

**What practitioners do:** When creating a new custom object, the admin checks every optional feature checkbox — Activities, Track Field History, Allow Notes, Chatter — reasoning that it is easier to enable now than to come back later.

**What goes wrong:**

1. **Activities and Track Field History cannot be disabled.** Once enabled, even if no activities or history records exist, the checkboxes become read-only. The object permanently carries the overhead of Activity and History framework associations.
2. **Storage cost.** Track Field History stores one row per field change. On a high-volume transactional object (e.g., an order status update object that inserts 500,000 records per year), enabling history on 5 fields generates up to 2.5 million History rows per year. This consumes storage and slows History-related queries.
3. **Performance.** The Chatter feed framework and Activity framework add processing overhead on every record save, even if no one uses those features.

**Correct approach:** Enable only the features that have a confirmed current use case. For Activities: only enable if the object will have logged calls, tasks, or emails. For Track Field History: only enable if there is a compliance or audit reason; configure which fields to track immediately after enabling. For Chatter: only enable if the record page will include a collaboration feed.
