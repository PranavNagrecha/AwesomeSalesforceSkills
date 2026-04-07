# Gotchas — Portal Requirements Gathering

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Skipping Contact Reason Analysis Produces a Portal With Near-Zero Deflection

**What happens:** Teams skip the 60–90 day contact data pull and build based on stakeholder preference — usually a knowledge base, search, and case form. Post-launch deflection rate is under 5% because the content and features do not match the real reasons customers contact support.

**When it occurs:** Any portal project where requirements are gathered through stakeholder interviews alone, without pulling actual support volume data. Common on fast-moving projects where business owners are confident they know customer needs.

**How to avoid:** Make the contact reason data pull a hard prerequisite before any feature scoping session. Categorize each contact reason as Answers, Status, or Action. Use the breakdown to set the feature priority stack. Do not hold a feature scoping session until the data is in hand.

---

## Gotcha 2: License Choice Is Locked at Provisioning and Costly to Reverse

**What happens:** Customer Community is selected during requirements as the lower-cost option. Post-launch, the business needs manual sharing or role hierarchy on custom objects — capabilities that Customer Community does not include. Upgrading to Customer Community Plus requires deactivating and reprovisioning every user record.

**When it occurs:** When license selection is treated as a cost-optimization decision without confirming whether the required sharing and object access capabilities are present in the chosen license. Discovered at build time when a developer tries to implement selective sharing on a custom object.

**How to avoid:** During requirements, walk through every sharing requirement: does the org need customers to share records with each other? Do customers need to see custom object data beyond Cases and Knowledge? If yes to either, Customer Community Plus is required. Record the decision and its rationale before any users are provisioned.

---

## Gotcha 3: Gamification and Social Features Defer Deflection Validation Indefinitely

**What happens:** Phase 1 scope includes idea exchange, chatter, leaderboards, and community forums alongside the core self-service features. The portal launches. Social engagement is measurable but deflection is not, because the core self-service loop was not instrumented first. Leadership cannot confirm the business case.

**When it occurs:** When stakeholders treat the portal as a community engagement initiative rather than a deflection initiative. Social features have visible, easy-to-measure engagement metrics that create the illusion of success even when deflection is zero.

**How to avoid:** Explicitly defer all social and gamification features to phase 2 in the requirements document. Mark them as "deferred — pending deflection validation" rather than "rejected." Set a measurable deflection target as the gate to phase 2.

---

## Gotcha 4: Hybrid Access Model Guest User Profile Is Overly Permissive by Default

**What happens:** A hybrid access model is chosen. The guest user profile is cloned from an existing profile without tightening object permissions. Post-launch, a security review finds that anonymous visitors can read Account or Contact records through the API, not just the portal UI.

**When it occurs:** When access architecture is decided but guest user profile lockdown is not assigned as a named deliverable during requirements. Developers focus on public page content and assume default guest permissions are safe.

**How to avoid:** When hybrid access is selected, add "guest user profile lockdown" explicitly to the build checklist in the requirements document. Assign an owner. List every object the guest user should and should not be able to read.

---

## Gotcha 5: Partner Community Requires Underlying Sales Cloud License

**What happens:** A service-heavy org selects Partner Community licenses for a PRM portal. During build, the developer discovers that Lead and Opportunity objects are unavailable because the org only has Service Cloud, not Sales Cloud. The entire PRM use case is blocked until Sales Cloud is procured.

**When it occurs:** When license selection focuses on the Experience Cloud license tier without confirming that the underlying CRM product license (Sales Cloud) is present. Common when the portal project is owned by a marketing or channel team without IT involvement in the license review.

**How to avoid:** During license selection in requirements, explicitly verify that the CRM product license required by the use case is present in the org. PRM requires Sales Cloud (Lead + Opportunity). Document this dependency in the requirements before any procurement or build planning.
