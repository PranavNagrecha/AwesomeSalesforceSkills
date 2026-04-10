# Well-Architected Notes — Agentforce Service AI Setup

## Relevant Pillars

- **Operational Excellence** — Einstein for Service setup is fundamentally an operational discipline problem. Enabling features without prerequisite assessment leads to poor adoption metrics, expensive rollback, and eroded confidence in AI investments. A phased activation sequence with explicit validation gates is the operational excellence pattern for this domain.
- **Security** — Generative AI features (Work Summaries, Service Replies) route conversation transcripts and case content through the Einstein Trust Layer before LLM processing. Ensuring the Trust Layer is properly configured — including data masking for PII and sensitive case content — is a security prerequisite for generative AI enablement. This skill's scope includes confirming the Trust Layer is active; detailed Trust Layer configuration belongs to the `einstein-trust-layer` skill.
- **Reliability** — Case Classification model quality directly affects operational reliability. A low-accuracy classification model produces incorrect field values that drive incorrect Omni-Channel routing, which creates reassignment overhead and SLA breaches. Verifying data thresholds before enablement is a reliability control — preventing a degraded model from entering production.
- **Performance** — Model training is asynchronous and can take 24–72 hours for initial training passes. Activation timelines must account for training latency. Features that depend on model training (Case Classification, Article Recommendations, Reply Recommendations) are not immediately available after enablement.

## Architectural Tradeoffs

**Suggestion mode vs. auto-populate mode for Case Classification:** Auto-populate mode maximizes efficiency (zero clicks for agents) but propagates classification errors silently — agents may not notice incorrect values, leading to bad data entering the pipeline and corrupting future model training. Suggestion mode adds one click but captures explicit agent corrections as training feedback, improving model accuracy over time. For initial deployments, suggestion mode is the architecturally safer choice: it validates model quality before allowing autonomous field population.

**Phased activation vs. big-bang enablement:** Enabling all Einstein for Service features simultaneously compresses the go-live timeline but makes it impossible to isolate issues during initial validation. A phased approach — predictive features first, generative features after license and channel prerequisites are independently confirmed — adds time but produces a more reliable and debuggable activation sequence.

**Data quality investment vs. feature deferral:** Enabling Case Classification with poor training data produces a feature that harms operations more than it helps. The correct tradeoff is to defer Case Classification until data quality meets the 1,000-case / 80%-completeness threshold, investing the intervening time in improving agent data entry habits, rather than enabling a low-accuracy model and managing the agent trust recovery that follows.

## Anti-Patterns

1. **License assumption without verification** — Assuming that purchasing Service Cloud Einstein includes all Einstein for Service features including generative AI. Work Summaries and Service Replies require Einstein Generative AI entitlement or Einstein 1 Service, which is a separately purchased license tier. Always verify provisioned entitlements in Setup > Company Information before beginning any Einstein for Service enablement project.

2. **Enabling all features on day one without data readiness assessment** — Activating Case Classification, Article Recommendations, and Reply Recommendations simultaneously without first assessing closed case volume, field completeness, Knowledge base quality, and messaging transcript volume. Each feature has different data prerequisites; enabling them before prerequisites are met produces features that appear broken and undermines AI adoption.

3. **Treating Einstein for Service as a one-time configuration task** — Einstein for Service features — particularly Case Classification and Article Recommendations — improve over time through agent behavior (consistently accepting or correcting suggestions, linking articles to cases). Treating the initial enablement as the endpoint, rather than the starting point for ongoing model feedback, produces stagnating or degrading feature quality over the months following go-live.

## Official Sources Used

- Einstein for Service overview — https://help.salesforce.com/s/articleView?id=sf.einstein_service.htm
- Einstein Case Classification — https://help.salesforce.com/s/articleView?id=sf.einstein_case_classification.htm
- Einstein Article Recommendations — https://help.salesforce.com/s/articleView?id=sf.einstein_article_recommendations.htm
- Einstein Reply Recommendations — https://help.salesforce.com/s/articleView?id=sf.einstein_reply_recommendations.htm
- Einstein Work Summary — https://help.salesforce.com/s/articleView?id=sf.einstein_work_summary.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Einstein for Service Setup Guide — https://help.salesforce.com/s/articleView?id=sf.einstein_service_setup.htm
