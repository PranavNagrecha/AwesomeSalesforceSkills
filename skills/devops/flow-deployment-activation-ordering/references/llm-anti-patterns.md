# LLM Anti-Patterns — Flow Deployment & Activation

Mistakes AI assistants reliably make when writing a flow deployment or rollback
procedure.

---

## Anti-Pattern 1: Rollback by Redeploying Prior Source

**What the LLM generates:** "to roll back, check out the previous release tag and
deploy the flow metadata."

**Why it happens:** redeploy-the-previous-artifact is the correct rollback for
almost everything else in software delivery, and a flow is a file in the
repository like any other.

**Correct pattern:** deploying a flow *always creates a new version* and never
restores an old one. The org ends up with a copy at a higher version number,
error emails from the incident reference a version that is no longer current, and
the deploy runs tests it did not need to. Roll back by activating the version
that already exists — one click on the flow's detail page, or a standalone
`FlowDefinition` deployment with `activeVersionNumber`.

**Detection hint:** `sf project deploy` and a `Flow` metadata name inside a
rollback procedure.

---

## Anti-Pattern 2: `status` of `Obsolete` to Mean "Inactive"

**What the LLM generates:** `<status>Obsolete</status>` on a newly deployed
version, described as deploying it inactive.

**Why it happens:** the status enumeration reads as an enable/disable pair with
spares, and `Obsolete` sounds more "off" than `Draft`.

**Correct pattern:** there are **five** valid values — `Active`, `Draft`,
`Obsolete`, `InvalidDraft`, and `UnderReview`. `Obsolete` is what the platform
assigns to a version that used to be active and has been superseded. A pending
version deploys as `Draft`. Do not reject `UnderReview` as invalid because a
four-value list left it out, and do not read the API value off the UI label: the
docs note `Draft` and `Obsolete` both appear as *Inactive*, `InvalidDraft` appears
as *Draft*, and `UnderReview` appears as *Under Review*.

**Detection hint:** `<status>Obsolete</status>` in a file being deployed for the
first time; or a "valid values" list of `status` with only four entries.

---

## Anti-Pattern 3: Bundling `FlowDefinition` With `Flow` "For Certainty"

**What the LLM generates:** a package that sets `<status>` on each flow *and*
includes a `FlowDefinition` with `activeVersionNumber`, on the theory that
belt-and-braces is safer.

**Why it happens:** two mechanisms that both express activation look
complementary rather than conflicting.

**Correct pattern:** they conflict, with documented precedence — "the active
version numbers in the flow definitions override the status fields in the flows."
A stale `FlowDefinition` silently wins over every carefully set `status` in the
package. Salesforce recommends discontinuing `FlowDefinition` for activation in
favour of the `Flow` object. Keep it out of routine packages; use it standalone
for rollback.

**Detection hint:** a package containing both a `FlowDefinition` and `Flow`
components with `<status>`.

---

## Anti-Pattern 4: Querying `Flow` Without the Tooling API

**What the LLM generates:** `sf data query --query "SELECT VersionNumber, Status
FROM Flow WHERE ..."` inside a pre-deploy or verification script.

**Why it happens:** `Flow` reads like an ordinary sObject and appears constantly
in documentation. Nothing in the name signals the API boundary.

**Correct pattern:** `Flow` is a Tooling API object; the standard API returns
"sObject type 'Flow' is not supported." Add `--use-tooling-api`, or use
`FlowDefinitionView` (standard, API 46.0+) where the script should not require
Tooling API access — noting that it gives `ActiveVersionId` and `LatestVersionId`
as Ids, not version numbers.

**Detection hint:** `FROM Flow` in a query with no tooling-api flag.

---

## Anti-Pattern 5: Inventing `FlowDefinition.ActiveVersion`

**What the LLM generates:** `<ActiveVersion>11</ActiveVersion>`,
`FlowDefinition.ActiveVersion = 11`, or similar near-miss field names.

**Why it happens:** the concept is "active version" and the model reconstructs a
plausible field name rather than recalling the exact one. Metadata XML does not
always fail loudly on an unrecognised element.

**Correct pattern:** the field is `activeVersionNumber`, an int, documented as
"The version number of the active flow." `FlowDefinition`'s complete field set is
`activeVersionNumber`, `apiVersion` (reserved for internal use), `description`,
and `masterLabel`.
<!-- UNVERIFIED: `activeVersionNumber` = 0 is widely reported to deactivate a
flow, but the field's documentation states no behaviour for 0. Do not assert it
as fact when reviewing; if it matters to the change, confirm it in a sandbox. -->

**Detection hint:** any `FlowDefinition` child element other than those four.

---

## Anti-Pattern 6: Ordering by Dependency but Not by Activation

**What the LLM generates:** "deploy the subflow first, then the caller,"
presented as sufficient, in a single deploy.

**Why it happens:** dependency ordering is the right instinct and half the
answer. The model does not model the deploy/activate split.

**Correct pattern:** a single deploy is atomic, so ordering *within* it changes
nothing. What matters is the order of *activation* when activation is a second
step: deploy both as `Draft`, verify the child, activate the child, then activate
the caller. And for a breaking child change there is no ordering that helps —
resolution is late, activation is not atomic across two flows, and the answer is
a new child flow with a caller repoint.

**Detection hint:** an ordering recommendation that mentions deployment order but
never mentions activation.

---

## Anti-Pattern 7: Treating Deactivation as a Kill Switch

**What the LLM generates:** "deactivate the flow to stop it running while we
investigate."

**Why it happens:** it is the obvious meaning of the word, and it is true for the
flow's own trigger.

**Correct pattern:** two documented ways it fails. A subflow with no active
version does not stop callers — the parent falls through to the *latest* version,
possibly an untested draft. And a flow with Apex callers may still be invocable.
For a real off switch, gate the callers: a Custom Metadata feature flag in the
Apex, or entry criteria in the flow.

**Detection hint:** deactivation offered as the containment step in an incident
runbook for a flow that has subflow or Apex callers.

---

## Anti-Pattern 8: "The Deploy Succeeded, So It Works"

**What the LLM generates:** a procedure that ends at a successful deploy result,
with no post-deploy verification.

**Why it happens:** the deploy command returns a clean success/failure, which is
exactly what a verification step wants.

**Correct pattern:** deploy success means metadata was saved. It does not mean
the intended version is active, that no *other* flow's active version moved, or
that the flow works. Diff `FlowDefinitionView` pre and post, run one real
interview of each changed flow through its actual entry point, and watch flow
error email volume for a step change. The diff is the part that catches the
surprise nobody anticipated — including a managed package upgrade moving a flow
you did not touch.

**Detection hint:** a deployment runbook with no post-deploy query.

---

## Anti-Pattern 9: Assuming Rollback Undoes the Data

**What the LLM generates:** "activate the previous version to roll back the
change," with no data-remediation step.

**Why it happens:** rollback in most systems restores state, and the word carries
that connotation.

**Correct pattern:** activating an old version changes what runs next and repairs
nothing that already ran. Records the bad version wrote stay wrong; platform
events it published are gone and their subscribers already acted; scheduled paths
it enqueued are still queued. Write the data-remediation plan alongside the
deploy plan, and consider stamping a version or run id on records the flow
touches so remediation is a query rather than a forensic exercise.

**Detection hint:** an incident runbook whose recovery section contains only an
activation step.

---

## Anti-Pattern 10: Ignoring the Production-Only Activation Preference

**What the LLM generates:** a release plan validated entirely in sandboxes, with
production treated as one more environment.

**Why it happens:** environment parity is the goal everywhere else, so the model
assumes it holds.

**Correct pattern:** the org preference controlling whether processes and
autolaunched flows can be deployed as active, and its flow test coverage
percentage, is **not available in developer, sandbox, or other non-production
orgs**. A green sandbox deploy is therefore not evidence the production deploy
will pass. Check the setting and the coverage in production during release
readiness. Note that the coverage requirement does not apply to flows that have
screens.

**Detection hint:** a release plan asserting production parity with sandbox for a
deploy that activates autolaunched flows.
