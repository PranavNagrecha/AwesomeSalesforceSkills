# Well-Architected Notes — Client Onboarding Design

## Relevant Pillars

- **Operational Excellence** — The most directly relevant pillar. A well-designed onboarding process establishes clear ownership, defined SLAs, governance for process changes (clone-and-republish versioning), and monitoring for in-progress onboarding journeys. Poorly governed onboarding processes degrade operationally over time: templates proliferate without naming conventions, ownership is unclear, and compliance changes are made by emergency workaround.

- **Security** — Compliance checkpoint sequencing is a security and regulatory concern. KYC/AML identity verification, beneficial ownership disclosure, and consent capture must occur in the correct order and must be enforced by the platform (required tasks, approval gates) rather than by convention alone. A process design that relies on advisors manually following a sequence without platform enforcement is a security and audit risk.

- **Reliability** — The onboarding process must behave consistently across all clients. Platform-enforced gates (required Action Plan tasks, approval steps) provide reliability that manual checklists and email reminders do not. The in-flight plan policy during version transitions is a reliability concern: clients should never experience an inconsistent onboarding sequence due to an unmanaged template update.

- **Adaptability** — The template versioning governance design directly addresses adaptability. A process that cannot be safely updated post-launch is fragile. The clone-and-republish pattern, combined with a named owner and change protocol, makes the onboarding process adaptable to regulatory changes without requiring a full re-implementation.

- **Performance** — Less directly relevant at the process design layer, but the decision to split large task sequences across multiple Action Plan phases (due to the 75-task limit) and the choice between OmniStudio and Screen Flow have downstream performance implications that should be flagged in the design brief.

## Architectural Tradeoffs

**OmniStudio vs. Screen Flow for intake:** OmniStudio OmniScripts offer a richer, more flexible intake experience with declarative branching and reusable DataRaptor integration steps. Screen Flows provide the same core capability with no additional license cost and are sufficient for most onboarding intake scenarios. The tradeoff is feature richness vs. license cost and implementation complexity. For orgs already licensing OmniStudio, OmniScript is the preferred choice. For orgs without OmniStudio, Screen Flow is the correct tool and should not be treated as a compromise — it is the standard platform capability.

**Platform-enforced gates vs. convention-based process:** Required tasks in Action Plans and approval steps in Approval Processes enforce compliance checkpoints at the platform level. Convention-based processes (e.g., "advisors know not to send funding instructions before KYC is cleared") are unreliable and not auditable. Well-Architected FSC onboarding uses platform enforcement for all mandatory compliance checkpoints.

**Single monolithic template vs. phased templates:** A single large template is simpler to manage but risks hitting the 75-task limit and creates a single point of failure for version updates (any change requires retiring the entire template). Phased templates (one per onboarding stage) are more modular, stay well under the task limit, and allow compliance to update a single phase without touching the rest of the onboarding sequence. For complex onboarding processes, phased templates are the more adaptable and reliable design.

## Anti-Patterns

1. **Designing for OmniStudio without confirming license** — Producing an OmniScript-based intake design before confirming OmniStudio license availability creates rework risk and can block implementation entirely. The correct approach is to confirm licensing in the design phase and select the intake tool accordingly.

2. **Omitting template versioning governance from the initial design** — Treating the clone-and-republish constraint as an implementation detail rather than a process design requirement results in no governance plan when the first post-launch compliance change arrives. Versioning governance must be part of the process design deliverable, not an afterthought.

3. **Sequential compliance checks enforced by convention, not platform** — Designing an onboarding process where compliance checkpoints are communicated as instructions to advisors (rather than required tasks or approval gates) produces an unauditable process that will fail regulatory review. All mandatory compliance checkpoints must be enforced by the platform.

## Official Sources Used

- Action Plans Overview — FSC Admin Guide (help.salesforce.com) — confirmed Action Plan template immutability, object support, and launch mechanics
- Financial Services Cloud Administrator Guide (help.salesforce.com) — FSC feature and license context, OmniStudio as separately licensed add-on
- Salesforce Well-Architected Overview (architect.salesforce.com) — Operational Excellence and Adaptability pillar framing for process governance and versioning design
