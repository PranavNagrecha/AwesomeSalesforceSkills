# Well-Architected Notes — Knowledge Taxonomy Design

## Relevant Pillars

- **Scalability** — The primary concern for Knowledge taxonomy. A poorly designed category hierarchy becomes unmaintainable as article volume grows. The 5-group / 5-level / 100-category limits create hard boundaries that require deliberate upfront design. Deep hierarchies compound search latency and SOSL result ranking degradation as article counts increase. A flat, composable multi-group taxonomy scales linearly with content growth.
- **Operational Excellence** — The Validation Status gating model and KCS Solve/Evolve Loop are operational design decisions, not just feature configurations. Well-architected Knowledge orgs define clear ownership (who authors, who reviews, who archives), measure content freshness (Validation Status distribution, stale article rate), and close the content gap loop via Search Activity Gaps. Without operational process design, the taxonomy degrades over time regardless of its structural quality.
- **User Experience** — Taxonomy depth and category naming directly determine agent and customer search experience. Agents navigating a 5-level tree to find an article add 30–60 seconds to average handle time at scale. Customers encountering zero-result searches on Experience Cloud abandon self-service and create cases. Well-architected taxonomy design treats findability as a first-class requirement, not an afterthought.

## Architectural Tradeoffs

**Granularity vs Maintainability:** Fine-grained categories at deep levels enable precise filtering but require high-maintenance categorisation at authorship time and create fragile structures when product lines change. Broader categories with fewer levels are easier to maintain and more resilient to org evolution. The tradeoff should be resolved in favour of breadth unless the org has a dedicated Knowledge admin team.

**Immediate Publication vs Quality Gating:** The KCS Solve Loop requires publishing imperfect articles immediately to maximise content coverage. A gated approval model maximises quality but delays coverage. The Well-Architected answer depends on case volume and agent skill: high-volume orgs with distributed authorship benefit from the Solve Loop; low-volume orgs with specialist authors can afford a gated model. Hybrid models (publish immediately with WIP status, evolve asynchronously) are the common production choice.

**Single Group vs Multiple Groups:** Using a single Data Category Group for all dimensions is simpler to set up but harder to navigate and extend. Multiple groups require more configuration but produce dramatically better findability through composable filters. The tradeoff tips toward multiple groups once an org has more than two independent classification dimensions and more than 500 articles.

## Anti-Patterns

1. **Deep single-group combined taxonomy** — Encoding product, topic, audience, and region in a single 4–5 level hierarchy forces articles into specific tree positions that become wrong when any dimension changes. The fix requires bulk re-categorisation. Use independent flat groups per dimension and let the platform compose them at query time.
2. **Enabling Validation Status without a workflow design** — Enabling the setting without defining picklist values, assigning ownership, or building the review queue results in all articles defaulting to "Not Validated" indefinitely. This is worse than no quality gating because it implies a false promise of a review process. Design the full workflow — roles, transitions, review cadence — before enabling in production.
3. **Ignoring Search Activity Gaps as a content strategy signal** — Treating Knowledge taxonomy as a one-time configuration decision rather than an ongoing content strategy creates static taxonomies that diverge from actual user search behaviour. The Search Activity Gaps dashboard is the primary feedback mechanism; orgs that do not review it at least monthly accumulate content gaps that erode agent and customer self-service adoption over time.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Knowledge Data Categories Best Practices — https://help.salesforce.com/s/articleView?id=sf.knowledge_data_category_best_practices.htm
- Work with Data Categories — https://help.salesforce.com/s/articleView?id=sf.knowledge_data_categories_parent.htm
- Archive Articles and Translations — https://help.salesforce.com/s/articleView?id=sf.knowledge_archiving_parent.htm
- KCS Methodology — Trailhead (Knowledge-Centered Service) — https://trailhead.salesforce.com/content/learn/modules/knowledge-centered-service
