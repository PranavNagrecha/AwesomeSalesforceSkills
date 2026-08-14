---
name: omnistudio-admin-configuration
description: "Use when configuring OmniStudio at the org level: enabling Standard Runtime, selecting the Runtime Namespace, assigning Permission Set Licenses, toggling feature settings, and granting Experience Cloud community access. Trigger keywords: OmniStudio Settings, Standard OmniStudio Runtime, managed package runtime, runtime namespace, OmniStudio Permission Set, OmniStudio PSL. NOT for moving an org off the vlocity namespace — use omnistudio/vlocity-to-native-omnistudio-migration. NOT for deciding whether to adopt OmniStudio — use architect/omnistudio-vs-standard-decision."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do I enable Standard OmniStudio Runtime in a new org"
  - "OmniStudio components are not activating after setup"
  - "which permission sets do I assign for OmniStudio admin and end users"
  - "Runtime Namespace field in OmniStudio Settings is blank and components fail"
  - "Experience Cloud users cannot see OmniScripts after permission assignment"
  - "managed package runtime vs native OmniStudio runtime comparison"
tags:
  - omnistudio-admin-configuration
  - omnistudio-settings
  - runtime-namespace
  - permission-set-license
  - standard-omnistudio-runtime
  - experience-cloud-omnistudio
inputs:
  - "org edition and OmniStudio license type (Industries or standalone OmniStudio)"
  - "target runtime mode: Standard OmniStudio Runtime (native) or Managed Package Runtime"
  - "active Vlocity namespace if migrating or running a legacy install (vlocity_ins, vlocity_cmt, vlocity_ps)"
  - "user populations requiring OmniStudio access: internal builders, internal consumers, Experience Cloud community members"
outputs:
  - "org-level OmniStudio Settings configuration checklist"
  - "permission set assignment plan for admins, users, and community members"
  - "runtime mode verification steps and post-activation checks"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# OmniStudio Admin Configuration

Use this skill when an org requires initial OmniStudio configuration or when runtime, namespace, or permission problems are blocking component activation. It covers two independent configuration axes — runtime mode selection and permission set assignment — that must both be correct for OmniStudio to function. A gap in either axis causes activation failures, missing UI, or components that appear active but silently error at runtime.

This skill is explicitly scoped to org-level setup. It does not cover OmniScript step design, DataRaptor logic, Integration Procedure orchestration, or namespace migration from Vlocity to native.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the current setting for **Standard OmniStudio Runtime** in Setup > OmniStudio Settings? Is it enabled or disabled?
- What value is set in the **Runtime Namespace** field? Is it blank, `omnistudio`, `vlocity_ins`, `vlocity_cmt`, or `vlocity_ps`?
- Which Salesforce edition and OmniStudio license are in use — Industries (included), standalone OmniStudio SKU, or Vlocity managed package?
- Who needs access — internal builders, internal consumers only, or Experience Cloud / community users as well?
- Has any component already been opened in the Standard OmniStudio designer? (If yes, that component cannot be reverted to managed package runtime.)
- Is **Enhanced Runtime Performance** on or off? It is a security change, not a tuning knob — see below before recommending either state.

---

## Core Concepts

### Runtime Mode Selection

OmniStudio supports two runtime modes that are mutually exclusive at the component level. **Managed Package Runtime** uses the installed Vlocity or OmniStudio managed package LWC components. **Standard OmniStudio Runtime** (also called native runtime) uses the Salesforce-platform-native LWC components shipped with the org.

Enabling Standard OmniStudio Runtime is a one-way toggle per component. Once a component is opened and saved in the Standard designer, it cannot revert to the managed package runtime path. Orgs in a mixed state — some components on native, some on managed — can cause inconsistent behavior and should be treated as transitional, not permanent.

To enable Standard Runtime: Setup > OmniStudio Settings > enable **Standard OmniStudio Runtime**. The same page contains a toggle to **Disable Managed Package Runtime** (OmniStudio Settings: `disableManagedPackageRuntime`), which prevents further use of the managed package components and forces all activity through the native runtime.

### Runtime Namespace Configuration

The **Runtime Namespace** field in OmniStudio Settings controls which managed package namespace is active for the org. Valid values are:

- `omnistudio` — for orgs that have the native OmniStudio package or are fully on Standard Runtime
- `vlocity_ins` — Insurance and Health Cloud
- `vlocity_cmt` — Communications, Media, and Energy Cloud
- `vlocity_ps` — Public Sector Solutions

Leaving this field blank or entering an incorrect namespace causes component activation failures that surface as generic errors. This field must match the actual installed namespace. If Standard Runtime is fully enabled and no managed package is present, set the namespace to `omnistudio`.

### Enhanced Runtime Performance and User Mode

**Enhanced Runtime Performance** is a toggle on the OmniStudio Settings page (Setup > Quick Find > Omnistudio Settings). It is a security change with a performance name. Salesforce Help describes it as ensuring "that Omnistudio communicates with the Salesforce Platform with in-platform capabilities instead of through Apex calls" — removing the Apex hop — and states that the setting makes all components execute in user mode, which "respects the access levels of the person performing an operation." Components that previously reached data through the managed package's Apex layer now stop at the running user's object and field permissions, so a user without the requisite object or field permissions cannot complete key actions.

Two consequences an org-level setup must plan for:

- **A prerequisite object grant.** Users need access to the **Omni Interaction Access Configuration** object; Salesforce documents this as a before-you-begin item, with a dedicated permission set. Beyond that, every persona running a component needs CRUD and FLS on everything its Data Mappers and Integration Procedures touch.
- **It gates the Apex entry point.** Invoking Integration Procedures from Apex through the Connect API (documented as `ConnectAPI.OmniDesignerConnect.integrationProcedureExecute`) requires Enhanced Runtime Performance to be enabled; when it is disabled, Integration Procedure calls from Apex do not route through the Connect API. Copy that identifier from the help topic rather than recalling it — it is not in the Apex Reference Guide.

Salesforce is explicit about rollout: do not enable the setting directly in production — test it in a production-like sandbox first. This is an org setting and is independent of the Apex `apiVersion` user-mode default, which is pinned per class in `.cls-meta.xml` — see [Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version) for that separate rule.

### Permission Set Licenses and Assignment

As of Winter '24, OmniStudio consolidates user access into a primary **Permission Set License (PSL)**: `OmniStudioPSL`. Two core permission sets are derived from this PSL:

- **OmniStudio Admin** — for builders and administrators who author OmniScripts, DataRaptors, and Integration Procedures. Grants access to the OmniStudio designer and all configuration tabs.
- **OmniStudio User** — for consumers who interact with published OmniScripts and FlexCards. Does not grant authoring access.

Assigning a permission set without the underlying PSL will fail silently or with a generic error. PSL assignment must precede permission set assignment in bulk provisioning workflows.

### Experience Cloud Community User Access

Experience Cloud (community) users require additional configuration beyond the standard `OmniStudio User` permission set. A custom permission set must be created that enables the **community consumer** custom permission, then assigned to the community profile or permission set group. Without this, authenticated and guest community members will receive access-denied errors even if all standard permission sets are assigned.

---

## Common Patterns

### Greenfield Native Runtime Setup

**When to use:** A new org or sandbox with no prior Vlocity install needs OmniStudio configured from scratch.

**How it works:**
1. Go to Setup > OmniStudio Settings.
2. Enable **Standard OmniStudio Runtime**.
3. Set **Runtime Namespace** to `omnistudio`.
4. Assign `OmniStudioPSL` Permission Set License to all builder and user accounts.
5. Assign the **OmniStudio Admin** permission set to builders.
6. Assign the **OmniStudio User** permission set to consumers.
7. Verify by opening the OmniStudio app and confirming the designer and list views load.

**Why not the alternative:** Skipping the Runtime Namespace field leaves it blank, which causes silent activation failures on first component save.

### Community / Experience Cloud User Access

**When to use:** Community members — authenticated portal users or guest users — need to run OmniScripts embedded in Experience Cloud pages.

**How it works:**
1. Complete the standard greenfield or managed-package setup first.
2. Create a new Permission Set with the **OmniStudio Community User** custom permission enabled.
3. Assign this permission set to the community profile or to the Experience Cloud permission set group.
4. In Experience Cloud Builder, confirm the OmniScript component is visible in the component palette.
5. For guest users, additionally confirm the guest user profile has access to the OmniScript record via sharing and that no IP or DataRaptor action requires authentication it cannot provide.

**Why not the alternative:** Assigning only `OmniStudio User` to the community profile produces access-denied errors at runtime because the community consumer custom permission is absent.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org, no prior Vlocity install | Enable Standard Runtime, set namespace to `omnistudio` | Avoids managed package dependency |
| Org has Vlocity managed package, not yet migrating | Set Runtime Namespace to correct Vlocity namespace, do not enable Standard Runtime yet | Preserves managed package compatibility |
| Org is mid-migration from Vlocity to native | Enable Standard Runtime, keep Managed Package Runtime enabled until all components are migrated | Per-component migration; mixed state is transitional only |
| Internal builders need design access | Assign `OmniStudioPSL` PSL + `OmniStudio Admin` permission set | PSL must precede permission set assignment |
| Internal consumers only | Assign `OmniStudioPSL` PSL + `OmniStudio User` permission set | Least privilege |
| Community or portal users | Standard setup + custom community consumer permission set | Community permission is separate from internal user permission |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Gather context** — confirm org edition, installed OmniStudio license type, current Runtime Namespace field value, and whether any components have already been opened in Standard designer.
2. **Determine runtime mode** — decide between Standard OmniStudio Runtime (native) and Managed Package Runtime based on org state; if the org has no Vlocity packages, use native.
3. **Configure OmniStudio Settings** — navigate to Setup > OmniStudio Settings, enable Standard OmniStudio Runtime if applicable, and set the Runtime Namespace to the correct value (`omnistudio` or the matching Vlocity namespace).
4. **Provision Permission Set Licenses** — assign the `OmniStudioPSL` PSL to every user who will be an admin or consumer before assigning any permission sets.
5. **Assign permission sets** — assign `OmniStudio Admin` to builders and `OmniStudio User` to consumers; for Experience Cloud users, create and assign the additional community consumer permission set.
6. **Verify activation** — open the OmniStudio app, create a test OmniScript, activate it, and confirm it renders; check that consumer users can view the component without errors.
7. **Document the configuration** — record the runtime mode, namespace value, and permission set assignments in the deployment runbook for future sandboxes and scratch org refreshes.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OmniStudio Settings page confirms the correct runtime mode (Standard or Managed Package).
- [ ] Runtime Namespace field is populated with the correct namespace value — not blank.
- [ ] All target users have the `OmniStudioPSL` Permission Set License assigned.
- [ ] Builders have `OmniStudio Admin`; consumers have `OmniStudio User`.
- [ ] Experience Cloud community users have the community consumer custom permission.
- [ ] **Enhanced Runtime Performance** state is deliberate and documented. If it is on, every consumer persona has been access-reviewed and has the Omni Interaction Access Configuration object, and the toggle was trialled in a production-like sandbox first.
- [ ] A test OmniScript activates without errors and renders correctly for both admin and consumer user profiles.
- [ ] Configuration is documented in the deployment runbook so sandbox refreshes replicate it.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Standard Runtime enable is irreversible per component** — once a component is opened in the Standard OmniStudio designer, it cannot be converted back to Managed Package Runtime. Plan the cutover carefully before enabling Standard Runtime in production.
2. **Blank Runtime Namespace causes silent activation failures** — the OmniStudio Settings page does not validate the namespace field on save; an empty value only surfaces as a cryptic activation error when a user first tries to activate a component.
3. **PSL must precede permission set assignment** — attempting to assign `OmniStudio Admin` or `OmniStudio User` before assigning the underlying PSL will fail, sometimes silently, in bulk user provisioning scripts.
4. **Community consumer permission is separate from standard user permission** — assigning `OmniStudio User` to a community profile is necessary but not sufficient; the community-consumer custom permission is an additional requirement that is easy to overlook.
5. **Enhanced Runtime Performance re-scopes every component to user mode at once** — the toggle reads as tuning, but it makes all components execute in user mode org-wide, so narrow-profile consumers, Experience Cloud users, and guest users break first. Salesforce directs orgs not to enable it directly in production.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OmniStudio Settings configuration checklist | Verified runtime mode, namespace value, and feature toggle state for the org |
| Permission set assignment plan | Maps user populations to PSL and permission set assignments including community users |
| Post-activation verification log | Test activation results for a sample OmniScript confirming correct runtime behavior |

---

## Related Skills

- `omnistudio/omnistudio-security` — use when reviewing the security posture of OmniStudio permission assignments and data exposure, beyond basic setup.
- `omnistudio/vlocity-to-native-omnistudio-migration` — use when the org needs to move from a Vlocity managed package namespace to the native `omnistudio` runtime.
