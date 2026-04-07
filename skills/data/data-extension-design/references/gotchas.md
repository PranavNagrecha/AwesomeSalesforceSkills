# Gotchas — Data Extension Design

Non-obvious Salesforce Marketing Cloud platform behaviors that cause real production problems in this domain.

## Gotcha 1: ResetRetentionPeriodOnImport Defaults Off — Rows Silently Expire

**What happens:** When a Data Extension has row-based data retention enabled and `ResetRetentionPeriodOnImport` is left at its default value of `false`, the retention clock for each row starts at the moment the row is first created and never resets. Even if that row is updated via upsert import every day, the clock keeps ticking from the original creation timestamp. When the configured retention period elapses, the row is deleted — silently, with no error or notification. Marketing teams discover this only when a send audience is unexpectedly empty or personalization lookups return null.

**When it occurs:** Any time data retention is enabled on a DE and the DE receives regular upsert imports. It is most dangerous on sendable DEs used as send audiences, because an empty DE causes a zero-send automation run that is easy to miss.

**How to avoid:** Explicitly set `ResetRetentionPeriodOnImport` to `true` whenever the intent is to keep rows alive as long as they keep being imported. Document this setting in the DE design specification. If the intent is for rows to expire from their creation date regardless of import activity (e.g., a time-limited offer DE), document the `false` setting and the business rationale. Never leave it at the default without an explicit decision.

---

## Gotcha 2: Primary Key Cannot Be Changed After DE Creation

**What happens:** The primary key column(s) of a Data Extension are permanent. There is no UI or API to change which fields form the PK after the DE is created. If the wrong fields were selected as PK — or if the PK composition needs to change as business requirements evolve — the DE must be recreated from scratch. Data must be exported from the old DE, the old DE deleted or archived, a new DE created with the correct PK, and data reimported. This is a multi-step, potentially multi-hour operation in production.

**When it occurs:** Most commonly when a DE is initially created with a single-field PK (e.g., `EmailAddress`) that later proves non-unique, or when a composite PK is missing a required field. Also occurs when a date field is erroneously selected as the sole PK (which the platform rejects at creation time, but sometimes practitioners work around using Text fields storing date values, creating a mismatch between field type and semantic use).

**How to avoid:** Finalize PK design before DE creation. Review with the team: Is this field guaranteed unique for every row that will ever exist? If the DE will receive upsert imports, does the PK match the business key in the source system? Lock the PK design in a DE specification document and get sign-off before clicking Create.

---

## Gotcha 3: Non-PK Field Queries Cause Full Table Scans — Indexes Require a Support Ticket

**What happens:** Marketing Cloud does not automatically index any field that is not part of the primary key. SQL query activities in Automation Studio and AMPscript `LookupRows` / `Lookup` calls that filter on non-PK fields perform full table scans. On DEs with more than roughly 100,000 rows, this causes noticeably slow query execution. On DEs with millions of rows, it reliably causes Automation Studio query timeouts (the hard limit is 30 minutes). When a query times out, the automation step fails, downstream steps do not run, and sends can be missed entirely.

**When it occurs:** Any time a non-PK field appears in a SQL `WHERE` clause or as the lookup key in an AMPscript `LookupRows` call, and the DE has significant row volume. This is particularly common when `SegmentCode`, `RegionCode`, `ProductCategory`, or similar classification fields are used as filters.

**How to avoid:** Before go-live, identify all non-PK fields that will appear in SQL WHERE clauses or AMPscript Lookup calls. Estimate the maximum row count. For DEs expected to exceed 100,000 rows with non-PK filter patterns, submit a Salesforce Support ticket requesting a custom index on the specific field(s). Include the DE name, field name, and row volume estimate in the ticket. Index requests are not always granted and are not guaranteed to be fast — plan at least two weeks lead time before production cutover.

---

## Gotcha 4: Send Relationship Must Map to All Subscribers, Not Another DE

**What happens:** Practitioners sometimes attempt to configure the Send Relationship of a sendable DE by pointing to a field in another Data Extension (e.g., a master contacts DE) rather than to the All Subscribers list. The UI may not clearly reject this, but the send will fail or produce subscriber resolution errors at runtime. Marketing Cloud resolves subscriber identity through All Subscribers; the Send Relationship must always terminate there.

**When it occurs:** Most commonly during initial Marketing Cloud setup when teams are trying to build a relational data model and assume the Send Relationship can traverse DE-to-DE relationships the way a SQL JOIN does.

**How to avoid:** When configuring the Send Relationship, always select the field mapping to the `All Subscribers` list specifically. The relationship must map a DE field to either `Subscriber Key` or `Email Address` in All Subscribers. If the DE does not contain a SubscriberKey or Email Address field, add one before configuring the Send Relationship.

---

## Gotcha 5: Maximum 4,000 Columns Exists but Performance Degrades Sharply Above ~200

**What happens:** The platform-documented maximum of 4,000 columns per DE is technically enforced, but performance of query activities and AMPscript lookups degrades significantly well below that limit. DEs with more than approximately 200 columns exhibit slower query execution, higher risk of timeouts, and increased memory pressure on query processing. This degradation is not documented with a precise threshold — it emerges empirically under production load.

**When it occurs:** Most commonly when teams consolidate all customer attributes into a single "golden record" DE to simplify personalization. The DE starts small, grows as new attributes are added, and performance issues appear gradually as row volume increases.

**How to avoid:** Design for vertical decomposition from the start. Group fields by query access pattern: fields always queried together go in the same DE; fields used only in specific journeys go in purpose-built DEs. Use SubscriberKey as the shared key to enable JOIN in SQL activities. Target fewer than 50–100 columns per DE; treat 200 columns as a hard design warning threshold.
