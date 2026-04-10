---
name: marketing-data-architecture
description: "Use this skill when designing or evaluating the overall Marketing Cloud data architecture — covering Data Extension schema design (sendable vs. non-sendable), Contact Key/SubscriberKey linkage across All Subscribers and attribute DEs, Data Relationship definitions for AMPscript Lookup and Query Activity joins, and CRM-to-MC data flow patterns (MC Connect Synchronized DEs vs. SFTP file imports). Trigger keywords: MC data model, relational data extensions, CRM to Marketing Cloud data flow, Contact Key linkage, data architecture, sendable DE design, normalized DE model, SFTP import strategy, synchronized data extension architecture. NOT for CRM (Sales/Service Cloud) custom object or data model design, NOT for individual DE field-level troubleshooting, NOT for Marketing Cloud Connect sync failure diagnosis."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "how should I structure my data extensions for a Marketing Cloud implementation"
  - "what is the right way to link CRM data to Marketing Cloud for personalization"
  - "my Automation Studio query is timing out on large data extensions"
  - "should I use synchronized data extensions or SFTP imports to get CRM data into Marketing Cloud"
  - "how do I set up data relationships so AMPscript can join across data extensions"
  - "we have a flat wide data extension with hundreds of columns and queries are slow"
  - "what is the Contact Key and how does it link all subscribers to data extensions"
tags:
  - marketing-cloud
  - data-extensions
  - contact-key
  - subscriber-key
  - data-relationships
  - mc-connect
  - sftp-import
  - relational-data-model
  - automation-studio
  - crm-to-mc
inputs:
  - "List of data entities to store in Marketing Cloud (contacts, products, orders, events, etc.)"
  - "Existing CRM objects and whether MC Connect is installed"
  - "Send audience requirements (who is being emailed, from what data)"
  - "Personalization fields needed at send time (AMPscript Lookup targets)"
  - "Estimated row volumes per data extension"
  - "Data freshness requirements (near-real-time vs. daily batch acceptable)"
  - "Whether SFTP infrastructure exists or CRM-to-MC Connect is the integration path"
outputs:
  - "Data extension schema design: sendable vs. non-sendable, primary keys, field types"
  - "Contact Key linkage diagram: All Subscribers → sendable DE → attribute DEs"
  - "Data Relationship definitions for AMPscript Lookup() and Query Activity joins"
  - "CRM-to-MC data flow recommendation (MC Connect Synchronized DEs vs. SFTP)"
  - "Normalized DE model vs. wide-table trade-off analysis"
  - "Performance risk assessment (query timeout exposure, indexing recommendations)"
  - "Automation Studio design checklist confirming architecture is within platform limits"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Marketing Data Architecture

This skill activates when a practitioner needs to design or evaluate the overall Marketing Cloud data architecture — covering Data Extension schema patterns, Contact Key/SubscriberKey linkage, Data Relationship definitions, CRM-to-MC integration strategy, and relational model trade-offs. It does NOT cover CRM data model design or individual Data Extension field-level troubleshooting.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether MC Connect is installed and active. This determines whether Synchronized Data Extensions are available as the CRM-to-MC integration path, or whether SFTP file imports are the only option.
- Identify all entities that need to exist in Marketing Cloud: contacts, preferences, products, orders, events. Each is a candidate DE, and the relationship model must be designed before any DE is created.
- The most common wrong assumption is that Marketing Cloud data storage works like a CRM data model. DEs are schema-defined relational tables, not lists, not objects, and not hierarchical records. Joins are not automatic — Data Relationships must be explicitly defined in Contact Builder for AMPscript and Query Activity access.
- The hard performance constraint is the 30-minute Automation Studio query timeout. Large DEs (millions of rows) with non-indexed, non-PK filter columns will reliably hit this limit.

---

## Core Concepts

### Data Extensions as Schema-Defined Relational Tables

Data Extensions (DEs) are the primary data storage mechanism in Marketing Cloud. They are schema-defined relational tables — not mailing lists, not CRM objects. Each DE has a fixed set of typed columns (Text, Number, Date, Boolean, Email, Phone, Decimal, Locale), a required primary key (1–3 columns), and optional data retention settings.

DEs do not have implicit relationships to each other. A DE holding contact attributes does not automatically join to a DE holding order history. Every cross-DE join — whether via AMPscript `Lookup()` / `LookupRows()`, a Query Activity SQL statement, or a Contact Builder Data Relationship — requires the relationship to be explicitly defined or coded.

### Contact Key (SubscriberKey): The Primary Linkage

The Contact Key (also called SubscriberKey) is the universal identifier that connects records across the MC data model:

- **All Subscribers list** — stores one row per subscriber identified by SubscriberKey. This is the master subscriber record used for subscription status, opt-out management, and deliverability.
- **Sendable Data Extensions** — must include a field that holds the SubscriberKey value and must define a Send Relationship mapping that field to `Subscriber Key` in All Subscribers. Without this mapping the DE cannot be used as a send audience.
- **Attribute/lookup Data Extensions** — should use the same Contact Key value as the join key between themselves and the sendable DE, enabling AMPscript and Query Activity to traverse the data model consistently.

The Contact Key value should be set at MC Connect configuration time (usually the Salesforce Contact ID or Lead ID) and must be populated in every DE that participates in the data model. Using email address as the primary join key instead of Contact Key causes deduplication failures when subscribers have multiple email addresses.

### Data Relationships: Explicit Definitions Required

Marketing Cloud does not infer relationships between DEs. To enable AMPscript `Lookup()` / `LookupRows()` and Query Activity joins that traverse multiple DEs, Data Relationships must be explicitly defined in Contact Builder > Data Designer.

Each Data Relationship specifies:
1. The source DE and its join field
2. The related DE and its corresponding join field
3. The relationship cardinality (one-to-one or one-to-many)

Without a defined Data Relationship, AMPscript `Lookup()` will query only within a single DE. Query Activity SQL can technically reference any DE by name, but Contact Builder relationships are required for the data model to be traversable as a unified Contact record for personalization and audience building.

### CRM-to-MC Data Flow Patterns

Two primary patterns exist for moving Salesforce CRM data into Marketing Cloud:

**MC Connect Synchronized Data Extensions (SDEs)**
- Mechanism: Marketing Cloud Connect pulls CRM object records (Contact, Lead, Account, Campaign, CampaignMember, Case, User, eligible custom objects) into read-only SDEs in Contact Builder on a near-real-time or up-to-15-minute scheduled basis.
- Best for: CRM-owned contact and account data where near-real-time freshness is required.
- Constraints: SDEs are read-only (no Import Activity, Query Activity write, or AMPscript insert). Hard cap of 250 fields per object. Encrypted, binary, and rich text CRM fields cannot be synced.

**SFTP File Imports via Import Activity**
- Mechanism: A file is placed on Marketing Cloud's SFTP server (or a connected SFTP) and an Import Activity in Automation Studio ingests it into a standard (writable) DE on a scheduled basis.
- Best for: Data from non-CRM systems, bulk historical loads, or organizations without MC Connect.
- Constraints: Batch only — no near-real-time option. Import frequency is limited by Automation Studio scheduling. File format and column mapping must be maintained manually.

### Normalized Relational Model vs. Wide Flat Table

A normalized DE model uses multiple DEs with shared keys — for example, a Contacts DE, an Orders DE, and a Products DE — joined at query time via Data Relationships or SQL. A wide flat table denormalizes everything into a single DE.

**Normalized model advantages:**
- Each DE is smaller, reducing query scan time.
- Data updates to a single entity (e.g., product name change) only require updating one DE.
- Query Activity SQL against smaller DEs is less likely to hit the 30-minute Automation Studio timeout.

**Wide flat table risks:**
- A single DE with hundreds of columns and millions of rows degrades query performance significantly. Full table scans against non-PK filter columns hit the 30-minute timeout reliably.
- Column count above ~200 per DE causes measurable query performance degradation. The hard maximum is 4,000 columns, but anything above 200 should be split.
- Updating one attribute (e.g., contact preference change) requires re-importing the full wide row, increasing import complexity and error risk.

---

## Common Patterns

### Pattern 1: Normalized Relational DE Model with Contact Key Join

**When to use:** When a Marketing Cloud org needs to send personalized emails referencing data from multiple entities (contacts, orders, preferences, product catalog). Standard architecture for most B2C and B2B implementations.

**How it works:**

1. Create a Contacts DE (sendable) with a `ContactKey` field (Text 18 or 50), PK on ContactKey. Define Send Relationship: ContactKey → All Subscribers Subscriber Key.
2. Create an Orders DE (non-sendable) with columns: OrderID (PK), ContactKey, OrderDate, TotalAmount, Status.
3. Create a Products DE (non-sendable) with columns: ProductID (PK), ProductName, SKU, Category.
4. In Contact Builder > Data Designer, define a Data Relationship: Contacts.ContactKey → Orders.ContactKey (one-to-many).
5. In Automation Studio, build SQL Query Activities that join Contacts + Orders for segment builds, e.g.:

```sql
SELECT c.ContactKey, c.EmailAddress, o.OrderID, o.TotalAmount
FROM Contacts_DE c
INNER JOIN Orders_DE o ON c.ContactKey = o.ContactKey
WHERE o.OrderDate >= DATEADD(day, -30, GETDATE())
```

6. In AMPscript, use `LookupRows()` to pull order rows for a contact at send time:

```ampscript
SET @rows = LookupRows("Orders_DE", "ContactKey", _subscriberkey)
SET @rowCount = RowCount(@rows)
FOR @i = 1 TO @rowCount DO
  SET @row = Row(@rows, @i)
  SET @orderId = Field(@row, "OrderID")
NEXT @i
```

**Why not the alternative:** A flat denormalized DE combining contacts and all order history results in one row per order per contact, causing audience duplication when used as a send audience and performance degradation at scale.

### Pattern 2: MC Connect SDE → Sendable DE Pipeline

**When to use:** When the primary data source is Salesforce CRM (Contact, Lead, Account) and near-real-time data freshness is required for personalization or send audience building.

**How it works:**

1. Confirm MC Connect is installed. In Contact Builder > Synchronized Data Sources, add the Contact and Lead objects. Select only required fields (stay under 250-field cap per object).
2. Create a sendable Contacts DE (writable) with ContactKey as PK and Send Relationship mapped to All Subscribers.
3. In Automation Studio, build a scheduled Query Activity that reads the Contact SDE and writes to the sendable Contacts DE:

```sql
SELECT
  c.Id AS ContactKey,
  c.Email AS EmailAddress,
  c.FirstName,
  c.LastName,
  c.AccountId
FROM Contact_Salesforce c
WHERE c.HasOptedOutOfEmail = 'false'
```

4. Schedule the Query Activity to run every 15–60 minutes to keep the sendable DE fresh.
5. Define Contact Builder Data Relationships from the sendable Contacts DE to any attribute DEs.

**Why not the alternative:** Using the SDE directly as a send audience is not supported — SDEs are read-only and have no Send Relationship defined. Attempting this causes journey entry failures with no clear error.

### Pattern 3: SFTP Batch Import for Non-CRM Data

**When to use:** When data originates outside Salesforce CRM (ERP, e-commerce platform, loyalty system) and MC Connect is not applicable.

**How it works:**

1. Design the target DE schema. Identify PK columns. Confirm field types match Marketing Cloud DE types.
2. Configure the SFTP upload: standardize file naming convention (e.g., `orders_YYYYMMDD.csv`) and encoding (UTF-8).
3. Create an Import Activity in Automation Studio: specify source file pattern, target DE, import type (Add and Update for upserts), and column mapping.
4. Schedule the Automation with an appropriate cadence (daily, hourly). Set file-presence triggers if near-daily freshness is needed.
5. Add a downstream Query Activity step that runs after import to build send audiences from the newly imported data.

**Why not the alternative:** Manual one-time imports via the UI do not scale. Automated Import Activities with file-naming conventions allow the pipeline to run unattended and recover from missing files without manual intervention.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| CRM data (Contact, Lead, Account) needed near-real-time | MC Connect Synchronized DEs → Query into sendable DE | Near-real-time sync; avoids manual file transfers |
| Non-CRM system data (ERP, e-commerce) | SFTP Import Activity | MC Connect only covers Salesforce CRM objects |
| Multiple entities need to be joined at send time | Normalized relational DE model with Data Relationships | Smaller DEs reduce query scan times and timeout risk |
| Single DE over ~200 columns or multi-million rows | Split into normalized DEs with shared Contact Key | Column count above 200 degrades query performance; large wide DEs cause Automation Studio timeout |
| AMPscript needs to look up data from a related DE | Define Data Relationship in Contact Builder | Lookup() and LookupRows() require explicit relationship definitions or will fail silently |
| DE needs to serve as send audience | Sendable DE with Send Relationship to All Subscribers via SubscriberKey | Platform requirement; no Send Relationship = DE cannot be selected as send audience |
| Email address used as primary join key | Replace with Contact Key (Salesforce ID or stable unique ID) | Email is not unique in All Subscribers; SubscriberKey is the stable identifier |
| Query Activity timing out in Automation Studio | Add Support-requested index on filter columns; normalize wide DEs; reduce scan set size | 30-minute hard timeout cannot be extended; only prevention works |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Map all data entities and their relationships** — List every type of data the org needs in Marketing Cloud (contacts, preferences, transactions, product catalog, behavioral events). Draw a relationship diagram identifying how entities connect and what the shared join key is (should be Contact Key / SubscriberKey).
2. **Identify sendable vs. non-sendable DEs** — For each entity, determine whether it will be used as a send audience or purely for personalization/joins. Sendable DEs require a Contact Key field and a Send Relationship mapped to All Subscribers. Design this mapping before creating any DE.
3. **Select CRM-to-MC integration path** — If data is in Salesforce CRM, confirm MC Connect is installed and choose Synchronized DEs as the source. For non-CRM data, design the SFTP import pipeline: file format, naming convention, Import Activity configuration, and schedule.
4. **Define Data Relationships in Contact Builder** — For every DE-to-DE join that AMPscript or Journey Builder audiences need to traverse, create a Data Relationship in Contact Builder > Data Designer. Document each relationship: source DE, join field, target DE, join field, cardinality.
5. **Assess query performance risk** — For each DE, estimate row volume. Any DE with more than 100,000 rows that will be queried on non-PK filter columns is a performance risk. Submit a Salesforce Support ticket for custom indexes on those columns before population. Verify no individual DE exceeds ~200 columns; split if needed.
6. **Build and validate the pipeline end-to-end** — Run the full pipeline: CRM sync or SFTP import → Query Activity segment build → send audience verification. Confirm record counts, personalization field resolution, and absence of Automation Studio timeouts.
7. **Document the data model** — Record the final DE schema, Data Relationships, CRM-to-MC integration path, and Contact Key mapping in a data model document. This is essential for future troubleshooting and onboarding.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All data entities are mapped to specific DEs with documented schemas (columns, types, PK)
- [ ] Every sendable DE has a Contact Key / SubscriberKey field and a Send Relationship mapped to All Subscribers
- [ ] Contact Key (SubscriberKey) is consistently used as the join key across all DEs — not email address
- [ ] Data Relationships are defined in Contact Builder for every DE-to-DE join used by AMPscript or audiences
- [ ] CRM-to-MC integration path is confirmed: MC Connect SDEs or SFTP Import Activity
- [ ] Each DE has fewer than ~200 columns; wide DEs have been split into normalized models
- [ ] Row volume estimates are documented; non-PK query columns on high-volume DEs have Support tickets for custom indexes
- [ ] Automation Studio query activities have been tested and confirmed to complete within the 30-minute timeout
- [ ] Data model document has been created and shared with the marketing operations team

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data Relationships are not automatic — AMPscript Lookup() silently returns no rows without them** — Practitioners often assume that AMPscript `Lookup("OrdersDE", "ContactKey", _subscriberkey)` will work because the OrdersDE exists and contains matching rows. Without a defined Data Relationship in Contact Builder linking the sendable DE to OrdersDE, the Lookup may behave unexpectedly in certain contexts. Always define Data Relationships before relying on cross-DE AMPscript.
2. **Synchronized DEs cannot be send audiences — SDEs are read-only** — MC Connect Synchronized DEs are stored in Contact Builder > Synchronized Data Sources, not the main DE folder. They have no Send Relationship and cannot be written to by any mechanism inside Marketing Cloud. Attempting to use an SDE as a Journey Builder entry source or Email Studio audience will fail. A writable sendable DE fed by a Query Activity reading the SDE is required.
3. **30-minute Automation Studio query timeout has no override** — SQL Query Activities that run more than 30 minutes are automatically terminated with no partial commit. There is no configuration option to extend this timeout. The only prevention is reducing DE size (normalization, archiving old rows) and adding custom indexes via Support ticket. Teams that discover this at campaign launch with million-row DEs have no emergency options.
4. **Email address as SubscriberKey causes deduplication failures** — Some implementations use email address as the SubscriberKey because it is human-readable. All Subscribers does not enforce unique email addresses — only SubscriberKey uniqueness. When a contact changes their email address, the All Subscribers record and any DEs using email as the join key diverge, causing sends to the old address or lost audience members.
5. **Wide flat DEs silently degrade performance before hitting hard limits** — The DE column maximum is 4,000, but query performance degrades measurably above ~200 columns. This degradation does not produce an error — queries just run slower and eventually time out. Teams building wide flat DEs for convenience do not realize the performance cost until they are close to or at the timeout limit.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data model diagram | Entity map showing all DEs, their schemas, and join keys linking them through Contact Key |
| Data Relationship definitions | List of Contact Builder Data Relationship configurations (source DE, field, target DE, field, cardinality) |
| CRM-to-MC integration design | Documented integration path (MC Connect SDE list with field selections, or SFTP Import Activity configurations) |
| Performance risk assessment | Row volume estimates per DE, non-PK query column list, indexing Support ticket status |
| Sendable DE specifications | Schema, Send Relationship mapping, Contact Key linkage for each sendable DE |

---

## Related Skills

- `data/data-extension-design` — Use for field-level DE design decisions: primary key composition, data retention configuration, sendable flag, column types
- `data/marketing-cloud-data-sync` — Use for MC Connect Synchronized DE configuration, sync failure diagnosis, and 250-field limit guidance
- `integration/marketing-cloud-api` — Use when programmatic DE writes via REST API are part of the data pipeline
- `admin/ampscript-development` — Use when AMPscript Lookup() and LookupRows() patterns need to be implemented against the designed data model
