# Well-Architected Notes — Process Flow As-Is To-Be

## Relevant Pillars

- **Operational Excellence** — Process maps are the canonical artefact tying business intent to platform configuration. A versioned, swim-lane-disciplined map with explicit automation-tier annotations is the difference between auditable change management and undocumented drift.
- **Reliability** — Reliability is built at design time, not at run time. Exception paths, timeout handling on every integration handshake, and explicit AND/OR-merge semantics on parallel paths are what make the build resilient. Maps that document only happy paths produce systems that fail silently.
- **User Experience** — The customer / external-counterparty swim lane is what surfaces the user experience design. Forgetting it produces internal-only automations that stall waiting for an action no one designed for. Including it forces the team to think about portal links, email confirmations, and signing flows as first-class steps.

## Architectural Tradeoffs

The central tradeoff in process mapping is **automation depth vs change agility**. Tagging every step `[FLOW]` or `[APEX]` produces a fully automated process that is fast and auditable — but expensive to change when the business pivots. Leaving steps `[MANUAL]` produces a slower process that is cheap to change. The map should make this tradeoff visible, not hide it. The "manual residue" output is the explicit acknowledgement of what the team chose to leave changeable.

The second tradeoff is **map completeness vs map readability**. A 50-step map covers every edge case but no human can read it. A 10-step map is readable but loses fidelity. The right answer is to cap each map at 30 steps and split larger processes into sub-processes with named handoff points. The handoff JSON's `process_id` makes sub-processes composable.

The third tradeoff is **decision-tree literalism vs domain judgement**. The `automation-selection.md` tree gives a deterministic answer, but real processes sometimes have constraints the tree does not encode (regulatory sign-off, legacy system limitations, team skill mix). When the practitioner overrides the tree's answer, the override must be documented in the citation: "automation-selection.md Q3 → Apex, but tagged `[FLOW]` because team has no Apex maintainers — accepted limit risk."

## Anti-Patterns

1. **Treating the As-Is as optional.** A To-Be without an As-Is is wishful thinking. The As-Is provides the ground truth that justifies each automation candidate.
2. **Lanes per system instead of per actor.** Architecture diagrams have system lanes; process diagrams have actor lanes. Conflating the two hides responsibility.
3. **Hand-waving exception paths.** Every decision diamond and integration handshake has a sad path. Documenting only the happy path produces systems that fail silently in UAT.
4. **Re-answering the decision tree inside the map.** The automation-selection tree is the authority. The map should cite it, not duplicate its logic. A map that re-explains "Flow vs Apex" inline is a smell — link to the tree instead.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — for the pillar definitions referenced above
- Salesforce Architects: Business Process Mapping — https://architect.salesforce.com/decision-guides — guidance on swim-lane and process-mapping conventions in the Salesforce context
- Trailhead: Business Process Mapping module — https://trailhead.salesforce.com/content/learn/modules/business-process-mapping — canonical introduction to swim-lane mapping for Salesforce projects
- Salesforce Help: Approval Processes — https://help.salesforce.com/s/articleView?id=sf.approvals_overview.htm — for the `[APPROVAL]` tier semantics and audit-trail features
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm — for the standard objects referenced in process maps
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — for the metadata types implied by automation-tier annotations (Flow, ApprovalProcess, ApexClass, PlatformEventChannel)
- BPMN 2.0 Specification (OMG) — https://www.omg.org/spec/BPMN/2.0/ — for the swim-lane, decision diamond, and parallel-gateway conventions adopted in this skill
