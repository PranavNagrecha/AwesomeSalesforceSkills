# Well-Architected Notes — Marketing Cloud Data Sync

## Relevant Pillars

- **Reliability** — The sync pipeline is the critical path between CRM truth and Marketing Cloud audience accuracy. Reliability failures (stale SDEs, silent field exclusions, deleted record propagation) directly affect campaign deliverability and personalization correctness. Practitioners must design for sync health monitoring and failure recovery, not just initial configuration.

- **Security** — The MC Connect connected user's FLS settings determine what data enters Marketing Cloud. Overly permissive connected user profiles risk syncing sensitive CRM fields (PII, financial data) that should not be present in the marketing platform. Shield-encrypted fields are correctly excluded by the sync engine — this is a security feature, not a limitation. Data minimization (syncing only necessary fields) reduces the CRM-to-MC data exposure surface.

- **Performance** — Sync frequency, object size, and field count all affect Salesforce API consumption. Full syncs on large objects during peak CRM activity windows can consume a significant share of the org's daily API limit, affecting other integrations and automations that depend on the same API allocation. Incremental sync is the correct operational mode; full sync is a recovery tool.

## Architectural Tradeoffs

**Automatic vs Scheduled Sync:** Automatic (triggered) sync provides near-real-time CRM data in Marketing Cloud, enabling time-sensitive journey triggers and transactional sends. However, it produces more API calls per unit time during high CRM activity periods. Scheduled sync (up to every 15 minutes) is more predictable in API cost but introduces staleness that may be unacceptable for operational sends (e.g., case resolution notifications). Choose based on the maximum acceptable data latency for the use case, not on convenience.

**Field breadth vs field discipline:** Syncing all available fields on a CRM object reduces the risk of a future "we need that field" gap but rapidly approaches the 250-field cap. Once the cap is hit, fields are silently excluded in an undocumented order. A disciplined, use-case-driven field selection (only fields needed for current or planned sends) is architecturally safer and easier to audit than a "sync everything" approach.

**SDE-centric vs DE-centric audience design:** Some teams build all their send audiences by querying directly from SDEs via Query Activity (with SDEs as source). Others maintain purpose-built DEs populated by nightly queries from SDEs. The SDE-centric approach uses fresher data but requires careful management of the read-only constraint at every step of the automation. The DE-centric approach introduces a processing step but gives the marketing ops team a writable, auditable intermediate layer that is easier to troubleshoot and enrich.

## Anti-Patterns

1. **Syncing all available fields without field selection planning** — Selecting every field on a CRM object to "future-proof" the sync virtually guarantees exceeding the 250-field cap and silently excluding the fields added last. The correct approach is a deliberate field selection review before each new sync configuration, scoped to active and planned campaign requirements.

2. **Using the MC Connect connected user as a shared org-wide integration account** — When the connected user's credentials are shared across multiple integrations (e.g., also used by a middleware platform or an Apex callout), API limit consumption becomes unpredictable and FLS changes made for one integration can break the MC sync. The connected user should be a dedicated profile with read access scoped to only the objects and fields needed for the sync.

3. **Triggering full syncs as the default sync failure recovery response** — Full syncs are resource-intensive and solve only a subset of sync problems (record count drift). They do not fix field type mismatches, FLS gaps, or deleted field mappings. Using full sync as a first response wastes API budget and delays diagnosis of the actual root cause.

## Official Sources Used

- Salesforce Help — Synchronized Data Sources overview: https://help.salesforce.com/s/articleView?id=sf.mc_co_sync_data_sources.htm&type=5
- Salesforce Help — Sync Best Practices: https://help.salesforce.com/s/articleView?id=sf.mc_co_sync_best_practices.htm&type=5
- Salesforce Help — Create Synced Data Sources in Contact Builder: https://help.salesforce.com/s/articleView?id=sf.mc_co_create_synced_data_sources.htm&type=5
- Salesforce Help — 250 Field Limit for Synchronized Data Sources: https://help.salesforce.com/s/articleView?id=sf.mc_co_250_field_limit.htm&type=5
- Salesforce Well-Architected Framework: https://architect.salesforce.com/well-architected/overview
