# Gotchas — OmniStudio vs Standard Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: License Gate — OmniStudio Is Not Available Without a Qualifying Industries Cloud

**What happens:** OmniStudio components (OmniScript, FlexCards, Integration Procedures) fail at runtime in any org that does not hold a qualifying Industries cloud license. The failure is not a configuration error — it is a licensing restriction enforced by Salesforce. Components may render blank, throw JavaScript errors, or fail silently depending on the component type and context.

**When it occurs:** Any time an OmniStudio component is deployed to or accessed in an org without Financial Services Cloud, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, or Education Cloud licensing. This includes sandboxes refreshed from licensed production orgs where the sandbox license provisioning has not been completed, and developer orgs that do not have OmniStudio enabled.

**How to avoid:** Confirm license entitlement in Setup > Company Information > Licenses before any architecture discussion involving OmniStudio. Do not rely on the org edition name alone — verify the specific license row. Include license confirmation as step one in any OmniStudio architecture decision workflow.

---

## Gotcha 2: Standard Runtime Must Be Explicitly Enabled — It Is Not Auto-On

**What happens:** Standard Runtime is natively available in all Industries-licensed orgs as of Spring '25, but it is not automatically enabled. Orgs that do not explicitly toggle on Standard Runtime in Setup > OmniStudio Settings continue to run the managed package runtime even if developers intend to use Standard Runtime tooling. Metadata deployed using standard metadata API types for OmniStudio (no namespace prefix) may not render or function correctly in an org still running on managed package runtime.

**When it occurs:** Most commonly affects new projects on licensed orgs where the Salesforce admin has not navigated to OmniStudio Settings, and projects migrating from managed package where the Standard Runtime toggle is assumed to be on.

**How to avoid:** As part of any Standard Runtime architecture, verify the OmniStudio Settings toggle state. Include this as an explicit setup step in project kickoff. Add a check in CI/CD pipeline documentation confirming the target org runtime state before deploying Standard Runtime components.

---

## Gotcha 3: Vlocity Managed Package and Standard Runtime Cannot Fully Coexist

**What happens:** Orgs running the Vlocity managed package (`vlocity_ins__` namespace) or the Salesforce managed package (`industries__` namespace) cannot simply deploy new Standard Runtime OmniStudio components alongside existing managed-package components for the same metadata types. The two runtimes use different metadata type names, namespace conventions, and LWC rendering paths. In some configurations, attempting to run both concurrently causes rendering conflicts and deployment failures.

**When it occurs:** Projects that attempt to build new OmniScripts or Integration Procedures using the Standard Runtime while leaving existing managed-package components in place. This is a common mistake when teams interpret "Standard Runtime is available" as meaning "new and old components can coexist freely."

**How to avoid:** Before starting any new OmniStudio development on an org with existing managed-package components, assess the full migration scope. Use Salesforce's OmniStudio Conversion Tool for migration. If migration is not feasible in the current timeline, build new components on the managed package as documented technical debt rather than attempting a hybrid split-runtime state.

---

## Gotcha 4: Not All Industries Cloud Editions Include the Same OmniStudio Entitlement

**What happens:** Some starter or limited editions of Industries clouds include restricted OmniStudio entitlements — for example, limited OmniScript step counts, restricted Integration Procedure HTTP action access, or no FlexCard entitlement. Architects who confirm "the org has FSC" without verifying the specific edition assume full OmniStudio access and design solutions that exceed the entitlement.

**When it occurs:** Orgs on FSC Starter, limited Health Cloud editions, or promotional/trial editions of Industries clouds. Also occurs when an org's Industries license has been downgraded or modified during a renewal negotiation.

**How to avoid:** Validate the specific Industries cloud edition and the OmniStudio entitlement level against the current Salesforce pricing and packaging documentation. If uncertainty exists, open a Salesforce case or review the contract order form before committing to an OmniStudio architecture.

---

## Gotcha 5: OmniStudio Team Ramp Is Consistently Underestimated

**What happens:** Projects that assume Salesforce Flow or LWC developers can adopt OmniStudio without meaningful ramp time consistently underdeliver on initial sprints. OmniStudio has its own designer tools (OmniScript Designer, Integration Procedure Designer, FlexCard Designer), its own data model (DataRaptors, Response Actions), and its own runtime behavior. A competent Salesforce developer with no OmniStudio experience typically requires 2–4 weeks of structured training before delivering production-quality components.

**When it occurs:** Any project where OmniStudio is selected for the technical capability and the team skill assessment is omitted or optimistic. Particularly common when a senior architect makes the OmniStudio recommendation and hands off to a delivery team without verifying OmniStudio experience.

**How to avoid:** Include an explicit team skills assessment in the architecture decision. If OmniStudio is selected and the team lacks experience, include OmniStudio training (minimum 2 weeks) in the project plan before the first development sprint. Factor ramp cost into the OmniStudio vs standard tooling comparison — for simple use cases, the ramp cost alone may tip the recommendation to Screen Flow.
