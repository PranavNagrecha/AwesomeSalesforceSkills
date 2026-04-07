# Well-Architected Notes — Subscriber Data Management

## Relevant Pillars

- **Trust** — Subscriber data management is directly load-bearing for regulatory compliance. Global unsubscribes, suppression lists, and Held status records are the technical enforcement mechanism for CAN-SPAM, GDPR, and CASL opt-out rights. Failures here are not operational inconveniences — they are legal violations. Trust is the primary pillar for this skill.

- **Security** — Subscriber Key design affects cross-system identity resolution. Using a stable internal ID (CRM Contact/Lead ID) rather than a mutable external value (email address) limits the attack surface for identity confusion and prevents compliance state from being bypassed through address changes. Auto-Suppression Lists enforce channel-level access control: ensuring suppressed addresses cannot receive sends even if they enter the system under new identities.

- **Reliability** — Deduplication behavior at send time must be understood and designed for. Non-deterministic attribute selection when duplicate Subscriber Keys exist in a sendable DE is a reliability risk for personalization accuracy. Held subscriber accumulation without a review process creates silent reliability failures: legitimate subscribers silently stop receiving sends with no alerting.

- **Operational Excellence** — Subscriber status management requires ongoing operational processes: Held subscriber review, suppression list refresh, cross-BU opt-out propagation in Enterprise 2.0 accounts. These are not one-time configurations but recurring maintenance activities. Automating suppression list refresh and building Data View-based subscriber health dashboards are the operational excellence investments that prevent compliance drift.

- **Scalability** — Subscriber Key strategy chosen at org inception is extremely expensive to change at scale. The migration path requires Salesforce Support engagement, maintenance windows, and careful status preservation. The scalability implication is that the right Subscriber Key choice (CRM ID) must be made before the subscriber population grows, because the cost of migration scales linearly with subscriber count and complexity of the send history.

---

## Architectural Tradeoffs

### Subscriber Key: Email vs. CRM ID

The choice of Subscriber Key is the highest-leverage architectural decision in Marketing Cloud subscriber data management. Email is intuitive and immediately available; CRM ID requires CRM integration to be in place before contact loading begins.

The tradeoff: email-based keys are operationally simpler at day one but accumulate technical debt proportional to the rate of email address changes in the subscriber population. CRM ID keys require upfront integration work but create a stable identity foundation that survives email address lifecycle events.

For any org with a connected CRM (Sales/Service Cloud) or any compliance requirement (GDPR, CAN-SPAM, CASL), the correct choice is CRM ID. The only legitimate reason to use email as Subscriber Key is in isolated marketing-only deployments with no CRM, and even then, the risk of later migration cost should be documented.

### Global Unsubscribe vs. Publication List Opt-Out

Global unsubscribes (All Subscribers) are blunt instruments: they suppress all sends in the BU permanently until manually reversed. Publication list opt-outs are granular but do not provide universal protection.

The architectural decision is whether the org's compliance obligation requires a single opt-out to stop all communication (GDPR legitimate interest model) or allows channel-by-channel opt-out (newsletter vs. transactional). Design the unsubscribe landing page and automation to write to the correct level based on the compliance requirement — defaulting to global unsubscribe is the more compliant but more operationally restrictive choice.

### Auto-Suppression vs. Publication List for Regulatory Exclusions

For permanent regulatory exclusions (erasure requests, litigation holds, regulatory sanctions), Auto-Suppression Lists are the correct mechanism because they apply to future sends regardless of list structure changes. Publication list unsubscribes are the correct mechanism for subscriber preference management (opted out of category X but still wants category Y).

Mixing these mechanisms — using publication list unsubscribes for regulatory exclusions — creates the risk that a new list bypasses the suppression. Using Auto-Suppression for subscriber preferences is unnecessarily coarse and removes the ability to honor channel-specific preferences.

---

## Anti-Patterns

1. **Email-as-Subscriber-Key in a CRM-connected org** — Using email address as Subscriber Key when a Salesforce CRM is connected via Marketing Cloud Connect fragments subscriber identity across the two systems. When a contact's email changes in the CRM, their Marketing Cloud subscriber record does not update the key — it creates a new record. Unsubscribe and bounce history for the old address is orphaned. The correct pattern is to use the 18-char CRM Contact/Lead ID as Subscriber Key so both systems share the same identity anchor.

2. **Relying on Publication List Active Status to Override Global Unsubscribe** — Orgs sometimes attempt to re-subscribe a globally unsubscribed contact by adding them to an active publication list, expecting this to reinstate deliverability. It does not. The All Subscribers global unsubscribe is the final authority. The anti-pattern creates a dangerous false belief that the subscriber is receiving sends when they are not. The correct pattern is to check All Subscribers status as the first step in any subscriber deliverability investigation.

3. **No Held Subscriber Review Process** — Treating Held status as "effectively deleted" rather than "suppressed until investigated" allows legitimate subscribers to accumulate in Held status indefinitely. The org loses deliverable audience silently. The correct pattern is a scheduled quarterly review of `_Bounce` Data View data to categorize hard bounces by type and reactivate false positives with documented evidence.

---

## Official Sources Used

- Salesforce Help: Subscriber Key — https://help.salesforce.com/s/articleView?id=sf.mc_es_subscriber_key.htm&type=5
- Salesforce Help: Subscriber Key Scenarios — https://help.salesforce.com/s/articleView?id=sf.mc_es_subscriber_key_scenarios.htm&type=5
- Salesforce Help: Subscriber De-Duplication on Sends — https://help.salesforce.com/s/articleView?id=sf.mc_es_subscriber_deduplication.htm&type=5
- Salesforce Help: Auto-Suppression Lists — https://help.salesforce.com/s/articleView?id=sf.mc_es_auto_suppression_lists.htm&type=5
- Salesforce Help: Manage Subscribers On Lists — https://help.salesforce.com/s/articleView?id=sf.mc_es_manage_subscriber_on_list.htm&type=5
