# Gotchas — Marketing Data Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: 30-Minute Automation Studio Query Timeout Cannot Be Extended

**What happens:** SQL Query Activities in Automation Studio that run longer than 30 minutes are automatically terminated by the platform. The query does not commit any partial results — the target DE is left in whatever state it was in before the query started. The Automation is marked as errored with a timeout message.

**When it occurs:** When a Query Activity performs a full table scan on one or more large DEs (hundreds of thousands to millions of rows) filtering on non-primary-key columns that do not have a custom index. Wide flat DEs (many columns) make this worse because each row is larger, reducing the rows-per-second scan rate. This commonly surfaces when a previously fast query slows down over months as DE row counts grow silently.

**How to avoid:** Design normalized DEs to reduce per-query scan sizes. Identify non-PK filter columns used in WHERE clauses on large DEs and submit a Salesforce Support ticket for custom indexes before the DE is heavily populated — index requests are not always granted and take time to process. Monitor DE row counts monthly and archive or purge rows that are no longer needed for active sends.

---

## Gotcha 2: Data Relationships Must Be Explicitly Defined — They Are Not Inferred from Shared Column Names

**What happens:** AMPscript `Lookup()` and `LookupRows()` functions query a single named DE directly by column value. However, Contact Builder Data Relationships are required for certain contexts — specifically Journey Builder decision splits that filter on related DE data and for Contact Builder audience builder traversals. Without defined Data Relationships, audience builders silently return zero results even when the underlying DE data is correct and the join key is present.

**When it occurs:** When a practitioner creates multiple DEs with a shared ContactKey column and assumes that Marketing Cloud automatically understands their relationship — similar to how a CRM data model with lookup fields works. Marketing Cloud has no such implicit relationship inference. This is most frequently discovered when building a Journey Builder entry split or Contact Builder segment that references an attribute DE and the audience count is unexpectedly zero.

**How to avoid:** For every pair of DEs that need to be traversed together in Contact Builder audience builder or Journey Builder decision splits, define a Data Relationship in Contact Builder > Data Designer. Specify the source DE, join column, target DE, join column, and cardinality. AMPscript LookupRows() called with explicit DE name and column does not require a Contact Builder relationship — but audience builder and Journey Builder data access does.

---

## Gotcha 3: Synchronized DEs Are Read-Only — No Marketing Cloud Process Can Write to Them

**What happens:** Any attempt to write to a Synchronized Data Extension (SDE) fails. This includes Import Activity, Query Activity write targets, AMPscript `InsertDE()` / `UpdateDE()` / `UpsertDE()`, and SSJS HTTP POST. The SDE is strictly a read-only mirror of the CRM source object.

**When it occurs:** When a practitioner builds an Automation that includes a Query Activity writing filtered or transformed contact data into an SDE, intending to use it as a more tailored version of the synced data. Or when they try to use an Import Activity to update SDE field values with marketing-side data (e.g., adding a custom preference column to the Contact SDE). Both fail with errors that are not always descriptive about the root cause.

**How to avoid:** Treat SDEs as input-only sources. Build a writable DE alongside every SDE that needs to be sent to or enriched. Use a Query Activity to read from the SDE and write the needed columns into the writable DE. Add any marketing-managed columns (preferences, scores, segments) to the writable DE, not to the SDE.

---

## Gotcha 4: The 250-Field Cap on Synchronized DEs Silently Drops Fields with No Error

**What happens:** When a CRM object has more than 250 fields selected for sync in Contact Builder, Marketing Cloud silently excludes fields beyond the cap. No error appears in the UI, in sync logs, or in any notification. The SDE column list simply does not include the excluded fields.

**When it occurs:** On CRM orgs with heavily customized objects — especially Contact and Account — where the field count routinely exceeds 250. Practitioners often discover missing personalization data only after live campaign sends return blank merge fields.

**How to avoid:** After initial SDE configuration, immediately inspect the SDE column list in Contact Builder and compare it against the intended field selection. If the object has more than 250 fields, prioritize and select only the fields needed for marketing use. Maintain a documented list of selected vs. excluded fields and refresh this audit whenever CRM admins add new fields to synced objects.

---

## Gotcha 5: Contact Key (SubscriberKey) Must Be Set Before All Subscribers Population — It Cannot Be Retroactively Changed

**What happens:** The SubscriberKey value for a subscriber in All Subscribers is set when the subscriber is first added — either by an import, a send, or a Journey entry. Once set, the SubscriberKey cannot be changed for that subscriber record. If the initial SubscriberKey was email address (or an incorrect ID), the only remediation is to remove the subscriber and re-add them with the correct key, which may affect subscription history and suppression records.

**When it occurs:** When a Marketing Cloud implementation begins with email address as the SubscriberKey (a common shortcut during initial setup) and the team later realizes they need to use Salesforce Contact ID as the stable identifier. Migrating SubscriberKey values in an org with millions of All Subscribers records requires a full re-import and may reset subscription status.

**How to avoid:** Define the SubscriberKey strategy before any subscriber is added to the org. The Salesforce Contact ID (18-character) is the recommended value for orgs using MC Connect. For orgs without CRM integration, use a stable system-generated UUID. Document this decision and enforce it in all DE designs and import configurations from day one.
