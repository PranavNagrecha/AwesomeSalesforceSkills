# LLM Anti-Patterns — Duplicate Management

Common mistakes AI coding assistants make when generating or advising on Salesforce Duplicate Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending "Block" action on duplicate rules without considering integrations

**What the LLM generates:** "Set the duplicate rule to Block so no duplicate records can be created."

**Why it happens:** LLMs default to the strictest enforcement. Blocking duplicates on save prevents duplicates from the UI, but also blocks API-based record creation from integrations, Data Loader, and Web-to-Lead. This causes silent data loss when external systems cannot insert records.

**Correct pattern:**

```
Configure duplicate rule actions by channel:
1. Duplicate Rule → Action on Create:
   - Allow (with Alert): shows a warning but lets the user save.
   - Block: prevents the save entirely.
2. Configure SEPARATELY for "Record Created by Non-Apex Sources"
   and "Record Created by Apex or API":
   - UI users: Block or Alert depending on business tolerance.
   - API/Integrations: typically Allow with logging, NOT Block.
     Blocking on API causes integration failures.
3. Route duplicates to a stewardship queue for manual review
   rather than silently blocking integration records.
```

**Detection hint:** If the output sets Block on the duplicate rule without differentiating between UI and API channels, integrations will break. Search for `API` or `integration` in the duplicate rule configuration.

---

## Anti-Pattern 2: Relying solely on exact matching for fuzzy data

**What the LLM generates:** "Create a matching rule on Email with exact match to find duplicates."

**Why it happens:** LLMs default to exact matching because it is deterministic. Real-world data has typos, formatting differences, and abbreviations. "john@acme.com" and "John@acme.com" may be the same person but fail exact match. Standard matching rules support fuzzy match methods for names and addresses.

**Correct pattern:**

```
Choose matching algorithms based on data quality:
- Email: Exact match is reasonable (case-insensitive by default).
- First Name / Last Name: use Fuzzy: First Name or Fuzzy: Last Name
  (handles nicknames like "Bob" vs "Robert" partially).
- Company/Account Name: use Fuzzy: Company Name
  (handles "Acme Corp" vs "Acme Corporation").
- Phone: use Exact match but normalize format first
  (strip spaces, dashes, country codes).
- Address: use Fuzzy matching or normalize to a standard format.

Combine multiple matching criteria for higher confidence:
  Match if: (Email = Exact) OR (First Name = Fuzzy AND Last Name = Fuzzy AND Phone = Exact)
```

**Detection hint:** If the output uses only Exact match on name or company fields, it will miss common duplicates. Search for `Exact` on fields like `Name`, `Company`, or `Account Name`.

---

## Anti-Pattern 3: Skipping survivorship rules before mass merge operations

**What the LLM generates:** "Use the Merge Accounts feature to combine the duplicates. Salesforce will keep the master record's data."

**Why it happens:** LLMs oversimplify the merge process. During a merge, the admin must choose which record is the master and which field values survive. Without defined survivorship rules, admins make ad hoc choices per merge, leading to inconsistent data (e.g., sometimes keeping the newer phone number, sometimes the older one).

**Correct pattern:**

```
Define survivorship rules BEFORE merging:
1. Document which field values should survive per field:
   | Field             | Survivorship Rule               |
   |-------------------|---------------------------------|
   | Phone             | Most recently modified value    |
   | Email             | Non-blank value from either record |
   | Account Owner     | From the master record          |
   | Annual Revenue    | Highest value                   |
   | Description       | Concatenate both values         |
2. For standard merge (Setup → Accounts → Merge):
   admin manually selects per field — train on the rules above.
3. For mass merge (third-party tool like DemandTools, Cloudingo):
   configure the survivorship rules in the tool before running.
4. Test the merge on a small sample in sandbox first.
```

**Detection hint:** If the output recommends merging without mentioning survivorship rules or field-by-field value selection, the merge is under-governed. Search for `survivorship` or `which value to keep` in the merge instructions.

---

## Anti-Pattern 4: Ignoring that standard duplicate rules only cover Leads, Contacts, and Accounts

**What the LLM generates:** "Enable the standard duplicate rule on the Opportunity object to prevent duplicate deals."

**Why it happens:** LLMs generalize duplicate rules to all objects. Salesforce provides standard matching rules and duplicate rules only for Leads, Contacts, and Accounts. For custom objects or other standard objects (Opportunity, Case), you must create custom matching rules and custom duplicate rules.

**Correct pattern:**

```
Standard duplicate management coverage:
- Leads: standard matching rules available out of the box.
- Contacts: standard matching rules available out of the box.
- Accounts: standard matching rules available out of the box.

For all other objects (Opportunity, Case, custom objects):
1. Create a Custom Matching Rule:
   Setup → Matching Rules → New → select the object.
   Define match criteria on relevant fields.
2. Activate the matching rule (may take time to index).
3. Create a Duplicate Rule referencing the custom matching rule.
4. Activate the duplicate rule.
```

**Detection hint:** If the output references "standard duplicate rule" on an object other than Lead, Contact, or Account, it is incorrect. Check the object name against the supported list.

---

## Anti-Pattern 5: Not accounting for cross-object duplicate detection (Lead-to-Contact)

**What the LLM generates:** "Create a duplicate rule on the Lead object to find duplicate Leads."

**Why it happens:** LLMs scope duplicate detection to a single object. Salesforce supports cross-object matching: a duplicate rule on Leads can reference a matching rule on Contacts (and vice versa) to flag when a Lead being created already exists as a Contact. Ignoring this creates duplicates across the lead-to-contact lifecycle.

**Correct pattern:**

```
Configure cross-object duplicate detection:
1. Duplicate Rule on Lead:
   - Matching Rule 1: Lead-to-Lead (find duplicate Leads).
   - Matching Rule 2: Lead-to-Contact (find Leads that already exist as Contacts).
2. Duplicate Rule on Contact:
   - Matching Rule 1: Contact-to-Contact (find duplicate Contacts).
   - Matching Rule 2: Contact-to-Lead (find Contacts that already exist as Leads).
3. Action: Alert the user that a matching Contact/Lead already exists.
   Include a link to the existing record in the duplicate alert.
4. Train users: when a duplicate is flagged across objects, convert
   the Lead rather than creating a new Contact.
```

**Detection hint:** If the output creates duplicate rules scoped to only one object without mentioning cross-object matching (Lead-to-Contact or Contact-to-Lead), the detection is incomplete. Search for `cross-object` or references to both Lead and Contact in the same duplicate rule.
