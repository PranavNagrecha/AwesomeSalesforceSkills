# Well-Architected Notes — Global Search Configuration

## Relevant Pillars

- **Operational Excellence** — Search Layouts and Synonym Groups are admin-controlled platform features that compound over time. A deliberate audit + refresh cadence (typically annual, or after every major Lightning rollout) keeps search results aligned with the way users actually scan records. Documenting current Search Layouts and active Synonym Groups in the org's Configuration Workbook is a baseline operational hygiene step.
- **Security** — Every column added to a Search Layout exposes that field's value to every user whose FLS allows reading it. Adding sensitive fields (compensation, SSN-bearing, PHI) to a Search Layout is a passive data-leak vector if FLS is not tight. The Customize Application permission required to edit Search Layouts is org-wide and should be granted via narrowly-scoped Permission Sets, not via profile updates.
- **Performance** — Search Layout column choice has no measurable performance impact on the search query itself (Salesforce executes the same SOSL regardless of which columns the layout will render). However, lookup auto-completion behavior and Drop-Down List size affect perceived performance of every lookup field across the org. Synonym Groups add minor index lookup overhead per query, capped well below the per-query budget at the 2,000-active-group limit.

## Architectural Tradeoffs

- **Org-wide Synonyms vs. object-scoped behavior.** Salesforce does not provide per-object scope for Synonym Groups. The choice is binary: accept that a synonym applies everywhere, or do not add it. When a domain shorthand makes sense on Accounts but is wrong on Cases, the correct path is to skip the synonym entirely and solve the search problem with a custom Lightning component running a constrained SOSL query — at the cost of building and maintaining that component.

- **Search Layout completeness vs. column overload.** Configuring all five layout slots per object with full 10-column sets gives users the maximum scanning surface. It also creates a maintenance burden — every renamed field, every new Permission Set whose users lack FLS on those columns, becomes a verification item. The pragmatic middle path: configure Default Layout (Lightning) + Lookup Dialog comprehensively (the two surfaces users hit most), and configure Search Results / Lookup Phone Dialog / Tab only when the use case is documented.

- **Customize Application breadth vs. delegation hygiene.** Salesforce ties Search Layout editing to a broad system permission. The architectural tradeoff is between centralized admin teams (who hold Customize Application org-wide and accept the implicit broad authority) versus delegated admin models (which need scoped Permission Sets and trust around scope discipline). For multi-business-unit orgs, the delegated path is correct despite the absence of a "manage search only" permission.

## Anti-Patterns

1. **Treating Search Results (Classic) as the canonical Search Layout.** Lightning Experience reads only the Default Layout slot. Lightning-first or Lightning-only orgs that configured only Search Results during their Classic era have empty Default Layouts and one-column Lightning search results.

2. **Adding a Synonym Group to "fix" search on one object.** Synonym Groups are org-wide. Single-object equivalences are not a synonym-shaped problem and should be solved via a different mechanism.

3. **Skipping FLS audit when adding columns to Search Layouts.** Hidden FLS renders as blank columns, which users interpret as missing data and file as bugs. Audit FLS on every field added to a Search Layout against every profile and permission set whose users will search.

4. **Diagnosing "newly created record not in search" as a configuration bug.** Index lag is the default explanation for changes within the last 15 minutes. Configuration is usually correct; the index is catching up.

5. **Granting Customize Application via Profile cloning.** The permission survives profile changes and is broader than needed. Permission Set Group assignment is reversible and auditable; profile-based grants are not, easily.

## Official Sources Used

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
