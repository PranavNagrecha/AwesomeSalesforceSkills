# Examples: DataRaptor Load and Extract

## Example 1: Extracting an Account With Its Contacts

**Context:** An OmniScript needs to show an Account's details and its Contacts when an advisor opens a customer record, in one server call.

**Problem:** Two separate Extracts mean two Integration Procedure steps and more latency.

**Solution:** One standard Extract with two extract steps.

```text
Extract tab
  Step 1  Object: Account   Extract Output Path: Account
          Filter: Id  =  AccountId        (input parameter from the OmniScript)
  Step 2  Object: Contact   Extract Output Path: Contact
          Filter: AccountId  =  Account:Id   (UNVERIFIED (2026-10-03) cross-step form)

Output tab
  Account:Name         ->  Account:Name
  Account:Phone        ->  Account:Phone
  Contact:LastName     ->  Account:Contacts:LastName
  Contact:Email        ->  Account:Contacts:Email

Options tab
  Check field level security: on (restricted users call this Extract)
  Platform cache: Session Cache, Time to Live 5 minutes

Preview tab
  Key: AccountId   Value: 001XXXXXXXXXXXXXXX
```

**Why it works:** The Extract tab defines objects and filters, not SOQL. The Output tab nests the Contact step under the Account node, so the OmniScript receives one JSON structure. The FLS option keeps hidden fields out of the response.

---

## Example 2: Upsert for an External Customer Feed

**Context:** An external system sends customer records. Some already exist in Salesforce (same `External_Customer_ID__c`), others are new.

**Problem:** An insert-only design duplicates existing customers; an update-only design drops new ones.

**Solution:** A Load on `Contact` with an Upsert Key.

```text
Objects tab
  1  Contact

Fields tab (Input JSON Path -> Domain Object Field)
  customer:externalId   ->  Contact.External_Customer_ID__c   [Upsert Key] [Is Required For Upsert]
  customer:firstName    ->  Contact.FirstName
  customer:lastName     ->  Contact.LastName                  [Is Required For Upsert]
  customer:email        ->  Contact.Email

Load settings
  rollbackOnError: true      (one feed record is one transaction)
  errorIgnored:    false
```

When the incoming `externalId` matches exactly one Contact, the Load updates it. When nothing matches, it creates a Contact. When `externalId` or `lastName` is empty, the Load skips that record, so the Integration Procedure should count and report skips. The Upsert Key doesn't have to be an External ID field; it has to match uniquely.

The deployable `OmniDataTransform` XML for both examples is in [metadata-examples.md](metadata-examples.md).

---

## Anti-Pattern: Using DataRaptor Load for Bulk Record Import

**What practitioners do:** Configure a DataRaptor Load called from an Integration Procedure looping over a large JSON array to insert hundreds of records.

**What goes wrong:** Data Mapper Load writes through **platform DML, not the Bulk API**, so the whole write is bounded by the calling transaction's governor limits, 150 DML statements and 10,000 DML rows per transaction. Driving it from a loop in an Integration Procedure is what makes this bite: each iteration issues its own DML, so the transaction dies at the **151st iteration** with `Too many DML statements`, long before the row limit is anywhere near reached.

Two things worth being precise about, because they are commonly stated wrongly:

- The binding limit for a loop-driven Load is the **150-statement** ceiling, not the 10,000-row one. Any account of this failure that has a 500-record load consuming "500 DML statements" before failing is arithmetically inconsistent, it would have failed at 151.
- Whether Data Mapper Load internally issues one DML per record for a *single* invocation carrying a 500-element array is **not something to assert without checking**. A genuinely bulkified 500-row write is comfortably inside both limits. Confirm the current batching behaviour against the Omnistudio Data Mapper Load documentation before quoting a per-record figure; the safe and sufficient statement is that Load is platform DML rather than Bulk API, and therefore unsuitable for high-volume writes.

A separate behavior also matters: the `OmniDataTransform` metadata has `synchronousProcessThreshold` ("If it's more than this number, then it uses a batch job") and `processSuperBulk`. Above the threshold the Load is no longer a synchronous call at all.

**Correct approach:** DataRaptor Load is designed for conversational, single-record or small-set operations within an OmniScript interaction. For bulk imports, use Bulk API 2.0 directly, Apex Batch with Database.executeBatch, or a data tool like Data Loader, outside the OmniStudio context.
