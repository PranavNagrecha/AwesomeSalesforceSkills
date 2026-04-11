# Well-Architected Notes — AI Ethics and Governance Requirements

## Relevant Pillars

- **Security** — AI governance is inseparable from security. Access to AI audit logs, model configuration, and Einstein Trust Layer settings must be restricted to appropriate roles. Sensitive predictor fields used in Einstein models must be governed by field-level security so that model training does not expose data to unauthorized users. Audit trail records must have object-level and field-level security that prevents tampering.

- **Trust** — The Salesforce Well-Architected Trust pillar maps directly to the responsible AI framework. Every AI feature that is customer-facing must carry a disclosure. Every high-impact AI decision must have a demonstrable human oversight gate. Failure to implement these controls erodes trust with customers, regulators, and the business stakeholders sponsoring the AI initiative.

- **Reliability** — Human oversight gates introduce workflow dependencies. If an approval process created for AI governance is misconfigured or understaffed, it can block downstream business processes. Governance design must include SLAs for review turnaround and escalation paths when a reviewer is unavailable, so the oversight mechanism does not become a reliability failure.

- **Operational Excellence** — AI governance is an ongoing operational discipline, not a one-time deployment task. Governance documentation must have a defined review cadence (at minimum: after every model retrain, after every significant feature update, and annually for regulatory review). The governance process itself must be operationalized — assigned owners, calendar reminders, and a documented escalation path.

- **Performance** — Human oversight gates add latency to AI-driven workflows. For real-time use cases (live chat, real-time scoring), the governance design must account for the time cost of human review. Either the review is asynchronous (recommendation held until reviewed) or the use case is classified as low-risk and exempt from synchronous oversight. This is an explicit architectural tradeoff, not a default.

## Architectural Tradeoffs

**Oversight rigor vs. workflow throughput:** Synchronous human review gates provide the strongest accountability but can block time-sensitive workflows. Asynchronous review (log first, review later) maintains throughput but means AI-driven actions are already taken before a human sees them. Governance design must make this tradeoff explicit and document it in the risk inventory with legal sign-off.

**Centralized vs. distributed governance ownership:** A central AI Ethics function provides consistent policy interpretation but creates a bottleneck. Distributing governance ownership to business unit leads increases speed but creates policy drift. Mature orgs run a central policy function with distributed compliance reviewers who are trained and accountable to the central standard.

**Comprehensive logging vs. storage cost and complexity:** Logging every AI inference with full feature attribution provides maximum audit coverage but generates significant data volume. Governance must define minimum required log fields and a retention period calibrated to the applicable regulatory statute of limitations — not simply log everything forever.

## Anti-Patterns

1. **Governance as a pre-launch checklist only** — Treating AI governance as a one-time review before go-live, then never revisiting it. AI models retrain, regulations evolve, and new features get added. Governance that is not operationalized with review cadence and assigned owners becomes stale within one product cycle. Orgs that discover this only during an audit face emergency remediation under regulator scrutiny.

2. **Equating platform configuration with policy** — Documenting Trust Layer settings, toxicity score thresholds, and prompt template details as the AI governance deliverable. Platform configuration is evidence that controls exist; it is not a substitute for the policy document that explains why those controls exist, who owns them, what their scope is, and what happens when they fail.

3. **Bias evaluation on training data only, not on live prediction output** — Running the Einstein bias report on the training dataset before model activation, then never checking whether bias is expressed differently in the live prediction population. Training data bias and inference bias are related but distinct. Governance must include a periodic review of live prediction distributions across protected segments, not just training data statistics.

## Official Sources Used

- Salesforce Trailhead — AI Governance: Establishing Responsible Practices — https://trailhead.salesforce.com/content/learn/modules/ai-governance-establishing-responsible-practices
- Salesforce Trailhead — Trusted Agentic AI — https://trailhead.salesforce.com/content/learn/modules/trusted-agentic-ai
- Salesforce Help — Detect and Remove Bias from a Model — https://help.salesforce.com/s/articleView?id=sf.bi_edd_model_bias.htm
- Salesforce Help — Implement Data Governance Permissions for Audit — https://help.salesforce.com/s/articleView?id=sf.bi_edd_data_governance_perms.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Responsible AI Principles — https://www.salesforce.com/company/responsible-ai/
