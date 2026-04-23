# LLM Anti-Patterns — Apex Connect Api Chatter

## Anti-Pattern 1: FeedItem DML With Literal `@` Mention

**What the LLM generates:**

```apex
insert new FeedItem(
    ParentId = caseId,
    Body = '@' + user.Name + ' please review'
);
```

**Why it happens:** LLMs treat `@mention` as string concatenation — it "looks like" what the UI shows.

**Correct pattern:** `ConnectApi.MentionSegmentInput` with the user's Id, assembled into a `MessageBodyInput`.

**Detection hint:** String literal containing `'@'` in a `FeedItem(Body=...)` DML.

---

## Anti-Pattern 2: Hardcoded Network Id

**What the LLM generates:**

```apex
ConnectApi.ChatterFeeds.postFeedElement('0DB...', recordId, input);
```

**Why it happens:** LLMs see `networkId` in the signature, reach for a hardcoded value from an example they saw.

**Correct pattern:** `Network.getNetworkId()` to follow the current context, or `null` for internal Chatter.

**Detection hint:** String literal matching `0DB[a-zA-Z0-9]{12,15}` as first argument.

---

## Anti-Pattern 3: ConnectApi In Test Without Mock

**What the LLM generates:**

```apex
@IsTest static void testPost() {
    EscalationFeedService.postEscalationMention(caseId, userId, 'reason');
    // throws UnsupportedOperationException
}
```

**Why it happens:** LLMs don't know ConnectApi has special test-mode rules.

**Correct pattern:** `Test.setMock(ConnectApi.ConnectApi.class, new MockConnectApi())` before the call.

**Detection hint:** `ConnectApi.` call site inside `@IsTest` method without a preceding `Test.setMock` line.

---

## Anti-Pattern 4: No Try/Catch Around ConnectApi Calls

**What the LLM generates:**

```apex
ConnectApi.ChatterFeeds.postFeedElement(networkId, recordId, input);
return;
```

**Why it happens:** LLMs treat Chatter posting as a simple, always-succeeds operation.

**Correct pattern:**

```apex
try {
    ConnectApi.ChatterFeeds.postFeedElement(networkId, recordId, input);
} catch (ConnectApi.ConnectApiException e) {
    System.debug(LoggingLevel.ERROR, 'Post failed: ' + e.getMessage());
}
```

**Detection hint:** `ConnectApi.ChatterFeeds.postFeedElement` without a surrounding `try`.

---

## Anti-Pattern 5: Using `SeeAllData=true` To Make ConnectApi Tests Pass

**What the LLM generates:**

```apex
@IsTest(SeeAllData=true)
static void testPost() { /* ... */ }
```

**Why it happens:** LLMs reach for the simplest fix that makes the test run without understanding the consequences.

**Correct pattern:** Use `Test.setMock(ConnectApi.ConnectApi.class, ...)`. `SeeAllData=true` makes tests org-specific and flaky.

**Detection hint:** `SeeAllData=true` annotation near a `ConnectApi.` call.

---

## Anti-Pattern 6: Missing Capabilities Wrapper For Attachments

**What the LLM generates:**

```apex
ConnectApi.FeedItemInput input = new ConnectApi.FeedItemInput();
input.attachment = new ConnectApi.ContentCapabilityInput(); // wrong field
```

**Why it happens:** LLMs hallucinate field names. The correct nesting is `input.capabilities.content = new ConnectApi.ContentCapabilityInput()`.

**Correct pattern:** Always go through `capabilities` on `FeedItemInput`/`FeedElementInput`.

**Detection hint:** `FeedItemInput` with any field name that isn't `body`, `subjectId`, `isBookmarkedByCurrentUser`, `capabilities`, `originalFeedElementId`, `visibility`, or `feedElementType`.

---

## Anti-Pattern 7: Generating Mentions For Bulk Post Inside A Trigger

**What the LLM generates:**

```apex
trigger OnCaseUpdate on Case (after update) {
    for (Case c : Trigger.new) {
        ConnectApi.ChatterFeeds.postFeedElement(...); // per-record call
    }
}
```

**Why it happens:** LLMs don't consider ConnectApi's per-transaction governor cost (one post ~= one DML on FeedItem, but capabilities trigger additional operations).

**Correct pattern:** Enqueue a single Queueable with the list of cases; the Queueable iterates and posts, staying within async limits.

**Detection hint:** `ConnectApi.` call inside a `for` loop inside a trigger.

---

## Anti-Pattern 8: Treating ConnectApi Posts As Email Alternatives

**What the LLM generates:** Using Chatter mentions as the delivery mechanism for transactional notifications (order confirmations, password resets, etc.).

**Why it happens:** LLMs don't distinguish internal collaboration (Chatter) from transactional email.

**Correct pattern:** Email via `Messaging.SingleEmailMessage`. Chatter is for internal collaboration; external-facing transactional notifications belong in email.

**Detection hint:** Chatter posts with subject lines like "password reset", "order confirmation", etc.
