# Well-Architected Notes — Salesforce Shield Architecture

## Relevant Pillars

- **Security** — Shield is the most direct security investment a
  Salesforce org can make: encryption-at-rest for the DB, real-time
  event visibility, multi-year audit retention. The architectural
  judgment is *which* component(s) the compliance posture actually
  demands. Buying all three "for safety" is a budget smell — each
  should be tied to a named driver (regulator, contract, internal
  control).
- **Reliability** — CCKM is the only Shield component design choice
  that can *reduce* availability for the protected fields. Document the
  trade explicitly: stronger key custody at the cost of HSM-availability
  coupling. BYOK and Salesforce-managed keys don't add this failure
  mode.
- **Operational Excellence** — Tenant-secret rotation, Field Audit
  Trail retention policy authoring, and Real-Time Event Monitoring
  subscriber operation are the three ongoing ops surfaces Shield adds.
  All three are documented operations; failure to operationalize them
  is what turns Shield from a feature into a maintenance burden.

## Architectural Tradeoffs

- **Probabilistic vs deterministic encryption.** Probabilistic is
  cryptographically stronger; deterministic is the only path that
  preserves filterability and sortability. The decision is per field,
  driven by what queries / reports the business needs against the
  field. Wrong choice produces either weaker security than necessary
  or queries that silently return zero rows.
- **CCKM vs BYOK vs Salesforce-managed keys.** Strongest custody
  posture (CCKM) couples encryption availability to HSM availability.
  Middle ground (BYOK) gives customer-controlled rotation without
  HSM operational burden. Salesforce-managed is fine when no
  regulator demands customer custody.
- **Field Audit Trail retention vs storage cost.** 10-year retention
  on every audited object on a high-volume org is a significant
  storage line item. Set retention per-object, sized to the actual
  compliance requirement — not "10 years on everything for safety".
- **Real-Time Event Monitoring subscriber vs Transaction Security
  Policy.** Custom subscribers (Pub/Sub API consumers) give arbitrary
  reaction logic; TSP gives in-flight blocking. Most use cases need
  both: TSP blocks the obvious cases, custom subscribers handle
  nuanced ones the TSP grammar can't express.

## Anti-Patterns

1. **Recommending Shield setup before confirming licenses.** The most
   common Shield-architecture mistake. Always pre-flight the Permission
   Set Licenses page.
2. **Probabilistic encryption on a field that needs to be filtered.**
   Queries silently return zero rows; deterministic is the only option.
3. **Encryption Policy that lists Formula / Roll-Up / unique-indexed
   External ID fields.** Setup rejects them; rework needed. Encrypt the
   source field.
4. **CCKM design with no HSM availability runbook.** The HSM is now
   the critical path for Salesforce write availability on encrypted
   fields. An availability target without a runbook isn't a design.
5. **Buying all three Shield components without a per-component
   compliance driver.** Shield is paid per component; each should be
   tied to a named driver, not "we got the bundle".

## Official Sources Used

- Salesforce Shield Overview — https://help.salesforce.com/s/articleView?id=salesforce_shield.htm&type=5
- Shield Platform Encryption concepts — https://help.salesforce.com/s/articleView?id=xcloud.security_pe_concepts.htm&type=5
- Shield Platform Encryption BYOK — https://help.salesforce.com/s/articleView?id=xcloud.security_pe_byok.htm&type=5
- Cache-Only Key Service — https://help.salesforce.com/s/articleView?id=xcloud.security_pe_cache_only_keys.htm&type=5
- Field Audit Trail — https://help.salesforce.com/s/articleView?id=xcloud.field_audit_trail.htm&type=5
- HistoryRetentionPolicy metadata — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/customobject_historyretentionpolicy.htm
- Real-Time Event Monitoring (Pub/Sub API) — https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Sibling skill — `skills/security/platform-encryption/SKILL.md` (when one exists)
