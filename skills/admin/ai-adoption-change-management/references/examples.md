# Examples — AI Adoption Change Management

## Example 1: Agentforce Sales Agent Rollout to a Skeptical Sales Team

**Context:** A mid-market SaaS company deployed Agentforce Sales Agent to their 120-person inside sales team. The team had heard rumors that AI would reduce headcount, and a viral Slack message from a VP at a competitor described an AI rollout that eliminated 30 sales roles. The admin team planned a standard go-live email and a 45-minute Zoom training session.

**Problem:** Despite the training session, adoption was near zero at two weeks post-launch. Reps were logging into Salesforce but not invoking the Sales Agent. In exit interviews, reps said they were afraid that using the AI would generate a record of their "needing help" visible to management, and that they did not understand how the AI knew what to suggest.

**Solution:**

The admin team paused and restructured the rollout using the LEVERS model:

- **Leadership:** The VP of Sales recorded a 3-minute video showing herself using the Sales Agent on a real deal, narrating what she was thinking and why she chose to accept or override each suggestion. This was shared in the all-hands Slack channel.
- **Values:** The rollout messaging was rewritten to explicitly address job security: "This tool is here to make you more effective with customers, not to replace you. Every suggestion is a draft — you decide what goes out."
- **Enablement:** A second training was delivered specifically on the black-box problem — what data the AI uses (closed-won email threads and call transcripts in the org), what it cannot see (personal emails, CRM data from before the import date), and how to give feedback via thumbs-up/down.
- **Ecosystem:** Three reps who were early adopters were designated AI champions and given 30 minutes per week to answer peer questions in a dedicated Slack channel.
- **Rewards:** Weekly leaderboard added a "Feedback Given" column alongside closed deals — reps who submitted five or more feedback responses per week were recognized in the Monday stand-up.

```
LEVERS Scorecard (post-restructure):
Leadership:  3/3  — VP video, manager talking points distributed
Ecosystem:   3/3  — Three champions active, Slack channel live
Values:      3/3  — Job security messaging explicit in all comms
Enablement:  3/3  — Black-box training delivered, role-specific
Rewards:     2/3  — Feedback leaderboard active; comp tie-in pending
Structure:   2/3  — Agent embedded in Opportunity record; manager 1:1 integration pending
Total levers engaged: 6 (all at 2+)
```

At 30 days post-restructure, invocation rate increased from 4% to 61% of daily active users. Acceptance rate was 58% — lower than the team wanted but paired with a 72% feedback participation rate, giving the team meaningful signal for model improvement.

**Why it works:** The original launch failed at the Leadership, Values, and Ecosystem levers while investing heavily in Enablement alone. The LEVERS model diagnosed the gap. The trust communication directly addressed the black-box problem that was driving the silent non-adoption.

---

## Example 2: Using Feedback API to Diagnose a Model Quality Problem vs. a Training Problem

**Context:** A financial services firm deployed Einstein Reply Recommendations to their service team. At 60 days post-launch, the acceptance rate was 31% — well below the 60% target. The training team assumed the issue was poor training quality and began rebuilding the training curriculum.

**Problem:** Without structured feedback data, there was no way to distinguish between two failure modes: (A) users understood the AI but did not trust the suggestions because the suggestions were genuinely poor quality, or (B) users did not know how to interact with the AI effectively.

**Solution:**

The Feedback API had been enabled on launch but the reason text had never been analyzed. The admin team pulled the reason text for all thumbs-down signals in the 60-day period:

```
Rejection reason text analysis (top themes, n=847 feedback responses):
- "Suggested response mentions product X which we discontinued in March" — 34%
- "Wrong tone for this customer tier" — 28%
- "Good suggestion but I already sent something similar" — 19%
- "Doesn't match how we talk to enterprise accounts" — 12%
- "Completely off topic" — 7%
```

The analysis showed 34% of rejections were due to the model recommending a discontinued product — a data quality problem, not a training problem. The model had been trained on email data that pre-dated the product discontinuation. Rebuilding the training curriculum would have done nothing to fix this.

The fix was a model data refresh and a filter excluding pre-discontinuation product references, not a new training program. After the fix, acceptance rate rose to 64% within three weeks.

**Why it works:** The Feedback API reason text surfaced the actual failure mode. Without structured feedback data, the team would have invested six weeks in rebuilding training that was not the problem. This is why Feedback API instrumentation and reason-text analysis are required pre-conditions of any adoption measurement cadence — usage volume alone cannot distinguish model quality problems from enablement problems.

---

## Anti-Pattern: Treating Agentforce Rollout Like a Standard CRM Feature Launch

**What practitioners do:** Apply the existing change management playbook — go-live email, click-path training, and a hypercare period — to an Agentforce or Einstein feature deployment with no AI-specific modifications.

**What goes wrong:** The standard playbook does not address the job security anxiety, the black-box trust problem, or the need for AI-specific override and feedback training. Users attend training, know where to click, and then silently avoid the feature because they do not trust it and are not sure they are supposed to override it. Adoption dashboards show healthy login rates but near-zero AI invocation rates. By the time the adoption problem is visible in the metrics, negative peer-to-peer narratives have already established themselves in the team culture and are difficult to reverse.

**Correct approach:** Run a LEVERS gap analysis before any training content is produced. Treat trust-building and transparency communication as the critical path — not a nice-to-have add-on after training. Configure the Feedback API from day one so adoption signal is available before the problem is large. Use a phased pilot with a promotion gate rather than a big-bang launch.
