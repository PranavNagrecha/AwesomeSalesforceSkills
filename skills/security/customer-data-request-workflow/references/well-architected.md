# Well-Architected Notes — Customer Data Subject Request (DSR) Workflow

## Relevant Pillars

- **Security** — Primary pillar, with an unusual shape: the goal is *destroying*
  data, and the risks run in both directions. Under-erasure leaves residual copies a
  regulator will find. Over-erasure destroys records the business is legally required
  to keep, irreversibly. And the evidence layer is itself a risk — an audit table
  that records the old values of erased fields is a second copy of the data the
  workflow was built to remove. Log a one-way hash, never the value.

- **Operational Excellence** — The measure of this capability is not whether it can
  execute one request but whether it can execute the volume that arrives after an
  incident, inside the regulatory window, with evidence. That means measured
  per-object timings, an inventory that is regenerated rather than remembered, and a
  rehearsal against a synthetic subject in a full sandbox. It also means a named
  legal owner for the exceptions, because the residual-risk register is a legal
  artifact that engineering cannot author.

- **Reliability** — The workflow is irreversible and runs under a deadline, which is
  the worst combination for an untested process. Write the audit row before the DML so
  a failure mid-run leaves evidence of the attempt; make the whole run idempotent so a
  partial failure can be re-run without double-processing; and use
  `Database.emptyRecycleBin` explicitly, because a soft delete that looks successful
  is the most common false completion in this domain.

- **Performance** — Secondary but real. The regulatory window is generous per
  request and unforgiving under load, and the constraint is usually the manual steps —
  off-platform copies, legal review of exceptions, sandbox repetition — not the Apex.

## Architectural Trade-offs

**Privacy Center vs a custom workflow.** Privacy Center gives you `DsarPolicy` and
`DsarPolicyLog`, and the log is generated as a side effect of execution, so the
evidence cannot drift from what was actually done — which a hand-built audit object
can. Its fields cover the questions a regulator asks: who requested, when they
requested, when it completed, when the generated file is deleted, and whether the
subject downloaded it. The costs are the licence and the object-scoped policy model,
whose completeness is exactly the completeness of your object inventory. A custom
workflow costs build and maintenance and gives you total control over scope and
evidence; policy-as-Custom-Metadata keeps the compliance team able to change scope
without an Apex deploy.

**Deletion vs pseudonymisation.** Deletion is unambiguous and destroys referential
integrity — on Person Accounts it cascades into Orders, Cases, and Assets, or fails.
Pseudonymisation (null or redact the identifying fields, keep the record) satisfies
erasure under most interpretations, preserves the transactional history the business
needs, and leaves a record that can be pointed at in an audit. It also leaves a
record, which some interpretations reject. This is a **legal** position with a
technical implementation, not the reverse, and it must be signed off by whoever owns
the legal interpretation.

**Where the evidence lives.** Privacy Center's log is authoritative and coupled to
execution. A custom `DSR_Action__c` is portable, queryable, and reportable alongside
the rest of your compliance data — and is only as trustworthy as the discipline that
writes to it. Whichever you choose, the record must contain object, record Id, field,
action, timestamp, and a hash — and must not contain the value.

**Sandbox repetition vs masking on refresh.** Repeating each erasure in every
sandbox is exhaustive, auditable, and scales badly — N erasures per request, forever.
Masking on every refresh is one control that covers all future copies and does nothing
for copies already taken, which means it has to be in place before the requests start.
Masking is the sustainable answer and the migration to it is a project of its own.

**How much to automate.** Automating the relational half is straightforward and
removes the errors that matter. The free-text half, the off-platform copies, and the
legal exceptions resist automation and are where the wall-clock time goes. Automating
only the easy half and calling the workflow automated is how a process that meets the
deadline at one request per week fails at ten.

## Anti-Patterns

1. **Treating `ShouldForget` as the erasure.** It is a stored preference. Its value
   is as the anchor for the SLA clock and the audit trail; something else has to act.

2. **Scoping to Contact and Lead.** Build the relational half from
   `getChildRelationships()` and the rest from a fixed checklist — consent objects,
   free text, files, history, archive, and off-platform copies.

3. **Forgetting `FieldHistoryArchive`.** The record delete cascades to history but
   not to the archive, leaving the old values of the erased fields in a separate
   store. It is the easiest gap to prove in a rehearsal and the most commonly missed.

4. **Stopping at a soft delete.** Records in the Recycle Bin are restorable and still
   contain the data. Hard delete, then verify.

5. **Storing old values in the audit trail.** The evidence layer becomes a complete
   copy of what you erased. Hash it.

6. **Deleting Person Accounts.** Two objects in one record with transactional
   dependencies. Pseudonymise by default, and record the choice as a legal position.

7. **Ignoring sandboxes and off-platform copies.** "We deleted it in production" does
   not answer "where else is it."

8. **Promising complete erasure.** Setup Audit Trail, some platform-managed history,
   and data held under a competing legal obligation cannot be removed. Enumerate them
   during design and get a written position for each.

9. **One handler for access and erasure.** Different scope, direction, output, SLA,
   approval gate, and risk profile. Two workflows sharing an `Individual` record.

10. **Rehearsing in production.** The first execution is irreversible and is happening
    under a deadline. Rehearse in a full sandbox against a synthetic subject with data
    in every object on the inventory, then search for residuals as an admin.

## Official Sources Used

- Object Reference for the Salesforce Platform — Individual (`ShouldForget`, `SendIndividualData`, the Data Protection and Privacy enablement requirement, the community/portal exclusion, and the associated `IndividualChangeEvent`, `IndividualHistory`, `IndividualShare` objects) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_individual.htm
- Object Reference for the Salesforce Platform — DsarPolicy (`IsActive` defaulting to `false`, the `ReadAllData` / `PrivacyDataAccess` access rule, API 50.0 and later) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_dsarpolicy.htm
- Object Reference for the Salesforce Platform — DsarPolicyLog (requesting subject ID, request and completion timestamps, generated-file deletion and download timestamps, error field, and the acting employee/admin ID; API 51.0 and later for several fields) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_dsarpolicylog.htm
- Salesforce Help — Satisfy Customer Requests and Data Privacy Laws (Privacy Center) — https://help.salesforce.com/s/articleView?id=platform.privacy_center.htm&type=5
- Salesforce Help — Delete Data with Right to Be Forgotten Policies (policies are created at the object level) — https://help.salesforce.com/s/articleView?id=platform.right_to_be_forgotten.htm&type=5
- Salesforce Help — Create a Right to Be Forgotten Policy — https://help.salesforce.com/s/articleView?id=platform.rtbf_policies.htm&type=5
- Salesforce Help — Data Protection and Privacy — https://help.salesforce.com/s/articleView?id=platform.data_protection_and_privacy.htm&type=5
- Salesforce Help — Privacy Center and Data Governance Laws (GDPR and CCPA framing) — https://help.salesforce.com/s/articleView?id=platform.privacy_center_and_data_governance_laws.htm&type=5
- Salesforce Security Guide — Field Audit Trail (the `FieldHistoryArchive` delete-cascade exclusion, and the list of objects supporting history retention policies including Individuals and the consent objects) — https://help.salesforce.com/s/articleView?id=platform.field_audit_trail.htm&type=5
- Apex Developer Guide — Custom Metadata Types in Apex (`getAll()` costs no SOQL query) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_types.htm
- Apex Reference Guide — Crypto Class, `generateDigest(algorithmName, input)` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_restful_crypto.htm
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: regulatory deadlines. The commonly cited 30-day GDPR and 45-day
     CCPA windows are legal facts, not Salesforce behaviour, and were NOT
     verified against the regulations in this pass. One Salesforce Help summary
     encountered during research states you "must delete, archive, or de-identify
     the data subject's PII in your org within 30 days of their request", but
     Salesforce is not an authority on the regulation. Confirm the applicable
     deadline with legal counsel for each jurisdiction in scope. This package
     therefore avoids asserting a specific number of days. -->
<!-- UNVERIFIED: the literal API names of DsarPolicyLog fields. The Object
     Reference documents the SEMANTICS quoted above, but the fields are
     managed-package-namespaced and vary by Privacy Center version. Describe the
     object in the target org before writing any query into a runbook. -->
<!-- UNVERIFIED: whether ContentDocument / ContentVersion file BODIES are
     reachable by the deletion mechanisms described. File deletion is listed in
     the inventory checklist as a required scope item; the mechanism for erasing
     file content (as distinct from the ContentDocument record) was not verified
     in this pass. -->
<!-- RESOLVED 2026-08-14: the Contact-to-Individual traversal is now verified
     against the Object Reference and corrected in examples.md. Contact carries
     `IndividualId` (type reference, Nillable), whose Relationship Name is
     `Individual` and which Refers To `Individual` — a standard relationship, so
     no `__r` suffix. `ShouldForget` and `SendIndividualData` are fields of
     `Individual`, not of Contact. The previous `Contact.Individual__r` form did
     not compile. -->
