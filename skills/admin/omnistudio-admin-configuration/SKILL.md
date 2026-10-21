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
  - "installed managed-package namespace, read from Installed Packages, if migrating or running a legacy install"
  - "user populations requiring OmniStudio access: internal builders, internal consumers, Experience Cloud community members"
outputs:
  - "org-level OmniStudio Settings configuration checklist"
  - "permission set assignment plan for admins, users, and community members"
  - "runtime mode verification steps and post-activation checks"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-21
---

# OmniStudio Admin Configuration

Use this skill when an org requires initial OmniStudio configuration or when runtime, namespace, or permission problems are blocking component activation. It covers two independent configuration axes — runtime mode selection and permission set assignment — that must both be correct for OmniStudio to function. A gap in either axis causes activation failures, missing UI, or components that appear active but silently error at runtime.

This skill is explicitly scoped to org-level setup. It does not cover OmniScript step design, DataRaptor logic, Integration Procedure orchestration, or namespace migration from Vlocity to native.

**Grounding status.** UNVERIFIED (2026-10-21): the OmniStudio Settings page — Standard OmniStudio Runtime, Disable Managed Package Runtime, Runtime Namespace, Enhanced Runtime Performance — has no Metadata API type or field in the corpus (api_meta 264 has no `OmniStudioSettings` type), so every statement about those toggles below is Help-only. What the corpus does hold:

- OmniStudio is licensed in pieces: scratch-org features `OmnistudioRuntime` ("execute OmniScripts, DataMappers, FlexCards ... in the employee facing applications"), `OmnistudioDesigner` ("create new OmniScripts/ DataMappers / Integration Procedures") and `OmnistudioMetadata` (sfdx_dev 264 L8554-8571), plus add-on licenses including `OmniStudioRuntimeCCAddon` (L6929).
- "OmniStudio Admin" appears in the Metadata API guide as a **permission set license** (api_meta 264 L56731-56732).
- A permission set that needs a permission set license can be assigned only to users who hold that license (secguide 262 L1999-2004).
- The component metadata types are `OmniDataTransform`, `OmniIntegrationProcedure`, `OmniScript` and `OmniUiCard` (sfdx_dev 264 L16493-16496).

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the current setting for **Standard OmniStudio Runtime** in Setup > OmniStudio Settings? Is it enabled or disabled?
- What value is set in the **Runtime Namespace** field? Is it blank, `omnistudio`, `vlocity_ins`, `vlocity_cmt`, or `vlocity_ps`? (UNVERIFIED (2026-10-21): field and values are Help-only.)
- Which Salesforce edition and OmniStudio license are in use — Industries (included), standalone OmniStudio SKU, or Vlocity managed package?
- Who needs access — internal builders, internal consumers only, or Experience Cloud / community users as well?
- Has any component already been opened in the Standard OmniStudio designer? (If yes, that component cannot be reverted to managed package runtime.)
- Is **Enhanced Runtime Performance** on or off? It is a security change, not a tuning knob — see below before recommending either state.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Has anyone opened an existing component in the Standard designer? | Gotcha 1: that component cannot go back to managed-package runtime (UNVERIFIED (2026-10-21): Help-only) | A component inventory before the toggle moves |
| Which namespace is installed, and what does Runtime Namespace say now? | Gotcha 2: a blank or wrong namespace fails at activation, not at save (UNVERIFIED (2026-10-21): Help-only) | The value read from Installed Packages, not assumed |
| Does every target user hold the OmniStudio permission set license before the permission sets go on? | Gotcha 3: a permission set tied to a license can go only to users with that license (secguide 262 L1999-2004) | A two-pass provisioning plan |
| Is any active component still on the managed-package runtime? | Gotcha 4: Disable Managed Package Runtime stops those components working (UNVERIFIED (2026-10-21): Help-only) | A converted-and-retested list before the toggle |
| Who re-checks OmniStudio Settings after each sandbox refresh? | Gotcha 5: the settings may not survive a refresh (UNVERIFIED (2026-10-21): Help-only) | A named owner and a post-refresh step |
| Has every consumer persona been access-reviewed for user mode? | Gotcha 6: Enhanced Runtime Performance runs every component in user mode (UNVERIFIED (2026-10-21): Help-only) | Object and field grants per persona, trialled in a sandbox |
| Do Experience Cloud or guest users run OmniScripts? | SKILL gotcha 4: community users need more than the internal user permission set (UNVERIFIED (2026-10-21): Help-only custom-permission name) | The community license and permission plan |

Configuring with these answers sets the runtime, namespace and access once, in the right order, instead of discovering each gap as a generic activation error.

---

## Core Concepts

### Runtime Mode Selection

OmniStudio supports two runtime modes that are mutually exclusive at the component level. **Managed Package Runtime** uses the installed Vlocity or OmniStudio managed package LWC components. **Standard OmniStudio Runtime** (also called native runtime) uses the Salesforce-platform-native LWC components shipped with the org.

Enabling Standard OmniStudio Runtime is a one-way toggle per component. Once a component is opened and saved in the Standard designer, it cannot revert to the managed package runtime path. Orgs in a mixed state — some components on native, some on managed — can cause inconsistent behavior and should be treated as transitional, not permanent. UNVERIFIED (2026-10-21): the one-way-per-component rule and the mixed-state behaviour are Help-only. The corpus confirms only that the two variants exist by name — a platform event is "part of OmniStudio Standard, not OmniStudio for Vlocity" (platform_events 264 L13801).

To enable Standard Runtime: Setup > OmniStudio Settings > enable **Standard OmniStudio Runtime**. The same page contains a toggle to **Disable Managed Package Runtime** (OmniStudio Settings: `disableManagedPackageRuntime`), which prevents further use of the managed package components and forces all activity through the native runtime. UNVERIFIED (2026-10-21): neither toggle nor the `disableManagedPackageRuntime` name appears in the Metadata API guide; the only OmniStudio settings keys in the corpus are the scratch-org definition keys `enableOmniStudio` and `enableOmniStudioMetadata` (sfdx_dev 264 L6070-6071, L5771-5772).

### Runtime Namespace Configuration

The **Runtime Namespace** field in OmniStudio Settings controls which managed package namespace is active for the org. Valid values are:

- `omnistudio` — for orgs that have the native OmniStudio package or are fully on Standard Runtime
- `vlocity_ins` — Insurance and Health Cloud
- `vlocity_cmt` — Communications, Media, and Energy Cloud
- `vlocity_ps` — Public Sector Solutions

Leaving this field blank or entering an incorrect namespace causes component activation failures that surface as generic errors. This field must match the actual installed namespace. If Standard Runtime is fully enabled and no managed package is present, set the namespace to `omnistudio`. UNVERIFIED (2026-10-21): the field, its valid values and the failure mode are Help-only; the corpus mentions only `vlocity_cmt` (as a flow action prefix, api_meta 264 L71920) and none of `vlocity_ins`, `vlocity_ps` or a Runtime Namespace field.

### Enhanced Runtime Performance and User Mode

UNVERIFIED (2026-10-21): this whole subsection rests on the Salesforce Help topics listed in `references/well-architected.md`; no corpus guide documents the toggle, the Omni Interaction Access Configuration object, or `ConnectAPI.OmniDesignerConnect` (absent from apexref 262).

**Enhanced Runtime Performance** is a toggle on the OmniStudio Settings page (Setup > Quick Find > Omnistudio Settings). It is a security change with a performance name. Salesforce Help describes it as ensuring "that Omnistudio communicates with the Salesforce Platform with in-platform capabilities instead of through Apex calls" — removing the Apex hop — and states that the setting makes all components execute in user mode, which "respects the access levels of the person performing an operation." Components that previously reached data through the managed package's Apex layer now stop at the running user's object and field permissions, so a user without the requisite object or field permissions cannot complete key actions.

Two consequences an org-level setup must plan for:

- **A prerequisite object grant.** Users need access to the **Omni Interaction Access Configuration** object; Salesforce documents this as a before-you-begin item, with a dedicated permission set. Beyond that, every persona running a component needs CRUD and FLS on everything its Data Mappers and Integration Procedures touch.
- **It gates the Apex entry point.** Invoking Integration Procedures from Apex through the Connect API (documented as `ConnectAPI.OmniDesignerConnect.integrationProcedureExecute`) requires Enhanced Runtime Performance to be enabled; when it is disabled, Integration Procedure calls from Apex do not route through the Connect API. Copy that identifier from the help topic rather than recalling it — it is not in the Apex Reference Guide.

Salesforce is explicit about rollout: do not enable the setting directly in production — test it in a production-like sandbox first. This is an org setting and is independent of the Apex `apiVersion` user-mode default, which is pinned per class in `.cls-meta.xml` — see [Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version) for that separate rule.

### Permission Set Licenses and Assignment

As of Winter '24, OmniStudio consolidates user access into a primary **Permission Set License (PSL)**: `OmniStudioPSL`. Two core permission sets are derived from this PSL:

- **OmniStudio Admin** — for builders and administrators who author OmniScripts, DataRaptors, and Integration Procedures. Grants access to the OmniStudio designer and all configuration tabs.
- **OmniStudio User** — for consumers who interact with published OmniScripts and FlexCards. Does not grant authoring access.

UNVERIFIED (2026-10-21): the `OmniStudioPSL` name, the "Winter '24" consolidation and the two derived permission sets are Help-only. The corpus pulls the other way on one point: it names "OmniStudio Admin" as a *permission set license* (api_meta 264 L56731-56732), and splits runtime and designer access into separate licences/features (`OmnistudioRuntime`, `OmnistudioDesigner`, sfdx_dev 264 L8559-8571). Read the org's Company Information > Permission Set Licenses list before naming any license.

PSL assignment must precede permission set assignment: "some permissions require users to have a specific user license or permission set license before you can grant them in permission sets", and such a permission set can be assigned only to users who hold that license (secguide 262 L1999-2004). UNVERIFIED (2026-10-21): that an out-of-order assignment fails *silently*.

### Experience Cloud Community User Access

Experience Cloud (community) users require additional configuration beyond the standard `OmniStudio User` permission set. A custom permission set must be created that enables the **community consumer** custom permission, then assigned to the community profile or permission set group. Without this, authenticated and guest community members will receive access-denied errors even if all standard permission sets are assigned. UNVERIFIED (2026-10-21): the custom-permission requirement and its name are Help-only; the corpus shows only an add-on license named `OmniStudioRuntimeCCAddon` (sfdx_dev 264 L6929), and does not say what it licenses.

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

**Why not the alternative:** Skipping the Runtime Namespace field leaves it blank, which causes silent activation failures on first component save. UNVERIFIED (2026-10-21): steps 2-6 name Help-only settings and licenses (see Grounding status); only the license-before-permission-set order in steps 4-6 is grounded (secguide 262 L1999-2004).

### Community / Experience Cloud User Access

**When to use:** Community members — authenticated portal users or guest users — need to run OmniScripts embedded in Experience Cloud pages.

**How it works:**
1. Complete the standard greenfield or managed-package setup first.
2. Create a new Permission Set with the **OmniStudio Community User** custom permission enabled.
3. Assign this permission set to the community profile or to the Experience Cloud permission set group.
4. In Experience Cloud Builder, confirm the OmniScript component is visible in the component palette.
5. For guest users, additionally confirm the guest user profile has access to the OmniScript record via sharing and that no IP or DataRaptor action requires authentication it cannot provide.

**Why not the alternative:** Assigning only `OmniStudio User` to the community profile produces access-denied errors at runtime because the community consumer custom permission is absent. UNVERIFIED (2026-10-21): Help-only, including the "OmniStudio Community User" permission name.

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

UNVERIFIED (2026-10-21): the runtime, namespace, `OmniStudioPSL` and community-permission choices in this table are Help-only; the license-before-permission-set reason is grounded (secguide 262 L1999-2004).

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Gather context** — confirm org edition, installed OmniStudio license type, current Runtime Namespace field value, and whether any components have already been opened in Standard designer.
2. **Determine runtime mode** — decide between Standard OmniStudio Runtime (native) and Managed Package Runtime based on org state; if the org has no Vlocity packages, use native.
3. **Configure OmniStudio Settings** — navigate to Setup > OmniStudio Settings, enable Standard OmniStudio Runtime if applicable, and set the Runtime Namespace to the correct value (`omnistudio` or the matching Vlocity namespace). UNVERIFIED (2026-10-21): Help-only settings.
4. **Provision Permission Set Licenses** — assign the OmniStudio permission set license(s) the org actually holds (Help names `OmniStudioPSL`; UNVERIFIED (2026-10-21)) to every user who will be an admin or consumer before assigning any permission sets (secguide 262 L1999-2004).
5. **Assign permission sets** — assign `OmniStudio Admin` to builders and `OmniStudio User` to consumers; for Experience Cloud users, create and assign the additional community consumer permission set (UNVERIFIED (2026-10-21): Help-only names).
6. **Verify activation** — run `python3 skills/admin/omnistudio-admin-configuration/scripts/check_omnistudio_admin_configuration.py --manifest-dir force-app` on the retrieved permission sets, then open the OmniStudio app, create a test OmniScript, activate it, and confirm it renders; check that consumer users can view the component without errors.
7. **Document the configuration** — record the runtime mode, namespace value, and permission set assignments in the deployment runbook for future sandboxes and scratch org refreshes.

---

## Review Checklist

Run through these before marking work in this area complete:

UNVERIFIED (2026-10-21): the settings, license and permission names in this checklist are Help-only (see Grounding status); the license-first order is grounded (secguide 262 L1999-2004).

- [ ] OmniStudio Settings page confirms the correct runtime mode (Standard or Managed Package).
- [ ] Runtime Namespace field is populated with the correct namespace value — not blank.
- [ ] All target users have the OmniStudio permission set license assigned (Help: `OmniStudioPSL`).
- [ ] Builders have `OmniStudio Admin`; consumers have `OmniStudio User`.
- [ ] Experience Cloud community users have the community consumer custom permission.
- [ ] **Enhanced Runtime Performance** state is deliberate and documented. If it is on, every consumer persona has been access-reviewed and has the Omni Interaction Access Configuration object, and the toggle was trialled in a production-like sandbox first.
- [ ] A test OmniScript activates without errors and renders correctly for both admin and consumer user profiles.
- [ ] Configuration is documented in the deployment runbook so sandbox refreshes replicate it.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Standard Runtime enable is irreversible per component** — once a component is opened in the Standard OmniStudio designer, it cannot be converted back to Managed Package Runtime. Plan the cutover carefully before enabling Standard Runtime in production. (UNVERIFIED (2026-10-21): Help-only.)
2. **Blank Runtime Namespace causes silent activation failures** — the OmniStudio Settings page does not validate the namespace field on save; an empty value only surfaces as a cryptic activation error when a user first tries to activate a component. (UNVERIFIED (2026-10-21): Help-only.)
3. **PSL must precede permission set assignment** — a permission set that needs a permission set license can be assigned only to users who already hold it (secguide 262 L1999-2004), so assigning `OmniStudio Admin` or `OmniStudio User` before the license fails in bulk provisioning scripts. UNVERIFIED (2026-10-21): "sometimes silently".
4. **Community consumer permission is separate from standard user permission** — assigning `OmniStudio User` to a community profile is necessary but not sufficient; the community-consumer custom permission is an additional requirement that is easy to overlook. (UNVERIFIED (2026-10-21): Help-only.)
5. **Enhanced Runtime Performance re-scopes every component to user mode at once** — the toggle reads as tuning, but it makes all components execute in user mode org-wide, so narrow-profile consumers, Experience Cloud users, and guest users break first. Salesforce directs orgs not to enable it directly in production. (UNVERIFIED (2026-10-21): Help-only, quoted from the Help topic in `references/well-architected.md`.)

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
