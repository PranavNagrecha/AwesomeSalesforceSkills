# Well-Architected Notes — Data Cloud Identity Resolution

## Relevant Pillars

- **Trusted** — Identity resolution directly affects data integrity. Incorrect match rules produce false-positive merges (two different people treated as one) or false-negative misses (the same person treated as two separate profiles). Either outcome degrades trust in Data Cloud as a system of record for customer identity. Reconciliation rule configuration affects which source's data values are surfaced in the Unified Individual, making source trust ranking a key governance decision.

- **Well-Performing** — Match rule type selection has direct performance implications. Fuzzy and full address Normalized rules are batch-only; using them in a ruleset expected to run in near-real-time causes incomplete resolution. Large orgs with millions of Individual records must size their expected re-run duration before making reconciliation rule changes that trigger full re-runs. The 4-manual-run-per-day limit also constrains how quickly iterative configuration can be validated.

- **Adaptable** — The 2-ruleset org limit and the immutable 4-character ruleset ID mean that identity resolution configuration is among the least reversible design decisions in a Data Cloud org. The Well-Architected adaptability principle — design for change — requires treating ruleset design as a long-lived architectural commitment, not a configuration detail. Documenting the ruleset ID and slot consumption in an architecture decision record supports future change management.

- **Efficient** — Running a full ruleset re-run due to an unplanned reconciliation rule change consumes significant compute time and delays downstream activation. Planning reconciliation rules correctly during initial design avoids unnecessary full re-runs and is more efficient than iterating post-run.

## Architectural Tradeoffs

### Real-Time Resolution Fidelity vs. Match Depth

Using only Exact and Exact Normalized match rules supports real-time resolution but misses merges that require Fuzzy name matching or full address normalization. Adding Fuzzy rules improves batch merge recall at the cost of real-time fidelity — real-time clusters will be a subset of batch clusters. The correct tradeoff depends on the downstream use case: real-time personalization use cases favor Exact-only rulesets; batch analytics and segmentation use cases can accept the batch-only Fuzzy rules.

### Single Ruleset Shared Across BUs vs. Segment Into Multiple Orgs

When an org serves multiple business units, the 2-ruleset limit forces a choice between sharing a single ruleset configuration (less flexibility, potentially wrong for one BU's identity attributes) or splitting into separate Data Cloud orgs (more operational complexity, higher cost). A shared ruleset with OR-combined match rules works well when BUs have non-overlapping customer bases. Separate orgs are warranted when BUs have different primary identity attributes and different reconciliation source trust hierarchies.

### Source Priority vs. Most Recent Reconciliation

Source Priority produces deterministic, predictable reconciliation output and is easier to audit. Most Recent produces output that can change with every run as source timestamps update, making it harder to debug unexpected changes in Unified Individual field values. Prefer Source Priority for legally or contractually sensitive attributes (name, date of birth) and Most Recent only for attributes where currency matters more than source trust (email address, phone number).

## Anti-Patterns

1. **Creating Rulesets Iteratively Without a Design Document** — Treating identity resolution configuration as something to figure out through trial-and-error consumes the limited 2-ruleset slots, produces test rulesets with poorly-chosen IDs that cannot be renamed, and risks triggering multiple full re-runs during testing. The correct approach is to design the ruleset configuration fully on paper before creating any ruleset in the org.

2. **Assuming Reconciliation Rule Changes Are Low-Risk Quick Fixes** — Modifying a reconciliation rule after the ruleset has run is treated by the platform as a structural change requiring a full re-run. Teams that change reconciliation rules during business hours to "quickly fix" an incorrect attribute value trigger hours-long re-runs that cause stale data in live segments and activations. Plan all reconciliation rule changes as scheduled maintenance.

3. **Using Data Cloud Identity Resolution for CRM Duplicate Management** — Data Cloud identity resolution operates on DMO-level records and produces Unified Individual profiles. It does not deduplicate Contact or Account records in the CRM org, does not merge CRM records, and does not enforce uniqueness on CRM sObjects. Using this skill to address CRM duplicate management requirements will not produce the expected outcome. CRM deduplication requires Duplicate Rules and Matching Rules on standard/custom objects, or a third-party data quality tool.

## Official Sources Used

- Identity Resolution Rulesets — https://help.salesforce.com/s/articleView?id=sf.c360_a_identity_resolution_ruleset.htm
- Identity Resolution Match Rules — https://help.salesforce.com/s/articleView?id=sf.c360_a_match_rules.htm
- Building a Complete View with Data Cloud and Identity Resolution — https://developer.salesforce.com/blogs/2024/10/data-cloud-and-identity-resolution
- Data Cloud Limits — https://help.salesforce.com/s/articleView?id=sf.c360_a_data_cloud_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Related Skills

- `architect/data-cloud-architecture` — end-to-end Data Cloud architecture patterns including multi-ruleset design
- `data/data-cloud-data-streams` — DMO mapping prerequisites for identity resolution
- `data/data-cloud-ingestion-api` — ingestion of identity attributes from external systems
