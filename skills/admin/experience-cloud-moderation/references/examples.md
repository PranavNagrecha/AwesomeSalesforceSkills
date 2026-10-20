# Examples — Experience Cloud Moderation

Cites are to the Winter '27 (264) `api_meta`, `object_reference` and `apexdev` guides.

## Example 1: Keyword Block Rule for Prohibited Terms

**Context:** A B2B partner community receives posts containing competitor product names that violate community guidelines. Compliance requires that these terms never appear in any feed post or comment.

**Problem:** A Flag rule would leave the content live (UNVERIFIED 2026-10-20: Flag visibility is Help-only), and a Replace rule does not run when a review rule also applies (api_meta 264 L92228-92229). Block runs before review, replace and flag rules (L92226-92227) and shows the member a message.

**Solution:** A keyword list and a Block rule, shaped on the guide's samples (api_meta 264 L84971-84990, L92344-92384). Files are named `site_name.developer_name` with suffixes `.keywords` and `.rule` in the `moderation` folder (L84937-84938, L92233-92234).

`moderation/Partner.competitor_terms.keywords`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<KeywordList xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Competitor Terms</masterLabel>
    <description>Competitor names that violate community guidelines</description>
    <keywords>
        <keyword>CompetitorA</keyword>
    </keywords>
    <keywords>
        <keyword>CompetitorB product</keyword>
    </keywords>
</KeywordList>
```

`moderation/Partner.block_competitor_mentions.rule`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ModerationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Block Competitor Mentions</masterLabel>
    <description>Blocks competitor terms in feed posts and comments</description>
    <action>Block</action>
    <active>true</active>
    <userMessage>You can't use %BLOCKED_KEYWORD% in this site. Review your content and try again.</userMessage>
    <entitiesAndFields>
        <entityName>FeedItem</entityName>
        <fieldName>RawBody</fieldName>
        <keywordList>Partner.competitor_terms</keywordList>
    </entitiesAndFields>
    <entitiesAndFields>
        <entityName>FeedComment</entityName>
        <fieldName>RawCommentBody</fieldName>
        <keywordList>Partner.competitor_terms</keywordList>
    </entitiesAndFields>
</ModerationRule>
```

Why it works: `RawBody` and `RawCommentBody` are the fields that moderate feed posts and comments (api_meta 264 L92302-92306); `%BLOCKED_KEYWORD%` shows up to five blocked words in the message (L92283-92285). Matching ignores capitalization and trailing punctuation, and wildcards are not supported (L84926-84927, L84967). No rule-ordering step is needed for Block.

UNVERIFIED (2026-10-20): the Setup UI screens for building the same list and rule are Help-only; the `<keywords><keyword>` nesting follows the guide's sample (api_meta 264 L84977-84982).

---

## Example 2: Reputation Levels and Points in the Network Metadata

**Context:** A customer community wants levels that reflect sustained participation.

**Problem:** Reputation is part of the site's `Network` metadata, with its own point events (api_meta 264 L93597-93603, L93766-93770), so the points table has to use the documented events and not invented actions such as logging in.

**Solution:** An excerpt of the `Network` file (only the reputation elements are shown; the rest of the file is unchanged), using the field names from L94359-94448:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: reputation elements of Network metadata; keep the rest of the file as retrieved -->
<Network xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableReputation>true</enableReputation>
    <reputationLevels>
        <level>
            <label>New Member</label>
            <lowerThreshold>0</lowerThreshold>
        </level>
        <level>
            <label>Contributor</label>
            <lowerThreshold>100</lowerThreshold>
        </level>
        <level>
            <label>Trusted Member</label>
            <lowerThreshold>500</lowerThreshold>
        </level>
    </reputationLevels>
    <reputationPointsRules>
        <pointsRule>
            <eventType>FeedItemWriteAPost</eventType>
            <points>1</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemReceiveALike</eventType>
            <points>5</points>
        </pointsRule>
        <pointsRule>
            <eventType>FeedItemYourAnswerMarkedBest</eventType>
            <points>20</points>
        </pointsRule>
    </reputationPointsRules>
</Network>
```

If `enableReputation` is on and no levels or rules are defined, the default values are used (api_meta 264 L93599-93603). `lowerThreshold` is the lower value of the range; the platform calculates the upper value (L94360, L94384-94387). Each rule's `eventType` and `points` are Required (L94412, L94431), and the available events are the 16 listed at L94414-94429. The defaults, such as +1 for a post and +5 for receiving a like, are at L94433-94448.

UNVERIFIED (2026-10-20): using a reputation level as Member Criteria in a moderation rule (earlier versions of this example created a "Reputation Level is below Level 2" Review rule), and the claim that points are not retroactive, are Help-only; the corpus names only `userCriteria` as a string (L92271-92272).

---

## Anti-Pattern: Using Flag Instead of Review for New Member Throttling

**What practitioners do:** Create a new-member rule with the Flag action, expecting new member posts to be held for approval.

**What goes wrong:** The documented hold is the `PendingReview` status that Review produces: visible to the author and to users who see the item and have View All Data or Can Approve Feed Post and Comment (object_reference 264 L136986-136990). UNVERIFIED (2026-10-20): that Flag leaves the post immediately visible to all members is Help-only.

**Correct approach:** Use Review when the requirement is "content must not be visible until approved", and document which scenarios use each action in the moderation policy.
