# Gotchas — Marketing Cloud Engagement Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: All Subscribers Is Per-BU — Unsubscribes Do Not Cross Business Unit Boundaries

**What happens:** When a subscriber opts out in Business Unit A, that unsubscribe is recorded in BU A's All Subscribers list. Business Unit B's All Subscribers list for the same email address remains in an active subscribed state. The subscriber continues to receive commercial emails sent from BU B.

**When it occurs:** Any Enterprise 2.0 account with multiple BUs. Particularly problematic when two BUs send to overlapping subscriber populations (e.g., a parent company and its subsidiary both emailing the same customer base from separate BUs).

**How to avoid:** If the business requires account-wide unsubscribe propagation, implement a custom solution: use Automation Studio to synchronize unsubscribe records from each BU's All Subscribers data extension to a shared parent data extension, then use that parent extension as a suppression list in all sends. This requires deliberate engineering and is not provided by the platform out of the box.

---

## Gotcha 2: Dedicated IP Reputation Is Unified Across All BUs

**What happens:** An Enterprise 2.0 account with a dedicated IP shares that IP (or IP pool) across all Business Units. If BU B sends a campaign to a stale list with high bounce and spam complaint rates, the resulting IP reputation damage affects deliverability for BU A and every other BU on the account — even if BU A maintains excellent list hygiene.

**When it occurs:** Any time one BU in the account sends to a lower-quality list, reactivates a lapsed segment without re-permission, or sends a high volume burst without a warm-up plan. The damage is not visible in BU A's tracking screens; you must check the account-level IP reputation report or monitor inbox placement via a third-party seed list tool.

**How to avoid:** Establish cross-BU send volume coordination. Any BU planning a large-volume or re-engagement campaign should notify the account administrator so that other BUs can defer planned sends if IP reputation dips. Enforce consistent list hygiene standards (bounce management, suppression of 6+ month inactives) as an account-wide policy, not a per-BU policy.

---

## Gotcha 3: New Business Unit Provisioning Requires a Salesforce Support Case — It Cannot Be Done from Setup

**What happens:** Administrators looking to create a new Business Unit find no self-service option in Setup > Business Units. The interface shows existing BUs but provides no "New" button for adding a BU. Attempts to find a permission or feature activation to unlock BU creation are unsuccessful because the option does not exist.

**When it occurs:** Any time an Enterprise 2.0 account needs to expand to support a new brand, region, or compliance boundary. This is routinely discovered mid-project when the BU was not requested early enough.

**How to avoid:** Include BU provisioning in project planning as a dependency with a minimum 1–3 business day lead time (longer during Salesforce peak periods). Open the support case with: requested BU name, primary locale/language, sending domain, brand contact name and email, and the parent account ID. Do not block all other setup work on BU availability — Sender Profiles, Delivery Profiles, and Send Classifications can be planned in parallel.

---

## Gotcha 4: Custom Roles Are Scoped to the BU Where They Are Created

**What happens:** An administrator creates a custom role in BU A with a tailored permission set (e.g., Content Creator access plus the ability to approve sends). When they navigate to BU B's user management and attempt to assign this custom role, it does not appear in the role dropdown for BU B.

**When it occurs:** Any time a custom role is needed across multiple BUs in an Enterprise 2.0 account. Organizations with many BUs that need consistent custom role definitions discover this during user provisioning.

**How to avoid:** Custom roles must be created independently in each BU where they are needed. Document custom role configurations (name, base role, specific permission overrides) in a runbook so they can be recreated consistently. There is no platform-level role template or import mechanism for custom roles across BUs.

---

## Gotcha 5: Send Classification Type (Commercial vs. Transactional) Is Set at the Time of Classification Creation and Has Broad Legal Implications

**What happens:** A new Send Classification is created without explicitly reviewing the Type field. The default type is Commercial. If the team later uses this classification for triggered order confirmation emails (assuming it would bypass opt-outs because it "feels transactional"), the send still respects commercial unsubscribes, silently failing to deliver to opted-out customers. Conversely, if a classification is set to Transactional and then reused for promotional newsletters, every opted-out subscriber receives the promotional email — a CAN-SPAM violation.

**When it occurs:** During initial account setup when Send Classifications are configured quickly without a documented approval process for the Transactional type. Also occurs during template reuse when a new campaign team inherits an existing MC account setup and does not audit Send Classifications before sending.

**How to avoid:** Create a naming convention that makes the type explicit (e.g., `BrandA-Commercial-Standard`, `BrandA-Transactional-OrderConfirm`). Require written business and legal sign-off before any Send Classification is created with Type = Transactional. Audit Send Classifications during quarterly account reviews to confirm Transactional classifications are only used for legally transactional message types.
