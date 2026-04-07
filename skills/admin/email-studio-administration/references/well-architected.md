# Well-Architected Notes — Email Studio Administration

## Relevant Pillars

- **Security** — Email sends carry CAN-SPAM, CASL, and GDPR compliance obligations. Send Classifications must be correctly assigned (Commercial vs Transactional) to ensure legal unsubscribe handling is enforced. Suppression lists (Global, Publication, Auto) are the primary mechanism for honoring subscriber opt-out rights. Misclassifying commercial sends as Transactional is both a security/compliance risk and a platform misuse that violates Marketing Cloud terms of service. IP pool selection (via Delivery Profile) determines whether transactional IPs are protected from marketing-send reputation damage.

- **Reliability** — Triggered Send Definitions require explicit activation to fire. A definition left in "Building" status silently drops messages without error — a reliability risk for transactional email delivery. A/B test auto-winner logic requires adequate audience size and evaluation window design to fire reliably. Suppression list changes are not retroactive to in-flight jobs, requiring process controls around emergency suppression.

- **Operational Excellence** — Dynamic content blocks reduce email version proliferation, lowering maintenance burden and operational risk from copy changes affecting N email versions. A/B testing with structured winner criteria eliminates guesswork and builds organizational learning. Pre-send validation pipelines (Content Detective → test send → Inbox Preview → approval) standardize quality gates. Send Classification governance prevents compliance drift as team membership changes.

- **Performance** — Dynamic content rule evaluation is performed at send time for every subscriber. Extremely complex rule trees (20+ conditions, nested logic) increase rendering time in the preview pane and may affect send throughput for large batches. Simplify rule logic where possible and test preview performance at scale.

- **Scalability** — Single email definitions with dynamic content blocks scale to any audience size without multiplying send jobs. Triggered Send Definitions scale horizontally to high API call volumes but require IP pool capacity planning for large transactional volumes. A/B test configurations should be validated for minimum viable test group sizes before being applied to smaller audiences.

## Architectural Tradeoffs

**Dynamic content vs separate email versions:** Dynamic content blocks trade build-time simplicity (one email, one approval, one reporting view) for rule-maintenance complexity (ordered conditions, default coverage, attribute dependency). For fewer than three segment variations, separate emails may be simpler. For four or more, dynamic content is the correct choice.

**Triggered Send vs Journey Builder send:** Triggered Send Definitions fire immediately on API call, are independently configurable, and are simpler to operate. Journey Builder sends support multi-step orchestration, wait activities, and decision branching but require Journey architecture design. For a single transactional event with no downstream steps, use a Triggered Send. For any multi-touch sequence or post-event nurture, use Journey Builder.

**A/B testing scope:** A/B tests in Email Studio are limited to one-time batch sends. Ongoing content optimization in an active Journey requires Pathway Optimizer (a Journey Builder feature), not Email Studio A/B testing.

## Anti-Patterns

1. **Transactional Classification as an Unsubscribe Bypass** — Assigning a Transactional Send Classification to commercial promotional emails to remove the unsubscribe footer. This violates CAN-SPAM and CASL legally, and corrupts the Business Unit's opt-out data because commercial unsubscribes are no longer being recorded correctly. Use Publication List unsubscribes for granular opt-out management within commercial sends.

2. **One Email Per Segment Instead of Dynamic Content** — Maintaining separate email versions for each subscriber segment instead of using dynamic content blocks. This creates N-times the maintenance burden, N-times the approval overhead, and fragmented reporting. Dynamic content blocks are the correct architectural response to segmented personalization requirements.

3. **Skipping Pre-Send Validation for "Small" Sends** — Treating small audience sends (under 10,000 subscribers) as too small to require Content Detective, seed send, or Inbox Preview. Domain reputation and deliverability issues compound over time; a spam complaint from a small send can affect IP reputation for all future sends. Validation pipeline should be mandatory regardless of audience size.

4. **IP Pool Commingling: Transactional and Commercial on Same IP** — Assigning both commercial marketing sends and transactional sends to the same dedicated IP pool. High unsubscribe or complaint rates from a marketing campaign can damage IP reputation and cause transactional emails (order confirmations, password resets) to be filtered to spam. Separate IP pools for transactional and commercial sends via distinct Delivery Profiles.

## Official Sources Used

- Salesforce Help — Email Studio Overview: https://help.salesforce.com/s/articleView?id=mc_es_email_studio.htm
- Salesforce Help — Send Classifications: https://help.salesforce.com/s/articleView?id=mc_es_send_classifications.htm
- Salesforce Help — Dynamic Content in Content Builder: https://help.salesforce.com/s/articleView?id=mc_cb_dynamic_content.htm
- Salesforce Help — A/B Testing in Email Studio: https://help.salesforce.com/s/articleView?id=mc_es_ab_testing.htm
- Salesforce Help — Build Email from Template in Content Builder: https://help.salesforce.com/s/articleView?id=mc_cb_build_email_from_template.htm
- Salesforce Help — Suppression Lists: https://help.salesforce.com/s/articleView?id=mc_es_suppression_lists.htm
- Salesforce Help — Triggered Sends: https://help.salesforce.com/s/articleView?id=mc_es_triggered_sends.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
