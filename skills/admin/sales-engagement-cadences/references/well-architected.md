# Well-Architected Notes — Sales Engagement Cadences

## Relevant Pillars

- **User Experience** — Cadences exist entirely to support rep productivity. A poorly designed cadence (too many steps, wrong step types, missing templates) degrades the Work Queue experience directly. Step naming, call script quality, and email template content all affect whether reps adopt the tool or work around it.

- **Operational Excellence** — Cadence governance is an ongoing operational concern. Without active management, orgs accumulate inactive cadences, stale templates, and enrolled-but-paused prospects that consume tracker limits. Operational excellence requires a defined cadence lifecycle: create, activate, monitor, retire.

- **Scalability** — The org-wide active target cap (500,000) and active tracker limit (150,000) are hard platform constraints. Designs that enroll prospects without a completion or exit strategy will approach these limits at scale. Any cadence architecture for a high-volume team must account for limit monitoring and prospect lifecycle management.

- **Reliability** — Silent failures (email steps skipping on blank email, LinkedIn steps failing without Sales Navigator) make the cadence appear unreliable from the rep's perspective even when the platform is functioning correctly. Reliability here is mostly about configuration correctness and data quality rather than system uptime.

- **Security** — Permission set assignment gates all cadence functionality. Over-provisioning (assigning Sales Engagement Manager to all reps) gives reps the ability to create, edit, and deactivate cadences, which creates governance risk. Under-provisioning blocks Work Queue access entirely. Permission set design must match role responsibility.

## Architectural Tradeoffs

**Branching complexity vs. maintainability:** Cadences with multiple branching tracks for every signal type are more precise but harder to maintain. For most orgs, a two-track model (main + positive) is sufficient and materially easier to understand and update than a full three-track design. Add the negative track only when email bounce handling is a documented business requirement.

**Template sharing vs. isolation:** Sharing email templates across cadences reduces template sprawl but creates coupling — a copy change affects all cadences using that template. For teams running A/B tests or different messaging for different segments, template isolation (one template per cadence context) is the correct tradeoff despite the duplication overhead.

**Enrollment automation vs. manual enrollment:** Auto-enrolling leads via Flow on Lead create is efficient but requires mature data quality practices. If leads are created with incomplete email fields, auto-enrollment triggers silent email-step skips at scale. Manual enrollment or a pre-enrollment validation step is safer until data quality is confirmed.

## Anti-Patterns

1. **One cadence for all rep roles and segments** — Building a single cadence intended for SDRs, AEs, and re-engagement all at once creates step sequences that are too long and too generic. Every distinct outreach motion (cold outbound, warm inbound, re-engagement, post-meeting follow-up) should be a separate cadence with targeted steps and templates.

2. **Never retiring or archiving completed cadences** — Leaving old cadences active with no enrolled prospects still contributes to limit monitoring confusion. Deactivate cadences that are no longer in use and document the reason. Establish a quarterly cadence review cycle to retire stale sequences.

3. **Using Sales Engagement for marketing-volume outreach** — Sales Engagement is designed for rep-driven, personalized outreach at a scale of hundreds to low thousands of prospects per rep. Using it to enroll tens of thousands of records for broadcast-style outreach risks hitting org limits rapidly and degrades the Work Queue signal for reps doing real pipeline work.

## Official Sources Used

- Salesforce Sales Engagement Implementation Guide (Spring '26) — https://help.salesforce.com/s/articleView?id=sf.sales_engagement_implementation_guide.htm
- Salesforce Help: Cadence Considerations — https://help.salesforce.com/s/articleView?id=sf.sales_cadence_considerations.htm
- Trailhead: Standard Cadences for Sales Engagement — https://trailhead.salesforce.com/content/learn/modules/sales-engagement-for-admins
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
