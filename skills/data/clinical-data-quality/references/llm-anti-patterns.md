# LLM Anti-Patterns — Clinical Data Quality

Common mistakes AI coding assistants make when generating or advising on clinical data quality in Health Cloud.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Clinical Records Reparent Automatically on Person Account Merge

**What the LLM generates:** Instructions or code that execute the Account merge DML first and then mention clinical records as an afterthought — or omit them entirely — under the assumption that Salesforce's standard merge reparenting logic will move EpisodeOfCare, PatientMedication, and ClinicalEncounter to the winning account automatically.

**Why it happens:** LLMs learn from general Salesforce merge documentation that describes standard related records being reparented on merge (Opportunities, Cases, etc.). Health Cloud clinical objects are not in the standard merge reparenting set, but this exception is not prominent in training data, so models generalize incorrectly.

**Correct pattern:**

```text
CORRECT ORDER:
1. Run PreMergePatientReassignment batch (reassign all clinical object lookups from losingId to winningId)
2. Confirm batch completes with zero errors
3. Execute: merge masterAccount duplicateAccount;
4. Run post-merge audit queries to confirm zero orphaned records

DO NOT merge first and reassign second — the losing Account ID is deleted after merge.
```

**Detection hint:** Flag any response that places `merge masterAccount duplicateAccount;` or instructions to "merge the accounts" BEFORE a step that explicitly handles EpisodeOfCare, PatientMedication, ClinicalEncounter reassignment. If clinical objects are not mentioned at all in a Health Cloud merge workflow, that is also a signal this anti-pattern is present.

---

## Anti-Pattern 2: Using the Contact Merge Flow for Person Account Patients

**What the LLM generates:** Instructions to navigate to Contacts, find the duplicate contact records for the patients, and use the "Merge Contacts" button or the Contact merge API to combine them.

**Why it happens:** Person Accounts have an underlying Contact record, and LLMs trained on generic Salesforce deduplication content often conflate Person Account patients with standard Contacts. The Contact merge path is the standard deduplication path for non-Person-Account orgs.

**Correct pattern:**

```text
Person Accounts must be merged via the Account merge path:
- UI: Account record > Related > (find duplicate) > Merge Accounts button
- Apex: merge masterAccountRecord duplicateAccountRecord;

Do NOT use:
- The "Merge Contacts" UI path
- Database.merge() on Contact SObjects for Person Account patients
- Any Contact-to-Contact merge API on records that have IsPersonAccount = true on their parent Account
```

**Detection hint:** Search the generated response for "Merge Contacts", `merge masterContact`, or any mention of the Contact merge button in a Health Cloud context. If present and the subject is patient record deduplication, flag as incorrect.

---

## Anti-Pattern 3: Claiming Health Cloud Has a Native Master Patient Index (MPI)

**What the LLM generates:** Statements such as "Health Cloud includes a built-in Master Patient Index" or "enable the MPI feature in Health Cloud Setup" or "use the Patient Identity Resolution component."

**Why it happens:** Healthcare IT literature frequently references MPI as a requirement for health cloud platforms, and LLMs may interpolate this as a feature that Salesforce Health Cloud ships with, when in fact it does not. There is no MPI feature in Salesforce Health Cloud as of Spring '25.

**Correct pattern:**

```text
Health Cloud has NO native MPI.

Duplicate detection uses standard Salesforce Duplicate Rules + Matching Rules on the Account object.
For enterprise-scale probabilistic matching and cross-system record linkage, a third-party ISV is required:
- ReltioConnect for Salesforce
- Veeva Network
- Informatica MDM for Salesforce Health Cloud
```

**Detection hint:** Search for phrases like "native MPI", "built-in Master Patient Index", "Health Cloud MPI", "Patient Identity Resolution (PIR)", or "enable MPI" in any response about Health Cloud deduplication. All such claims should be challenged against official documentation.

---

## Anti-Pattern 4: Missing the Pre-Merge Clinical Record Reassignment Step in Bulk Merge Designs

**What the LLM generates:** A bulk merge Apex batch that queries duplicate Account pairs and calls `merge` in the `execute` method without a prior reassignment step for clinical objects. The batch may even call merge with a batch size greater than 1, which is unsupported for merge DML.

**Why it happens:** Bulk merge patterns in generic Salesforce examples focus on the merge DML itself and the two-at-a-time constraint. Clinical object reassignment is a Health Cloud-specific requirement that does not appear in generic merge templates.

**Correct pattern:**

```apex
// WRONG — merge without pre-reassignment
public void execute(Database.BatchableContext bc, List<AccountMergePair__c> pairs) {
    for (AccountMergePair__c pair : pairs) {
        Account master = new Account(Id = pair.MasterId__c);
        Account dup    = new Account(Id = pair.DuplicateId__c);
        merge master dup; // clinical records will be orphaned
    }
}

// CORRECT — pre-reassignment then merge (separate batch jobs chained)
// Step 1: PreMergePatientReassignment batch (one pair at a time)
// Step 2: Only after Step 1 completes — MergePatientAccounts batch
public void execute(Database.BatchableContext bc, List<AccountMergePair__c> pairs) {
    for (AccountMergePair__c pair : pairs) {
        // Pre-reassignment must have already completed for this pair
        Account master = new Account(Id = pair.MasterId__c);
        Account dup    = new Account(Id = pair.DuplicateId__c);
        merge master dup;
    }
}
```

**Detection hint:** If a bulk merge batch response does not include a chained or preceding reassignment step for EpisodeOfCare, PatientMedication, ClinicalEncounter, and similar Health Cloud clinical objects, the design is incomplete. Flag responses that jump directly to `merge` without a clinical record reassignment gate.

---

## Anti-Pattern 5: Treating Standard Duplicate Rules as HIPAA-Sufficient Without Audit Logging

**What the LLM generates:** A deduplication design that configures Duplicate Rules and Matching Rules on Account and presents this as a complete HIPAA-compliant patient identity management solution, with no mention of merge decision audit trails, reviewer identity capture, or PHI handling controls.

**Why it happens:** HIPAA compliance requirements are complex and context-dependent. LLMs often conflate "deduplication is configured" with "deduplication is compliant." Standard Duplicate Rules do create DuplicateRecordSet and DuplicateRecordItem records but do not capture who reviewed a match, what decision was made, or when — all of which are relevant to HIPAA audit requirements for PHI access and modification.

**Correct pattern:**

```text
Standard Duplicate Rules provide:
  - Detection of potential duplicate patients at intake
  - DuplicateRecordSet / DuplicateRecordItem audit objects showing which records matched

Standard Duplicate Rules do NOT provide:
  - Reviewer identity (who reviewed the match)
  - Decision rationale (merge vs. not-a-duplicate)
  - Merge event timestamp with user attribution
  - HIPAA-compliant audit trail for patient record modification

For HIPAA compliance, augment with:
  - A custom Merge Audit object capturing: User ID, timestamp, losingAccountId, winningAccountId, decision reason
  - Salesforce Shield Field Audit Trail on clinical objects if required
  - A review workflow that gates merge execution on documented approval
```

**Detection hint:** Any deduplication design response for a Health Cloud (healthcare) org that mentions HIPAA or PHI but does not address audit trail requirements for merge decisions should be flagged as incomplete. Look for whether the response only mentions Duplicate Rules without any custom audit logging layer.
