# Gotchas — Clinical Data Quality

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Clinical Records Are NOT Reparented on Person Account Merge — They Become Orphaned

**What happens:** When two Person Account records are merged in Health Cloud, the platform's standard merge reparenting logic does NOT move Health Cloud clinical objects (EpisodeOfCare, PatientMedication, ClinicalEncounter, CareObservation, CoveredBenefit, and similar objects) to the winning Account. These records remain associated with the losing (deleted) Account ID and become orphaned. They no longer appear on the winning patient's Health Cloud timeline, care plan, or clinical summary components. The patient's medical history is silently incomplete.

**When it occurs:** Every Person Account merge in a Health Cloud org where clinical records exist on the losing Account — unless a pre-merge reassignment step has explicitly moved those records first.

**How to avoid:** Before invoking the merge DML (whether through UI, Apex, or API), run a pre-merge Apex batch that queries each clinical object for records where the patient lookup equals the losing Account ID and updates them to point to the winning Account ID. Only after this batch completes with zero errors is it safe to execute the merge. See references/examples.md for a complete implementation.

---

## Gotcha 2: Person Account Merge Is Two-At-A-Time Only — There Is No Bulk Merge API

**What happens:** The standard Salesforce Account merge operation — whether triggered from the UI via "Merge Accounts" or invoked via Apex `merge masterAccount duplicateAccount` — accepts exactly one master record and one duplicate record per call. There is no bulk merge endpoint or API that accepts a list of duplicate pairs. An Apex attempt to merge three records in one statement (`merge master new List<Account>{dup1, dup2}`) compiles but throws a runtime limit error at execution. Bulk deduplication projects that skip this constraint end up with failed merges, partial data states, or governor limit exceptions.

**When it occurs:** Any deduplication project involving more than a handful of duplicate patient pairs, or any automation that attempts to batch-merge accounts outside a carefully written Apex Batch pattern.

**How to avoid:** Design all bulk merge orchestration as Apex Batch jobs that process one duplicate pair per `execute` call. Pair the merge DML with a governor-limit-safe batch size of 1 record per execute chunk (batchSize = 1) to ensure each merge completes cleanly before the next begins. Pre-merge clinical reassignment can use a larger batch size since it is standard DML, not merge DML.

---

## Gotcha 3: No Native MPI — Standard Duplicate Rules Are Insufficient for Enterprise-Scale Patient Identity

**What happens:** Health Cloud ships with no native Master Patient Index. Organizations that rely exclusively on standard Salesforce Duplicate Rules and Matching Rules for patient deduplication discover two failure modes at scale: (1) field-level fuzzy matching produces high false-positive rates when patient data comes from multiple source systems with inconsistent formatting, and (2) there is no cross-system record linkage — the Duplicate Rule can only compare records already in Salesforce, not resolve identity against external EMR, EHR, or claims systems. Enterprise healthcare organizations end up with thousands of undetected or incorrectly merged patient records.

**When it occurs:** Any Health Cloud implementation that receives patient data from more than one source system, or that has a patient population exceeding tens of thousands of records where intake data quality is variable.

**How to avoid:** For enterprise or multi-source deployments, evaluate a third-party MPI or MDM ISV solution (such as ReltioConnect for Salesforce, Veeva Network, or Informatica MDM for Salesforce Health Cloud) that performs probabilistic record linkage, survivorship rules, and cross-system identity resolution before records reach Salesforce. Native Duplicate Rules remain useful as a last-line-of-defense catch for records that slip through, but they cannot replace a dedicated MPI for complex healthcare identity scenarios.

---

## Gotcha 4: Duplicate Rules on the Contact Object Do Not Apply to Person Accounts

**What happens:** A practitioner creates a Duplicate Rule and Matching Rule targeting the Contact object, expecting it to catch duplicate Person Account patients. It has no effect on Person Accounts. Person Accounts have a system-managed underlying Contact record, but deduplication for Person Accounts runs against the Account object — not the underlying Contact. The Contact-scoped rule fires only for standalone Contacts, not for Person Account patients.

**When it occurs:** When an admin or developer unfamiliar with Person Account internals sets up deduplication by analogy with standard Contact deduplication workflows.

**How to avoid:** Always create Duplicate Rules and Matching Rules on the **Account** object for Person Account patient deduplication. Add a filter condition `IsPersonAccount = true` on the Duplicate Rule to scope it to patient records only and avoid matching against business account records.

---

## Gotcha 5: HIPAA Audit Considerations Are Not Addressed by Standard Duplicate Rules

**What happens:** Standard Duplicate Rules generate a DuplicateRecordItem and DuplicateRecordSet when a potential duplicate is flagged, but they produce no HIPAA-relevant audit trail. The duplicate alert does not log which user reviewed the match, what decision was made (merge vs. not-a-duplicate), or when the resolution occurred. In a HIPAA-regulated environment, patient record merge and deduplication decisions are subject to audit requirements — who touched which patient record and why. Relying on Duplicate Rules alone leaves a compliance gap.

**When it occurs:** Any Health Cloud deployment subject to HIPAA or similar healthcare data regulations, particularly where patient identity merges are performed by clinical staff.

**How to avoid:** Augment the deduplication workflow with a merge decision audit object (custom or leveraging Salesforce Shield Platform Encryption + Field Audit Trail) that captures: the reviewer's User ID, the timestamp of the merge decision, the losing Account ID, the winning Account ID, and the rationale. This is a process design requirement, not something Duplicate Rules provide automatically.
