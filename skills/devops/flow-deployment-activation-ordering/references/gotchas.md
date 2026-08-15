# Gotchas — Flow Deployment & Activation

Non-obvious behaviours that turn a routine flow deploy into an incident.

---

## Gotcha 1: Deploying a Flow Always Creates a New Version

**What happens:** A team "redeploys version 11" and ends up with version 13.

**When it occurs:** Every flow deployment. The Metadata API adds a version; it
never restores one. This is the asymmetry the whole domain turns on — deploy and
activate are different operations with different rollback properties.

**How to avoid:** Roll back by *activating* an existing version, not by
deploying old source. Capture the active version number before every deploy;
it is the entire rollback plan and the repository does not contain it.

---

## Gotcha 2: `FlowDefinition` Overrides `Flow.status` in the Same Deployment

**What happens:** A package sets `<status>` correctly on several flows and one
comes out active when it should not have been — or inactive when it should have
been active.

**When it occurs:** When a `FlowDefinition` component is in the same package. The
precedence is documented: "the active version numbers in the flow definitions
override the status fields in the flows." A stale `FlowDefinition` left in a
package directory silently wins over every `status` in it.

**How to avoid:** quote the recommendation accurately, because the paraphrase
"upgrade flows to API version 44.0" is a different claim from the one Salesforce
makes. The text is: "In API version 44.0, we recommend upgrading your flows to
flow metadata file names without version numbers and discontinue using the
FlowDefinition object to activate or deactivate a flow." It is dated *in* 44.0 and
it is about file naming plus retiring `FlowDefinition` in favour of the `Flow`
object — it says nothing about which API version your flows should target. Keep
`FlowDefinition` out of routine packages.
Use it deliberately and standalone for rollback, where pointing at an existing
version number is exactly the thing `status` cannot express.

---

## Gotcha 3: `Obsolete` Is Not "Inactive, Ready to Activate"

**What happens:** A new version is deployed with `<status>Obsolete</status>` on
the theory that it means "not active yet."

**When it occurs:** Whenever the status enumeration is read as a generic
enable/disable pair. There are five valid values — `Active`, `Draft`, `Obsolete`,
`InvalidDraft`, and `UnderReview` — and `Obsolete` is what the platform assigns to
a version that *used* to be active and has been superseded. Only `Active` and
`Draft` are values you set deliberately.

**How to avoid:** Deploy a pending version as `Draft`. Anything else misleads the
next person deciding which versions are safe to delete.

---

## Gotcha 4: Subflow Resolution Is Late, So Activation Order Matters

**What happens:** A caller and its subflow both deploy successfully, and the
caller misbehaves for a few minutes.

**When it occurs:** The parent holds a reference to the child *flow*, not to a
pinned version — it runs whatever version of the child is active at interview
time. Activating the caller before the child leaves a window in which the new
caller runs against the old child.

**How to avoid:** Deploy both as `Draft`, verify the child in isolation, activate
the child, then activate the caller. And know the technique's limit: activation
is not atomic across two flows, so a breaking child change needs a new child flow
with a caller repoint, not a cleverer ordering.

---

## Gotcha 5: A Child With No Active Version Does Not Stop Callers

**What happens:** A subflow is deactivated to take it out of service, and callers
keep running it — against an untested draft.

**When it occurs:** Salesforce's documented fallback: if a child flow has no
active version, the parent runs the *latest* version. Deactivation removes the
active pointer; it does not remove reachability.

**How to avoid:** Deleting the version is the only way to make it unreachable —
and Gotcha 8 governs that deletion. If a subflow must be taken out of service,
repoint or disable the callers, not the child.

---

## Gotcha 6: `Flow` Is a Tooling API Object

**What happens:** `SELECT VersionNumber, Status FROM Flow` returns "sObject type
'Flow' is not supported," and a verification script silently degrades to
checking nothing.

**When it occurs:** Any standard-API query against `Flow`. Version numbers and
their status live in the Tooling API. The standard API exposes the read-only
views `FlowDefinitionView` and `FlowVersionView` (API 46.0 and later), and live
interviews as `FlowInterview`.

**How to avoid:** Use `--use-tooling-api` for `Flow`; use `FlowDefinitionView`
for anything a CI job should be able to run without Tooling API access. Note that
`FlowDefinitionView` gives you `ActiveVersionId` and `LatestVersionId` — Ids, not
version numbers — so a script that wants "version 11" needs the Tooling API query
as well.

---

## Gotcha 7: "Deploy Processes and Flows as Active" Does Not Exist in Sandboxes

**What happens:** A deploy that activates a flow works in every sandbox and fails
in production on test coverage.

**When it occurs:** The org preference governing whether processes and
autolaunched flows can be deployed as active — with an associated flow test
coverage percentage — is not available in developer, sandbox, or other
non-production orgs, because there you can always deploy a new active version.
The constraint is structurally invisible until production.

**How to avoid:** Check Setup → **Process Automation Settings** → **Deploy
processes and flows as active** and the configured coverage percentage in
production as part of release readiness. Note the shape of the requirement: it
applies to processes and autolaunched flows deployed via change sets and the
Metadata API, and **flow test coverage requirements do not apply to flows that
have screens**.

---

## Gotcha 8: Paused Interviews Break at Resume, Not at Delete

**What happens:** A cleanup deletes old versions. Weeks later, users resuming
long-paused screen flows get errors nobody connects to the cleanup.

**When it occurs:** A paused interview resumes on the version it started on.
Deleting that version breaks it — silently at delete time, visibly at resume
time, with a long gap in between. Since Spring '24 there is no platform cap on
how many paused and waiting interviews an org accumulates, so the population
grows quietly.

**How to avoid:** Gate deletion on "zero interviews reference this version,"
using the `InterviewLabel` field (which embeds the flow API name and version
number) to check. Age is at best a cheap pre-filter. Retain three inactive
versions as rollback depth regardless.

---

## Gotcha 9: Deleting a Flow Can Fail Opaquely

**What happens:** Deleting a flow returns an internal server error rather than a
message naming the blocker.

**When it occurs:** When interviews still reference a version of it. The
presentation is unhelpful enough that teams misdiagnose it as a platform fault
and retry.

**How to avoid:** Clear the interviews first from Setup → **Paused And Failed
Flow Interviews**. Deleting a `FlowInterview` record requires the Manage Flow
user permission; for volume, `FlowInterview` is exposed through the REST and SOAP
APIs, so use Data Loader or Workbench rather than the UI.

---

## Gotcha 10: A Managed Package Upgrade Can Move an Active Version

**What happens:** A flow that was not in this release changes its active version.

**When it occurs:** Installing an updated managed package can change which
version of a packaged flow is active. Nothing in your own release notes mentions
it, because it was not your change.

**How to avoid:** The pre-state / post-state diff from `FlowDefinitionView`
catches exactly this class of surprise. Run it on every deploy and on every
package upgrade, and treat an unexplained row in the diff as a finding rather
than noise.

---

## Gotcha 11: Rollback Stops Future Damage and Repairs Nothing Past

**What happens:** The bad version is rolled back and the incident is declared
closed. Days later, the records it wrote are found to be wrong.

**When it occurs:** Whenever the bad version committed records, published
platform events, or enqueued scheduled paths before it was rolled back.
Activating the previous version changes what runs next; it has no effect on what
already ran. Published events in particular are gone — the subscribers already
acted.

**How to avoid:** Write the data-remediation plan as part of the deploy plan, not
after the incident. For a flow whose failure mode is "writes wrong data," a
reversible field stamp (a version number or run id on the records it touches)
turns remediation from a forensic exercise into a query.

---

## Gotcha 12: A Scheduled Flow Picks Up the Active Version at Run Time

**What happens:** A version is activated at 16:00 and the 02:00 batch behaves
differently from every rehearsal, which was run against the previous version.

**When it occurs:** Scheduled flow runs resolve the active version when they run,
not when the schedule was created. There is no pinning, and rolling back
mid-window means one night's run used one version and the next used another.

**How to avoid:** Treat activating a scheduled flow's version as changing
tonight's batch job. Rehearse against the version you are about to activate.
Prefer activating close to the run, where the rollback window is easy to reason
about, over activating hours ahead.

---

## Gotcha 13: An Inactive Flow Is Not Unreachable From Apex

**What happens:** A flow is deactivated as a kill switch and Apex keeps invoking
it.

**When it occurs:** `Flow.Interview.createInterview` and similar entry points do
not universally require an active version, so "deactivated" is not a reliable
platform-level off switch for a flow with code callers. `<!-- UNVERIFIED: the
exact conditions under which an inactive flow version remains invocable from Apex
were not confirmed against a fetchable official page during authoring. Test the
behaviour in a sandbox before relying on deactivation as a kill switch. -->`

**How to avoid:** Do not use deactivation as the kill switch for a flow with Apex
callers. Gate the caller — a Custom Metadata feature flag checked in the Apex, or
an entry-criteria condition in the flow itself — so the off switch lives
somewhere whose behaviour you have tested.
