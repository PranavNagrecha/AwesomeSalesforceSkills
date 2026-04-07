# Examples — Subscriber Data Management

## Example 1: Migrating from Email-Based to CRM-ID-Based Subscriber Key

**Context:** A retail company has been running Marketing Cloud for three years with email address as Subscriber Key. Their CRM (Sales Cloud) is now connected via Marketing Cloud Connect, and they are seeing duplicate subscriber records when customers update their email addresses. Compliance is raising concerns because unsubscribe records tied to old email keys are not being honored when the customer reappears under a new email key.

**Problem:** The org has accumulated thousands of "ghost" subscriber records — old email addresses that hold unsubscribe history while the same physical contact now exists under a new email Subscriber Key with no compliance history. A globally unsubscribed customer who changed their email is receiving marketing sends because the new email key is Active with no suppression.

**Solution:**

This is a Salesforce Support engagement, not a self-service fix. The process follows these steps:

1. Export the current All Subscribers list to a CSV with columns: `SubscriberKey` (current email), `EmailAddress`, `Status`.
2. Join this list against the Sales Cloud Contact export (ContactId, Email) to map old email keys to 18-char Contact IDs.
3. Identify records where `Status = Unsubscribed` or `Status = Held` — these must be migrated with their status intact to preserve compliance state.
4. Open a Salesforce Support case requesting Subscriber Key migration. Provide the mapping file (OldKey → NewKey) and the population size. Support will schedule a maintenance window.
5. Post-migration, audit All Subscribers to confirm statuses transferred correctly, especially global unsubscribes.
6. Update all future imports, automations, and API calls to use ContactId as SubscriberKey going forward.

```
-- Conceptual mapping query (run in Sales Cloud Reports or Data Loader)
-- Export: ContactId (18-char), Email, Unsubscribed__c
-- Match against MC All Subscribers export on Email column
-- Output: OldSubscriberKey (email), NewSubscriberKey (ContactId), Status
```

**Why it works:** Subscriber Key migration via Support preserves the unsubscribe and bounce records mapped to old email keys under the new CRM ID keys. Without this formal migration, re-importing contacts under new keys creates Active subscriber records that bypass existing suppression — a compliance failure that email-based keying makes structurally inevitable.

---

## Example 2: Configuring Auto-Suppression for GDPR Right-to-Erasure Requests

**Context:** A European e-commerce company receives Right-to-Erasure requests under GDPR. Their legal team requires that these email addresses be suppressed from all future Marketing Cloud sends immediately upon request, including sends to lists that haven't been created yet.

**Problem:** The current process manually unsubscribes the contact from each active publication list. But when new lists are created next quarter, these "erased" addresses are at risk of being included if the suppression list is not maintained. Publication list unsubscribes do not extend to new lists automatically.

**Solution:**

1. In Marketing Cloud, navigate to: Email Studio > Subscribers > Suppression Lists > Auto-Suppression.
2. Create a new Auto-Suppression List named `GDPR-Erasure-Requests`.
3. Set the association to apply to all Send Classifications (Commercial and Transactional, if applicable per legal guidance).
4. Import the erasure request addresses using the import wizard or an Automation Studio Import Activity sourced from a dedicated Data Extension.
5. Maintain the source Data Extension as the system of record for erasure requests; schedule a nightly Import Activity to refresh the Auto-Suppression List.
6. Validate suppression by attempting a test send to a known suppressed address — it should appear in the exclusion log, not the sent log.

```
-- Automation: Nightly GDPR Suppression Refresh
-- Activity 1: SQL Query — pull new erasure requests from CRM sync DE
-- Activity 2: Import Activity — load addresses into GDPR-Erasure-Requests suppression list
-- Schedule: Daily at 01:00 BU timezone
```

**Why it works:** Auto-Suppression Lists are evaluated at send time against the current list contents. Because the nightly refresh keeps the list current, any address added to the erasure request DE after list creation will be suppressed on the next scheduled automation run — no manual intervention per send required. Unlike publication list unsubscribes, this suppression applies to every send in the BU regardless of which list is targeted.

---

## Example 3: Diagnosing Subscribers Not Receiving Sends Despite Active Publication List Status

**Context:** A subscriber calls customer support reporting they signed up for a newsletter but never received it. The support agent can see the subscriber is Active on the publication list.

**Problem:** The subscriber is Active on the publication list but has a global unsubscribe recorded in All Subscribers from a previous campaign three years ago. Publication list active status does not override global unsubscribes.

**Solution:**

1. In All Subscribers, search for the subscriber by email address.
2. Check the Status field — if it shows `Unsubscribed`, this is a global unsubscribe, not a per-list unsubscribe.
3. Check the unsubscribe date and source (tracking data) to understand how the global unsubscribe was recorded.
4. If the subscriber confirms they want to receive sends and provides a new explicit opt-in (documented), manually change their All Subscribers status to Active.
5. Retain the opt-in evidence (form submission timestamp, IP, confirmation email) in the CRM record for audit purposes.
6. Run a test send to confirm the subscriber now receives the message.

**Why it works:** The All Subscribers list is the final gate for all sends. Publication list status is evaluated first, but All Subscribers global unsubscribe overrides it completely. There is no configuration to make a send "bypass" All Subscribers — it is by design to ensure a single opt-out in any channel prevents all future sends, satisfying CAN-SPAM, CASL, and GDPR consent revocation requirements.

---

## Anti-Pattern: Using Email Address as Subscriber Key

**What practitioners do:** When setting up Marketing Cloud for the first time, they use the subscriber's email address as the Subscriber Key because it is the most obvious unique identifier for an email marketing system.

**What goes wrong:** Email addresses change. When a subscriber updates their address, the old email key retains all history (unsubscribes, bounces, send history). The new email is treated as a brand-new subscriber with no compliance history. A subscriber who globally unsubscribed via the old address now receives sends via the new address — a direct CAN-SPAM/GDPR violation. Additionally, if the org later enables Marketing Cloud Connect with Sales Cloud, the CRM Contact IDs will not match any existing Subscriber Keys, breaking cross-system contact resolution.

**Correct approach:** Use the 18-character Salesforce Contact or Lead ID as Subscriber Key from day one. This ID is stable across the lifetime of the CRM record regardless of email address changes. If email-based keying is already in production, engage Salesforce Support for a formal migration rather than attempting a workaround.
