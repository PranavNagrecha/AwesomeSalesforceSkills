# Gotchas — Flow Versioning

Non-obvious behaviours in how Salesforce versions, activates, and resolves flows.

---

## Gotcha 1: Paused Interviews Pin to Their Version

**What happens:** An old version is deleted as cleanup. Weeks later, users
resuming long-paused screen flows get errors that have no apparent connection to
anything that changed.

**When it occurs:** A paused interview always resumes on the version it started
on. Deleting that version breaks it — not at delete time, when someone would
notice the causation, but at resume time, which may be months later and looks
like a data problem.

**How to avoid:** Drain before delete. The condition to check is "zero interviews
reference this version," not "this version is old." And note that since Spring
'24 there is no platform cap on how many paused and waiting interviews an org
accumulates, so the population you are draining is unbounded and grows quietly.

---

## Gotcha 2: "Obsolete" Does Not Mean Unused

**What happens:** A cleanup script filters on `Status = 'Obsolete'` and treats
those versions as dead.

**When it occurs:** Always. Activating a new version marks the previous one
Obsolete automatically — it is a statement about which version *starts* new
interviews, not about which versions are running. Obsolete versions continue to
host every paused interview that began on them.

**How to avoid:** Treat Obsolete as "no longer receiving new traffic" and check
the interview population separately. The status enumeration has five values —
`Active`, `Draft`, `Obsolete`, `InvalidDraft`, `UnderReview` — and none of them
means "safe to delete." A cleanup script that enumerates statuses by hand will
also quietly miss whichever value the author forgot; filter on `Status != 'Active'`
and gate deletion on the interview count instead.

---

## Gotcha 3: Subflow Versions Resolve at Run Time, Not at Activation

**What happens:** Activating a new version of a shared subflow silently changes
the behaviour of a dozen parent flows, none of which were touched or redeployed.

**When it occurs:** Always. Salesforce's own wording: "If a child flow has
multiple versions, the parent flow runs the child flow's active version. If a
child flow has no active version, the parent flow runs the latest version." The
parent holds a reference to the child flow, not to a pinned version number.

Two consequences worth planning for:

- A subflow edit is a **production change to every caller**. Search the metadata
  for `<flowName>` references before activating; the blast radius is not visible
  from the child's own screen.
- The "no active version" fallback is the trap. Deactivating a child flow does
  not stop callers — it silently drops them onto the latest version, which may be
  an unfinished, never-activated draft. Deleting the version is the only way to
  make it unreachable, and Gotcha 1 still governs that deletion.

**How to avoid:** Treat shared subflows as published interfaces. Version them
conservatively, inventory the callers before every activation, and prefer a new
subflow over a breaking change to an existing one.

---

## Gotcha 4: Renaming a Variable Breaks Callers With No Compile Step

**What happens:** An input or output variable is renamed. Flow Builder saves
happily. Activation succeeds. Nothing fails until each caller next runs.

**When it occurs:** Any rename on the contract surface. The callers — Apex
`Flow.Interview.createInterview`, `lightning-flow` with `inputVariables`, another
flow's `<subflows>` input assignments, quick actions, Experience Cloud pages —
bind by name at run time. There is no compilation over that surface and no
deploy-time warning.

**How to avoid:** Inventory callers before renaming, by searching the repository
for both the flow's API name and the variable's name. Then decide: if anything
outside the flow has to change at the same moment, it is a new flow, not a new
version.

---

## Gotcha 5: Rollback Is Activation, Not Redeployment

**What happens:** A team rolls back by redeploying the previous version's source
and ends up with three versions where they expected two, and a version number in
the incident's error emails that no longer matches anything active.

**When it occurs:** Every time. Deploying flow metadata creates a **new version**
whose content happens to match the old one. It does not restore the old version.

**How to avoid:** Roll back by activating the version that already exists — the
flow's detail page lists every version with an Activate link, which is one click
and no deploy. Capture the active version number *before* the deploy; it is the
only input the rollback needs. And do not delete the bad version: it is the
evidence, and keeping it preserves the forward-fix path.

---

## Gotcha 6: `FlowDefinition` Overrides `Flow.status` in the Same Deployment

**What happens:** A deployment sets `status` correctly on several flows and one
of them comes out active when it should not have, or inactive when it should
have been active.

**When it occurs:** When a `FlowDefinition` component is present in the same
package. Salesforce documents the precedence explicitly: "the active version
numbers in the flow definitions override the status fields in the flows." A
stale `FlowDefinition` left in a package directory silently wins over every
`status` in it.

**How to avoid:** Salesforce's recommendation, quoted exactly: "In API version
44.0, we recommend upgrading your flows to flow metadata file names without
version numbers and discontinue using the FlowDefinition object to activate or
deactivate a flow." It was made *in* 44.0 and it is about file naming plus
retiring `FlowDefinition` in favour of the `Flow` object's `status` field — it is
not a recommendation to move flows *to* API version 44.0, which is how it is
usually misquoted. Keep `FlowDefinition` out of routine deployment packages. If you use it deliberately for a rollback — where pointing
at an existing version number is exactly what you want — do that as a standalone
deployment, not bundled with other flow changes.

---

## Gotcha 7: `Flow` Is a Tooling API Object

**What happens:** `SELECT VersionNumber FROM Flow` returns "sObject type 'Flow'
is not supported," and the author concludes flow versions are not queryable.

**When it occurs:** Any standard-API query against `Flow`. Flow versions live in
the Tooling API. The standard API exposes the read-only views
`FlowDefinitionView` and `FlowVersionView` (API 46.0 and later), and the live
interviews as `FlowInterview`.

**How to avoid:** Use `--use-tooling-api` for `Flow`, or the `*View` objects for
anything a reporting or CI script should be able to run without Tooling API
access. Knowing which of the four objects answers which question is most of the
skill in this area.

---

## Gotcha 8: There Is a Ceiling on Versions Per Flow

**What happens:** A save fails because the flow has reached its maximum number of
versions, and the team has to decide which historical versions are safe to delete
under time pressure — which is exactly the decision Gotcha 1 says not to make
casually.

**When it occurs:** On heavily iterated flows, especially ones where every
sandbox deploy creates a version. The ceiling is **50 versions per flow** — the
figure in the Visual Workflow Implementation Guide's limits table, and the one
Salesforce puts in the save error itself: "Maximum number of Versions per flow is
50."
`<!-- PARTIALLY VERIFIED: 50 is corroborated by the Implementation Guide table
and by the runtime error text. Not confirmed: whether the current General Flow
Limits page restates it — help.salesforce.com is a Lightning SPA that fetchers
cannot read. Two neighbouring figures on that legacy page (2,000 executed
elements, 500 active flows) are stale, so do not lean on the page for anything
else. -->`

**How to avoid:** Cap the version count by policy well below whatever the
platform ceiling is — ten is a workable number — so that pruning happens on a
calm cadence rather than in response to a failed save.

---

## Gotcha 9: Activation Is Per-Org State, Not Repository State

**What happens:** A team assumes the repository records which version is active
and discovers production and UAT are on different versions with nothing in git
saying so.

**When it occurs:** Always. Activation is org state. The repository holds flow
*source*; which version an org is running is a property of that org.

**How to avoid:** Capture the active version per environment as an explicit
pre-deploy step and store it with the release record. That inventory is
simultaneously the rollback plan (Gotcha 5) and the drift check. Without it,
"what is running in prod?" is only answerable by querying prod.

---

## Gotcha 10: Every Save Can Bump the API Version

**What happens:** A trivial label fix to an old flow changes its runtime
behaviour, sometimes substantially.

**When it occurs:** Flow Builder can move a flow's API version forward when you
open and save it. Flow behaviour is versioned: the removal of the 2,000
executed-elements cap landed at API 57.0, run-mode defaults changed at API 52.0,
and custom scheduled-flow batch sizes require runtime version 63.0. A flow that
crosses one of those boundaries during a cosmetic edit picks up the new
behaviour.

**How to avoid:** Note the API version before and after any edit to a legacy
flow, and treat a bump as a change requiring testing rather than a side effect of
saving. If the flow predates Spring '21, the run-mode default is the one to check
first — see `flow/flow-runtime-context-and-sharing`.

---

## Gotcha 11: A Scheduled Flow Picks Up the Active Version at Run Time

**What happens:** A new version is activated at 16:00 and the 02:00 scheduled run
behaves differently from every rehearsal, which was done against the old version.

**When it occurs:** Scheduled flow runs resolve the active version when they run,
not when the schedule was created. There is no pinning.

**How to avoid:** Treat activating a version of a scheduled flow as changing
tonight's batch job. Rehearse against the version you are about to activate, not
the one currently active, and prefer activating immediately before a run rather
than hours ahead where a rollback window is harder to reason about.

---

## Gotcha 12: Deleting a Flow Can Fail Opaquely

**What happens:** Deleting a flow returns an internal server error rather than a
clear "this is still referenced" message.

**When it occurs:** When interviews still reference a version of it. The
underlying cause is Gotcha 1; the presentation is unhelpful enough that teams
misdiagnose it as a platform fault.

**How to avoid:** Before deleting a flow, open Setup → **Paused And Failed Flow
Interviews**, filter to it, and clear the referencing interviews. Deleting a
`FlowInterview` record requires the Manage Flow user permission, and
`FlowInterview` is exposed through the REST and SOAP APIs — so use Data Loader or
Workbench for volume, because one-at-a-time deletion in the UI does not scale.
