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

---

## Gotcha 5: "Swap the Skewed Lookup for a Picklist" Is a One-Way Migration, Not a Field Edit

**What happens:** Reading the documented lookup-skew fix — "when you have a relatively low number of lookup values, it's generally a good idea to use a picklist field rather than a lookup field" — teams plan it as a field type change. It is not. The lookup stores record IDs and the picklist stores values, so it means standing up a new field, backfilling it, and repointing every report filter, formula, flow, validation rule, and integration that references the relationship before the lookup can be deleted — deleting the lookup takes its stored IDs with it.

**When it occurs:** Whenever remediation of `UNABLE_TO_LOCK_ROW` contention jumps straight to the picklist option. The same source states the precondition most teams skip: "In many cases, you cannot substitute a picklist for a lookup field if you have additional fields and other data on the lookup records." If the target object carries fields anyone reads or reports on, low cardinality is no longer sufficient justification — audit what else lives on those records before committing to the swap.

**How to avoid:** Try distribution first — it is reversible and needs no schema change. Skew usually concentrates on a generic "catchall" target, so leaving the lookup blank on records where it genuinely does not apply beats pointing them all at a placeholder record. Also reduce lock duration before reshaping data: locks are held for the whole save, so moving non-critical trigger and flow logic out of the synchronous path shrinks the collision window. Reserve the picklist swap for value sets that are small, static, and backed by a target object holding nothing but a name.

---

## Gotcha 6: Defer Sharing Calculation Is Not In Your Org Yet, and Resuming It Recalculates Both Queues at Once

**What happens:** The runbook says "defer sharing calculations during the load." The team deploys
`Sharing.settings` with `<deferGroupMembership>true</deferGroupMembership>` on the night of the migration
and the deploy succeeds — but nothing is deferred, because the underlying feature was never provisioned.
Separately, teams that *do* have it enabled flip `deferGroupMembership` back to `false` at 2 a.m. and are
surprised when two recalculations start, not one.

**When it occurs:** Both fields are API 49.0 and later (`api_meta.txt` L126995, L127025), and the Metadata
API Developer Guide states the precondition explicitly: "The defer sharing calculation feature isn't enabled
by default. To enable it for your Salesforce org, contact Salesforce Customer Support."
(`api_meta.txt` L127000). The resume behaviour is documented in the same block: "When you change the value
of this field from `true` to `false`, group membership is automatically recalculated. Sharing rules are also
automatically recalculated, unless the `deferSharingRules` field is set to `true` prior to modifying
`deferGroupMembership`." (`api_meta.txt` L127004). And while group membership is deferred you cannot steer
the other switch at all — "If the `deferGroupMembership` field is set to `true`, you can't change the value
of `deferSharingRules`. Sharing rule calculations are suspended regardless of the value of
`deferSharingRules`." (`api_meta.txt` L127021).

**How to avoid:** File the Support case weeks ahead and confirm the permission is visible in the org before
the change window is booked. Write the resume as its own deploy artifact, not a Setup click, and set
`deferSharingRules` to `true` *before* flipping `deferGroupMembership` to `false` when you want the group
membership recalculation to finish and be observed before sharing rules start. Both files belong in source
control — see `references/metadata-examples.md` § 1.

---

## Gotcha 7: "Switch the Load to Serial Mode" Does Nothing on Bulk API 2.0

**What happens:** A load fails with lock errors, the fix everyone knows is serial concurrency, and the team
adds `"concurrencyMode": "Serial"` to a Bulk API 2.0 job. The API accepts the create call and the job still
runs in parallel; the lock failures continue and the team concludes that serial mode "didn't help."

**When it occurs:** On every Bulk API 2.0 job. The field exists but is inert: "Reserved for future use. How
the request is processed. Currently only parallel mode is supported. (When other modes are added, the API
chooses the mode automatically. The mode isn't user configurable.)" (`api_asynch.txt` L3050–L3054, repeated
at L3214–L3219). Serial concurrency is a Bulk API v1 capability — "In serial mode, batches are processed
serially with other batches from the same job and batches from other serial mode jobs, and each batch must
complete before the next batch starts processing." (`api_asynch.txt` L4986–L4988).

**How to avoid:** Decide the API by the concurrency requirement, not by recency. A remediation touching the
four operations the guide names as lock-prone — creating users, updating ownership for records with private
sharing, updating user roles, updating territory hierarchies (`api_asynch.txt` L2695–L2699, L5010–L5015) —
is a Bulk API v1 job with `JobInfo.concurrencyMode = Serial` if reorganising batches by parent does not
clear the contention first. Reorganise first: the guide's stated preference is "Avoid processing data in
serial mode unless you know that parallel mode would otherwise result in lock timeouts and you can't
reorganize your batches to avoid locks." (`api_asynch.txt` L4993–L4995).

---

## Gotcha 8: Deploying the Bucket Group Deploys an Empty Group

**What happens:** The remediation splits one catch-all owner across four bucket groups, deploys the four
`Group` files and the four owner-based sharing rules together, the deploy is green — and nobody gains
access, because every bucket is empty. The sharing rules are live and correct and resolve to zero users.

**When it occurs:** Always. The `Group` metadata type carries only `description`, `doesIncludeBosses`,
`fullName`, and `name` (`api_meta.txt` L79635–L79649), and the guide states the consequence in one line:
"Members of the public group aren't migrated when you deploy the group type." (`api_meta.txt` L79630).
Membership lives in `GroupMember`, a data object with `GroupId` and `UserOrGroupId`
(`object_reference.txt` L154390) that must be loaded through the API after the metadata lands.

**How to avoid:** Treat every bucket group as a two-artifact change — the `.group` file *and* a
`GroupMember` load step — and make the post-deploy `GroupMember` count query in
`references/metadata-examples.md` § 6 a gate, not a nicety. When creating the groups through the API rather
than metadata, set `DeveloperName` yourself: "When creating large sets of data, always specify a unique
`DeveloperName` for each record. If no `DeveloperName` is specified, performance may slow while Salesforce
generates one for each record." (`object_reference.txt` L154208).

---

## Gotcha 9: The Skewed Lookup Is Already Indexed — Selectivity Is What Broke, Not the Index

**What happens:** A diagnostic query grouped by a skewed lookup field times out. The team opens a Support
case asking for a custom index on that lookup. The case is closed as "already indexed," and the query is
still slow, so the finding gets dropped and the skew survives another quarter.

**When it occurs:** On every foreign key. The platform maintains indexes on `RecordTypeId`, `Division`,
`CreatedDate`, `Systemmodstamp`, `Name`, `Email` for contacts and leads, "Foreign key relationships (lookups
and master-detail)", and the record Id (`ldv.txt` L400–L409). What fails is the optimizer's selectivity
test, not index existence: a custom indexed field is used only "if the filter matches less than 10% of the
first million records and less than 5% of additional records" (`ldv.txt` L468). A lookup value carrying
903,000 of 1,050,000 rows is roughly 86% of the object and clears no threshold at any table size, so the
optimizer skips the index and scans.

**How to avoid:** Measure the distribution before requesting anything from Support — `GROUP BY ROLLUP` on
the lookup field returns the per-value counts and the object total in one query (`ldv.txt` L248) — and
compare against the published thresholds rather than guessing. Then fix the *distribution*: leaving the
lookup blank where it genuinely does not apply is better than a placeholder target record, because "By
default, the index tables don't include records that are null (records with empty values)."
(`ldv.txt` L436) — null rows stay out of the index table entirely instead of piling onto one indexed value.

---

## Gotcha 10: `includeRecordsOwnedByAll` Is Immutable, and It Governs Exactly the Users Skew Lives In

**What happens:** A criteria-based sharing rule is created during remediation and later found to be missing
several hundred thousand records — every record owned by the integration user, the automated process user,
and the high-volume site users. The obvious fix is to edit the rule's setting. The setting cannot be edited;
the rule has to be deleted and recreated, which triggers a fresh recalculation over the whole object.

**When it occurs:** At creation of any `SharingCriteriaRule`. The field is Required and permanent:
"Indicates whether records owned by users who can't have an assigned role are included in the records shared
(`true`) or not (`false`). Examples of users who can't have an assigned role are high-volume users and
system users such as automated process users… You can't edit this field after the sharing rule is created."
(`api_meta.txt` L129312). Parking-lot and integration owners are precisely that population — and the
documented ownership-skew mitigation of taking the user *out* of the role hierarchy puts them there
deliberately.

**How to avoid:** Set `includeRecordsOwnedByAll` consciously in the XML before the first deploy, and record
the choice in the mitigation plan next to the "remove the parking-lot user from the role hierarchy" action,
because the two decisions interact. Also note what sharing rules cannot do for you here: "You can't
retrieve, delete, or deploy manual sharing rules or sharing rules by their type (owner, criteria-based,
territory, or guest user)." (`api_meta.txt` L129249) — cleaning up manual shares left behind by an OWD
change is a data task, not part of the deploy.

---

## Gotcha 11: A "Failed" Bulk API v1 Batch Has Usually Committed Some of Its Records

**What happens:** A reparenting batch comes back failed after lock contention. The operator resubmits the
whole file. Rows that already committed are processed a second time, roll-up summaries and downstream
automation double-fire, and the reconciliation counts stop matching the source system.

**When it occurs:** Whenever lock contention hits a Bulk API v1 batch, which is the normal condition when
reparenting children of a skewed parent. The documented behaviour is layered: the API "waits a few seconds
for its release and, if it doesn't happen, the record is marked as failed"; "If there are problems acquiring
locks for more than 100 records in a batch, the Bulk API places the remainder of the batch back in the queue
for later processing… records marked as failed aren't retried"; the batch is "reprocessed up to 10 times
before the batch is permanently marked as failed"; and "Even if the batch failed, some records could have
completed successfully." (`api_asynch.txt` L5002–L5008). Bulk API 2.0 reports the same class of problem as
`TooManyLockFailure` — "Too many lock failures while processing the current batch."
(`api_asynch.txt` L2790–L2792).

**How to avoid:** Never resubmit a failed batch wholesale. Pull the per-record results, resubmit only the
rows marked failed, and prevent the contention in the first place by sorting the file: "For large data
loads, sort main records based on their parent record to avoid having different child records (with the same
parent) in different jobs." (`api_asynch.txt` L2701–L2702). The Large Data Volumes guide gives the same
instruction for the ingest side — "group records by the field `ParentId` in the same batch to minimize
locking conflicts" (`ldv.txt` L894–L896).
