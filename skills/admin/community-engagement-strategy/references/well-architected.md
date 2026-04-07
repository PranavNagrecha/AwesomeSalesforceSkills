# Well-Architected Notes — Community Engagement Strategy

## Relevant Pillars

- **Adaptable** — The engagement model must be designed to evolve. Reputation tiers and point thresholds should be revisited as community behavior matures. IdeaThemes should be scoped to release cycles, not left open-ended, so the feedback pipeline can be adapted per planning period.
- **Operational Excellence** — Content ownership maps, status review cadences, and member onboarding paths are operational disciplines, not one-time configurations. Without these, a technically correct community setup degrades in quality over time. The engagement model is only as durable as the operational processes behind it.
- **Trusted** — Reputation levels and idea status workflows are trust mechanisms. Members trust the community when they can see that their contributions are recognized (reputation display) and that their feedback is acted on (idea status updates). Breaking either signal damages member trust in ways that are difficult to reverse.

## Architectural Tradeoffs

**Reputation depth vs. simplicity:** A 10-tier system creates a fine-grained progression path that keeps experienced members engaged longer. However, it requires ongoing calibration — point thresholds that feel aspirational at launch may become trivially achievable as the member base grows and average activity increases. Plan for a 6-month threshold review.

**Ideation breadth vs. focus:** Creating many IdeaThemes allows granular feedback collection but dilutes vote density — if 500 ideas are spread across 20 themes, few ideas accumulate the vote signal needed for confident product prioritization. Prefer fewer, broader themes early and split them as volume warrants.

**Open contribution vs. quality control:** Granting all members contribution rights maximizes content volume but requires moderation investment. Restricting contribution to vetted member roles reduces volume but improves average quality. Choose based on the community's staffing model for moderation; do not design for a moderation investment you cannot sustain.

## Anti-Patterns

1. **Launching Reputation without meaningful tier names** — Using "Level 1" through "Level 10" or similar generic labels fails to communicate community identity or member standing. It also removes the social incentive that makes reputation visible to peers. Tier names should reflect the community's domain and signal something meaningful to members who see them on another member's profile.

2. **Enabling Ideation without a defined status workflow and named owners** — An ideation feature with no status movement communicates to members that feedback is not read. This is worse than no ideation feature at all, because it actively creates a negative signal. Every IdeaTheme must have a named owner and a committed review cadence before it is opened to members.

3. **Treating content ownership as a post-launch concern** — Content that has no owner ages out. Assigning ownership after launch is harder because the community sponsor's attention has shifted to adoption and moderation. Ownership must be a pre-launch deliverable.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing (Trusted/Adaptable/Easy pillars)
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Enable Reputation — Salesforce Help (Experience Cloud site reputation configuration)
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_reputation_setup.htm
- Encourage Idea Creation — Salesforce Help (Ideas feature setup and IdeaTheme configuration)
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_ideas.htm
- Trailhead: Optimize Community Engagement with Reputation Levels
  URL: https://trailhead.salesforce.com/content/learn/modules/community_mgmt/community_mgmt_reputation
- Trailhead: Experience Cloud Site Strategy
  URL: https://trailhead.salesforce.com/content/learn/modules/experience-cloud-site-strategy
