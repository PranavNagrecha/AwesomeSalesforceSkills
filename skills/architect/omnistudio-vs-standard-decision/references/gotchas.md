# Gotchas — OmniStudio vs Standard Decision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: OmniStudio Is Not Licensed in Core Sales Cloud or Service Cloud

**What happens:** OmniStudio components (OmniScript, FlexCards, Integration Procedures) fail at runtime — silently or with unhelpful errors — in orgs that do not hold an Industries Cloud license. The components may appear to work in sandboxes provisioned with a developer or trial license but break in production.

**When it occurs:** Any time an OmniStudio component is deployed to or activated in an org without a valid Industries Cloud license (FSC, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, Education Cloud). This includes scenarios where the license has expired or been removed from the org.

**How to avoid:** Before designing any solution that relies on OmniStudio, check Setup > Company Information > Licenses and confirm an Industries license is active. Do not assume that because the managed package is installed the license is valid — the package can be installed without the license being provisioned.

---

## Gotcha 2: Managed Package and Standard Designers Are Not Interchangeable Without Migration — but Coexistence Now Has a Supported Name

**What happens:** Orgs on the managed-package version of OmniStudio (`vlocity_ins__` namespace for legacy Vlocity orgs, `industries__` namespace for post-acquisition Salesforce-packaged orgs) cannot simply adopt Standard Designers components alongside existing managed-package components. The metadata types, field references, and runtime behaviors differ, and ad-hoc mixing creates broken references, failed activations, and deployment errors. What has changed is that "you can never have both in one org" is no longer true as an absolute: Salesforce documents Omnistudio Hybrid — "You can create Omnistudio components using standard designers and standard runtime in your managed package environment using Omnistudio Hybrid." Architects who plan a full build freeze because they believe a big-bang cutover is the only path are costing themselves a release cycle.

**When it occurs:** When an org on managed-package OmniStudio attempts to build new components using the Standard Designers tooling outside the Hybrid configuration, or when deployment pipelines move Standard Designers components into a managed-package org.

**How to avoid:** Establish which configuration the org is actually in before scoping anything. If the target is full migration, treat it as a dedicated project run through the **Omnistudio Migration Assistant (OMA)**, an SF CLI plugin installed with `sf plugins install @salesforce/plugin-omnistudio-migration-tool@<tool_version>`. OMA runs Assess mode first to surface issues, then Migrate mode, across three phases: development sandbox, validation sandbox with full regression testing, then production. Scope the known gaps explicitly — "The OMA tool cannot convert Angular Omniscript to work with the standard runtime," and Vlocity industry-specific objects and OmniAnalytics data structures need manual work. If the target is coexistence rather than migration, read the Salesforce Help topic "Omnistudio Hybrid Compatibility Matrix" and confirm the component types you care about are eligible before committing a design — that matrix, not a general rule of thumb, governs what Hybrid supports.

---

## Gotcha 3: FlexCards Break Silently in Lightning App Builder Without License

**What happens:** FlexCard components placed in Lightning App Builder page layouts render as blank areas or produce a generic component error for end users, with no clear indication that a license issue is the cause. Admins frequently interpret this as a configuration or permissions problem and waste significant time debugging.

**When it occurs:** In any org or sandbox where the OmniStudio license is not active, including production orgs after license expiry, sandboxes refreshed from production after a license change, or trial orgs where the trial period has ended.

**How to avoid:** Include an OmniStudio license validity check in any deployment runbook that involves FlexCards. When troubleshooting blank components in Lightning App Builder, check license status as the first diagnostic step before investigating component configuration or user permissions.

---

## Gotcha 4: Integration Procedure Callout Limits and Timeout Behavior

**What happens:** Integration Procedures share the org's HTTP callout governor limits with Apex (100 callouts per transaction) but have their own timeout constraints that are not identical to Apex's configurable timeout. Long-running external APIs that an Apex class handles with async patterns (Queueable, Future) cannot be handled the same way inside an Integration Procedure.

**When it occurs:** When an Integration Procedure calls an external REST API that has response times exceeding the Integration Procedure's timeout threshold, or when an Integration Procedure makes more than the callout limit in a single invocation chain (e.g., looping over a collection and calling an HTTP Action per item).

**How to avoid:** For external APIs with unpredictable response times, evaluate whether an Apex-backed callout with explicit async handling is more appropriate than an Integration Procedure HTTP Action. For bulk callout patterns, design the Integration Procedure to batch records and call the external endpoint once per batch rather than once per record. Always test Integration Procedures against realistic data volumes and external API response times in a sandbox before production deployment.

---

## Gotcha 5: Namespace Confusion Between vlocity_ins__ and industries__

**What happens:** Legacy Vlocity-origin orgs use the `vlocity_ins__` namespace for managed-package OmniStudio fields and metadata. Post-acquisition Salesforce-repackaged orgs use the `industries__` namespace. Code, queries, and integrations that reference one namespace prefix fail silently in orgs using the other. This is especially common in cross-org deployments or when teams use shared code templates.

**When it occurs:** When SOQL queries, Apex classes, or data migration scripts reference `vlocity_ins__` fields in an org that has been migrated to the `industries__` namespace package, or vice versa.

**How to avoid:** Identify the active namespace for OmniStudio in the org by checking installed packages (Setup > Installed Packages) before writing any SOQL or Apex that references OmniStudio fields. Use dynamic schema inspection (`Schema.describeSObjects`) in Apex if the code must be portable across namespace versions. Document the namespace in the project's architecture decision record.
