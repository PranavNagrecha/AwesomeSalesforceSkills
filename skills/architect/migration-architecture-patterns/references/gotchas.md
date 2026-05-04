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
