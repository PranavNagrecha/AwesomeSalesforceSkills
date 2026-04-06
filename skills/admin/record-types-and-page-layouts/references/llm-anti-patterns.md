# LLM Anti-Patterns — Record Types and Page Layouts

Common mistakes AI coding assistants make when generating or advising on Salesforce Record Types and Page Layouts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Creating record types for UI differences that Dynamic Forms can handle

**What the LLM generates:** "Create a record type for each department so they see different fields on the page."

**Why it happens:** LLMs treat record types as the only way to show different fields to different users. Dynamic Forms (on supported objects) can conditionally show/hide fields based on profile, permission, field value, or device -- without creating record types. Record types add data model complexity (every record gets a RecordTypeId, picklist filtering, page layout matrix).

**Correct pattern:**

```
Decision: Record Type vs Dynamic Forms
Use Record Types when:
- Different picklist values per business process (different Stage values).
- Different business processes on the same object (B2B vs B2C Account).
- Different workflow/approval behavior per process.

Use Dynamic Forms when:
- Same picklist values, but different fields visible per profile.
- Conditional field visibility based on field values.
- Simplifying page complexity without adding record type overhead.

Record types add: RecordTypeId on every record, picklist matrix,
profile-to-record-type-to-page-layout assignment matrix.
Dynamic Forms add: visibility rules on the Lightning page. No data model change.
```

**Detection hint:** If the output creates record types solely to show/hide fields for different profiles without different picklist values or business processes, Dynamic Forms is the simpler solution. Check whether the requirement involves picklist variation or just field visibility.

---

## Anti-Pattern 2: Assuming record types control data security or record access

**What the LLM generates:** "Create a 'Confidential' record type to prevent non-authorized users from seeing those records."

**Why it happens:** LLMs conflate record types with security mechanisms. Record types control UI presentation (page layouts, picklist values, default values) but do NOT control record-level access. A user with object Read permission can see all records regardless of record type. Record access is controlled by OWD, sharing rules, and role hierarchy.

**Correct pattern:**

```
Record types ≠ Security:
- Record types control: page layout, picklist values, business process.
- Record types do NOT control: who can see or edit the record.

For record-level security:
- Use sharing rules with criteria (e.g., Type = 'Confidential' → share
  with Confidential Users group only).
- Use OWD set to Private + criteria-based sharing rules.
- Use Apex sharing (programmatic sharing) for complex scenarios.

A record type named "Confidential" without corresponding sharing rules
provides ZERO security benefit.
```

**Detection hint:** If the output creates a record type for security purposes without configuring sharing rules or OWD, the security is illusory. Search for `security`, `restrict access`, or `prevent` combined with `record type` without `sharing`.

---

## Anti-Pattern 3: Creating a 1:1 mapping of page layouts to record types

**What the LLM generates:** "Create Record Type A with Page Layout A, Record Type B with Page Layout B, Record Type C with Page Layout C."

**Why it happens:** LLMs create one page layout per record type by default. The actual assignment is a matrix: Profile x Record Type → Page Layout. Different profiles can see different page layouts for the same record type. A 1:1 mapping misses the opportunity to show sales reps a simpler layout while managers see a detailed layout for the same record type.

**Correct pattern:**

```
Page Layout Assignment Matrix:
                    | RT: B2B Account | RT: B2C Account |
|--------------------|-----------------|-----------------|
| Sales Rep profile  | B2B Simple      | B2C Simple      |
| Sales Mgr profile  | B2B Detailed    | B2C Detailed    |
| Service Agent      | Service Layout  | Service Layout  |

Multiple profiles can share a page layout.
One record type can have different page layouts per profile.
Design the matrix intentionally, not 1:1.

To configure: Setup → Object Manager → [Object] → Page Layouts →
Page Layout Assignment → Edit Assignment.
```

**Detection hint:** If the output creates one page layout per record type without considering the profile dimension, the assignment matrix is underutilized. Search for `Page Layout Assignment` matrix or `profile` in the layout configuration.

---

## Anti-Pattern 4: Forgetting to assign record types to profiles

**What the LLM generates:** "Create the record type. Users can now select it when creating records."

**Why it happens:** LLMs skip the profile assignment step. A record type is not available to users until it is assigned to their profile (or permission set, in newer releases). Unassigned record types are invisible in the record type selector during record creation.

**Correct pattern:**

```
After creating a record type:
1. Assign to profiles:
   Setup → Object Manager → [Object] → Record Types → [RT] → Edit.
   Or: Setup → Profiles → [Profile] → Object Settings → [Object] → Edit.
   Check the record type under "Available Record Types."
2. Set one record type as "Default" per profile:
   The default is auto-selected when the user creates a record.
   If only one RT is assigned, it is auto-selected (no prompt).
3. If a user has multiple record types assigned:
   They see a record type selector during record creation.
4. Assign via Permission Sets (newer feature):
   Permission sets can grant access to additional record types
   beyond what the profile allows.
```

**Detection hint:** If the output creates a record type without assigning it to profiles, users will not see it. Search for `assign to profile` or `Available Record Types` after record type creation.

---

## Anti-Pattern 5: Over-engineering with too many record types

**What the LLM generates:** "Create record types for: New Lead, Qualified Lead, Unqualified Lead, Converted Lead, Recycled Lead."

**Why it happens:** LLMs create a record type for each status or stage. Status-based differentiation should use a picklist field (Status, Stage), not record types. Record types are for fundamentally different business processes that require different picklist values, page layouts, or workflow behavior. Status changes within the same process should use a field value change.

**Correct pattern:**

```
"Do you actually need a Record Type?" decision:
1. Are the picklist values fundamentally different? → Yes → Record Type.
2. Is the page layout fundamentally different? → Maybe → check Dynamic Forms first.
3. Is the difference just a status or stage progression? → No Record Type.
   Use a picklist field + path component.
4. General guideline: 2-4 record types per object is healthy.
   5+ record types suggests the object is overloaded or status is
   being confused with process.

Example:
- Good: Account RT: B2B, B2C (different business processes).
- Bad: Lead RT: New, Qualified, Unqualified, Converted
  (these are statuses, not processes — use Lead Status picklist).
```

**Detection hint:** If the output creates more than 4 record types for a single object, or creates record types that correspond to a status progression, the model is over-engineered. Count the record types and check if they represent statuses rather than processes.
