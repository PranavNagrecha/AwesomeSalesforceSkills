# Gotchas — Marketing Cloud Data Sync

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The 250-Field Cap Is Silent — No Error, No Warning, No Log Entry

**What happens:** When a Synchronized Data Source is configured with more than 250 fields selected for a single CRM object, Marketing Cloud syncs the first 250 fields (by selection order in the UI) and silently discards the rest. There is no error in Contact Builder, no entry in the sync activity log, and no notification to the Marketing Cloud admin. The sync is reported as successful.

**When it occurs:** Any time a CRM object with many custom fields is synced. Enterprise orgs with heavily customized Contact or Lead objects frequently exceed the 250-field threshold. The problem manifests days or weeks after initial setup when a personalization field is found to be blank in send previews.

**How to avoid:** After every initial sync configuration or field selection change, manually compare the SDE column list to the intended field selection. Count selected fields before saving — if above 250, prioritize ruthlessly. Remove reporting-only fields from the sync and source them from Salesforce reports instead. Document the excluded fields and the justification for exclusion in the team's sync configuration record.

---

## Gotcha 2: Deleted CRM Records Propagate to SDE and Can Silently Shrink Send Audiences

**What happens:** When a Contact or Lead record is deleted in Salesforce CRM, the deletion is synced to the corresponding SDE record. Any audience built by querying the SDE or joining to it will no longer include the deleted subscriber. If the sendable DE is populated by a Query Activity that sources from the SDE, the deleted subscriber is dropped from future sends without any explicit exclusion step or audit trail.

**When it occurs:** Most commonly during CRM data cleanup initiatives (merging duplicate Contacts, archiving inactive Leads) that coincide with an active Marketing Cloud campaign season. The audience shrink is discovered after send reports show lower-than-expected recipient counts.

**How to avoid:** Design audience queries to filter on active status fields (e.g., `IsDeleted = false`, `Status = 'Active'`) rather than relying on record presence in the SDE as an implicit active indicator. When CRM cleanup is planned, coordinate with the marketing ops team to audit audience counts before and after the cleanup window. Consider maintaining an unsubscribe/suppression DE outside the SDE to retain opt-out records even after CRM deletion.

---

## Gotcha 3: Encrypted CRM Fields and Unsupported Field Types Cannot Sync — No Fallback

**What happens:** Fields marked as encrypted in Salesforce CRM (using Salesforce Shield Platform Encryption) cannot be synced to Marketing Cloud. The field will be excluded from the sync without a clear error message in most configurations. Similarly, binary (Blob) fields, rich text area fields, and certain complex formula fields are not supported by the sync engine and are silently skipped.

**When it occurs:** When a compliance or security team applies Shield Encryption to a field after the sync configuration was already in place (e.g., encrypting `Phone` or `SSN__c` mid-project), the field stops syncing on the next cycle. Marketing Cloud reports referencing that field will show blank values. The issue is often misdiagnosed as a sync failure rather than an encryption policy change.

**How to avoid:** Before configuring the field selection for a synchronized object, run a field audit to identify encrypted fields and unsupported field types. For data that must be available in Marketing Cloud, work with the CRM admin to create a non-encrypted formula or text field that holds a safe representation of the data (e.g., masked last 4 digits). Document which fields are excluded due to encryption and why, so future troubleshooters have context.

---

## Gotcha 4: MC Connect Sync Uses Salesforce API Calls — Peak Hours Can Trigger API Throttling

**What happens:** Each incremental or full sync cycle consumes Salesforce API calls against the connected CRM org's daily API limit. For large orgs with high CRM activity (many record changes triggering automatic syncs) or for full syncs across large objects (millions of Contacts), the sync can consume a significant share of the daily API allocation. When the org approaches its daily API limit, MC Connect sync calls are throttled or dropped, resulting in stale SDEs during business-critical send windows.

**When it occurs:** Most commonly during quarter-end periods when CRM activity peaks (mass Opportunity updates, bulk Contact imports from trade shows) simultaneously with large Marketing Cloud campaign sends. Also occurs when a full sync is triggered manually on a large object without checking current API consumption.

**How to avoid:** Monitor Salesforce API limit consumption in the CRM org (Setup > System Overview > API Requests). Avoid triggering full syncs during peak CRM activity windows. Schedule the MC Connect sync window for off-peak hours where possible. For orgs with very high CRM volume, consider requesting an API limit increase from Salesforce or staggering full syncs across multiple low-activity windows.

---

## Gotcha 5: The Connected User's FLS Settings Silently Gate Which Fields Sync

**What happens:** MC Connect authenticates to Salesforce CRM using a specific Salesforce user (the "connected user" configured during MC Connect setup). If that user's Field-Level Security (FLS) profile does not grant read access to a selected field, the field is excluded from the sync without any error. The SDE column list will be missing the field, and the admin will see no indication of why.

**When it occurs:** When a Salesforce admin adjusts FLS profiles or permission sets after MC Connect is already in use, or when the connected user's profile is changed. New custom fields added to CRM objects also default to hidden on most profiles — the connected user must be explicitly granted read access to new fields before they will sync.

**How to avoid:** The MC Connect connected user should use a dedicated integration profile with broad read access across all objects and fields intended for sync. After adding new CRM fields that need to sync, immediately verify FLS on the connected user's profile. If a field is unexpectedly absent from the SDE, check FLS on the connected user before assuming a sync engine failure.
