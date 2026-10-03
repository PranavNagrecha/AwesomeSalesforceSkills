# Gotchas: Client Onboarding Design

Non-obvious Action Plan and document checklist behaviors that cause real problems in FSC onboarding designs. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of the Summer '26 PDFs, written as `<guide> L<n>`. A claim that could not be re-read in an official source carries an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: A plan stays bound to the published version it was created from

**What happens:** `ActionPlan.ActionPlanTemplateVersionId` is "the ID of the version of the action plan template used to create this action plan. At creation, the referenced action plan template must be in the published state" (Object Reference, ActionPlan, `object_reference L21624-21630`). Versions are separate records (`ActionPlanTemplateVersion`) with a `Status` of `Draft`, `Final` (published), `Obsolete`, or `ReadOnly`, plus `IsLocked`, `MayEdit`, and a `Version` index (`object_reference L22670-22765`). Publishing a new version does not rewrite plans already launched.

**When it occurs:** A regulator adds a beneficial-ownership step, the team publishes a corrected version, and assumes clients mid-onboarding now see the new task. They do not.

**How to avoid:** Write an in-flight policy into the design: clients finish on their starting version, unless a mandated correction requires remediation of open plans (add the missing item to each open plan, and record who approved that). UNVERIFIED (2026-10-03): earlier versions of this skill said an active template "returns an error" on any edit and must be cloned; the guide shows locking flags and versions but does not describe the UI behavior, so test the revision path in a sandbox.

---

## Gotcha 2: Ordering between items needs a dependency, not only a required flag

**What happens:** `IsRequired` "indicates whether the task created from this template item is required" (`api_meta L15180`). Ordering is a separate structure: `actionPlanTemplateItemDependencies` (API 59.0) define "the sequential relationship and creation timing of items", with `previousTemplateItem` the prerequisite and `templateItem` the dependent (`api_meta L15112-15114`, `L15191-15205`). The guide's sample uses `creationType` `OnPreviousItemCompleted` (`L15315`).

**When it occurs:** A design marks the KYC task required and assumes the funding-instructions task cannot start until KYC closes. Without a dependency, both tasks are created when the plan launches.

**How to avoid:** Model every regulatory "A before B" rule as a dependency pair, and keep `IsRequired` for "this must be done". UNVERIFIED (2026-10-03): earlier versions of this skill said a required item prevents plan completion; the guide does not describe that behavior.

---

## Gotcha 3: Supported template parents differ between the Metadata API and the plan object

**What happens:** The Metadata API lists `ActionPlanTemplate.targetEntityType` parents as Account, BusinessMilestone, Campaign, Case, Claim, Contact, Contract, InsurancePolicy, InsurancePolicyCoverage, Lead, Opportunity, PersonLifeEvent, Visit, and custom objects with activities enabled (`api_meta L15161-15166`). The object reference lists plan parents by API version and includes Financial Account, Financial Goal, and Financial Holding from API 48.0 (`object_reference L21745-21750`).

**When it occurs:** The design anchors onboarding on `FinancialAccount`, and the template cannot be deployed or launched there in the target org.

**How to avoid:** Pick the anchor object early and launch a test plan on it in a sandbox. If Financial Account anchoring fails, anchor on Account or Opportunity and link the Financial Account from the plan's tasks.

---

## Gotcha 4: Due dates are formulas on the start date, and holiday handling is a plan flag

**What happens:** Template item due dates are item values such as `ActivityDate` with `valueFormula` `StartDate + 10` (`api_meta L15244-15248`). There is no `TaskDeadlineType` or `DaysFromStart` field in the Metadata API or Object Reference for these objects; earlier versions of this skill named both. The plan carries `IsUsingHolidayHours`, which "indicates whether task completion dates have been calculated by incrementing the task offset for each non-work day, excluding recurring holidays" (`object_reference L21661-21667`).

**When it occurs:** Compliance defines SLAs in jurisdictional business days with public holidays, and the design assumes the platform will skip them.

**How to avoid:** Agree the SLA definition with compliance, state whether plans use holiday hours, and test the calculated due dates around a real holiday in a sandbox. UNVERIFIED (2026-10-03): the exact meaning of "excluding recurring holidays" (whether recurring holidays are skipped or not counted as non-work days) is not explained further in the guide.

---

## Gotcha 5: Document checklist items fix `IsRequired` at creation and waive through `Status`

**What happens:** `DocumentChecklistItem` (API 47.0) "represents a checklist item for a file documentation upload". `IsRequired` shows Create and Defaulted on create but no Update property, and `Status` takes `Accepted`, `New`, `Pending`, or `Waived` (FSC Developer Guide, `fsc_dev_guide L14520-14680`). Template items can be document checklist items: the template item `ItemEntityType` includes Document Checklist Item (`object_reference L22280-22290`), and the plan item value is `DocumentChecklistItem` (`L21840`).

**When it occurs:** Operations wants to "un-require" a document for one client by editing the flag, or the design has no way to record that compliance waived a document.

**How to avoid:** Decide required documents per template version. Record exceptions as `Status = Waived` with a comment, not by editing `IsRequired`. Define document types as `DocumentType` metadata (API 59.0; `api_meta L55744-55800`).

---

## Gotcha 6: OmniStudio availability must be confirmed before designing OmniScript intake

**What happens:** Onboarding designs often specify OmniScript intake because FSC material shows it. If the org does not have OmniStudio, the design must be redone as a Screen Flow. UNVERIFIED (2026-10-03): that OmniStudio is always licensed separately from FSC, and that deployments fail "silently or with cryptic errors" in an unlicensed org, are claims from earlier versions of this skill that are not stated in the guides read.

**When it occurs:** The license is assumed rather than checked, and the gap appears mid-build.

**How to avoid:** Check installed packages and licences at design start, record the result in the technology selection rationale, and design for Screen Flow if OmniStudio is absent.

---

## Gotcha 7: A per-plan item ceiling is unconfirmed, so test large templates

**What happens:** Earlier versions of this skill stated a hard limit of 75 task items per plan, with plan launch failing above it. UNVERIFIED (2026-10-03): no item limit appears in the Object Reference or Metadata API entries for Action Plans read for this pass.

**When it occurs:** Highly granular regulated onboarding, where each document and signature becomes its own item.

**How to avoid:** Count items during design. For templates approaching the old figure, launch a test plan in a sandbox, and split into phased templates (Pre-Onboarding and Document Collection; Compliance Review and Activation) if launch fails or the plan becomes unusable. Phased templates are easier to version anyway.

---

## Gotcha 8: Template metadata needs the IndustriesActionPlans license

**What happens:** "To create or access action plan templates, you must have the Customize Application permission and the IndustriesActionPlans license" (`api_meta L15104`). The type also requires `isAdHocItemCreationEnabled` from API 59.0 (`L15135`) and `uniqueName` on the template and every item.

**When it occurs:** A deployment user without the license, or a hand-written template missing a required element, fails the deploy.

**How to avoid:** Deploy with a user who holds the license, retrieve a template built in Setup before hand-editing one, and keep `uniqueName` values stable across versions.
