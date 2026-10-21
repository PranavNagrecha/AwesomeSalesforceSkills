# Well-Architected Notes — Global Search Configuration

## Relevant Pillars

- **Operational Excellence** — Search Layouts and Synonym Groups are admin-controlled platform features that compound over time. A deliberate audit + refresh cadence (typically annual, or after every major Lightning rollout) keeps search results aligned with the way users actually scan records. Documenting current Search Layouts and deployed Synonym Groups in the org's Configuration Workbook is a baseline operational hygiene step.
- **Security** — Every column added to a Search Layout exposes that field's value to every user whose FLS allows reading it. Adding sensitive fields (compensation, SSN-bearing, PHI) to a Search Layout is a passive data-leak vector if FLS is not tight. The Customize Application permission used to edit Search Layouts (UNVERIFIED (2026-10-20): Help-only) is org-wide and should be granted via narrowly-scoped Permission Sets, not via profile updates; synonyms need "Manage Synonyms" (api_meta 264 L136378).
- **Performance** — Search Layout column choice is unlikely to change the index search itself (UNVERIFIED (2026-10-20): no corpus line measures it; search builds its result set from the index first; "the result set is then used to query the records from the database to retrieve the fields that a user sees", ldv 264 L171-174). However, per-object lookup auto-completion and results-per-page settings shape perceived lookup performance (UNVERIFIED (2026-10-20): no corpus line measures it). UNVERIFIED (2026-10-20): any synonym query overhead and a 2,000-active-group limit.

## Architectural Tradeoffs

- **Org-wide Synonyms vs. object-scoped behavior.** `SynonymGroup` has no object field (api_meta 264 L136400-136410); UNVERIFIED (2026-10-20): that a group therefore applies to every object. The choice is binary: accept that a synonym applies everywhere, or do not add it. When a domain shorthand makes sense on Accounts but is wrong on Cases, the correct path is to skip the synonym entirely and solve the search problem with a custom Lightning component running a constrained SOSL query — at the cost of building and maintaining that component.

- **Search Layout completeness vs. column overload.** Configuring every `SearchLayouts` list per object with full column sets (UNVERIFIED (2026-10-20): the 10-column cap) gives users the maximum scanning surface. It also creates a maintenance burden — every renamed field, every new Permission Set whose users lack FLS on those columns, becomes a verification item. The pragmatic middle path: configure `searchResultsAdditionalFields` (plus any `profileSearchLayouts`) and `lookupDialogsAdditionalFields` comprehensively, and configure the phone-dialog and tab lists only when the use case is documented.

- **Customize Application breadth vs. delegation hygiene.** Salesforce ties Search Layout editing to a broad system permission (UNVERIFIED (2026-10-20): Help-only). The architectural tradeoff is between centralized admin teams (who hold Customize Application org-wide and accept the implicit broad authority) versus delegated admin models (which need scoped Permission Sets and trust around scope discipline). For multi-business-unit orgs, the delegated path is correct despite the absence of a "manage search only" permission.

## Anti-Patterns

1. **Treating the default search results layout as the only one.** `searchResultsAdditionalFields` applies only where no `profileSearchLayouts` entry exists for the user's profile (api_meta 264 L47265-47266); an audit that skips profile layouts misses what most users see.

2. **Adding a Synonym Group to "fix" search on one object.** Synonym Groups have no object scope in metadata (api_meta 264 L136400-136410; UNVERIFIED (2026-10-20): org-wide reach). Single-object equivalences are not a synonym-shaped problem and should be solved via a different mechanism.

3. **Skipping FLS audit when adding columns to Search Layouts.** Hidden FLS renders as blank columns (UNVERIFIED (2026-10-20): Help-only), which users interpret as missing data and file as bugs. Audit FLS on every field added to a Search Layout against every profile and permission set whose users will search.

4. **Diagnosing "newly created record not in search" as a configuration bug.** Index lag — "about 15 minutes or more" (ldv 264 L160-162) — is the default explanation. Configuration is usually correct; the index is catching up.

5. **Granting Customize Application via Profile cloning.** The permission survives profile changes and is broader than needed. Permission Set Group assignment is reversible and auditable; profile-based grants are not, easily.

## Official Sources Used

- Metadata API — `SearchLayouts` fields, mandatory Name column, no wildcard — api_meta 264 L47495-47622; `profileSearchLayouts` as the per-profile override of the default layout — L44503-44506, L47259-47266
- Metadata API — `SearchSettings` / `ObjectSearchSetting` fields (lookup autocomplete, results per page, User-only blank lookup) — api_meta 264 L129086-129249
- Metadata API — `SynonymDictionary` / `SynonymGroup` (Manage Synonyms, 50-char terms, symmetric groups) — api_meta 264 L136361-136413
- Metadata API — `enableSearch` defaults for custom and external objects; Cross-Org and OData `searchEnabled` — api_meta 264 L44347-44354, L13818-13850; Apex custom adapter `SEARCH` capability — apexref 262 L151747-151752
- Large Data Volumes Best Practices — index lag "about 15 minutes or more"; results narrowed by access permissions — ldv 264 L160-172
- Customize Search Results in Lightning Experience — https://help.salesforce.com/s/articleView?id=sf.search_results_customize_lightning_experience.htm
- Search Layouts — https://help.salesforce.com/s/articleView?id=sf.search_layouts_overview.htm
- Synonym Groups — https://help.salesforce.com/s/articleView?id=sf.search_synonyms_create.htm
- Configure Search Settings (Setup → Search Settings) — https://help.salesforce.com/s/articleView?id=sf.search_settings.htm
- Enable Salesforce Connect External Object Search — https://help.salesforce.com/s/articleView?id=sf.platform_connect_search.htm
- Make Salesforce Search Index Aware — https://help.salesforce.com/s/articleView?id=sf.search_overview.htm
- SOQL and SOSL Reference (SOSL) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl.htm
- Metadata API: CustomObject `<searchLayouts>` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/customobject.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
