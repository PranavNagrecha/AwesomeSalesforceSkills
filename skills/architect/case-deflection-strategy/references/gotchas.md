# Gotchas — Case Deflection Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Bot Session Timeout Counts as Containment, Not Deflection

**What happens:** When a bot session times out because the customer stopped responding, the session is marked as "contained" (no agent transfer occurred) in standard Einstein Bot analytics. Teams report containment rate as their deflection KPI and show inflated numbers. In reality, a timed-out session means the customer gave up, not that they were deflected.

**When it occurs:** Any time a bot deployment uses containment rate as a proxy for deflection rate and does not separately track goal completion rate. Common in first-generation bot programs where KPIs were not defined before launch.

**How to avoid:** Always track goal completion rate (GCR) alongside containment rate. Use bot session end surveys or post-session CSAT to distinguish between resolved sessions and abandoned sessions. Report GCR as the primary quality KPI and containment rate as a secondary efficiency metric.

---

## Gotcha 2: Einstein Conversation Mining Does Not Analyze Email-to-Case or Web-to-Case

**What happens:** ECM analyzes Messaging and Chat transcripts. It does not process Email-to-Case message bodies or Web-to-Case subject/description fields. Orgs that receive the majority of their contact volume via email will see a sparse or misleading ECM topic list because the tool is analyzing only the chat subset of their volume.

**When it occurs:** When the ECM report is used to prioritize deflection topics for an org where email is the dominant channel. The report will make high-email-volume topics appear low-priority because they are rarely discussed in chat.

**How to avoid:** Supplement ECM with a case report analysis: export Case Subject or Description text and use keyword frequency or a simple text clustering approach to identify topic distribution across all channels before setting the deflection roadmap.

---

## Gotcha 3: Data Category Inheritance Is Downward Only

**What happens:** Assigning a user profile or Experience Cloud channel access to a parent data category does NOT make articles assigned exclusively to child categories visible. Conversely, granting access to a child category does not surface articles assigned only to the parent. Each article must be assigned to the appropriate level, and visibility grants must match.

**When it occurs:** When the knowledge team assigns all articles to a top-level data category for convenience, then sub-teams create child categories and assign new articles there without re-assigning the old articles. Guest user profiles that were set up against the parent category can no longer see new child-category articles.

**How to avoid:** Audit data category assignments end-to-end before launching any deflection channel. Test as a guest user (not an admin) with the Experience Cloud site preview. Confirm that a test article assigned to each child category is visible via search and direct URL on the target channel.

---

## Gotcha 4: Einstein Article Recommendations in Bots Use Channel-Scoped Visibility

**What happens:** When a bot uses Einstein Article Recommendations to return articles during a conversation, it searches only the articles visible to the Experience Cloud site context the bot is embedded in — not all published articles in the org. This means articles that are published and visible in Setup but not assigned to the correct data categories for the guest user profile on that specific site will never be returned by the bot.

**When it occurs:** When bot article search is tested in the agent desktop or Setup test environment (where the tester is an authenticated admin) and shows correct results, but guest users on the public-facing site get "no articles found." The admin sees all articles; the guest user sees only articles with matching data category visibility grants.

**How to avoid:** Always test bot article search using the Experience Cloud site preview in guest user mode, not in the bot builder test harness. The test harness runs as the admin context and bypasses data category visibility rules.

---

## Gotcha 5: Deflection Rate Calculation Varies — Align on a Definition Before Reporting

**What happens:** Deflection rate has at least three common interpretations: (1) percentage of bot sessions with no agent transfer, (2) percentage of all inbound contacts (across all channels) resolved in self-service, (3) percentage reduction in case creation over a baseline period. Each definition produces a different number, and stakeholders often compare incompatible figures.

**When it occurs:** When the deflection program spans multiple teams (bot team, portal team, knowledge team) each reporting their own deflection metric to leadership without a shared definition.

**How to avoid:** Define the deflection rate formula in writing before launch and include it in the KPI framework document. The Salesforce-cited 27% industry average refers to bot-specific deflection (sessions where no agent transfer occurred and customer completed goal), not org-wide contact volume reduction.
