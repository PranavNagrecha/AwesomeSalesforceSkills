# Well-Architected Notes — Agentforce Sales AI Setup

## Relevant Pillars

- **Operational Excellence** — Einstein for Sales setup is a sequenced operational task with hard prerequisite dependencies. Skipping steps (e.g., enabling Pipeline Inspection before Collaborative Forecasting is active) produces a silently broken configuration that degrades rep trust in the platform. Operational excellence here means deterministic, checklist-driven setup with explicit gate checks before each feature is enabled.
- **Security** — License tier management is a security concern: the Einstein Generative AI license (required for email composition) gives the platform permission to pass Salesforce data to an LLM. Orgs should confirm their Einstein Trust Layer data masking and zero-data-retention policies apply before enabling generative AI email features for reps. Over-provisioning the Einstein Generative AI license to users who do not need email composition unnecessarily expands the data surface area.
- **User Experience** — The primary UX risk in Einstein for Sales setup is deploying features to reps before they are fully operational (e.g., enabling Opportunity Scoring before the model is Active, or enabling Pipeline Inspection AI insights before Collaborative Forecasting is enabled). Reps who see blank score fields or missing AI insights columns conclude the feature is broken. A phased, gate-driven rollout that only surfaces features to users after they are confirmed operational is the correct UX-first approach.

## Architectural Tradeoffs

**Feature sequencing vs. fast activation:** The temptation is to enable all Einstein for Sales features simultaneously to deliver value quickly. The correct architectural choice is sequential enablement with confirmation gates between each step. The cost of sequential enablement is 2–7 days of additional lead time. The cost of simultaneous enablement is features that silently fail, eroding rep trust and generating support escalations that take longer to resolve than the lead time saved.

**Sandbox vs. production validation:** Because Opportunity Scoring does not train in sandboxes, orgs that require full sandbox validation before production enablement must accept that score generation can only be validated post-production deployment. The architectural response is to separate the enablement validation (which can be done in sandbox) from the scoring validation (which requires production) and design UAT acceptance criteria accordingly.

**License procurement sequencing:** Organizations planning to offer generative email composition must procure the Einstein Generative AI add-on before beginning setup. Discovering the missing license mid-deployment stalls the project and creates a poor practitioner experience. License verification should be the first step of any Einstein for Sales setup, before any configuration work begins.

## Anti-Patterns

1. **Enable-all-at-once deployment** — Enabling all Einstein for Sales features (Opportunity Scoring, Pipeline Inspection, email composition) in a single Setup session without waiting for prerequisite gates is an anti-pattern. It produces a configuration where Pipeline Inspection AI insights never appear (because Opportunity Scoring model is still training) and email composition errors (if the generative AI license is missing). The correct pattern is sequential feature enablement with explicit wait states and status confirmations between steps.

2. **Sandbox score validation** — Expecting Opportunity Scoring to produce scores in a sandbox and marking the feature as defective when scores are absent is an anti-pattern. Sandboxes do not run the model training pipeline. Acceptance criteria for Opportunity Scoring must explicitly exclude score generation from sandbox validation scope and restrict it to production or a developer org with representative data.

3. **Conflating Einstein for Sales with Einstein Generative AI license tiers** — Assuming a single Einstein license covers all Einstein Sales features, including generative email composition, is an architectural anti-pattern in license planning. It produces a rollout plan that cannot deliver email composition without a mid-stream procurement change. License verification as a distinct pre-work step eliminates this risk.

## Official Sources Used

- Einstein for Sales Overview — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_overview.htm
- Einstein Opportunity Scoring — https://help.salesforce.com/s/articleView?id=sf.einstein_sales_oppty_scoring.htm
- Pipeline Inspection Guidelines and Limits — https://help.salesforce.com/s/articleView?id=sf.pipeline_inspection_guidelines_and_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
