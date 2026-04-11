# Well-Architected Notes — AI Use Case Assessment

## Relevant Pillars

- **Trust and Security** — AI use case assessment is fundamentally a trust exercise. Poorly assessed use cases that activate AI on unready data or for high-risk autonomous decisions erode business trust in the platform. The assessment must include a Risk Profile dimension specifically to surface use cases with potential for harmful or biased outputs, ensuring human oversight is built into the approved design before implementation begins. Data governance scoring directly supports data privacy and regulatory compliance.
- **Operational Excellence** — The assessment establishes the operational baseline that all subsequent AI work is measured against. Structured scoring, documented assumptions, and a clear prioritized shortlist reduce ad-hoc decision-making during implementation. The recommended workflow enforces a repeatable process that can be audited and improved across multiple AI initiative cycles.
- **Reliability** — Assessing data readiness rigorously before implementation prevents the most common reliability failure: AI models trained on insufficient or low-quality data that produce outputs with no predictive validity. A use case that fails the data readiness gate at assessment time is far less expensive than one that fails in production after go-live.
- **Performance** — For use cases involving real-time AI inference (e.g., next-best-action recommendations surfaced in a Lightning page), the assessment should flag latency expectations and whether the underlying data retrieval pattern (synchronous API call vs. Data Cloud pre-computed scores) is compatible with the target user experience.
- **Scalability** — Impact-Effort scoring should account for whether a use case scales with org growth. A feature that works well at 10,000 records but requires re-training every month as data volume grows has a different ongoing effort profile than a rule-based automation.

## Architectural Tradeoffs

**Breadth vs. depth in the initial assessment:** Running a full four-dimension feasibility analysis on twenty use cases produces comprehensive coverage but requires significant stakeholder time and can delay momentum. Running a lightweight Impact-Effort pass on all use cases and a deep feasibility analysis only on the top quadrant is faster but risks missing a blocking constraint in a use case that looked easy. The recommended pattern is: lightweight scoring for all, full feasibility for Quick Wins and Big Bets only.

**Consensus scoring vs. expert scoring:** Stakeholder workshops produce buy-in and surface business context that technical assessors miss, but they also inflate impact scores for politically favored use cases and underestimate effort for technically complex ones. Expert-only scoring is more calibrated but produces less organizational commitment. Best practice: combine both — expert pre-scoring followed by stakeholder calibration with explicit outlier discussion.

**Assessment cadence:** AI use case assessments have a shelf life. A use case blocked by data readiness in Q1 may be unblocked after a Data Cloud implementation in Q3. Treat the assessment as a living document with a scheduled review cycle (recommended: every 6 months for active AI programs), not a one-time deliverable.

## Anti-Patterns

1. **Conflating assessment with implementation scoping** — Running the use case assessment and immediately producing sprint plans, developer assignments, or feature configuration specifications in the same session. Assessment outputs are a prioritized shortlist and feasibility scorecard; they feed an implementation project intake process. When implementation scoping starts before the shortlist is signed off, the boundary between assessment and implementation collapses, and blocked use cases consume implementation capacity before the gate check is completed.

2. **Treating data readiness as a binary yes/no** — Marking a use case as data-ready if any relevant records exist, without sub-dimension scoring of quality, unification, and governance. This is the single most common cause of AI feature activations that produce no business value — the data exists but is too noisy or incomplete for the model to learn valid patterns. Data readiness must be scored at the sub-dimension level per the framework.

3. **Skipping the Risk Profile dimension for autonomous decision use cases** — Assessing an AI use case that involves automated outbound communication, credit decisions, or pricing adjustments purely on Technical and Data Readiness dimensions without scoring the Risk Profile. High-risk autonomous decisions require human-in-the-loop design from the start; retrofitting oversight controls into an already-implemented feature is significantly more expensive and may require rearchitecting the entire flow.

## Official Sources Used

- Trailhead: Identifying Effective AI Use Cases for Business — https://trailhead.salesforce.com/content/learn/modules/ai-strategy/identify-ai-use-cases
- Salesforce Agentforce Use Cases — https://www.salesforce.com/agentforce/
- Salesforce Blog: 5 Ways to Measure Data Readiness for AI — https://www.salesforce.com/blog/data-readiness-for-ai/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce AI Acceptable Use Policy — https://www.salesforce.com/company/legal/ai-acceptable-use-policy/
- Einstein for Service Setup Guide — https://help.salesforce.com/s/articleView?id=sf.einstein_for_service_setup.htm
