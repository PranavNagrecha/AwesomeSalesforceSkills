# Well-Architected Notes — Consent Management Marketing

## Relevant Pillars

- **Security** — Consent management is a security and privacy domain. Incorrect opt-out handling exposes the org to CAN-SPAM penalties (up to $51,744 per email under 2024 FTC guidelines) and GDPR fines (up to 4% of global annual turnover). The All Subscribers global opt-out flag must be treated as a hard security boundary: no code, import, or automation should bypass it. GDPR lawful basis documentation and Privacy Center erasure workflows are direct security controls.
- **Reliability** — The opt-out system must work correctly on every send, including Triggered Sends, Journey Builder emails, and API-initiated sends. Send Classification propagation gaps (e.g., Journey activities without assigned classifications) create silent reliability failures. Reliability also applies to the MC-to-CRM sync: if the sync lags or fails, subscribers opt out in MC but remain reachable in CRM, which is a systemic reliability failure.
- **Operational Excellence** — Consent management requires ongoing operational discipline: monitoring publication list growth, auditing Send Classifications on new sends, processing Privacy Center requests within regulatory SLAs (GDPR requires responses within 30 days), and maintaining the consent-tracking Data Extension. Well-run orgs build automated monitoring for erased subscribers re-appearing in CRM syncs and for sends missing a valid Send Classification.

## Architectural Tradeoffs

**Subscription Center vs. Custom Preference Center:** The MC Subscription Center requires zero development effort and is maintained by Salesforce. The tradeoff is limited branding and no support for advanced flows (double opt-in, category descriptions, re-subscription). Custom CloudPages Preference Centers offer full brand control and flow flexibility but introduce a development and maintenance burden. The one-click unsubscribe requirement (Google/Yahoo 2024) adds a correctness constraint to custom builds: the opt-out must be processed immediately on the URL visit, not after a confirmation step.

**Global opt-out vs. granular publication list opt-out:** A global opt-out is the most conservative and compliant choice: when in doubt, stop sending. Publication lists provide a better subscriber experience by allowing targeted opt-outs, but they require more design effort (list taxonomy) and more sophisticated monitoring (subscribers who are opted out of all lists but not globally opted out may still receive sends targeting them directly via All Subscribers). The right architecture separates content categories clearly and uses publication lists only where a subscriber would meaningfully distinguish between them.

**In-MC consent tracking vs. CRM consent tracking:** For GDPR, consent records stored only in a Marketing Cloud Data Extension are at risk: if the subscriber exercises the right to erasure, the consent record is deleted along with the personal data, removing the proof of consent. A better architecture stores a consent record hash or consent event ID in both MC and the CRM so that the existence of consent can be confirmed even after the personal data is erased.

## Anti-Patterns

1. **Using Publication List Opt-In to Override a Global Opt-Out** — Re-importing an opted-out subscriber as "Active" on a publication list to bypass their global unsubscribe is a compliance violation. The All Subscribers global opt-out is enforced by MC and cannot be circumvented through list status. Any attempt to do so produces sends that MC suppresses silently, wasting send volume, and creates an auditable trail of intentional opt-out bypass.

2. **Treating MC Opt-Out as Automatically Synced to Salesforce CRM** — Assuming that an opt-out in MC has updated the CRM contact record without verifying MC Connect configuration leads to continued sending from CRM-based channels (Sales Cloud email, Pardot, Sales Engagement) to opted-out subscribers. This pattern is especially dangerous when the opt-out was prompted by a GDPR or CAN-SPAM complaint, because the subscriber's expectation is that all sending has stopped.

3. **Storing Consent Evidence in Personal Data Fields That Are Erased** — Storing the entire consent record (timestamp, source, confirmation status) only in a Data Extension field tied to the subscriber's email address means the evidence is wiped when a right-to-erasure request is processed. Architecting for GDPR requires separating the consent event record (which must be retained to defend against future claims) from the personal data subject to erasure. Use a hashed identifier or separate consent event table that can survive subscriber erasure.

## Official Sources Used

- Salesforce Help — Consent Management for Marketing Cloud Engagement: https://help.salesforce.com/s/articleView?id=sf.mc_co_consent_management.htm
- Salesforce Help — CAN-SPAM Requirements: https://help.salesforce.com/s/articleView?id=sf.mc_es_canspam_requirements.htm
- Salesforce Help — How a Subscriber Opts Out: https://help.salesforce.com/s/articleView?id=sf.mc_es_how_subscriber_opts_out.htm
- Salesforce Help — Marketing Cloud Data Protection and Privacy Tools: https://help.salesforce.com/s/articleView?id=sf.mc_co_data_protection_and_privacy_tools.htm
- Salesforce Help — Privacy Center Implementation Guide: https://help.salesforce.com/s/articleView?id=sf.privacy_center_implementation_guide.htm
- Salesforce Help — Publication Lists: https://help.salesforce.com/s/articleView?id=sf.mc_es_publication_lists.htm
- Salesforce Help — Subscription Center: https://help.salesforce.com/s/articleView?id=sf.mc_es_subscription_center.htm
- Salesforce Help — Delivery Profiles: https://help.salesforce.com/s/articleView?id=sf.mc_es_delivery_profiles.htm
- Salesforce Help — Send Classifications: https://help.salesforce.com/s/articleView?id=sf.mc_es_send_classifications.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
