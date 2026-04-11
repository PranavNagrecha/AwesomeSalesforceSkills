# Gotchas — FSC Compliant Data Sharing API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: OWD Public Read/Write Silently Blocks CDS Share Row Creation

**What happens:** An `AccountParticipant` insert succeeds without errors, and the participant record appears in the database, but no `AccountShare` row with `RowCause = 'CompliantDataSharing'` is ever created. Queries on `AccountShare` return zero CDS-managed rows.

**When it occurs:** When the target object's OWD is set to Public Read/Write. The CDS engine skips share row generation entirely because universal read/write access already covers every user — the platform treats participant records as no-ops in this configuration. This is most frequently encountered in sandboxes where an administrator changed OWD to Public Read/Write to simplify development or testing, forgetting that CDS will stop functioning.

**How to avoid:** Before troubleshooting missing CDS grants, always verify the OWD. Navigate to Setup > Sharing Settings and confirm the object is set to Private or Public Read Only. If changing OWD back to a restrictive setting, manually trigger a CDS recalculation or wait for the nightly job, because share rows are not retroactively created for existing participant records when OWD changes.

---

## Gotcha 2: Revoking Access Requires Deleting the Participant Record — Not the Share Row

**What happens:** An administrator or developer deletes an `AccountShare` row to revoke a user's CDS-managed access. The `AccountShare` row disappears. The user loses access temporarily. After the next CDS recalculation (triggered by an OWD change, org-level recalculation request, or nightly job), the `AccountShare` row reappears and the user regains access. The revocation appears to have worked but is not durable.

**When it occurs:** Any time a developer treats the `AccountShare` table as the control point for CDS access. This mistake also occurs when automated cleanup jobs delete share rows without touching the corresponding participant records.

**How to avoid:** Always revoke CDS access by deleting the `AccountParticipant` or `OpportunityParticipant` record. The CDS engine will then omit the share row on its next pass. Verify revocation by confirming the participant record no longer exists, not by checking the share row — the share row may persist briefly until the next recalculation cycle completes.

---

## Gotcha 3: CDS is Asynchronous — Share Rows Are Not Available Immediately After Participant Insert

**What happens:** An Apex class inserts `AccountParticipant` records and immediately queries `AccountShare WHERE RowCause = 'CompliantDataSharing'` in the same transaction. The query returns no rows. Developers conclude CDS is broken or misconfigured when in fact the CDS engine has not yet processed the participant records.

**When it occurs:** In any synchronous Apex context — triggers, controller methods, REST callouts, and Apex test execute blocks. CDS processes participant changes asynchronously via a platform background job. The share rows are not guaranteed to exist in the same transaction that created the participant records.

**How to avoid:** In Apex tests, wrap participant DML inside `Test.startTest()` and `Test.stopTest()`. The `stopTest()` call flushes asynchronous work, allowing share rows to be queried reliably in the assertion block. In integration or UI tests, build in a polling check or a brief wait rather than asserting on share rows in the same request that created the participant records. In production code, do not use share row existence as a synchronous post-insert validation gate.

---

## Gotcha 4: enableCompliantDataSharingForCustomObjects Is a Separate Required Flag

**What happens:** A developer enables `enableCompliantDataSharingForAccount = true` and the equivalent custom object flag (`enableCompliantDataSharingForMyObject = true`) in IndustriesSettings metadata. `AccountParticipant` inserts work correctly for Account. But the custom object participant inserts succeed silently and produce no share rows.

**When it occurs:** Custom object CDS requires `enableCompliantDataSharingForCustomObjects = true` as a separate master toggle in IndustriesSettings, in addition to the per-object flag. Enabling the per-object flag alone is not sufficient. This requirement was introduced with Summer '22 and is not prominently called out in all CDS documentation.

**How to avoid:** When enabling CDS for any custom object, deploy both flags in IndustriesSettings:
- `enableCompliantDataSharingForCustomObjects` set to `true`
- The per-object flag (e.g., `enableCompliantDataSharingForMyObject`) set to `true`

Validate by inserting a test participant record in a sandbox and confirming the corresponding share row appears in the custom object's `__Share` table.

---

## Gotcha 5: ParticipantGroup Fan-Out Creates Share Rows for Each Member at Recalculation Time

**What happens:** A `ParticipantGroup` with 100 members is referenced by 10,000 `AccountParticipant` records. An OWD change or admin-triggered recalculation causes the CDS engine to generate 1,000,000 `AccountShare` rows (100 members × 10,000 accounts). This can trigger sharing recalculation timeouts, lock the sharing recalculation queue for hours, or hit org-level sharing table size limits.

**When it occurs:** In large FSC deployments where `ParticipantGroup` is used broadly without considering the fan-out effect. A group with N members referenced across M accounts produces N × M share rows. The problem compounds when multiple groups have overlapping account coverage.

**How to avoid:** Design `ParticipantGroup` scope carefully. Use groups at the role or team level rather than org-wide. Segment large groups by region or portfolio to reduce per-group account coverage. Monitor the total projected share row count (members × accounts) before creating wide-scope group participant records. Consider using per-user `AccountParticipant` records for accounts that require fine-grained access controls rather than group-level access.
