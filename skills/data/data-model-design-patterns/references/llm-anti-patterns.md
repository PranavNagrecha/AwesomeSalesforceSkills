# LLM Anti-Patterns — Data Model Design Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce data model design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Defaulting to Master-Detail Without Evaluating Reparenting and Optionality Needs

**What the LLM generates:** "Use a Master-Detail relationship between Account and Project__c" without assessing whether the child record needs to exist independently, be reparented, or have optional parent assignment.

**Why it happens:** Master-detail relationships are presented as "stronger" and "better" in training data because they support roll-up summaries and cascade delete. LLMs default to master-detail without evaluating the constraints it imposes.

**Correct pattern:**

```text
Master-Detail vs Lookup decision:

Master-Detail:
- Child cannot exist without parent (required relationship)
- Cascade delete: deleting parent deletes all children
- Child inherits parent sharing (OWD of child is "Controlled by Parent")
- Supports native Roll-Up Summary fields
- Cannot reparent once created (unless Allow Reparenting is enabled)
- Maximum 2 master-detail relationships per object

Lookup:
- Child can exist without parent (optional relationship)
- No cascade delete by default (configurable on custom objects)
- Independent sharing model
- No native Roll-Up Summary (use DLRS, Flow, or Apex alternatives)
- Can be reparented freely
- Up to 40 lookup relationships per object

Choose Lookup when: optionality, reparenting, or independent sharing is needed.
Choose Master-Detail when: cascade delete and roll-up summaries are required
AND the child should never exist without its parent.
```

**Detection hint:** Flag master-detail recommendations that do not mention cascade delete implications, reparenting constraints, or sharing model inheritance.

---

## Anti-Pattern 2: Creating Redundant Fields Instead of Using Formula Fields or Relationships

**What the LLM generates:** "Add a Account_Name__c text field to the Contact object and populate it with a trigger" instead of using the standard Account.Name traversal via the AccountId lookup relationship, or "Add a Full_Address__c field and concatenate with a trigger" instead of using a formula field.

**Why it happens:** LLMs generate data model solutions that mirror application database design (denormalization) rather than leveraging Salesforce's native relationship traversal, formula fields, and roll-up summaries. Apex triggers for field synchronization are overrepresented in training data.

**Correct pattern:**

```text
Before adding a redundant field, check native alternatives:

1. Cross-object field access: use relationship notation
   Contact.Account.Name (in formulas), Account.Name (in SOQL via AccountId)

2. Calculated values: use Formula fields
   Full_Address__c = BillingStreet & ", " & BillingCity & " " & BillingState

3. Aggregated values: use Roll-Up Summary (master-detail) or
   Flow/DLRS/Apex (lookup relationships)

Redundant trigger-populated fields should only be used when:
- Cross-object formula fields exceed the compiled formula size limit (5,000 chars)
- The value is needed in a report filter or list view filter (formula fields
  have filtering limitations)
- Performance: frequently queried fields on large-volume objects where
  formula computation adds measurable overhead
```

**Detection hint:** Flag custom text/number fields that mirror a parent object field when a formula or relationship traversal would work. Look for trigger patterns that copy parent field values to child records.

---

## Anti-Pattern 3: Using Text Fields for Structured Data That Should Be Picklists or Lookups

**What the LLM generates:** "Add a Status__c Text(50) field" or "Add a Country__c Text(100) field" for values that should be constrained picklists or lookup relationships to reference objects.

**Why it happens:** Text fields are the simplest to create and require no value set definition. LLMs default to text fields because they appear in more training examples and avoid the additional setup of picklist values or lookup objects.

**Correct pattern:**

```text
Field type selection for constrained values:

Use Picklist when:
- Fixed set of values (< 1,000 distinct values)
- Values rarely change
- Reporting and filtering on the values is needed
- Consider Global Picklist Value Sets for shared values across objects

Use Lookup to reference object when:
- Values change frequently or are managed as data (not metadata)
- Additional attributes exist per value (e.g., Country has ISO code, region)
- Values exceed 1,000 entries
- Values are shared across multiple objects with referential integrity

Use Text only when:
- Values are truly freeform (names, descriptions, notes)
- No validation or constraint is needed
- The field will not be used for filtering or grouping in reports
```

**Detection hint:** Flag Text field recommendations for Status, Type, Category, Country, or State fields. Check whether a picklist or lookup would be more appropriate.

---

## Anti-Pattern 4: Ignoring the 40-Relationship-per-Object Limit

**What the LLM generates:** Data models that add lookup after lookup to a central object (e.g., Case) without tracking the total relationship count. Salesforce limits each object to 40 lookup/master-detail relationships combined.

**Why it happens:** The 40-relationship limit is a hard platform constraint that training data rarely mentions because most examples involve a few relationships. LLMs do not track cumulative relationship counts across a data model design.

**Correct pattern:**

```text
Relationship limits per object:
- Maximum 40 total relationships (lookups + master-details combined)
- Maximum 2 master-detail relationships per object
- Each polymorphic lookup (e.g., WhoId, WhatId) counts as 1

Before adding relationships to an object:
1. Query current count:
   SELECT COUNT() FROM EntityParticle
   WHERE EntityDefinitionId = 'CustomObject__c'
   AND DataType IN ('reference')

2. If approaching 40, consider:
   - Junction objects to consolidate relationships
   - Custom Metadata Types for configuration references
   - Text fields with External IDs for soft references (not enforced)
```

**Detection hint:** Flag data model designs that add 5+ relationships to a single object without checking the current relationship count. Look for central objects (Case, Account) that may already be near the limit.

---

## Anti-Pattern 5: Designing Many-to-Many Without a Junction Object

**What the LLM generates:** "Add a multi-select picklist on Account to store related Product names" or "Use a text field with comma-separated IDs" to model a many-to-many relationship instead of creating a proper junction object.

**Why it happens:** Junction objects require additional setup (new object, two master-detail or lookup relationships, page layouts). LLMs take shortcuts by suggesting multi-select picklists or text fields that avoid creating a new object but sacrifice queryability, reportability, and data integrity.

**Correct pattern:**

```text
Many-to-many relationship pattern in Salesforce:

1. Create a junction object: Account_Product__c
2. Add two relationships from the junction to each parent:
   - Account__c (Master-Detail or Lookup to Account)
   - Product__c (Master-Detail or Lookup to Product2)
3. Optionally add attributes on the junction (Quantity, Start_Date, etc.)
4. Create a Related List on each parent object's page layout

Junction object advantages over multi-select picklist:
- Reportable: join reports, cross-filters
- Queryable: SOQL with relationship queries
- Supports additional attributes per association
- Enforced referential integrity
- No 4,099-character limit (multi-select picklist limit)
```

**Detection hint:** Flag multi-select picklist or comma-separated text field recommendations where the data model describes a relationship between two objects. Look for "store related [object] names in a field" patterns.
