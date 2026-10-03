# Examples — Migration Architecture Patterns

## Example 1 — M&A merge: external system stored source-org Salesforce IDs

**Context.** Acquired company's CRM data is being merged into the
acquirer's Salesforce org. Their finance system stores the
acquired-company Salesforce Account.Id values to link invoices to
customer records.

**Wrong instinct.** Run the data migration first, then "figure out
the finance system later".

**Why it's wrong.** Once Account records land in the target org with
new IDs, the finance system's stored IDs are orphaned. The link
between invoices and customers is broken — and reconstructing it
later requires custom matching logic on Name + a probabilistic key.

**Right answer.**

1. **Before migration:** ensure every acquired-company Account has a
   stable external-Id field populated (e.g. `Acquired_Account_Code__c`).
2. **During migration:** insert into target with the external-Id field
   set; capture the **source-Id ↔ external-Id ↔ target-Id** triple
   in a migration mapping table.
3. **In parallel:** update the finance system's stored Salesforce-Id
   references using the mapping table. Either (a) replace stored IDs
   with target IDs, or (b) add a new column for target-Id and
   transition queries over time.
4. **Post-cutover:** keep the mapping table accessible — other
   external systems may surface later that also stored source IDs.

The mapping table is the migration's most-referenced artifact, both
during and for years after.

---

## Example 2 — Regulatory split: divestiture of a healthcare BU

**Context.** A holding company is divesting its healthcare BU. The
HIPAA-regulated patient data must move to the divested entity's new
org. The remaining business must have NO ongoing access to the
patient data.

**Critical constraint.** "No ongoing access" is enforced by
architecture, not policy. A Salesforce Connect bridge or any other
runtime read path defeats the divestiture's entire point.

**Sequence.**

1. **Define the boundary with the regulator.** Patient_Account__c,
   Patient_Case__c, related notes, encrypted SSN field — and every
   user who's seen those records.
2. **Provision the new org** in the geographically-correct Hyperforce
   region.
3. **Replicate the relevant metadata subset.** The new org gets only
   the objects + fields in the regulatory boundary, plus the
   minimum infrastructure needed (record types, permission sets).
4. **Bulk export from source, bulk insert to target,** with external-Id
   preservation for the integrations that will follow.
5. **Cut over identity.** Healthcare users get accounts in the new
   org's IdP; their access to the source org is revoked at the same
   moment.
6. **Cut over external integrations.** Any system that previously
   pointed at the source org for patient data now points at the new
   org.
7. **Source-org cleanup.** Patient_Account__c, Patient_Case__c, and
   the encrypted SSN field are removed from the source org. Audit
   logs in the source org are retained for the regulator-required
   period but are now read-only and detached from any user account.

The most common failure: keeping a Salesforce Connect bridge "for
emergencies". The bridge IS access; it cannot exist in a regulatory
split.

---

## Example 3 — Coexistence: shared customer between sales and service BUs

**Context.** Two BUs (sales and service) operate distinct Salesforce
orgs. Customers exist in both — sales-led acquisition flows into the
sales org, customer service issues are managed in the service org.
Neither BU wants to consolidate, and there's no exec mandate.

**Design.**

- **Identity.** SSO via shared corporate IdP. Each user has a per-org
  permission set; cross-org access is by per-user policy, not
  default.
- **Customer record.** Master in the sales org. Service org gets a
  replica via Platform Events: when an Account changes in the sales
  org, a `Account_Updated__e` event fires; an Apex subscriber in the
  service org upserts by external-Id.
- **Service activity feedback.** When the service org logs a
  significant case interaction, a `Service_Interaction__e` event
  fires back to the sales org. Sales-org Apex updates the related
  Account record's "Last Service Interaction" field.
- **Reporting.** Both orgs feed a downstream warehouse (Snowflake);
  cross-BU reporting happens there, not via cross-org SOQL.

Coexistence is not free. The team owns:
- Schema-drift monitoring (when sales-org adds a field, does service-org need it?)
- Bridge availability (Platform Event lag, dead-letter for unprocessable events)
- Conflict resolution (when both orgs update the same field at the same time)

Budget for ongoing bridge maintenance, not just initial build.

---

## Example 4 — Pre-migration metadata audit catches a picklist landmine

**Context.** Two-org merge. Both source orgs have a `Status__c`
picklist on a custom Order object, but with different values:

- Source A: New, In Progress, Completed, Cancelled
- Source B: New, Pending, Shipped, Delivered, Returned

Migration team assumes "both orgs have a Status__c picklist; we'll
just merge them".

**What goes wrong without the audit.** Bulk insert into target hits
validation: source-A's `In Progress` value isn't in target's
picklist. 30,000 rows fail. A frantic admin adds the missing values;
some inactive. Later, reports break because users see picklist values
that don't match documentation.

**Right approach.** Pre-migration audit produces a delta document:

```
Object: Order
Field: Status__c
Source A values: New, In Progress, Completed, Cancelled
Source B values: New, Pending, Shipped, Delivered, Returned
Target values (decision): New, Pending, In Progress, Shipped, Completed, Delivered, Cancelled, Returned
Mapping rules:
  Source A "In Progress" → Target "In Progress"
  Source A "Completed"   → Target "Completed"
  Source B "Shipped"     → Target "Shipped"
  ... etc
Rationale:
  Union both sets; map exact-match identical labels; sequence
  reflects business workflow.
```

Document signed off before migration. Target picklist provisioned
correctly. Migration ETL applies the mapping rules. No surprise
failures.

---

## Anti-Pattern: Merging without disabling target-org automation

```
Step 1: Bulk insert 50,000 Accounts into target org.
Step 2: Watch the Process Builder fire 50,000 welcome emails to acquired customers.
```

**What goes wrong.** Customers get welcome emails for accounts they've
been with for years. Some get duplicate emails because their record
hits multiple automation paths. Brand damage; legal escalation in
some jurisdictions.

**Correct.** Disable bulk-load-side automation (Process Builders,
Flows, triggers) for the migration window. Use a custom-setting flag
or Custom Metadata kill-switch that the trigger framework respects.
Migrate. Validate. Re-enable automation. Run a delta-update batch
that triggers only the necessary follow-up logic for the migrated
records (or none, if the records are pre-existing).

---

## Example 5: Worked decision record and pre-load checks for an M&A merge

**Context.** Company A (Enterprise Edition, 420 users) acquires Company B
(Enterprise Edition, 130 users). Both run Sales Cloud and Service Cloud.
B's ERP and data warehouse store B's Salesforce Account and Opportunity IDs.
The executive mandate is one org by Q3.

**Pre-load checks in the source org (B).** Run before wave 1; each answers a
question from the skill's Questions table.

```soql
-- C1. Records that will need a remapping row (every Account that moves)
SELECT COUNT() FROM Account

-- C2. Records already carrying a stable key for the target upsert
SELECT COUNT() FROM Account WHERE Legacy_B_Id__c != null

-- C3. Owners in B with more than 10,000 Opportunities: plan their target
--     owners and the load order before the move (LDV guide, Best Practices > General)
SELECT OwnerId, COUNT(Id) owned
FROM Opportunity
GROUP BY OwnerId
HAVING COUNT(Id) > 10000

-- C4. Setup changes in the retention window that must be exported before
--     decommission (SetupAuditTrail keeps at least 180 days; aggregate
--     queries other than count() are not supported on it)
SELECT CreatedDate, CreatedBy.Name, Action, Section, Display
FROM SetupAuditTrail
WHERE CreatedDate = LAST_N_DAYS:180
ORDER BY CreatedDate DESC
```

`Legacy_B_Id__c` is a Text field marked External ID in the target org (A),
populated with B's 18-character Id on insert. External ID fields are indexed
automatically (LDV guide, Indexes), which keeps the upsert and later lookups
selective.

**The decision record** lives at `docs/adr/0105-merge-org-b-into-org-a.md` in
the target org's delivery repository. It deploys nothing; the metadata it
commits to (the external ID fields as `CustomField`, the migration permission
set as `PermissionSet`, and the bypass custom metadata as `CustomMetadata`
records) goes into the wave-0 `package.xml`.

```markdown
# ADR-0105: Merge org B into org A in three waves with a remapping table

## Status
Accepted (2026-10-03), Integration Architecture Board

## Context
- Direction: merge (2 → 1). Driver: M&A, executive mandate for Q3.
- B's ERP and warehouse store B record IDs. IDs are org-scoped; the
  API returns 18-character case-safe IDs (Object Reference, ID type).
- Created dates and owners drive B's renewal reports and case SLAs.
  Audit fields can be set on create only after enabling "Set Audit
  Fields upon Record Creation" (Object Reference, Audit Fields).
- A's target has 140 active validation rules and 31 record-triggered
  flows. The LDV guide recommends disabling triggers, workflow, and
  validations during loads and processing afterward with batch Apex.
- Coexistence for 8 weeks: B users read A Accounts through Salesforce
  Connect (cross-org adapter, `SfdcOrg`). No event bridge: replay
  resets on refresh or org migration, and 8 weeks does not justify it.

## Decision
1. Wave 0: deploy Legacy_B_Id__c (External ID) on every moving object,
   the migration permission set (Set Audit Fields upon Record
   Creation), and a bypass flag that triggers, flows, and validation
   rules check.
2. Waves 1-3: reference data, then Accounts and Contacts, then
   Opportunities, Cases, and activities. Upsert on Legacy_B_Id__c;
   map audit fields and OwnerId from the remapping table. Data Loader
   Time Zone set to America/Chicago (B's org zone); assignment rule
   setting left empty.
3. Remapping table (B Id, A Id, object) is retained indefinitely and
   published to the ERP and warehouse teams before wave 3.
4. Before decommissioning B: export SetupAuditTrail (180-day window),
   field history, and login history to the compliance store.

## Consequences
### Positive
- External systems remap with a lookup, not a re-integration.
- Reports keep original created dates and owners.
### Negative
- Automation that should run on migrated records (for example
  entitlement assignment) must run as a post-load batch.
- The remapping table becomes a permanent integration dependency.
- 8 weeks of cross-org reads add per-page latency for B users.

## Alternatives Considered
### Long-term coexistence with an event bridge
Rejected: no business driver for two orgs; bridge debt grows.
### Big-bang single load
Rejected: one failed wave would block the Q3 date with no rollback point.

## Rollback
Each wave records the A Ids it created; rollback deletes those Ids and
restores the previous wave's remapping snapshot.

## Date
2026-10-03
```

**Why it works.** Each premise cites what the platform actually does (org-scoped
IDs, settable audit fields, load-time bypass guidance, cross-org adapter), the
pre-load checks turn the Questions table into numbers, and every wave has a
rollback that names its own Ids.

