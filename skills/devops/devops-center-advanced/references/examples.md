# Examples — DevOps Center Advanced Workflows

Worked examples for teams already running DevOps Center who need it to coexist
with a CLI-based workflow, survive an emergency, and stay governable at scale.

Two products share the name and are documented separately. Getting the
distinction right is the first thing every one of these examples depends on:

| | DevOps Center (Managed Package) | Next Generation DevOps Center |
|---|---|---|
| Delivery | Installed as a managed package and configured as an app | Native platform capability — no package install |
| Setup docs | *Install and Configure DevOps Center (Managed Package)* | *Set Up Next Generation DevOps Center* |
| Source control | GitHub | GitHub, Bitbucket (beta) |
| Change tracking | In-app | DX Inspector, surfaced in the sandbox / scratch org / Developer Edition org itself |
| Edition floor | See the managed-package setup docs | Professional Edition with API access or higher; Lightning Experience; not available in Government Cloud Plus or the EU Operating Zone |
| Agent governance | — | Policies covering coding agents as well as users |

When you read a runbook, a blog post, or an AI-generated answer about DevOps
Center, establish which of these two it describes before acting on it.

---

## Example 1: Admins in the UI, Developers in the CLI, One Pipeline

**Context:** A team of four admins and three developers on one Salesforce org.
The admins want a click path; the developers want branches, local tooling, and
code review. Splitting into two release processes was tried and produced two
sets of drift.

**Problem:** DevOps Center's promotion model is work-item-shaped: a work item
owns a branch and a set of changes, and promotion moves that branch through the
pipeline stages. A developer who branches and merges outside that model
produces commits the work item does not know about. The pipeline stays green
and the promotion is wrong.

**Solution:** Make the work item the unit of promotion for *both* populations,
and let each population reach it differently.

```text
Work item WI-0142  "Add renewal reminder automation"
  │
  ├── Admin path
  │     Change made declaratively in the dev sandbox
  │     DX Inspector (next-gen) surfaces the change in the org itself:
  │       track → select components → commit to the work item branch
  │
  ├── Developer path
  │     git checkout <work-item-branch>          <- the branch DOC created
  │     sf project retrieve start --target-org devsbx
  │     git commit / git push                    <- same branch, same work item
  │
  └── Promotion
        DOC merges the work-item branch into the next stage's branch
        and deploys to that stage's org
```

**Why it works:** There is exactly one branch per work item, and both
populations write to it. The developers keep their tools; the admins keep their
UI; nothing is promoted that is not attached to a work item. The rule that makes
it hold is negative rather than positive: **no branch that is not a work-item
branch is ever merged into a pipeline branch.**

**The failure this avoids:** a developer creating a feature branch, merging it
straight to the integration branch, and the work item that "covers" that change
promoting an empty or partial diff later. The pipeline reports success. The
target org has the change from the direct merge and the work item's record of it
is wrong, so the next environment down the line gets a different set.

---

## Example 2: A Bypass Runbook Written Before You Need It

**Context:** Production incident at 02:00. A validation rule is blocking every
Case save. The fix is a one-field change. Promotion through the pipeline takes
about twenty minutes of deploys the team does not have.

**Problem:** Every team eventually deploys directly to production around the
pipeline. The question is not whether but whether the runbook was written in
advance or improvised by a tired person. Improvised bypasses skip the
reconciliation step, and the org and the repository diverge silently — which
surfaces a week later as the next normal promotion reverting the hotfix.

**Solution:** A pre-authorized, pre-written bypass with a mandatory
reconciliation step.

```bash
# --- BYPASS RUNBOOK: production hotfix outside the pipeline ---
# Authorized by: <on-call lead>. Trigger: Sev-1 only.

# 1. Capture the pre-state so rollback is possible.
sf project retrieve start \
  --metadata "ValidationRule:Case.Require_Reason" \
  --target-org prod
git checkout -b hotfix/INC-4471
git add . && git commit -m "INC-4471: capture pre-state"

# 2. Validate before you deploy. Non-negotiable, even at 02:00.
sf project deploy validate \
  --metadata "ValidationRule:Case.Require_Reason" \
  --target-org prod \
  --test-level RunSpecifiedTests \
  --tests CaseTriageServiceTest \
  --wait 30

# 3. Deploy the validated set by job id — no second compile, no surprises.
sf project deploy quick --job-id <validate-job-id> --target-org prod

# 4. RECONCILIATION — the step that gets skipped. Do it before you sleep.
#    a. Merge hotfix/INC-4471 into the production pipeline branch.
#    b. Cascade it DOWN the pipeline (prod -> uat -> integration -> dev)
#       so the next normal promotion does not revert it.
#    c. Open a work item recording the bypass and link the incident.
```

**Why it works:** `deploy validate` followed by `deploy quick` gives you a
tested deployment without paying the test time twice, and the job id is a
durable artifact for the incident record. Step 4b is the one that actually
prevents the second incident: a hotfix applied only to production is a change
that every lower environment does not have, and the next promotion from a lower
environment overwrites it.

**Governance that keeps this honest:** count bypasses per month and review them.
A bypass rate that does not trend toward zero is a statement about pipeline
latency, not about incident frequency — the fix is to make normal promotion fast
enough that nobody wants the bypass.

---

## Example 3: Two Admins, One Flow, One Merge Conflict

**Context:** Two admins are assigned separate work items in the same sprint.
Both edit `Case_Escalation_Router` in their own dev sandboxes. The second
promotion fails on a merge conflict.

**Problem:** Flow metadata is one XML document per version, with element
positions (`locationX`, `locationY`) embedded in it. Two people editing the same
flow produce a conflict that is textually enormous and semantically opaque —
diffing two flow XML documents does not tell a human which business rule won.
Resolving it in a text editor is how flows get silently corrupted.

**Solution:** Do not resolve flow conflicts textually.

1. Accept one side wholesale. Pick the version that is further along and take it
   entire — no hand-merging of XML hunks.
2. Re-apply the other admin's change in Flow Builder, in a sandbox, by hand.
3. Commit that result to the losing work item's branch.
4. Deploy to a test stage and open the flow in Flow Builder to confirm the
   canvas is intact before promoting further.

**Why it works:** It treats the flow as a build artifact rather than source. The
semantic merge happens in the tool that understands the semantics, and the
version control system only ever stores whole, valid documents.

**The prevention, which is better than the cure:** treat "who is editing which
flow this sprint" as a scheduling constraint at work-item assignment time. Flow
is one of a small set of metadata types — flows, page layouts, profiles,
permission sets, translations — where concurrent edits are expensive enough to
be worth serializing. For permission sets specifically, the conflict is not even
the worst part: see `devops/permission-set-deployment-ordering` for the
full-replace behaviour that silently drops permissions the deploying package did
not contain.

---

## Example 4: Wrong vs Right — Testing on the Promotion

**Wrong:**

```bash
# Promotion runs the org default and finds out at the last stage.
sf project deploy start --target-org prod --wait 60
```

Deploying to production without an explicit `--test-level` takes the org's
default behaviour, and the first honest signal about test health arrives at the
most expensive possible moment. Worse, a long-running test suite on the
production deploy is the thing that makes promotion slow, which is what drives
teams to the bypass in Example 2.

**Right:**

```bash
# Cheap, early, on every work item: validate against a test stage.
sf project deploy validate \
  --target-org uat \
  --test-level RunLocalTests \
  --wait 60

# Production promotion: validate, then quick-deploy the validated set.
sf project deploy validate --target-org prod --test-level RunLocalTests --wait 60
sf project deploy quick --job-id <job-id> --target-org prod
```

`deploy validate` performs a full check-only deploy including tests, and
`deploy quick` then commits that already-validated set without re-running them.
The expensive part happens once, ahead of the change window, and the production
step is short. A validated deployment does not stay eligible for quick-deploy
indefinitely, so plan the validation close to the change window rather than
weeks ahead. <!-- UNVERIFIED: the exact eligibility window for a quick deploy
(commonly cited as 10 days) was not confirmed against a fetchable official page
during authoring; check the Metadata API deploy documentation before writing a
number into a runbook. -->

**Driving the same thing from the CLI — install the plugin first:** the pipeline
commands are *not* part of the base Salesforce CLI. They come from
`@salesforce/plugin-devops-center`, which Salesforce documents as an optional beta
plugin. Without this step every command below fails as "command not found," which
is the usual way a CI runner discovers the dependency.

```bash
sf plugins install @salesforce/plugin-devops-center
sf plugins        # confirm it is present, and record the version you pinned
```

Once installed, the CLI exposes pipeline operations directly, currently as beta
commands — `sf project deploy pipeline validate`, `sf project deploy pipeline
start`, `sf project deploy pipeline quick`, `sf project deploy pipeline report`,
and `sf project deploy pipeline resume`. These deploy from a branch into the
pipeline stage's org, which is the supported way to put a DevOps Center promotion
behind a CI job instead of a human clicking Promote. Both the plugin and the
commands are beta — "Any aspect of this command can change without advanced
notice. Don't use beta commands in your scripts" — so pin the plugin version in
the CI image, and keep this in a pilot before it goes in a release runbook.

**The DevOps Center consequence:** promotion into a stage deploys into that
stage's org, and every test run there consumes that org's capacity. On a shared
UAT org with several teams promoting, test-run contention is a real scheduling
constraint, not a rounding error.

---

## Example 5: Deciding Whether to Move to Next Generation DevOps Center

**Context:** A team on the managed-package DevOps Center is asked whether to
move to the next-generation, native version.

**Problem:** "It's the newer one" is not a decision. The two differ in setup
model, source-control support, and governance surface, and the answer depends on
which of those the team is actually blocked on.

**Solution:** Decide against concrete blockers, in this order.

| If the team is blocked on… | Next-gen changes it? |
|---|---|
| Managed package install / upgrade friction in a regulated org | Yes — instant setup, no package to install or upgrade |
| Bitbucket rather than GitHub | Yes, in beta — treat a beta as a pilot, not a migration target |
| Developers switching browser tabs to track changes | Yes — DX Inspector surfaces tracking and commit inside the org |
| Coding agents committing without review | Yes — governance policies cover agents as well as users |
| Non-source-tracked environments in the pipeline | Yes — flexible environment support |
| Nothing; the current pipeline works | No — stay, and revisit when one of the above becomes true |

Then check the constraints before committing: Professional Edition with API
access or higher, Lightning Experience, and availability — Government Cloud Plus
and the EU Operating Zone are excluded. An org in either of those is not
choosing.

**Why it works:** It converts a version-number question into a blocker question.
It also surfaces the case that most teams are in — nothing is blocked — where
the correct answer is to do nothing and keep the option.

---

## Anti-Pattern: Treating DevOps Center as Optional for Half the Team

**What practitioners do:** Roll DevOps Center out to the admins and leave the
developers on their existing branch-and-deploy workflow, on the theory that the
developers already have a working process.

**What goes wrong:** The repository now has two writers with different notions of
what a branch means. Work-item branches contain the admins' changes; ad-hoc
feature branches contain the developers'. Both merge into the same pipeline
branches. Promotion order becomes non-deterministic, and the org's state stops
being derivable from any single artifact — which is the one property the whole
exercise was supposed to buy.

**Correct approach:** Everyone promotes through work items. Developers keep every
tool they already use — the CLI, local test runs, their editor — and simply
commit to the work item's branch instead of one they created. If a category of
work genuinely does not fit the work-item model, that is a scoping decision to
make explicitly and document, not a per-developer opt-out.

---

## Anti-Pattern: Keeping Every Work Item Forever

**What practitioners do:** Close work items and leave them in place, on the
reasonable-sounding basis that they are the audit trail.

**What goes wrong:** The list becomes unusable long before it becomes large. The
people who need to find an in-flight item are filtering past years of completed
ones, and the branches those items created linger in the repository, so `git
branch -r` stops being informative too. The audit value people are protecting is
mostly in the commits and the pull requests, which persist independently of the
work item record.

**Correct approach:** Decide a retention window deliberately and write it down —
what closes, when, and what is preserved. Keep the commit history and the
promotion record; retire the work item from the working view. Delete the merged
branches on a cadence. The important part is that the decision is explicit,
because the default is accretion.

---

## Anti-Pattern: Making the Bypass the Normal Path

**What practitioners do:** Use the emergency direct-deploy for anything urgent,
where "urgent" gradually expands from Sev-1 to "the customer is asking."

**What goes wrong:** Reconciliation is skipped because it always feels optional
in the moment. The repository and production diverge one change at a time. The
first symptom is a normal promotion reverting something that was working, and by
then nobody remembers which of the last twenty bypasses introduced the
divergence.

**Correct approach:** Instrument the bypass. Count it, review the count monthly,
and treat a non-decreasing rate as a defect in pipeline latency rather than a
fact about the business. Every bypass carries a mandatory reconciliation task
that cascades the change down the pipeline, and the task is not optional even
when the change is trivial.
