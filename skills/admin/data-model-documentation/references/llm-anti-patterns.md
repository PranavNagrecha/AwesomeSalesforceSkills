# LLM Anti-Patterns — Data Model Documentation

Common mistakes AI coding assistants make when generating or advising on Salesforce data model documentation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Documenting only custom objects and ignoring standard objects

**What the LLM generates:** "Here is the ER diagram showing all custom objects and their relationships."

**Why it happens:** LLMs focus on what the admin built (custom objects) and skip standard objects. In most Salesforce orgs, critical business processes flow through standard objects (Account, Contact, Opportunity, Case, Lead) with custom fields. A data model document that excludes standard objects misrepresents the actual architecture.

**Correct pattern:**

```
Include both standard and custom objects in documentation:
1. Core standard objects in scope:
   - Account, Contact, Lead, Opportunity, Case, Product, PricebookEntry
   - Include their custom fields, not just their existence.
2. Custom objects and their relationships to standard objects.
3. Junction objects that create many-to-many relationships.
4. Mark which objects are standard vs custom in the documentation
   (e.g., color-coding in ER diagrams: blue = standard, green = custom).
```

**Detection hint:** If the data model documentation only lists objects ending in `__c` without standard objects like Account, Contact, or Opportunity, the coverage is incomplete. Check for standard object names in the output.

---

## Anti-Pattern 2: Using field labels instead of API names in technical documentation

**What the LLM generates:** "The Account object has a field called 'Annual Revenue' related to the 'Industry' field."

**Why it happens:** LLMs use human-readable labels because they appear in the UI. Technical data model documentation must include API names because labels can be renamed by admins, differ across translations, and are not unique. Developers and integrations reference API names.

**Correct pattern:**

```
Field inventory format for technical audiences:
| Object API Name | Field Label      | Field API Name        | Type     | Required |
|-----------------|------------------|-----------------------|----------|----------|
| Account         | Annual Revenue   | AnnualRevenue         | Currency | No       |
| Account         | Industry         | Industry              | Picklist | No       |
| Account         | Customer Tier    | Customer_Tier__c      | Picklist | Yes      |

Always include the API name. Labels are supplementary context.
For code, integration, and metadata references, the API name is authoritative.
```

**Detection hint:** If the documentation uses only field labels without API names, it is incomplete for technical use. Search for `__c` or standard API names like `AnnualRevenue` in the output.

---

## Anti-Pattern 3: Generating fabricated relationship cardinality

**What the LLM generates:** "Account has a many-to-many relationship with Contact."

**Why it happens:** LLMs hallucinate relationship types based on general database knowledge. In Salesforce, Contact has a standard Lookup to Account (one Account to many Contacts). While AccountContactRelation enables a Contact to be related to multiple Accounts (with the Contacts to Multiple Accounts feature), the base model is one-to-many, not many-to-many.

**Correct pattern:**

```
Document relationships as they actually exist in the org:
- Standard Lookup: Contact.AccountId → Account (Many Contacts : One Account).
- If "Contacts to Multiple Accounts" is enabled:
  AccountContactRelation junction object enables indirect M:N,
  but the direct lookup is still one-to-many.
- Master-Detail: Opportunity Line Item → Opportunity (cascade delete, inherits sharing).
- Custom junction objects: explicitly document both master-detail relationships
  that create the many-to-many pattern.

Verify cardinality by checking the actual field type (Lookup vs Master-Detail)
in Object Manager, not by assuming from business logic.
```

**Detection hint:** If the output states a relationship cardinality (1:1, 1:N, M:N) without referencing the actual field type or junction object, it may be fabricated. Search for `many-to-many` and verify a junction object is identified.

---

## Anti-Pattern 4: Omitting field usage metadata (blank descriptions, unused fields)

**What the LLM generates:** "Here is the complete field inventory for the Account object: [list of all fields with types]."

**Why it happens:** LLMs list fields mechanically without assessing quality. A useful data model document flags fields with blank Description values (undocumented), fields with 0% population rates (potentially unused), and fields with identical purposes (duplicates). These quality signals help the admin prioritize cleanup.

**Correct pattern:**

```
Field inventory should include usage quality columns:
| Field API Name       | Type     | Description        | Population % | Notes          |
|----------------------|----------|--------------------|-------------|----------------|
| Customer_Tier__c     | Picklist | Customer segment   | 94%         | Active, documented |
| Legacy_Code__c       | Text     | (blank)            | 2%          | Likely unused  |
| Revenue_Category__c  | Picklist | Revenue bracket    | 91%         | Active         |
| Old_Revenue_Cat__c   | Picklist | (blank)            | 0%          | Candidate for removal |

Flag fields where:
- Description is blank → undocumented.
- Population rate < 5% → potentially unused.
- Multiple fields serve similar purposes → possible duplicates.
```

**Detection hint:** If the field inventory has no Description column, no population/usage data, or no quality flags, it is a raw dump rather than an actionable document. Search for `Description`, `population`, or `usage` in the inventory.

---

## Anti-Pattern 5: Creating an ER diagram that is too dense to be useful

**What the LLM generates:** "Here is the full org ER diagram with all 150 objects and every relationship."

**Why it happens:** LLMs try to be comprehensive and generate a single diagram with every object. An ER diagram with more than 15-20 objects becomes unreadable. Effective documentation uses domain-specific sub-diagrams (Sales objects, Service objects, custom app objects) with a high-level overview connecting the domains.

**Correct pattern:**

```
Structure ER diagrams by domain:
1. High-level overview: one diagram showing major object groups
   and the key relationships between them (max 10-12 boxes).
2. Sales domain: Account, Contact, Lead, Opportunity, Quote,
   Opportunity Line Item, Product, PricebookEntry.
3. Service domain: Account, Contact, Case, Entitlement,
   Knowledge Article, related custom objects.
4. Custom app domain(s): one diagram per functional area.

Each diagram should have:
- Max 15-20 objects.
- Relationship lines with cardinality (1:N, M:N via junction).
- Legend distinguishing standard vs custom objects.
```

**Detection hint:** If the output produces a single diagram instruction listing more than 20 objects, it will be unreadable. Count the number of objects in the diagram spec.
