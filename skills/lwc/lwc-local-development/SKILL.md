---
name: lwc-local-development
description: "Use when previewing Lightning web components, Lightning apps, or Experience (LWR) sites in real time during development with Live Preview (formerly Local Dev) — the `sf lightning dev app` / `sf lightning dev site` / `sf lightning dev component` CLI commands and the Live Preview VS Code extension — including single-component preview with platform-module access (LDS wire adapters, `@salesforce` scoped modules, Apex controllers) and knowing which edits live-reload vs need a manual redeploy. Triggers: 'preview my LWC without deploying', 'set up local dev live reload', 'run sf lightning dev component', 'why don't new @api properties show on save'. NOT for Jest unit testing (use lwc/lwc-testing), NOT for the Apex/Flow Unified Testing / Test Discovery & Test Runner APIs (a separate, LWC-unrelated capability), and NOT for CI/production deployment."
category: lwc
salesforce-version: "Winter '26+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "how do I preview my Lightning web component without deploying it to the org first"
  - "set up local development so my LWC changes reload live in the browser as I save"
  - "why don't my new @api properties or wire adapter changes show up when I save during live preview"
  - "run sf lightning dev component to preview a single LWC in isolation with real Apex data"
  - "preview my Experience Cloud LWR site locally before I publish it"
tags:
  - lwc-local-development
  - live-preview
  - local-dev
  - sf-lightning-dev
  - single-component-preview
inputs:
  - "An authenticated SFDX project (sfdx-project.json) connected to a sandbox or scratch org"
  - "The LWC bundle, Lightning app, or Experience (LWR) site you want to preview"
  - "The @salesforce/plugin-lightning-dev CLI plugin installed, or the Live Preview VS Code extension"
  - "For mobile app preview: Xcode (iOS) or Android Studio (Android)"
outputs:
  - "A running local Live Preview server rendering the component/app/site with real-time reload"
  - "Guidance on which sf lightning dev command to use and which edits need a manual redeploy vs live-reload"
  - "A preview-session runbook and a local-dev readiness check over the project"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-07
---

# LWC Local Development

This skill activates when a developer wants to see Lightning web component changes rendered in real time **without a full deploy cycle** — using Live Preview (the tooling formerly branded "Local Dev"). It covers the three `sf lightning dev` CLI commands, the Live Preview VS Code extension, single-component preview with platform-module access, and the edit categories that live-reload versus those that force a manual refresh or redeploy. It is a development-workflow capability, distinct from Jest unit testing (`lwc/lwc-testing`) and unrelated to the Apex/Flow Unified Testing APIs.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm you're targeting a non-production org.** Live Preview works against production, sandbox, and scratch orgs, but Salesforce recommends running it against **sandbox or scratch orgs only** — preview loads real org data and metadata into a local server. Have an authenticated SFDX project (`sfdx-project.json`) pointed at that org.
- **Install the plugin or extension.** The commands come from the versioned `@salesforce/plugin-lightning-dev` CLI plugin (`sf plugins install @salesforce/plugin-lightning-dev`). The Live Preview VS Code extension wraps the single-component flow in the IDE. On first run the CLI prompts you to enable the feature — press Enter / `y`. Enabling requires the **View Setup** and **Customize Application** permissions.
- **Know it's LWC-only.** Live Preview cannot render Aura components: "Live Preview only lets you preview Lightning web components. You can't use it to test Aura components in your app or site preview." An app or site that mixes Aura will preview the LWC parts only.
- **Respect the maturity nuance.** The overall app/site preview tooling is **GA**. Single-component preview (`sf lightning dev component`) was **Beta as of Winter '26** — the release that added platform-module access — and reached **GA as "Single Component Live Preview" starting the week of April 13, 2026**. In the VS Code extension, LWC preview is GA while **React component preview is Beta**. Do not state a maturity the release notes don't give.

---

## Core Concepts

### The three preview commands

Live Preview exposes three CLI commands, each backed by the `plugin-lightning-dev` plugin. All take a required `-o/--target-org` and an optional `-n/--name`:

| Command | Previews | Notable flags |
|---|---|---|
| `sf lightning dev app` | A Lightning Experience app on desktop or the Salesforce mobile app | `-t/--device-type desktop\|ios\|android`, `-i/--device-id` |
| `sf lightning dev site` | An Experience Builder (LWR) site in the browser | `-n/--name` (site name) |
| `sf lightning dev component` | A single LWC in isolation | `-n/--name` (component), `-c/--client-select` (pick in-browser) |

The server watches your local source and pushes changes to the running preview as you save.

### Live-reload vs manual refresh — the critical distinction

Most edits hot-reload, but a specific set of changes do **not** and need a manual step. This is the single biggest source of "my change isn't showing up" confusion.

**Auto-reloads on save:**
- HTML/template attribute changes
- Basic CSS revisions
- References to new components
- JavaScript method changes that don't alter the public API
- Newly added or deleted files (since Spring '25)

**Requires a manual redeploy (apps/sites) or browser refresh (single component):**
- New `@api` properties or methods
- **Wire adapter modifications** — config, imports, `@wire` decorator changes, GraphQL queries
- Importing a new `@salesforce` scoped module
- Updates to `.js-meta.xml` files
- Service component library revisions

For `app`/`site` preview, run `sf project deploy start` for the changed metadata and restart the server; for `component` preview, refresh the browser page.

### Single-component preview and platform-module access

`sf lightning dev component` renders one component on a dedicated preview page, decoupled from any app or record page. As of Winter '26 it "supports access to platform modules, such as Lightning Data Service wire adapters, `@salesforce` scoped modules, and Apex controllers" — so a component that reads live data through LDS wires or Apex renders with real org data, not just static mocks. Use `-c/--client-select` to choose which component to preview from the browser.

### What it does NOT cover

- **Aura components** — not previewable at all.
- **Mobile app preview** requires the native SDKs: **Xcode** (iOS) or **Android Studio** (Android); the CLI prompts to install the Salesforce mobile app if needed. Experience LWR sites preview on desktop only.
- **Jest unit tests** run independently of the preview server — Live Preview is not a test runner.
- **The Unified Testing / Test Discovery & Test Runner APIs** are a separate Winter '26 capability scoped to **Apex and Flow** tests, surfaced through the Application Test Execution page in Setup. They have no connection to LWC or to `sf lightning dev component`.

---

## Common Patterns

### Single-component inner loop

**When to use:** iterating on one component's markup, styling, or logic against real org data, without wiring it into an app or record page.

**How it works:** from the project root run `sf lightning dev component -o mySandbox` (add `-n myComponent` or `-c` to select), then edit the bundle. Template/CSS/JS-method edits reload live; when you add an `@api` property or change a `@wire`, refresh the browser. The component pulls LDS/Apex data through its normal wires.

**Why not the alternative:** deploying and clicking through an app page for every tweak is slow and pollutes the org with iteration noise; single-component preview keeps the loop local and fast.

### Full-app preview, including mobile

**When to use:** verifying a component in the context of a real Lightning app, or checking behavior on the Salesforce mobile app.

**How it works:** `sf lightning dev app -o mySandbox -n MyApp` for desktop; add `-t ios` or `-t android` (with Xcode / Android Studio installed) to preview in a simulator. Metadata edits that fall in the "manual" list need `sf project deploy start` plus a server restart.

**Why not the alternative:** single-component preview can't reproduce app-level navigation, layout, or cross-component interactions.

### Experience (LWR) site preview

**When to use:** previewing LWR Experience Cloud site changes before publishing.

**How it works:** `sf lightning dev site -o mySandbox -n MySite` renders the site locally in the browser. This is desktop-only; Aura sites are not supported (see `lwc/lwr-site-development` for the publish-freeze model).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Iterating on one component's UI/logic | `sf lightning dev component` | Isolated, fast, still gets LDS/Apex data |
| Component depends on app navigation or sibling components | `sf lightning dev app` | Only app preview reproduces app-level context |
| Verifying on phone / Salesforce mobile app | `sf lightning dev app -t ios\|android` | Requires Xcode / Android Studio |
| Previewing an LWR Experience site | `sf lightning dev site` | Desktop-only site preview |
| The component is an Aura component | Not supported — deploy and test in-org | Live Preview is LWC-only |
| Change not appearing after save | Check the manual-reload list; redeploy or refresh | `@api`, `@wire`, `@salesforce`, and `.js-meta.xml` edits don't hot-reload |
| Need to run assertions on the component | Use Jest (`lwc/lwc-testing`), not preview | Live Preview renders; it doesn't assert |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — confirm an authenticated SFDX project against a **sandbox or scratch** org, the `View Setup` + `Customize Application` permissions, and `@salesforce/plugin-lightning-dev` installed (`sf plugins --core` / `sf plugins install @salesforce/plugin-lightning-dev`).
2. **Pick the command** — component vs app vs site from the Decision Guidance table; add `-t ios|android` only if the native SDK is present.
3. **Start the preview** — run the command with `-o <org>` (and `-n`/`-c` as needed); on first run press Enter to enable the feature.
4. **Edit and observe** — make changes and watch for live reload; when a change is in the manual list (`@api`, `@wire`, `@salesforce` imports, `.js-meta.xml`), redeploy (`sf project deploy start`) + restart for apps/sites, or refresh the browser for a single component.
5. **Validate readiness** — run `scripts/check_lwc_local_development.py --project-dir <root>` to flag Aura bundles that can't be previewed and LWC bundles missing a valid `.js-meta.xml`.
6. **Hand off to real tests** — Live Preview confirms rendering; run Jest (`lwc/lwc-testing`) and deploy through the normal pipeline for anything beyond visual iteration.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Preview ran against a sandbox or scratch org, not production
- [ ] The correct command was used for the surface (component / app / site) and any mobile SDK was present
- [ ] Changes in the manual-reload list were redeployed or the browser refreshed — not assumed to hot-reload
- [ ] No Aura component was expected to render via Live Preview
- [ ] Maturity was stated correctly (single-component preview: Beta in Winter '26, GA week of April 13, 2026; React-in-VS-Code preview: Beta)
- [ ] Final verification did not rely on preview alone — Jest and a real deploy still ran

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`@api` / `@wire` / `.js-meta.xml` edits don't hot-reload** — new public properties, wire adapter changes, new `@salesforce` imports, and metadata-file edits require a manual redeploy (apps/sites) or a browser refresh (single component). The server keeps running and shows the stale build, so it looks like your change "did nothing."
2. **Aura silently doesn't preview** — Live Preview renders LWC only. A mixed app previews its LWC parts and quietly omits Aura, which can look like a broken component rather than an unsupported one.
3. **Running against production is allowed but discouraged** — the CLI won't stop you, but preview pulls org data locally; Salesforce recommends sandbox/scratch. Treat a production target as a red flag, not a convenience.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Running Live Preview server | Local server from `sf lightning dev component/app/site` rendering with real-time reload |
| `templates/lwc-local-development-template.md` | A preview-session runbook: command selection, enable steps, and the live-reload vs manual-refresh cheat sheet |
| `scripts/check_lwc_local_development.py` | Stdlib readiness check: flags Aura bundles and LWC bundles missing/invalid `.js-meta.xml`, warns if `sfdx-project.json` is absent |

---

## Related Skills

- `lwc/lwc-testing` — Jest unit testing for LWC; the assertion layer Live Preview does **not** provide. Use both: preview to see it, Jest to prove it.
- `lwc/lwr-site-development` — the LWR Experience Cloud model, including the publish-time freeze that `sf lightning dev site` lets you sidestep during iteration.
- `devops/unlocked-package-development` — the deploy/packaging pipeline that takes over once local iteration is done.
