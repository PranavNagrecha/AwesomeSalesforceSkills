# LLM Anti-Patterns — Data Migration Planning

Common mistakes AI coding assistants make when generating or advising on Salesforce data migration planning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Wrong Object Load Order for Parent-Child Relationships

**What the LLM generates:** "Load Contacts first, then load Accounts" or loading child objects before their parent objects, which causes lookup/master-detail failures because the parent record IDs do not exist yet.

**Why it happens:** LLMs generate load sequences alphabetically or in the order objects are mentioned in the conversation, rather than following the dependency graph. Master-detail children cannot be inserted without an existing parent record.

**Correct pattern:**

```text
Migration load order must follow the dependency graph:

1. Users (if assigning ownership to non-default users)
2. Parent objects with no dependencies (Accounts, Products, Pricebooks)
3. Child objects of those parents (Contacts, Opportunities, PricebookEntries)
4. Grandchild objects (OpportunityLineItems, OpportunityContactRoles)
5. Junction objects (many-to-many relationships — both parents must exist first)
6. Objects with self-lookups (Accounts with ParentId — load parents first,
   then update ParentId in a second pass)

Always map the full relationship graph before determining load order.
```

**Detection hint:** Flag migration plans that load child objects before parent objects. Check for Contact before Account, OpportunityLineItem before Opportunity, or junction objects before both parent objects.

---

## Anti-Pattern 2: Not Using External IDs for Upsert Idempotency

**What the LLM generates:** "Insert the records using Data Loader" without setting up an External ID field for upsert operations, meaning every re-run of the migration creates duplicate records instead of updating existing ones.

**Why it happens:** Insert is simpler than upsert and dominates tutorial content. The concept of External IDs for idempotent data loading is a migration-specific pattern that requires pre-migration planning.

**Correct pattern:**

```text
External ID strategy for migrations:

1. Create an External ID field on each target object (Text, unique, external ID)
   Example: Legacy_Id__c (Text, 18 chars, External ID, Unique)

2. Populate the External ID with the source system's primary key

3. Use UPSERT (not INSERT) for all load operations:
   - Data Loader: select "Upsert" and choose the External ID field
   - Bulk API: operation = "upsert", externalIdFieldName = "Legacy_Id__c"

4. Re-running the migration updates existing records instead of creating dupes

5. Use External ID for relationship mapping:
   Instead of: AccountId = "001xx000003abcDEF" (Salesforce ID)
   Use: Account.Legacy_Id__c = "ACCT-12345" (source system ID)
```

**Detection hint:** Flag migration plans that use "insert" without an External ID strategy. Look for Salesforce IDs used as relationship mapping keys instead of External IDs.

---

## Anti-Pattern 3: Ignoring Validation Rule and Trigger Bypass During Migration

**What the LLM generates:** "Load the data and fix any validation errors that come up" as a reactive approach, instead of proactively planning for validation rule bypasses, trigger suppression, and Flow deactivation during the migration window.

**Why it happens:** LLMs approach migrations as a straightforward data load. The operational reality — that migrated data often violates validation rules designed for UI data entry, and that triggers designed for single-record operations cause governor limit failures during bulk loads — is underrepresented.

**Correct pattern:**

```text
Pre-migration bypass strategy:

1. Validation Rules:
   - Add a bypass condition: $User.Bypass_Validation__c = true
   - Or temporarily deactivate non-essential rules (with change log)

2. Apex Triggers:
   - Implement a bypass flag: Custom_Settings__c.Bypass_Triggers__c
   - Check the flag in trigger handler before processing

3. Flows:
   - Deactivate record-triggered Flows on objects being loaded
   - Or add an entry condition: $User.Bypass_Flow__c != true

4. Workflow Rules / Process Builders:
   - Deactivate during migration window

5. Assignment Rules:
   - Uncheck "Use Assignment Rules" in Data Loader settings

6. Sharing Rules:
   - Defer sharing calculation during large loads (Setup > Sharing Settings)

Re-enable ALL bypass mechanisms after migration and verify data integrity.
```

**Detection hint:** Flag migration plans that do not include a validation rule or trigger bypass strategy. Look for missing references to `Bypass` custom settings or deactivation steps.

---

## Anti-Pattern 4: Not Planning for Rollback

**What the LLM generates:** "If something goes wrong, delete the bad records and reload" as the rollback strategy, without planning for cascade delete implications, recycle bin limits, and the difficulty of identifying which records were loaded in the failed batch.

**Why it happens:** Rollback in Salesforce is not a single "ROLLBACK" command like in a database transaction. LLMs apply relational database thinking to a platform where rollback requires deliberate planning.

**Correct pattern:**

```text
Migration rollback plan:

1. Pre-load: record IDs of all existing records on each target object
   (snapshot for comparison)

2. Tag loaded records:
   - Populate a "Migration_Batch__c" field with the migration run ID
   - This allows querying all records from a specific load for deletion

3. Rollback procedure:
   - Query: SELECT Id FROM Account WHERE Migration_Batch__c = 'Run-001'
   - Delete using Bulk API hardDelete to bypass Recycle Bin
   - Delete children before parents to avoid cascade issues

4. Point-of-no-return assessment:
   - If triggers updated existing records, rollback is not a simple delete
   - If other users created records referencing migrated data, those references break
   - Define the point-of-no-return in the migration plan

5. Dry run in sandbox first — always.
```

**Detection hint:** Flag migration plans that mention "delete and reload" as rollback without a batch tagging strategy, cascade delete handling, or point-of-no-return assessment.

---

## Anti-Pattern 5: Overlooking Owner Assignment for Inactive Users

**What the LLM generates:** "Map the OwnerId field to the correct user in Salesforce" without checking whether the target owner is an active user. Assigning ownership to inactive users causes DML failures.

**Why it happens:** Training data assumes all referenced users are active. Migration-specific scenarios where source data references users who have left the organization are not commonly covered.

**Correct pattern:**

```text
Owner assignment during migration:

1. Extract unique owner values from source data
2. Map to Salesforce User records:
   SELECT Id, IsActive, Username FROM User WHERE Username IN :ownerList
3. For inactive users:
   - Option A: reactivate temporarily during migration, then deactivate
   - Option B: assign to a default active user or queue, tag with
     Original_Owner__c for audit
   - Option C: create an integration user as the default migration owner

4. For queue ownership (Cases, Leads):
   SELECT Id, Name FROM Group WHERE Type = 'Queue'
   Map source queue names to Salesforce Queue IDs

5. Validate owner mapping BEFORE loading data — not during.
```

**Detection hint:** Flag migration plans that map OwnerId without a step to verify user active status. Look for missing handling of inactive or missing users.
