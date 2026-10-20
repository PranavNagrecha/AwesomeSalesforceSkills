# Gotchas — Apex Connect Api Chatter

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: `FeedItem.Body` Mentions Are Literal Text

**What happens:** `insert new FeedItem(Body='@Jane please review')` shows the literal string `@Jane` in the feed. No notification fires; Jane never knows.

**When it occurs:** Any attempt to create a Chatter post via DML rather than ConnectApi.

**How to avoid:** Use `ConnectApi.MentionSegmentInput` — the only way to produce a notifying mention.

---

## Gotcha 2: ConnectApi Needs Org Data Or Registered Test Output

**What happens:** A unit test calling `ConnectApi.ChatterFeeds.postFeedElement` fails. Most Connect in Apex methods require access to real org data and fail unless the test method is marked `@IsTest(SeeAllData=true)`; some methods, such as `getFeedElementsFromFeed`, may not access org data in tests at all and need their output registered first with the matching `setTest*` method, as each method's "Usage" section states (Apex Developer Guide 264 L26331-26335). UNVERIFIED (2026-10-20): the exact exception type and message a non-`SeeAllData` test receives — not stated in Apex Developer Guide 264.

**When it occurs:** Default tests (without `SeeAllData=true`), and any test of a `setTest*`-registered method whose registration does not match the call's parameter signature (L26345-26346).

**How to avoid:** Keep payload assembly in its own method and unit-test the `FeedItemInput` it returns without calling ConnectApi. Test the real call under `@IsTest(SeeAllData=true)`, or with the `setTest*` registration where the method's Usage section requires it. Do not reach for `Test.setMock(ConnectApi.ConnectApi.class, …)`: no `ConnectApi.ConnectApi` mock class is documented in Apex Developer Guide 264 or Apex Reference Guide 262.

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

**What happens:** Uploading a 25MB PDF via `BinaryInput` exceeds the 10 MB synchronous heap limit outright and leaves no headroom under the 25 MB asynchronous one, so it fails on heap before it hits any DML limit. The heap overrun is an uncatchable `System.LimitException` (Apex Developer Guide 264 L19780, L19853). These are Winter '27 limits for every org whatever the class API version; Summer '26 was 6MB / 12MB, and in Winter '27 only a nonproduction org can opt back to those with `ApexSettings.enableEnforceSummer26ApexHeapLimit` (Metadata API 264 L113855-113862).

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
