---
name: static-resources-in-lwc
description: "Use when packaging third-party JavaScript, CSS, or asset files into Salesforce static resources for Lightning Web Components, including `@salesforce/resourceUrl`, `loadScript`, `loadStyle`, zip pathing, versioning, and CSP-safe delivery. Triggers: 'static resource in lwc', 'loadScript not working', 'resourceUrl path in zip', 'third party library in salesforce'. NOT for npm-bundled code that should ship through the build pipeline or server-side integration assets."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Performance
  - Operational Excellence
tags:
  - static-resources
  - resource-url
  - platform-resource-loader
  - third-party-library
  - csp
triggers:
  - "how do i load a static resource in lwc"
  - "loadscript is not working in lightning web components"
  - "path inside zipped static resource in lwc"
  - "third party javascript library in salesforce"
  - "static resource versioning strategy"
inputs:
  - "which library or asset is being loaded and whether it is zipped"
  - "whether the resource is JavaScript, CSS, images, fonts, or a mixed asset pack"
  - "whether Lightning Web Security or CSP constraints are affecting the load path"
outputs:
  - "static-resource loading pattern for LWC with versioning and guard rails"
  - "review findings for CSP, duplicate loading, and pathing mistakes"
  - "implementation guidance for script, style, or asset references"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-15
---

Use this skill when a component needs code or assets that do not belong inline in the bundle. Static resources are the supported way to bring third-party libraries and packaged assets into Salesforce UI, but they work well only when loading is deliberate, one-time, and compatible with Salesforce security boundaries.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the dependency really an external library, or should it be solved with a native base component or local LWC code first?
- Will the resource be a single file, a zip archive with nested paths, or a reusable asset pack?
- Does the component need JavaScript execution, stylesheet loading, or only a URL to an image or font?

---

## Core Concepts

Static resources separate packaged assets from component source and let Salesforce deliver them through supported platform mechanisms. In LWC, there are two common paths: reference the resource URL directly for assets such as images, or load executable files with `lightning/platformResourceLoader`. Problems start when teams mix those paths, rely on CDNs, or reload the same library on every render.

### `resourceUrl` Gives You A Stable Base Path

Importing `@salesforce/resourceUrl/Name` returns a deployable URL for the resource. For zipped assets, you append the internal file path yourself. That means naming and internal archive structure matter. If the zip changes shape between versions, every consumer path becomes part of the migration work.

### `loadScript` And `loadStyle` Need A Real Lifecycle

`loadScript(this, url)` and `loadStyle(this, url)` should run from a controlled lifecycle path, usually `renderedCallback()` with a guard or another one-time initialization branch. Loading on every rerender creates duplicate initialization, event leaks, and inconsistent state. The loader is for supported static-resource delivery, not for arbitrary remote URLs.

### Security Boundaries Still Apply

Static resources are compatible with Salesforce CSP and Lightning Web Security in a way public CDN tags are not. If a library needs elevated trust or direct global access, that is a design review point, not a default setting. The more a library expects to own the global browser environment, the higher the fit risk inside Salesforce UI.

### Versioning Is An Operational Concern

The resource name, archive structure, and consumer paths should support clean upgrades. A stable versioning convention such as `chartjs_4_4` or a package-level asset manifest makes rollouts and rollbacks much safer than overwriting ambiguous resource names repeatedly.

---

## Common Patterns

### One-Time Third-Party Library Loader

**When to use:** The component needs a JavaScript library for charts, maps, or specialized editors.

**How it works:** Import the resource URL, guard the loader in `renderedCallback()`, and initialize the library only after the script promise resolves.

**Why not the alternative:** Inline `<script>` tags or CDN URLs conflict with Salesforce security posture and bypass deployable asset control.

### Zipped Asset Pack With Explicit Paths

**When to use:** A library ships multiple files or an asset family belongs together.

**How it works:** Store the package as a zip static resource and construct paths from the resource base URL so every consumer uses the same internal structure.

**Why not the alternative:** Uploading many loosely named resources creates drift and makes upgrades harder to coordinate.

### Versioned Resource Naming

**When to use:** The asset is likely to change independently of the component code or must be rollback-safe.

**How it works:** Use an explicit version in the static resource name or a well-documented packaging convention so releases can move forward or back without guessing which asset is live.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need an image, font, or static file URL | Import `@salesforce/resourceUrl` directly | No runtime script loading is needed |
| Need a third-party JavaScript or CSS library | Use `loadScript` or `loadStyle` from a static resource | Supported loading path inside Salesforce UI |
| Library ships multiple related files | Use a zip static resource with explicit internal paths | Keeps related assets versioned together |
| Team wants to use a public CDN tag | Prefer a packaged static resource | Better CSP compatibility and release control |
| Library assumes global browser ownership | Reassess library fit or trust model | LWS and platform boundaries may make it a poor fit |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The dependency justifies itself over a native base component or local code path.
- [ ] Asset loading uses `resourceUrl` or `platformResourceLoader`, not remote script tags.
- [ ] Script or style loading is guarded against repeated rerender execution.
- [ ] Zip paths are documented and stable for every consumer.
- [ ] Versioning and rollback expectations are explicit.
- [ ] Security review covers any trust-elevation or global-library assumptions.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CDN habits do not translate cleanly into LWC** - a library that works in generic web HTML often fails under Salesforce CSP or deployment controls.
2. **`renderedCallback()` can run many times** - loading a script there without a guard creates duplicate initialization and hard-to-debug side effects.
3. **Zip path changes are breaking changes** - consumers usually concatenate paths manually, so internal archive structure becomes part of the contract.
4. **Security exceptions are design decisions** - if a library needs trusted-mode style escape hatches, that should be reviewed explicitly rather than normalized.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Resource loading pattern | Recommended use of `resourceUrl`, `loadScript`, or `loadStyle` |
| Versioning plan | Naming and packaging guidance for safe upgrades and rollback |
| Security review findings | Risks around CSP, global access, and repeated library loading |

---

## Related Skills

- `lwc/lifecycle-hooks` - use when the real bug is rerender timing or cleanup around one-time initialization.
- `lwc/lwc-security` - use when the library choice raises deeper DOM or trust-boundary concerns.
- `lwc/lwc-performance` - use when large asset payloads or repeated initialization hurt page responsiveness.
