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

3. **Omitting Navigate Action from requirements** — Treating the form submission as implicit (as in standard web forms) and not specifying the Navigate Action type and destination leaves users on the final Step, and the gap is discovered late in the build cycle.

## Official Sources Used

Read for the 2026-10-03 revision (Trailhead pages fetch as plain HTML; help.salesforce.com does not):

- Trailhead, Design and Build a Branching Omniscript: https://trailhead.salesforce.com/content/learn/modules/omniscripts-with-branching/design-and-build-a-branching-omniscript. Supports the required-elements list, Conditional View on almost every element, Block-per-branch grouping, and the Send/Response JSON properties.
- Trailhead, Validate Data and Handle Errors: https://trailhead.salesforce.com/content/learn/modules/omniscripts-with-branching/validate-data-and-handle-errors. Supports current-Step-only required fields and the Set Errors properties.
- Trailhead, Configure a Simple OmniScript: https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/create-a-simple-omniscript. Supports Type/SubType/Language identity, one active version, element naming, action placement semantics, and JSON-to-element name matching.
- Trailhead, Optimize Workflow with OmniScript Design: https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/design-a-simple-omniscript. Supports action placement before and after the Step and the Edit Account example.
- Trailhead, Explore Omniscript Group and Input Elements: https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript-fundamentals/explore-omniscript-group-and-input-elements. Supports conditional Steps, Action Block parallel execution, and input types.
- Trailhead, Use Action, Function, and Display Elements: https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript-fundamentals/use-action-function-and-display-elements. Supports Navigate actions, one-level nesting, and unique element names across parent and child.
- Salesforce Industries Developer Guide (Spring '26), OmniScript metadata type (Discovery Framework Metadata API Types): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_industries_dev_guide.pdf. Supports the `omniScript` suffix, `omniScripts` folder, required `type`/`subType`/`language`, and `uniqueName` format.

Carried from earlier revisions (not re-read on 2026-10-03):

- OmniScript Best Practices — https://help.salesforce.com/s/articleView?id=sf.os_omniscript_best_practices.htm
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `omnistudio/omniscript-design-patterns` — implementation skill to use after requirements are complete
- `architect/omnistudio-vs-standard-decision` — decision skill for whether OmniScript is the right tool
- `admin/flexcard-requirements` — companion BA requirements skill for FlexCard components
