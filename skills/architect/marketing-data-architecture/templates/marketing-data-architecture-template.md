# Marketing Data Architecture — Work Template

Use this template when designing, reviewing, or documenting a Marketing Cloud data architecture for a specific project or implementation.

## Scope

**Skill:** `marketing-data-architecture`

**Request summary:** (fill in what the practitioner or user asked for)

**In scope:**
- [ ] Data Extension schema design
- [ ] Contact Key / SubscriberKey linkage
- [ ] Data Relationship definitions
- [ ] CRM-to-MC integration path (MC Connect / SFTP)
- [ ] Automation Studio query performance assessment

---

## Context Gathered

Answer these before designing anything:

- **MC Connect installed?** Yes / No / Unknown
- **Salesforce CRM objects to expose in MC:** (e.g., Contact, Lead, Account, custom objects)
- **Non-CRM data sources:** (e.g., ERP orders, e-commerce events — list them)
- **SubscriberKey strategy:** (Salesforce Contact ID recommended; document if different)
- **Send audience requirements:** (who is being emailed, from what DE)
- **Personalization fields needed at send time:** (list the AMPscript Lookup targets)
- **Estimated row volumes:** (rough order of magnitude per DE — thousands, hundreds of thousands, millions)
- **Data freshness requirements:** (near-real-time / daily batch / weekly)

---

## Data Extension Inventory

List every DE in the data model. Add rows as needed.

| DE Name | Sendable? | Primary Key Field(s) | Approx Row Count | Source (MC Connect / SFTP / Internal) | Notes |
|---|---|---|---|---|---|
| (e.g.) Contacts_Marketing_DE | Yes | ContactKey | ~500,000 | MC Connect → Query Activity | Send Relationship: ContactKey → All Subscribers |
| (e.g.) Orders_DE | No | OrderID | ~2,000,000 | SFTP daily import | FK: ContactKey |
| (e.g.) Products_DE | No | LineItemID | ~10,000,000 | SFTP daily import | FK: OrderID |
| | | | | | |

---

## Contact Key Linkage

Document how Contact Key flows through the data model:

- **SubscriberKey value used:** (Salesforce Contact ID 18-char / custom UUID / other)
- **All Subscribers Send Relationship:** `[Sendable DE name].[ContactKey field]` → `All Subscribers.Subscriber Key`
- **Attribute DEs using Contact Key as FK:**
  - `[DE Name].[ContactKey field]` links to `[Sendable DE].[ContactKey field]`
  - (add rows as needed)

---

## Data Relationships (Contact Builder)

Define every Data Relationship needed for AMPscript audience traversal and Journey Builder access.

| Relationship Name | Source DE | Source Field | Target DE | Target Field | Cardinality |
|---|---|---|---|---|---|
| (e.g.) Contacts → Orders | Contacts_Marketing_DE | ContactKey | Orders_DE | ContactKey | One-to-Many |
| (e.g.) Orders → Products | Orders_DE | OrderID | Products_DE | OrderID | One-to-Many |
| | | | | | |

---

## CRM-to-MC Integration Path

**Path selected:** MC Connect Synchronized DEs / SFTP Import Activity / Both

**MC Connect (if used):**

| CRM Object | SDE Name | Field Count | Sync Mode | Key CRM Fields Included |
|---|---|---|---|---|
| Contact | Contact_Salesforce | (count) | Automatic | Id, Email, FirstName, LastName, HasOptedOutOfEmail |
| Account | Account_Salesforce | (count) | Scheduled | Id, Name, TierSegment__c |
| (add rows) | | | | |

**SFTP Import (if used):**

| Target DE | File Name Pattern | Import Frequency | Import Type | PK Field |
|---|---|---|---|---|
| Orders_DE | orders_YYYYMMDD.csv | Daily 02:00 UTC | Add and Update | OrderID |
| Products_DE | products_YYYYMMDD.csv | Weekly Sunday | Overwrite | LineItemID |
| (add rows) | | | | |

---

## Performance Risk Assessment

| DE Name | Row Volume | Non-PK Filter Columns Used in Queries | Index Needed? | Support Ticket Submitted? |
|---|---|---|---|---|
| Orders_DE | ~2M | OrderDate, Status | Yes | No |
| Contacts_Marketing_DE | ~500K | AccountTier | No (low volume) | N/A |
| (add rows) | | | | |

**Wide DE check:** Any DE with more than ~200 columns?
- [ ] No DEs exceed 200 columns
- [ ] The following DEs exceed 200 columns and require normalization: (list them)

---

## Automation Studio Pipeline Design

| Automation | Steps | Schedule | Timeout Risk? |
|---|---|---|---|
| CRM Sync Refresh | 1. Query: SDE → Contacts_Marketing_DE | Every 15 min | No (~500K rows) |
| Daily Segment Build | 1. Import: Orders_DE 2. Query: segment build | Daily 03:00 UTC | Review (2M rows) |
| (add rows) | | | |

---

## Review Checklist

Complete before marking the architecture design done:

- [ ] All data entities are mapped to specific DEs with documented schemas
- [ ] Every sendable DE has a Contact Key field and a Send Relationship to All Subscribers
- [ ] Contact Key (SubscriberKey) is used as the join key across all DEs — not email address
- [ ] Data Relationships are defined in Contact Builder for every DE-to-DE join
- [ ] CRM-to-MC integration path is confirmed and documented
- [ ] Each DE has fewer than ~200 columns; split strategy documented if exceeded
- [ ] Row volume estimates recorded; non-PK query columns assessed for indexing
- [ ] Automation Studio query activities assessed for 30-minute timeout risk
- [ ] Support ticket submitted for any required custom indexes
- [ ] Data model document shared with marketing operations team

---

## Notes and Deviations

Record any deviations from the standard pattern and the rationale:

(e.g., "Using email address as SubscriberKey for legacy compatibility — migration planned for Q3.")
