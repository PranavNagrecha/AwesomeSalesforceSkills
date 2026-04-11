# Gotchas — OmniStudio Admin Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Enabling Standard Runtime Is Irreversible Per Component

**What happens:** Once a component (OmniScript, DataRaptor, FlexCard, or Integration Procedure) is opened and saved in the Standard OmniStudio designer, it is permanently converted to the native runtime path. There is no UI or API option to revert it to Managed Package Runtime. If the org still has other components on Managed Package Runtime, those two sets of components must now coexist in a mixed state.

**When it occurs:** Any time a developer or admin opens a pre-existing managed-package component in the Standard designer after Standard OmniStudio Runtime has been enabled in OmniStudio Settings.

**How to avoid:** Before enabling Standard Runtime in a production org or any sandbox that shares component state, audit all existing components and create a migration plan. Enable Standard Runtime only once the team is ready to fully convert components. Use a full-copy sandbox to validate the transition before touching production. Do not enable Standard Runtime as an exploratory or temporary change.

---

## Gotcha 2: Blank Runtime Namespace Causes Silent Activation Failures

**What happens:** The Runtime Namespace field in OmniStudio Settings is optional in the UI — it accepts an empty value and saves without any warning. However, when a builder tries to activate a component, the platform cannot resolve the namespace and the activation fails with a generic error message that does not mention the namespace field. The builder typically spends time debugging the component itself before discovering the root cause is a missing org-level configuration value.

**When it occurs:** On any newly provisioned org where OmniStudio Settings has never been explicitly configured, or after a sandbox refresh that does not copy custom settings values.

**How to avoid:** As part of every org setup checklist and every sandbox refresh runbook, explicitly verify and set the Runtime Namespace field. For orgs on native OmniStudio with no Vlocity package, set it to `omnistudio`. For orgs with a Vlocity package, match the value to the installed namespace (`vlocity_ins`, `vlocity_cmt`, or `vlocity_ps`). Include this check in any org health validation script.

---

## Gotcha 3: PSL Assignment Must Precede Permission Set Assignment in Bulk Provisioning

**What happens:** When a bulk user provisioning script or Data Loader job assigns the `OmniStudio Admin` or `OmniStudio User` permission set before the `OmniStudioPSL` Permission Set License has been assigned to the user, the assignment either silently fails or produces a generic license error. The user shows the permission set in their profile but cannot access OmniStudio functionality. Debugging is difficult because the user record appears correctly configured at the permission set level.

**When it occurs:** In bulk provisioning scripts, automated onboarding flows, or any scenario where PSL and permission set assignments are made in parallel or out of order.

**How to avoid:** Structure all provisioning workflows to assign the `OmniStudioPSL` Permission Set License in a first pass, then assign permission sets in a second pass after confirming PSL assignment. In Flows or Apex provisioning logic, add an explicit check that the PSL is present before attempting permission set assignment. Never assume PSL and permission set assignment can be parallelized safely.

---

## Gotcha 4: Disabling Managed Package Runtime Does Not Remove Installed Components

**What happens:** Enabling the "Disable Managed Package Runtime" toggle in OmniStudio Settings prevents new components from being run on the managed package path, but it does not uninstall or deactivate existing managed-package-mode components. Those components will simply stop functioning and may surface null-render errors to users who already have the component embedded in page layouts or Experience Cloud pages.

**When it occurs:** When an admin enables the toggle during or after a migration, without first confirming that all active, published components have been converted to Standard Runtime.

**How to avoid:** Before enabling "Disable Managed Package Runtime," run a full inventory of active OmniScripts, FlexCards, DataRaptors, and Integration Procedures that are still on the managed package runtime path. Convert all of them to Standard Runtime, re-activate, and verify they render correctly before flipping the disable toggle.

---

## Gotcha 5: Sandbox Refreshes Reset OmniStudio Settings

**What happens:** A full sandbox refresh from production creates a fresh copy of the org, but custom settings — including the OmniStudio Settings values for Runtime Namespace and Standard Runtime toggle — may not be copied reliably, or may be reset to defaults depending on the refresh type and org configuration. After a refresh, the sandbox silently loses the namespace value and developers encounter the same blank-namespace activation failures described in Gotcha 2.

**When it occurs:** After any full or partial sandbox refresh, particularly in organizations that rely on sandbox environments for active development.

**How to avoid:** Add an OmniStudio Settings verification step to the post-refresh runbook. After every sandbox refresh, a designated admin must log in, navigate to Setup > OmniStudio Settings, and confirm the Runtime Namespace and runtime mode toggles are correct before handing the sandbox to developers.
