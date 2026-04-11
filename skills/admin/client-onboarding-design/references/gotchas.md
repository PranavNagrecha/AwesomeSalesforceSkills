# Gotchas — Client Onboarding Design

Non-obvious Salesforce FSC platform behaviors that cause real production problems in this domain.

## Gotcha 1: Action Plan Templates Are Immutable After Activation

**What happens:** Once an ActionPlanTemplate is set to Status = Active (published), Salesforce locks the record and all its ActionPlanTemplateItem children. Any attempt to edit the template or its tasks — via the UI, Apex, or the Metadata/Data API — returns an error. There is no "edit active template" escape hatch.

**When it occurs:** Any time an admin or automated process attempts to revise an active template — adding a task, changing a deadline offset, or updating an owner. This most commonly surfaces when compliance or regulatory requirements change post-launch and the team realizes they have no governance plan for updates.

**How to avoid:** Design the versioning governance protocol before the first template is published. The correct update path is clone-and-republish: clone the active template (produces a Draft), modify the clone, then activate the clone as the new version. Establish a naming convention (e.g., "Client Onboarding v3") so versions are traceable. Document who owns the versioning workflow and under what circumstances a new version is warranted.

---

## Gotcha 2: OmniStudio Is a Separately Licensed Add-On

**What happens:** OmniStudio FlexCards and OmniScripts are prominently featured in FSC documentation because they are commonly purchased with FSC, but they require a separate license. Orgs with only the base FSC license do not have OmniStudio available. Attempting to access OmniStudio Setup or deploy OmniScript components in an unlicensed org fails silently or with cryptic errors.

**When it occurs:** When a process design recommends OmniScript-based intake without verifying the org's license entitlements. This is discovered mid-implementation when the OmniStudio app is absent from Setup or when a deployment of an OmniScript component is rejected.

**How to avoid:** Confirm OmniStudio license availability at the start of process design by checking Setup > Installed Packages for the OmniStudio managed package. If OmniStudio is not installed, design the guided intake as a standard Screen Flow. Document the license basis in the process design artifacts so the decision is traceable and the implementation team does not retry an OmniStudio approach.

---

## Gotcha 3: In-Flight Plans Are Not Updated When a New Template Version Is Published

**What happens:** Publishing a new version of a template (via clone-and-republish) does not modify or restart plans that were already launched from the previous version. Clients currently in onboarding under version 1 continue with version 1 tasks, deadlines, and owners — even if version 2 corrects a significant process error.

**When it occurs:** When compliance or regulatory requirements change and the business assumes that publishing the corrected template will update all open onboarding journeys. It does not. The ActionPlan instance is bound to the template version at the time of launch.

**How to avoid:** Include an explicit in-flight plan policy in the process design governance documentation. The policy should state: (a) whether in-flight plans will complete on the prior version (standard, lowest-risk approach), (b) whether a manual remediation step is required for in-flight plans if the change is a critical compliance correction (e.g., a regulator-mandated new task), and (c) who has authority to decide. For critical corrections, a manual action plan remediation script (updating open ActionPlan instances via Apex or Data Loader) may be required.

---

## Gotcha 4: BusinessDays Deadline Mode Does Not Skip Org Holidays

**What happens:** Setting TaskDeadlineType = BusinessDays on an Action Plan template causes deadline calculation to skip Saturdays and Sundays. It does not skip org-configured public holidays. Teams expecting holiday-aware deadline calculation (e.g., for regulatory SLAs that reference business days as defined by a jurisdiction's holiday calendar) find that plans launched before a holiday have task due dates that fall on the holiday itself.

**When it occurs:** When the process design specifies "business day" SLAs without clarifying that BusinessDays mode excludes only weekends, not holidays. This is a gap between business expectation and platform behavior.

**How to avoid:** During process design, confirm the SLA definition with the compliance team. If the SLA definition includes holidays, document that the platform's BusinessDays mode is insufficient and that post-launch date adjustment logic (via Flow or Apex) will be required to account for holiday offsets. Do not leave this assumption unresolved.

---

## Gotcha 5: The 75-Task Hard Limit on Action Plans Can Break Complex Onboarding Sequences

**What happens:** An ActionPlan instance can contain a maximum of 75 task items. This is a hard platform limit. If an ActionPlanTemplate has more than 75 items, launching a plan from the template fails. The error is not surfaced clearly to end users — the plan launch button may appear to do nothing, or an error message appears without clearly identifying the task count as the cause.

**When it occurs:** When the process design includes a highly detailed onboarding sequence — common in regulated industries where each sub-step is tracked individually. Crossing 75 items is easier than expected when document collection tasks are broken into per-document checklist items.

**How to avoid:** Count the total task items during process design, before implementation. If the count approaches or exceeds 75, split the onboarding into two or more sequential templates (e.g., Phase 1: Pre-Onboarding and Document Collection; Phase 2: Compliance Review and Activation). Launch Phase 2 automatically upon Phase 1 completion via a Flow trigger or Apex. Document the split in the process map so the handoff between plans is explicit.
