# Examples — Flow Versioning Strategy

Worked examples for deciding between a new version and a new flow, draining
paused interviews safely, and getting the inventory you need before either.

Where these examples query, they name the API explicitly. This trips people up
constantly, so it is worth stating once:

| What you want | Object | API |
|---|---|---|
| Flow versions, their status, their definition | `Flow` | **Tooling API** — not standard SOQL |
| Which version is active, per definition | `FlowDefinition` (metadata) / `FlowDefinitionView` | Metadata API / standard |
| Version metadata, read-only, standard API | `FlowVersionView` | Standard (API 46.0+) |
| Live and paused interviews | `FlowInterview` | Standard |

Running a `Flow` query through the standard API and getting "sObject type 'Flow'
is not supported" is the single most common first stumble in this domain.

---

## Example 1: Non-Breaking Change — New Version

**Context:** `Customer_Onboarding` is at version 12, active. The change adds an
optional input variable `partnerAccountId` with a default of null.

**Problem:** Deciding whether this is a version bump or a new flow, and knowing
what happens to the interviews already in flight.

**Solution:**

```text
1. Diff v13 against v12 on the contract surface:
     - inputs added?          yes, optional with a default  -> non-breaking
     - inputs removed?        no
     - outputs changed shape? no
     - element removed that a paused interview could be sitting on?  no
2. Activate v13. v12 becomes Obsolete automatically — activation is
   one-active-version-per-definition.
3. Paused interviews that started on v12 continue to resume on v12.
     Do NOT delete v12.
4. Drain: monitor until no interview references v12, then delete it.
```

**Why it works:** The contract surface — inputs, outputs, and the elements a
paused interview can be sitting on — is what a version bump has to preserve.
Everything else (labels, formulas, added branches on paths no paused interview
occupies) is safely versionable.

**The step that gets skipped:** step 3. Obsolete does not mean unused, and
deleting an obsolete version with live paused interviews breaks them at resume,
not at delete time. The failure arrives weeks later and looks like a data
problem.

---

## Example 2: Breaking Change — New Flow, Not a New Version

**Context:** Same flow. The change renames `customerId` to `accountId`
throughout, and reorders two screens so a paused interview's current element no
longer exists.

**Problem:** A version bump cannot express this. A paused interview resumes on
the version it started on, so v13's paused interviews are fine — but every
*caller* (Apex, LWC, another flow, an OmniScript, a quick action) that passes
`customerId` breaks on the next invocation, and there is no compile step to
catch it.

**Solution:**

```text
1. Inventory the callers BEFORE deciding.
     grep -rn "Customer_Onboarding" force-app/
     grep -rn "customerId" force-app/main/default/flows/
   Callers to check by hand: Apex (Flow.Interview.createInterview),
   LWC (lightning-flow with inputVariables), other flows (<subflows>),
   quick actions, Lightning page targets, Experience Cloud pages.
2. Create Customer_Onboarding_V2 as a NEW flow.
3. Repoint new traffic at V2 caller by caller.
4. Let Customer_Onboarding drain: no new starts, existing paused interviews
   resume on the version they started on.
5. Retire Customer_Onboarding only after the drain completes.
```

**Why it works:** A new flow gives both contracts a place to exist
simultaneously, which is what makes the cutover incremental instead of a big
bang. The old flow keeps working for everything that has not moved.

**The rule, stated as a test:** if anything outside the flow has to change at
the same moment the flow changes, it is a new flow. If the change is invisible
from outside, it is a new version.

---

## Example 3: Wrong vs Right — Rollback

**Wrong:**

```bash
# Redeploy the source of the previous version.
git checkout v12-tag -- force-app/main/default/flows/Customer_Onboarding.flow-meta.xml
sf project deploy start --metadata "Flow:Customer_Onboarding" --target-org prod
```

This does not restore v12. Deploying flow metadata creates a **new version** —
v14 — whose content happens to match v12. The org now has v12 (obsolete), v13
(the bad one, obsolete), and v14 (active, a copy of v12). Version numbers no
longer mean anything to whoever debugs this next, and the error emails from the
incident reference a version number that is now two versions behind the active
one.

**Right — activate the version that already exists:**

The direct route is the UI: the flow's detail page lists every version with an
Activate link. One click, no deploy, no new version. That is the fastest
rollback available on the platform and it is why capturing the pre-deploy active
version number matters — it is the only thing the rollback needs.

The scriptable route is `FlowDefinition` metadata, with a caveat:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <activeVersionNumber>12</activeVersionNumber>
</FlowDefinition>
```

Deploying that sets version 12 active. The field's documentation says exactly one
thing about it — "The version number of the active flow" — so use it to point at a
version, not to express anything else.
<!-- UNVERIFIED: `activeVersionNumber` = 0 is widely reported to deactivate a
flow, but meta_flowdefinition.htm states no behaviour for 0. This rollback pattern
does not need it: to take the flow off, deactivate on the flow's detail page or
deploy the version with <status>Draft</status>. -->

**The caveat, in Salesforce's own words** — quoted rather than paraphrased,
because the paraphrase in circulation says something different: "In API version
44.0, we recommend upgrading your flows to flow metadata file names without
version numbers and discontinue using the FlowDefinition object to activate or
deactivate a flow." Read it carefully. It is a recommendation made *in* API
version 44.0, and its content is (a) drop version numbers from flow metadata file
names and (b) stop using `FlowDefinition` for activation in favour of the `Flow`
object's `status`. It is **not** advice to upgrade your flows *to* API version
44.0 — a flow's API version is a separate decision with separate consequences (see
the breaking-change list in `SKILL.md`). And when a deployment contains both, "the
active version numbers in the flow definitions override the status fields in the
flows" — so a stray `FlowDefinition` in the package silently wins over every
`status` you carefully set. If you use `FlowDefinition` for rollback, know that
you are using a discouraged mechanism deliberately, and keep it out of routine
deployment packages.

**Either way, do not delete the bad version.** v13 is the evidence. Keeping it
also keeps forward-fix available.

---

## Example 4: The Inventory Queries You Actually Need

**Context:** Before any cleanup, you need to know what exists and what is holding
a reference.

**Versions and their status — Tooling API:**

```bash
sf data query \
  --use-tooling-api \
  --target-org prod \
  --query "SELECT Id, MasterLabel, VersionNumber, Status, ProcessType, LastModifiedDate \
           FROM Flow \
           WHERE Definition.DeveloperName = 'Customer_Onboarding' \
           ORDER BY VersionNumber DESC"
```

`Status` values on a flow version are `Active`, `Draft`, `Obsolete`,
`InvalidDraft`, and `UnderReview` — the same five-value enumeration the `Flow`
metadata type's `status` field uses. A `WHERE Status != 'Active'` filter is
therefore safer than enumerating the inactive values by hand, which is how
`UnderReview` rows go missing from cleanup inventories.

**Which version is active, and how many versions exist — standard API:**

```bash
sf data query \
  --target-org prod \
  --query "SELECT DurableId, ApiName, Label, ActiveVersionId, LatestVersionId, \
                  ProcessType, TriggerType, IsActive, LastModifiedDate \
           FROM FlowDefinitionView \
           ORDER BY LastModifiedDate DESC"
```

`FlowDefinitionView` and `FlowVersionView` are read-only standard-API views
(available from API 46.0) and are the right choice for a reporting or
CI-inspection script that should not need the Tooling API.

**Interviews still holding a reference — standard API:**

```bash
sf data query \
  --target-org prod \
  --query "SELECT Id, InterviewLabel, CurrentElement, PauseLabel, CreatedDate, OwnerId \
           FROM FlowInterview \
           ORDER BY CreatedDate ASC"
```

`InterviewLabel` is the practical filter here: it embeds the flow's API name and
version number, which is what lets you answer "does anything still reference
version 12?" — a filter Salesforce's own guidance points people at.
`<!-- UNVERIFIED: the full FlowInterview field list, including whether an
InterviewStatus or IsPaused field exists and what its values are, was not
confirmed against the Object Reference during authoring — the reference pages
would not render. Confirm the field set with `sf sobject describe --sobject
FlowInterview` against a real org before scripting against it. -->`

**The UI equivalents, which are often faster:** Setup → **Paused And Failed Flow
Interviews** for interview state, and the flow's own detail page for the version
list.

---

## Example 5: A Drain Plan With a Real Number In It

**Context:** A screen flow with a Pause element used by field staff who
frequently abandon a session and resume the next day. The team wants a cleanup
rule.

**Problem:** "Delete versions older than 30 days" is the rule everybody writes
and it is measured from the wrong event. A version's age is irrelevant; what
matters is whether anything still points at it.

**Solution:** Derive the retention window from observed interview lifetime.

```text
1. Measure. Query FlowInterview ordered by CreatedDate ascending and look at
   the oldest still-live interview per flow. Do this over a few weeks, not once
   — the tail is what you are trying to size.
2. Set the window to the observed p99 lifetime plus a margin, per flow.
   A screen flow with an overnight pause and a scheduled flow with a 90-day
   wait have wildly different windows; one org-wide number is wrong for both.
3. Encode the window as a check, not a calendar rule:
     "delete version N only when zero interviews reference it"
   Age is a heuristic for that condition, never a substitute.
4. Keep at least three inactive versions regardless of the window, as rollback
   depth.
5. Alert on the oldest live interview age. A long tail is a signal that
   something is stuck, not just that people are slow.
```

**Why it works:** It replaces a rule that is wrong in both directions —
deleting versions that are still in use, and keeping versions nothing has
referenced in a year — with a condition that is checkable.

**The ceiling that makes this urgent rather than aesthetic:** the maximum number
of versions per flow is 50. Hit it and you cannot create a new version at all
until you delete old ones — which is a terrible time to be reasoning carefully
about which ones are safe to delete. Capping at 10 by policy leaves the decision
somewhere calm. Salesforce puts the number in the failure itself — "Maximum
number of Versions per flow is 50" — which is the citation to use.
`<!-- PARTIALLY VERIFIED: 50 is corroborated by the Visual Workflow Implementation
Guide's limits table and by that save-error text. Not confirmed: whether the
current General Flow Limits page restates it, because help.salesforce.com is a
Lightning SPA that fetchers cannot read. Two neighbouring figures on the legacy
page (2,000 executed elements, 500 active flows) are stale, so quote the error
message rather than that page. -->`

---

## Example 6: A Changelog Entry That Answers the Right Questions

```text
### Flow: Quote_Approval
- From:      v7 (active in prod since 2026-06-02)
- To:        v8 (this PR)
- Change:    split the "Qualify" decision into two outcomes
- Breaking?  NO — no input or output change; no element removed that a paused
             interview can occupy (the split is downstream of the only Pause).
- Callers:   QuoteApprovalController.cls, quoteApprovalCard LWC — neither
             touched; verified by grep for "Quote_Approval".
- Paused:    3 interviews live on v7 at time of writing; longest-running is
             4 days. Retain v7 until zero.
- Rollback:  activate v7 from the flow detail page. No redeploy.
- Retire v6: after v8 has been active 30 days AND zero interviews reference v6.
```

**Why this shape:** every line answers a question somebody will ask during an
incident. "Breaking?" with a reason, not a yes/no. "Callers" with the evidence,
not an assertion. "Rollback" naming the version number, because that is the only
input the rollback needs. A changelog that omits the paused-interview count is
missing the one fact that decides whether the cleanup step is safe.

---

## Anti-Pattern: Treating a Breaking Change as a Version Bump

**What practitioners do:** Rename a required input variable, bump the version,
activate, and move on — because Flow Builder let them.

**What goes wrong:** Nothing at authoring time. Nothing at activation. The
failure lands on the next invocation from each caller, one at a time, spread over
however long it takes each caller to run. Apex callers throw at run time; LWC
callers fail to launch the flow; a parent flow's subflow input assignment silently
maps to nothing. There is no compile step over this surface and no deploy-time
warning.

**Correct approach:** apply the test from Example 2 — if anything outside the
flow has to change at the same moment, it is a new flow. Inventory the callers
first, and treat that inventory as part of the change, not as verification
afterwards.

---

## Anti-Pattern: Cleanup by Calendar

**What practitioners do:** Script "delete all flow versions older than 30 days"
and schedule it.

**What goes wrong:** It deletes versions that paused interviews still reference,
breaking them at resume — days or months later, with no connection back to the
cleanup job. It simultaneously fails to delete versions nothing has referenced in
a year, because they happen to be recent. Both errors, from one rule.

**Correct approach:** the condition is "zero interviews reference this version,"
and age is at best a cheap pre-filter for it. Keep three inactive versions as
rollback depth regardless. Cap total versions well below the platform maximum so
that the decision is never made under pressure.

---

## Anti-Pattern: Assuming a Subflow Is Pinned

**What practitioners do:** Activate a new version of a shared subflow, treating
it as a local change to that flow.

**What goes wrong:** Subflow version resolution is late, not early. The parent
holds a reference to the child *flow*, not to a pinned version — so activating a
new child version changes the behaviour of every already-active parent on its
next interview, with no redeploy and no re-activation of the parent. The blast
radius is invisible from the child's own screen.

**Correct approach:** search the metadata for `<flowName>` references to the
child before activating a new version, and treat the activation as a production
change to every caller found. Note the fallback trap too: deactivating a child
flow does not stop callers — it drops them onto the latest version, which may be
an unfinished draft. Deleting the version is the only way to make it
unreachable, and the paused-interview rule still applies to that deletion.
