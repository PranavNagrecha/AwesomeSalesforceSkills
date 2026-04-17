# Examples — Connect REST API Patterns

## Example 1: Post feed item with mention

**Context:** Notify record owner

**Problem:** Raw FeedItem insert doesn't render @mentions

**Solution:**

`ConnectApi.ChatterFeeds.postFeedElement(communityId, FeedItem, FeedElementType.FeedItem, ...)` with message segments

**Why it works:** Renders @mention correctly with notification


---

## Example 2: CMS content publish

**Context:** Publish a Knowledge article

**Problem:** SObject approach misses workflow

**Solution:**

Connect API `/connect/cms/contents/{id}/publish`

**Why it works:** Runs the full publish pipeline

