# Well-Architected Notes — AI Adoption Change Management

## Relevant Pillars

- **Trusted** — This is the primary pillar for AI adoption change management. The Salesforce Well-Architected Trusted pillar explicitly addresses building and maintaining confidence in AI system behavior, including transparency about how AI models make decisions and ensuring users can understand and audit AI outputs. The black-box trust problem is a direct Trusted-pillar concern: when users cannot explain why an AI made a recommendation, they cannot trust the system or take accountability for decisions influenced by it. The Feedback API is the canonical Trusted-pillar mechanism for ongoing trust signal collection post-deployment.

- **Adaptable** — AI features evolve significantly across Salesforce releases. An adoption plan built around Spring '25 Agentforce capabilities must accommodate model updates, new action types, and UI changes in subsequent releases. The LEVERS model's Ecosystem lever (champions and community of practice) provides the organizational infrastructure to absorb these changes without requiring a full re-launch each time. Training content must be designed for update, not for permanence.

- **Operational Excellence** — The Agentforce Analytics Data 360 adoption measurement dashboard represents the operational excellence instrumentation layer. Without defined metrics, review cadence, and owners, the AI deployment has no feedback loop. The 90-day post-launch review cadence with named owners is the operational excellence commitment for this domain.

- **Security** — Relevant specifically for trust communication: users must be clearly informed about what data the AI model can and cannot access, what personal or customer data the AI uses, and how AI-generated outputs are governed before they reach external parties. Security concerns surface when users mistakenly believe the AI has access to data it does not (inflating trust inappropriately) or when AI-generated content is sent to customers without human review in contexts where that is a compliance risk.

## Architectural Tradeoffs

**Phased rollout vs. big-bang launch:** A phased rollout with a pilot cohort and promotion gate is slower but produces a significantly lower risk of negative sentiment spreading org-wide before model quality issues are resolved. The tradeoff is time-to-value: a big-bang launch with a well-prepared organization (all six LEVERS at active status) can succeed, but requires a level of organizational readiness that is rarely achieved. Default to phased unless executive mandate and full LEVERS readiness are both confirmed.

**Structured feedback collection vs. qualitative only:** The Feedback API provides structured, quantifiable signal (thumbs ratio, reason text categories) at the cost of UI real estate and user training on what "thumbs down" means. Qualitative-only approaches (manager observations, open-ended surveys) produce richer context but are not scalable and do not feed model refinement. Both are needed: Feedback API for scale signal, qualitative sessions for root cause depth.

**Broad vs. role-specific training:** Generic AI training is cheaper to produce but produces lower adoption because it does not address role-specific trust concerns. A sales rep's AI trust questions differ fundamentally from a service agent's. Role-specific training requires more content production but produces measurably better adoption outcomes. Invest in role specificity at the Enablement layer.

## Anti-Patterns

1. **Standard CRM Rollout Playbook Applied to AI** — Applying a go-live email, click-path training, and hypercare without any AI-specific trust, transparency, or feedback instrumentation. This fails because the psychological barriers to AI adoption (job anxiety, black-box distrust) are categorically different from barriers to adopting a new CRM field or layout. The LEVERS model exists precisely because generic change management frameworks are insufficient for AI.

2. **Deployment Without Pre-Launch Adoption Metrics** — Deploying Agentforce to production without configuring Agentforce Analytics Data 360 dashboards and defining baseline and target metrics before go-live. This leaves the adoption team without a signal to distinguish success from silent non-use, and makes it impossible to detect model quality problems via Feedback API rejection patterns.

3. **Feedback API Enabled but Never Reviewed** — Instrumenting the Feedback API on AI surfaces as a technical deployment step but not establishing a named owner and review cadence for the feedback data. The feedback data exists but is invisible and unactioned. This is the most common failure mode in post-launch Agentforce programs — the data exists in the platform but no one is reading it.

## Official Sources Used

- Change Management for AI Implementation (Trailhead module) — LEVERS model, 10x success statistic, AI-specific change management framework
  URL: https://trailhead.salesforce.com/content/learn/modules/change-management-for-ai-implementation/unite-ai-and-change-management

- Empower Your Workforce with AI Strategies (Trailhead module) — Worker empowerment, trust-building communication, transparency requirements
  URL: https://trailhead.salesforce.com/content/learn/modules/change-management-for-ai-implementation/support-and-empower-workers-in-the-ai-age

- Agent Development Lifecycle (Salesforce Architects) — Agentforce deployment lifecycle, Feedback API role in post-deployment signal collection, adoption measurement
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/agent-development-lifecycle

- Salesforce Well-Architected Overview — Trusted, Adaptable, and Operational Excellence pillar framing for AI adoption
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
