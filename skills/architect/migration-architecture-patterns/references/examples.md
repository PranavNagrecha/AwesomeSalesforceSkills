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
