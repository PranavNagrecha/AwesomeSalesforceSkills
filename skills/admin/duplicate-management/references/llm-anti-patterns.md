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

For Apex-initiated DML, the per-transaction control is `Database.DMLOptions.DuplicateRuleHeader`:

```apex
Database.DMLOptions dml = new Database.DMLOptions();
dml.DuplicateRuleHeader.allowSave = true;         // bypass an Alert-configured rule
dml.DuplicateRuleHeader.runAsCurrentUser = true;  // enforce running user's sharing during matching
Database.SaveResult sr = Database.insert(record, dml);
```

`allowSave = true` bypasses alerts and saves the duplicate; `false` prevents the save. It has no effect on a rule configured to Block — that is why "just set it to Block and let Apex opt out" does not work. `runAsCurrentUser = true` enforces the current user's sharing rules while duplicate rules run, so users can't be shown duplicate records that aren't available to them.

**Detection hint:** If the output sets Block on the duplicate rule without differentiating between UI and API channels, integrations will break. Search for `API` or `integration` in the duplicate rule configuration. If the output tells an Apex developer to "handle" a Block-configured rule, it is wrong — no `DMLOptions` setting overrides Block.

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

---

## Anti-Pattern 6: Designing past the platform's rule ceilings

**What the LLM generates:** "Create a duplicate rule for each matching scenario: one for email matches, one for phone matches, one for name+company, one for name+address, one for domain, and one for the D&B key."

**Why it happens:** LLMs treat duplicate rules as free composable units, one per business scenario, the way they would write validation rules. The platform imposes hard ceilings. Salesforce documents up to five active duplicate rules per object, up to three matching rules in each duplicate rule with one active matching rule per object, and up to five active matching rules per object when using multiple duplicate rules. A six-rule design does not warn at design time; it fails at activation, usually in the target org rather than the sandbox where the sixth rule was never activated.

**Correct pattern:**

```
Budget the rules before designing them:
1. Active duplicate rules per object:               max 5
2. Matching rules per duplicate rule:               max 3
3. Active matching rules per object,
   within one duplicate rule:                       max 1
4. Active matching rules per object,
   across all duplicate rules:                      max 5

Consolidate along axes the platform respects:
- Split by operation (create vs. edit), not by field.
- Split by channel (UI vs. API/Apex), not by scenario.
- Express "email OR (name AND phone)" as multiple criteria
  inside ONE matching rule, not as multiple duplicate rules.

Cross-object detection consumes the per-duplicate-rule budget fast:
  Lead-to-Lead + Lead-to-Contact + Lead-to-Account = all 3 slots used.
```

**Detection hint:** Count the duplicate rules and matching rules in the output. If a single object has more than five active duplicate rules, more than three matching rules inside one duplicate rule, or two active matching rules targeting the same object inside one duplicate rule, the design cannot be activated as written.

---

## Anti-Pattern 7: Assuming duplicate rules run on every record-creation path

**What the LLM generates:** "Activate the duplicate rule on Contact and duplicates will be prevented across the org."

**Why it happens:** LLMs model duplicate rules as an object-level invariant, like a uniqueness constraint in a relational database. They are a save-path control, and Salesforce documents specific paths that skip them entirely: Quick Create, Community Self-Registration, Lightning Sync, Einstein Activity Capture, manual merges, undelete, and lead conversion when "Use Apex Lead Convert" isn't enabled. None of these raise an error or write a log entry. An org with a self-registering community can have its largest duplicate source sitting completely outside the rule.

The second, subtler version of this mistake: assuming the rule works uniformly for all users. If a user who updates a record doesn't have field-level access to one or more fields referenced in the matching rule, the duplicate rule doesn't work as expected for that user. The admin testing it sees correct behavior every time.

**Correct pattern:**

```
Before claiming an object is protected:
1. Inventory the create paths for the object:
   UI save, Quick Create, API/Apex, Bulk API, Web-to-Lead,
   self-registration, Lightning Sync, Einstein Activity Capture,
   lead conversion, undelete, merge.
2. Mark which ones duplicate rules actually evaluate.
3. For each skipped path, move the control upstream:
   - External ID + idempotent upsert for integrations
   - explicit pre-insert query for Apex-created records
   - a duplicate job / DuplicateRecordSet review for the rest
4. Audit field-level security on EVERY field the matching rule
   references, for every profile and permission set that
   creates or edits the object.
5. Report coverage as "% of create paths covered",
   not "duplicate rule is active".
```

**Detection hint:** If the output claims duplicates are "prevented" or "impossible" after activating a rule, it is overclaiming. Search for whether the output names any skipped create path, and whether it mentions field-level access as a precondition for matching. Neither appearing means the coverage claim is untested.
