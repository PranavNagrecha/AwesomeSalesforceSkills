# Custom Notification Type — Examples

## Example 1: SLA Escalation CNT

**Trigger:** Case nears SLA breach (30 min remaining) via scheduled Flow.

**CNT:** `Case_SLA_Warning__c`, channels: bell + mobile push. Targeted to
case owner + queue members. Throttled one per case per hour.

**Body:** "Case {!caseNumber} breaches SLA in 30 minutes. Tap to open."

**Deep-link:** `/lightning/r/Case/{!caseId}/view`.

**Why:** actionable, urgent, targeted.

---

## Example 2: Approval Ready CNT

**Trigger:** Approval request arrives for a user.

**CNT:** `Approval_Pending__c`, bell + Slack DM (via Slack integration).

**De-dup:** one per approval instance; if user already notified in last
15 min, skip.

**Deep-link:** approval page.

**Why:** replaces email approval spam with a single channel that already
has user attention.

---

## Example 3: Non-Urgent Daily Digest

**Trigger:** daily scheduled flow summarizing new account assignments.

**CNT:** bell only, once per day at 9am local time. Lists up to 10 new
accounts with deep-links.

**Why:** bundles low-urgency info into one notification; zero push/Slack
noise.

---

## Anti-Pattern: Notify On Every Update

A team emitted CNTs on any Account field change. Users got 40 bells/day
for routine system updates. Within two weeks users silenced the channel.
Fix: notify on meaningful transitions only (owner change, opportunity
stage cross, etc.).
