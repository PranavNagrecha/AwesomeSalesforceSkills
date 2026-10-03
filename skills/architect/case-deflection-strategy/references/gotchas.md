# Gotchas — Case Deflection Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names the source it rests on. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: An Abandoned Bot Session Looks Like Containment

**What happens:** A customer stops replying and the bot session closes on its idle timeout. No transfer happened, so any metric defined as "sessions without a transfer" counts it as contained. Teams report that number as deflection and overstate the program.

**When it occurs:** When the KPI framework uses containment alone. UNVERIFIED (2026-10-03): that standard Einstein Bot analytics label a timed-out session as contained could not be confirmed from a fetched source; test it in your org before relying on either reading.

**How to avoid:** Define goals on the bot version and mark the dialog step that proves the goal was met, so goal completion is recorded by the platform rather than inferred from the absence of a transfer. Report goal completion rate as the quality KPI and containment as an efficiency KPI. Set the bot's idle timeout deliberately so "abandoned" has a known definition.

**Source:** Metadata API Developer Guide v67.0, BotVersion: `conversationGoals` (API 57.0+) and BotStep type `GoalStep`; Bot: `sessionTimeout`, "the maximum amount of minutes that a bot session can be idle" (API 58.0+).

---

## Gotcha 2: Einstein Conversation Mining Sees Only Conversation Transcripts

**What happens:** The topic list produced by Einstein Conversation Mining reflects the chat and messaging slice of volume. In an email-heavy org the top email reasons look minor or absent, and the deflection roadmap targets the wrong topics.

**When it occurs:** When the mining report is the only topic source for an org whose dominant Case Origin is Email or Web. UNVERIFIED (2026-10-03): the exact data sources Conversation Mining reads, and the often-quoted 90-day transcript minimum, are documented only in Salesforce Help, which does not fetch.

**How to avoid:** Pull the Case Origin and Case Reason distribution first (query in `references/examples.md`). Use mining output for the conversational channels and case text analysis for email and web. Confirm the feature is on before planning around it: it is the `enableConversationMining` setting.

**Source:** Metadata API Developer Guide v67.0, ConversationalIntelligenceSettings: `enableConversationMining`, "Indicates whether Einstein Conversation Mining is enabled" (API 61.0+). Object Reference v67.0, Case: `Origin` ("The source of the case, such as Email, Phone, or Web") and `Reason` are filterable and groupable picklists.

---

## Gotcha 3: Data Category Visibility Is Broad, And The Real Trap Is The Multi-Group Rule

**What happens:** Teams expect visibility to flow only downward, so they re-tag articles at every level. The documented behavior is broader. Making a category visible makes its whole family line visible: ancestors, parent, children, and descendants. The failure that actually hides articles is different. An article classified in two category groups is visible only if the user can see at least one category in each group. A guest profile that can see `Products > Router` but has no visibility in the `Region` group never sees an article tagged `Router` and `EMEA`.

**When it occurs:** When a second category group (region, audience, product line) is added after launch and only internal roles get visibility to it. Users with no visibility in a group see only articles not classified in that group.

**How to avoid:** For every category group, set visibility for the guest profile, the authenticated customer profile or permission set, and partner roles before launch. Test one article per group combination as each audience. Keep the number of category groups on customer-facing articles small.

**Source:** Salesforce Knowledge Implementation Guide (Summer '26), Data Category Visibility: "Setting a category as visible makes that category and its entire directly related family line—ancestors, immediate parent, primary children, other descendants—visible to users"; "Categorized Article Visibility: User's can see an article if they can see at least one category per category group on the article"; Revoked Visibility. This corrects the earlier "inheritance is downward only" statement in this skill.

---

## Gotcha 4: The Right Category With The Wrong Channel Still Hides The Article

**What happens:** An article is published, correctly categorized, and visible to the guest profile, but it never appears on the site. Its channel flags exclude the customer or public channel.

**When it occurs:** When authors publish from the internal app with the default channel selection, or when an import file omits the channel column and the article lands in the internal app only.

**How to avoid:** Add the channel flags to the knowledge readiness audit: `IsVisibleInPkb` for the public knowledge base, `IsVisibleInCsp` for customers, `IsVisibleInPrm` for partners, `IsVisibleInApp` for agents. On import, set the `Channels` column explicitly. When channels change, align translations before publishing, because a translation whose channels differ blocks the publish.

**Source:** Object Reference v67.0, KnowledgeArticleVersion: `IsVisibleInApp`, `IsVisibleInCsp`, `IsVisibleInPkb`, `IsVisibleInPrm`. Knowledge Implementation Guide (Summer '26), import "Channels" keyword ("application for Internal App. If you don't specify a channel, application is the default"; `sites`, `csp`, `prm` for the other channels) and translation publishing: "You can't change channels on an article translation and then publish the article. Doing so generates an error."

---

## Gotcha 5: Bot Article Answers Depend On The Context The Bot Runs In

**What happens:** Knowledge answers look complete when an admin tests the bot, then guests on the live site get no results. The bot searches what its running context can see, not every published article.

**When it occurs:** When testing happens in Setup or the builder preview instead of through the deployed site as a guest. UNVERIFIED (2026-10-03): that the builder test harness runs with admin visibility and that Einstein Article Recommendations inherit the embedding site's category visibility are stated in Salesforce Help only.

**How to avoid:** Test knowledge answers through the deployed channel as each audience. Assign a dialog to the `KnowledgeFallback` system event so a no-result search ends in a designed path, not a dead end.

**Source:** Metadata API Developer Guide v67.0, BotVersion: `knowledgeActionEnabled`; ConversationSystemDialog types `KnowledgeAction` (API 60.0) and `KnowledgeFallback` (API 51.0).

---

## Gotcha 6: Three Teams, Three Deflection Rates

**What happens:** The bot team reports sessions without transfer, the portal team reports sessions without a case, and the service director reports the drop in case creation. Leadership compares the three numbers as if they measured the same thing.

**When it occurs:** When the program spans bot, portal, and knowledge teams and the formula was never written down.

**How to avoid:** Write the formula into the KPI framework before launch, name its numerator and denominator objects, and report per topic. UNVERIFIED (2026-10-03): the widely quoted "27% average deflection rate" attributed to Salesforce could not be traced to a fetched Salesforce source; do not use it as a target.

**Source:** Practice guidance; no platform behavior is claimed beyond the objects named in `references/examples.md`.

---

## Gotcha 7: High-Volume Portal Users Have No Role, So Role Visibility Never Reaches Them

**What happens:** Category visibility is configured on customer roles, and portal users on high-volume licences still see no categorized articles.

**When it occurs:** When the customer population uses high-volume portal licences, which carry no role. Role-based visibility settings cannot apply to users without a role.

**How to avoid:** Grant category visibility to high-volume users through their profile or a permission set. Remember that role, permission set, and profile visibility combine with a logical OR, and that a child role can reduce but never exceed its parent's visibility.

**Source:** Knowledge Implementation Guide (Summer '26), Role-Based Visibility Setting Inheritance: "Because high-volume portal users don't have roles, you must designate visibility settings by permission set or profile before these users can view categorized articles and questions"; note on logical OR between role, permission set, and profile definitions.

---

## Gotcha 8: Article View Counts Are Not Resolutions

**What happens:** The program reports rising article views as deflection. Views measure reach. A customer can read three articles and still open a case.

**When it occurs:** When `KnowledgeArticleViewStat` is the only self-service metric. It counts unique views per channel for published and archived articles; draft views are not tracked, and the normalized score weights recent views more heavily.

**How to avoid:** Pair view statistics with a resolution signal: a "did this answer your question" vote, a case-creation check after an article session, or a bot goal step. Use `CaseArticle` to see which articles agents attach, which shows the articles customers needed but did not find.

**Source:** Object Reference v67.0, KnowledgeArticleViewStat: "The view count statistics are for published and archived articles only. View counts for draft articles aren't tracked"; `ViewCount` is unique views; `NormalizedScore` weighting; `Channel` values `AllChannels`, `App`, `Pkb`, `Csp`, `Prm`. CaseArticle: "Represents the association between a Case and a KnowledgeArticle."
