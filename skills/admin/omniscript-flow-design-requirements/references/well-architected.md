# Well-Architected Notes — OmniScript Flow Design Requirements

## Relevant Pillars

- **Reliability** — Well-specified requirements prevent mid-build structural discoveries that force OmniScript rebuilds; documenting all structural requirements (Navigate Action, data source bindings) before build reduces activation-failure risk.
- **Operational Excellence** — Structured requirements artifacts (journey maps, data matrices) serve as living documentation for future maintenance; without them, OmniScript modifications require reverse-engineering the built component.
- **Security** — Requirements must identify user context (internal agent vs Experience Cloud community user vs guest user); guest-user OmniScripts require explicit sharing rules and FLS documentation that must be captured at requirements time.
- **Performance** — Requirements that specify Integration Procedure vs DataRaptor vs Remote Action for each data need influence runtime performance; IP with sequential callouts vs parallel sub-actions must be a requirements-time decision.
- **Scalability** — Requirements that identify high-volume use cases (OmniScript launched by automation for bulk record processing) must flag that OmniScript is not designed for bulk processing and an alternative architecture should be specified.

## Architectural Tradeoffs

**OmniScript vs Screen Flow:** Requirements should include a documented decision for why OmniScript is chosen over Screen Flow. OmniScript requires a license and adds managed complexity; for simple single-object screens, Screen Flow is the preferred choice. The decision should be documented in requirements so it is auditable.

**DataRaptor vs Integration Procedure:** A DataRaptor is the right choice for simple single-object CRUD operations; an Integration Procedure is required for multi-object orchestration, external API calls, or complex branching server-side logic. Requirements must specify which is appropriate per step — this decision cannot be deferred to the developer without risking an incorrect implementation that must be rebuilt.

**Single OmniScript vs Embedded OmniScripts:** Complex multi-section processes are sometimes better decomposed into a primary OmniScript that launches child OmniScripts via OmniScript Launch actions. Requirements should evaluate whether a single long OmniScript or a composed multi-OmniScript architecture better serves the user journey and maintenance model.

## Anti-Patterns

1. **Generic wireframes without OmniScript-specific structure** — Producing Screen Flow-style wireframes without Block container groupings, Conditional View expressions, and Pre/Post action timing creates ambiguity that results in developer re-work. Requirements must use OmniScript-native notation.

2. **Deferring data source decisions to the developer** — Requirements that say "load account data somewhere" without specifying DataRaptor vs Integration Procedure, Pre vs Post timing, and the specific fields needed force the developer to make architectural decisions that should be requirements-time choices.

3. **Omitting Navigate Action from requirements** — Treating the form submission as implicit (as in standard web forms) and not specifying the Navigate Action type and destination causes activation failures that are discovered late in the build cycle.

## Official Sources Used

- OmniScript Best Practices — https://help.salesforce.com/s/articleView?id=sf.os_omniscript_best_practices.htm
- OmniScripts with Branching — https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/omniscripts-with-branching
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `omnistudio/omniscript-design-patterns` — implementation skill to use after requirements are complete
- `admin/omnistudio-vs-standard-decision` — decision skill for whether OmniScript is the right tool
- `admin/flexcard-requirements` — companion BA requirements skill for FlexCard components
