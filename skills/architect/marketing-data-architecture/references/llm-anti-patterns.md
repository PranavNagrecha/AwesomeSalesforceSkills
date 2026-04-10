# LLM Anti-Patterns — Marketing Data Architecture

Common mistakes AI coding assistants make when generating or advising on Marketing Data Architecture. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Direct Sends Against Synchronized Data Extensions

**What the LLM generates:** Advice to use a Synchronized Data Extension (SDE) directly as a Journey Builder entry source or send audience: "Select the Contact_Salesforce synchronized DE as your entry source in Journey Builder."

**Why it happens:** LLMs conflate Synchronized DEs (read-only MC Connect mirrors) with regular writable Data Extensions. Training data describes SDEs as containing contact records, so the model infers they can be used anywhere a contact DE is used.

**Correct pattern:**

```
Synchronized DEs are read-only and have no Send Relationship defined.
To send to CRM contacts, build a writable sendable DE fed by a Query Activity:

1. Create Contacts_Marketing_DE (sendable) with ContactKey PK, Send Relationship → All Subscribers.SubscriberKey
2. Create a Query Activity:
   SELECT Id AS ContactKey, Email AS EmailAddress, FirstName, LastName
   INTO Contacts_Marketing_DE
   FROM Contact_Salesforce
   WHERE HasOptedOutOfEmail = 'false'
3. Schedule the Query Activity in Automation Studio
4. Use Contacts_Marketing_DE as the Journey Builder entry source
```

**Detection hint:** If generated advice references a `_Salesforce` suffixed DE as a send audience or Journey entry, flag it.

---

## Anti-Pattern 2: Using Email Address as SubscriberKey or Join Key

**What the LLM generates:** DE schema definitions or import configurations that use `EmailAddress` as the primary key and as the foreign key linking DEs: `Contacts_DE.EmailAddress → Orders_DE.EmailAddress`.

**Why it happens:** Email address is the most visible identifier in email marketing contexts. LLMs trained on generic email marketing content associate email address with subscriber identity, not understanding that Marketing Cloud's All Subscribers list uses a distinct SubscriberKey that must be a stable unique identifier.

**Correct pattern:**

```
-- WRONG: Email as PK and join key
Contacts_DE: EmailAddress (PK), FirstName, LastName
Orders_DE: OrderID (PK), EmailAddress (FK), TotalAmount

-- CORRECT: Contact Key as PK and join key
Contacts_DE: ContactKey (PK, TEXT 18), EmailAddress, FirstName, LastName
  Send Relationship: ContactKey → All Subscribers.Subscriber Key

Orders_DE: OrderID (PK), ContactKey (FK, TEXT 18), TotalAmount

Data Relationship defined: Contacts_DE.ContactKey → Orders_DE.ContactKey
```

**Detection hint:** Any schema or import config where `EmailAddress` is marked as PK or used as a FK in a join condition should be flagged for review.

---

## Anti-Pattern 3: Omitting Data Relationship Definitions for Cross-DE AMPscript

**What the LLM generates:** AMPscript that calls `LookupRows("RelatedDE", "ContactKey", _subscriberkey)` without any mention of needing to define a Data Relationship in Contact Builder, implying the AMPscript alone is sufficient for the data model to work.

**Why it happens:** AMPscript `LookupRows()` with an explicit DE name and column does technically query a DE without requiring a Contact Builder Data Relationship when called directly. LLMs overgeneralize this to all cross-DE access patterns, missing that Contact Builder audience builder traversals and Journey Builder data access DO require explicit Data Relationships.

**Correct pattern:**

```
For AMPscript LookupRows() called at send time:
  → Works without a Contact Builder Data Relationship (queries DE directly by column)

For Contact Builder Audience Builder filters on related DE attributes:
  → Requires explicit Data Relationship defined in Contact Builder > Data Designer

For Journey Builder decision splits using related DE data:
  → Requires explicit Data Relationship defined in Contact Builder > Data Designer

Best practice: Always define Data Relationships for any DE-to-DE join in the data model,
regardless of whether the immediate use case requires it. This prevents silent failures
when the data model is accessed through audience builder or Journey Builder later.
```

**Detection hint:** Any architecture doc that describes a multi-DE model without a "Define Data Relationships in Contact Builder" step is likely incomplete.

---

## Anti-Pattern 4: Recommending Wide Flat DEs for Simplicity

**What the LLM generates:** Schema designs that denormalize all contact + order + product + preference data into a single DE with 100–300+ columns, justified as "simpler to query" or "avoids joins."

**Why it happens:** In general database contexts, denormalized flat tables can simplify read-heavy workloads. LLMs apply this heuristic to Marketing Cloud without accounting for the 30-minute Automation Studio query timeout and the Marketing Cloud-specific performance degradation above ~200 DE columns.

**Correct pattern:**

```
AVOID: Single wide DE
  Contacts_Orders_Products_DE (250+ columns, multi-million rows)
  → Query timeouts at scale
  → Updating one attribute requires reimporting millions of rows

PREFER: Normalized model with shared Contact Key
  Contacts_DE     — contact identity, ~20 columns
  Orders_DE       — order transactions, ~10 columns, FK: ContactKey
  Products_DE     — line items, ~8 columns, FK: OrderID
  Preferences_DE  — opt-in flags, ~15 columns, FK: ContactKey

  Each DE scans only its own rows.
  Query Activity joins only the two DEs needed for a given segment.
  Column counts well below 200 per DE.
```

**Detection hint:** Any single DE schema with more than 50 columns or combining data from more than two distinct business entities (contact + order + product) should be flagged for normalization review.

---

## Anti-Pattern 5: Treating SFTP Imports as Near-Real-Time

**What the LLM generates:** Architecture recommendations that rely on SFTP file imports to achieve near-real-time data freshness (e.g., "schedule your SFTP import every 5 minutes for real-time contact data"), or that recommend SFTP as an alternative to MC Connect for CRM contact data without noting the latency trade-off.

**Why it happens:** LLMs are familiar with SFTP as a data integration mechanism and may not differentiate between MC Connect's event-triggered sync and Automation Studio's scheduled import cadence. The model may assume that "frequent scheduling" compensates for batch latency.

**Correct pattern:**

```
SFTP Import Activity via Automation Studio:
  → Minimum practical cadence: ~15–30 minutes (automation scheduling + file transfer time)
  → Not event-driven — data freshness depends on upstream file generation frequency
  → Not appropriate for compliance-sensitive data (e.g., opt-out status)

MC Connect Synchronized DEs:
  → Near-real-time (minutes) for CRM-owned Contact, Lead, Account, Campaign objects
  → Event-triggered: syncs when CRM record changes
  → Required for scenarios where CRM opt-out must be reflected in MC within minutes

Correct guidance:
  - For CRM contact and opt-out status: MC Connect Synchronized DEs (near-real-time)
  - For non-CRM data or bulk historical loads: SFTP Import Activity (batch)
  - Never recommend SFTP for opt-out or subscription status that must propagate quickly
```

**Detection hint:** Any recommendation to use SFTP for "real-time" or "near-real-time" CRM data, or to schedule SFTP imports more frequently than hourly as an alternative to MC Connect, should be flagged.

---

## Anti-Pattern 6: Omitting Send Relationship on Sendable DEs

**What the LLM generates:** DE schema designs or CREATE DATA EXTENSION configurations that mark a DE as "sendable" but do not specify a Send Relationship mapping the SubscriberKey field to All Subscribers. The generated config assumes that marking the DE as sendable is sufficient.

**Why it happens:** LLMs understand the concept of a sendable DE but miss the two-part requirement: (1) the sendable flag AND (2) the explicit Send Relationship definition mapping a specific DE column to All Subscribers. Without the Send Relationship, the DE cannot actually be selected as a send audience at runtime.

**Correct pattern:**

```
WRONG (incomplete):
  DE: Contacts_DE, Is Sendable: true, ContactKey TEXT(18)
  → Missing Send Relationship — DE cannot be used as send audience

CORRECT:
  DE: Contacts_DE, Is Sendable: true, ContactKey TEXT(18)
  Send Relationship:
    DE field: ContactKey
    relates to: Subscriber Key
    on: All Subscribers

This two-part configuration is required. The Send Relationship must be defined
during DE creation (or via the Edit Data Extension UI before the first send).
```

**Detection hint:** Any sendable DE configuration that does not explicitly specify a Send Relationship field mapping should be flagged as incomplete.
