# Gotchas — OmniStudio vs Standard Decision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: OmniStudio Is Not Licensed in Core Sales Cloud or Service Cloud

**What happens:** OmniStudio components (OmniScript, FlexCards, Integration Procedures) fail at runtime — silently or with unhelpful errors — in orgs that do not hold an Industries Cloud license. The components may appear to work in sandboxes provisioned with a developer or trial license but break in production.

**When it occurs:** Any time an OmniStudio component is deployed to or activated in an org without a valid Industries Cloud license (FSC, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, Education Cloud). This includes scenarios where the license has expired or been removed from the org.

**How to avoid:** Before designing any solution that relies on OmniStudio, check Setup > Company Information > Licenses and confirm an Industries license is active. Do not assume that because the managed package is installed the license is valid — the package can be installed without the license being provisioned.

---

## Gotcha 2: Managed Package and Standard Designers Are Not Interchangeable Without Migration

**What happens:** Orgs on the managed-package version of OmniStudio (`vlocity_ins__` namespace for legacy Vlocity orgs, `industries__` namespace for post-acquisition Salesforce-packaged orgs) cannot simply adopt Standard Designers components alongside existing managed-package components. The metadata types, field references, and runtime behaviors differ. Mixing them creates broken references, failed activations, and deployment errors.

**When it occurs:** When an org on managed-package OmniStudio attempts to build new components using the Standard Designers tooling, or when deployment pipelines move Standard Designers components into a managed-package org.

**How to avoid:** Treat the managed-package-to-Standard-Designers migration as a dedicated project. Salesforce provides an OmniStudio Conversion Tool to assist. Plan for a full conversion of existing OmniScript and Integration Procedure components — partial migration is supported in some configurations but must be explicitly scoped. Do not start new Standard Designers components in a managed-package org without a documented migration plan.

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
