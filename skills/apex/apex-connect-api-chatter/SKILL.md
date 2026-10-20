---
name: apex-connect-api-chatter
description: "Use when posting to a Chatter feed, creating feed comments, @mentioning users or groups, or rendering rich-text posts from Apex via the ConnectApi namespace. Trigger keywords: ConnectApi, FeedItem, Chatter post, @mention, rich text post, FeedElementCapabilities, link post. NOT for Experience Cloud feed embeds. NOT for sending email from Apex — use apex/apex-outbound-email-patterns. NOT for custom bell notifications — use apex/apex-custom-notifications-from-apex. NOT for turning down org-wide Chatter feed and digest noise — use admin/chatter-notification-tuning."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "How do I post a Chatter comment with a file attachment from Apex?"
  - "I want to @mention a user in a FeedItem I'm creating from a trigger"
  - "My ConnectApi.ChatterFeeds.postFeedElement call works in UI tests but fails in @future context"
tags:
  - apex-connect-api-chatter
  - apex-chatter-posting
  - apex-connectapi
  - apex-mentions
inputs:
  - "Feed parent Id (record, user, group) being posted to"
  - "Post payload: text, mentions, links, file attachment"
  - "Execution context (sync, trigger, async)"
outputs:
  - "ConnectApi-based Chatter post implementation"
  - "Checker findings against unsupported async usage and unsafe input"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex Connect Api Chatter

Activate this skill when Apex needs to post to Chatter, reply to a feed item, or @mention a user programmatically. The `ConnectApi` namespace is the only supported way to produce rich-content posts (mentions, links, files, polls) — direct DML on `FeedItem` is limited and does NOT support mention rendering.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is Chatter enabled in the org? `ConnectApi` throws `ConnectApi.ConnectApiException` if disabled.
- What's the execution context? `ConnectApi` has strict restrictions in `@future` and test methods.
- What sort of post? Plain text, text-with-mentions, link, file attachment, poll, or announcement?
- Who's the author? Running user by default; can impersonate only via `ConnectApi.ChatterFeeds.postFeedElement` parameters in limited cases.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is Chatter enabled in every org this code deploys to? | With Chatter off, every ConnectApi call throws `ConnectApiException` (gotcha 3). | A feature check and a fallback path, decided before the code is written. |
| Does the post need @mentions, files, links or polls? | `FeedItem` DML writes `@Jane` as literal text and fires no notification (gotcha 1). | The ConnectApi-vs-DML choice made from the content, not habit. |
| Which feed parent — user, group or record — and is feed tracking on for that object? | Posting to an untracked object throws (gotcha 4). | The parent type and the feed-tracking setting listed as a deployment dependency. |
| Will the post be made from an Experience Cloud site? | A missing or `null` network Id posts to internal Chatter, where site users never see it (gotcha 5). | `Network.getNetworkId()` passed, and a site test case. |
| Can every mentioned user read the parent record? | The mention renders but no notification reaches a user without access (gotcha 6). | A sharing check on the mentioned users, or a different notification channel. |
| How large are attached files, and does the post run sync or async? | A `Blob` counts toward heap: 10 MB sync / 25 MB async in Winter '27, and the overrun is uncatchable (gotcha 7). | A size guard, or a ContentVersion upload referenced by Id. |
| Who should appear as the author? | Connect in Apex runs as the context user and does not support `runAs` (Apex Developer Guide 264 L26329-26330; gotcha 9). | The running user named for each entry point, including async ones. |

Answering these first gives posts that reach the right feed, notify the right people and survive Chatter-off and large-file cases, where coding the post directly ships one that fails or posts invisibly.

---

## Core Concepts

### ConnectApi vs Direct DML On FeedItem

- `insert new FeedItem(...)` works but produces plain text only. No mentions, no files, no polls.
- `ConnectApi.ChatterFeeds.postFeedElement(...)` supports the full post capability set (mentions, files, links, polls, announcements).
- Rule: if the post has any rich content, use ConnectApi. Use direct DML only for the simplest text post where capabilities are not needed.

### `FeedItemInput` + `MessageBodyInput` + `MessageSegmentInput`

Rich posts are assembled from segments:

- `TextSegmentInput` — plain text
- `MentionSegmentInput` — `@user` or `@group`
- `LinkSegmentInput` — inline URL
- `HashtagSegmentInput` — `#topic`

Segments are concatenated in order into a `MessageBodyInput`, which is wrapped in a `FeedItemInput`.

### Test Context Restrictions

- Most Connect in Apex methods need real org data and fail unless the test method is marked `@IsTest(SeeAllData=true)` (Apex Developer Guide 264 L26331-26332).
- Some methods (for example `getFeedElementsFromFeed`) may not touch org data in tests; you register their output first with the matching `setTest*` method (`ConnectApi.ChatterFeeds.setTestGetFeedElementsFromFeed(...)`), and the method's "Usage" section says when this applies (L26333-26335, example at L26360-26377).
- There is no documented `Test.setMock(ConnectApi.ConnectApi.class, …)` mock: no `ConnectApi.ConnectApi` class appears in the Apex Developer Guide 264 or the Apex Reference Guide 262, and the 262 reference lists no `setTestPostFeedElement`. To unit-test payload assembly without `SeeAllData`, build the `FeedItemInput` in a separate method and assert on it, and keep one `SeeAllData=true` test for the real post.
- `@future` methods CAN call `ConnectApi`, but the calls run as the user who enqueued (or the automated user in some contexts) — test this explicitly.

### Feed Parent Id Types

Feeds hang off a parent record. Common parent types:

- User Ids (`005...`) — user's personal feed
- Group Ids (`0F9...`) — Chatter group
- Record Ids (`001...` etc.) — any object with feed tracking enabled
- `'me'` — shorthand for the running user

---

## Common Patterns

### Plain-Text Post With @Mention

**When to use:** A trigger or service needs to notify an owner by @mentioning them in a record feed.

**How it works:**

```apex
public static void postMentionToRecord(Id recordId, Id userToMention, String message) {
    ConnectApi.FeedItemInput post = new ConnectApi.FeedItemInput();
    ConnectApi.MessageBodyInput body = new ConnectApi.MessageBodyInput();
    body.messageSegments = new List<ConnectApi.MessageSegmentInput>();

    ConnectApi.MentionSegmentInput mention = new ConnectApi.MentionSegmentInput();
    mention.id = userToMention;
    body.messageSegments.add(mention);

    ConnectApi.TextSegmentInput text = new ConnectApi.TextSegmentInput();
    text.text = ' ' + message;
    body.messageSegments.add(text);

    post.body = body;

    ConnectApi.ChatterFeeds.postFeedElement(Network.getNetworkId(), recordId, post);
}
```

**Why not the alternative:** `insert new FeedItem(Body='@Jane ...')` shows literal `@Jane` text — no notification fires, no link is rendered.

### Post With File Attachment

**When to use:** Uploading a report PDF and posting it to a record feed in one go.

**How it works:**

```apex
ConnectApi.FeedItemInput input = new ConnectApi.FeedItemInput();
ConnectApi.MessageBodyInput body = new ConnectApi.MessageBodyInput();
body.messageSegments = new List<ConnectApi.MessageSegmentInput>{
    new ConnectApi.TextSegmentInput()
};
((ConnectApi.TextSegmentInput) body.messageSegments[0]).text = 'See attached report.';
input.body = body;

ConnectApi.NewFileAttachmentInput file = new ConnectApi.NewFileAttachmentInput();
file.title = 'Weekly Report';
input.capabilities = new ConnectApi.FeedElementCapabilitiesInput();
input.capabilities.content = new ConnectApi.ContentCapabilityInput();
input.capabilities.content.title = file.title;

ConnectApi.BinaryInput binary = new ConnectApi.BinaryInput(
    Blob.valueOf(pdfBytes), 'application/pdf', 'report.pdf');

ConnectApi.ChatterFeeds.postFeedElement(
    Network.getNetworkId(), recordId, input, binary);
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Plain text post, no mentions | Either ConnectApi or DML | Choose by team convention |
| Text with @mention | ConnectApi `MentionSegmentInput` | DML produces literal text |
| Post + file attachment | ConnectApi with `BinaryInput` | No DML equivalent |
| Poll post | ConnectApi `PollCapabilityInput` | No DML equivalent |
| Scheduled reminder post | Queueable calling ConnectApi | Governor-safe |
| Bulk posts (100s) | Batch + ConnectApi per record | Respects limits per execution |
| Experience Cloud posts | `Network.getNetworkId()` arg | `null` posts to internal Chatter |

---

## Recommended Workflow

1. Confirm Chatter is enabled — feature check via `FeatureManagement` or an admin confirm.
2. Identify feed parent — user, group, or record with feed tracking enabled.
3. Build the `FeedItemInput` by assembling message segments; handle null/empty text explicitly.
4. Decide sync vs async — post in the current transaction unless you need isolation; if async, write a governor-bounded Queueable.
5. Write tests — assert the payload shape on the `FeedItemInput` built by a separate method; cover the real post with an `@IsTest(SeeAllData=true)` test, or a `setTest*` registration where the method's Usage section requires one (Apex Developer Guide 264 L26331-26335).
6. Test Experience Cloud separately if posts must appear in a partner/customer community — `Network.getNetworkId()` argument matters.

---

## Review Checklist

- [ ] No literal `@username` strings in FeedItem.Body — mentions are always `MentionSegmentInput`.
- [ ] `Network.getNetworkId()` (not hardcoded network Id) for community context.
- [ ] Payload assembly is tested without ConnectApi; real ConnectApi calls are tested under `@IsTest(SeeAllData=true)` or with the method's `setTest*` registration (Apex Developer Guide 264 L26331-26335).
- [ ] ConnectApi call wrapped in try/catch of `ConnectApi.ConnectApiException`.
- [ ] Messages under Chatter's 10,000 char soft limit.
- [ ] File attachments under 2GB / org-specific limit.

---

## Salesforce-Specific Gotchas

1. **Chatter off means ConnectApiException** — orgs with Chatter disabled throw on every call; feature-flag the code.
2. **`FeedItem` DML cannot render mentions** — `@Jane` appears as literal text, no notification fires.
3. **`ConnectApi` in tests needs org data or registered output** — most methods fail without `@IsTest(SeeAllData=true)`; a few require a `setTest*` registration instead (Apex Developer Guide 264 L26331-26335). There is no `Test.setMock` mock for ConnectApi.
4. **Network Id must be passed** — omitting or using the wrong community Id posts to the wrong feed silently.
5. **Mentions require feed visibility** — user must have access to the parent record; otherwise the mention is rendered but no notification fires.
6. **Feed tracking must be on** — posting to a record whose object lacks feed tracking fails with a specific ConnectApiException.
7. **Polls cannot be edited after posting** — only deleted and reposted.
8. **ConnectApi does NOT call triggers on FeedItem** — `FeedItem` triggers fire on DML, but ConnectApi writes go through a separate path; relying on FeedItem triggers for ConnectApi posts is unreliable.

---

## Data 360 ConnectApi data graph reads (Spring '25–Spring '26)

Chatter is the primary ConnectApi surface for this skill, but teams mixing **Data 360 data graphs** into Apex should know the **`ConnectApi.CdpQuery`** additions (check each method's documented API version):

| Method family | API version | Use |
|---|---|---|
| `getDataGraphData(..., live)` | 63.0 (Spring '25) | Live/real-time data graph reads |
| `getDataGraphDataWithLookupKeys(..., noCache)` | 64.0 (Summer '25) | Lookup-key reads that bypass cache |
| `getMetadataEntities()` (+ overloads with dataspace) | 66.0 (Spring '26) | Discover graph entity metadata |

Earlier APIs expose materialized-view reads only. Version-gate call sites on **`apiVersion`**, not org release calendar.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `scripts/check_apex_connect_api_chatter.py` | Scans for literal `@` mentions in FeedItem DML, ConnectApi test calls without `SeeAllData=true`, and unsafe error handling |
| `templates/apex-connect-api-chatter-template.md` | Work template for assembling FeedItemInput with mentions and attachments |

---

## Related Skills

- `apex-custom-notifications-from-apex` — bell notifications (different system from Chatter)
- `apex-email-messaging` — email outreach (Chatter is not email)
- `apex-blob-and-content-version` — managing files attached to Chatter posts
