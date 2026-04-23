# Apex Connect Api Chatter — Work Template

Use this template when assembling a Chatter post via `ConnectApi`.

## Scope

**Skill:** `apex-connect-api-chatter`

**Request summary:** (what is being posted, to which feed, and why)

## Post Composition

- [ ] Plain text only
- [ ] Text + @mention
- [ ] Text + link
- [ ] Text + file attachment (`BinaryInput`)
- [ ] Poll
- [ ] Announcement

## Context Gathered

- **Feed parent:** (User Id / Group Id / Record Id / 'me')
- **Parent object feed tracking enabled?** (yes / no — required)
- **Execution context:** (sync / trigger / Queueable / @future)
- **Experience Cloud?** (yes — need `Network.getNetworkId()`)
- **Chatter enabled in all target orgs?** (yes / no — feature-flag if no)
- **Expected failure mode:** (log and continue / propagate)

## Approach

- [ ] Assemble `FeedItemInput` with correct segments
- [ ] Pass `Network.getNetworkId()` explicitly
- [ ] Wrap in `try/catch (ConnectApi.ConnectApiException)`
- [ ] Bulk: move to Queueable if posting > 5 items

## Code Sketch

```apex
public static void postToFeed(Id parentId, Id mentionedUserId, String message) {
    ConnectApi.FeedItemInput input = new ConnectApi.FeedItemInput();
    input.subjectId = parentId;

    ConnectApi.MessageBodyInput body = new ConnectApi.MessageBodyInput();
    body.messageSegments = new List<ConnectApi.MessageSegmentInput>();

    if (mentionedUserId != null) {
        ConnectApi.MentionSegmentInput m = new ConnectApi.MentionSegmentInput();
        m.id = mentionedUserId;
        body.messageSegments.add(m);
    }

    ConnectApi.TextSegmentInput t = new ConnectApi.TextSegmentInput();
    t.text = (mentionedUserId != null ? ' ' : '') + message;
    body.messageSegments.add(t);

    input.body = body;

    try {
        ConnectApi.ChatterFeeds.postFeedElement(Network.getNetworkId(), input);
    } catch (ConnectApi.ConnectApiException e) {
        System.debug(LoggingLevel.ERROR, 'Feed post failed: ' + e.getMessage());
    }
}
```

## Test Setup

- [ ] `Test.setMock(ConnectApi.ConnectApi.class, new MockConnectApi())`
- [ ] Mock captures the `FeedItemInput` for assertion
- [ ] Test asserts presence of mention segment when expected
- [ ] Test covers the Chatter-disabled (ConnectApiException) path

## Checklist

- [ ] No literal `'@'` in `FeedItem.Body` DML anywhere.
- [ ] `Network.getNetworkId()` used, not a hardcoded `0DB...` literal.
- [ ] `try/catch` around every `ConnectApi` call.
- [ ] No `SeeAllData=true` near ConnectApi tests.
- [ ] Bulk posts go through Queueable, not per-record in trigger.

## Notes

Any edge cases (Experience Cloud nuance, feed-tracking gaps, attachment-size limits).
