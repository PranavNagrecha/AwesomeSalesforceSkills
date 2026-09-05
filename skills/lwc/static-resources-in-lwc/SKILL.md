---
name: static-resources-in-lwc
description: "Use when packaging third-party JavaScript, CSS, or asset files into Salesforce static resources for Lightning Web Components, including `@salesforce/resourceUrl`, `loadScript`, `loadStyle`, zip pathing, versioning, and CSP-safe delivery. Also covers the StaticResource `-meta.xml` (cacheControl Private vs Public, contentType), `lwc:dom=\"manual\"` containers for DOM-owning libraries, and Jest-mocking the resource loader. NOT for npm-bundled code that ships through the build pipeline or server-side integration assets — use security/csp-and-trusted-urls."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Performance
  - Operational Excellence
  - Security
tags:
  - static-resources
  - resource-url
  - platform-resource-loader
  - third-party-library
  - csp
  - cache-control
triggers:
  - "how do i load a static resource in lwc"
  - "loadscript is not working in lightning web components"
  - "path inside zipped static resource in lwc"
  - "third party javascript library in salesforce"
  - "static resource versioning strategy"
  - "resourceUrl loadScript static resource salesforce lwc"
  - "load chart.js or d3 from a static resource in lwc"
  - "chart reinitializes every time the component rerenders"
  - "cannot use import statement outside a module after loadScript"
  - "set cacheControl public or private on a static resource"
  - "styles from a static resource leak into other components"
  - "mock platformResourceLoader and resourceUrl in a jest test"
  - "library appendChild renders but ignores my css in lwc"
  - "resource url 404 for a file inside the zip"
  - "use a static resource in a lightning web component"
inputs:
  - "which library or asset is being loaded and whether it is zipped"
  - "whether the resource is JavaScript, CSS, images, fonts, or a mixed asset pack"
  - "whether Lightning Web Security or CSP constraints are affecting the load path"
  - "whether the resource content is safe for unauthenticated internet traffic"
  - "whether the resource ships in, or is consumed from, a managed package"
outputs:
  - "static-resource loading pattern for LWC with versioning and guard rails"
  - "review findings for CSP, duplicate loading, and pathing mistakes"
  - "implementation guidance for script, style, or asset references"
  - "deployable StaticResource -meta.xml, LWC bundle, package.xml, and Jest test"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when a component needs code or assets that do not belong inline in the bundle. Static resources are the supported way to bring third-party libraries and packaged assets into Salesforce UI, but they work well only when loading is deliberate, one-time, and compatible with Salesforce security boundaries.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the dependency really an external library, or should it be solved with a native base component or local LWC code first?
- Will the resource be a single file, a zip archive with nested paths, or a reusable asset pack?
- Does the component need JavaScript execution, stylesheet loading, or only a URL to an image or font?

---

## Questions to Ask Before Configuring

Ask these before uploading anything. Each one maps to a failure in
`references/gotchas.md` that costs a redeploy — or a security review — after the fact.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which build of the library are we packaging — UMD, IIFE, or ESM?" | `loadScript` does not support ES modules; an ESM build deploys cleanly and defines nothing | The exact filename to zip, before anyone debugs a silent no-op |
| "Is this content safe for unauthenticated internet traffic?" | `cacheControl` is an access decision: `Public` is readable by anyone once cached | The `cacheControl` value, decided on content sensitivity rather than page speed |
| "Does the library write its own DOM, or does it only return data?" | DOM-owning libraries need an empty `lwc:dom="manual"` container; without it the engine does not preserve encapsulation | The template shape, and whether `disconnectedCallback()` has cleanup to do |
| "Does the library ship a stylesheet, and how broad are its selectors?" | In synthetic shadow, CSS loaded with `loadStyle` is global — it leaks into every component on the page | A second file in the archive, plus a decision on whether its selectors are safe org-wide |
| "What is the exact path of every file inside the archive, and who else imports this resource?" | Consumers concatenate paths by hand, so the internal layout is a published contract; a packaged resource also needs its `ns__` prefix | The path list to put in `<description>`, the consumer list, and the version-bump rule |
| "Is the org on Lightning Web Security or Lightning Locker, and does the library create globals, call `eval()`, or scan the whole document?" | Under Locker those are hard blockers, not warnings; under LWS a library that sets `"use strict"` needs changes | A go/no-go on the library before it is packaged, not after the first demo |
| "How large is the production build, and what is the org's current static-resource total?" | 5 MB per resource and 250 MB per org are deploy-time ceilings, and the org total is nobody's job to watch | A trimmed archive (no source maps, tests, or `node_modules`) and a headroom number |

What a proper configuration adds over just uploading the file: the library loads exactly once per component instance through a supported path, the archive layout is a documented contract instead of tribal knowledge, the caching policy matches the sensitivity of the bytes, and the Jest test fails when someone moves a file inside the zip.

---

## Core Concepts

Static resources separate packaged assets from component source and let Salesforce deliver them through supported platform mechanisms. In LWC, there are two common paths: reference the resource URL directly for assets such as images, or load executable files with `lightning/platformResourceLoader`. Problems start when teams mix those paths, rely on CDNs, or reload the same library on every render.

### `resourceUrl` Gives You A Stable Base Path

Importing `@salesforce/resourceUrl/Name` returns a deployable URL for the resource. For zipped assets, you append the internal file path yourself. That means naming and internal archive structure matter. If the zip changes shape between versions, every consumer path becomes part of the migration work. A resource that lives in a managed package is imported as `ns__Name`.

### `loadScript` And `loadStyle` Need A Real Lifecycle

`loadScript(this, url)` and `loadStyle(this, url)` should run from a controlled lifecycle path, usually `renderedCallback()` with a guard or another one-time initialization branch. Loading on every rerender creates duplicate initialization, event leaks, and inconsistent state. Both return promises: nothing the library defines exists until they resolve, so the initialization call belongs inside `then()` or after `await`, never on the next line. The loader is for supported static-resource delivery, not for arbitrary remote URLs.

### The `-meta.xml` Carries Two Required Decisions

Each resource needs a `<name>.resource-meta.xml` beside its content file. `contentType` and `cacheControl` are both required fields, and `cacheControl` has only two legal values. `Public` shares the cached bytes with all internet traffic including unauthenticated users; `Private` keeps them per-user, per-session, behind authentication. See `references/code-examples.md` § 2 for the decision table and the deployable XML.

### Security Boundaries Still Apply

Static resources are compatible with Salesforce CSP and Lightning Web Security in a way public CDN tags are not — the platform will not load JavaScript from a third-party site even through a Trusted URL. If a library needs elevated trust or direct global access, that is a design review point, not a default setting. The more a library expects to own the global browser environment, the higher the fit risk inside Salesforce UI.

### Versioning Is An Operational Concern

The resource name, archive structure, and consumer paths should support clean upgrades. A stable versioning convention such as `chartjs_4_4` or a package-level asset manifest makes rollouts and rollbacks much safer than overwriting ambiguous resource names repeatedly. Resource names allow only letters, digits, and underscores, must start with a letter, and must not end with an underscore or contain two consecutive underscores.

---

## Common Patterns

### One-Time Third-Party Library Loader

**When to use:** The component needs a JavaScript library for charts, maps, or specialized editors.

**How it works:** Import the resource URL, guard the loader in `renderedCallback()`, and initialize the library only after the script promise resolves. Aggregate the script and its stylesheet with `Promise.all` and attach a `catch` that resets the guard so a later render can retry.

**Why not the alternative:** Inline `<script>` tags or CDN URLs conflict with Salesforce security posture and bypass deployable asset control.

### Zipped Asset Pack With Explicit Paths

**When to use:** A library ships multiple files or an asset family belongs together.

**How it works:** Store the package as a zip static resource and construct paths from the resource base URL so every consumer uses the same internal structure. Record the layout in the resource's `<description>` — it is the only place it sits next to the artifact.

**Why not the alternative:** Uploading many loosely named resources creates drift and makes upgrades harder to coordinate.

### Manual-DOM Container For A Library That Owns Its Nodes

**When to use:** The library appends its own elements (D3, most charting and editor libraries).

**How it works:** Give it an empty native element carrying `lwc:dom="manual"`, hand it that element via `this.template.querySelector` — never `document` — and let the library's own stylesheet style the interior.

**Why not the alternative:** Without the directive the engine does not preserve encapsulation, and component CSS does not reach appended nodes anyway.

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
| Only the ESM build is available | Ask the vendor for a UMD/IIFE build, or bundle one | `loadScript` does not support ES modules |
| Asset must be editable by marketing in Experience Builder | Use a content asset (`@salesforce/contentAssetUrl`) instead | Content assets come from Salesforce Files, not a deploy |
| Library needs to write its own DOM | Empty container with `lwc:dom="manual"` | Preserves encapsulation for manually inserted DOM |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Justify and scope** — answer the Questions table above. Check `templates/lwc/patterns/` and the base components first; a library you do not add is a library you do not have to package, version, or security-review.
2. **Package the resource** — zip only the production UMD/IIFE build and its stylesheet, fix the internal layout, and write `<name>.resource-meta.xml` with `cacheControl` and `contentType` using `references/code-examples.md` § 2. Put the archive layout in `<description>`.
3. **Wire the component** — import `@salesforce/resourceUrl/<name>`, load in `renderedCallback()` behind a one-time boolean guard, aggregate with `Promise.all`, handle `catch`, and give a DOM-owning library an `lwc:dom="manual"` container. Copy from `references/code-examples.md` §§ 3–6; the bundle shape is `templates/lwc/component-skeleton/`.
4. **Test it locally** — write the Jest test from `references/code-examples.md` § 7: mock `lightning/platformResourceLoader` and each `@salesforce/resourceUrl` import, assert the exact archive path, assert one load across repeated renders, and assert the failure fallback. Config is `templates/lwc/jest.config.js`.
5. **Run the checker** — `python3 scripts/check_static_resources_in_lwc.py --manifest-dir force-app` and clear every SR001–SR008 finding (remote script tags, loading outside `renderedCallback()`, missing guard, unknown resource name, missing `cacheControl`/`contentType`, unchained promise, missing `lwc:dom="manual"`, orphaned `-meta.xml`).
6. **Deploy and verify** — `sf project deploy start --manifest manifest/package.xml --dry-run`, then deploy and run the `StaticResource` SOQL in `references/code-examples.md` § 9 to confirm `CacheControl`, `ContentType`, and `BodyLength` are what you intended.
7. **Record the contract** — fill in `templates/static-resources-in-lwc-template.md` with the archive layout, version convention, consumer list, and rollback plan, so the next upgrade is a diff rather than an excavation.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The dependency justifies itself over a native base component or local code path.
- [ ] Asset loading uses `resourceUrl` or `platformResourceLoader`, not remote script tags.
- [ ] Script or style loading is guarded against repeated rerender execution.
- [ ] Nothing the library defines is touched before its promise resolves.
- [ ] The packaged file is a UMD or IIFE build, not an ES module.
- [ ] `cacheControl` and `contentType` are set, and `Public` was a deliberate choice.
- [ ] Zip paths are documented and stable for every consumer.
- [ ] A DOM-owning library has an `lwc:dom="manual"` container and a teardown path.
- [ ] Versioning and rollback expectations are explicit.
- [ ] Security review covers any trust-elevation or global-library assumptions.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems (full detail, with
sources, in `references/gotchas.md`):

1. **CDN habits do not translate cleanly into LWC** - a library that works in generic web HTML often fails under Salesforce CSP or deployment controls.
2. **`renderedCallback()` can run many times** - loading a script there without a guard creates duplicate initialization and hard-to-debug side effects.
3. **Zip path changes are breaking changes** - consumers usually concatenate paths manually, so internal archive structure becomes part of the contract.
4. **Security exceptions are design decisions** - if a library needs trusted-mode style escape hatches, that should be reviewed explicitly rather than normalized.
5. **`loadScript` will not run an ES module** - the file downloads, nothing is defined, and there is no deploy-time warning.
6. **`Public` caching is an internet publication** - once cached, the bytes are reachable by unauthenticated traffic.
7. **`loadStyle` CSS is global in synthetic shadow** - it is the documented mechanism, not a bug, so a broad vendor stylesheet restyles the whole page.
8. **Component CSS cannot reach inside `lwc:dom="manual"`** - style the container and let the library's own stylesheet do the rest.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Resource loading pattern | Recommended use of `resourceUrl`, `loadScript`, or `loadStyle` |
| `StaticResource` `-meta.xml` | `cacheControl` + `contentType` per resource, with the archive layout in `<description>` |
| LWC bundle + Jest test | Guarded loader, manual-DOM container, mocked-loader test asserting the archive path |
| Versioning plan | Naming and packaging guidance for safe upgrades and rollback |
| Security review findings | Risks around CSP, global access, caching policy, and repeated library loading |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building it: the full bundle, `StaticResource` XML, `cacheControl` decision table, `package.xml`, `sf` commands, Jest test, and SOQL verification |
| `references/gotchas.md` | Something loads but misbehaves — double initialization, undefined globals, 404 inside the zip, leaking styles, unstyled library nodes, a rejected deploy |
| `references/llm-anti-patterns.md` | You are reviewing generated code, or want the detection hints the checker automates |
| `references/well-architected.md` | You need the pillar tradeoffs, or the official source behind a specific claim |
| `references/examples.md` | You want worked scenarios before committing to a packaging approach |
| `templates/static-resources-in-lwc-template.md` | Recording the packaging, loading, and security decisions for review |
| `scripts/check_static_resources_in_lwc.py` | Before every deploy: static analysis over `lwc/` bundles and `staticresources/` |

---

## Related Skills

- `lwc/lifecycle-hooks` - use when the real bug is rerender timing or cleanup around one-time initialization.
- `lwc/lwc-security` - use when the library choice raises deeper DOM or trust-boundary concerns.
- `lwc/lwc-performance` - use when large asset payloads or repeated initialization hurt page responsiveness.
- `lwc/lwc-css-and-styling` - use when the question is about scoping, SLDS hooks, or shadow-boundary CSS rather than about packaging the file.
- `lwc/lwc-chart-and-visualization` - use when the topic is choosing and tuning a charting approach; this skill only covers getting the library into the org.
- `lwc/lwc-locker-to-lws-migration` - use when a library that worked under Lightning Locker breaks after LWS is enabled.
- `lwc/lwc-testing` - use when the Jest setup itself, rather than the resource mock, is the problem.
