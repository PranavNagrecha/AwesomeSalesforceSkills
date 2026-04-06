# LLM Anti-Patterns — System Field Behavior and Audit

Common mistakes AI coding assistants make when generating or advising on system fields and audit field behavior.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending LastModifiedDate for Delta Sync Queries

**What the LLM generates:**

```sql
SELECT Id, Name FROM Account WHERE LastModifiedDate > :lastSync
```

**Why it happens:** LastModifiedDate is the more "human-readable" field name, and most training data examples use it. LLMs default to the familiar name without understanding the indexing and update-scope differences.

**Correct pattern:**

```sql
SELECT Id, Name FROM Account WHERE SystemModstamp > :lastSync ORDER BY SystemModstamp ASC
```

**Detection hint:** Any SOQL query using `LastModifiedDate` in a WHERE clause for sync/replication/ETL purposes.

---

## Anti-Pattern 2: Claiming SystemModstamp and LastModifiedDate Are Interchangeable

**What the LLM generates:** "SystemModstamp and LastModifiedDate both track when the record was last modified and can be used interchangeably."

**Why it happens:** Training data often describes both fields with the same generic definition ("timestamp of last modification"). The nuance that SystemModstamp includes automated system changes while LastModifiedDate does not is frequently omitted.

**Correct pattern:** "SystemModstamp updates on all changes including automated processes (workflow field updates, formula recalculations). LastModifiedDate updates only on direct user or API modifications. SystemModstamp >= LastModifiedDate. SystemModstamp is indexed; LastModifiedDate is not."

**Detection hint:** Any statement containing "interchangeable", "same as", or "equivalent" when comparing these two fields.

---

## Anti-Pattern 3: Suggesting Update DML to Fix CreatedDate

**What the LLM generates:**

```apex
account.CreatedDate = DateTime.newInstance(2020, 1, 15, 0, 0, 0);
update account;
```

**Why it happens:** LLMs treat Salesforce fields like regular database columns and assume any field can be updated if you have sufficient permissions. They do not know that audit fields are insert-only even with the Create Audit Fields permission.

**Correct pattern:** Audit fields (CreatedDate, CreatedById, LastModifiedDate, LastModifiedById) can only be set on insert with the Create Audit Fields permission enabled. To correct a wrong CreatedDate, you must delete and re-insert the record (with cascading implications) or store the correct date in a custom field.

**Detection hint:** Any DML `update` statement that sets `CreatedDate`, `CreatedById`, `LastModifiedDate`, or `LastModifiedById`.

---

## Anti-Pattern 4: Omitting ALL ROWS When Querying Deleted Records

**What the LLM generates:**

```sql
SELECT Id, Name FROM Account WHERE IsDeleted = true
```

**Why it happens:** LLMs generate syntactically valid SOQL but forget the `ALL ROWS` keyword. Standard SOQL queries automatically exclude deleted records regardless of the IsDeleted filter, so the query returns zero results.

**Correct pattern:**

```sql
SELECT Id, Name FROM Account WHERE IsDeleted = true ALL ROWS
```

**Detection hint:** Any SOQL query referencing `IsDeleted` without the `ALL ROWS` keyword at the end.

---

## Anti-Pattern 5: Stating Create Audit Fields Is Self-Service

**What the LLM generates:** "Go to Setup > Create Audit Fields and enable the checkbox."

**Why it happens:** LLMs hallucinate a simple Setup path because most org-level settings follow that pattern. In reality, enabling Create Audit Fields historically required a Salesforce Support case, though some editions now expose it under Setup > User Interface.

**Correct pattern:** "The org-level setting may be available under Setup > User Interface > 'Enable Set Audit Fields upon Record Creation.' If the option is not visible, open a case with Salesforce Support. Additionally, the individual user performing the migration must be assigned the 'Set Audit Fields upon Record Creation' user permission via a permission set."

**Detection hint:** Any instruction that mentions only the org-level setting without also mentioning the required user-level permission, or that oversimplifies the enablement path.

---

## Anti-Pattern 6: Confusing queryAll with ALL ROWS

**What the LLM generates:** "Use the `ALL ROWS` keyword in your REST API query URL" or "Use `queryAll` in your SOQL statement."

**Why it happens:** LLMs conflate the SOQL keyword (`ALL ROWS`) with the REST API endpoint (`/queryAll/`). They serve the same purpose but are used in completely different contexts.

**Correct pattern:** In SOQL (Apex, Developer Console, SOQL Builder), append `ALL ROWS` to the query string. In REST API calls, use the `/services/data/vXX.0/queryAll/` endpoint instead of `/query/`. In Bulk API, set the operation to `queryAll`. These are three distinct mechanisms for the same logical behavior.

**Detection hint:** Mixing `ALL ROWS` and `queryAll` terminology in the wrong context — SOQL syntax vs. REST endpoint vs. Bulk API operation.
