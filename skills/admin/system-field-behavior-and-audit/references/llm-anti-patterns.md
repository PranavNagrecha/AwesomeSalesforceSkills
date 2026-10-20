# LLM Anti-Patterns — System Field Behavior and Audit

Common mistakes AI coding assistants make when generating or advising on system fields and audit field behavior.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending LastModifiedDate for Delta Sync Queries

**What the LLM generates:**

```sql
SELECT Id, Name FROM Account WHERE LastModifiedDate > :lastSync
```

**Why it happens:** LastModifiedDate is the more "human-readable" field name, and most training data examples use it. LLMs default to the familiar name without understanding the update-scope difference (user modification, object_reference 264 L2563, vs user or automated process, L2566).

**Correct pattern:**

```sql
SELECT Id, Name FROM Account WHERE SystemModstamp > :lastSync ORDER BY SystemModstamp ASC
```

**Detection hint:** Any SOQL query using `LastModifiedDate` in a WHERE clause for sync/replication/ETL purposes.

---

## Anti-Pattern 2: Claiming SystemModstamp and LastModifiedDate Are Interchangeable

**What the LLM generates:** "SystemModstamp and LastModifiedDate both track when the record was last modified and can be used interchangeably."

**Why it happens:** Training data often describes both fields with the same generic definition ("timestamp of last modification"). The nuance that SystemModstamp includes automated system changes while LastModifiedDate does not is frequently omitted.

**Correct pattern:** "SystemModstamp records when a user or automated process last modified the record (object_reference 264 L2566); LastModifiedDate records when a user did (L2563). SystemModstamp is on the default index list (large_data_volumes_bp 264 L404). It does not capture every change — a value that object A retrieves from object B moves B's SystemModstamp, not A's (L2581-2583)." Do not state that SystemModstamp >= LastModifiedDate or that LastModifiedDate is unindexed: UNVERIFIED (2026-10-20).

**Detection hint:** Any statement containing "interchangeable", "same as", or "equivalent" when comparing these two fields.

---

## Anti-Pattern 3: Suggesting Update DML to Fix CreatedDate

**What the LLM generates:**

```apex
account.CreatedDate = DateTime.newInstance(2020, 1, 15, 0, 0, 0);
update account;
```

**Why it happens:** LLMs treat Salesforce fields like regular database columns and assume any field can be updated if you have sufficient permissions. They do not know that audit fields are insert-only even with the Create Audit Fields permission.

**Correct pattern:** Audit fields (CreatedDate, CreatedById, LastModifiedDate, LastModifiedById) are set when the record is created, with the Setup setting and user permission enabled (object_reference 264 L2599-2603). The guide documents no update path, so plan the values before insert; UNVERIFIED (2026-10-20): that delete and re-insert is the only remediation — a custom field for the true date is the safe alternative.

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

**Why it happens:** LLMs invent a Setup path such as "Setup > Create Audit Fields", or swing the other way and claim a Support case is required. The real path is Setup > User Interface (object_reference 264 L2599-2601).

**Correct pattern:** "Setup > User Interface > select 'Enable Set Audit Fields upon Record Creation' (and 'Update Records with Inactive Owners'). Then enable the permission 'Set Audit Fields upon Record Creation' in the profile or permission set of the migrating user, and create the record through the API (object_reference 264 L2599-2603)." The earlier "open a case with Support" fallback is removed: no corpus line says it. UNVERIFIED (2026-10-20): whether some orgs lack the Setup option.

**Detection hint:** Any instruction that mentions only the org-level setting without also mentioning the required user-level permission, or that oversimplifies the enablement path.

---

## Anti-Pattern 6: Confusing queryAll with ALL ROWS

**What the LLM generates:** "Use the `ALL ROWS` keyword in your REST API query URL" or "Use `queryAll` in your SOQL statement."

**Why it happens:** LLMs conflate the SOQL keyword (`ALL ROWS`) with the REST API endpoint (`/queryAll/`). They serve the same purpose but are used in completely different contexts.

**Correct pattern:** In SOQL (Apex, Developer Console, SOQL Builder), append `ALL ROWS` to the query string. In REST API calls, use the `/services/data/vXX.0/queryAll/` endpoint instead of `/query/`. In Bulk API, set the operation to `queryAll`. These are three distinct mechanisms for the same logical behavior.

**Detection hint:** Mixing `ALL ROWS` and `queryAll` terminology in the wrong context — SOQL syntax vs. REST endpoint vs. Bulk API operation.
