# Well-Architected Notes — Nonprofit Platform Architecture

## Relevant Pillars

### Trustworthiness

Trustworthiness is the most critical WAF pillar for NPC platform architecture. The Person Account data model is the single source of truth for constituent identity across all six modules. A trustworthy NPC architecture must define:
- Constituent deduplication strategy before any module is configured (Person Account matching rules and duplicate rules)
- Data ownership model: who can create, edit, and merge constituent records
- Audit trail and data lineage for gift transactions processed via the Fundraising Connect API
- A canonical record-of-truth for constituent giving history, volunteer hours, and program participation when data crosses module boundaries

### Adaptability

Adaptability governs long-term platform health. NPC's modular architecture is a natural enabler of adaptability, but only if the cross-module data model is designed for extension from the start:
- Person Account record types and page layouts must accommodate constituent roles from modules not yet active (a donor who later becomes a volunteer must not require a record type migration)
- SIDM object customization should be additive (custom fields on standard objects) rather than shadow objects that duplicate SIDM functionality
- Integration architecture should use loosely coupled patterns (Platform Events, Connect API) rather than tightly coupled direct DML, enabling module replacements without integration rewrites
- Phasing strategy must include a module dependency map so future module additions do not require backtracking on foundational decisions

### Operational Excellence

Operational Excellence for NPC spans configuration governance, release management, and team capability:
- NPC modules should be deployed via scratch orgs and unlocked packages (not change sets) to maintain configuration traceability
- Gift Entry Manager workflows must include a reconciliation process with the finance system — configuration without finance sign-off is an operational risk
- Volunteer Management's 19 objects require documented data stewardship roles (who approves volunteer hours, who maintains capacity records)
- Agentforce agent prompts and grounding configurations are versioned artifacts that must be managed in source control, not manually edited in production

### Security

NPC's Security considerations span the Person Account sharing model and external-facing module surfaces:
- Person Account OWD and sharing rules govern constituent visibility across the entire platform — a sharing model error in one module exposes constituent data across all modules
- Grantmaking implementations with Experience Cloud require explicit sharing rule design for external grant applicants: applicants must see only their own Funding Request records
- AI/Agentforce agents with Data Cloud grounding must have field-level security and data access policies defined at the Data Cloud layer before agent activation
- Payment processing via the Fundraising Connect API must route through PCI-compliant payment processor infrastructure — gift transaction records in NPC store tokenized references, not raw payment data

---

## Architectural Tradeoffs

### Modular Licensing vs. Holistic Data Model Design

The NPC modular licensing model encourages organizations to license only the modules they need today. The architectural tradeoff is that each deferred module may require data model retrofitting when it is eventually added. Organizations that design the Person Account record type strategy and cross-module SIDM object schema for the full intended platform scope — even before all modules are licensed — reduce future rework significantly. The cost is slightly over-engineered configuration in phase 1; the benefit is no data model migration in phases 2 and 3.

### Connect API Integration vs. Direct Apex DML

Integrations that write gift transaction records via the Fundraising Connect API benefit from Salesforce-managed business logic (duplicate detection, batch reconciliation, rollup triggers). Direct Apex DML on Gift Transaction objects bypasses this logic and produces silent data integrity issues that are difficult to detect and expensive to remediate. The tradeoff is integration complexity: Connect API requires REST endpoint management and API version governance, while direct DML is simpler to implement. For any production fundraising integration, Connect API is the correct pattern regardless of short-term complexity cost.

### All-Modules-Now vs. Phased Adoption

Launching all licensed NPC modules simultaneously minimizes total project calendar time but maximizes project risk. Cross-module data dependencies compound: an error in the Person Account deduplication strategy affects every module simultaneously. Phased adoption isolates defects but extends the timeline to full platform capability. For organizations with more than two modules in scope, phased adoption with explicit phase exit criteria is the recommended pattern for implementations under 12 months.

---

## Anti-Patterns

1. **Treating NPC as a Managed Package** — Designing NPC architecture as if it were an App Exchange installed package (scoping "package updates," "namespace conflicts," "managed package upgrade testing") is incorrect and produces wasted effort. NPC is a native Industry Cloud with no managed package namespace. Architecture and governance patterns from NPSP do not apply.

2. **Deferring Person Account Strategy to Module Configuration** — Teams that start configuring Fundraising or Program Management without a documented Person Account strategy (record types, page layouts, deduplication rules, sharing model) consistently encounter constituent data integrity problems that require costly remediation. Person Account architecture is a prerequisite, not a parallel track.

3. **Scoping AI Agents Without Data Cloud** — Including Agentforce Nonprofit agents in scope without including Data Cloud licensing and architecture is a recurring NPC project risk. It produces agent configurations that cannot be meaningfully tested or activated until Data Cloud is retroactively provisioned — causing timeline delays and rework.

---

## Official Sources Used

- Nonprofit Cloud Developer Guide: Introduction to Nonprofit Cloud — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud_dev.meta/nonprofit_cloud_dev/npc_overview.htm
- Nonprofit Cloud Data Model Gallery — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud_dev.meta/nonprofit_cloud_dev/npc_data_model.htm
- Volunteer Management Data Model — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud_dev.meta/nonprofit_cloud_dev/npc_volunteer_management_data_model.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Nonprofit Cloud: Key Concepts — https://help.salesforce.com/s/articleView?id=sfdo.npc_key_concepts.htm
