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
|  |  | Moderate Experiences Feeds |  |
|  |  | Moderate Experiences Feeds |  |

- [ ] All moderators are internal Salesforce users (not community-only license)
- [ ] Moderate Experiences Feeds permission set is created or identified
- [ ] Permission set is assigned to all moderators
- [ ] Moderators can access the moderation queue in Experience Workspaces

---

## Keyword Lists

| List Name | Purpose | Sample Terms | Tested in Sandbox |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |

- [ ] Each keyword list created in Setup > Experience Cloud Sites > [Site] > Moderation > Keyword Lists
- [ ] All keywords tested in sandbox for false positive partial matches
- [ ] Lists reviewed by compliance or community team

---

## Moderation Rules

List rules in **priority order** (top = fires first):

| Priority | Rule Name | Criteria Type | Criteria Detail | Content Type | Action | Active |
|---|---|---|---|---|---|---|
| 1 |  | Keyword List |  | Posts + Comments | Block |  |
| 2 |  | Member Criteria |  | Posts + Comments | Review |  |
| 3 |  | Keyword List |  | Posts + Comments | Flag |  |

- [ ] Block rules appear above Review and Flag rules in the ordered list
- [ ] Rule order reviewed in Setup after all rules are created
- [ ] Each rule tested with a sample post in sandbox before go-live
- [ ] Review action behavior (content hidden) communicated to stakeholders

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
| Post a question |  |
| Post an answer |  |
| Receive a like |  |
| Best answer selected |  |
| Log in |  |

- [ ] Reputation configured before or at site launch (not retroactive)
- [ ] If configuring on an active community: member communication plan in place
- [ ] Any Member Criteria rules referencing reputation levels tested with correct level thresholds

---

## Pre-Launch Verification

- [ ] Submitted a test post from a new member account — confirm Review hold behavior
- [ ] Submitted a test post containing a keyword list term — confirm Block rejection message
- [ ] Submitted a test post from a member matching Flag criteria — confirm post is live and moderator queue entry is created
- [ ] Moderator accessed queue, viewed held item, and approved it successfully
- [ ] Moderation policy documented (what triggers each action, SLA for queue review, moderator contacts)

---

## Notes

Record any deviations from standard configuration, stakeholder decisions, or known gaps here:

