# Examples — Connect REST API Patterns

## Example 1: Post a feed item that actually mentions the record owner

**Context:** when a Case breaches its SLA, the owner should be notified in the record
feed.

**Problem:** the first implementation inserted a `FeedItem` whose `Body` contained
`'@' + owner.Name`. The post appeared, so the change passed review — but the mention
rendered as literal text, resolved to no user and generated no notification. The
requirement had failed silently, and it stayed failed for a quarter because the post was
visibly there.

**Solution:** build the body from message segments through `ConnectApi`, and do it away
from the trigger so a bulk update cannot fan out.

```apex
public with sharing class SlaBreachNotifier implements Queueable {

    private final List<Id> caseIds;

    public SlaBreachNotifier(List<Id> caseIds) { this.caseIds = caseIds; }

    public void execute(QueueableContext ctx) {
        List<Case> cases = [
            SELECT Id, CaseNumber, OwnerId, Owner.Type
            FROM Case
            WHERE Id IN :caseIds
            WITH USER_MODE
        ];

        Id networkId = Network.getNetworkId();   // null in the internal org, which is correct

        for (Case c : cases) {
            if (c.Owner.Type != 'User') { continue; }   // a queue cannot be mentioned

            ConnectApi.MentionSegmentInput mention = new ConnectApi.MentionSegmentInput();
            mention.id = c.OwnerId;

            ConnectApi.TextSegmentInput text = new ConnectApi.TextSegmentInput();
            text.text = ' Case ' + c.CaseNumber + ' has breached its SLA and needs an update.';

            ConnectApi.MessageBodyInput body = new ConnectApi.MessageBodyInput();
            body.messageSegments =
                new List<ConnectApi.MessageSegmentInput>{ mention, text };

            ConnectApi.FeedItemInput input = new ConnectApi.FeedItemInput();
            input.body = body;
            input.subjectId = c.Id;
            input.feedElementType = ConnectApi.FeedElementType.FeedItem;

            ConnectApi.ChatterFeeds.postFeedElement(networkId, input);
        }
    }
}
```

**Why it works:** a mention is a `MentionSegmentInput` carrying a user Id, not an `@`
character in a string — which is why the SObject route cannot produce one no matter how
the body is formatted. Passing `Network.getNetworkId()` rather than `null` makes the same
code correct in the internal org and inside an Experience Cloud site. Skipping
queue-owned cases matters because a queue has no user to notify, and the alternative is
an exception mid-loop that abandons the rest of the batch. Running from a Queueable keeps
a 5,000-record bulk update from producing 5,000 notifications inside the triggering
transaction.

---

## Example 2: Reading a feed from an external client, with correct pagination

**Context:** an external portal renders a community feed. The team's first client
computed `LIMIT`/`OFFSET` over the results, and users reported posts appearing twice and
others vanishing.

**Problem:** a feed is not a stable ordered result set. New elements arrive between
requests, so an offset computed against page 1 no longer points at the same place by page
2. Connect returns an opaque page token precisely because offsets cannot be correct here.

**Solution:** follow `nextPageUrl` until it is null, and treat the token as opaque.

Connect REST is the right surface for an external client: the caller is outside the org,
so the `ConnectApi` Apex namespace is not available to it.

```javascript
async function readCommunityFeed(instanceUrl, accessToken, communityId) {
  const elements = [];
  let next =
    `/services/data/v64.0/connect/communities/${communityId}` +
    `/chatter/feeds/company/feed-elements?pageSize=25`;

  while (next) {
    const res = await fetch(`${instanceUrl}${next}`, {
      headers: { Authorization: `Bearer ${accessToken}` }
    });

    if (res.status === 401) throw new Error('token expired; refresh and retry');
    if (!res.ok) {
      const [err] = await res.json();
      throw new Error(`Connect ${res.status} ${err?.errorCode}: ${err?.message}`);
    }

    const page = await res.json();
    elements.push(...page.elements);

    // Opaque cursor. Never parse it, never rebuild it, never cache it across sessions.
    next = page.nextPageUrl;

    if (elements.length > 500) break;   // bound the walk; feeds are unbounded
  }
  return elements;
}
```

**Why it works:** the cursor is positional relative to the feed's own ordering rather than
to a numeric index, so concurrent posts shift neither the page boundary nor the caller's
place in it. The `nextPageUrl` value arrives already path-qualified, which is why it is
concatenated to `instanceUrl` rather than to the resource path.

Two things worth noting about this surface. The response is verbose — each element
carries actor, body segments, capabilities and preamble — so request only the page size
you will render, and expect payloads far larger than the equivalent `FeedItem` query.
And because Connect runs as the authenticated user and respects sharing, a permission gap
returns an empty `elements` array rather than an error: verify against a real community
member, because an integration user with broad access will never reproduce it.
