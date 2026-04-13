# Gotchas — Analytics Data Manager

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Connected Objects Are Not Queryable — They Must Be Materialized First

**What happens:** Admins enable a Salesforce object for data sync, the Monitor tab shows a successful sync with correct row counts, but the object is invisible in Analytics Studio lens builder, recipe input selector, and dashboard queries. No error is surfaced.

**When it occurs:** Any time a practitioner expects a connected object to behave like a CRM Analytics dataset. This happens most frequently when a new object is enabled for sync and the downstream recipe or dataflow has not yet been created or re-run. It also occurs when a recipe is modified to consume a new connected object but is not executed after the change.

**How to avoid:** Treat connected objects as an internal staging layer only. Every connected object must be consumed by a recipe or dataflow that writes a named output dataset before any analytics layer component can access the data. After enabling an object for sync, always create and run a recipe that materializes the data into a dataset. Validate by confirming the dataset appears in the Data Manager > Datasets tab (or Analytics Studio dataset list) before building any dashboard components.

---

## Gotcha 2: Incremental Sync Silently Misses Records Updated via Related-Object Changes

**What happens:** Records in a connected object show stale field values even though the underlying Salesforce data was updated. The sync completes successfully with no errors. The Monitor tab row count looks plausible. Dashboards display incorrect totals or roll-ups.

**When it occurs:** When a Salesforce object has formula fields or roll-up summary fields whose values depend on changes to related child objects. For example: an Account with a `Total_Revenue__c` roll-up summary from Opportunities is not stamped with a new `LastModifiedDate` when an Opportunity is won. Incremental sync on Account relies solely on `LastModifiedDate` to detect which records changed — so the Account is excluded from the incremental sync batch even though its effective data changed.

**How to avoid:** Identify all objects enabled for incremental sync that have cross-object formula fields or roll-up summaries. For those objects, supplement incremental sync with a scheduled full sync (nightly or weekly depending on data freshness requirements). Document this configuration in a sync runbook so that future admins understand the dual-schedule pattern and its reason. There is no Salesforce setting that makes incremental sync aware of related-object changes — periodic full syncs are the only solution.

---

## Gotcha 3: Remote Connection Credential Expiry Does Not Alert by Default

**What happens:** An external database connection (Snowflake, BigQuery, Redshift) stops syncing because credentials have expired. Sync jobs for that connection fail silently — they appear as errors in the Monitor tab, but no email, in-app notification, or alert is sent to admins unless a monitoring notification has been explicitly configured.

**When it occurs:** When OAuth tokens, passwords, or key pairs used for remote connections reach their expiration date. This is especially common with Snowflake key pairs rotated on a security schedule, BigQuery OAuth tokens with short-lived refresh windows, or Redshift passwords subject to a company password rotation policy.

**How to avoid:** After creating any remote connection, set up Data Manager monitoring notifications (available under Monitor > Notifications) to send alerts on sync failure. Additionally, track credential expiration dates externally (in a team calendar or a secrets manager rotation policy) so the renewal can be coordinated before expiry. When a remote connection sync fails, always check the Monitor tab error detail — the failure reason typically names the authentication problem explicitly.

---

## Gotcha 4: Field-Level Sync Errors Do Not Fail the Object-Level Sync

**What happens:** An object sync completes with status "Completed" and a plausible row count, but one or more fields are silently absent from the connected object schema. Downstream recipes that reference those fields either fail with a "field not found" error or silently drop the field from output datasets.

**When it occurs:** When a Salesforce field that was previously synced is deleted, renamed, or changed to an incompatible type. Also occurs when a custom field is added to the sync configuration but its API name contains a typo or the field is in a managed package with a namespace prefix that was not included in the configuration.

**How to avoid:** After enabling any new object for sync or after making schema changes to a synced object, inspect the connected object's field list in Data Manager (not just the row count) to confirm all expected fields are present. When a recipe or dataflow subsequently fails with a "field not found" error, check the connected object schema first before investigating the recipe logic.

---

## Gotcha 5: The 100-Object Sync Limit Is Org-Wide and Includes All Connections

**What happens:** An attempt to enable a new object for sync fails or the new object cannot be toggled on in the Data Manager UI. No clear error message is displayed in some versions of the UI.

**When it occurs:** When the org has already reached the maximum of 100 objects enabled for sync across all connections (local Salesforce connection plus any remote connections). This limit is cumulative — a Snowflake table counts the same as a Salesforce object toward the 100-object limit.

**How to avoid:** Before enabling new objects, count the total objects currently enabled for sync across all connections in Data Manager. If the count is at or near 100, audit existing enabled objects for ones that are no longer referenced by any active recipe or dataflow and disable them. Maintain a documented inventory of enabled objects and their downstream recipe consumers to make this audit tractable.
