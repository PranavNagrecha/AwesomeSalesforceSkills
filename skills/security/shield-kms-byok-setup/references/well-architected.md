# Well-Architected Notes — Shield Platform Encryption: BYOK / KMS Setup

## Relevant Pillars

- **Security** — Primary pillar, but narrower than it first appears. The key model
  determines who controls decryption *at the storage tier*: it protects against a
  database-level compromise, against media disposal, and — for BYOK and Cache-Only —
  against Salesforce itself. It does not change who can read a field. Shield is
  transparent above storage, so every user with field-level security Read sees the
  same plaintext under every model. The genuine security property BYOK and
  Cache-Only add is **crypto-shredding**: destroying the tenant secret renders data
  under it permanently unreadable, unilaterally.

- **Reliability** — The pillar that decides between BYOK and Cache-Only Keys. BYOK
  adds no runtime dependency. Cache-Only Keys make your key service a hard
  dependency of your org's ability to read encrypted data, on a refresh schedule
  Salesforce controls: "The cache is regularly flushed every 72 hours. Certain
  Salesforce operations flush the cache on average every 24 hours." The requirement
  that creates is availability at an arbitrary instant, not throughput — a very
  different engineering problem from the one teams usually plan for.

- **Operational Excellence** — Every mechanism here has a rehearsal obligation.
  Rotation is not complete on upload; destruction cannot be first executed in
  production; replay detection requires the key service to participate; and the
  production upload window is 24 hours, so a failed rotation cannot be retried the
  same day. None of these are discoverable from the Setup screens.

- **Performance** — Largely a non-issue and widely misunderstood. Cache-Only Keys
  do not call out per decryption; the key is cached. Steady-state latency is
  unaffected. The cost is availability, not speed.

## Architectural Trade-offs

**Salesforce-managed vs BYOK.** Salesforce-managed is operationally simplest and
satisfies most encryption-at-rest mandates. BYOK adds key provenance — you can
demonstrate the material originated outside Salesforce — and unilateral
crypto-shredding, at the cost of generating and wrapping material, holding your own
copy securely, and living with a 24-hour production upload window. It adds **no**
runtime availability risk, which is what makes it the right default for orgs whose
requirement is about key control rather than key non-persistence.

**BYOK vs Cache-Only Keys.** The dividing question is a single one: does a
contractual or regulatory clause require that key material never persist in the
vendor's systems, or that revocation be unilateral and immediate? If yes, Cache-Only
is the only model that provides it — Salesforce "doesn't retain or persist your
cache-only keys in any system of record or backups." If no, Cache-Only buys a
runtime dependency for a property nobody asked for. The failure mode is total and
org-wide: an unavailable key service at a cache flush means encrypted fields cannot
be decrypted, on record pages, in Apex, and in every integration simultaneously.

**Rotation cadence vs re-encryption cost.** Frequent rotation limits the data volume
under any one secret, which is the point of rotation. It also means frequent
re-encryption jobs, each a long background operation proportional to data volume,
each occupying a window. Quarterly is a common landing point; the honest way to
choose is to measure one re-encryption on the largest object and set the cadence
against that number rather than against a policy template.

**Where the destroy rehearsal lives.** Rehearsing in a sandbox costs a quarterly
window and produces the evidence your support desk will need — the actual UI error,
the Apex exception type, the integration response. Not rehearsing costs nothing
until the first real revocation, at which point nobody knows what users will see or
how long recovery takes. The sandbox upload window is four hours rather than 24,
which makes the sandbox the only practical place to iterate.

**Key model vs field-level security.** These are orthogonal and are constantly
conflated because both are called "protecting the data." Run them as separate
workstreams with separate deliverables: a key management decision record, and an FLS
matrix. A design document that cites BYOK in its access-control section has one
control where it believes it has two.

## Anti-Patterns

1. **Ranking the models as a security ladder.** Each answers a different compliance
   sentence and carries a different operational obligation. "Strongest available" is
   not a design rationale.

2. **Choosing Cache-Only Keys without citing the clause that requires them.** The
   org inherits an availability dependency it usually cannot operate to the required
   standard, for a property it did not need.

3. **Treating rotation as complete on upload.** Existing data stays under the
   previous secret until re-encryption runs *and completes*. Verify on Encryption
   Statistics, not on the key management screen.

4. **Rehearsing destruction in production**, or recommending a destroy test without
   naming the environment. Destruction is irreversible for data already written
   under that secret; there is no recovery path.

5. **Presenting the key model as an access control.** Under every model, FLS Read
   sees plaintext. The key model protects against a storage compromise and against
   Salesforce — not against a logged-in user.

6. **Confusing Manage Encryption Keys with read access.** It governs administering
   the feature, including irreversible tenant secret destruction. It is one of the
   most dangerous permissions in the org and should be scoped accordingly — and it
   has no bearing on who can see a value.

7. **Assuming encryption is retroactive.** Policies encrypt subsequent writes;
   historical data waits for an explicit re-encryption job. Make its completion a
   gating criterion for compliance sign-off.

8. **Enabling replay detection without the key service implementing it.** Every
   callout begins to fail. Build and test the `RequestIdentifier` / nonce path when
   the service is first written.

9. **Recommending Cache-Only Keys without designing the key service.** SLO,
   multi-region, independent monitoring, on-call ownership, and a *rehearsed*
   fallback are part of the decision, not follow-up work.

## Official Sources Used

- Salesforce Help — Bring Your Own Key (BYOK) Option — https://help.salesforce.com/s/articleView?id=xcloud.security_shield_pe_byok.htm&type=5
- Salesforce Help — How Shield Platform Encryption Works (customer-supplied tenant secret upload frequency: once every 24 hours in production and Developer Edition orgs, every 4 hours in sandboxes; rotation applies to subsequent data; AES-256 CBC with a random IV) — https://help.salesforce.com/s/articleView?id=xcloud.security_pe_concepts.htm&type=5
- Salesforce Help — Cache-Only Key Service (key material stored outside Salesforce, "Salesforce doesn't retain or persist your cache-only keys in any system of record or backups", 256-bit AES keys returned in a JSON response wrapped using JWE, replay detection and the `RequestIdentifier` marker) — https://help.salesforce.com/s/articleView?id=xcloud.security_pe_byok_cache.htm&type=5
- Salesforce Help — How Cache-Only Keys Works (cache flushed every 72 hours; certain Salesforce operations flush on average every 24 hours) — https://help.salesforce.com/s/articleView?id=platform.security_pe_byok_cache_how.htm&type=5
- Salesforce Help — Prerequisites and Terminology for Cache-Only Keys — https://help.salesforce.com/s/articleView?id=platform.security_pe_byok_cache_prereqisites.htm&type=5
- Salesforce Help — Troubleshoot Cache-Only Keys — https://help.salesforce.com/s/articleView?id=platform.security_pe_byok_cache_troubleshoot.htm&type=5
- Salesforce Security Guide — Reactivate a Cache-Only Key — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_pe_byok_cache_activate.htm
- Salesforce Help — Salesforce Encryption Principles — https://help.salesforce.com/s/articleView?id=xcloud.security_shield_pe_principles.htm&type=5
- Salesforce Help — Implementation and Ongoing Management (Shield Platform Encryption) — https://help.salesforce.com/s/articleView?id=xcloud.security_shield_pe_implementation_and_mgt.htm&type=5
- Platform Encryption REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_encryption_rest_api_guide.meta/platform_encryption_rest_api_guide/api_rest_encryption.htm
- Salesforce Security Guide — Salesforce Shield (Shield comprises Shield Platform Encryption, Event Monitoring, and Field Audit Trail) — https://help.salesforce.com/s/articleView?id=platform.security_overview.htm&type=5
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: the exact BYOK wrapping procedure in examples.md - downloading
     a Salesforce-provided RSA certificate, wrapping 32 bytes of key material
     with RSA-OAEP, and Base64-encoding for upload - is presented as the shape
     of the flow and was NOT verified step-by-step against the BYOK
     documentation in this pass. The openssl commands are illustrative. Follow
     Salesforce's current BYOK article for the authoritative padding mode,
     certificate retrieval path, and upload format before executing. -->
<!-- UNVERIFIED: the Setup navigation paths "Setup → Platform Encryption → Key
     Management" and "Setup → Platform Encryption → Encryption Statistics" were
     not re-verified in this pass. Both surfaces exist; confirm the current menu
     labels before putting them in a runbook. -->
<!-- UNVERIFIED: the claim that "Manage Encryption Keys" plus "Customize
     Application" are the permissions governing encryption administration is
     carried over from the in-repo security/platform-encryption package rather
     than re-verified here. The orthogonality claim (that neither governs read
     access, which is FLS) is well established in the Shield documentation. -->
<!-- UNVERIFIED: "quarterly" as a rotation or destroy-rehearsal cadence is a
     practitioner convention, not a Salesforce requirement. No Salesforce source
     mandates a rotation interval. Set the cadence against your own measured
     re-encryption duration and your own policy. -->
