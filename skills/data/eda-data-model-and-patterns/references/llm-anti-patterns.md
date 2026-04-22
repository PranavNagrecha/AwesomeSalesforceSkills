# LLM Anti-Patterns — EDA Data Model and Patterns

Common mistakes AI coding assistants make when modeling education data in EDA.

## Anti-Pattern 1: Creating a Student__c custom object alongside Contact

**What the LLM generates:** "Student__c with fields GPA, Major, Graduation_Date" as a separate object.

**Why it happens:** The model thinks domain objects deserve their own table.

**Correct pattern:**

```
Student = Contact with an Affiliation__c (Role = "Student"). No
parallel Student__c object. Extend Contact with student-specific
fields and use the Affiliation__c to express the student-to-program
relationship. Shadow objects break every EDA report and rollup.
```

**Detection hint:** A `Student__c` custom object in the EDA org with a Contact__c lookup.

---

## Anti-Pattern 2: Putting guardian data as a field on student Contact

**What the LLM generates:** `Guardian_Name__c`, `Guardian_Email__c`, `Guardian_Phone__c` directly on Contact.

**Why it happens:** The model flattens related data to avoid joins.

**Correct pattern:**

```
Guardian is a Contact with a Relationship__c to the student Contact.
Role = "Parent" or "Guardian". The reverse Relationship is created
automatically by EDA's trigger. Guardian fields on Contact scale
badly for multi-guardian families and break privacy rules.
```

**Detection hint:** Fields named `Guardian_*` or `Parent_*` on Contact object.

---

## Anti-Pattern 3: Course_Connection__c without record types

**What the LLM generates:** Single record type on Course_Connection__c; faculty and student connections look the same.

**Why it happens:** The model creates the minimum viable schema.

**Correct pattern:**

```
Course_Connection__c needs distinct record types for Student
(enrollment) and Faculty (teaching assignment), each with its own
page layout and validation. Reports filter by record type to
distinguish enrollment rosters from teaching loads.
```

**Detection hint:** Course_Connection__c with a single record type in an org that tracks both enrollment and faculty assignments.

---

## Anti-Pattern 4: Storing every demographic field on Contact

**What the LLM generates:** 150 fields on Contact for race, ethnicity, test scores, survey answers.

**Why it happens:** The model defaults to fields rather than extensibility patterns.

**Correct pattern:**

```
Stable demographics belong on Contact. Highly variable or optional
attributes (survey responses, test score history) fit Attribute__c
(key-value) or a dedicated child object. Wide Contact tables slow
every query and confuse admins.
```

**Detection hint:** Contact object with more than 100 custom fields, many with low population.

---

## Anti-Pattern 5: Hard-coding term IDs in Apex or Flow

**What the LLM generates:** `if (Course_Connection__c.Term__c == '0011x00000XYZ') { ... }` in Apex.

**Why it happens:** The model writes a conditional against a specific term rather than term attributes.

**Correct pattern:**

```
Never hard-code Term__c IDs. Query Term__c by dates or an "Is_Current"
flag maintained by a scheduled process. Hard-coded IDs break every
academic year and are a common source of semester-rollover bugs.
```

**Detection hint:** Apex or Flow with a literal Salesforce ID in a condition involving Term__c.
