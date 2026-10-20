# Well-Architected Notes — Experience Cloud Moderation

## Relevant Pillars

- **Security** — Moderation directly enforces the content security posture of a community. Mis-configured rules (wrong action type, wrong rule order, missing moderator permissions) allow prohibited or harmful content to reach members. The Review action in particular requires that Can Approve Feed Post and Comment (or Modify All Data) and Moderate Experiences Feeds are assigned to the right people (object_reference 264 L136986-136990; apexdev 264 L25687-25688); a gap here means held content is never actioned. UNVERIFIED (2026-10-20): that it "accumulates unseen in the queue" is Help-only.

- **Operational Excellence** — The moderation queue is an ongoing operational process, not a one-time configuration. A well-run moderation practice requires clear ownership (named moderators), a defined SLA for queue review, and regular keyword-list tuning. Launching without documented moderator responsibilities creates a queue that backs up and eventually surfaces ignored content to frustrated community managers.

- **Reliability** — Action precedence determines which rule fires (block, then review, then replace, then flag; the oldest rule runs first among equals; api_meta 264 L92226-92229). A misread precedence is a latent reliability defect: the site appears to work, but a subset of content is handled incorrectly. Treat the rule set as configuration code and review it as part of any change to moderation settings.

## Architectural Tradeoffs

**Automated rules vs. human moderation queue:** Automated keyword and member criteria rules reduce queue volume but introduce false positives. Block rules stop all matching content, including legitimate posts that happen to contain a listed word. Striking the right balance requires starting with narrower rules (multi-word phrases, higher specificity) and expanding only when queue volume reveals uncaught content.

**Review (hold) vs. Flag:** Review provides higher content safety (the item is `PendingReview`, object_reference 264 L136986-136990) but increases moderator workload and delays member engagement. Flag reduces moderator load; UNVERIFIED (2026-10-20): that it keeps the item live for all members until a moderator acts is Help-only. The correct choice depends on the community's compliance requirements and moderation team capacity.

**Reputation gating vs. open posting:** Requiring reputation thresholds before relaxing moderation creates friction for new, legitimate members. Over-aggressive gating can suppress early community participation. Under-aggressive gating allows spam accounts to post freely. A common pattern is a short initial Review period (first 3–5 posts or first 7 days) rather than a permanent reputation gate.

## Anti-Patterns

1. **Configuring moderation rules without assigning moderator permissions** — Rules that trigger Review or Flag actions create items that nobody can process if no user holds Moderate Experiences Feeds (Moderation feed) or Can Approve Feed Post and Comment (publishing held items). Assign the permissions as part of the same setup task as the rules.

2. **Setting up reputation after site launch without accounting for existing members** — UNVERIFIED (2026-10-20): that points are not retroactive, so all existing members start at Level 1, is Help-only. If Member Criteria rules tied to reputation are active, test with a prior-activity account in a sandbox before launch.

3. **Using broad single-word keyword lists without sandbox testing** — Short keywords can generate false positives (UNVERIFIED 2026-10-20: substring matching is not stated in the corpus) that block legitimate content and increase moderator load. Treat keyword lists as precision tooling that is tested and refined iteratively.

## Official Sources Used

- ModerationRule — api_meta 264 L92203-92384 (action precedence L92226-92229, limits L92218-92219, fields L92246-92308, sample L92344-92384)
- KeywordList — api_meta 264 L84916-84990 (limits and matching L84924-84927, fields L84950-84967)
- Reputation in Network — api_meta 264 L93597-93603, L93766-93770, L94345-94448 (levels, point events and defaults)
- Pending-review feed items and comments — object_reference 264 L136366-136379, L136982-136999, L4345-4348; Moderation feed — apexdev 264 L25687-25688; flags — object_reference 264 L190960-190961, L191019-191022
- Experience Cloud Site Moderation Strategies — help.salesforce.com (UNVERIFIED (2026-10-20): Help-only; the source for the Setup UI paths, Replace behaviour, Flag visibility and non-retroactive reputation)
- Connect REST API Developer Guide — Moderation REST resources `/communities/communityId/chatter/feeds/moderation/` (UNVERIFIED (2026-10-20): the endpoint path is not in the corpus)
- Salesforce Help — Assign a Moderator: https://help.salesforce.com/s/articleView?id=experience.networks_moderator_assign.htm&type=5 (UNVERIFIED (2026-10-20): Help-only; the only source for the metadata API name `ModerateNetworkFeeds`)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (architecture quality framing for security and operational excellence pillars)
