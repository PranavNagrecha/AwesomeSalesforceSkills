# Gotchas: Change Set Deployment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names the official source it rests on.

---

## Gotcha 1: Profile Settings Travel Only for Components in the Same Deployment, Except Three That Always Travel

**What happens:** A team adds the `Sales User` profile to a change set to grant access to one new object. In the target, the profile gains the object and field permissions for components in that change set. Its user permissions, login IP ranges, and login hours are also replaced with the source values, because the Metadata API always includes those three. A production-only IP range or system permission disappears.

The opposite misconception is also costly. Teams that believe "the whole profile is replaced" add every object to the change set to "protect" it, and widen the blast radius.

**When it occurs:** Any change set or Metadata API deployment that includes a Profile. Profiles built in a refreshed sandbox often lack production-only IP ranges and permissions.

**How to avoid:** Grant new access with permission sets. When a profile must ship, retrieve the target profile first and compare the user permissions, `loginIpRanges`, and `loginHours` sections, because those deploy regardless of the other components. UNVERIFIED (2026-10-03): the exact list of profile settings the change set UI carries is documented only in Salesforce Help; verify in a sandbox deploy before production.

**Source:** Metadata API Developer Guide, Profile > Usage: "the returned .profile files only include security settings for the other metadata types referenced in the retrieve request. Exceptions include user permissions, IP address ranges, and login hours, which are always retrieved." The same section notes that deploying custom objects does not overwrite profile permissions for standard objects and fields.

---

## Gotcha 2: Flows Deploy Inactive to Production by Default

**What happens:** A flow is active in the source sandbox and is added to the change set. After deployment to production, the flow exists but is inactive. Users trigger the process and nothing happens.

**When it occurs:** Production targets where "Deploy processes and flows as active" is off, which is the production default. In scratch, sandbox, and developer orgs the setting defaults to on, so sandbox-to-sandbox rehearsals behave differently.

**How to avoid:** Either activate flows as a named post-deploy step, or turn the setting on in production and plan for the consequence: deploying an active flow then runs Apex tests, and the deployment rolls back if tests do not launch the required percentage of active processes and autolaunched flows.

**Source:** Metadata API Developer Guide, FlowSettings `enableFlowDeployAsActiveEnabled` ("Indicates whether processes and flows can be deployed as active via change sets or Metadata API. When the value is false, all processes and flows are deployed as inactive.").

---

## Gotcha 3: Run Specified Tests Checks Coverage per Class and Trigger

**What happens:** A change set validated with "Run specified tests" fails on coverage even though the org's overall coverage is 85%. One deployed trigger reaches only 60% from the listed tests.

**When it occurs:** Validations that list a subset of test classes for speed.

**How to avoid:** List test classes that cover each deployed class and trigger at 75% or more. Use the default or Run local tests when you cannot guarantee per-component coverage.

**Source:** Metadata API Developer Guide, DeployOptions `testLevel` (RunSpecifiedTests: "Each class and trigger in the deployment package must be covered by the executed tests for a minimum of 75% code coverage").

---

## Gotcha 4: View/Add Dependencies Misses Runtime References

**What happens:** View/Add Dependencies returns a clean list. After upload, validation fails with a missing component. The missed component was referenced at runtime: a class instantiated through `Type.forName()`, a custom label read in Apex, or a custom metadata record that the code queries.

**When it occurs:** Change sets that rely on the dependency action alone for Apex-heavy features.

**How to avoid:** After View/Add Dependencies, walk the code for `Type.forName()`, `Label.` references, custom metadata queries, named credentials used in callouts, and invocable methods called from flows. Add those components explicitly.

**Source:** Apex Developer Guide, "Deploy Components to Production" (the View/Add Dependencies step). UNVERIFIED (2026-10-03): the limits of the dependency scanner are not documented in a fetchable guide; the list above is drawn from field experience.

---

## Gotcha 5: Classes With Active Scheduled Jobs Can't Be Updated Through the UI

**What happens:** A change set that updates an Apex class fails because the class, or a class it references, has an active scheduled job in the target org.

**When it occurs:** Releases that touch schedulable classes or their dependencies while jobs are scheduled in production.

**How to avoid:** Pause or abort the scheduled jobs before deploying, or enable the deployment setting that allows deployments to update classes with pending or in-progress jobs, after assessing the risk. Reschedule the jobs after the release.

**Source:** Apex Developer Guide, Apex Scheduler: "If there are one or more active scheduled jobs for an Apex class, you can't update the class or any classes referenced by this class through the Salesforce user interface. However, you can enable deployments to update the class with active scheduled jobs by using the Metadata API." The guide points to "Deployment Connections for Change Sets" in Salesforce Help for the setting.

---

## Gotcha 6: Tests Run Serially in Change Set Deployments

**What happens:** A test suite that runs in 10 minutes in parallel from the Developer Console takes much longer during a change set validation. The release window estimate is wrong.

**When it occurs:** Every change set validation or deployment that runs Apex tests.

**How to avoid:** Time a full validation in a full-copy sandbox and use that figure for the window. Validate days ahead and quick deploy on release night.

**Source:** Apex Developer Guide, code coverage considerations: "Tests don't run in parallel in metadata deployments, package installations, or change set deployments."

---

## Gotcha 7: A Re-Upload Needs a New Validation Before Quick Deploy

**What happens:** A team validates on Monday, notices a missing field on Wednesday, adds it, and re-uploads. Quick deploy is no longer offered for the new inbound change set.

**When it occurs:** Any change to the component list after validation.

**How to avoid:** Finalize the component list before uploading for validation. If a component is missing after validation, decide whether a small follow-up change set is safer than re-validating the whole set. When re-upload is unavoidable, schedule the new validation immediately.

**Source:** Metadata API Developer Guide, `deployRecentValidation()` (quick deploy applies to "a recently validated component set"). UNVERIFIED (2026-10-03): the statement that a re-upload produces a separate inbound change set with no validation is documented only in Salesforce Help.

---

## Gotcha 8: Deployments During Service Upgrades Restart From the Beginning

**What happens:** A change set deployment started on a maintenance weekend runs far longer than the rehearsal. Component deployment and validation restart after the service is restored.

**When it occurs:** Change set deployments that overlap planned service downtime for the target instance.

**How to avoid:** Check the target instance on Salesforce Trust before fixing the release window.

**Source:** Metadata API Developer Guide, "Slow Deployments" ("This behavior affects file-based deployment and retrieval, change sets, some package installs and upgrades...").
