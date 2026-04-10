# Well-Architected Notes — Marketing Consent Architecture

## Relevant Pillars

- **Security** — Consent is a privacy and data protection concern. The Well-Architected Security pillar requires that personal data is handled according to the data subject's stated preferences and applicable law. Using the platform consent data model (Individual, ContactPointTypeConsent, ContactPointConsent) provides an auditable, structured record that satisfies data subject access requests and demonstrates compliance with GDPR Article 7 (conditions for consent) and CCPA opt-out requirements. Storing consent only in Marketing Cloud or in unstructured custom fields creates a security and compliance risk because the records are not queryable through CRM reporting, not linkable to the Contact's audit trail, and not surfaced by standard Salesforce privacy tooling.

- **Reliability** — A consent architecture that has MC and CRM as independent sources of truth is unreliable. If either system's data diverges — through failed sync, manual overrides, or misconfiguration — the org either sends to opted-out subscribers (compliance failure) or suppresses opted-in subscribers (revenue failure). The CRM-as-system-of-record pattern with MC reading at send time eliminates the dual-write race condition and makes the send decision deterministic: the CRM record at the time of send is the single arbiter.

- **Operational Excellence** — The platform consent objects support structured audit history through standard Salesforce field history tracking and the CaptureDate/CaptureSource fields. This makes operational review of consent data feasible without custom reporting infrastructure. The alternative — piecing together consent history from MC send logs, custom fields, and manual notes — is operationally expensive and error-prone during regulatory audits.

## Architectural Tradeoffs

**CRM system of record vs. MC system of record:**
The CRM-as-system-of-record pattern is more reliable and auditable but requires enabling and validating the MC Consent Management integration. It also introduces a send-time dependency: if CRM is unavailable, MC must have a defined fallback (suppress all, or use cached consent). The MC-as-system-of-record pattern avoids this dependency but cannot support per-purpose tracking, multi-channel consistency, or GDPR Article 17 erasure requests that span beyond email.

**ContactPointTypeConsent vs. ContactPointConsent granularity:**
Channel-level consent (ContactPointTypeConsent) is simpler to implement and sufficient for most orgs. Address-level consent (ContactPointConsent) is required only when a person has multiple contact points (multiple email addresses) and wishes to manage preferences independently per address. Defaulting to ContactPointConsent adds implementation complexity without benefit for orgs where each person has one email address per channel.

**Single purpose vs. multi-purpose consent records:**
A single "Email" consent record per Individual is simpler but conflates marketing and transactional consent. Multi-purpose records require more Data Use Purpose setup and more Flows/triggers to maintain, but enable the GDPR-correct behavior of continuing transactional sends after marketing consent is withdrawn. For GDPR-regulated orgs, multi-purpose is the only architecturally sound choice.

## Anti-Patterns

1. **Consent stored only in MC All Subscribers** — MC's subscriber data does not carry DataUsePurpose, CaptureDate, or CaptureSource in a CRM-queryable form. It cannot support GDPR Article 15 access requests, cannot scope suppression by lawful basis, and cannot be used by non-MC send channels. Any architecture that treats MC as the consent authority for a GDPR or CCPA regulated org is non-compliant by design.

2. **Consent managed through custom Contact boolean fields** — Custom fields like `Opted_Out_Marketing__c` appear simple but create a parallel consent model that diverges from the platform standard. They do not integrate with the MC Consent Management integration, do not support DataUsePurpose, and must be maintained separately from the Individual and ContactPointTypeConsent objects that compliance tools and data subject request workflows reference.

3. **Enabling MC Consent Management without testing the suppression path** — Orgs frequently enable the integration and assume it works. Without an explicit suppression test (send a message to a subscriber with an OptOut record and confirm they are excluded), there is no confirmation that the purpose mapping is correct, the consent record structure is right, or the integration is live. Failures in suppression are silent — the send proceeds and no error is raised if the consent lookup returns no matching record.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help — Salesforce Consent Data Model — https://help.salesforce.com/s/articleView?id=sf.consent_mgmt_data_model.htm
- Salesforce Help — Consent Management for Marketing Cloud Engagement — https://help.salesforce.com/s/articleView?id=sf.consent_mgmt_marketing_cloud.htm
- Salesforce Help — Respect Consent Preferences in Marketing Cloud — https://help.salesforce.com/s/articleView?id=sf.consent_mgmt_respect_preferences.htm
- Salesforce Help — Consent Management for Salesforce Platform — https://help.salesforce.com/s/articleView?id=sf.consent_mgmt_platform.htm
