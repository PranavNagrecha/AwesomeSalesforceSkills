# Custom Notification Type Design

One of these per notification type. Fill it before creating the type in Setup;
the unanswerable questions are the design problems.

Checked by `scripts/check_custom_notification_type_design.py --docs-dir <dir>`.

## Purpose

- Notification type API name (max 80 chars):
- Label:
- Description (max 255 chars, written as prose a human reads next to the name):
- Owner (team, not an individual):
- **Actionable outcome expected from recipient** — one sentence, with a verb:
  > e.g. "The on-call agent reassigns or escalates the case before SLA breach."
- If that sentence cannot be written, stop. This is a report subscription.

## Trigger

- Source (Flow / Apex / Process Builder):
- Event (record change / schedule / platform event):
- Entry condition — the *transition*, not the save:
- Actor excluded from recipients? (Y/N — the person who did the thing should not
  be told the thing was done):
- Throttling (min interval per record / daily cap per user):
- Where the throttle state lives (record field / delivery-log object):
- Fate of suppressed events (dropped / rolled into digest):

## Channels

- [ ] Desktop (`desktop` on the type) — the bell and browser notifications
- [ ] Mobile push (`mobile` on the type)
- [ ] Slack — **separate notification type**; record its name here if in scope:

Justification per channel, tied to required response time:

| Channel | Enabled? | Required response time | Justification |
|---|---|---|---|
| Desktop | | | |
| Mobile  | | | |

`slack` on `CustomNotificationType` is "Reserved for future use" — leave it unset.

## Delivery gates

All four must be open or the notification silently goes nowhere.

- [ ] Gate 1 — channel flags set on the `.notiftype`
- [ ] Gate 2 — `NotificationTypeConfig` deployed with this type, listing:
  - `notificationChannels`: desktopEnabled / mobileEnabled / slackEnabled
  - `appSettings` — every connected app that must deliver (exact API names read
    from the target org, not guessed):
- [ ] Gate 3 — user preference (cannot be forced; note the default)
- [ ] Gate 4 — verified on a real mobile device, not just a browser

## Targeting

- [ ] Owner (`OwnerId` — may be a user or a queue; both are valid)
- [ ] Public group (`GroupId` — all active members)
- [ ] Queue (`QueueId` — all active members)
- [ ] Account team (`AccountId` — **requires account teams enabled**)
- [ ] Opportunity team (`OpportunityId` — **requires team selling enabled**)
- [ ] Dynamic via Flow
- [ ] Explicit user list (avoid — a snapshot that starts rotting on day one)

ID expression (aim for the fewest values; 500 is a cap on IDs, not on people):

Prerequisites this design depends on, and how they are asserted at deploy time:

Who is deliberately NOT notified, and why:

## Body

- Title (max 250 chars after merge fields resolve):
- Body (max 750 chars after merge fields resolve):
- Longest realistic value of each merge field, and where it is clipped:
- Deep link:
  - [ ] `targetId` (record destination — preferred)
  - [ ] `targetPageRef` (non-record destination; serialized PageReference)
  - [ ] Raw `/lightning/r/...` URL — **not acceptable**
- Does the body contain any field value the recipient may not have access to?
  (The body bypasses the record's sharing model; the deep link does not.)

## Consent And Frequency

- User preference honored: Y
- Daily cap per user:
- Quiet hours:
- Digest alternative considered? Why rejected:
- Bypass switch for bulk loads and migrations (so a data load cannot consume the
  org-wide notification allocation):

## Observability

- Success metric (a follow-on action, not a delivery count):
- Where it is recorded:
- Engagement threshold below which this type is redesigned or deleted:
- Review cadence and next review date:
- Registry entry created (`Notification_Registry__mdt`): Y/N

## Sign-Off

- [ ] Recipient can act on this notification, and has permission to.
- [ ] Channel matches urgency; every enabled channel has a written justification.
- [ ] `NotificationTypeConfig` ships with the type.
- [ ] Deep link lands on the specific record.
- [ ] Throttling prevents rapid repeats and survives across transactions.
- [ ] Body leaks no data the recipient cannot already see.
- [ ] Registry entry added, with owner and review date.
- [ ] Delivery verified on desktop AND on a real mobile device.
