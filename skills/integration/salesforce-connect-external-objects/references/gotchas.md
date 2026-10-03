# Gotchas - Salesforce Connect External Objects

Non-obvious behaviors that cause real production problems. "Apex Guide" means the Apex Developer Guide, Version 67.0, chapter Salesforce Connect. "SOQL Reference" means the SOQL and SOSL Reference, Version 67.0. "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: There Are No Triggers on External Objects

**What happens:** A design depends on a trigger to react when an external order changes, and the trigger can never be created.

**When it occurs:** "These features aren't available for external objects: Apex-managed sharing; Apex triggers (However, you can create triggers on external change data capture events from OData 4.0 connections.)"

**How to avoid:** For OData 4.0 sources, subscribe with a trigger on the `__ChangeEvent` object, which can be packaged and tested with `Test.getEventBus().deliver()`. For other adapters, move the reaction to the source system or a middleware event.

**Source:** Apex Guide, Apex Considerations for Salesforce Connect External Objects; External Change Data Capture Packaging and Testing.

---

## Gotcha 2: Plain DML Does Not Work on External Objects in Apex

**What happens:** `insert order;` on a `SalesOrder__x` fails, or a portal user's insert fails from Apex while the same insert works from the UI.

**When it occurs:** "Apex can't execute standard insert(), update(), or create() operations on external objects." Apex uses asynchronous methods such as `Database.insertAsync()`, which queue a background job; `BackgroundOperation` shows job status. "Database.insertAsync() methods can't be executed in the context of a portal user"; use `Database.insertImmediate()` there. Writes from the UI and API are synchronous. The data source must have `isWritable` set, because external objects are read-only by default.

**How to avoid:** Use the async or immediate methods, store the async locator from `Database.getAsyncLocator(saveResult)`, and monitor `BackgroundOperation`. Set `isWritable` deliberately; the cross-org adapter supports it only from API 39.0.

**Source:** Apex Guide, Writable External Objects; Apex Considerations for Salesforce Connect External Objects; Metadata API, ExternalDataSource (`isWritable`).

---

## Gotcha 3: Standard SOQL Features Fail on `__x`

**What happens:** A report, LWC, or Apex query that works on a custom object throws when pointed at the external object.

**When it occurs:** External objects do not support `AVG()`, `COUNT(fieldName)`, `HAVING`, `GROUP BY`, `MAX()`, `MIN()`, `SUM()`, `EXCLUDES`, `FOR VIEW`, `FOR REFERENCE`, `INCLUDES`, `LIKE`, `toLabel()`, `TYPEOF`, or `WITH`. A subquery that involves external objects fetches at most 1,000 rows, and a query can have up to 4 joins, each a separate round trip. With OData adapters, `ORDER BY` is not supported in relationship queries and `NULLS FIRST`/`NULLS LAST` are ignored.

**How to avoid:** Check every query against the list before committing to virtualization. Because `WITH` is unsupported, enforce user mode with `AccessLevel.USER_MODE` on `Database.query` or `Database.queryWithBinds` rather than a `WITH USER_MODE` clause. The skill checker flags these clauses as `SC-SOQL-01`.

**Source:** SOQL Reference, SOQL Object Limits and Limitations (External objects); Relationship Query Limitations.

---

## Gotcha 4: `COUNT()` Needs Request Row Counts

**What happens:** `SELECT COUNT() FROM Order__x` fails or a list view cannot show totals.

**When it occurs:** For OData 2.0 and 4.0 adapters, "the COUNT() aggregate function is supported only on external objects whose external data sources have Request Row Counts enabled. Specifically, the response from the external system must include the total row count of the result set." In metadata, Request Row Counts is `inlineCountEnabled` inside `customConfiguration`.

**How to avoid:** Enable `inlineCountEnabled` and confirm the OData service returns the count. If it cannot, design without totals.

**Source:** SOQL Reference, SOQL Object Limits and Limitations; Metadata API, ExternalDataSource (customConfiguration for OData 2.0 or 4.0).

---

## Gotcha 5: Batch Apex Over External Objects Needs Paging Decisions

**What happens:** A batch job processes some external records twice or skips others, or fails to start.

**When it occurs:** With `Database.QueryLocator` over an OData adapter, Request Row Counts must be enabled and each response must include the total. With client-driven paging (Server Driven Pagination off), records added during the job can be processed twice and records deleted can cause others to be skipped. With Server Driven Pagination on, the runtime batch size is the smaller of the scope parameter (default 200) and the page size the source returns. An iterable batch over an external source stores the external records in Salesforce while the job runs and removes them when it completes.

**How to avoid:** Turn on server-driven paging for large sets, have the source return pages of 200 or fewer, and treat iterable batches as a temporary data residency event for compliance review.

**Source:** Apex Guide, Apex Considerations for Salesforce Connect External Objects (Important note and batch bullets).

---

## Gotcha 6: External ID and Name Values May Be Stored in Salesforce

**What happens:** A privacy review finds patient identifiers in Salesforce even though the data was supposed to stay external.

**When it occurs:** "Don't use sensitive data as the values of the External ID standard field or fields designated as name fields, because Salesforce sometimes stores those values." External lookup fields on child records store and display parent External ID values, and Salesforce stores the External ID of each retrieved row for internal use, except with high-data-volume data sources.

**How to avoid:** Use surrogate keys for External ID and name fields. Consider the High Data Volume option (`noIdMapping`) when row-level ID storage is a concern.

**Source:** Apex Guide, External IDs for Salesforce Connect External Objects.

---

## Gotcha 7: Relationship Direction Decides the Lookup Type

**What happens:** A related list stays empty because the team created the wrong kind of lookup.

**When it occurs:** An indirect lookup "links a child external object to a parent standard or custom object", matching against a parent field named in `referenceTargetField` that "must have both externalId and unique set to true". An external lookup "links a child standard, custom, or external object to a parent external object" and matches on the parent's External ID standard field.

**How to avoid:** Decide the parent first, then the lookup type. For indirect lookups, make the parent field External ID and unique before creating the relationship.

**Source:** Apex Guide, Apex Connector Framework Examples (relationship definitions); Metadata API, CustomField (`referenceTargetField`).

---

## Gotcha 8: Search Settings Are Overwritten by Sync, and OData Search Drops Operators

**What happens:** An admin turns off search on one external object and it comes back on after a sync; a user's `OR` search returns nothing.

**When it occurs:** "To include an external object in SOSL and Salesforce searches, enable search on both the external object and the external data source. However, syncing always overwrites the external object's search status to match the search status of the external data source." OData adapters "don't support logical operators in a FIND clause"; the whole string is sent as one case-sensitive phrase after removing punctuation except hyphens. Only text fields are searchable, and external objects must be named in a `RETURNING` clause.

**How to avoid:** Set search at the data source level. Tell users that OData-backed search is phrase search.

**Source:** SOQL Reference, SOSL Limits on External Object Search Results.

---

## Gotcha 9: Custom Adapter Code Has Its Own Traps

**What happens:** After a code change, the custom adapter disappears from the external data source Type picklist and the external object tabs vanish; or adapter tests fail.

**When it occurs:** "If you change and save a DataSource.Connection class, resave the corresponding DataSource.Provider class." "DML operations aren't allowed in the Apex code that comprises the custom adapter." All Apex governor limits apply, test methods cannot make callouts, and tests with static SOQL against external objects fail. Strings longer than 255 characters map to long text area fields and Doubles lose precision beyond 18 digits.

**How to avoid:** Resave the Provider in the same deployment, keep the adapter read-and-callout only, mock callouts, use dynamic SOQL in tests, and use Decimal for high-precision numbers.

**Source:** Apex Guide, Considerations for the Apex Connector Framework.

---

## Gotcha 10: OAuth Access Without a Refresh Token Stops When the Token Expires

**What happens:** The external objects work for an hour after setup and then fail for every user.

**When it occurs:** Salesforce refreshes OAuth tokens automatically only when a valid refresh token exists from an earlier flow. "If the authentication provider doesn't provide a refresh token, access to the external system is lost when the current access token expires."

**How to avoid:** Request offline access from the provider (for a Salesforce provider, add `refresh_token` to the default scopes; for Google, append `access_type=offline`). In a custom adapter, throw `DataSource.OAuthTokenExpiredException` so Salesforce refreshes and retries.

**Source:** Apex Guide, OAuth for Salesforce Connect Custom Adapters.

---

## Gotcha 11: Certificates Do Not Travel in Packages

**What happens:** A packaged external data source fails in the subscriber org.

**When it occurs:** "Certificates aren't packageable. If you package an external data source that specifies a certificate, make sure that the subscriber org has a valid certificate with the same name."

**How to avoid:** Document the certificate name as an install prerequisite and check it in a post-install step.

**Source:** Apex Guide, External Change Data Capture Packaging and Testing.

---

## Gotcha 12: Availability and Latency Belong to the Architecture

**What happens:** Users think Salesforce is slow or broken, but the external system is the bottleneck.

**When it occurs:** Pages issue repeated or broad queries against external data; every query and every join is a round trip to the source.

**How to avoid:** Treat latency budgets and external uptime as design inputs, keep external objects off high-traffic layouts, and replicate the hot subset when users need local speed.

**Source:** SOQL Reference (each join is a separate round trip); practice guidance for the rest.
