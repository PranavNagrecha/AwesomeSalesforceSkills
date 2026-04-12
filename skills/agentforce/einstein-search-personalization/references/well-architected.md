# Well-Architected Notes — Einstein Search Personalization

## Relevant Pillars

- **Performance** — Einstein Search personalization directly improves task performance for users by surfacing the most relevant records at the top of results. Poorly configured signals (or signals absent entirely) force users to scroll or refine queries, increasing time-on-task. NLS reduces friction further by eliminating the need to construct filter queries manually. Promoted results ensure critical records are instantly accessible.

- **Adaptability** — Personalization signals adapt to evolving user behavior automatically. As a rep's territory changes or their account mix shifts, Einstein re-weights rankings based on new activity patterns. This adaptive behavior means search relevance improves over time without admin intervention — a key advantage over static promoted results alone.

- **Security** — FLS is enforced at every layer of Einstein Search: NLS criteria for hidden fields are silently excluded, and promoted results respect the sharing model. Admins must understand that FLS gaps do not produce errors — they produce silent result distortion. Security reviews should include a check of field permissions for fields likely to appear in NLS queries.

- **Reliability** — Einstein Search personalization falls back gracefully: if a signal has insufficient data (e.g. a new user), it simply contributes no weight. NLS falls back to keyword search if the query is not parseable. These degradation paths are silent, which is reliable in terms of availability but can mislead users who expect personalized results from day one.

- **Operational Excellence** — Setup is entirely declarative (no code, no deployments). Changes to signals, promoted results, and NLS settings take effect immediately. This low operational overhead is a strength, but it also means changes are easy to make accidentally. Admins should document current settings in change management records since there is no built-in audit trail for Einstein Search Settings changes.

## Architectural Tradeoffs

**Promoted results vs. personalization signals:** Promoted results guarantee placement for specific keyword-record pairs but are static and do not adapt to individual users. Personalization signals adapt but require activity history and cannot guarantee specific records appear for specific searches. Most production orgs benefit from a hybrid approach: promoted results for a small set of always-critical records, signals for the bulk of ranking.

**NLS vs. custom filter UX:** NLS is zero-code, zero-maintenance, and works immediately for supported objects. A custom filter UI built in LWC or OmniStudio can cover custom objects and complex logic, but requires development, testing, and ongoing maintenance. Prefer NLS for standard objects; design a custom filter panel only when the object or language scope requirement is genuinely outside NLS capability.

**All signals on vs. selective signals:** Enabling all four personalization signals provides the most complete ranking picture, but in some use cases (e.g. a shared service account team where ownership is not meaningful), some signals add noise. Review whether the four signals map to actual user behavior patterns in the org before selectively disabling any.

## Anti-Patterns

1. **Promising NLS on custom objects** — Configuring Einstein Search with NLS and assuring stakeholders that custom objects will support conversational queries. NLS is limited to five standard objects and there is no extension mechanism. This promise will fail in user acceptance testing and damage trust in the search rollout.

2. **Ignoring FLS before enabling NLS** — Enabling NLS without auditing field-level security for commonly queried fields. Fields with hidden FLS silently drop their criteria, making search appear to work while returning incorrect result sets. This is a security and reliability risk that only surfaces through careful query testing.

3. **Relying solely on promoted results without signals** — Configuring only promoted results and assuming search is "personalized." Promoted results are global, static, and identical for all users. Without personalization signals, search results for non-promoted records are unranked and feel generic. Promoted results are a complement to signals, not a replacement.

## Official Sources Used

- Einstein Search Help — Get Personalized Results — https://help.salesforce.com/s/articleView?id=sf.search_einstein_personalization.htm
- Einstein Search Help — Manage Einstein Search Settings — https://help.salesforce.com/s/articleView?id=sf.search_einstein_settings.htm
- Einstein Search Help — Einstein Search Limitations — https://help.salesforce.com/s/articleView?id=sf.search_einstein_limitations.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
