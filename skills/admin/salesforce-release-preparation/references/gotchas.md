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

---

## Gotcha 6: A Release Update's Enforcement Release Can Be Postponed to a Later Release

**What happens:** Salesforce publishes an enforcement release with each Release Update, but that release is not a commitment. When adoption lags, Salesforce pushes enforcement out a cycle. "Restrict User Access to Run Flows" was scheduled to be enforced in Winter '25; Salesforce postponed it and enforced it in Winter '26. Teams that logged the original release, watched it pass without incident, and closed the item as "handled" carried a stale entry into the cycle that actually enforced it. When it did land, the FAQ article states: "The FlowSites org perm is deprecated. A user's ability to run a flow is restricted unless the correct profile or permission set to run the flow is granted." Scope it correctly before acting on it: the restriction covers flows a user launches directly — screen flows and autolaunched flows — which now require **Run Flows** (or **Manage Flow**, which also covers creating, updating, and deleting flows) granted through a profile or permission set. Flows the platform runs on a record's behalf are not in scope; the article lists record-triggered, scheduled-triggered, and platform-event-triggered flows among the unaffected types. Do not grant Run Flows to a population merely because automation touches their records.

**When it occurs:** When the release readiness checklist records an enforcement date once and treats it as immutable, or when a postponement is read as a cancellation. The postponed update is the dangerous one precisely because the team has already rehearsed ignoring it.

**How to avoid:** Re-read the enforcement release from Setup > Release Updates in every preparation cycle rather than carrying forward the date logged last cycle. Keep postponed updates on the checklist with the status "postponed — re-confirm next cycle," never "done." For the flow update specifically, verify that every profile or permission set covering a persona who launches screen or autolaunched flows directly actually grants Run Flows before the enforcing release upgrades production.

---

## Gotcha 7: Not Every Breaking Behavior Change Arrives as a Toggleable Release Update

**What happens:** Some platform changes are enabled progressively across all orgs with no entry in Setup > Release Updates at all, and a Release Update is opened later covering only the slice Salesforce could not change unilaterally. Asynchronous sharing recalculation is the live example: the behavior "was introduced in Summer '25 and rolled out over several releases. Salesforce completed the enablement of this updated behavior in all orgs in April 2026." After large group or role changes, related owner-based sharing rules and account owner share records may now be recalculated asynchronously, while "The group or role changes are processed synchronously (no change from current behavior)." The accompanying Release Update — "Update Apex Code and Flows for Changed Sharing Recalculation Behavior" — is available in Spring '26 and enforced in Spring '27, and governs only changes originating from Apex code and flows, which keep running synchronously until enforcement.

**When it occurs:** When Release Updates triage is treated as the complete inventory of breaking changes for a release, so a change with no toggle is never assigned an owner or a sandbox test.

**How to avoid:** Treat Setup > Release Updates as necessary but not sufficient — the release notes still have to be triaged for behavior changes that ship without a toggle. Scope this one honestly before raising it: the article notes that "Most group membership or role changes don't lead to asynchronous sharing recalculation." It matters for orgs with large data volumes and very high ownership data skew, orgs whose Apex or flows modify group membership or roles, and code that depends on share records being available immediately. Where it applies, the recalculation stages are observable in the Setup Audit Trail — synchronous group/role processing appears as one row, with two further rows marking the start and completion of the asynchronous recalculation.

---

## Gotcha 8: OmniStudio Standard Runtime and the Managed Package Ride Different Calendars

**What happens:** The team treats "the Salesforce upgrade weekend" as one event. `enableStandardOmniStudioRuntime=true` puts OmniScripts / IPs / Data Mappers on the **core** calendar. The `omnistudio` managed package stays on the **package** calendar. They remain bonded through `omnistudio.VlocityOpenInterface` / `Callable`. A core upgrade can change standard-runtime behaviour while the package (and every `without sharing` Callable helper) has not moved, or the reverse.

**When it occurs:** Public-sector and Experience Cloud orgs that switched on standard runtime but still invoke Apex via VlocityOpenInterface. Guest-hardening CRUC opt-outs, leftover Live Experience networks, and Locker vs LWS (`lockerServiceNext`) each follow yet another clock.

**How to avoid:** Score upgrade exposure **by layer**, not by product name: core platform, OmniStudio standard runtime, OmniStudio package, Auth. Providers, guest sharing, BRE / Decision Matrices. For each layer record which calendar it follows, whether a failure is detectable in Apex tests, and the blast radius. Do not close a seasonal cycle as "no Apex impact" when the guest OmniScript path never ran in the test suite.

---

## Gotcha 9: A Settings Deploy Can Flip a Release Update With Nobody Reviewing It As One

**What happens:** A Release Update is not only a checkbox in Setup. Many of them are also a boolean field on an org `Settings` metadata type, and the Metadata API Developer Guide says so in the field description itself — `FlowSettings.doesEnforceApexCpuTimeLimit` "Corresponds to the Accurately Measure the CPU Time Consumption of Flows and Processes release update" (api_meta.txt L116849–116853); `FlowSettings.isTimeResumedInSameRunContext` corresponds to "Make Paused Flow Interviews Resume in the Same Context with the Same User Access" (L117048–117054); `LightningExperienceSettings.enableStackedModalManagerEnabled` to "Enable LWC Stacked Modals" (L121509–121514); `ApexSettings.enableAuraApexCtrlGuestUserAccessCheckPref` to the guest-user `@AuraEnabled` restriction (L110753–110758). A deployment that carries a `Flow.settings` or `Apex.settings` file therefore activates or deactivates release updates as a side effect. Because settings files are small and boring, they get waved through in review, and because the reviewer is reading a field name rather than an update name, nobody connects `doesEnforceApexCpuTimeLimit: true` to the CPU-accounting change until flows start hitting limits.

The reverse is worse. A team that snapshots a sandbox's settings and deploys them to production can silently *revert* an update an admin activated by hand in Setup, because the sandbox file still holds the old value. Setup and source control are two writers to the same field, and the last deploy wins.

**When it occurs:** Any org with settings files under source control — which is most orgs running a CI pipeline, since a full-org retrieve pulls them. It occurs most often just after a preview sandbox is refreshed or a new pipeline is stood up, when the settings files in the repo are a snapshot of some environment's posture rather than a deliberate declaration.

**How to avoid:** Treat release-update booleans as a reviewed artefact, not incidental settings. Keep only the fields you intend to govern in the deployed `.settings` files, annotate each one with the release update it corresponds to and the guide line, and require a named reviewer on any diff that touches them — the shape is in `references/worked-examples.md` §4. Before every deploy that includes a settings file, retrieve the same manifest from the target org first and diff; the diff is the release-update posture change. Do not use `<members>*</members>` for this: the wildcard "applies only when retrieving all settings, not for an individual setting" (api_meta.txt L110860–110864), so it buries the fields you care about in a whole-org dump.

---

## Gotcha 10: An Enforced Update's Field Reads Back False Forever and Ignores What You Set

**What happens:** Once Salesforce enforces a release update, the corresponding Settings field does not disappear — it goes inert. `MyDomainSettings.useStabilizedSandboxMyDomainHostnames` corresponds to the "Stabilize the Hostname for My Domain URLs in Sandboxes" release update, "which was enforced in Summer '20." The guide then states plainly: "As of API version 49.0, this field's value is always true, regardless of the value that you set. Changing its value has no effect on Salesforce, even if it reads false" (api_meta.txt L122427–122440). The same pattern appears elsewhere: `ApexSettings.enableSecureNoArgConstructorPref` is documented as "Not used. Critical update is automatically enforced" (api_meta.txt L110831–110833), and `MyDomainSettings.useEnhancedDomainsInSandbox` is likewise always `true` as of API version 58.0 regardless of what you set (api_meta.txt L122398–122407).

So a retrieved settings file can show `false` for a behaviour that has been enforced for years. An admin reads the `false`, concludes the org is exposed, files a remediation item, deploys `true`, sees no change in behaviour, and escalates a non-issue. An LLM reading the same file will do it faster and with more confidence.

**When it occurs:** Whenever a retrieved settings file is used as the evidence for "is this update on?" — a drift report, an org-health scan, a compliance checklist, or an agent summarising a repo.

**How to avoid:** A retrieved settings field answers "what is stored," not "what is enforced." Setup > Release Updates is the authority on enforcement status. When a field and the Setup screen disagree, the Setup screen wins and the field is inert. Record already-enforced updates in the run sheet with status `enforced` and a note that the field is inert (`references/worked-examples.md` §1) so the same false reading does not get re-investigated next cycle. Never deploy an inert field to "fix" it — the deploy succeeds and changes nothing, which is the most misleading result available.

---

## Gotcha 11: Preview Opt-In Is Decided by the Refresh Date, Not by the Sandbox's Name

**What happens:** Teams pick the preview sandbox by importance — "use UAT, it's the most production-like." The constraint that actually decides it is refresh cadence, because preview opt-in cannot be undone for the cycle (Gotcha 1) and the only exit is a refresh. Refresh floors differ sharply by type: Developer and Developer Pro can be refreshed daily, Partial Copy every 5 days, Full every 29 days (`admin/sandbox-strategy` › Type Capacities and Refresh Windows). A Full sandbox is therefore the *worst* place to make an irreversible decision — a bad preview strands it for the better part of a month, which is most of a release preparation window. A Developer Pro is the cheapest place to be wrong.

The second half of the trap runs the other way. A refresh after the preview upgrade returns the sandbox to whatever release its source org is on, so a routine mid-cycle refresh silently throws the preview away and the team keeps testing against the current release believing it is the next one.

**When it occurs:** When the preview sandbox is chosen from an environment list by prestige rather than from the refresh calendar, and when refresh scheduling is owned by a different person from release preparation — so the two calendars never get laid over each other.

**How to avoid:** Choose the preview sandbox by refresh floor and absence of in-flight work, then freeze its refresh from the preview cutover to the production upgrade and record the freeze in the run sheet (`references/worked-examples.md` §1, `preview_sandbox.refresh_freeze_from`). Name the sandbox owner and the refresh approver — `admin/sandbox-strategy` makes both a required column of the topology table for exactly this reason. If a refresh does happen, the sandbox is no longer a preview environment; say so out loud rather than letting the test results stand.

---

## Gotcha 12: The Org Upgrades but a Pinned Apex Class Does Not

**What happens:** "The org is on the new release" and "this class behaves the way the new release documents" are two different facts. Classes and triggers are stored with the version settings for a specific Salesforce API version, which exists precisely so that "as Apex, the API, and the components in managed packages evolve in subsequent released versions, a class or trigger is still bound to versions with specific, known behavior" (apexdev.txt L6876–6881). A class saved at API 62.0 keeps API 62.0 semantics after the org upgrades — it does not pick up versioned behaviour changes it was not saved with.

The changes this hides are not cosmetic. In API version 67.0 and later, Apex runs in user context by default where API 66.0 and earlier defaulted to system mode; classes without an explicit sharing declaration run in the current user's context; and `WITH SECURITY_ENFORCED` is no longer supported in SOQL `SELECT` queries in Apex (apexdev.txt L44494–44503). A class pinned at 66.0 skips all three. So a release regression pass that ran green proves nothing about the day someone bumps that class's version — the behaviour change lands then, in a change window nobody labelled "release."

**When it occurs:** In orgs with a long tail of old classes, and in any org where a developer bumps an API version as an incidental part of an unrelated fix. It also occurs in the opposite direction on managed packages: setting a version for an installed package "determines the exposed interface of any Apex code in the installed package" (apexdev.txt L6882–6884), so a package version bump can change what a class can call.

**How to avoid:** Inventory the distinct API versions in the codebase as part of release preparation and list, per version, what the class is skipping — the Apex Developer Guide's *Apex Versioned Behavior Changes* appendix (apexdev.txt L44482 onward) is organised by version number for exactly this lookup. Treat an API version bump as its own change with its own regression, never as a tidy-up inside another ticket. Salesforce's own guidance is to "consolidate your Apex codebase to use the minimal number of API versions, ideally, just one API version" (apexdev.txt L6905–6910); the fewer versions in play, the smaller this surface. Depth on the versioning strategy itself lives in `integration/api-versioning-strategy`.
