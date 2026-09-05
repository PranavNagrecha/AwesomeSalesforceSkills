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
- Salesforce Certified Business Analyst Exam Guide — canonical BA role, exam domains (Stakeholder Collaboration 23%, Requirements 18%, User Stories 18%, Customer Discovery 17%, Business Process Mapping 12%, UAT/Dev Support 12%) — https://trailhead.salesforce.com/  (page retired — see host index for current equivalent)
- Trailhead: User Story Creation module — if/then acceptance criteria format, INVEST framework, user story structure — https://trailhead.salesforce.com/content/learn/modules/user-story-creation
- Trailhead: Business Process Mapping module — UPN notation, 8–10 box limit per level, As-Is/To-Be/Transition State methodology — https://trailhead.salesforce.com/content/learn/modules/business-process-mapping
- Trailhead: Explore Techniques for Information Discovery — BABOK-aligned elicitation, stakeholder discovery — https://trailhead.salesforce.com/content/learn/modules/business-analyst_skills-strategies/explore-techniques--information-discovery
- Salesforce Help: Field-Level Security — https://help.salesforce.com/s/articleView?id=sf.admin_fls.htm
- Salesforce Help: Custom Fields Allowed Per Object + Edition Allocations — https://help.salesforce.com/s/articleView?id=platform.custom_field_allocations.htm&type=5 — the allocation is per object, not per data type: Professional 100, Enterprise 500, Performance/Unlimited 800, Developer 500; "An org can't have more than 900 custom fields on most object types, regardless of the edition or source of those fields."
- Salesforce Help: Sharing Rules — https://help.salesforce.com/s/articleView?id=sf.security_about_sharing.htm

### Platform facts used to bound the NFR sheet

- **Salesforce Developer Limits and Allocations Quick Reference** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf — *Per-Transaction Apex Limits* (the 100/200 SOQL, 50,000 rows retrieved, 150 DML statements and 10,000 DML records that bound the record-volume NFR and Gotcha 4); *Bulk API and Bulk API 2.0 Limits and Allocations* (the 2,000-record line between bulkified synchronous calls and Bulk API 2.0, the 15,000 batches per rolling 24 h and the 150,000,000 records per 24 h that bound the data-movement NFR); *API Request Limits and Allocations* (the Enterprise Edition formula 100,000 + licences × calls per licence type + add-ons, and the per-licence-type table — Salesforce 1,000 in EE and 5,000 in UE/PE, Customer Community 0, Customer Community Login 0, Customer Community Plus 200, Partner Community 200, Partner Community Login 10 — which bound the integration and licence NFRs and Gotchas 8 and 9). Also the source for the absence of storage figures: the guide states up front that it does not cover contractual limits.
- **Metadata API Developer Guide, `ObjectRelationship`** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — "A maximum of four objects can be joined in a custom report type. When more than two objects are joined, an inner join isn't allowed if there has been an outer join earlier in the join sequence" (the reporting NFR row and Gotcha 7).
- **Data Loader Guide, Settings** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf — maximum import batch size of 200 records for SOAP API and 10,000 for Bulk API, with Bulk API 2.0 handling batch size automatically (the data-movement NFR row and Gotcha 4).
- **Apex Developer Guide, Testing Apex** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf — "Unit tests must cover at least 75% of your Apex code, and all of those tests must complete successfully" (the deployment-gate asymmetry that makes the automation tier a tree decision rather than a preference — Gotcha 5).

### Repo standards used

- **`standards/decision-trees/automation-selection.md`** — Q1–Q6 (record-change routing to before-save vs after-save Flow vs Apex), Q11 (external system → Salesforce), and the Cheat sheet row "Approval chain → Approval Process → Flow post-approval; never Apex custom approval". Cited by the catalogue's `decision_tree_step` column and by Gotcha 5.
- **`standards/decision-trees/sharing-selection.md`** — the 7-step sharing design sequence (OWD → Role Hierarchy → Sharing Rules → Teams → Manual/Apex → Restriction/Scoping → Implicit), Q2–Q3, and the "Experience Cloud sharing — a different world" section. Cited by the `sharing_layer` column, by the linter's allowed-layer set, and by Gotcha 6.
- **`standards/decision-trees/integration-pattern-selection.md`** — Direction 1 Q1–Q2 (callout shape and Named Credential auth) and Direction 2 Q5–Q6 (volume and latency routing to REST / Composite / Bulk API 2.0). Cited by the integration rows in `references/worked-examples.md` and by Gotcha 8.
- **`agents/story-drafter/AGENT.md`, `agents/fit-gap-analyzer/AGENT.md`, `agents/process-flow-mapper/AGENT.md`, `agents/config-workbook-author/AGENT.md`** — the Inputs tables of each (`discovery_artifact_kind`, `backlog_path` + mandatory `target_org_alias`, `process_narrative_path` + `process_kind`, and the workbook's org-profile probe). These define the shape the catalogue must be in to be consumable, and produce the handoff map in `references/worked-examples.md`.
- **`agents/_shared/AGENT_CONTRACT.md`** — the Citations requirement that every skill id, template path and decision-tree branch consulted must be cited. It is why `decision_tree_step` is a required column on any row naming a mechanism rather than an optional note.
