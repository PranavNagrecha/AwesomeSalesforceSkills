# Well-Architected Notes — User Story Writing For Salesforce

## Relevant Pillars

User-story shape is upstream of every build pillar. The pillars below describe how poorly-shaped stories degrade the eventual implementation.

- **Operational Excellence** — Stories are the unit of work that flows from the business to the build team. Stories that lack INVEST-compliance, observable AC, or handoff metadata break the operational chain: build agents stall, dependencies surface late, sprint demos slip. A clean story shape is the operational primitive that makes the rest of the SDLC reliable.

- **User Experience** — The persona named in `As A` is the same persona whose UX gets built. A vague "as a user" persona means the build team makes UX choices without grounding — wrong navigation, wrong field-level security, wrong record types surfaced. Grounding the persona in a Salesforce profile/permission set/role is what makes the resulting UX defensible.

- **Reliability** — Acceptance criteria with sad-path coverage are what make a feature reliable in production. Stories that ship with happy-path-only AC produce features that work in demo and break in production at the first edge case. The "at least one sad path AC" rule in this skill is a reliability primitive.

## Architectural Tradeoffs

| Tradeoff | When to favor it |
|---|---|
| Smaller stories vs. coherent narrative | Favor smaller stories when in doubt — split-then-rebuild is cheaper than commit-then-slip |
| Specific AC vs. negotiable implementation | The AC must be specific (what is observable); the implementation must stay negotiable (no Flow/Apex prescription in the story body) |
| Handoff metadata vs. backlog tool simplicity | Always emit the handoff JSON, even if the backlog tool only renders markdown — downstream agents need the structured form |
| Pinning a complexity early vs. waiting for refinement | Pin a draft size early using the heuristic; let refinement adjust it. Don't ship without a size. |

## Anti-Patterns

1. **Implementation-prescriptive stories** — A story that names "use a Record-Triggered Flow with a Fast Field Update" violates Negotiable. The build agent should choose technology per `standards/decision-trees/automation-selection.md`. Shape the story around *what the persona observes*, not *how it gets done*.

2. **The "epic disguised as a story" anti-pattern** — A story titled "Quote-to-cash automation" or "Lead routing" is not a story; it's an epic. Sizing comes back XL. Splitting must happen before commit. See the workflow-step / business-rule / persona / data-variation / happy-path splitting techniques in SKILL.md.

3. **Handoff-less stories** — A story committed without `recommended_agents[]` populated severs the chain. The next agent has no signal to pick up the work, and the BA becomes a manual router. The handoff JSON is the architectural primitive that makes BA-to-build automation possible.

## Official Sources Used

- Salesforce Trailhead — User Story Creation module — https://trailhead.salesforce.com/content/learn/modules/user-story-creation
- Salesforce Trailhead — Agile Methods for Salesforce — https://trailhead.salesforce.com/content/learn/modules/agile-methods-for-salesforce
- Salesforce Certified Business Analyst Exam Guide — https://trailhead.salesforce.com/help?article=Salesforce-Certified-Business-Analyst-Exam-Guide
- Salesforce Architects: Business Analysts and the Well-Architected Framework — https://architect.salesforce.com/well-architected
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
