# Well-Architected Notes — In-App Guidance and Walkthroughs

## Relevant Pillars

- **Operational Excellence** — In-App Guidance is fundamentally an operational excellence tool. It reduces support load, improves process adherence, and accelerates feature adoption without requiring live training. Well-designed prompts are part of a deliberate org maintenance and change adoption practice. The risk is operational debt: stale prompts that reference removed UI elements or outdated processes erode user trust in the system.

- **Reliability** — Targeted prompts have a silent failure mode (anchor element removed). A reliable guidance implementation requires an audit process tied to the release and deployment lifecycle to catch broken prompts before users encounter the absence of expected guidance.

- **Security** — In-App Guidance content is visible to all users matching the audience profile. Avoid including any sensitive data, internal system details, PII, or security-relevant instructions inside prompt copy. Prompt content is stored in Salesforce metadata and is accessible to admins with the "Manage Prompts" permission.

- **Performance** — Page-load delay settings prevent prompts from competing with initial page render. Setting a 2–3 second delay is a low-cost operational excellence practice that reduces premature dismissal rates.

- **Scalability** — The 3-slot active walkthrough limit on the free tier is a hard constraint that does not scale with org complexity. Orgs with broad adoption programs (multiple products, many teams, high-churn onboarding needs) will hit this ceiling quickly. Architectural planning should account for the Sales Enablement license cost as a programmatic scaling decision, not a per-walkthrough decision.

## Architectural Tradeoffs

**Targeted prompts vs. floating prompts:** Targeted prompts provide the highest user comprehension for specific UI actions but create a maintenance dependency on page layout stability. Floating prompts are maintenance-free but lower-signal. In orgs with frequent layout changes, a floating-heavy approach reduces operational risk at the cost of some guidance precision.

**Free tier vs. Sales Enablement:** The 3-slot limit forces prioritization. This is not purely a budget decision — it is an architectural discipline that prevents prompt sprawl. Orgs that upgrade to Sales Enablement without a governance model often end up with dozens of overlapping prompts degrading user experience. The free tier's constraint enforces a deliberate "highest value first" approach.

**In-App Guidance vs. custom LWC onboarding:** For highly conditional or behavioral-trigger scenarios (e.g., "show only to users who have logged a call in the past 30 days"), custom LWC components or Flow-based solutions provide flexibility that In-App Guidance cannot. The trade-off is implementation and maintenance cost. In-App Guidance is the correct first choice for any scenario that fits within its targeting model.

## Anti-Patterns

1. **Creating new walkthroughs without deactivating stale ones** — Orgs accumulate walkthroughs over time. Without a periodic audit and deactivation process, the 3-slot cap becomes a blocker precisely when a high-priority adoption campaign needs a new walkthrough. Governance practice: review all active walkthroughs at the start of each release cycle and deactivate any that are past their intended window.

2. **Anchoring targeted prompts to frequently-changed UI elements** — Fields added to page layouts via seasonal releases, admin customization, or managed package updates are at risk of removal without notice. Anchoring targeted prompts to frequently-changed elements (e.g., a field added by a managed package) creates a brittle guidance implementation. Prefer floating prompts for content that is expected to persist beyond a single release cycle, and reserve targeted prompts for stable, long-lived UI elements.

3. **Using In-App Guidance as a substitute for change management** — Prompts are a reinforcement tool, not a replacement for stakeholder communication, training documentation, and rollout planning. An org that relies on a single walkthrough to drive adoption of a significant process change without any other communication will see poor outcomes. In-App Guidance should augment a change management program, not replace it.

## Official Sources Used

- Salesforce Help: In-App Guidance Overview — https://help.salesforce.com/s/articleView?id=sf.customhelp_lex_prompt_parent.htm
- Salesforce Help: Types of In-App Guidance — https://help.salesforce.com/s/articleView?id=sf.customhelp_lex_prompt_types.htm
- Salesforce Help: Considerations for Creating In-App Guidance — https://help.salesforce.com/s/articleView?id=sf.customhelp_lex_prompt_considerations.htm
- Salesforce Help: Limits for In-App Guidance — https://help.salesforce.com/s/articleView?id=sf.customhelp_lex_prompt_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
