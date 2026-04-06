# Well-Architected Notes — Lead Data Import and Dedup

## Relevant Pillars

- **Reliability** — Duplicate leads degrade pipeline reliability. If the same prospect appears as two leads, one may be worked while the other sits uncontacted, leading to missed follow-up or conflicting outreach. Dedup controls are a reliability mechanism for the sales process, not just a data hygiene preference.
- **Operational Excellence** — Import workflows without normalization and dedup controls accumulate technical debt rapidly. Each dirty import creates remediation work downstream (manual merge sessions, data steward reviews, support tickets from reps confused by duplicate assignment notifications). Well-designed import pipelines include dedup as a first-class step, not an afterthought.
- **Security** — Web-to-Lead forms are a public POST endpoint. Poorly configured forms without CAPTCHA or rate limiting become spam targets. Each spam submission is processed by duplicate rule evaluation, trigger logic, and Flow, consuming compute resources. Security controls at the form layer (reCAPTCHA, submission rate limits) reduce load on dedup infrastructure and prevent the `DuplicateRecordSet` table from being flooded with junk data.
- **Performance** — Fuzzy matching rule evaluation runs at lead insert time. On orgs with large Lead volumes (>1M records), non-selective matching rules (e.g., fuzzy match on Company alone) perform near-full-table scans and add save latency. Matching rules should anchor on selective indexed fields (Email first, then Name) to keep evaluation fast.
- **Scalability** — Native dedup mechanisms (Duplicate Rules, Data Import Wizard) have documented limits (5 active rules per object, single-field exact match in the wizard, no cross-object fuzzy match at volume). Designs that rely entirely on native tools will fail to scale beyond a few hundred thousand records or cross-object matching requirements. Scalable designs layer third-party tools or external matching pipelines for high-volume cases.

## Architectural Tradeoffs

**Native rules vs. Apex vs. Third-party tools:**
- Native Duplicate Rules are zero-code, fast to configure, and work reliably for UI-based data entry. They are insufficient for high-volume imports, Web-to-Lead, or complex cross-object matching.
- Apex triggers give programmatic control over all insert pathways but add maintenance overhead and require careful governor limit management. Best for medium-complexity use cases where a simple "flag and route" behavior is sufficient.
- Third-party tools (DemandTools, Cloudingo) handle volume, fuzzy matching, and survivorship logic that native tools cannot. They introduce vendor dependency and cost, but are the correct choice for enterprise-scale lead dedup.

**Alert vs. Block duplicate rule action:**
- "Block" provides a better user experience for UI data entry (the user sees the duplicate before saving) but is unreliable for non-UI channels. Relying on Block for all channels creates a false sense of security.
- "Alert" captures all duplicate signals via Duplicate Record Sets without preventing any inserts. It requires a downstream process (human review queue or automated routing) to act on the signals. Alert-mode with a well-designed queue is more operationally robust than Block-mode with no fallback.

**Pre-import cleansing vs. post-import dedup:**
- Pre-import cleansing (normalization script, within-file dedup) prevents duplicate records from being created in the first place. It is always cheaper than post-import cleanup.
- Post-import dedup (reviewing Duplicate Record Sets, running merge jobs) is necessary when pre-import controls were skipped or when the import source had data quality issues. It should be treated as remediation, not the primary strategy.

## Anti-Patterns

1. **Using "Block" mode as the sole duplicate prevention mechanism for all channels** — Block mode does not stop Web-to-Lead, API, or Apex inserts. Orgs that configure "Block" and consider the problem solved will accumulate duplicates from every non-UI channel while believing their controls are working. Always complement Block with Alert-mode detection and an after-insert trigger or Flow for non-UI channels.

2. **Skipping pre-import normalization and relying entirely on the Data Import Wizard dedup** — The wizard's single-field exact match is not a substitute for data cleansing. Uploading raw vendor files without normalizing email casing and removing within-file duplicates guarantees unnecessary inserts. The cost of a 10-minute normalization step before each import is far lower than the cost of post-import merge work.

3. **Configuring high-weight fuzzy matching on non-indexed fields for real-time dedup** — Fuzzy matching on Company or Title fields that are not indexed causes full-table scan evaluation at every lead insert. On large orgs, this adds seconds of latency to every lead save and can cause timeout errors during bulk imports. Anchor matching rules on Email (indexed, selective) and add fuzzy Name as a secondary criterion rather than the primary one.

## Official Sources Used

- Salesforce Help: Duplicate Rules — https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_map_of_reference.htm&type=5
- Salesforce Help: Standard Lead Matching Rule — https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_standard_lead_matching_rule.htm&type=5
- Salesforce Help: Data Import Wizard — https://help.salesforce.com/s/articleView?id=sf.data_import_wizard.htm&type=5
- Salesforce Help: Web-to-Lead — https://help.salesforce.com/s/articleView?id=sf.crm_lead_web_to_lead.htm&type=5
- Apex Developer Guide: Datacloud.DuplicateRule.findDuplicates() — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Datacloud_DuplicateRule.htm
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
- Trailhead: Resolve and Prevent Duplicate Data — https://trailhead.salesforce.com/content/learn/modules/sales_admin_duplicate_management
