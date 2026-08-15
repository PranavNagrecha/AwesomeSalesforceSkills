# Examples — Flow Deployment & Activation Ordering

Worked examples for deploying flows without deactivating the wrong thing,
stranding an interview, or discovering at rollback time that you did not record
what was running.

**The one asymmetry that explains most of this domain:** deploying a flow always
creates a *new version*. It never restores an old one. Activation, by contrast,
is a pointer into versions that already exist in the org. Deploy and activate are
different operations with different rollback properties, and conflating them is
the root of nearly every incident here.

---

## Example 1: Capture the Pre-State — the Whole Rollback Plan

**Context:** A release changes four flows in production.

**Problem:** Rollback for a flow is "activate the version that was active
before." That requires knowing which version that was, per environment, and
nothing in the repository records it — activation is org state, not source state.

**Solution:** Make the capture a pipeline step, not a habit.

```bash
#!/usr/bin/env bash
# pre-deploy-capture.sh <target-org> <release-tag>
set -euo pipefail
ORG="$1"; TAG="$2"

sf data query \
  --target-org "$ORG" \
  --result-format csv \
  --query "SELECT ApiName, Label, ActiveVersionId, LatestVersionId, IsActive, \
                  ProcessType, TriggerType, LastModifiedDate \
           FROM FlowDefinitionView" \
  > "artifacts/${TAG}-${ORG}-flow-pre-state.csv"

# Version NUMBERS (not Ids) require the Tooling API.
sf data query \
  --use-tooling-api \
  --target-org "$ORG" \
  --result-format csv \
  --query "SELECT Definition.DeveloperName, VersionNumber, Status, LastModifiedDate \
           FROM Flow \
           WHERE Status = 'Active'" \
  > "artifacts/${TAG}-${ORG}-flow-active-versions.csv"
```

**Why it works:** `FlowDefinitionView` is a read-only standard-API view (API 46.0
and later), so a CI job needs no Tooling API access for the first query. The
second query needs the Tooling API because `Flow` — the object that holds version
numbers and their `Active` / `Draft` / `Obsolete` / `InvalidDraft` /
`UnderReview` status — is a
Tooling API object. Running it through the standard API returns "sObject type
'Flow' is not supported," which is most people's first stumble here.

**Also capture, before you deploy:** the interviews that will pin old versions.

```bash
sf data query --target-org "$ORG" --result-format csv \
  --query "SELECT Id, InterviewLabel, CurrentElement, PauseLabel, CreatedDate \
           FROM FlowInterview ORDER BY CreatedDate ASC" \
  > "artifacts/${TAG}-${ORG}-paused-interviews.csv"
```

`InterviewLabel` embeds the flow's API name and version number, which is what
lets you answer "does anything still reference version 7?" without a field you
have to guess at.

---

## Example 2: Wrong vs Right — Deploying a Flow as Inactive

**Wrong:**

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <label>Quote Approval</label>
    <status>Obsolete</status>
    ...
</Flow>
```

`Obsolete` is not "inactive, ready to activate." It is the status the platform
assigns to a version that *used* to be active and has been superseded. Deploying
a brand-new version as `Obsolete` produces a version that reads, to anyone
inspecting the org later, as a retired version rather than a pending one — and it
is a poor signal to the next person deciding what is safe to delete.

**Right:**

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <label>Quote Approval</label>
    <status>Draft</status>
    ...
</Flow>
```

Deploy as `Draft`, verify, then activate as a separate step. The `status` field
has five valid values — `Active`, `Draft`, `Obsolete`, `InvalidDraft`, and
`UnderReview` — and only the first two are things you choose deliberately. The
rest are platform-assigned states, and their UI labels differ from their API
values: `Draft` and `Obsolete` both display as *Inactive*, `InvalidDraft` displays
as *Draft*, and `UnderReview` displays as *Under Review*.

**The activation step, and its caveat:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <activeVersionNumber>8</activeVersionNumber>
</FlowDefinition>
```

The value is the version number you want live. `meta_flowdefinition.htm` documents
the field as, in full, "The version number of the active flow."
<!-- UNVERIFIED: `activeVersionNumber` = 0 is widely reported to deactivate a
flow, and it may well work, but the field's documentation states no behaviour for
0. Nothing on this page depends on it. To take a flow off, deactivate on the
flow's detail page or deploy the version with <status>Draft</status>. -->

In Salesforce's own words — quoted exactly, because this one is routinely
paraphrased into something it does not say: "In API version 44.0, we recommend
upgrading your flows to flow metadata file names without version numbers and
discontinue using the FlowDefinition object to activate or deactivate a flow."
That is a recommendation made *in* API version 44.0, about file naming and about
retiring `FlowDefinition` in favour of the `Flow` object. It is not advice to move
your flows *to* API version 44.0. And the precedence rule matters: when a
deployment carries both, "the active version numbers in the flow definitions
override the status fields in the flows."

So: prefer `<status>Active</status>` on the `Flow` for normal deployment, and
reach for `FlowDefinition` only when you specifically need to point at an
*existing* version number — which is exactly the rollback case in Example 4. Do
that as a standalone deployment. A stale `FlowDefinition` left in a package
directory silently overrides every `status` in it, which is a genuinely nasty way
to lose an afternoon.

---

## Example 3: Deploying a Subflow and Its Caller Together

**Context:** `Onboarding_Main` calls subflow `Address_Capture`. Both change in
this release.

**Problem:** Subflow version resolution is late. The parent holds a reference to
the child flow, not to a pinned version — it runs whatever version of the child
is active at the moment the interview runs. If the caller activates first, there
is a window in which the new caller runs against the old child. If the child is
deployed but left with no active version, callers silently fall through to the
*latest* version, which may be the draft you just deployed and have not tested.

**Solution:** Deploy both as `Draft`, then activate child-first.

```bash
# 1. Deploy both new versions inactive.
sf project deploy start \
  --metadata "Flow:Address_Capture" --metadata "Flow:Onboarding_Main" \
  --target-org prod --test-level RunLocalTests --wait 60
#    (both files carry <status>Draft</status>)

# 2. Verify the child in isolation — run it from Setup, or via a
#    throwaway parent in a sandbox with the same version.

# 3. Activate the child.
sf project deploy start --metadata "FlowDefinition:Address_Capture" \
  --target-org prod --wait 30

# 4. Activate the caller.
sf project deploy start --metadata "FlowDefinition:Onboarding_Main" \
  --target-org prod --wait 30
```

**Why the order is child-then-parent:** between steps 3 and 4 the *old* caller
runs against the *new* child, which is the compatible direction if the child's
change is backward-compatible. Activating the parent first would put the new
caller against the old child, which is the direction that breaks when the caller
depends on something new in the child.

**If the child's change is not backward-compatible, this ordering does not save
you.** There is no atomic activation across two flows. A breaking child change
needs a new child flow with a new API name and a caller repoint — that is a
versioning decision, and `flow/flow-versioning-strategy` owns it.

---

## Example 4: Rollback Without Creating a New Version

**Context:** Version 12 activated at 09:00 and is throwing at run time.

**Wrong:**

```bash
git checkout release-11 -- force-app/main/default/flows/Quote_Approval.flow-meta.xml
sf project deploy start --metadata "Flow:Quote_Approval" --target-org prod
```

This does not restore version 11. It creates version **13**, whose content
matches 11. The org now has 11 (obsolete), 12 (the bad one, obsolete), and 13
(active, a copy of 11). Version numbers have stopped meaning anything, and every
error email from the incident references version 12 while the active version is
13 — which is precisely the confusion the next responder does not need.

**Right — fastest path:** the flow's detail page lists every version with an
Activate link. One click. No deploy, no new version, no test run.

**Right — scriptable path:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <activeVersionNumber>11</activeVersionNumber>
</FlowDefinition>
```

```bash
sf project deploy start --metadata "FlowDefinition:Quote_Approval" \
  --target-org prod --wait 30
```

This is the case where `FlowDefinition` earns its place despite the general
recommendation against it: pointing at an existing version number is the one
thing `Flow.status` cannot express.

**Do not delete version 12.** It is the evidence, and keeping it preserves the
forward-fix path. Deleting it also risks the paused-interview problem in Example
5.

**Rollback also does not undo everything.** If the bad version already committed
records, published platform events, or enqueued scheduled paths, activating the
old version stops future damage and repairs none of the past. Data remediation is
a separate plan and it should be written before the deploy, not after the
incident.

---

## Example 5: Deploying Around Paused Interviews

**Context:** A screen flow with a Pause element used by field staff who resume
the next day. Sixty interviews are live at deploy time.

**Problem:** A paused interview resumes on the version it started on. The deploy
itself is safe — the old version stays in the org. The *cleanup* is what breaks
them, and it usually happens weeks later in a different change, so nobody
connects the failure to the deploy.

**Solution:** Treat retention as an output of the deploy, not a separate hygiene
task.

```text
Pre-deploy:
  1. Snapshot FlowInterview (Example 1). Note the oldest CreatedDate for
     this flow's versions.
  2. Record: "Do not delete Quote_Approval v11 until zero interviews
     reference it. Oldest live interview at deploy: 2026-08-11."

Post-deploy:
  3. Re-run the interview query weekly. Delete v11 only when the count
     for v11 reaches zero.
  4. If the count is not falling, the interviews are stuck, not slow.
     Investigate before deleting.

Never:
  - "Delete versions older than 30 days." Measured from the wrong event,
    it deletes versions that are still in use and keeps ones nothing has
    touched in a year.
```

**Why it works:** the retention rule is a checkable condition rather than a
calendar. And since Spring '24 there is no platform cap on how many paused and
waiting interviews an org accumulates, so this population grows quietly and will
not self-limit.

**Deleting a flow that still has interviews** fails, sometimes with an opaque
server error rather than a clear message. Clear the interviews first from Setup →
**Paused And Failed Flow Interviews**; deleting a `FlowInterview` requires the
Manage Flow user permission, and for volume use Data Loader or Workbench against
the `FlowInterview` object.

---

## Example 6: The Org Preference That Changes What "Deploy as Active" Means

**Context:** A deploy that activates a flow fails in production with a coverage
error, having worked in every sandbox.

**Problem:** There is an org preference governing whether processes and
autolaunched flows can be deployed as active, and it carries a test-coverage
requirement. It is **not available in developer, sandbox, or other non-production
orgs** — because there you can always deploy a new active version. So the
constraint is structurally invisible until production.

**Solution:**

Setup → Quick Find `Automation` → **Process Automation Settings** → **Deploy
processes and flows as active** → enter the flow test coverage percentage → Save.

Then know its edges:

- It applies to processes and autolaunched flows deployed via change sets and the
  Metadata API.
- At least one Apex test must cover the configured percentage of active processes
  and autolaunched flows.
- **Flow test coverage requirements do not apply to flows that have screens.**
- Because the setting does not exist in sandboxes, a green sandbox deploy is not
  evidence the production deploy will pass.

**Why it works:** it converts a production-only surprise into a pre-release
check. Verify the setting and the current coverage in production as part of
release readiness, not as part of the deploy.

---

## Example 7: Post-Deploy Verification That Would Actually Catch a Failure

**Context:** The deploy reported success. That is a statement about metadata
being saved, not about the right version being active or the flow working.

**Solution:**

```bash
#!/usr/bin/env bash
# post-deploy-verify.sh <target-org> <release-tag>
set -euo pipefail
ORG="$1"; TAG="$2"

# 1. Re-query and diff against the pre-state.
sf data query --target-org "$ORG" --result-format csv \
  --query "SELECT ApiName, ActiveVersionId, LatestVersionId, IsActive \
           FROM FlowDefinitionView" \
  > "artifacts/${TAG}-${ORG}-flow-post-state.csv"

diff "artifacts/${TAG}-${ORG}-flow-pre-state.csv" \
     "artifacts/${TAG}-${ORG}-flow-post-state.csv" || true

# 2. Anything active that should not be, or inactive that should be?
sf data query --use-tooling-api --target-org "$ORG" \
  --query "SELECT Definition.DeveloperName, VersionNumber, Status \
           FROM Flow WHERE Status = 'Active'"
```

Then the three checks a script cannot make:

1. **Run one real interview** of each changed flow through its actual entry
   point. A deploy that succeeded and a flow that works are different claims.
2. **Watch flow error email volume** for the next few hours. A step change is the
   earliest signal of a version that deploys cleanly and fails at run time.
3. **Check the scheduled and async queues** — Setup → **Environments** →
   **Monitoring** → **Time-Based Workflow** — for entries that should have drained
   and have not.

**The diff in step 1 is the load-bearing part.** It catches the case nobody
anticipates: a flow that was not in this release changing its active version,
usually because a `FlowDefinition` was in the package or a managed package upgrade
moved it.

---

## Anti-Pattern: Rolling Back by Redeploying Old Source

**What practitioners do:** Check out the previous release tag and deploy the
flow's metadata.

**What goes wrong:** It creates a new version rather than restoring the old one.
The org accumulates a copy, the version numbers stop corresponding to anything
meaningful, and every artifact from the incident — error emails, log rows,
interview labels — references a version number that is now behind the active one.
It is also slower, because it runs tests.

**Correct approach:** activate the version that already exists, from the flow's
detail page or via a standalone `FlowDefinition` deployment. Capture the
pre-deploy active version number so you know which one that is. Keep the bad
version.

---

## Anti-Pattern: Mass-Deleting Old Versions as Cleanup

**What practitioners do:** Script "delete flow versions older than N days" and
schedule it.

**What goes wrong:** Paused interviews pin to their version. The delete succeeds;
the interviews fail at resume, weeks or months later, with no traceable link back
to the cleanup job. The same rule simultaneously fails to remove versions nothing
has referenced in a year, because they happen to be recent.

**Correct approach:** the condition is "zero interviews reference this version."
Age is at best a cheap pre-filter for it. Retain three inactive versions as
rollback depth regardless, and cap total versions by policy so the pruning
decision is never made in response to a failed save.

---

## Anti-Pattern: Deploying Caller and Callee in Alphabetical Order

**What practitioners do:** Let the tooling deploy whatever order it likes,
because a single deploy is atomic.

**What goes wrong:** The *deploy* is atomic; the *activation* is not, when
activation is a second step. And subflow resolution is late — the parent runs
whatever child version is active at interview time. Getting the activation order
backwards puts the new caller against the old child during the window between the
two activations. Worse, a child deployed with no active version does not stop
callers; it drops them onto the latest version, which may be the untested draft.

**Correct approach:** deploy both as `Draft`, verify the child, activate the
child, then activate the caller. And recognise the limit of the technique: for a
breaking child change there is no ordering that helps, and the answer is a new
child flow with a caller repoint.
