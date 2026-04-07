# LLM Anti-Patterns — Subscriber Data Management

Common mistakes AI coding assistants make when generating or advising on Subscriber Data Management in Marketing Cloud. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Email Address as Subscriber Key

**What the LLM generates:** Advice to use `EmailAddress` as the Subscriber Key when setting up Marketing Cloud, framing it as the natural unique identifier for an email marketing platform.

**Why it happens:** Email address is the most semantically obvious unique identifier in email marketing contexts. LLMs trained on general marketing content see email address described as "the subscriber's unique identifier" in many non-Salesforce sources, and this bleeds into MC-specific advice. The distinction between the routing address (email) and the identity anchor (Subscriber Key) is Salesforce-specific and underrepresented in training data.

**Correct pattern:**

```
Use the 18-character Salesforce CRM Contact or Lead ID as Subscriber Key.
EmailAddress is the routing address — it changes over a contact's lifecycle.
SubscriberKey is the identity anchor — it must be stable for the lifetime of the subscriber.

Example import mapping:
  SubscriberKey = Contact.Id  (18-char CRM ID)
  EmailAddress  = Contact.Email
```

**Detection hint:** Look for `SubscriberKey = EmailAddress` or any recommendation to "use the email address as the unique identifier" in Marketing Cloud setup advice. Also flag advice that treats `EmailAddress` and `SubscriberKey` as synonymous fields.

---

## Anti-Pattern 2: Claiming a Publication List Opt-In Overrides a Global Unsubscribe

**What the LLM generates:** Advice that adding a subscriber to an active publication list will allow them to receive sends even if they globally unsubscribed, or that setting publication list status to Active reactivates a globally unsubscribed contact.

**Why it happens:** LLMs reason by analogy with list-based unsubscribe systems (Mailchimp, Constant Contact) where opting into a specific list does restore deliverability. In those systems, unsubscribes are per-list. Marketing Cloud's All Subscribers global unsubscribe is a separate and overriding authority that does not exist in most other email platforms, so LLMs default to the more familiar list-based mental model.

**Correct pattern:**

```
All Subscribers global unsubscribe = final authority. It CANNOT be overridden by:
  - Adding to an active publication list
  - Updating status in a sendable Data Extension
  - Any automation or API call that doesn't explicitly update All Subscribers status

To restore deliverability for a globally unsubscribed contact:
  1. Obtain documented fresh opt-in consent
  2. Manually update status in All Subscribers to Active
  3. Retain opt-in evidence for compliance audit
```

**Detection hint:** Look for phrases like "add them back to the list to reactivate" or "publication list status overrides global opt-out." Any advice suggesting a publication list operation can reinstate deliverability for a globally unsubscribed contact is wrong.

---

## Anti-Pattern 3: Treating Deduplication as Configurable or Row-Order-Deterministic

**What the LLM generates:** Advice that the practitioner can configure which duplicate row Marketing Cloud selects when a Subscriber Key appears multiple times in a sendable DE, or that the first/last row inserted determines which personalization attributes are used.

**Why it happens:** Most data systems expose deduplication control (e.g., SQL `ROW_NUMBER()`, `DISTINCT ON`, merge rules). LLMs assume Marketing Cloud's send-time deduplication follows similar patterns and that it respects some predictable ordering. The actual platform behavior is non-deterministic for attribute selection across duplicates, which is rarely stated explicitly in documentation.

**Correct pattern:**

```
Marketing Cloud send-time deduplication:
- Sends exactly ONE message per SubscriberKey per send job
- Which row's attributes are used when duplicates exist: NON-DETERMINISTIC
- There is NO configuration to control attribute selection among duplicates

Correct approach: Pre-aggregate the sendable DE BEFORE the send.
Use SQL with explicit ranking to produce one row per SubscriberKey:

SELECT
    SubscriberKey,
    EmailAddress,
    ProductName
FROM (
    SELECT
        SubscriberKey,
        EmailAddress,
        ProductName,
        ROW_NUMBER() OVER (PARTITION BY SubscriberKey ORDER BY EventDate DESC) AS rn
    FROM MySourceDE
) ranked
WHERE rn = 1
```

**Detection hint:** Look for claims that MC "uses the first row" or "respects DE sort order" for duplicate key attribute selection. Also flag any suggestion to leave duplicates in the source DE and rely on platform deduplication for personalization accuracy.

---

## Anti-Pattern 4: Advising Self-Service Subscriber Key Migration

**What the LLM generates:** Instructions for changing an existing subscriber's Subscriber Key by reimporting the contact record with a new key value, or by using the API to update the `SubscriberKey` field on an existing subscriber object.

**Why it happens:** In most systems, changing a record's primary key is a database operation (update or upsert). LLMs apply this reasoning to Marketing Cloud and suggest an upsert or reimport with the new key as the natural migration path. The platform constraint that Subscriber Key changes require Salesforce Support engagement is highly specific and not widely documented in general usage.

**Correct pattern:**

```
Subscriber Key migration in Marketing Cloud:
- Self-service key changes are NOT supported
- Reimporting with a new SubscriberKey creates a DUPLICATE record
  (old key record persists in All Subscribers with all compliance history)
- The new key record is created as a fresh Active subscriber with NO compliance history

Correct approach:
  1. Open a Salesforce Support case requesting Subscriber Key migration
  2. Provide: mapping file (OldKey → NewKey), population size, desired migration date
  3. Support executes the migration in a maintenance window, preserving status records
  4. Post-migration: audit All Subscribers to verify status transfer
```

**Detection hint:** Flag any advice to "reimport with the new key" or "use API to update SubscriberKey." Look for upsert patterns targeting Subscriber Key field as the update target rather than as a stable lookup key.

---

## Anti-Pattern 5: Assuming Cross-BU Unsubscribe Propagation in Enterprise 2.0

**What the LLM generates:** Advice that a global unsubscribe in one Business Unit automatically prevents sends from all other Business Units in the same Enterprise 2.0 account, or that the All Subscribers list is shared across BUs.

**Why it happens:** It is semantically reasonable to assume that a subscriber opting out from "your company's emails" opts out from all emails from that company's marketing system. LLMs reason about this from the subscriber's intent, not from the platform's data isolation architecture. Enterprise 2.0 BU isolation is a platform-specific architectural detail that contradicts the intuitive expectation.

**Correct pattern:**

```
Enterprise 2.0 subscriber isolation:
- Each Business Unit has its OWN All Subscribers list
- Unsubscribe in BU A does NOT propagate to BU B or the parent BU
- No automatic cross-BU suppression exists

Correct approach for cross-BU compliance:
  Option A: API-based propagation
    - When unsubscribe recorded in any BU, call REST API to update status
      in all other relevant BUs
    - Endpoint: PATCH /contacts/v1/contacts/{contactId}
      with status: "Unsubscribed" in each BU context

  Option B: Centralized suppression via Auto-Suppression Lists
    - Maintain a master suppression DE at parent BU level
    - Nightly automation pushes addresses to Auto-Suppression Lists
      in each child BU
```

**Detection hint:** Look for claims that "a global unsubscribe applies across all Business Units" or that "Enterprise 2.0 shares a single All Subscribers list." Also flag advice that treats BU-level unsubscribe as account-level suppression without explicit cross-BU propagation logic.

---

## Anti-Pattern 6: Recommending Held Subscriber Auto-Reactivation Without Bounce Investigation

**What the LLM generates:** Scripts or automation that bulk-reactivate all Held subscribers on a schedule (e.g., "clear Held status after 90 days") without evaluating the underlying bounce reason.

**Why it happens:** In some email systems, a soft bounce or temporary block auto-resolves after a waiting period. LLMs generalize this pattern to Marketing Cloud's Held status, which represents a hard bounce — a permanent delivery failure that requires investigation before reactivation is appropriate. Auto-reactivating hard-bounced addresses damages sender reputation and risks being flagged as spam.

**Correct pattern:**

```
Held subscriber reactivation process:
1. Query _Bounce Data View for Held records and bounce reason:
   SELECT SubscriberKey, EmailAddress, BounceType, BounceSubtype, BouncedDate
   FROM _Bounce
   WHERE BounceType = 'HardBounce'
   ORDER BY BouncedDate DESC

2. Triage by BounceSubtype:
   - "InvalidAddress" / "NoSuchDomain" → do NOT reactivate (address is invalid)
   - "MailboxFull" + hard bounce → investigate (may be temporary, verify with deliverability team)
   - "PolicyViolation" by inbox provider → investigate (may be provider error)

3. Only reactivate addresses with documented evidence of deliverability.
4. Reactivate individually or via API PATCH with audit log entry.
5. Do NOT build automated bulk-reactivation without human review gate.
```

**Detection hint:** Look for scheduled automation or bulk API calls that change subscriber status from Held to Active without a bounce reason evaluation step. Flag any `status = "Active"` bulk update that targets all Held records without filtering by bounce type.
