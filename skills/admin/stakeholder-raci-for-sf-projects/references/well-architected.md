# Well-Architected Notes — Stakeholder RACI for Salesforce Projects

## Relevant Pillars

The Salesforce Well-Architected framework treats decision rights as part of `Operational Excellence` and overlaps with `Security` (who decides on access) and `Reliability` (who decides on change). A RACI tailored to a Salesforce project is a load-bearing artifact across all three.

- **Operational Excellence** — A RACI that encodes the canonical Salesforce decision categories with one accountable owner per category gives the org a deterministic decision-making surface. Salesforce Well-Architected's "Trusted" lens treats clear ownership and escalation as a precondition for change-management hygiene; without a versioned RACI, every change request becomes ad-hoc.
- **Security** — Security model decisions (OWD, role hierarchy, sharing rules, profiles, permission set groups, restriction rules, FLS, named credentials) are an explicit row in the RACI with the security architect as A. Compliance officer holds A on regulated-data rows. This routes security decisions to the role with the proximate authority instead of letting them default to "whoever is in the meeting."
- **Reliability** — Deployment decisions (what gets promoted, when, with what backout, through which sandboxes) carry the release manager as A. Without a named release manager, deploy decisions surface during a hot incident instead of during release planning. The CAB row in the matrix acts as the consulted body for high-blast-radius deploys per `admin/change-management-and-deployment`.

## Architectural Tradeoffs

- **Granularity vs. usability.** A RACI with one row per decision is precise but unreadable; a RACI with one row per category is readable but lossy. The pragmatic balance: one row per category, with sub-rows only where regulatory or org-strategy concerns force a split (e.g., "Data model — PHI" vs. "Data model — non-PHI" on a HIPAA project).
- **Single sponsor vs. steerco-as-A.** Naming a single sponsor as A on org-strategy decisions is faster but disenfranchises competing org owners on M&A and multi-BU projects. Steerco-as-A is slower but reflects the actual organizational state. Use the steerco pattern when more than one legal entity or business unit has a legitimate claim.
- **Internal A vs. partner A during build.** Partner-as-A is unavoidable while the SI owns the design. The tradeoff is the transfer date — bringing A in-house too early hands decisions to under-prepared internal staff; transferring too late leaves the customer dependent on the partner post-hypercare. The Well-Architected "Trusted" pillar treats unaddressed long-term dependencies as a reliability risk.

## Anti-Patterns

1. **Universal-sponsor A** — Putting the sponsor as A on every row collapses decision-making to a single bottleneck and erodes the meaning of A. Sponsor's A is scope/budget/license/go-no-go; operational A flows to the role with proximate domain expertise. Well-Architected `Operational Excellence` calls for distributed accountability, not centralized.
2. **Compliance-as-perpetual-C on regulated data** — Treating compliance as Consulted on rows that audit will care about is a Well-Architected `Trusted/Compliant` failure. Compliance must hold A on retention, audit trail, BAA, data subject rights, and PHI/PII access for HIPAA/FINRA/PCI/GDPR/SOX projects.
3. **Single "Architecture" column** — Collapsing security architect and integration architect into one role hides the fact that those decisions span domains. Well-Architected `Secure` and `Resilient` pillars treat them as distinct concerns; the matrix must, too.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Frames the four lenses (Trusted, Easy, Adaptable, Sustainable) the RACI must support.
- Salesforce Well-Architected — Trusted / Compliant — https://architect.salesforce.com/well-architected/trusted/compliant — Authoritative for the compliance officer's role on regulated data and the audit-trail / retention rows.
- Salesforce Well-Architected — Trusted / Secure — https://architect.salesforce.com/well-architected/trusted/secure — Authoritative for the security architect's A on the security-model row and the split between security and integration architecture.
- Salesforce Well-Architected — Adaptable / Resilient — https://architect.salesforce.com/well-architected/adaptable/resilient — Authoritative for release manager / CAB pattern on the deployment row.
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm — Reference for the data-model row's scope (standard vs. custom objects, fields, relationships).
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — Reference for what a deployment row covers (metadata types, packaging).
