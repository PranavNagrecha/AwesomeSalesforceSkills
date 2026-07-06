---
name: multi-framework-ui-bundles
description: "Use when building, deploying, or reviewing a React web app that runs natively on Salesforce via Salesforce Multi-Framework and the UIBundle metadata type — scaffolding with `sf template generate ui-bundle`, data access through @salesforce/sdk-data (createDataSDK, GraphQL, Apex fetch), App Launcher / Custom Application / Experience targeting, and embedding Agentforce chat with the Agentforce Conversation Client. Open Beta: scratch orgs and sandboxes only, English default language, no production deploys. NOT for standard Lightning Web Component development (use lwc/* skills), NOT for Lightning Out 1.0 / Visualforce embedding, and NOT for authoring LightningTypeBundle UI overrides (use agentforce/agentforce-custom-lightning-types)."
category: lwc
salesforce-version: "Spring '26+ (API 66.0+, Open Beta)"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "build a React app that runs natively on Salesforce instead of LWC"
  - "scaffold a ui-bundle project with sf template generate and deploy it to a sandbox"
  - "query Salesforce data from a React app using the @salesforce/sdk-data package"
  - "embed an Agentforce chat experience in a React app with the Conversation Client"
  - "deployed my UIBundle but the app doesn't show up in the App Launcher"
tags:
  - multi-framework
  - uibundle
  - react-on-salesforce
  - ui-bundle
  - agentforce-conversation-client
inputs:
  - "The org type and API version you're targeting (scratch org / sandbox; UIBundle needs API 66.0+)"
  - "The frontend framework and app concept (React is the supported beta framework)"
  - "The intended surface: App Launcher via Custom Application, or an Experience Cloud external site"
  - "Whether the app needs an embedded Agentforce agent conversation (ACC)"
outputs:
  - "A source-format uiBundles/<app>/ package with a valid .uibundle-meta.xml (masterLabel, version, isActive, target)"
  - "A React project preconfigured with the Multi-Framework SDK, Vite, Vitest, shadcn/ui, and Tailwind CSS"
  - "Data-access wiring via createDataSDK() — GraphQL queries and Apex fetch() with no hand-rolled token management"
  - "A deployment manifest at API 66.0+ and a beta-restriction go/no-go assessment"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-06
---

# Multi-Framework UI Bundles

This skill activates when a practitioner wants to build or ship a **React app that runs natively on Salesforce** using **Salesforce Multi-Framework** — a framework-agnostic runtime on the Agentforce 360 Platform — packaged and deployed as the **UIBundle** metadata type. It covers scaffolding, the UIBundle meta XML contract, data access through the Multi-Framework SDK, surfacing the app (App Launcher / Experience), and embedding an Agentforce agent conversation via the Agentforce Conversation Client (ACC).

**Maturity flag (do not soften):** Multi-Framework is in **open beta** — available only in **scratch orgs and sandboxes that use English as the org default language**. Beta apps **cannot be deployed to production orgs**. The ACC Web SDK carries its own **Beta** label, and embedding React components directly into Lightning pages as micro-frontends is a narrower **closed pilot** (Spring 2026).

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the org qualifies.** Only scratch orgs and sandboxes with English as the default org language can run Multi-Framework during the beta. If the ask is "ship this to production," the honest answer is *not yet* — plan around the beta boundary.
- **Confirm Setup enablement.** The Salesforce app domain must be enabled for the org under **React Development with Salesforce Multi-Framework** in Setup before a UIBundle deploy will work.
- **Check the API floor.** `UIBundle` exists from **Metadata API version 66.0**; the `CustomApplication` target (now the default) is available from **67.0**, where the older `AppLauncher` target is deprecated.
- **Kill the biggest wrong assumption early:** this is not "React replaces LWC." Multi-Framework runs *alongside* LWC — existing Lightning Web Components keep working, and the two coexist in the same org.

---

## Core Concepts

### The UIBundle metadata type

The Metadata API defines a UIBundle as representing "the UI of a Salesforce Multi-Framework app, such as a React app." It lives in a `uiBundles/<your_app>/` folder with a `.uibundle-meta.xml` descriptor. The meta XML has three required fields — `masterLabel` (name shown in the UI), `version` (version identifier of the web app), and `isActive` (controls accessibility) — plus optional `description`, `target`, and `isProtected` (internal use only). A single UIBundle can contain **up to 2,500 files**, and `package.xml` manifests support the `*` wildcard for the type.

### Targets: where the app surfaces

The optional `target` field decides where users find the app:

| Target | Meaning | Availability |
|---|---|---|
| `CustomApplication` | Pairs with a CustomApplication so the app shows in the **App Launcher**. Default when unspecified. | API 67.0+ |
| `AppLauncher` | Legacy direct App Launcher target. | **Deprecated in 67.0** — use CustomApplication |
| `Experience` | External-facing site/portal; the app appears in the **Digital Experiences** app. | — |

### The Multi-Framework SDK and data access

The scaffolded React app ships with the Multi-Framework SDK. Data flows through the **`@salesforce/sdk-data`** package: query records via **GraphQL**, invoke Apex methods through the SDK's **`fetch()`** method, and read user/context info through UI APIs. The `createDataSDK()` utility "handles authentication automatically so no token management is required in the application code" — you never hand-roll OAuth in the app.

### Agentforce Conversation Client (ACC)

ACC is the prebuilt conversational UI for embedding an **Agentforce Employee Agent** chat into a React (or other external) app. It functions as a **Lightning Web Component Interface (LWCI) built on Lightning Out 2.0**, so you drop a pre-built ACC UI container into the app instead of hand-building chat. Interactive responses (e.g., flight bookings, property listings) render dynamically from **Lightning Types** rather than hardcoded components. The ACC Web SDK is documented with its own **Beta** label.

---

## Common Patterns

### Scaffold-first internal app (Custom Application target)

**When to use:** an internal team needs a rich React UI (dashboards, wizards, dense grids) surfaced through the App Launcher.

**How it works:** run `sf template generate ui-bundle` — it generates a starter React app under `force-app/main/default/uiBundles`, preconfigured with the Multi-Framework SDK, Vite, Vitest, shadcn/ui, and Tailwind CSS. Develop locally on the Vite dev server (default `localhost:5173`), read data via `createDataSDK()`, then build and push with standard deploy commands. The app is discoverable in the App Launcher post-deployment.

**Why not the alternative:** wrapping a React SPA in Visualforce or an iframe forfeits the platform's built-in authentication, security, and governance, and leaves you managing tokens by hand.

### Agent-embedded app (ACC)

**When to use:** the React app should include a conversational Agentforce experience — a support console, a booking assistant — without building chat UI from scratch.

**How it works:** embed the ACC container (LWCI on Lightning Out 2.0) into the React app; the agent's interactive outputs render dynamically from Lightning Types. Pair with `agentforce/agentforce-custom-lightning-types` when the agent's action output needs custom rendering.

**Why not the alternative:** re-implementing chat over raw APIs means rebuilding streaming, rendering, and session plumbing that ACC already provides — and it won't pick up Lightning-Type-driven interactive UI.

### AI-generated bundle (Agentforce Vibes 2.0)

**When to use:** rapid prototyping. Multi-Framework connects to Agentforce Vibes 2.0: describe the component in natural language and Vibes generates the React code, GraphQL queries, and Salesforce metadata (including the UIBundle files) automatically. Review the generated metadata against this skill's checklist before deploying.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Team needs a production app this quarter | LWC (`lwc/*` skills), not Multi-Framework | Beta apps cannot be deployed to production orgs |
| Internal React app for a sandbox pilot | UIBundle + `CustomApplication` target | Default target from 67.0; surfaces in App Launcher |
| External-facing portal experience | UIBundle `Experience` target | Marks the app as an external site; appears in Digital Experiences |
| App needs Salesforce data | `@salesforce/sdk-data` via `createDataSDK()` | GraphQL + Apex `fetch()` with automatic auth |
| App needs an agent conversation | Embed ACC | Prebuilt LWCI on Lightning Out 2.0; Lightning-Type-driven rendering |
| Want React *inside* a Lightning page | Wait / treat as closed pilot | Lightning-page micro-frontend embedding is in closed pilot (Spring 2026); App Builder drag-and-drop is unsupported in beta |
| Existing LWC estate | Keep it; add React beside it | Multi-Framework runs alongside LWC, it doesn't replace it |

---

## Recommended Workflow

1. **Gate on the beta boundary** — confirm the target is a scratch org or sandbox with English default language, and that the requirement tolerates "no production during beta." If not, route to LWC.
2. **Enable and verify Setup** — enable the Salesforce app domain under **React Development with Salesforce Multi-Framework** in Setup; confirm CLI + Node.js v18+ locally.
3. **Scaffold** — run `sf template generate ui-bundle`; inspect the generated `uiBundles/<app>/` folder and its `.uibundle-meta.xml` (masterLabel, version, isActive; pick `CustomApplication` or `Experience` target).
4. **Build data access** — wire `createDataSDK()` from `@salesforce/sdk-data`; use GraphQL for record reads and the SDK `fetch()` for Apex; never add manual token handling.
5. **Develop and test locally** — iterate on the Vite dev server (`localhost:5173`); run Vitest; keep the deployable bundle to built output well under the 2,500-file cap.
6. **Deploy and verify** — push at API 66.0+ (67.0+ for `CustomApplication`), then open the App Launcher (or Digital Experiences for `Experience`) and confirm the app loads with platform auth. Run `scripts/check_multi_framework_ui_bundles.py` against the metadata tree first.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Target org is a scratch org or sandbox with English default language; no production deploy is promised
- [ ] Salesforce app domain enabled in **React Development with Salesforce Multi-Framework** in Setup
- [ ] `.uibundle-meta.xml` has `masterLabel`, `version`, and `isActive`; target is `CustomApplication` or `Experience` (not deprecated `AppLauncher`)
- [ ] Manifest API version is 66.0+ (67.0+ when using the `CustomApplication` target)
- [ ] Bundle ships built output only — file count is comfortably under 2,500 (no `node_modules/`, no `.env`)
- [ ] Data access goes through `createDataSDK()` / `@salesforce/sdk-data`; no hand-rolled OAuth or stored tokens
- [ ] Any Lightning-page micro-frontend embedding is flagged as closed pilot, not committed scope

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The beta wall is org-shaped, not feature-shaped** — everything works in your scratch org, then the release plan collapses because beta apps cannot be deployed to production orgs and non-English-default orgs are excluded. Surface this in the first estimate, not the last sprint.
2. **`AppLauncher` target quietly aged out** — samples written against API 66.0 use `target=AppLauncher`; from 67.0 it's deprecated and `CustomApplication` is the default. Old snippets deploy but point at the deprecated path.
3. **The 2,500-file cap punishes lazy packaging** — a React project's source tree plus `node_modules` is tens of thousands of files. Only the built app belongs in the bundle; blowing the cap fails the component, not just a lint rule.

See `references/gotchas.md` for the full list.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `uiBundles/<app>/*.uibundle-meta.xml` | UIBundle descriptor: masterLabel, version, isActive, optional description/target |
| React app under `force-app/main/default/uiBundles/` | Vite + Vitest + shadcn/ui + Tailwind starter with the Multi-Framework SDK |
| `package.xml` | Manifest with `<name>UIBundle</name>` (wildcard `*` supported) at version 66.0+ |
| Beta go/no-go note | Org-type, language, and production-restriction assessment for stakeholders |

---

## Related Skills

- `agentforce/agentforce-custom-lightning-types` — author the Lightning Types that drive ACC's dynamic interactive rendering inside the embedded chat.
- `lwc/lwc-graphql-wire` — the classic LWC GraphQL wire adapter; compare with the SDK's GraphQL access when deciding React vs LWC for a data-heavy UI.
- `lwc/lwr-site-development` — LWR-based external sites; the GA alternative to a beta `Experience`-target UI bundle for portal work.
