# Gotchas — Salesforce Release Preparation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Sandbox Preview Enrollment is Per-Sandbox and Irreversible for the Release Cycle

**What happens:** Once a sandbox is enrolled in the preview program and the preview upgrade runs, that sandbox is on the new release version permanently until the next release cycle. There is no rollback option. If development teams are actively using that sandbox when it upgrades to the preview version, they will encounter all new release behaviors — including any breaking changes — before the team is prepared.

**When it occurs:** Any time an admin enrolls a sandbox in preview without confirming it is safe to disrupt. Common failure mode: enrolling the shared integration sandbox or the UAT sandbox being used for a parallel project, then the sandbox upgrades and breaks the in-flight project.

**How to avoid:** Only enroll sandboxes that have no active sprint or UAT work, or that are specifically created for release validation. Communicate to all sandbox users before enrollment. If no suitable sandbox exists, refresh a spare Developer sandbox specifically for preview testing rather than enrolling a shared environment.

---

## Gotcha 2: Release Update Auto-Activation Fires Without User-Visible Warning

**What happens:** When a Release Update's auto-activation date arrives and the update has not been manually toggled by the admin, Salesforce activates it automatically. There is no system notification, banner, or email sent to admins or users when auto-activation fires. The only visible change is that the update's status in Setup > Release Updates moves to "Enforced." If no one is monitoring, the behavior change is live in production before anyone on the team knows it happened.

**When it occurs:** When admins treat the enforcement deadline as an informational date rather than a hard deadline requiring action. Also occurs when admins rotate and the incoming admin is unaware of pending enforcement dates.

**How to avoid:** Document all enforcement dates in the release readiness checklist at the start of the preparation cycle. Set calendar reminders two weeks and one week before each enforcement date. Best practice: activate updates in production manually well before the auto-activation date, after sandbox validation, so the timing is deliberate and monitored.

---

## Gotcha 3: The Upgrade Date Shown in Release Notes is Not Your Org's Upgrade Date

**What happens:** Salesforce publishes a general release schedule with a range of upgrade weekends. The specific upgrade date for a given org depends on its instance (e.g., NA1, NA100, EU15, AP10). Admins who reference the first date in the release calendar assume their org upgrades that weekend, when in fact it may be two or three weekends later — or earlier. This miscalculation shortens or extends the actual preparation window.

**When it occurs:** When teams plan their preparation timeline against the first published upgrade date in the release calendar rather than looking up their specific instance.

**How to avoid:** Navigate to trust.salesforce.com, find the org's instance under Planned Maintenance, and read the specific upgrade date for that instance. Alternatively, check Setup > Release Updates for the org-specific upgrade timeline. Treat this lookup as Step 1 of every release preparation cycle, not an optional detail.

---

## Gotcha 4: Feature Impact Filter Does Not Surface All Developer-Impacting Changes

**What happens:** Some release changes that affect Apex compilation, API version behavior, or governor limit calculations are categorized as "Admin" in the Feature Impact filter because they require configuration to trigger, even though they may also require code changes to resolve. Filtering only on "Developer" misses these, and filtering only on "Admin" causes them to be routed to the wrong owner.

**When it occurs:** When the triage process assigns items rigidly by the Feature Impact label without the admin reading the item description. For example, a change to how Apex-invoked Flows handle null returns may be labeled "Admin" because it is toggle-on, but the fix may require a developer to update calling Apex code.

**How to avoid:** When triaging Admin-tagged items, check whether the description mentions Apex, Visualforce, LWC, API version, or integration behavior. If it does, add the developer as a co-owner regardless of the Feature Impact label.

---

## Gotcha 5: Release Updates Can Have Different Enforcement Dates Across Orgs

**What happens:** Salesforce occasionally rolls out enforcement of Release Updates on a phased schedule — some org editions, instances, or configurations receive enforcement on different dates. An admin who researches the enforcement date on a community forum or Trailhead blog may see a date that does not apply to their specific org.

**When it occurs:** When teams use community-reported enforcement dates as the source of truth instead of checking Setup > Release Updates in their own org, which shows the enforcement date specific to that org.

**How to avoid:** Always read the enforcement date directly from Setup > Release Updates in the org being prepared, not from external summaries. The date shown in that screen is the authoritative date for that specific org and instance.
