# Gotchas — Data Skew and Sharing Performance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Removing a User from a Role Is as Expensive as Adding Them

**What happens:** Admins assume that removing a user from a role (or moving them to a "simpler" position in the hierarchy) is a fast cleanup operation. In practice, if the user owns a large number of records, the demotion triggers a full sharing recalculation for all those records — the same cost as adding them.

**When it occurs:** Any time a user who owns more than ~10,000 records has their role changed, or is added to or removed from a public group that is the source of a sharing rule. This includes both manual admin changes and API-driven provisioning operations.

**How to avoid:** Before changing a user's role or group membership, check how many records they own using a record count report. If the count exceeds 10,000, schedule the change during a low-activity maintenance window, ensure no other batch role changes are running concurrently, and monitor the sharing recalculation background job after the change.

---

## Gotcha 2: A Single-Record Update Can Trigger the Implicit Sharing Scan

**What happens:** Practitioners assume that parent-child data skew only matters during bulk data loads. In reality, even updating a single child record's owner or losing access to a single child record will trigger the full implicit sharing scan on the parent account. On a parent with 300,000 children, this means a single-record operation from the UI can take seconds to minutes.

**When it occurs:** Any time a user's access to a child record changes — through an owner change, a sharing rule update, a role move, or a manual share being revoked. The system must check all sibling records to determine whether to retain or remove the parent implicit share.

**How to avoid:** Keep parent-child cardinality below 10,000 children per parent. Evaluate setting the child object OWD to "Controlled by Parent" when child records do not need independent sharing — this configuration eliminates implicit sharing entirely, so no scan occurs.

---

## Gotcha 3: Switching to "Controlled by Parent" OWD Removes All Existing Child-Level Manual Shares

**What happens:** An admin sets a child object's OWD to "Controlled by Parent" to eliminate implicit sharing scan overhead. Immediately after, existing users who had been granted access to specific child records through manual shares or sharing rules lose access — because "Controlled by Parent" overrides all independent child-level access grants.

**When it occurs:** Any time an OWD is changed to "Controlled by Parent" mid-implementation, after child-level sharing has already been configured or granted.

**How to avoid:** Before switching to "Controlled by Parent," audit all existing manual shares, sharing rules, and Apex-managed shares on the child object. Document every user and group that currently has explicit access to child records. Understand that after the switch, access to children will only flow from the parent — no independent shares are possible. Run the OWD change in a sandbox first and verify that no user loses required access before applying to production.

---

## Gotcha 4: Granular Locking Does Not Eliminate All Lock Conflicts

**What happens:** Admins learn that Salesforce has "granular locking" enabled by default and assume this means concurrent group maintenance operations will not produce lock errors. They run multiple large-scale integrations and provisioning jobs in parallel and still encounter "could not obtain lock" errors.

**When it occurs:** Granular locking allows concurrent operations only between groups that have no hierarchical relationship. Operations like role reparenting (moving a role to a different parent in the hierarchy) still block almost all other group updates, regardless of granular locking. During end-of-quarter realignments where role reparenting happens alongside mass user provisioning, lock errors remain common.

**How to avoid:** Review the granular locking compatibility matrix in the *Designing Record Access for Enterprise Scale* guide. Do not assume parallel processing is safe for all group operations. Always sequence role-reparenting operations separately from user provisioning, and add retry logic to integration code for lock-error recovery.
