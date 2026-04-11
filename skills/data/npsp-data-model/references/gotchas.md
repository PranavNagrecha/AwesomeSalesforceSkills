# Gotchas — NPSP Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Wrong Namespace Prefix Returns Zero Rows Without an Error

**What happens:** A SOQL query against an NPSP object using the wrong namespace prefix (e.g., `npsp__OppPayment__c` instead of `npe01__OppPayment__c`) executes without throwing an exception and returns an empty result set. There is no "object not found" error at runtime in anonymous Apex or in most query tools — the query silently returns nothing.

**When it occurs:** Any time a developer or LLM guesses a namespace prefix rather than confirming it from the NPSP data dictionary or a Schema.describe() call. This is extremely common because NPSP is marketed under the "npsp" brand, leading people to assume all objects use the `npsp__` prefix.

**How to avoid:** Always use the five-prefix reference table. Payments and household objects = `npe01__`. Recurring Donations = `npe03__`. Relationships = `npe4__`. Affiliations = `npe5__`. GAUs and Allocations = `npsp__`. When in doubt, confirm the object exists using the Object Manager in Setup or `SELECT QualifiedApiName FROM EntityDefinition WHERE QualifiedApiName LIKE '%npe%' OR QualifiedApiName LIKE '%npsp%'`.

---

## Gotcha 2: Deleting an Opportunity Leaves Orphaned GAU Allocation Records

**What happens:** `npsp__Allocation__c` records link to their parent Opportunity via a lookup field (`npsp__Opportunity__c`), not a master-detail relationship. When an Opportunity is deleted, Salesforce does not cascade-delete its related allocation records. The orphaned allocations retain the deleted Opportunity's ID in their lookup field, making them inaccessible via standard Opportunity traversal and causing GAU totals in reports to be inflated by the "ghost" amounts.

**When it occurs:** Any bulk delete of Opportunities — data cleanup operations, deduplication merges (note: merging Opportunities via the UI does handle allocations, but programmatic merges may not), or migration scripts that delete source records after loading to a new org.

**How to avoid:** Before deleting any Opportunity batch, run `SELECT Id FROM npsp__Allocation__c WHERE npsp__Opportunity__c IN :oppIds` and delete the results first. Include this pre-delete allocation cleanup in every data maintenance script that touches Opportunity deletion. After any bulk delete, audit for orphans with `SELECT Id, npsp__Opportunity__c FROM npsp__Allocation__c WHERE npsp__Opportunity__c = NULL`.

---

## Gotcha 3: Creating Installment Opportunities Without a Parent Recurring Donation Breaks Rollups

**What happens:** NPSP maintains several rollup summary fields on Contact and Account that aggregate donation totals from recurring gift installments (e.g., `npe01__TotalOppAmount__c`). These rollups operate correctly only when installment Opportunities have a populated `npe03__Recurring_Donation__c` lookup field pointing to the parent `npe03__Recurring_Donation__c` record. Creating installment Opportunities directly — without the parent recurring donation — causes the recurring donation schedule to fall out of sync and produces incorrect totals in those rollup fields.

**When it occurs:** Data migration projects that recreate historical installment records directly as Opportunities; Apex code that generates future installments to pre-populate them before the NPSP scheduler runs; any import that maps installments to Opportunities but does not also create and link the parent recurring donation.

**How to avoid:** Always create the parent `npe03__Recurring_Donation__c` record first and populate the `npe03__Recurring_Donation__c` lookup on each installment Opportunity. For programmatic creation, use NPSP's provided Recurring Donations API or set the lookup field explicitly. After any bulk load of installment Opportunities, verify rollup field values against expected totals.

---

## Gotcha 4: Mirror Relationship Deletion is Bidirectional and Causes Double-Count Errors

**What happens:** NPSP's relationship engine auto-creates a reciprocal mirror `npe4__Relationship__c` record for every relationship you create (e.g., creating "Contact A is Spouse of Contact B" also creates "Contact B is Spouse of Contact A"). When you delete one relationship record, NPSP's automation deletes the mirror as well. If a bulk delete operation targets both records in a mirrored pair, the automation attempts to delete an already-deleted record, causing a DML exception or a double-count on the delete batch's error tally.

**When it occurs:** Bulk data cleanup using Data Loader or Apex when both the primary and mirror relationship records are included in the delete list — which happens naturally if you export all `npe4__Relationship__c` records for a contact and then delete all exported IDs.

**How to avoid:** When bulk-deleting relationship records, filter your delete list to include only records where `npe4__Type__c` matches one direction (e.g., the "primary" direction), or where `npe4__ReciprocalRelationship__c` is null. Let NPSP automation handle deletion of the mirror. Alternatively, disable NPSP's Relationships trigger temporarily — but this requires understanding the full impact on relationship data integrity.

---

## Gotcha 5: Setting npe5__Primary__c Directly in DML Triggers NPSP Affiliation Automation

**What happens:** `npe5__Affiliation__c` has a `npe5__Primary__c` checkbox field that marks a contact's primary organizational affiliation. NPSP automation monitors this field and, when it is set to true on one affiliation, automatically sets it to false on all other affiliations for the same Contact. If a bulk data load sets `npe5__Primary__c = true` on multiple affiliations for the same Contact in the same transaction, NPSP's trigger fires for each record and produces conflicting updates, often resulting in the wrong affiliation being marked primary or a trigger recursion error.

**When it occurs:** Data migrations that import affiliation records with `npe5__Primary__c` set directly; integrations that sync contact-organization relationships from an external system and include the primary flag.

**How to avoid:** During bulk affiliation imports, set `npe5__Primary__c = false` for all records. After the load completes, set the primary flag on one record at a time through the UI or in a separate, single-record Apex update with NPSP's trigger context checked. If using Data Loader for the primary flag update, process no more than one record per Contact per batch to avoid trigger conflicts.
