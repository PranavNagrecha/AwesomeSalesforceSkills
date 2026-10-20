# Examples — Apex Connect Api Chatter

## Example 1: Trigger-Sourced Owner @Mention On Case Escalation

**Context:** When a Case is escalated, the Case's owner should be @mentioned in the Case feed with a message explaining why.

**Problem:** Developers post a `FeedItem` with `Body = '@' + ownerName + ' case escalated'` and wonder why the owner never gets a notification. `FeedItem` DML renders the `@` as literal text — it does not produce a mention.

**Solution:**

```apex
public with sharing class EscalationFeedService {
    public static void postEscalationMention(Id caseId, Id ownerId, String reason) {
        ConnectApi.FeedItemInput input = new ConnectApi.FeedItemInput();
        ConnectApi.MessageBodyInput body = new ConnectApi.MessageBodyInput();
        body.messageSegments = new List<ConnectApi.MessageSegmentInput>();

        ConnectApi.MentionSegmentInput mention = new ConnectApi.MentionSegmentInput();
        mention.id = ownerId;
        body.messageSegments.add(mention);

        ConnectApi.TextSegmentInput text = new ConnectApi.TextSegmentInput();
        text.text = ' — case escalated. Reason: ' + reason;
        body.messageSegments.add(text);

        input.body = body;
        input.subjectId = caseId;

        try {
            ConnectApi.ChatterFeeds.postFeedElement(Network.getNetworkId(), input);
        } catch (ConnectApi.ConnectApiException e) {
            System.debug(LoggingLevel.ERROR, 'Feed post failed: ' + e.getMessage());
        }
    }
}
```

**Why it works:** `MentionSegmentInput` produces a real mention with a notification bell on the owner's side. `Network.getNetworkId()` scopes the post to the current community context so it appears correctly for Experience Cloud users.

---

## Example 2: Posting A Generated PDF To A Record Feed

**Context:** A weekly report is generated as a PDF Blob and needs to be attached to a specific Account feed with a short message.

**Solution:**

```apex
public static void postReportToAccount(Id accountId, Blob pdfBlob, String fileName) {
    ConnectApi.FeedItemInput input = new ConnectApi.FeedItemInput();
    ConnectApi.MessageBodyInput body = new ConnectApi.MessageBodyInput();
    ConnectApi.TextSegmentInput text = new ConnectApi.TextSegmentInput();
    text.text = 'Weekly report attached.';
    body.messageSegments = new List<ConnectApi.MessageSegmentInput>{ text };
    input.body = body;
    input.subjectId = accountId;

    input.capabilities = new ConnectApi.FeedElementCapabilitiesInput();
    input.capabilities.content = new ConnectApi.ContentCapabilityInput();
    input.capabilities.content.title = fileName;

    ConnectApi.BinaryInput binary = new ConnectApi.BinaryInput(
        pdfBlob, 'application/pdf', fileName);

    ConnectApi.ChatterFeeds.postFeedElement(
        Network.getNetworkId(), input, binary);
}
```

**Why it works:** `FeedElementCapabilitiesInput.content` attaches the file. The resulting post shows a preview in the feed and automatically creates a ContentVersion in the process.

---

## Example 3: Unit Testing A ConnectApi Call

**Context:** You need to test code that calls `ConnectApi.ChatterFeeds.postFeedElement`. Most Connect in Apex methods fail in tests unless the method is marked `@IsTest(SeeAllData=true)`; a few need their output registered with a `setTest*` method, as each method's Usage section states (Apex Developer Guide 264 L26331-26335). There is no documented `Test.setMock` mock for ConnectApi.

**Solution:** split the service so payload assembly is a separate method (`buildEscalationInput`, returning the `FeedItemInput` that Example 1 builds inline), test that in isolation, and keep one `SeeAllData=true` test for the real post.

```apex
@IsTest
private class EscalationFeedServiceTest {
    @IsTest
    static void buildsMentionSegment() {
        Id caseId = '500000000000001'; // 15-char Case Id; no DML needed
        Id ownerId = UserInfo.getUserId();

        ConnectApi.FeedItemInput input =
            EscalationFeedService.buildEscalationInput(caseId, ownerId, 'SLA breach');

        Boolean hasMention = false;
        for (ConnectApi.MessageSegmentInput seg : input.body.messageSegments) {
            if (seg instanceof ConnectApi.MentionSegmentInput) hasMention = true;
        }
        Assert.isTrue(hasMention, 'Post missing mention segment');
        Assert.areEqual(caseId, input.subjectId);
    }

    @IsTest(SeeAllData=true)
    static void postsToCaseFeed() {
        Case c = new Case(Subject = 'Test');
        insert c;

        Test.startTest();
        EscalationFeedService.postEscalationMention(c.Id, UserInfo.getUserId(), 'SLA breach');
        Test.stopTest();

        Assert.areEqual(1, [SELECT COUNT() FROM FeedItem WHERE ParentId = :c.Id]);
    }
}
```

**Why it works:** the isolated test needs no Chatter call, so it runs without org data and asserts the mention was assembled. The `SeeAllData=true` test exercises the real post under the annotation most Connect in Apex methods require. UNVERIFIED (2026-10-20): that a `FeedItem` row is queryable in the same test transaction after `postFeedElement` — not stated in Apex Developer Guide 264; drop the final assertion if it does not hold in your org.

---

## Anti-Pattern: Literal `@` In FeedItem.Body

**What practitioners do:**

```apex
insert new FeedItem(
    ParentId = caseId,
    Body = '@' + [SELECT Username FROM User WHERE Id = :ownerId].Username +
           ' Please review'
);
```

**What goes wrong:** The `@` is rendered as literal text. The owner gets no notification. The "mention" is just text the UI does not turn into a link.

**Correct approach:** Use `ConnectApi.MentionSegmentInput` with the user's Id; the platform resolves it to a notifying mention.

---

## Anti-Pattern: Calling ConnectApi Without Try/Catch

**What practitioners do:**

```apex
ConnectApi.ChatterFeeds.postFeedElement(null, recordId, input);
```

**What goes wrong:** `ConnectApiException` bubbles up to the caller. A webhook or async job aborts on a transient Chatter issue (Chatter disabled, feed tracking off, rate limit).

**Correct approach:** Wrap in `try/catch (ConnectApi.ConnectApiException e)` and degrade gracefully — log and continue, don't abort the primary transaction for a feed post.
