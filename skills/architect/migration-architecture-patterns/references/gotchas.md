# Gotchas — Migration Architecture Patterns

Non-obvious Salesforce platform behaviors that bite real org-migration
projects.

---

## Gotcha 1: Skipping the pre-migration metadata audit

**What happens.** The team starts moving data without first reconciling
metadata between source and target. Validation rules in target reject
imported source data. Required fields in target aren't populated.
Picklist values from source don't exist in target. Tens of thousands
of rows fail; team scrambles to patch metadata mid-migration.

**When it occurs.** Always — unless the team explicitly slots a
metadata-audit phase before data movement. The pull to "just move the
data" is strong; resist it.

**How to avoid.** Build a metadata delta document covering every
metadata type in scope (objects, fields, picklists, validation rules,
automation, profiles, permission sets, record types, page layouts).
Every delta gets a decision: align source, align target, or accept
with a documented mitigation. Sign off on the document before
designing the data load.

**Source:** Practice guidance for the audit itself. The load-time consequences it prevents are documented in Gotchas 3 and 4.

---

## Gotcha 2: Salesforce record IDs are org-scoped

**What happens.** External systems (data warehouses, integration
tooling, finance systems, BI dashboards) often store Salesforce 15- or
18-character record IDs. After migration, those IDs no longer
correspond to anything in the target org — the link is silently
broken.

**When it occurs.** Almost every merge / split. The discovery point
is usually post-cutover ("why are these reports showing zero
results?").

**How to avoid.** Inventory external-system Salesforce-Id references
before migration. For each, plan the remap:
1. Ensure every record has a stable external-Id field populated.
2. During migration, set the external-Id on insert; capture the
   source-Id ↔ external-Id ↔ target-Id triple.
3. Update each external system to use the target-Id, or to look up
   via the external-Id via the mapping table.
4. Persist the mapping table indefinitely — late-discovered systems
   will still need it.

Watch the ID format too. Salesforce IDs are 15-character case-sensitive strings;
the API returns 18-character case-safe IDs. An external store that kept
15-character IDs in a case-insensitive column (spreadsheets, some databases)
may already have collisions, so remap on the 18-character form.

**Source:** Object Reference v67.0, Overview of Salesforce Objects and Fields,
ID field type: "These 15-character IDs are case-sensitive"; "all API calls
return an 18-character ID that's case-safe". Data Loader Guide (Summer '26),
Perform Mass Updates: upsert matches on an external ID field, and related
records can be matched by the related object's external ID.

---

## Gotcha 3: Validation rules in target reject imported source data

**What happens.** Target org has stricter validation than source —
required fields, format constraints, cross-field rules. Bulk insert
fails on rows that were valid in source but aren't in target.

**When it occurs.** Whenever target org's metadata is more
constrained than source. Common after several years of independent
metadata evolution.

**How to avoid.** Either (a) align source data to target's
constraints during ETL, or (b) controlled disable of validation rules
during the migration window, then re-enable. Option (b) is safer
when the rules represent business policy that shouldn't be relaxed
even briefly — use a Custom Metadata "migration mode" flag that
rules check and bypass during the window.

**Source:** Best Practices for Deployments with Large Data Volumes (Summer '26 PDF), Best Practices > Loading Data from the API: "Disable Apex triggers, workflow rules, and validations during loads; investigate the use of batch Apex to process records after the load is complete."

---

## Gotcha 4: Target-org automation fires on bulk-imported records

**What happens.** Process Builders, Flows, and Apex triggers in
target run on every imported record. Auto-emails go out. Field
auto-stamps overwrite migrated values. Sub-record auto-creation
duplicates records that the migration ETL was supposed to handle.

**When it occurs.** Any bulk migration into a target with active
automation — almost always.

**How to avoid.** Disable bulk-load-side automation for the migration
window. The cleanest pattern is a kill-switch via Custom Metadata
that every trigger framework respects: `if (MigrationMode.isOn) return;`.
After data validation post-migration, re-enable. For records that
genuinely need follow-up automation, run a controlled delta-update
that triggers only the wanted logic.

**Source:** Best Practices for Deployments with Large Data Volumes (Summer '26 PDF), Best Practices > Loading Data from the API (same row as Gotcha 3). The kill-switch implementation is practice guidance.

---

## Gotcha 5: Coexistence bridges accumulate operational debt

**What happens.** A coexistence bridge built for a 3-month transition
is still running 3 years later. Schema drift between the two orgs is
ongoing — every new field someone adds in one org may or may not
need to flow through the bridge. Bridge maintenance becomes a
permanent team responsibility nobody planned for.

**When it occurs.** Any coexistence design without an explicit
sunset date or ongoing-ownership commitment.

**How to avoid.** Coexistence designs should answer: "is this
permanent or transitional?" If transitional, when does the bridge
get retired (tie to a downstream consolidation)? If permanent, who
owns ongoing bridge maintenance, and what's the budget for schema
drift, monitoring, and conflict resolution? "We'll figure it out
later" produces a bridge that becomes legacy quickly.

**Source:** Practice guidance. See Gotcha 11 for the documented event-stream behavior that makes event-based bridges fragile during migrations.

---

## Gotcha 6: Regulatory split with a Salesforce Connect bridge defeats the isolation

**What happens.** A split executed for HIPAA / regulator-driven
isolation includes a Salesforce Connect bridge "so users can still
view the protected data when needed". The bridge IS access — the
regulator's whole point was that the original org has no path to
the protected data.

**When it occurs.** Architects building "the most usable" version of
a split, optimizing for user convenience without regard to the
regulatory driver.

**How to avoid.** Hard rule for regulatory splits: NO runtime bridge
to protected data. If users genuinely need access to both orgs,
they're either (a) granted accounts in both orgs (with full audit
trail in both), or (b) on the wrong side of the split. Anything
else is a bridge by another name.

**Source:** Practice guidance. The cross-org adapter is a distinct Salesforce Connect adapter type (`SfdcOrg`), separate from the OData 2.0 and 4.0 adapters (Metadata API Developer Guide v67.0, ExternalDataSource `type`).

---

## Gotcha 7: Hyperforce region constraints during merge / split

**What happens.** Source org is in `us-east-1`, target / new org is
in `eu-west-1` (or vice versa). Data migration crosses regions —
which has compliance implications (GDPR, regional data residency
requirements) and latency implications during phased migration.

**When it occurs.** Geographic-driven splits, M&A across regions, or
intentional region migrations.

**How to avoid.** Verify region of source and target before any data
movement plan. If regions differ for compliance reasons, the
migration ETL itself must respect the constraint — extract may need
to happen via a tool that's also in the appropriate region. Document
the residency posture explicitly.

**Source:** UNVERIFIED (2026-10-03): Hyperforce region behavior is documented in Salesforce Help, which does not fetch. The related, documented risk is in Gotcha 11: an org migration to a new data center resets the retained platform event stream.

---

## Gotcha 8: Permission inventory mismatch causes "I can't see anything" escalations

**What happens.** Users migrated from source to target find that
records they could see in their old org are invisible in the new
one. Sharing rules, permission sets, profile differences cause
narrower access by default.

**When it occurs.** Org consolidations where source and target have
different sharing models or different profile structures.

**How to avoid.** Permission inventory — for each migrating user
group, document what records they could see in source and what
they need to see in target. Provision permission sets / sharing
rules to match before migration. Validate by spot-checking pilot
users post-migration before opening to the full population.

**Source:** Best Practices for Deployments with Large Data Volumes (Summer '26 PDF), Best Practices > Loading Data from the API: load users into roles, then records with owners, then groups and queues, then sharing rules one at a time; "Use Public Read/Write security during initial load to avoid sharing calculation overhead" where the data allows it.

---

## Gotcha 9: Audit-log retention loss on source-org decommission

**What happens.** Source org is decommissioned (or downgraded to
read-only) post-merge. Setup Audit Trail, Field History, and Login
History — all retained on the *org*, not the user — become harder to
access. Compliance / legal teams discover this when they need
historical records that are now in cold storage.

**When it occurs.** Any merge where source orgs are fully
decommissioned without a documented archival plan.

**How to avoid.** Before decommissioning a source org, export
retention-required logs (Field Audit Trail archive, Setup Audit Trail
exports, Login History) to a long-term storage system that the
compliance team can query. Document the retention schedule and the
query path.

**Source:** Object Reference v67.0, SetupAuditTrail: "Represents changes you or other admins made in your org's Setup area for at least the last 180 days"; aggregate queries such as `count(Id)` are not supported on it. UNVERIFIED (2026-10-03): field history and login history retention periods are stated in Salesforce Help only.


---

## Gotcha 10: Every migrated record looks created today by the integration user

**What happens.** `CreatedDate`, `CreatedById`, `LastModifiedDate`, and
`LastModifiedById` on migrated records show the load time and the migration
user. Reports by age, SLA clocks keyed on creation, and audit questions about
who created a record all go wrong.

**When it occurs.** On any merge or split load where the permission to set
audit fields was not enabled before the load.

**How to avoid.** Before the load, enable "Set Audit Fields upon Record
Creation" and "Update Records with Inactive Owners" in User Interface settings,
grant the permission to the migration user, and map the source audit values on
insert. It works only on create, only for the listed objects (including
Account, Case, Contact, Lead, Opportunity, Task, Event, and custom objects),
and `SystemModstamp` cannot be set. Audit dateTime values must fall between
1970-01-01 and 4000-12-31 GMT.

**Source:** Object Reference v67.0, System Fields, Audit Fields (import
procedure, object list, `systemModstamp` exception, valid date range).

---

## Gotcha 11: Event-based bridges lose their replay history when the org moves

**What happens.** A coexistence bridge built on high-volume platform events
relies on replay to recover missed events. After an org migration to a new
data center, an instance refresh, or a sandbox refresh, the retained event
stream resets: earlier events cannot be replayed and old replay IDs have no
relation to new ones. Subscribers that resume from a stored replay ID miss
data or fail.

**When it occurs.** During data-center or instance migrations of either org in
a coexistence, and in every sandbox refresh used for bridge testing. Retention
is 72 hours for high-volume events even without a reset.

**How to avoid.** Design the bridge to resynchronize from source data, not
only from event replay. Store a business watermark (for example the last
`SystemModstamp` processed) alongside the replay ID, and run a reconciliation
query after any maintenance or refresh event.

**Source:** Platform Events Developer Guide v66.0 (Spring '26), Event Retention
in the Event Bus ("High-volume platform event messages are stored for 72 hours")
and Salesforce Maintenance Activities and Sandbox Refresh (stream reset; replay
IDs unrelated after the activity). Local corpus
`knowledge/imports/platform-events.md`.

---

## Gotcha 12: Data Loader quietly changes dates and owners

**What happens.** Two Data Loader settings rewrite migrated data. Date values
without a time zone are interpreted in the time zone of the machine running
Data Loader, or GMT if the configured value is invalid, which shifts dates
near midnight by a day. The assignment rule setting, when filled, applies to
cases and leads and "overrides Owner values in your CSV file".

**When it occurs.** When the load runs from a laptop in a different time zone
from the source org, and when someone sets an assignment rule to "make routing
work" during the load.

**How to avoid.** Set the Data Loader Time Zone setting explicitly to the
source system's zone, or export dateTimes with an explicit offset. Leave the
assignment rule setting empty for migration loads and map `OwnerId` from the
remapping table.

**Source:** Salesforce Data Loader Guide (Summer '26), Configure Data Loader:
Time Zone ("If no value is specified, the time zone of the computer where Data
Loader is installed is used"; "If an incorrect value is entered, GMT is used")
and Assignment rule settings.

---

## Gotcha 13: Archived data in big objects cannot be bridged with Salesforce Connect

**What happens.** A coexistence plan reads the other org's archive through a
Salesforce Connect cross-org external object. Big objects are not reachable
that way.

**When it occurs.** When one of the orgs archived history to big objects and
the bridge design assumes every object is visible cross-org.

**How to avoid.** Move big object data as data (Bulk API or SOAP API, which big
objects support) or keep the archive in its original org with a documented
query path.

**Source:** Big Objects Implementation Guide v66.0, Considerations When Using
Big Objects: "You can't use Salesforce Connect external objects to access big
objects in another org"; API Support for Big Objects (SOQL, Bulk, Chatter,
SOAP; no REST). Local corpus `knowledge/imports/salesforce-big-objects-guide.md`.
