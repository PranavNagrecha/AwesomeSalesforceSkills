# Well-Architected Notes — Experience Cloud Moderation

## Relevant Pillars

- **Security** — Moderation directly enforces the content security posture of a community. Mis-configured rules (wrong action type, wrong rule order, missing moderator permissions) allow prohibited or harmful content to reach members. The Review action in particular requires that the Moderate Experiences Feeds permission is assigned to the right internal users; a gap here means held content is never actioned and accumulates unseen in the queue.

- **Operational Excellence** — The moderation queue is an ongoing operational process, not a one-time configuration. A well-run moderation practice requires clear ownership (named moderators), a defined SLA for queue review, and regular keyword-list tuning. Launching without documented moderator responsibilities creates a queue that backs up and eventually surfaces ignored content to frustrated community managers.

- **Reliability** — Rule order determines which action fires. An out-of-order rule list is a latent reliability defect: the site appears to work, but a subset of content is handled incorrectly and the bug may not be noticed for weeks. Treat rule order as configuration code — review it as part of any change to moderation settings.

## Architectural Tradeoffs

**Automated rules vs. human moderation queue:** Automated keyword and member criteria rules reduce queue volume but introduce false positives. Block rules stop all matching content, including legitimate posts that happen to contain a flagged word. Striking the right balance requires starting with narrower rules (multi-word phrases, higher specificity) and expanding only when queue volume reveals uncaught content.

**Review (hold) vs. Flag (live):** Review provides higher content safety but increases moderator workload and delays member engagement. Flag reduces moderator load and keeps the community responsive but exposes potentially problematic content to all members until a moderator acts. The correct choice depends on the community's compliance requirements and moderation team capacity.

**Reputation gating vs. open posting:** Requiring reputation thresholds before relaxing moderation creates friction for new, legitimate members. Over-aggressive gating can suppress early community participation. Under-aggressive gating allows spam accounts to post freely. A common pattern is a short initial Review period (first 3–5 posts or first 7 days) rather than a permanent reputation gate.

## Anti-Patterns

1. **Configuring moderation rules without assigning moderator permissions** — Rules that trigger Review or Flag actions create queue entries that nobody can process. This is a silent failure: content is moderated (held or flagged) but the queue is never reviewed because no user has the Moderate Experiences Feeds permission. Always assign the permission as part of the same setup task as the rules.

2. **Setting up reputation after site launch without accounting for existing members** — Enables a reputation system that treats all existing members as brand-new (Level 1, 0 points). If Member Criteria rules tied to reputation are also active, long-standing members are suddenly throttled by review holds. This creates a support surge and erodes member trust. Configure reputation at launch or with a member migration plan.

3. **Using broad single-word keyword lists without sandbox testing** — Short keywords generate false positives that block legitimate content, frustrate members, and increase moderator queue load. The architectural anti-pattern is treating keyword lists as quick configuration rather than precision tooling that must be tested and refined iteratively.

## Official Sources Used

- Experience Cloud Site Moderation Strategies — help.salesforce.com (Experience Cloud admin documentation: moderation rules, keyword lists, action types, rule evaluation order)
- Set Up Reputation Levels/Points — help.salesforce.com (Experience Cloud reputation configuration, point actions, level thresholds)
- Connect REST API Developer Guide — developer.salesforce.com (Moderation REST resources: `/communities/communityId/chatter/feeds/moderation/`, audit statistics, feed flagging endpoints)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (architecture quality framing for security and operational excellence pillars)
