# Well-Architected Notes — Sales Process Mapping

## Relevant Pillars

- **Operational Excellence** — The primary pillar for this skill. A well-designed sales process mapping exercise produces documented entry/exit criteria, transition rules, and win/loss taxonomies that make the Salesforce implementation deterministic and auditable. Without it, configuration decisions are made ad hoc, leading to rework and degraded data quality over time. The mapping document is the operational specification that downstream configuration, validation rules, and automation are built from.

- **User Experience** — The secondary pillar. Well-scoped stage design directly improves the rep's UI experience: reps see only the stages relevant to their deal type, Path guidance is targeted, and required fields per stage match the actual deal context. A sales process mapping artefact designed with distinct motions (new logo, renewal, channel) mapped to separate stage sequences allows each motion to evolve independently without disrupting the others. A single undifferentiated stage sequence creates tight coupling: a change needed for the enterprise motion breaks the SMB motion's user experience.

- **Trust** — Indirectly relevant. Forecast accuracy depends on stage data quality, which depends on well-defined stage gates. An organisation whose sales team does not trust the forecast is an organisation whose sales process mapping was either skipped or produced without stakeholder buy-in. The mapping exercise, when done with the right stakeholders, produces alignment that makes stage data trustworthy.

## Architectural Tradeoffs

**One shared process vs. separate processes per motion:** A single Sales Process is simpler to configure and maintain but forces all motions through the same stage vocabulary and forecast category assignments. Separate processes per motion allow independent evolution but require separate Record Types, separate Page Layouts, and separate Path configurations. The mapping exercise is the right moment to make this decision — it is much more expensive to split a shared process after go-live than to design for separation upfront.

**Descriptive stage names vs. activity-based stage names:** Stage names that describe buyer state (e.g., "Under Evaluation") age better than names that describe rep activity (e.g., "Demo Sent"). Activity-based names tend to multiply as the team adds new activities, inflating the stage count beyond what is manageable. Buyer-state names focus on what has been achieved, which is what entry/exit criteria capture.

**Strict enforcement via validation rules vs. advisory guidance via Path:** Path provides low-friction guidance with zero enforcement overhead. Validation rules enforce stage gate compliance but add friction and require maintenance. The mapping exercise must explicitly decide, for each transition, whether enforcement is required (producing a validation rule requirement) or advisory is sufficient (producing a Path configuration requirement). Defaulting to enforcement for everything creates excessive friction; defaulting to advisory for everything produces meaningless stage data.

## Anti-Patterns

1. **Stage list without criteria** — Delivering a list of stage names to the configuration team without entry/exit criteria. This is the most common and most damaging anti-pattern in sales process mapping. The configuration team implements the stages, but without criteria, reps use stages arbitrarily. Stage data degrades within 60 days. The fix (adding criteria retroactively) requires discovery, validation rule implementation, and rep re-training — all more expensive after go-live than during the original mapping exercise.

2. **Win/loss taxonomy designed in isolation** — Creating a win/loss reason taxonomy without involving front-line reps and sales managers in the design. Analysts and admins tend to produce taxonomies that are either too granular (20+ reasons) or too strategic (reasons that describe macro trends rather than deal-specific factors). Neither is completed consistently by reps. A taxonomy built with actual sellers, constrained to 5–8 values per outcome, has dramatically better completion rates and data utility.

3. **Ignoring platform constraints during mapping** — Producing a mapping document that references forecast category labels, probability defaults, or stage progression enforcement without checking whether the platform supports the specified design. Documents that list "Upside" as a forecast category, or specify "stage order enforced by Salesforce natively," require rework when the configuration team discovers the constraints. The mapping practitioner must validate all platform-level design decisions before the document is finalised.

## Official Sources Used

- Trailhead: Create and Manage Stages and Sales Processes — https://trailhead.salesforce.com/content/learn/modules/sales-cloud-basics/set-up-stages-and-sales-processes
- Trailhead: Business Process Mapping — https://trailhead.salesforce.com/content/learn/modules/salesforce-business-analyst-quick-look/map-business-processes
- Salesforce Object Reference: OpportunityStage — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunitystage.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Sales Processes — https://help.salesforce.com/s/articleView?id=sf.customize_salesstages.htm
- Salesforce Help: Opportunity Stages — https://help.salesforce.com/s/articleView?id=sf.customize_opportunitystages.htm
