# Gotchas — Nonprofit Platform Architecture

Non-obvious Salesforce platform behaviors and architectural facts that cause real production problems in this domain.

## Gotcha 1: Person Accounts Cannot Be Disabled Once Enabled

**What happens:** Enabling Person Accounts is an irreversible org-level configuration change. Once activated, the Person Account record type merges Contact and Account fields on a single record type. The setting cannot be reversed without provisioning a completely new Salesforce org.

**When it occurs:** Teams that enable Person Accounts in a sandbox to evaluate the NPC data model — and then want to revert to standard Contacts for other reasons — discover there is no undo option. It also catches teams that accidentally enable Person Accounts in production before the constituent data model has been finalized.

**How to avoid:** Establish a documented architecture decision record for Person Accounts before touching any org setting. Enable Person Accounts in a dedicated architecture sandbox first. Validate all planned integrations (payment processors, marketing automation, volunteer platforms) for Person Account compatibility before enabling in production. The decision is permanent — treat it with the same gravity as an org partition decision.

---

## Gotcha 2: No In-Place Upgrade Path from NPSP to NPC

**What happens:** There is no Salesforce-provided tool, wizard, or migration accelerator that converts an existing NPSP org into an NPC org. Moving to NPC always requires provisioning a net-new Salesforce org with NPC licenses, rebuilding all configuration, and performing a formal ETL data migration. Teams that assume an "upgrade button" exists will discover this only after project planning is underway.

**When it occurs:** This is discovered during scoping when an implementation partner or internal team estimates migration effort assuming an in-place migration. It is also triggered when a client reads Salesforce marketing materials that describe NPC as the "next generation of NPSP" and assumes a straightforward upgrade.

**How to avoid:** Explicitly state in all project scoping and architecture documents: "Nonprofit Cloud requires a net-new org. There is no in-place upgrade from NPSP." Use the `architect/npsp-vs-nonprofit-cloud-decision` skill to set this expectation before NPC architecture work begins. Budget a full data migration project (typically 6–18 months depending on org complexity) separately from configuration work.

---

## Gotcha 3: Agentforce Nonprofit Agents Require Data Cloud — Licensing and Architecture Dependency

**What happens:** AI agents built on the Agentforce Nonprofit framework require Data Cloud to maintain context across sessions, access unified constituent history, and ground agent responses in real organizational data. An Agentforce Nonprofit agent deployed without Data Cloud has no memory, no personalization, and no ability to reference historical constituent interactions. It will behave like a generic prompt-response agent with no access to the organization's data.

**When it occurs:** Teams license the AI/Agentforce module without including Data Cloud in the contract, assuming AI capabilities are self-contained within the NPC platform. This is also triggered by product demos that show AI capabilities without highlighting the Data Cloud prerequisite.

**How to avoid:** When scoping any AI/Agentforce component of an NPC implementation, verify Data Cloud licensing is included. Data Cloud must be architected and activated — with data streams, data lake objects, and identity resolution configured — before Agentforce agents can be meaningfully configured. Include Data Cloud architecture as a mandatory prerequisite phase for any AI module work.

---

## Gotcha 4: Volunteer Management Is 19 Objects — Not a Simple Scheduling Feature

**What happens:** The NPC Volunteer Management module comprises 19 distinct objects including Volunteer Projects, Jobs, Shifts, Shift Workers, Hours, Capacity entries, Recurrence Schedules, and Eligibility Rules. Teams that scope Volunteer Management as "set up shift scheduling" consistently discover mid-implementation that 12–15 of the 19 objects were not accounted for in timeline or resource estimates. This causes scope creep, delayed go-lives, and underconfigured sharing models.

**When it occurs:** Anytime Volunteer Management is scoped without reviewing the Salesforce Volunteer Management Data Model documentation in full. This is especially common when the feature is added to an NPC scope late in the sales cycle as a "nice to have."

**How to avoid:** Reference the Volunteer Management Data Model documentation (developer.salesforce.com) and conduct an object-by-object scoping exercise before locking the Volunteer Management workstream timeline. Allocate a minimum of 6–8 weeks for a full Volunteer Management implementation with at least one dedicated resource.

---

## Gotcha 5: Grantmaking Is for Grant-Givers Only — Not Grant-Receivers

**What happens:** The Grantmaking module is designed for foundations that award grants to other organizations. It is not designed for nonprofits that apply for and receive grants from external funders. Organizations that receive grants (grant seekers) should manage their grant tracking in the Fundraising module using Opportunity or Gift Commitment records. Licensing and configuring Grantmaking for grant-seeking results in a data model that does not fit the use case and requires significant rework.

**When it occurs:** During sales and scoping, clients with grant-seeking needs hear "Salesforce has Grantmaking" and assume it covers both directions of the grant relationship. Implementation teams that have not worked with the module before make the same assumption.

**How to avoid:** During requirements gathering, explicitly ask: "Does your organization award grants to others, or receive grants from others?" Grant-givers need Grantmaking. Grant-receivers need Fundraising with appropriate record types for institutional funders. Document this distinction clearly in the module adoption map.

---

## Gotcha 6: Fundraising Connect API Version Lock at 59.0+

**What happens:** The Fundraising module's Connect API for gift entry, payment processing, and batch operations is available only from API version 59.0 onward. External payment processor integrations, fundraising platform connectors, and custom Lightning components that use earlier API versions will not have access to the Fundraising endpoints. Any integration built against API version 55.0–58.0 will encounter missing endpoint errors for gift entry operations.

**When it occurs:** During integration design when a legacy or low-code integration tool is configured to call the Salesforce REST API without specifying the correct version. Also occurs when a third-party ISV integration has not yet been updated to API 59.0+ and claims NPC compatibility without version qualification.

**How to avoid:** Verify that all payment processor and external fundraising integrations explicitly target API version 59.0 or higher. Include API version as a qualification criterion when evaluating third-party NPC integrations. Document the minimum API version in the integration architecture document for all Fundraising-adjacent integrations.
