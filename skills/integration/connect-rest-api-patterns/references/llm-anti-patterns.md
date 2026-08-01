# LLM Anti-Patterns — Connect REST API Patterns

Scope: choosing Connect REST API or the Apex `ConnectApi` namespace over raw SObject
access for Chatter feeds, CMS content and Experience Cloud. The Apex-side mechanics of
feed posting are covered in depth by `apex/apex-connect-api-chatter`; this file is about
when Connect is the right surface and what breaks when it is not.

## Anti-Pattern 1: Inserting FeedItem when the requirement mentions a mention

The single most common substitution. Asked to "post to the record feed and notify the
owner", assistants insert a `FeedItem` with the `@name` text in the body. The row is
created and the post renders — as plain text. There is no mention, no link, and crucially
no notification, so the requirement silently fails.

A mention is not a string. It is a structured message segment, and the feed's rich body
is a list of segments rather than a `Body` string. Only the Connect surface builds them.

**Wrong** — the text renders literally and notifies nobody:

```apex
FeedItem post = new FeedItem(
    ParentId = caseId,
    Body     = '@' + ownerName + ' this case has breached its SLA'
);
insert post;
```

**Right** — a mention segment, which resolves the user, renders as a link and notifies:

```apex
ConnectApi.MentionSegmentInput mention = new ConnectApi.MentionSegmentInput();
mention.id = ownerId;

ConnectApi.TextSegmentInput text = new ConnectApi.TextSegmentInput();
text.text = ' this case has breached its SLA';

ConnectApi.MessageBodyInput body = new ConnectApi.MessageBodyInput();
body.messageSegments = new List<ConnectApi.MessageSegmentInput>{ mention, text };

ConnectApi.FeedItemInput input = new ConnectApi.FeedItemInput();
input.body = body;
input.subjectId = caseId;
input.feedElementType = ConnectApi.FeedElementType.FeedItem;

ConnectApi.ChatterFeeds.postFeedElement(Network.getNetworkId(), input);
```

Source: ConnectApi namespace, ChatterFeeds —
https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/connectapi_namespace_overview.htm

## Anti-Pattern 2: Calling Connect REST over HTTP from inside Apex

Assistants generate an `Http` callout to `/services/data/vXX.0/connect/...` from Apex,
usually with a Named Credential pointing the org back at itself. It works, and it is the
wrong shape: it spends a callout, it consumes the org's API allocation, it cannot
participate in the transaction, and it forces you to hand-parse untyped JSON.

❌ `req.setEndpoint('callout:Self/services/data/v64.0/connect/feed-elements');`
✅ The `ConnectApi` namespace, which is the same capability in-process, strongly typed,
with no callout and no allocation cost. Reserve raw Connect REST for callers **outside**
the org.

## Anti-Pattern 3: Writing ConnectApi tests as if they were ordinary Apex tests

This is where generated code fails at deploy rather than at review. Most `ConnectApi`
methods read from Salesforce infrastructure that is not available inside a test
transaction, and calling them in a test throws rather than returning empty. Assistants
write the obvious `@IsTest` method, it fails, and the usual "fix" is to wrap it in a
try/catch that swallows the exception — leaving a test that asserts nothing.

❌ Call `ConnectApi.ChatterFeeds.getFeedElementsFromFeed(...)` in a test and catch
whatever comes out.
✅ Use the matching `setTest*` method to register the data the call should return, then
call the real method and assert on it. The naming is mechanical: for
`getFeedElementsFromFeed` there is a `setTestGetFeedElementsFromFeed` that takes the same
arguments plus the result to serve. If a method has no `setTest*` counterpart, it cannot
be unit-tested — isolate it behind an interface and mock that instead.

## Anti-Pattern 4: Omitting the network context

Every Connect call happens inside a community context, and assistants either omit the
parameter or pass `null` because the compiler accepts it. In an org with Experience Cloud
sites, the post then lands in the internal feed rather than the community the user is
actually in — and the defect is invisible to an internal admin, who sees the post exactly
where they expect.

❌ `ConnectApi.ChatterFeeds.postFeedElement(null, input);`
✅ Pass the network explicitly. `Network.getNetworkId()` returns the current context and
is null in the internal org, which is the correct value there — so passing it is right in
both cases, and hard-coding an Id is right in neither.

## Anti-Pattern 5: Paginating by computing offsets

Assistants apply the SOQL habit and build `LIMIT`/`OFFSET` arithmetic over feed elements.
Feeds are not a stable ordered result set — items arrive while you are reading — so
offsets skip and duplicate. Connect returns an opaque page token for this reason.

❌ Loop an incrementing offset until fewer than `pageSize` items come back.
✅ Follow `nextPageUrl` (REST) or `nextPageToken` (Apex) until it is null, and treat the
token as opaque. Do not parse it, cache it across sessions, or attempt to construct one.

## Anti-Pattern 6: Verifying as an administrator

Connect runs in the context of the current user and respects sharing, which is one of its
real advantages over hand-built SObject access. It also means an administrator sees
everything and therefore verifies nothing. Assistants generate the happy path and it
passes review because the reviewer is an admin.

❌ Test the community feed as a System Administrator and ship.
✅ Verify as a member of the actual audience — an Experience Cloud user with the licence
the real users hold. Permission gaps in Connect surface as empty collections rather than
exceptions, so an untested path looks like "no data" instead of "no access".

## Anti-Pattern 7: Posting to the feed from a trigger

Chatter posts generate notifications and feed-tracking side effects, so a post made from
a record-triggered context can fan out per record and, in the worst arrangement, feed back
into the automation that created it. Assistants place the call in the trigger because that
is where the record change is.

❌ `ConnectApi.ChatterFeeds.postFeedElement(...)` inside a `before`/`after` trigger for
each record in scope.
✅ Move the post to an asynchronous boundary — Queueable or a platform-event subscriber —
and aggregate. A bulk update of 5,000 records should produce one digest post or a bounded
batch, not 5,000 notifications.
