# LLM Anti-Patterns — Chatter Notification Tuning

Common mistakes AI assistants make when an admin asks for chatter-noise reduction. Avoid these when generating recommendations.

---

## Anti-Pattern 1: Recommending org-level disable as the first move

**What the LLM generates:** "Go to Setup → Chatter Settings and uncheck Enable Chatter to fix the email volume."

**Why it's wrong:**
- Disabling Chatter org-wide is a one-way operation; re-enabling does not restore feed history.
- Most "noise" complaints are from a small set of automated sources, not Chatter itself.
- Org-level email-off doesn't affect users who saved their Email Notifications preferences.

**What to do instead:** Inventory automated `FeedItem` sources first. Tune Feed Tracking and per-group frequency. Disable Chatter only as a last resort for compliance-driven full removal.

---

## Anti-Pattern 2: Confusing Custom Notifications with Chatter

**What the LLM generates:** "Use Notification Builder to send a Chatter post" or "post to the user's bell via FeedItem."

**Why it's wrong:**
- Custom Notifications and Chatter feed posts are different APIs with different storage and visibility models. They are not interchangeable.
- A `FeedItem` does not produce a bell notification on its own; the bell is a separate channel driven by `Messaging.CustomNotification.send()` or follow-based feed digest.

**What to do instead:** Call them by their right names — Chatter posts insert `FeedItem`; bell notifications use `Messaging.CustomNotification`. When the user says "bell" they mean the latter; when they say "feed" they mean the former.

---

## Anti-Pattern 3: Setting `NotificationFrequency = 'Limited'` instead of `'L'`

**What the LLM generates:**

```apex
update new CollaborationGroupMember(Id = m.Id, NotificationFrequency = 'Limited');
```

**Why it's wrong:** `NotificationFrequency` stores a one-character code (`D`, `W`, `P`, `N`, `L`). The UI shows the long label but the API expects the code. The above silently fails or stores an invalid value depending on API version.

**What to do instead:** Always use the code:

```apex
update new CollaborationGroupMember(Id = m.Id, NotificationFrequency = 'L');
```

---

## Anti-Pattern 4: Forgetting `Visibility = 'InternalUsers'` on automated FeedItem inserts

**What the LLM generates:**

```apex
FeedItem fi = new FeedItem();
fi.ParentId = oppId;
fi.Body = '🎉 Closed won!';
insert fi;
```

**Why it's wrong:** `Visibility` defaults to `AllUsers`, which exposes the post to Experience Cloud / Customer Community users with feed access on the parent record. For internal-only celebratory or operational posts, this is a low-frequency data leak.

**What to do instead:**

```apex
FeedItem fi = new FeedItem();
fi.ParentId = oppId;
fi.Body = '🎉 Closed won!';
fi.Visibility = 'InternalUsers';
insert fi;
```

Audit existing automation for this default.

---

## Anti-Pattern 5: Recommending a Flow / Apex purge of `FeedItem` records as a "cleanup"

**What the LLM generates:** "Run a daily batch deleting `FeedItem` older than 30 days to keep feeds clean."

**Why it's wrong:**
- `FeedItem` is the audit trail for Chatter-driven business events. Approvals, owner changes, escalations may all be recorded there.
- Deleting `FeedItem` removes that audit record permanently — not just from the feed UI but from the data layer. Compliance teams will be unhappy.
- The `feed full of automated posts` problem is a *source* problem, not a *retention* problem. Don't paper over the source by deleting evidence.

**What to do instead:** Migrate transient automated posts to Custom Notifications (which don't write `FeedItem` records). Leave durable business-event posts in place.

---

## Anti-Pattern 6: Confusing `EntitySubscription` (auto-follow) with feed visibility

**What the LLM generates:** "To stop chatter notifications for a user, remove them from `EntitySubscription`."

**Why it's wrong:**
- `EntitySubscription` is the "follow" relationship — it controls whether the user *receives* feed updates from that record's followed-feed channel.
- Notifications also flow from group membership (`CollaborationGroupMember`), @mentions, and bell notifications — none of which are `EntitySubscription` records.

**What to do instead:** Identify the *channel* of the unwanted notification — followed records, group activity, or bell — then tune the right control surface.

---

## Anti-Pattern 7: Telling the user to "disable Feed Tracking" when the issue is auto-follow

**What the LLM generates:** "Turn off Feed Tracking on Account to reduce noise."

**Why it's wrong:** Feed Tracking generates `FeedItem` on tracked field changes — but those `FeedItem`s only land in a user's feed if the user is *following* that record. If the noise complaint is "I see updates on records I never asked to follow," the auto-follow rule is the problem, not Feed Tracking.

**What to do instead:** Diagnose first. If user has `EntitySubscription` records they didn't create, the fix is auto-follow tuning. If `FeedItem` volume on the parent is high regardless of who follows, the fix is Feed Tracking pruning.
