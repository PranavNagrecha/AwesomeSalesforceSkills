# Gotchas — Data Cloud Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in Data Cloud architecture.

## Gotcha 1: Identity Resolution Only Works on DMOs with ContactPoint or PartyIdentification Mappings — Incomplete Mapping Silently Excludes Records

**What happens:** Records ingested via a data stream map correctly to the `Individual` DMO and are queryable in Data Cloud. However, those records never appear in any Unified Individual cluster, even when the same person exists in other sources. The identity resolution run completes successfully with no errors — the records are simply absent from all clusters.

**When it occurs:** When a source data stream maps contact fields (including email address) to custom fields on the `Individual` DMO rather than to the `ContactPointEmail`, `ContactPointPhone`, or `PartyIdentification` DMO. The `Individual` DMO alone does not qualify a record for identity resolution participation. Only the three link DMOs carry matchable identifiers that the identity resolution engine reads.

**How to avoid:** Before finalizing any data stream field mapping, confirm that at least one of the following DMOs is populated per source: `ContactPointEmail` (with `emailAddress`), `ContactPointPhone` (with `telephoneNumber`), or `PartyIdentification` (with `partyIdentificationNumber` and `partyIdentificationType`). Verify participation by checking the "Source DMOs" list in the Identity Resolution ruleset configuration — only listed DMOs feed the resolution engine. After adding or correcting a mapping, re-ingest the source and re-run identity resolution.

---

## Gotcha 2: Calculated Insights Have Batch Lag — Time-Sensitive Segment Filters Must Use Streaming Insights

**What happens:** A segment that filters on a Calculated Insight attribute does not reflect activity that occurred after the last CI batch run. The segment appears to be "real-time" because it is published on a continuous schedule, but the filter values are stale by the length of the CI refresh interval (which can be 15 minutes to several hours depending on configuration and volume).

**When it occurs:** Whenever a segment filter uses a CI-derived attribute for a time-sensitive activation use case — abandoned cart re-targeting, in-session behavioral triggers, or post-email-open suppression. The lag is invisible in the segment builder UI; there is no warning that the filter attribute is batch-derived.

**How to avoid:** Classify every segment filter attribute before building the segment: if the attribute is derived from a Calculated Insight, identify the CI's configured refresh schedule and determine whether that lag is acceptable for the use case. For sub-hour time sensitivity, replace the CI attribute with a Streaming Insight that processes the same behavioral events from the real-time ingestion pipeline. Document the effective data freshness SLA for each published segment so stakeholders understand what "real-time" actually means.

---

## Gotcha 3: Each Activation Target Requires a Separate Authenticated Connection Before Segment Publish — Failures Only Surface at Publish Time

**What happens:** A segment is fully configured and scheduled for activation to an ad platform target. At the scheduled publish time, the activation job fails silently. No warning appears during segment build or scheduling. The failure only surfaces in the Activation History log after the publish attempt.

**When it occurs:** When an activation target was created in Data Cloud Setup but its authentication has not been completed (OAuth flow not finished, API credentials not validated, or token expired since last use). Ad platform tokens are particularly prone to expiry — Meta tokens expire after 60 days; Google Ads OAuth tokens require re-consent if API scopes change. Marketing Cloud target connections break when the API user's password changes or the connected app is revoked.

**How to avoid:** Before any segment go-live, navigate to Activation Targets in Data Cloud Setup and verify that every target used in upcoming activations shows a "Connected" status with a recent last-verified timestamp. For file-based targets (SFTP, S3), test write permissions by performing a manual test export. For ad platform targets, re-authenticate if the token age is more than 30 days (half the typical expiry window). Treat activation target authentication as a deployment prerequisite, not a day-of-launch task.

---

## Gotcha 4: Transitive Matching Can Create Unexpectedly Large Identity Clusters from Low-Precision Secondary Match Rules

**What happens:** After adding a secondary fuzzy or compound name match rule to an identity resolution ruleset, the Unified Individual count drops dramatically while average cluster size increases. Some clusters contain hundreds of records that are clearly different individuals. The resolution appears to be "merging everyone together."

**When it occurs:** Transitive matching is applied automatically: if Record A matches Record B under Rule 1, and Record B matches Record C under Rule 2 (fuzzy name), then A, B, and C are placed in the same cluster even though A and C share no direct match. A low-precision secondary rule (fuzzy name, or first name + zip code) acts as a bridge, connecting clusters that the primary rule correctly kept separate. Common names ("John Smith") become massive cluster anchors.

**How to avoid:** After adding any secondary match rule, run identity resolution in test mode and inspect the cluster size distribution. Any cluster larger than 10–15 records warrants investigation unless the use case explicitly calls for household-level resolution. To reduce false merges: raise the fuzzy match threshold, add additional required matching fields (increase the compound rule field count), or add filter conditions to the rule (e.g., only apply the secondary rule to records from sources with confirmed data quality). Never add a fuzzy name rule without validating its impact on cluster distribution first.

---

## Gotcha 5: Re-Running Identity Resolution After a DMO Mapping Change Does Not Retroactively Update Existing Unified Individual Attributes

**What happens:** After changing a reconciliation rule (e.g., switching from Most Frequent to Most Recent for email address), the Unified Individual records continue to show the old reconciled values. The change appears to have had no effect.

**When it occurs:** Reconciliation rule changes are applied on the next full identity resolution run, but the run must be triggered manually or wait for the scheduled recurrence. Incremental runs may not reprocess existing clusters. Additionally, if the underlying DMO data has not changed since the last run, some optimization paths may skip recomputing reconciliation for unchanged clusters.

**How to avoid:** After changing reconciliation rules, trigger a full identity resolution run (not an incremental run) to ensure all existing clusters are reprocessed with the new rule. Validate the outcome by checking a known set of test records where the correct reconciled value is established. Document reconciliation rule configurations in version control — changes to reconciliation rules are metadata changes that should be tracked and tested like code changes.
