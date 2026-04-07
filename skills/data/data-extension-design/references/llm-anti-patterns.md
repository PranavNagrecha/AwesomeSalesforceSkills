# LLM Anti-Patterns — Data Extension Design

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud Data Extension design. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Email Address as the Send Relationship Mapping

**What the LLM generates:** Advice to map the Send Relationship to the `EmailAddress` field in the DE, reasoning that "email address uniquely identifies a subscriber."

**Why it happens:** Email address is the most human-recognizable subscriber identifier. LLMs trained on general marketing content associate "email send" with "email address as identity." The SubscriberKey concept is Marketing Cloud-specific and underrepresented in training data relative to generic email marketing content.

**Correct pattern:**

```
Send Relationship:
  DE field: SubscriberKey (Text 50)
  maps to: Subscriber Key in All Subscribers

Reason: SubscriberKey is the stable, unique identifier in All Subscribers.
Email Address is not guaranteed unique. Subscribers who change their email
address retain their SubscriberKey, preserving suppression and preference data.
```

**Detection hint:** Look for phrases like "map Email Address to the Send Relationship" or "use EmailAddress as the subscriber identifier." Any send relationship advice that does not mention SubscriberKey should be reviewed.

---

## Anti-Pattern 2: Treating Data Extension Primary Keys as Mutable

**What the LLM generates:** Advice to "update the primary key" or "add a field to the primary key" of an existing DE, as if DE schema changes work like SQL ALTER TABLE statements.

**Why it happens:** LLMs generalize from relational database patterns where ALTER TABLE can modify primary keys. Marketing Cloud DEs do not support this. The PK is set at creation and cannot be changed through any UI or API.

**Correct pattern:**

```
If the PK needs to change:
1. Export all data from the existing DE (using a Data Extract or query to a temp DE)
2. Delete or archive the existing DE
3. Create a new DE with the correct PK configuration
4. Reimport the exported data

There is no ALTER TABLE equivalent in Marketing Cloud Data Extensions.
```

**Detection hint:** Look for phrases like "alter the primary key," "add a primary key column to an existing DE," or "modify the PK after creation." These indicate the LLM is applying SQL database semantics incorrectly.

---

## Anti-Pattern 3: Assuming Non-PK Fields Are Indexed for Queries

**What the LLM generates:** SQL query activity code or AMPscript Lookup calls that filter on non-PK fields (e.g., `WHERE SegmentCode = 'VIP'`) without any mention of indexing requirements, presented as if this will perform acceptably on large DEs.

**Why it happens:** In most relational databases and cloud data platforms, indexes can be created by the developer on any column. LLMs default to the assumption that filtering a column is a valid performance pattern without considering whether the underlying store is indexed. Marketing Cloud's indexing model is opaque and requires a Support ticket.

**Correct pattern:**

```
-- Before using this pattern in production:
-- 1. Confirm DE row volume (< 100K: acceptable; > 100K: index required)
-- 2. If row volume > 100K, submit Salesforce Support ticket:
--    Subject: "Request custom index on [DE Name] field [FieldName]"
--    Include: DE name, field name, current/projected row count

SELECT SubscriberKey, EmailAddress
FROM My_Large_DE
WHERE SegmentCode = 'VIP'  -- Only safe if SegmentCode has a custom index
```

**Detection hint:** Look for SQL WHERE clauses filtering on non-PK fields in DEs with no accompanying note about indexing. Also check for AMPscript `LookupRows` with a non-PK filter field and no volume caveat.

---

## Anti-Pattern 4: Using Date as the Sole Primary Key

**What the LLM generates:** A DE schema where a `Date` field is the only primary key field, reasoning that "events are unique by date" or "each day has one record."

**Why it happens:** Date fields are a natural deduplication key for time-series or daily aggregate data patterns. LLMs apply this pattern from general data modeling knowledge without knowing that Marketing Cloud explicitly prohibits a Date-only PK.

**Correct pattern:**

```
-- Wrong: Date as sole PK
DE Schema:
  - ReportDate | Date | Primary Key   <-- INVALID: platform rejects this

-- Correct: composite PK with Date as one component
DE Schema:
  - AccountKey | Text(50) | Primary Key
  - ReportDate | Date     | Primary Key

-- Or: use a Text field to store the date if a single PK is required
  - ReportDateKey | Text(10) | Primary Key  -- e.g., "2026-04-07"
```

**Detection hint:** Look for DE schemas where the only `Primary Key: true` field has type `Date`. The platform will reject this at creation time, but the LLM may generate it confidently.

---

## Anti-Pattern 5: Recommending a Wide "Golden Record" DE

**What the LLM generates:** A single Data Extension with 100–500+ fields consolidating all customer attributes (demographics, behavioral, segment, product interest, communication preferences), justified as "a single source of truth for personalization."

**Why it happens:** The "single source of truth" pattern is a well-established data architecture principle. LLMs apply it without knowing that Marketing Cloud query performance degrades significantly above ~200 columns per DE, that different attribute groups often have different retention requirements, and that SQL JOIN across multiple DEs is fully supported in Automation Studio query activities.

**Correct pattern:**

```
-- Instead of one 350-column DE, use decomposed DEs:

DE: Contact_Core (SubscriberKey PK, EmailAddress, FirstName, LastName)
DE: Contact_Segments (SubscriberKey PK, SegmentCode, ValidFrom, ValidTo)
DE: Contact_ProductInterests (SubscriberKey + ProductCategory PK, Score, LastUpdated)
DE: Contact_Preferences (SubscriberKey PK, OptInEmail, OptInSMS, PreferredLanguage)

-- JOIN in SQL query activity:
SELECT c.SubscriberKey, c.EmailAddress, s.SegmentCode, p.PreferredLanguage
FROM Contact_Core c
JOIN Contact_Segments s ON s.SubscriberKey = c.SubscriberKey
JOIN Contact_Preferences p ON p.SubscriberKey = c.SubscriberKey
WHERE s.SegmentCode = 'VIP'
```

**Detection hint:** Look for a single DE schema with more than 50 fields covering obviously different data domains (demographics + behaviors + preferences + segments). Any "master customer DE" or "golden record DE" recommendation should trigger a decomposition review.

---

## Anti-Pattern 6: Ignoring ResetRetentionPeriodOnImport When Configuring Data Retention

**What the LLM generates:** Data retention configuration advice that sets a retention period (e.g., "delete rows older than 30 days") without mentioning `ResetRetentionPeriodOnImport`, leaving it at the platform default of `false`.

**Why it happens:** Data retention configuration surfaces only in Marketing Cloud's UI and is rarely discussed in general Salesforce documentation. LLMs are likely to know that data retention periods exist but not the nuance of the retention clock reset behavior, which is a Marketing Cloud-specific concept with no common-knowledge analog.

**Correct pattern:**

```
Data Retention Configuration:
  Retention Mode: Row-based (delete individual rows after N days)
  Retention Period: 90 days

  ResetRetentionPeriodOnImport:
    Set to TRUE if: DE receives regular upsert imports and rows should stay
                   alive as long as they are being actively imported
    Set to FALSE if: rows should expire from their creation date regardless
                    of import activity (e.g., time-limited offer eligibility)

  Default is FALSE. Always make an explicit decision — never leave at default.
```

**Detection hint:** Any data retention configuration recommendation that does not mention `ResetRetentionPeriodOnImport` is incomplete. Check whether the import pattern is upsert-based; if it is, the omission of this setting is a probable defect.
