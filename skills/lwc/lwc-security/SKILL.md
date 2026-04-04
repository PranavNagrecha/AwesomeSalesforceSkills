---
name: lwc-security
description: "Use when designing or reviewing Lightning Web Components for DOM safety, Lightning Web Security boundaries, third-party library handling, and secure server-side data access from LWC. Triggers: 'innerHTML in lwc', 'Lightning Web Security', 'document.querySelector', 'light DOM security', 'secure apex class for lwc'. NOT for org-wide sharing architecture or Apex-only security reviews when no LWC surface is involved."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Security
  - Reliability
  - User Experience
tags:
  - lwc-security
  - lightning-web-security
  - xss
  - light-dom
  - secure-apex
triggers:
  - "is innerhtml safe in lwc"
  - "document queryselector in lightning web components"
  - "lightning web security vs locker"
  - "guest user can call auraenabled apex from lwc"
  - "light dom security risk in lwc"
inputs:
  - "whether the component uses ui api, apex, or third-party libraries"
  - "whether it runs in lightning experience, experience cloud, or mobile"
  - "whether it uses light dom, manual dom, or direct html rendering"
outputs:
  - "security review findings for lwc and supporting apex"
  - "recommended safe rendering and data-access pattern"
  - "remediation plan for dom or server-side exposure risks"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the security question crosses the LWC boundary between browser behavior and Salesforce data access. The component may look harmless in markup, but the real risk often lives in direct DOM access, unsafe third-party library integration, or Apex controllers that expose more data than the UI should ever receive.

## Before Starting

- Does the component rely on Lightning Data Service, custom Apex, third-party libraries, or all three?
- Is it using `innerHTML`, `lwc:dom="manual"`, light DOM, or direct DOM queries?
- Will the component run in Experience Cloud, guest-user contexts, or any surface where relaxed assumptions become dangerous?

## Core Concepts

### Template Rendering Is Safer Than Manual DOM Work

Standard LWC template bindings are the safest default because the framework handles rendering and escaping for you. Risk rises sharply when the component bypasses declarative rendering through `innerHTML`, manual DOM insertion, or broad DOM queries.

### Lightning Web Security Protects Isolation, Not Business Logic

LWS exists to isolate namespaces and reduce unsafe access to DOM and globals, but it does not replace application security design. Data exposure can still happen if the component calls Apex that ignores sharing, CRUD, or FLS, or if the app deliberately exposes too much information to the client.

### Light DOM Is A Conscious Security Tradeoff

Light DOM can be appropriate for very specific use cases, but it relaxes encapsulation. Top-level light DOM components are not protected by Lightning Locker or LWS in the same way shadow DOM components are, so the placement and hierarchy of light DOM components matter.

### Secure Apex Is Part Of LWC Security

LWC security is not only about the browser. Apex called by the component must still enforce sharing and object/field access intentionally. Salesforce recommends Lightning Data Service for standard record access because it handles sharing, CRUD, and FLS for you; when Apex is required, the controller must enforce security explicitly.

## Common Patterns

### Prefer LDS And UI API For Standard Data Access

**When to use:** The component reads or updates standard Salesforce records without unusual server-side logic.

**How it works:** Use base components, LDS, or UI API adapters so record-level sharing plus object and field checks stay aligned to the platform model.

**Why not the alternative:** Custom Apex adds a server-side attack surface and can bypass security controls if written carelessly.

### Minimal Third-Party Library Boundary

**When to use:** A genuine business need requires a library for visualization, editors, or specialized UI behavior.

**How it works:** Load the library from a static resource, keep DOM ownership narrow, and avoid giving the library broad access to component internals or raw record data.

**Why not the alternative:** Remote scripts, broad manual DOM manipulation, and implicit globals are avoidable security risks.

### Shadow DOM First, Light DOM Only With Justification

**When to use:** Most components should remain in shadow DOM unless a strong integration or customization reason exists.

**How it works:** Default to encapsulation, and if light DOM is required, ensure it is nested appropriately and reviewed as a deliberate tradeoff.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard record access for forms or detail views | LDS or UI API | Platform-managed sharing, CRUD, and FLS |
| Need custom server-side logic | Apex with explicit sharing and data enforcement | Browser isolation is not enough |
| Need to inject or manage raw HTML | Re-evaluate the design first | Manual DOM work is the highest-risk pattern |
| Considering light DOM for convenience | Default to shadow DOM unless justified | Better encapsulation and safer boundaries |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Declarative template rendering is used wherever possible.
- [ ] `innerHTML`, `lwc:dom="manual"`, and direct DOM queries are justified and constrained.
- [ ] Apex controllers called by the component set explicit sharing and enforce data access intentionally.
- [ ] Third-party libraries are loaded through static resources and do not rely on remote script injection.
- [ ] Light DOM usage is deliberate and not top-level without a reviewed reason.
- [ ] Experience Cloud or guest-user deployment paths were reviewed separately.

## Salesforce-Specific Gotchas

1. **Top-level light DOM components are not protected like shadow DOM components** — they must be nested carefully and reviewed as an explicit tradeoff.
2. **`document.querySelector()` and other global DOM access are anti-patterns in LWC** — component code should access only elements it owns.
3. **An authenticated or guest user can invoke `@AuraEnabled` Apex only if access is granted, but that still does not make the Apex secure** — the class must enforce sharing plus object and field access intentionally.
4. **LWS improves component isolation but does not sanitize bad application design** — overexposed data in Apex is still overexposed data.

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC security review | Findings on DOM access, light DOM, third-party libraries, and Apex exposure |
| Safe rendering recommendation | Guidance on template-first rendering and secure alternatives to manual DOM work |
| Server-boundary remediation plan | Changes needed in Apex or LDS usage to reduce data-exposure risk |

## Related Skills

- `apex/soql-security` — use when the supporting Apex data-access layer is the main risk.
- `security/injection-prevention` — use when the question expands into SOQL, SOSL, formula, or broader XSS prevention beyond the component surface.
- `lwc/lifecycle-hooks` — use when the issue is primarily lifecycle misuse rather than security.
