# Well-Architected Notes — Apex Managed Sharing Patterns

## Relevant Pillars

- **Security** — Primary pillar. Apex managed sharing is a row-level access
  control implemented in application code rather than configuration, which moves
  a security decision out of Setup and into a deployment pipeline. The custom
  `RowCause` is the audit artifact: it records *why* a user was granted access, in
  a form the platform will not overwrite and an auditor can query
  (`SELECT UserOrGroupId, AccessLevel, RowCause FROM Job__Share`). Designs that
  fall back to `RowCause = 'Manual'` lose that provenance entirely — a manual share
  looks identical whether an admin created it by hand or a nightly batch did.

- **Reliability** — The failure mode of a sharing bug is asymmetric. A grant that
  does not fire produces a support ticket within hours. A revoke that does not
  fire produces nothing at all until an audit, months later. Reliability here means
  the pair is atomic: grant and revoke live in the same service, are exercised by
  the same trigger context, and are rebuilt by the same recalculation class. The
  recalculation class is what makes the system self-healing after the events the
  application does not control — an OWD change, a record-locking failure during a
  bulk load, a partially failed `Database.insert`.

- **Operational Excellence** — Sharing reasons must be source-controlled
  `SharingReason` metadata, not clicks in a Classic UI that most admins can no
  longer reach. The recalculation class needs a registration step that is easy to
  forget on sandbox refresh, so it belongs on the post-refresh checklist. Job
  outcomes are visible under **Setup → Apex Jobs**; nothing surfaces them
  proactively, so wire the `finish()` method to your logging framework.

- **Performance** — `__Share` DML is real DML against a real table. On an object
  with a wide fan-out (one record shared to 300 users), a 200-record trigger batch
  becomes 60,000 share rows in one transaction and will exceed the 10,000-record
  DML limit. Sharing to public groups instead of individual users collapses that
  fan-out to one row per record per group, at the cost of maintaining group
  membership. Group membership changes themselves trigger asynchronous
  recalculation, so the cost does not disappear — it moves.

## Architectural Trade-offs

**Custom object vs standard object.** This is not a preference, it is a hard
platform boundary: "Apex sharing reasons and Apex managed sharing recalculation
are only available for custom objects." If the record that needs programmatic
sharing is an Opportunity, the available options are the built-in Opportunity
Team, criteria-based sharing rules, or manual shares that evaporate on owner
change. Discovering this after the design is signed off is expensive. Ask "which
object?" before "which mechanism?"

**Per-user shares vs group shares.** Per-user shares are precise and trivially
auditable — you can see exactly who was granted what and why. They scale linearly
with population, and past roughly 50 users per record the row volume starts
dominating both DML limits and recalculation time. Public-group shares collapse the
row count but push the complexity into group membership maintenance and make the
audit question ("can this specific person see this record?") a two-hop query. Pick
per-user when the population is small and the audit story matters; pick groups when
the population is large and stable.

**Trigger-synchronous vs Queueable.** Granting inside the trigger keeps sharing
consistent with the record at the moment of commit, which is what users expect.
It also puts share DML inside the user's transaction, where it competes for the
DML row limit and adds latency to the save. Moving to a Queueable keyed on record
Ids decouples them, at the cost of a visible window where the record exists and
the access does not. For bulk loads the Queueable (or Batch) form is the only
viable option; for interactive saves the synchronous form is usually correct.

**Apex managed sharing vs redesigning the model.** A sharing requirement that
cannot be expressed declaratively is often a signal that the data model is wrong
rather than that code is needed. If "everyone on the deal team sees the
Opportunity" requires Apex, the alternative is frequently to make the *team
membership itself* the shared record — a custom object with its own OWD, its own
sharing rules, and a lookup to the Opportunity. That trades one hard problem
(programmatic sharing on a standard object, which is not available) for one easy
one (declarative sharing on a custom object). Cost the redesign before committing
to code you now own forever. See
[`standards/decision-trees/sharing-selection.md`](../../../../standards/decision-trees/sharing-selection.md).

**Declarative headroom before writing code.** The Salesforce Security Guide caps
sharing rules at "up to 300 total sharing rules for each object, including up to 50
criteria-based or guest user sharing rules." Teams frequently reach for Apex on the
belief they are near a limit they have never measured. Count first — collapsing
several criteria into one formula field that a handful of rules key off is far
cheaper than an Apex implementation with a service class, a trigger, a
recalculation batch, and a permanent test-maintenance burden.

## Anti-Patterns

1. **Shipping grant without revoke.** The most common and most consequential
   defect in this domain. Access that is never withdrawn accumulates silently and
   is discovered by an auditor, not a user. Treat `revoke` as part of the
   definition of done, and require a `System.runAs` test that asserts the count
   drops to zero after the driving relationship is removed.

2. **Deleting `__Share` rows without a `RowCause` filter.** An unfiltered delete
   removes sharing-rule rows, team rows, territory rows, and end-user manual
   shares. Rule-based rows return on the next recalculation; manual shares do not.
   Every delete against a share object must name the reasons the application owns.

3. **No recalculation class.** Without one, an unrelated OWD change made by an
   admin who has never heard of your application silently destroys its access
   model. This is not a hypothetical — the platform documents that it removes "all
   types of sharing ... if the access they grant is considered redundant" on an OWD
   change.

4. **Running share DML in user mode for non-admin users.** Apex managed sharing
   requires Modify All Data. Code that uses `AccessLevel.USER_MODE` for the share
   insert works in an admin sandbox and fails for every standard user in
   production. Make the system-mode escape explicit and comment why, so the next
   reviewer does not revert it in the name of security hygiene.

5. **Enabling Experience Cloud without auditing the sharing code.** Enabling
   digital experiences automatically widens `RoleAndSubordinates` grants to include
   portal subordinates. An implementation that was correct and internal-only on
   Friday is an external data exposure on Monday, with no code change. Convert to
   `RoleAndSubordinatesInternal` before the enablement, not after.

6. **Treating a `__Share` row count as a test.** A row can exist and grant nothing
   — for example when its access level is not more permissive than the object's
   org-wide default, in which case the platform rejects it with
   `FIELD_FILTER_VALIDATION_EXCEPTION` and the test that only counts successful
   inserts never notices. Assert visibility inside `System.runAs`.

## Official Sources Used

- Understanding Apex Managed Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing.htm
- Understanding Sharing (types of sharing, access levels, Modify All Data requirement, custom-objects-only constraint) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Sharing a Record Using Apex (share object properties, `FIELD_FILTER_VALIDATION_EXCEPTION`, master-detail and guest-user constraints) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm
- Recalculating Apex Managed Sharing (`Database.Batchable` requirement, automatic execution on OWD change) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_recalc.htm
- SharingReason (Metadata API) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingreason.htm
- Salesforce Security Guide — Sharing Rules (300 rules per object, 50 criteria-based) — https://help.salesforce.com/s/articleView?id=platform.security_about_sharing_rules.htm&type=5
- Salesforce Security Guide — Automatic Recalculation of Org-Wide Defaults and Sharing Rules — https://help.salesforce.com/s/articleView?id=platform.security_sharing_rule_recalculation.htm&type=5
- Group (RoleAndSubordinatesInternal) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_group.htm
- Use Batch Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
