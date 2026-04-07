# Gotchas — Experience Cloud Moderation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Review-Status Content Is Hidden from Everyone Except the Author and Moderators

**What happens:** A member submits a post that matches a moderation rule with the Review action. The post is created in the platform but is not visible to any other community member. Only the original author (who sees their own post in their profile feed) and users with the Moderate Experiences Feeds permission can see it. The author cannot edit the held post while it is under review.

**When it occurs:** Any time a post or comment triggers a rule configured with the Review action. This surprises both community managers who expect to see all posts in the feed and members who submit a post and then see it appear to "disappear" from the community feed.

**How to avoid:** Communicate the Review workflow to moderators before launch. Confirm that all intended moderators have the Moderate Experiences Feeds permission; without it, they cannot see the held content. Customize the post-submission error or confirmation message so members understand their post is pending review, not lost.

---

## Gotcha 2: Reputation Points Are Not Retroactive

**What happens:** When reputation levels and point configurations are set up after a community has already been active, no points are awarded for historical member actions. Members who posted, commented, or received likes before reputation was enabled start at 0 points and Level 1, regardless of how long they have been active. This can cause long-standing members to be incorrectly throttled by Member Criteria rules that reference a minimum reputation level.

**When it occurs:** When reputation is configured after site launch, or when new point-earning actions are added to an existing reputation config. Retroactive credit is not applied in either case.

**How to avoid:** Configure reputation levels before site launch whenever possible. If enabling reputation on an active community, audit current member activity and consider manually adjusting point values upward for established members, or temporarily relaxing Member Criteria moderation rules until members have had time to earn points under the new system.

---

## Gotcha 3: Moderation Rules Fire in Order; First Match Wins

**What happens:** Salesforce evaluates moderation rules from top to bottom. The first rule whose criteria match the submitted content fires its action, and no further rules are evaluated for that content item. A Block rule placed below a Flag rule will never fire for content that already matches the Flag rule's criteria.

**When it occurs:** When admins add new rules without reviewing the full rule order, or when rules are copied and appended at the bottom of the list. A common failure mode is adding a strict Block rule for a critical keyword but seeing that content is still appearing live because a broader Flag rule higher in the list matched first.

**How to avoid:** After creating or editing any moderation rule, review the full ordered rule list in Setup. Place more restrictive rules (Block) above less restrictive rules (Flag, Review) whenever the same content might match both. Document the intended rule priority and review order as part of the moderation policy.

---

## Gotcha 4: Keyword Rules Match Partial Words

**What happens:** A keyword entered in a keyword list will match any word containing that string, not only the exact word. The keyword "ban" matches "banner", "abandoned", and "band". Overly short keywords cause unexpected false positives that block or flag legitimate content.

**When it occurs:** When keyword lists are built quickly without testing. Short words, common root words, or acronyms are the most frequent sources of false positives.

**How to avoid:** Test all keyword lists in a sandbox community before activating rules in production. Use multi-word phrases (e.g., "banned user" rather than "ban") where precision is required. Review flagged content in the queue after go-live to identify false positives and refine the keyword list.

---

## Gotcha 5: The Moderate Experiences Feeds Permission Is an Internal Org Permission, Not a Community Role

**What happens:** Admins assume that community moderator roles — such as a "Community Manager" role in the community — grant the ability to access the moderation queue. They do not. Moderator queue access requires the "Moderate Experiences Feeds" permission, which is a Salesforce platform permission assigned via profile or permission set in the internal org. External community members (Customer Community or Partner Community license users) cannot be granted this permission unless they also have an internal Salesforce user record.

**When it occurs:** When community managers are external partners or customers who are only provisioned with a community license. They can be given community manager roles with elevated content privileges, but they cannot access the moderation queue or approve Review-status content.

**How to avoid:** Ensure at least one internal Salesforce user (with a full or limited internal license) is assigned the Moderate Experiences Feeds permission and is accountable for the moderation queue. If the moderation team includes external users, provide them with internal user accounts with appropriate license types, or design an escalation path to internal moderators.
