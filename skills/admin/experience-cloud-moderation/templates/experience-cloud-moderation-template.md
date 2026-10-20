# Experience Cloud Moderation — Setup Checklist Template

Use this template when configuring moderation for a new or existing Experience Cloud site. Fill in each section before beginning configuration. Check off each item before marking setup complete.

---

## Scope

**Site name:**
**Site type:** (Customer Community / Partner Community / LWR / Aura)
**Environment:** (Sandbox / Scratch Org / Production)
**Configuration date:**
**Configured by:**

---

## Moderator Assignment

| User Name | License Type | Permission Set Assigned | Queue Access Confirmed |
|---|---|---|---|
|  |  | Moderate Experiences Feeds, Can Approve Feed Post and Comment |  |
|  |  | Moderate Experiences Feeds, Can Approve Feed Post and Comment |  |

- [ ] License pairing for each moderator checked in a sandbox (UNVERIFIED 2026-10-20: whether community-only licenses can hold these permissions is Help-only)
- [ ] Permission set is created or identified for Moderate Experiences Feeds (Moderation feed) and Can Approve Feed Post and Comment (publishing held items)
- [ ] Permission set is assigned to all moderators
- [ ] Moderators can open the Moderation feed (UNVERIFIED 2026-10-20: the Experience Workspaces location is Help-only)

---

## Keyword Lists

| List Name | Purpose | Sample Terms | Tested in Sandbox |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |

- [ ] Each keyword list created (UNVERIFIED 2026-10-20: the Setup > Experience Cloud Sites > [Site] > Moderation path is Help-only) and within the limits: 2,000 keywords per list, 100 characters per keyword, 30 lists per org (api_meta 264 L84924-84925, L84965)
- [ ] All keywords tested in sandbox for false positives (matching ignores capitalization and trailing punctuation; no wildcards)
- [ ] Lists reviewed by compliance or community team

---

## Moderation Rules

List rules by action precedence (Block runs first, then Review, then Replace, then Flag; the oldest rule runs first among rules with the same action; api_meta 264 L92226-92229):

| Precedence | Rule Name | Criteria Type | Criteria Detail | Entity and field | Action | Active |
|---|---|---|---|---|---|---|
| 1 |  | Keyword List |  | FeedItem RawBody, FeedComment RawCommentBody | Block |  |
| 2 |  | userCriteria |  | FeedItem RawBody, FeedComment RawCommentBody | Review |  |
| 3 |  | Keyword List |  | FeedItem RawBody, FeedComment RawCommentBody | Flag |  |

- [ ] Rule count within the org limit of 30 (content and rate rules together) and three keyword criteria per rule (api_meta 264 L92218-92219)
- [ ] Rules created with the Metadata API are not edited in the UI (api_meta 264 L92215-92216)
- [ ] Each rule tested with a sample post in sandbox before go-live
- [ ] Review action behavior (PendingReview: visible to the author and permitted users) communicated to stakeholders

---

## Reputation Configuration

| Level | Name | Point Threshold | Used in Moderation Rule |
|---|---|---|---|
| 1 | New Member | 0 | Yes / No |
| 2 |  |  | Yes / No |
| 3 |  |  | Yes / No |
| 4 |  |  | Yes / No |
| 5 |  |  | Yes / No |

**Point values per action:**

| Action | Points Awarded |
|---|---|
| FeedItemPostAQuestion |  |
| FeedItemAnswerAQuestion |  |
| FeedItemReceiveALike |  |
| FeedItemYourAnswerMarkedBest |  |
| Other documented events (api_meta 264 L94412-94429) |  |

- [ ] Reputation configured before or at site launch (UNVERIFIED 2026-10-20: whether points are retroactive is Help-only; test with a prior-activity account)
- [ ] If configuring on an active community: member communication plan in place
- [ ] Any Member Criteria rules referencing reputation levels tested with correct level thresholds (UNVERIFIED 2026-10-20: reputation as member criteria is Help-only)

---

## Pre-Launch Verification

- [ ] Submitted a test post from a new member account — confirm Review hold behavior
- [ ] Submitted a test post containing a keyword list term — confirm Block rejection message
- [ ] Submitted a test post from a member matching Flag criteria — record whether it is live and whether it reaches the Moderation feed (UNVERIFIED 2026-10-20: live visibility is Help-only)
- [ ] Approver viewed the held item and published it successfully
- [ ] Moderation policy documented (what triggers each action, SLA for queue review, moderator contacts)

---

## Notes

Record any deviations from standard configuration, stakeholder decisions, or known gaps here:

