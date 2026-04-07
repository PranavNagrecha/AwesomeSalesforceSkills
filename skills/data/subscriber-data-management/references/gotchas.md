# Gotchas — Subscriber Data Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Subscriber Key Migration Is Not Self-Service

**What happens:** An org that has been using email address as Subscriber Key cannot simply re-import contacts with new Subscriber Key values to change their identity. Attempting to do so creates duplicate subscriber records: the original email-keyed record remains in All Subscribers with its unsubscribe/bounce history, while the new CRM-ID-keyed record is created as a fresh Active subscriber with no compliance history.

**When it occurs:** This bites when an org decides to switch from email-based to CRM-ID-based Subscriber Keys after initial deployment — often when Marketing Cloud Connect is first enabled and the team realizes keys need to align with CRM IDs. It also occurs during data migrations or platform consolidations.

**How to avoid:** Plan the Subscriber Key strategy before loading any subscriber data. If migration is required, engage Salesforce Support to run the official Subscriber Key migration process, which maps old keys to new keys while preserving status records. Budget weeks for this engagement, not hours. Never attempt to self-service this by reimporting with new key values.

---

## Gotcha 2: Enterprise 2.0 BUs Do Not Share All Subscribers Lists

**What happens:** In an Enterprise 2.0 account with a parent BU and multiple child BUs, each BU maintains its own independent All Subscribers list. A global unsubscribe recorded in Child BU A does not propagate to Child BU B or to the parent BU. Suppression and unsubscribe state is isolated per BU.

**When it occurs:** This causes compliance failures when sends are distributed across multiple BUs for the same subscriber population. A subscriber who unsubscribes from a send originating in the "US" BU may still receive sends from the "EU" BU because the opt-out was not recorded there. This is especially risky in orgs where BU segmentation follows geography or brand rather than subscriber population.

**How to avoid:** For Enterprise 2.0 setups, design a centralized opt-out sync: when a global unsubscribe is recorded in any BU, propagate it to all relevant BUs via API or an Automation Studio process using the REST API subscriber status endpoint. Alternatively, use a shared Data Extension at the parent BU level as the suppression source and push updates to child BU Auto-Suppression Lists nightly.

---

## Gotcha 3: Deduplication Does Not Guarantee Consistent Personalization Attribute Selection

**What happens:** When a sendable Data Extension contains multiple rows with the same Subscriber Key (which is legal and common in segment-based sends), Marketing Cloud sends exactly one message per Subscriber Key per send job. However, the platform does not document or guarantee which row's field values are used for personalization when duplicates exist. In practice, the behavior can vary and is non-deterministic.

**When it occurs:** This affects any send where the source DE is built from a join or union that can produce multiple rows per subscriber — for example, a product recommendation DE where each subscriber has multiple recommended products, or a multi-event trigger where the subscriber qualifies via several criteria. If personalization fields differ across duplicate rows (e.g., different `ProductName` values), the rendered email may use any of them.

**How to avoid:** Pre-aggregate the sendable DE to one row per Subscriber Key before the send. Use SQL in Automation Studio to apply explicit ranking logic (e.g., `ROW_NUMBER() OVER (PARTITION BY SubscriberKey ORDER BY EventDate DESC)`) and filter to `RowNum = 1`. Never rely on row insertion order or DE sort order to control which duplicate row is selected by the platform.

---

## Gotcha 4: Held Status Requires Manual Intervention — It Does Not Auto-Clear

**What happens:** When a subscriber's email address generates a hard bounce, Marketing Cloud sets their status to Held. A Held subscriber is permanently suppressed from all future sends in that BU. Unlike soft bounces, there is no automatic retry or auto-recovery from Held status. Even if the underlying address issue is resolved (e.g., an inbox provider mistakenly rejected the message), the subscriber remains Held until explicitly reactivated.

**When it occurs:** This frequently hits when a batch of contacts is imported from a list with known deliverability issues, or when a corporate email domain has a temporary misconfiguration that causes a wave of hard bounces. The Held status persists indefinitely and silently suppresses legitimate subscribers who would have received future sends.

**How to avoid:** Build a Held subscriber review process into the operational calendar — at minimum quarterly. Use the Data View `_Bounce` to query bounce reasons and distinguish genuine hard bounces (invalid address, domain does not exist) from false positives (temporary configuration errors, inbox provider anomalies). Reactivate only with documented evidence. For bulk reactivation, use the REST API PATCH endpoint with explicit status change and maintain an audit log of each reactivation with justification.

---

## Gotcha 5: Auto-Suppression Lists Are Email-Address-Based, Not Subscriber-Key-Based

**What happens:** Auto-Suppression Lists match against the email address at send time, not the Subscriber Key. This means a suppressed address is excluded from sends even if the subscriber has a different Subscriber Key (e.g., they were re-imported under a CRM ID key). Conversely, if a suppressed address is re-registered under a brand-new email, the new address is not automatically suppressed — only the original address appears in the Auto-Suppression List.

**When it occurs:** This creates gaps when orgs assume Auto-Suppression protects against a contact re-entering the system under a different identity. It also means that in CRM-ID-keyed orgs, a Subscriber Key change does not bypass an existing Auto-Suppression List entry for the address — the address is still matched and suppressed regardless of the key change. Both failure modes (false assumption of key-based protection, and surprise address-based suppression after key migration) cause production issues.

**How to avoid:** Understand that Auto-Suppression is always address-based. Design compliance suppression workflows accordingly: maintain address-level exclusion lists for regulatory requirements (since addresses are what email infrastructure routes on), and handle identity-level suppression separately through All Subscribers status management. Document this distinction for any team managing erasure or suppression requests.
