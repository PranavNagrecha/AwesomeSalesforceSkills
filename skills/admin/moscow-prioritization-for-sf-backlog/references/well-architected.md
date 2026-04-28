# Well-Architected Notes — MoSCoW Prioritization for Salesforce Backlog

## Relevant Pillars

- **Operational Excellence** — Prioritization is the operational heartbeat of a Salesforce delivery practice. A backlog without a disciplined prioritization rubric becomes either an empty queue (everyone idle) or an over-committed queue (everyone late). MoSCoW + effort + value gives a team a repeatable, auditable way to commit work to a horizon and to defend the commit to sponsors. This skill directly supports the Well-Architected operational-excellence theme of "manageable, predictable change".
- **Reliability** — A release whose Must list exceeds capacity is a release that will slip. Slip cascades degrade reliability of every downstream commitment: sponsor trust, integration cutover dates, training schedules, change-management communications. The 60% Must rule and the capacity-bounded commit rule are reliability controls. Treating Won't-ever as an archive decision is a reliability control on the backlog itself.

## Architectural Tradeoffs

- **MoSCoW vs full-WSJF backlog ranking** — MoSCoW is fast and human-legible; WSJF is rigorous but cognitively expensive. The tradeoff is settled by using MoSCoW as the primary signal and WSJF only at capacity-boundary ties. Choosing one or the other exclusively is the wrong frame.
- **Sponsor-present synchronous session vs asynchronous review** — Asynchronous review feels efficient and produces provisional output that frequently gets overturned. Synchronous sessions cost calendar time but produce durable commits. The tradeoff favours synchronous for commit-grade output and asynchronous only for advisory passes.
- **Frequent re-prioritization vs locked grooming cadence** — Frequent re-prioritization preserves agility at the cost of throughput. Locked cadence preserves throughput at the cost of responsiveness. A two-sprint grooming cadence is the typical equilibrium for a Salesforce admin/dev team; sub-sprint changes go to the next grooming unless a production-down or regulatory exception applies.

## Anti-Patterns

1. **Everything-is-Must** — Without the 60% rule, MoSCoW collapses into a wishlist. The remediation is to enforce effort tagging at the same session and surface the capacity math.
2. **Won't as a permanent purgatory** — Items tagged Won't-this-release that are never archived clog every future grooming session. The remediation is the Won't-ever sub-tag and active archival.
3. **WSJF as backlog ranking** — Using WSJF beyond a tie-break creates score-fatigue and produces noisy rankings that the team stops trusting. The remediation is to scope WSJF to clusters of <15 rows.

## Official Sources Used

- DSDM Agile Project Framework — MoSCoW Prioritisation — https://www.agilebusiness.org/dsdm-project-framework/moscow-prioririsation.html
- Scaled Agile Framework (SAFe) — WSJF — https://framework.scaledagile.com/wsjf
- Salesforce Architects — Well-Architected: Operationally Excellent — https://architect.salesforce.com/well-architected/trusted/operationally-excellent
- Salesforce Architects — Well-Architected: Resilient — https://architect.salesforce.com/well-architected/trusted/resilient
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
