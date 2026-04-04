# Well-Architected Notes — Platform Encryption

## Relevant Pillars

- **Security** — Primary pillar. Shield Platform Encryption is fundamentally a data-at-rest security control. Choosing the right encryption scheme, granting the View Encrypted Data permission precisely, managing tenant secrets carefully, and designing key rotation are all Security pillar concerns. A poorly designed encryption rollout can create false compliance confidence (probabilistic on filtered fields silently breaks queries) or false security confidence (re-encryption never run, so historical data remains plaintext).

- **Reliability** — Relevant for Cache-Only Keys specifically. The decision to use Cache-Only Keys introduces a runtime dependency on an external service. An org that uses Cache-Only Keys is only as available as its external key service. Architects must evaluate this tradeoff against the org's availability requirements before committing to Cache-Only Keys.

- **Operational Excellence** — Key rotation schedules, re-encryption runbooks, permission audits, and the Platform Encryption Analyzer output are all operational artifacts that need to be owned, documented, and periodically reviewed. Without an operational model, encryption configurations drift: keys go unrotated, new integration users get missed for the View Encrypted Data permission, and new fields get added to SOQL filters without checking whether they are encrypted.

- **Performance** — Encrypted search operations are slower than unencrypted equivalents. Encrypted full-index search using AES-256 with per-segment index encryption adds latency, particularly on large data volumes. Probabilistic encryption eliminates index search entirely; deterministic encryption adds index encryption overhead. Orgs with large encrypted datasets should baseline query performance before and after encryption rollout.

## Architectural Tradeoffs

**Deterministic vs Probabilistic:** This is the most consequential field-level decision. Deterministic encryption sacrifices the strongest confidentiality property (unique ciphertext per value) in exchange for query capability. The tradeoff is explicitly about security vs functionality. Default to probabilistic unless a concrete, documented need for equality filtering exists. Do not apply deterministic encryption preemptively "in case we need to search it later."

**BYOK vs Cache-Only Keys vs Salesforce-Managed:** Salesforce-managed keys are operationally simplest and adequate for most compliance requirements. BYOK adds meaningful key control (you can destroy your own tenant secret material) without adding runtime availability risk. Cache-Only Keys are the right choice only when a compliance mandate explicitly requires that the key material never reside in Salesforce storage and the org can tolerate the availability dependency. Map the key model choice explicitly to the compliance requirement — do not over-engineer toward Cache-Only Keys when BYOK satisfies the mandate.

**Re-Encryption Timing:** Re-encrypting large datasets (tens of millions of records) is a background job that takes wall-clock time. This creates a window during which old data is unencrypted. Architects must decide whether this window is acceptable or whether the rollout should be staged by object, with each object's re-encryption completing before proceeding to the next.

**Encrypted Fields in Integrations:** Fields encrypted with probabilistic encryption cannot be used as matching keys in integration middleware. If an integration uses `Email` or `Phone` as a record-matching key, those fields must use deterministic encryption or the integration must be redesigned to use Salesforce record IDs as the canonical match key.

## Anti-Patterns

1. **Applying probabilistic encryption to searchable fields without auditing query usage first** — This silently breaks SOQL filters, list views, reports, and automations. The impact is not surfaced as an error; it appears as zero results or empty reports. Run the Platform Encryption Analyzer and audit all SOQL queries before enabling any encryption policy in production.

2. **Declaring encryption rollout complete without running re-encryption** — Enabling the policy is not the same as encrypting existing data. A team that enables Shield, passes a compliance audit, and never runs the re-encryption job has provided false compliance assurance. Make re-encryption job completion a gating criterion for any compliance sign-off.

3. **Using Cache-Only Keys without an external key service SLA** — Selecting Cache-Only Keys for the strongest possible key separation and then deploying the key service without defined availability monitoring and runbooks creates a situation where a key service outage can render all encrypted records unreadable in production with no recovery path short of restoring Salesforce-managed key control. This is an availability anti-pattern that outweighs the security benefit for most orgs.

4. **Assigning View Encrypted Data to all profiles by default** — The View Encrypted Data permission exists to enforce need-to-know access to plaintext values. Assigning it broadly to avoid support tickets negates the access control benefit of encryption. Maintain a documented list of profiles and personas that genuinely need plaintext access and restrict the permission to only those profiles.

## Official Sources Used

- Shield Platform Encryption Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5
- How Shield Platform Encryption Works — https://help.salesforce.com/s/articleView?id=sf.security_pe_concepts.htm&language=en_US&type=5
- Filter Encrypted Data with Deterministic Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_deterministic.htm&language=en_US&type=5
- Considerations for Using Deterministic Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_deterministic_considerations.htm&language=en_US&type=5
- Which Standard Fields Can I Encrypt? — https://help.salesforce.com/s/articleView?id=sf.security_pe_standard_fields.htm&language=en_US&type=5
- Which Custom Fields Can I Encrypt? — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_pe_custom_fields.htm
- Bring Your Own Key (BYOK) — https://help.salesforce.com/s/articleView?id=sf.security_pe_byok_setup.htm&language=en_US&type=5
- Cache-Only Key Service — https://help.salesforce.com/s/articleView?id=sf.security_pe_byok_cache.htm&language=en_US&type=5
- Key Management and Rotation — https://help.salesforce.com/s/articleView?id=sf.security_pe_setup.htm&language=en_US&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
