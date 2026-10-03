# Gotchas — High Volume Sales Data Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "LDV guide" means Best Practices for Deployments with Large Data Volumes (Summer '26 PDF).

## Gotcha 1: One Owner Above 10,000 Records Turns Every Sharing Change Into A Long Job

**What happens:** An integration user or a "house" user owns hundreds of thousands of Accounts or Opportunities. Each sharing rule change, role change, or territory realignment touching that owner's records runs long and queues other sharing work behind it. UNVERIFIED (2026-10-03): the earlier claim in this skill that recalculation cost grows "5x" from 10,000 to 50,000 records is not in a fetched source.

**When it occurs:** When integration-created records default to the integration user, or when unassigned records are parked on one user.

**How to avoid:** Keep every user, queue, and the combined members of any single role or public group below 10,000 owned records per object. Reassign integration-created records to territory users or queues at creation. If a data-owning user must keep a large set, leave that user without a role, or place it in a distinct role at the top of the hierarchy and do not change that role casually. For large one-time ownership or sharing changes, use the defer sharing calculation permission to suspend group membership and sharing rule calculation and resume it in a maintenance window.

**Source:** LDV guide, Best Practices > General: "Avoid having any user own more than 10,000 records"; Defer Sharing Calculation ("suspend and resume sharing calculations ... group membership calculation and sharing rule calculation"). Salesforce Well-Architected, Trusted > Reliable, Data Volume: no single user or queue, nor all members of a single role or public group, should own more than 10,000 records from the same object; role placement for data-owning users.

---

## Gotcha 2: One Account With Too Many Children Causes Lock Contention And Slow Related Lists

**What happens:** A single Account carries tens of thousands of Opportunities, Contacts, or custom child records. Parallel loads and batch jobs that update children contend for the parent lock, and related lists on that Account load slowly.

**When it occurs:** With catch-all Accounts ("Unknown Customer", "Web Leads"), and when a B2C model is forced onto Account-Contact.

**How to avoid:** Distribute children so no parent exceeds 10,000 child records, for example across several placeholder Accounts. Sort bulk loads by parent Id so one batch does not update the same parent from parallel threads.

**Source:** LDV guide, Best Practices > General: "Distribute child records so that no parent has more than 10,000 child records. For example, in a deployment that has many contacts but does not use accounts, set up several dummy accounts and distribute the contacts among them"; case study on data skew delaying a related list.

---

## Gotcha 3: The Selectivity Thresholds Are Tiered, And Standard And Custom Indexes Differ

**What happens:** A team computes selectivity with a flat "10% for standard, 5% for custom" rule and either requests indexes it does not need or ships queries that are not selective. The documented thresholds are tiered: a standard index is used when the filter matches less than 30% of the first million records and less than 15% of additional records; a custom index when it matches less than 10% of the first million and less than 5% of additional records. This corrects the flat percentages earlier versions of this skill gave.

**When it occurs:** When sizing pipeline report filters and Apex queries on multi-million-row Opportunity tables.

**How to avoid:** Compute the threshold for the actual row count. For 5 million Opportunities, a custom-indexed filter must match 300,000 or fewer rows; a standard-indexed filter 900,000 or fewer. For AND conditions, each index is used unless it returns more than 20% of the object's records; for OR, every field must be indexed. Confirm with the Query Plan tool.

**Source:** LDV guide, Indexes > Standard and Custom Indexed Fields (thresholds and worked examples) and the AND, OR, and LIKE rules.

---

## Gotcha 4: Custom Indexes Are Metadata You Can Track, And They Follow Production Into Sandboxes

**What happens:** Earlier versions of this skill said custom indexes are Support-only, not version-controlled, and can silently disappear on sandbox refresh. The documentation says otherwise: custom indexes can be created by contacting Support "or by deploying a custom index XML file via the Metadata API" (the `CustomIndex` type, API 50.0+, whose use still requires contacting Support), and Support-created indexes in production "are copied to all sandboxes that you create from that production environment." External ID fields create an index automatically.

**When it occurs:** When teams keep an informal index register and re-request indexes after every refresh.

**How to avoid:** Track indexes as `CustomIndex` metadata where Support has enabled it, keep the Support case numbers in the register, and use External ID on Auto Number, Email, Number, or Text fields where a unique business key exists. Remember index tables exclude null values by default; ask Support to include nulls if the filter needs them.

**Source:** LDV guide, Indexes (creation paths, sandbox copy note, External IDs, null rows); Metadata API Developer Guide v67.0, CustomIndex (`allowNullValues`, `booleanIndexedValue`; "contact Salesforce Customer Support").

---

## Gotcha 5: Skinny Tables Take Encrypted Fields But Not Formulas Or Fields From Other Objects

**What happens:** A skinny table is requested for a wide Opportunity object. Report columns that are formulas, or that reach across to Account, cannot be included, so the report still joins. Earlier versions of this skill also said encrypted fields are excluded; the LDV guide says "Skinny tables and skinny indexes can also contain encrypted data."

**When it occurs:** When the slowest pipeline reports depend on formula fields such as weighted amount or days in stage, or on parent-object fields.

**How to avoid:** List the report's columns against the allowed types (Checkbox, Currency, Date, Date and time, Email, Number, Percent, Phone, multi-select Picklist, Text, Text area, Text area (long), URL). Replace critical formulas with stored values maintained by Flow so they qualify. Plan within the 200-column maximum. Expect the skinny table in Full sandboxes only; other sandbox types need a Support request.

**Source:** LDV guide, Skinny Tables (eligible objects: custom objects, Account, Contact, Opportunity, Lead, Case; allowed field types; encrypted data; considerations: 200 columns, no fields from other objects, Full sandbox copy).

---

## Gotcha 6: Big Objects Answer Synchronous SOQL, But Only Along The Index

**What happens:** Earlier versions of this skill said big objects support only Async SOQL. The current guides document standard SOQL against big objects, through SOQL, Bulk, Chatter, and SOAP APIs. The constraint is the query shape: filters must use the index fields in index order without gaps, only the last filtered field may use `=`, `<`, `>`, `<=`, `>=`, or `IN`, earlier fields only `=`, and `!=`, `LIKE`, `NOT IN`, `EXCLUDES`, and `INCLUDES` are not supported. Aggregate functions such as `COUNT()` are not supported.

**When it occurs:** When an archive lookup page filters on a field that is not first in the index, or when a reconciliation step tries `SELECT COUNT()` on the archive.

**How to avoid:** Design the index for the lookups users will make (for example `AccountId`, then `CloseDate`, then Opportunity Id). Count rows with batch Apex, as the Big Objects guide shows. For reporting, extract a subset into a reportable custom object on a schedule.

**Source:** Big Objects Implementation Guide v66.0 (Spring '26), API Support for Big Objects, Aggregate Queries, View Big Object Data in Reports and Dashboards (local corpus `knowledge/imports/salesforce-big-objects-guide.md`); SOQL and SOSL Reference v66.0, SOQL Object Limits and Limitations, Big objects (`knowledge/imports/salesforce-soql-sosl.md`).

---

## Gotcha 7: Archiving Opportunities To A Big Object Drops Record-Level Sharing And Encryption

**What happens:** Closed Opportunities move to a big object. Any user with read access to the big object can now read every archived deal, because big objects "support only object and field permissions, not regular or standard sharing rules." Encrypted source fields land in clear text, because "big objects don't support encryption."

**When it occurs:** In orgs with a Private Opportunity model, territory-based visibility, or Shield Platform Encryption on Amount or custom fields.

**How to avoid:** Grant big object access to a small reporting group only, and serve reps archived data through a summary custom object that keeps normal sharing. Exclude or tokenize encrypted fields before archiving, or keep those records out of the archive. Record both decisions in the archival design.

**Source:** Big Objects Implementation Guide v66.0, Overview (behavioral constraints) and Considerations When Using Big Objects ("Big objects don't support encryption. If you archive encrypted data from a standard or custom object, it's stored as clear text on the big object").

---

## Gotcha 8: `insertImmediate()` Fails Quietly And Writes Are Idempotent

**What happens:** The archival batch logs success, but some rows never reached the big object. `Database.insertImmediate()` does not throw on a failed insert; it returns `SaveResult` objects with errors. Re-running the batch does not duplicate rows that match an existing index exactly, but a row with the same index and different data behaves like an upsert.

**When it occurs:** When the archival batch ignores the returned results, then hard-deletes the source Opportunities.

**How to avoid:** Inspect every `SaveResult`, write failures to a log object, and gate the hard-delete step on zero failures for the scope. Trim index field values before insert, because SOQL strips leading and trailing white space when matching.

**Source:** Big Objects Implementation Guide v66.0, Considerations for Populating Big Objects with Apex; Overview (identical record inserted multiple times creates a single record).

---

## Gotcha 9: Report Row Display Limits Are Not The Same As Wrong Totals

**What happens:** A pipeline report shows a capped number of detail rows and managers assume the totals are truncated too, or the reverse. UNVERIFIED (2026-10-03): the 2,000-detail-row display limit, and whether summary totals and dashboard components include rows beyond it, are documented in Salesforce Help only.

**When it occurs:** On "all open pipeline" reports without date or stage filters on large Opportunity tables.

**How to avoid:** Check a report's grand total against `SELECT SUM(Amount) FROM Opportunity WHERE ...` with the same filters before trusting it at scale. Add selective, indexed date-range filters. Use reporting snapshots or CRM Analytics datasets for executive views of the full table.

**Source:** UNVERIFIED as noted; the verification query uses standard SOQL aggregates.

---

## Gotcha 10: Mass Owner Changes Can Strip Account Teams Unless Data Loader Is Configured

**What happens:** The skew fix reassigns hundreds of thousands of Accounts, and account teams built over years disappear from the reassigned records. Data Loader keeps account teams on mass owner updates only when explicitly configured.

**When it occurs:** During ownership redistribution with Data Loader's default settings, and with the Bulk API enabled.

**How to avoid:** Use Data Loader 56.0.3 or later, set `sfdc.useBulkApi=false` and `process.keepAccountTeam=true` in `config.properties`, and split the load so every row in a file has the same current owner and the same new owner, because mixed values make the operation fail. Test on a full sandbox and compare `AccountTeamMember` counts before and after.

**Source:** Salesforce Data Loader Guide (Summer '26), Keep Account Teams: "To keep Account Teams intact when mass-updating account owners", the version, the two properties, and the note that the CSV must have the same current owner and the same new owner on all records.
