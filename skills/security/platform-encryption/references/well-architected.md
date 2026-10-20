# Well-Architected Notes — Platform Encryption

## Relevant Pillars

- **Security** — Primary pillar. Shield Platform Encryption is fundamentally a data-at-rest security control. Choosing the right encryption scheme, scoping field-level security precisely (encryption at rest is not the access decision — gotchas.md Gotcha 6), managing tenant secrets carefully, and designing key rotation are all Security pillar concerns. A poorly designed encryption rollout can create false compliance confidence (probabilistic on filtered fields breaks queries) or false security confidence (history duplicates and `FieldHistoryArchive` copies left plaintext — secguide 262 L4899-4904).

- **Reliability** — Relevant for Cache-Only Keys specifically. The decision to use Cache-Only Keys introduces a runtime dependency on an external service. An org that uses Cache-Only Keys is only as available as its external key service. Architects must evaluate this tradeoff against the org's availability requirements before committing to Cache-Only Keys.

- **Operational Excellence** — Key rotation schedules, background-encryption checks, and permission audits are all operational artifacts that need to be owned, documented, and periodically reviewed. Without an operational model, encryption configurations drift: keys go unrotated, new profiles quietly acquire Read on encrypted fields, and new fields get added to SOQL filters without checking whether they are encrypted.

- **Performance** — Search index files have their own tenant-secret type (`SearchIndex`, obj 264 L283816) that rotates at most once every seven days (L283644-283645). UNVERIFIED (2026-10-20): the latency cost of encrypted search and of each scheme is Help-only — baseline query performance before and after rollout.

## Architectural Tradeoffs

**Deterministic vs Probabilistic:** This is the most consequential field-level decision. Deterministic encryption sacrifices the strongest confidentiality property (unique ciphertext per value) in exchange for query capability. The tradeoff is explicitly about security vs functionality. Default to probabilistic unless a concrete, documented need for equality filtering exists. Do not apply deterministic encryption preemptively "in case we need to search it later."

**BYOK vs Cache-Only Keys vs Salesforce-Managed:** Salesforce-managed keys are operationally simplest and adequate for most compliance requirements. BYOK adds meaningful key control (you can destroy your own tenant secret, and re-import an exported copy to restore access — obj 264 L283928-283929) without adding runtime availability risk. Cache-Only Keys are the right choice only when a compliance mandate explicitly requires that the key material never reside in Salesforce storage and the org can tolerate the availability dependency. Map the key model choice explicitly to the compliance requirement — do not over-engineer toward Cache-Only Keys when BYOK satisfies the mandate.

**Background Encryption Timing:** Bringing existing data under the active key is a background process (api_meta 264 L127877-127882) that takes wall-clock time, so there is a window during which old data is not yet covered. Architects must decide whether this window is acceptable or whether the rollout should be staged by object, with each object's re-encryption completing before proceeding to the next.

**Encrypted Fields in Integrations:** Fields encrypted with probabilistic encryption cannot be used as matching keys in integration middleware. If an integration uses `Email` or `Phone` as a record-matching key, those fields must use deterministic encryption or the integration must be redesigned to use Salesforce record IDs as the canonical match key.

## Anti-Patterns

1. **Applying probabilistic encryption to searchable fields without auditing query usage first** — This silently breaks SOQL filters, list views, reports, and automations. UNVERIFIED (2026-10-20): whether the impact surfaces as an error or as empty results is not in the corpus. Audit all SOQL queries, reports and automations before enabling any encryption policy in production.

2. **Declaring encryption rollout complete without checking history and archives** — background encryption covers existing values, but history duplicates need `enableEncryptFieldHistory` and `FieldHistoryArchive` copies stay plaintext until Salesforce re-archives them (secguide 262 L4899-4904). Make that check a gating criterion for compliance sign-off.

3. **Using Cache-Only Keys without an external key service SLA** — Selecting Cache-Only Keys for the strongest possible key separation and then deploying the key service without defined availability monitoring and runbooks puts an unmonitored dependency on every read of encrypted data (material is applied on demand, api_meta 264 L118684-118687). UNVERIFIED (2026-10-20): the exact outage behaviour and recovery path are Help-only.

4. **Treating encryption as an access control** — Shield Platform Encryption is a data-at-rest control. "View Encrypted Data" and masking are documented for Classic Encryption (secguide 262 L2486, L2548); for Shield the corpus only mentions "encrypted data permissions" (L305-306), so test who sees plaintext in a sandbox. If need-to-know is the requirement, the deliverable is a field-level-security matrix.

## Official Sources Used

- Salesforce Security Guide (262) — Shield Platform Encryption overview, "set encrypted data permissions" (secguide 262 L303-306); criteria-based sharing rules can't use encrypted fields (L3478-3479); existing data, history and `FieldHistoryArchive` behaviour (L4899-4904); Classic Encryption and View Encrypted Data (L2483-2548).
- Object Reference (264) — `TenantSecret`: KDF seed description and rotation limits (obj 264 L283642-283645), `KeyDerivationMode` (L283671-283683), `Source` HSM/Uploaded/Remote (L283743-283769), `Status` Active/Archived/Destroyed (L283771-283786), export/import before destroy (L283928-283929), cache-only reactivation (L283943-283944); Cache-Only Key Service add-on (L134305-134306).
- Metadata API Developer Guide (264) — `CustomField.encryptionScheme` values (api_meta 264 L45623-45630); deterministic filters with equals/not equals (L33328-33329); `PlatformEncryptionSettings` incl. `enableDeterministicEncryption` and `enableEncryptFieldHistory` (L127844-127896); `EncryptionKeySettings.enableCacheOnlyKeys` / `enableReplayDetection` (L118655-118692); enhanced lookups description (L44305-44311).
- Platform Events Developer Guide (264) — Key Management and Encryption Policy pages (platform_events 264 L5732-5733); `RemoteKeyCalloutEvent` (L15274).
- Further reading, not corpus (Help-only, used only for claims marked UNVERIFIED): Shield Platform Encryption Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5 ; Which Custom Fields Can I Encrypt? — https://help.salesforce.com/s/articleView?id=xcloud.security_pe_custom_fields.htm&type=5 ; KB 000382508 (View Encrypted Data and Shield) — https://help.salesforce.com/s/articleView?id=000382508&type=1
