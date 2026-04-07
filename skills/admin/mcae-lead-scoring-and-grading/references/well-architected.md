# Well-Architected Notes — MCAE Lead Scoring and Grading

## Relevant Pillars

- **Operational Excellence** — The core challenge in this skill. A scoring and grading model must be explainable, auditable, and maintainable. Point values and threshold decisions should be documented so any admin can understand the current model, reproduce the MQL definition, and modify it without breaking the downstream handoff. Decay rules and profile criteria need to be reviewed periodically as ICPs evolve. Automation rule activation procedures need runbooks to prevent retroactive queue floods.

- **Reliability** — The MQL pipeline must fire predictably. Automation rules need repeat/reset logic that is explicitly designed, not left at a default that causes stale MQLs or prevents re-qualification. The scoring field sync must be validated end-to-end so that CRM-visible score and grade always match MCAE's current values. Monitoring for manual override accumulation prevents scoring from silently breaking for individual prospects.

- **Security** — Score and Grade fields on Lead/Contact should be protected from non-MCAE writes via field-level security. Preventing CRM users from manually editing Score or Grade on the CRM side avoids divergence. Marketing admin roles in MCAE should follow least privilege — not every marketing user needs to edit scoring rules or profiles. MCAE admin access should be audited periodically.

- **Performance** — Large automation rules that evaluate the full prospect database in real-time can put load on the MCAE processing queue. Overly broad rules (no criteria other than a score threshold) on a database of millions of prospects may produce delays in action execution. Scoping rules with additional criteria (e.g., list membership, date ranges) reduces the evaluation footprint.

- **Scalability** — Scoring models need to scale gracefully as the prospect database grows. Decay rules that remove stale score weight prevent the database from becoming cluttered with high-score cold prospects. Profile criteria that are too broad (matching most of the database) produce meaningless grades at scale — keep profiles narrow and discriminating.

## Architectural Tradeoffs

**Sensitivity vs. Specificity in the MQL Threshold:** A low score threshold produces more MQLs (higher sensitivity) but more noise for Sales. A high threshold reduces volume but may miss borderline prospects. The grade gate adds a second discriminator. The tradeoff between sales coverage and precision must be agreed with Sales leadership, not set by Marketing alone.

**Single MQL Rule vs. Segment-Specific Rules:** A single automation rule with one score+grade threshold is simpler to maintain but treats all segments equally. Segment-specific rules (one per ICP profile or product line) allow different thresholds but multiply maintenance burden. For most orgs, start with one rule and add segmentation only after the pipeline shows systematic false positives from a specific segment.

**Decay Aggressiveness vs. Long Sales Cycles:** Heavy score decay (large reductions, short periods) is appropriate for high-velocity SMB sales cycles. For enterprise deals with 6-12 month cycles, aggressive decay would constantly recycle legitimate long-term prospects. Calibrate decay period to the expected sales cycle length.

**Automation Rules vs. Engagement Studio:** For simple threshold routing, Automation Rules are the right tool. Engagement Studio (drip programs) is appropriate for time-based nurture sequences. Do not use Engagement Studio to implement the primary MQL routing logic — it adds unnecessary complexity and the branching behavior is harder to audit.

## Anti-Patterns

1. **Single-Dimension MQL (Score Only)** — Building an MQL threshold purely on score without a grade gate produces a lead queue full of high-activity, low-fit prospects (competitors, students, tire-kickers who clicked many emails). This erodes Sales' trust in the MQL list and leads to SDRs ignoring the queue. Always gate MQL routing on both score AND grade.

2. **No Decay Rules on a Long-Running Instance** — MCAE instances that have been running for 2+ years without score decay accumulate large numbers of stale MQL-eligible prospects. When a new campaign activates, the automation rule retroactively routes all of these stale high-scorers to Sales at once. Decay rules are not retroactive — they only prevent future accumulation. Implement decay early. If decay is being added to an existing high-score database, plan a one-time score reset campaign before activating decay.

3. **Overlapping Profile Criteria Without a Default Profile** — Creating multiple profiles with overlapping industry or title criteria and not designating a default profile causes unpredictable grade assignment. Prospects may be graded against the wrong ICP, producing inaccurate grades that mislead Sales. Always: (a) keep profile criteria non-overlapping on the primary discriminating field, (b) designate one profile as the default catch-all.

## Official Sources Used

- Salesforce Help — Default Scoring System — https://help.salesforce.com/s/articleView?id=sf.pardot_scoring_default.htm
- Salesforce Help — Customize Scoring Rules — https://help.salesforce.com/s/articleView?id=sf.pardot_admin_scoring_overview.htm
- Salesforce Help — Using Profiles to Grade Prospects — https://help.salesforce.com/s/articleView?id=sf.pardot_profiles_overview.htm
- Salesforce Help — Guidelines for Grading — https://help.salesforce.com/s/articleView?id=sf.pardot_profiles_guidelines.htm
- Salesforce Help — Automation Rules — https://help.salesforce.com/s/articleView?id=sf.pardot_automation_rules.htm
- Salesforce Help — Completion Actions — https://help.salesforce.com/s/articleView?id=sf.pardot_completion_actions.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
