# Gotchas — Apex Connect Api Chatter

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: `FeedItem.Body` Mentions Are Literal Text

**What happens:** `insert new FeedItem(Body='@Jane please review')` shows the literal string `@Jane` in the feed. No notification fires; Jane never knows.

**When it occurs:** Any attempt to create a Chatter post via DML rather than ConnectApi.

**How to avoid:** Use `ConnectApi.MentionSegmentInput` — the only way to produce a notifying mention.

---

## Gotcha 2: ConnectApi Requires Mocks In Standard Tests

**What happens:** A unit test calling `ConnectApi.ChatterFeeds.postFeedElement` throws `System.UnsupportedOperationException: The method you called is not supported in Apex tests.`

**When it occurs:** Default tests (without `SeeAllData=true`).

**How to avoid:** `Test.setMock(ConnectApi.ConnectApi.class, new MyMock())` with a class extending `ConnectApi.ConnectApi`. Avoid `SeeAllData=true` — it breaks org isolation.

---

## Gotcha 3: Chatter Can Be Disabled Org-Wide

**What happens:** ConnectApi calls throw `ConnectApi.ConnectApiException: Chatter is not enabled` and the feature is invisible to most admins.

**When it occurs:** Orgs that never enabled Chatter or turned it off.

**How to avoid:** Defensive `try/catch (ConnectApi.ConnectApiException)` with a feature-flag fallback. Document the Chatter requirement in the feature's admin guide.

---

## Gotcha 4: Feed Tracking Must Be On For The Parent Object

**What happens:** Posting to a record whose sObject has no feed tracking throws `ConnectApiException: Feed tracking is not enabled for this object`.

**When it occurs:** Any object not configured with feed tracking in Setup (Opportunity? on by default. Custom objects? off by default).

**How to avoid:** Document the feature's feed-tracking requirement. For custom objects, ship the `.object-meta.xml` with `<enableFeeds>true</enableFeeds>`.

---

## Gotcha 5: Network Id Defaults To Internal Chatter

**What happens:** Omitting or passing `null` as the network Id posts to the internal Chatter feed, not the current Experience Cloud community. Experience Cloud users never see the post.

**When it occurs:** Webhooks, triggers, async jobs — contexts where `Network.getNetworkId()` is not obvious.

**How to avoid:** Always pass `Network.getNetworkId()` explicitly. If posting from a context with no network (pure internal), use `null`; otherwise pass the current network.

---

## Gotcha 6: Mentions To Users Without Record Access Render But Don't Notify

**What happens:** A `MentionSegmentInput` for a user who lacks read access to the parent record shows as a mention in the feed, but no notification bell rings for that user.

**When it occurs:** Record-level sharing restricts visibility.

**How to avoid:** Verify feed parent is visible to the mentioned user. For guaranteed notifications, use `apex-custom-notifications-from-apex` instead of Chatter mentions.

---

## Gotcha 7: `BinaryInput` Counts Against Heap, Not DML

**What happens:** Uploading a 25MB PDF via `BinaryInput` hits the 6MB sync / 12MB async heap limit before it hits any DML limit.

**When it occurs:** Posting generated reports, document attachments.

**How to avoid:** Check `Blob.size()` before the post; for large files, upload a ContentVersion first and then reference it by Id rather than sending the Blob through ConnectApi.

---

## Gotcha 8: FeedItem Triggers Fire Inconsistently For ConnectApi Writes

**What happens:** A team adds a trigger on `FeedItem` to redact sensitive words. The trigger fires for DML-inserted FeedItems but not reliably for ConnectApi-inserted ones (behavior depends on API version and capability type).

**When it occurs:** Mixed DML + ConnectApi posting within the same org.

**How to avoid:** Don't rely on `FeedItem` triggers for validation of ConnectApi posts. Validate at the service layer before calling ConnectApi.

---

## Gotcha 9: `@future` Can Call ConnectApi But Runs As Different User

**What happens:** `@future` methods run as the enqueuing user by default, but in some contexts (Platform Event triggers, automated processes) the `UserInfo.getUserId()` may differ. A post attributed to "the wrong person" appears in the feed.

**When it occurs:** Platform Event-driven posts, automation-triggered posts.

**How to avoid:** Pass the intended post author's Id explicitly, and in async contexts, log the running user at post time so attribution is auditable.
