# Well-Architected Notes — Data Skew and Sharing Performance

## Relevant Pillars

- **Reliability** — Data skew directly causes sharing recalculation failures, lock errors, and inconsistent access state. Eliminating skew before it accumulates is a reliability investment: operations that should be fast and deterministic remain so at scale.
- **Scalability** — Sharing recalculation cost grows non-linearly with record concentration. A pattern that works at 1,000 records may cause multi-hour background jobs at 100,000 records. Skew mitigation is fundamentally a scalability concern.
- **Security** — While this skill is not about security design (see sharing-and-visibility), data skew can leave sharing in an inconsistent state after a failed recalculation. Implicit sharing scans that are too slow to complete can temporarily expose incorrect access, making skew a security risk as well as a performance risk.
- **Operational Excellence** — Skew-driven lock errors are frequently misdiagnosed as integration bugs or infrastructure problems. Understanding the root cause reduces meantime-to-resolution and prevents recurring incidents.

## Architectural Tradeoffs

**Distributing ownership vs. simplifying integration:** Parking all imported records under one user simplifies integration design (no assignment logic required), but creates a time bomb. The more records accumulate, the higher the cost of any future role or group change for that user. The correct tradeoff is to build assignment logic early, before skew becomes a remediation project.

**"Controlled by Parent" vs. independent child sharing:** Configuring a child object as "Controlled by Parent" eliminates implicit sharing overhead entirely but permanently removes the ability to grant independent access to individual child records. This is the right choice for tightly-coupled parent-child models (e.g., Order Items under an Order) and the wrong choice for loosely-coupled models where child records may need to be shared independently (e.g., Contacts that might be shared with partners).

**Single large parent vs. segmented parents:** A single catch-all account is easy to manage initially but creates irreversible implicit sharing scan costs. Segmented parents are slightly more complex to maintain but scale indefinitely.

## Anti-Patterns

1. **The catch-all parking-lot account** — Creating a single Account to hold all unassociated Contacts, Leads, or Cases. Easy at import time, expensive as the org grows. Results in O(n) scans on every access change where n is the total children. Replace with multiple segmented accounts or "Controlled by Parent" OWD.

2. **The integration-user owner** — Routing all records from an external system through one service account user to keep integration logic simple. At 10,000+ records, this user becomes the most dangerous node in the role hierarchy. Any role or group change for this user fans out across all owned records. Distribute across queues or multiple service users from the start.

3. **Ignoring skew until it becomes a crisis** — Skew is often invisible until a major operation (end-of-quarter realignment, large import, org restructure) reveals it. By then, remediation requires batch re-parenting or re-assignment under production conditions, which itself can trigger the recalculation problems it is trying to fix. Run quarterly record count reports grouped by owner and by parent to catch accumulation early.

## Official Sources Used

- Designing Record Access for Enterprise Scale (Salesforce Architects) — primary source for ownership skew threshold (10,000 records), parent-child skew threshold (10,000 children), group membership locking behavior, granular locking concurrency table, and all mitigation recommendations. Stored locally at `knowledge/imports/draes.md`.
  URL: https://architect.salesforce.com/design/record-access-for-enterprise-scale
- Best Practices for Deployments with Large Data Volumes (Summer '26 PDF, read in full) — source for the ownership ceiling "Avoid having any user own more than 10,000 records" (L1033); the parent ceiling and dummy-account remedy "Distribute child records so that no parent has more than 10,000 child records" (L1052–L1056); the load ordering used in the Recommended Workflow and `references/metadata-examples.md` § 7 — roles, record data, groups and queues, then sharing rules one at a time (L852–L900); the `ParentId` batch-grouping instruction (L894–L896); Defer Sharing Calculation as a feature (L595–L604); the list of platform-indexed fields including foreign keys (L400–L409); the standard (30%/15%) and custom (10%/5%) index selectivity thresholds and the AND/OR/LIKE rules (L463–L481); null exclusion from index tables (L436); `GROUP BY ROLLUP` as the distribution method (L248); the related-list rendering case study and the Enable Separate Loading of Related Lists mitigation (L1173–L1177).
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/ldv.pdf

- Metadata API Developer Guide (Summer '26 PDF) — source for every XML block in `references/metadata-examples.md` and for Gotchas 6, 8, and 10: `SharingSettings` `deferGroupMembership` / `deferSharingRules`, the Support-case precondition, and the resume-recalculates-both behavior (L126981–L127167); `Group` fields and "Members of the public group aren't migrated when you deploy the group type" (L79612–L79676); `SharingRules` / `SharingCriteriaRule` / `SharingOwnerRule` / `SharedTo` shapes, the immutable `includeRecordsOwnedByAll`, and the no-manual-rule-deploy limitation (L129018–L129535); `CustomField.externalId` and `unique` setting `isIndexed` (L43402, L43451, L43702); `CustomObject.sharingModel` and the `SharingModel` enumeration including `ControlledByParent` (L42250, L45801); `CustomIndex` (L41099–L41147).
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

- Bulk API and Bulk API 2.0 Developer Guide (Summer '26 PDF) — source for Gotchas 7 and 11 and for Pattern 3's correction: Bulk API 2.0's `concurrencyMode` is "Reserved for future use… Currently only parallel mode is supported" (L3050–L3054, L3214–L3219); Bulk API v1 serial mode semantics and the "avoid serial unless you can't reorganize your batches" preference (L4983–L4995); the four lock-prone operations, creating users / updating ownership for records with private sharing / updating user roles / updating territory hierarchies (L2695–L2699, L5010–L5015); sorting records by parent to minimize lock contention (L2701–L2707); the 100-record lock threshold, 10 reprocess attempts, and partial success inside a failed batch (L5002–L5008); `TooManyLockFailure` (L2790–L2792); PK chunking thresholds and the Sharing/History parent header (L7143–L7185, L7312–L7314).
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
- Large Data Volumes: Design Your Data Model (Trailhead) — source for the data skew definition ("Data skew happens when more than 10,000 child records are associated with the same parent record within an org") and for the three named skew types: account data skew, ownership skew, and lookup skew.
  URL: https://trailhead.salesforce.com/content/learn/modules/large-data-volumes/design-your-data-model
- Managing Lookup Skew in Salesforce to Avoid Record Lock Exceptions (Salesforce Developers engineering blog) — source for lookup-field target-record locking, lock duration across custom code execution, and the distribute-the-skew vs. picklist-substitution mitigations including the "additional fields and other data" precondition.
  URL: https://developer.salesforce.com/blogs/engineering/2013/04/managing-lookup-skew-to-avoid-record-lock-exceptions
- SOAP API Developer Guide — Core Data Types Used in API Calls (StatusCode reference) — source for the exact `UNABLE_TO_LOCK_ROW` status code, its "deadlock or timeout condition has been detected" semantics, and whole-batch failure behavior.
  URL: https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm
- Salesforce Well-Architected Overview — architecture quality framing for reliability and scalability pillars.
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — sObject relationship semantics (Lookup vs Master-Detail, Controlled by Parent OWD behavior).
  URL: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm

- Object Reference for the Salesforce Platform (Summer '26 PDF) — source for the `AccountShare.RowCause` value `ImplicitParent` and its definition, used in the Core Concepts implicit-sharing chain and the post-deploy verification query (L17717–L17743); the compression of `ImplicitParent` / `Manual` / `Owner` share rows into one record at the highest access level, which is why counting share rows understates the work done (L17816); `Group.Type` values and the create-time restriction to `Personal`, `Regular`, `Queue` (L154307–L154362); `GroupMember` as the object holding membership, and the `DeveloperName` performance note behind Gotcha 8 (L154208, L154390).
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

- Salesforce App Limits Cheat Sheet (Summer '26 PDF) — source for the Bulk batch allocation of 15,000 batches per rolling 24-hour period shared between Bulk API and Bulk API 2.0, which bounds how finely a skew remediation can be batched (L737).
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
