# Well-Architected Notes — Requirements Gathering for Salesforce

## Relevant Pillars

- **Operational Excellence** — High-quality requirements directly reduce rework, failed UAT, and post-deployment defect costs. A fit-gap analysis that classifies requirements before build starts prevents the most common cause of project overruns: discovering integration or customization needs after implementation has begun. The Salesforce Well-Architected Framework calls out clear requirements and defined acceptance criteria as foundational to operational excellence.

- **User Experience** — Requirements gathered only from sponsors and managers (rather than end users) produce builds optimized for reporting, not for the people who use the system daily. The Well-Architected Framework emphasizes that easy-to-use systems are built from empathy with the actual user. Requirements gathering is where that empathy is captured or lost.

## Architectural Tradeoffs

**Discovery depth vs. delivery speed:** Thorough requirements gathering (interviews, process mapping, fit-gap) reduces downstream rework but adds time to the project start. The tradeoff depends on project complexity. For small enhancements to a stable org, a single interview and a short user story may be sufficient. For a multi-cloud implementation or a migration from a legacy system, skipping fit-gap analysis typically costs more in rework than the time saved in discovery. The Well-Architected approach favors upfront discovery for changes with broad scope or cross-team impact.

**Declarative vs. custom classification:** The fit-gap analysis forces this decision during requirements — not during implementation. Classifying requirements as "Standard," "Configuration," "Customization," or "Process Gap" before building ensures that custom development is a deliberate choice, not the path of least resistance. Standard and Configuration requirements should be exhausted before accepting Customization work. This is consistent with the Salesforce Well-Architected principle of preferring platform-native capabilities.

## Anti-Patterns

1. **Writing stories without Salesforce feature mapping** — User stories that describe outcomes without specifying which Salesforce feature delivers them ("users should be able to track follow-up") produce ambiguous acceptance criteria and mid-sprint scope discovery. Every story should name the Salesforce object, field, or automation feature that delivers it before the story is sprint-ready.

2. **Treating all requirements as equal effort** — A BA who presents a list of 50 requirements without fit classification leaves sprint sizing to guesswork. Mixing a standard-fit requirement (enable a feature toggle) with a customization-gap requirement (build a multi-step Flow with external callout) in the same sprint with the same estimate causes schedule failures. Fit-gap classification is what makes a backlog plannable.

3. **Skipping integration requirements as "out of scope"** — Requirements that depend on data from external systems (ERP, billing, HR) are sometimes deferred with the assumption that "we'll figure out the integration later." This pattern consistently causes mid-implementation blockers when it is discovered that key data needed for a Salesforce validation rule or workflow does not exist in the org. All external data dependencies must be captured as integration requirements at discovery time.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing, operational excellence and user experience pillars — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Certified Business Analyst Exam Guide — canonical BA role, exam domains (Stakeholder Collaboration 23%, Requirements 18%, User Stories 18%, Customer Discovery 17%, Business Process Mapping 12%, UAT/Dev Support 12%) — https://trailhead.salesforce.com/credentials/businessanalyst
- Trailhead: User Story Creation module — if/then acceptance criteria format, INVEST framework, user story structure — https://trailhead.salesforce.com/content/learn/modules/user-story-creation
- Trailhead: Business Process Mapping module — UPN notation, 8–10 box limit per level, As-Is/To-Be/Transition State methodology — https://trailhead.salesforce.com/content/learn/modules/business-process-mapping
- Trailhead: Explore Techniques for Information Discovery — BABOK-aligned elicitation, stakeholder discovery — https://trailhead.salesforce.com/content/learn/modules/business-analyst_skills-strategies/explore-techniques--information-discovery
- Salesforce Help: Field-Level Security — https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm
- Salesforce Help: Sharing Rules — https://help.salesforce.com/s/articleView?id=sf.security_about_sharing.htm
