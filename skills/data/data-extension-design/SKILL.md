---
name: data-extension-design
description: "Use this skill when designing, creating, or troubleshooting Marketing Cloud Data Extensions — including sendable vs. non-sendable DE selection, primary key composition, data retention configuration, Send Relationship mapping, and performance indexing. Trigger keywords: data extension, sendable DE, send relationship, DE primary key, data retention, Marketing Cloud data model, DE columns, subscriber key mapping. NOT for CRM (Sales/Service Cloud) custom object design, Marketing Cloud Connect object sync configuration, or Contact Builder attribute group architecture beyond simple relationship type selection."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Security
triggers:
  - "how do I create a sendable data extension in Marketing Cloud"
  - "my data extension primary key is not unique and imports are failing"
  - "what data retention setting should I use for my Marketing Cloud DE"
  - "data extension query is timing out in Automation Studio"
  - "should I use a composite primary key or single field for my data extension"
  - "how do I map a send relationship to subscriber key"
  - "data is disappearing from my data extension after import"
tags:
  - data-extension
  - marketing-cloud
  - sendable-de
  - send-relationship
  - primary-key
  - data-retention
  - mc-data-model
inputs:
  - "Intended use of the DE: sending emails, lookup/join table, or data staging"
  - "Fields required and their data types"
  - "Expected row volume (thousands, millions)"
  - "Import frequency and whether upsert is used"
  - "Whether the DE needs to be queryable by non-PK fields"
  - "Data retention requirements (how long rows should persist)"
outputs:
  - "DE design recommendation: sendable vs. non-sendable, PK composition, field types"
  - "Data retention configuration: mode selection and reset-on-import guidance"
  - "Send Relationship specification for sendable DEs"
  - "Indexing request checklist for non-PK field queries"
  - "Review checklist confirming the DE is production-ready"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Data Extension Design

This skill activates when a practitioner needs to design or troubleshoot a Marketing Cloud Data Extension — covering sendable vs. non-sendable selection, primary key composition, Send Relationship mapping, data retention configuration, and performance indexing strategy. It does NOT cover CRM custom object design or Marketing Cloud Connect sync configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the DE will be used to send emails (sendable) or purely for lookups, joins, or staging (non-sendable). This determines whether a Send Relationship is required.
- Identify the field(s) that uniquely identify each row. Primary key fields cannot be changed after DE creation; choosing them wrong requires recreating the DE.
- Understand import volume and frequency. DEs with millions of rows are at risk of 30-minute Automation Studio query timeouts; large sendable DEs need indexing strategy considered upfront.

---

## Core Concepts

### Sendable vs. Non-Sendable Data Extensions

A sendable DE is one that can be selected as the audience for a Journey Builder entry, an Email Studio send, or an Automation Studio send activity. A non-sendable DE stores data for lookup, personalization, or intermediate staging.

Sendable DEs require exactly one **Send Relationship** that maps a DE field to either `SubscriberKey` or `Email Address` in the All Subscribers list. Without this mapping the DE cannot be selected as a send audience. Non-sendable DEs have no Send Relationship and are used with AMPscript `LookupRows`, SQL query activities, or Data Relationship joins in Contact Builder.

### Primary Key Composition

Every DE row must be uniquely identified by its primary key. Rules that are non-negotiable:

- A DE can have up to 3 primary key columns (composite PK). Using more than 3 is not supported.
- A `Date` field cannot be the sole primary key. It can be part of a composite PK alongside other types.
- Primary key columns **cannot be modified after the DE is created**. Changing the PK requires creating a new DE, exporting data, and reimporting.
- Upsert behavior (import with "Overwrite" or "Add and Update") matches on the composite PK to determine whether to insert or update. If the PK combination is not unique in the source file, imports will fail or produce unpredictable results.
- The platform supports a maximum of 4,000 columns per DE, but performance degrades significantly above approximately 200 columns. Wide DEs should be split or redesigned.

### Data Retention

Data retention is configured per-DE at creation time. Two modes are available:

- **Row-based retention** — rows are deleted after a configured period from the date each row was last modified or created (depending on the "Reset Retention Period on Import" setting).
- **Period-based retention** — all rows in the DE are deleted at a fixed calendar interval (e.g., delete all rows older than 6 months from now).

The most dangerous configuration option is **ResetRetentionPeriodOnImport**. When enabled, every upsert resets the retention clock for that row, extending its life. When disabled, a row's clock starts at creation and is never reset — rows can expire and be deleted even if they were recently touched via import. Misconfiguring this setting is a leading cause of unexpected data loss in production Marketing Cloud orgs.

### Performance and Indexing

Marketing Cloud does not automatically index non-PK fields. Any SQL query activity or AMPscript `Lookup` that filters on a non-PK column performs a full table scan. On large DEs (hundreds of thousands to millions of rows) this will cause:

- Automation Studio query timeouts (hard limit: 30 minutes)
- Slow AMPscript `LookupRows` calls at send time

To index a non-PK field, a Salesforce Support ticket must be submitted — there is no self-service UI. Only a small number of additional indexes are granted per DE. Plan indexing requirements before go-live, not after performance issues appear.

---

## Common Patterns

### Pattern 1: Sendable DE with SubscriberKey Mapping

**When to use:** When the DE will be used as the send audience for email, SMS, or push journeys in Marketing Cloud. Required any time a DE is selected as an entry source or send audience.

**How it works:**

1. Create the DE and include a field to hold the `SubscriberKey` value (typically Text 50 or 254).
2. When creating the DE, set **Is Sendable** to true.
3. Define the Send Relationship: map the `SubscriberKey` field in the DE to `Subscriber Key` in the All Subscribers list.
4. Verify: navigate to Email Studio > Subscribers > Data Extensions, select the DE, and confirm the Send Relationship column shows the mapped field.

**Why not the alternative:** Mapping to `Email Address` instead of `SubscriberKey` causes subscriber deduplication issues when contacts have multiple email addresses. SubscriberKey is the stable unique identifier; Email Address is not guaranteed to be unique in All Subscribers.

### Pattern 2: Composite PK for Transactional/Event DEs

**When to use:** When a single field is not unique per row but the combination of two or three fields is (e.g., OrderID + LineItemID, or ContactKey + EventDate + EventType).

**How it works:**

1. Identify the minimal set of fields (2–3) whose combination is always unique.
2. Mark all fields in the set as Primary Key during DE creation.
3. Set the import activity to "Add and Update" so that reimporting a row with the same PK combination updates the existing row rather than failing or creating a duplicate.

**Why not the alternative:** Using a single auto-increment surrogate key prevents upsert from matching existing rows — every import creates new rows, causing unbounded DE growth and inaccurate send audiences.

### Pattern 3: Staging DE with Time-Bounded Retention

**When to use:** For intermediate DEs that hold data temporarily between Automation Studio steps (e.g., a filtered audience segment built by a query activity).

**How it works:**

1. Create the DE with row-based retention, set to delete rows after the number of days that matches the automation run cadence (e.g., 2 days for a daily automation).
2. Set ResetRetentionPeriodOnImport to `true` so that rows written by each automation run stay alive until the next run replaces them.
3. Do not use period-based retention for staging DEs — it deletes all rows at once, which can empty the DE mid-automation if the period boundary falls inside the automation window.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| DE will be used as a send audience | Sendable DE with Send Relationship mapped to SubscriberKey | Required by platform; Email Address mapping causes dedup issues |
| DE is a lookup or join table | Non-sendable DE | Simpler, no Send Relationship overhead |
| Single unique field exists | Single-field PK | Keep PKs minimal; easier import matching |
| Combination of 2–3 fields is unique | Composite PK (2–3 fields) | Platform-supported; enables upsert accuracy |
| DE has more than ~200 columns | Split into multiple DEs with shared PK | Column count above 200 causes query performance degradation |
| Data should persist until replaced by next import | Row-based retention + ResetRetentionPeriodOnImport = true | Rows stay alive as long as they keep being imported |
| Data should expire regardless of import activity | Row-based retention + ResetRetentionPeriodOnImport = false | Clock starts at creation and is never reset |
| Non-PK field is queried frequently | Submit Support ticket for custom index | No self-service indexing; plan before go-live |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Determine sendable vs. non-sendable** — Confirm whether the DE will be used as a send audience. If yes, identify the field that holds the SubscriberKey or Email Address; it must be part of the DE schema.
2. **Design the primary key** — Identify the minimal set of fields (1–3) whose combination uniquely identifies every row. Confirm no Date-only PK. Verify the PK cannot be changed post-creation; rebuild the DE if an incorrect PK was already applied.
3. **Select and configure data retention** — Choose row-based or period-based retention. If row-based, explicitly decide whether ResetRetentionPeriodOnImport should be true or false and document the rationale. Default off is the safer choice when in doubt.
4. **Define the Send Relationship (sendable DEs only)** — Map the DE's SubscriberKey field to `Subscriber Key` in All Subscribers. Verify in the DE properties that the relationship is shown.
5. **Assess indexing needs** — Identify all non-PK fields that will appear in SQL WHERE clauses or AMPscript Lookup calls. For each, estimate row volume. If volume > 100,000 rows, submit a Salesforce Support ticket for a custom index before the DE is populated.
6. **Validate column count and field types** — Confirm total columns are well below 200 for query performance. Confirm all field types are supported Marketing Cloud DE types (Text, Number, Date, Boolean, Email, Phone, Decimal, Locale); SQL types like BIGINT, TIMESTAMP, or UUID are not valid.
7. **Run a test import and verify** — Import a small test file, confirm row counts, confirm PK uniqueness enforcement, and confirm retention settings are reflected in the DE properties screen.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Sendable DEs have exactly one Send Relationship mapped to SubscriberKey or Email Address
- [ ] Primary key composition is finalized and confirmed immutable (no changes planned post-creation)
- [ ] No `Date`-only primary key is used
- [ ] Data retention mode is explicitly chosen; ResetRetentionPeriodOnImport is documented and set intentionally
- [ ] Column count is below 200 (or split strategy is documented)
- [ ] All field types are valid Marketing Cloud DE types (no raw SQL types)
- [ ] Non-PK fields used in queries have been assessed for indexing; Support ticket submitted if needed
- [ ] Test import completed and row count/PK enforcement verified

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **PK is immutable after creation** — There is no way to change the primary key columns of an existing Data Extension. If the wrong fields were marked as PK, the DE must be recreated and all data re-imported. This has caused multi-day recovery efforts in production orgs.
2. **ResetRetentionPeriodOnImport defaults off — rows can silently expire** — When retention is enabled and ResetRetentionPeriodOnImport is false (the default), imported rows start a one-way countdown from creation. Rows are deleted without warning when the period expires, even if they were recently used. Many teams discover this only after a send audience is unexpectedly empty.
3. **Non-PK fields are not indexed — full table scans are the default** — Any SQL query or AMPscript Lookup filtering on a non-PK field performs a full table scan. On DEs with millions of rows this reliably causes Automation Studio query timeouts (hard 30-minute limit). The only remedy is a Support-ticketed custom index, and index requests are not always granted.
4. **Date cannot be the sole primary key** — The platform rejects a DE configuration where a single Date column is the only primary key. This is not documented prominently in UI error messages, causing confusion when trying to model time-series data.
5. **Send Relationship must map to All Subscribers, not another DE** — Practitioners sometimes attempt to map the Send Relationship to a field in another Data Extension (e.g., a master contacts DE). This is not supported. The Send Relationship must always map to the All Subscribers list's `Subscriber Key` or `Email Address` field.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DE design specification | Field list, PK composition, sendable flag, Send Relationship mapping, data retention settings |
| Indexing request checklist | List of non-PK fields requiring custom indexes with row volume estimates |
| Test import results | Row count, PK enforcement confirmation, retention configuration verification |

---

## Related Skills

- `marketing-cloud-engagement-setup` — Use alongside this skill when the DE is part of initial Marketing Cloud org setup and the broader data model is being established
- `email-studio-administration` — Use when the sendable DE is being connected to a specific email send or list management workflow
- `journey-builder-administration` — Use when the DE will serve as a Journey Builder entry source or decision split data source
