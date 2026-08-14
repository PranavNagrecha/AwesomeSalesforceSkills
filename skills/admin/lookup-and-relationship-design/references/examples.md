# Examples — Lookup and Relationship Design

## Example 1: Lookup with `Restrict` Delete Instead of a Master-Detail

**Scenario:** Assets hang off Accounts. Finance wants deletion of an Account with open Assets blocked, but Asset records must keep their own owner so the service team can be assigned individual Assets through a queue.

**Problem:** The reflex answer — "make it master-detail so the delete cascades" — takes the Owner field off Asset. Detail-side objects "can't have sharing rules, manual sharing, or queues, because these elements require the Owner field," so the service team's queue-based assignment stops working the day the relationship is deployed.

**Solution:** Keep it a Lookup and set the delete constraint explicitly. `deleteConstraint` is a `CustomField` property, so it lives in source control and survives org-to-org deploys:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Owning_Account__c</fullName>
    <label>Owning Account</label>
    <type>Lookup</type>
    <referenceTo>Account</referenceTo>
    <relationshipName>Owned_Assets</relationshipName>
    <relationshipLabel>Owned Assets</relationshipLabel>
    <!-- SetNull is the platform default and silently blanks this field
         when the Account is deleted. Restrict blocks the parent delete. -->
    <deleteConstraint>Restrict</deleteConstraint>
    <required>true</required>
    <trackHistory>true</trackHistory>
</CustomField>
```

**Why it works:** `Restrict` gives the business the guarantee it actually asked for (no orphaned Assets, no silent data loss) while the Owner field stays on Asset, so queues, manual sharing, and owner-based sharing rules all remain available. `required` is what enforces "an Asset must have an Account" — that requirement was never a reason to reach for master-detail.

---

## Example 2: Junction Object with an Explicit Primary Parent

**Scenario:** A `Course_Registration__c` junction ties `Student__c` to `Course_Offering__c`. Registrations should be visible to whoever owns the student record, not whoever owns the course.

**Problem:** Both master-detail fields look identical in Object Manager. Whichever one is created first becomes primary, and the primary parent is what sets the junction record's owner. Create them in the wrong order — or retrieve and redeploy from an org where the order differs — and every registration is owned by the course's owner instead.

**Solution:** Pin `relationshipOrder` on both fields in the retrieved metadata:

```xml
<!-- Course_Registration__c.Student__c -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Student__c</fullName>
    <label>Student</label>
    <type>MasterDetail</type>
    <referenceTo>Student__c</referenceTo>
    <relationshipName>Registrations</relationshipName>
    <!-- 0 = primary. This parent supplies the junction record's owner. -->
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
</CustomField>
```

```xml
<!-- Course_Registration__c.Course_Offering__c -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Course_Offering__c</fullName>
    <label>Course Offering</label>
    <type>MasterDetail</type>
    <referenceTo>Course_Offering__c</referenceTo>
    <relationshipName>Registrations</relationshipName>
    <!-- 1 = secondary. -->
    <relationshipOrder>1</relationshipOrder>
    <reparentableMasterDetail>true</reparentableMasterDetail>
</CustomField>
```

**Why it works:** `relationshipOrder` "is valid for all master-detail relationships, but the value is only non-zero for junction objects" — declaring it turns an implicit creation-order side effect into a reviewable line of source. `reparentableMasterDetail` is set per side deliberately here: a registration should never move to a different student, but moving it to a different offering of the same course is a legitimate admin action.

---

## Anti-Pattern: Designing a Read Path Deeper Than SOQL Can Follow

**What practitioners do:** Model six or seven levels of parent lookups because each hop is individually defensible, then discover at build time that the report or LWC cannot reach the top:

```sql
-- Six child-to-parent hops. Exceeds the documented ceiling.
SELECT Id,
       Account__r.Parent__r.Region__r.Division__r.Company__r.Group__r.Name
FROM Service_Contract__c
```

**What goes wrong:** "In each specified relationship, no more than five levels can be specified in a child-to-parent relationship." Nothing in Setup prevents building the seventh level — the model deploys cleanly and only the query fails, usually after the data has already been loaded.

**Correct approach:** Flatten at the midpoint with a cross-object formula field so the deep value becomes a one-hop read for everything downstream:

```
/* Region__c.Group_Name__c — Formula (Text), cross-object up the hierarchy */
Division__r.Company__r.Group__r.Name
```

```sql
-- Two hops. Well inside every documented cap.
SELECT Id, Account__r.Region__r.Group_Name__c
FROM Service_Contract__c
```

Budget the read path when you draw the model. The same reference notes "A custom object allows up to 40 relationships" and caps a single query at 55 child-to-parent relationships and 20 parent-to-child relationships — those are the real design constraints, not the number of boxes on the diagram.
