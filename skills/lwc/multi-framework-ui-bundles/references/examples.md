# Examples — Multi-Framework UI Bundles

All code below is illustrative scaffolding authored from the official Metadata API reference
and the Salesforce Multi-Framework GA announcement (July 2026). Multi-Framework is **GA** —
production, sandbox, Developer Edition, and scratch orgs on **Summer '26 (API 67.0)** or
later. The GA SDK package is `@salesforce/platform-sdk`; the beta-era `@salesforce/sdk-data`
no longer ships. API version target: `66.0`+ for `UIBundle` itself, `67.0`+ for the
`CustomApplication` target.

## Example 1: Scaffold and describe a UI bundle

**Context:** an internal ops team wants a React dashboard surfaced in the App Launcher of a
sandbox pilot org.

**Problem:** hand-assembling a React + Salesforce project means wiring bundler, tests, SDK,
and metadata layout yourself — and getting the UIBundle descriptor contract wrong.

**Solution:**

Scaffold with the Salesforce CLI:

```bash
sf template generate ui-bundle
```

This generates a starter React app under `force-app/main/default/uiBundles`, preconfigured
with the Multi-Framework SDK, Vite (bundling), Vitest (testing), shadcn/ui (components), and
Tailwind CSS (styling).

Source layout (bundle folder plus descriptor):

```text
force-app/main/default/
└── uiBundles/
    └── opsDashboard/
        ├── opsDashboard.uibundle-meta.xml
        └── ... (built app assets — up to 2,500 files per UIBundle)
```

`opsDashboard.uibundle-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<UIBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Ops Dashboard</masterLabel>
    <version>1.0.0</version>
    <isActive>true</isActive>
    <description>React operations dashboard (Multi-Framework beta pilot).</description>
    <target>CustomApplication</target>
</UIBundle>
```

**Why it works:** `masterLabel`, `version`, and `isActive` are the required fields;
`CustomApplication` (available in API 67.0+, and the default if you omit `target`) pairs the
bundle with a Custom Application so it appears in the App Launcher. The older `AppLauncher`
target is deprecated in 67.0.

---

## Example 2: Read data with the Multi-Framework SDK

**Context:** the dashboard needs live Account data and a server-side rollup computed in Apex.

**Problem:** models and developers reflexively reach for OAuth flows and REST clients — but a
UI bundle runs inside the platform's session, and hand-rolled token management is both
unnecessary and a security smell.

**Solution:** use `@salesforce/platform-sdk` (the GA name; `@salesforce/sdk-data` was the
beta package and no longer ships). The `createDataSDK()` factory handles authentication
automatically, so no token management appears in application code. Records are queried via
GraphQL and Apex methods are invoked through the SDK's `fetch()` method.

```javascript
// data.js
import { createDataSDK, gql } from '@salesforce/platform-sdk';

const sdk = await createDataSDK(); // awaited at GA; auth handled by the platform

// GraphQL read — note `.query()` with a `query` key, and optional chaining on the result
export async function loadAccounts(MY_QUERY) {
    const result = await sdk.graphql?.query({ query: MY_QUERY });
    return result?.data?.uiapi?.query?.Account?.edges;
}

// GraphQL write — `.mutate()` with a `mutation` key
export async function saveAccount(MY_MUTATION, input) {
    return sdk.graphql?.mutate({ mutation: MY_MUTATION, variables: { input } });
}

// Server-side logic via Apex, invoked through the SDK's fetch()
export async function loadRollup() {
    return sdk.fetch(/* Apex method reference + params */);
}
```

**Why it works:** the SDK is the sanctioned data plane for UI bundles — GraphQL for reads,
`fetch()` for Apex, UI APIs for user/context info — and it keeps credentials out of the
JavaScript bundle entirely.

---

## Example 3: Deployment manifest and verification

**Context:** ship the bundle to a sandbox and confirm users can reach it.

`package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>*</members>
    <name>UIBundle</name>
  </types>
  <version>67.0</version>
</Package>
```

Deploy and verify:

```bash
# Local dev first: Vite dev server (default http://localhost:5173)
npm run dev

# Build, then push with standard deploy commands
sf project deploy start --manifest package.xml
```

After deployment, search for the app's `masterLabel` in the **App Launcher**
(`CustomApplication` target) or find it in the **Digital Experiences** app (`Experience`
target).

**Why it works:** `UIBundle` supports the `*` wildcard in `package.xml`, is available from
API 66.0, and deploys like any other source-format metadata. Prerequisite: the Salesforce app
domain must be enabled for the org in **React Development with Salesforce Multi-Framework**
in Setup, or the org won't serve the app.

---

## Example 4: Embed an Agentforce conversation (ACC)

**Context:** the dashboard should include an Agentforce Employee Agent assistant so users can
ask questions ("which orders are stuck?") without leaving the app.

**Problem:** building chat UI from scratch means re-implementing streaming, message rendering,
and interactive result display.

**Solution:** drop in the **Agentforce Conversation Client (ACC)** — a Lightning Web
Component Interface (LWCI) built on **Lightning Out 2.0** that embeds a prebuilt
conversational UI container into non-LWC stacks, including React apps, external dashboards,
and Tableau. Interactive agent outputs (e.g., flight bookings, property listings) render
dynamically from **Lightning Types**, not hardcoded components. ACC supports token-by-token
streaming, brand theming, a Floating Action Button entry point, and an Inline Mode for a
designated parent container.

Integration sketch (conceptual — follow the ACC Developer Guide for the exact embed code; the
ACC Web SDK is labeled **Beta**):

```text
React app (UI bundle)
└── ACC container (LWCI on Lightning Out 2.0)
    ├── conversation stream ←→ Agentforce Employee Agent
    └── interactive outputs rendered from Lightning Types
        └── custom rendering? → agentforce/agentforce-custom-lightning-types
```

**Why it works:** ACC is the platform's own conversation surface — it inherits agent
capabilities (including Lightning-Type-driven UI) that a hand-built chat over raw APIs would
have to re-create.

---

## Anti-Pattern: shipping the source tree as the bundle

**What practitioners do:** commit the entire React project — `node_modules/`, `src/`,
`.env`, source maps — into `uiBundles/<app>/` and deploy.

**What goes wrong:** a UIBundle component is capped at **2,500 files**; `node_modules` alone
is typically tens of thousands, so the deploy fails — and even below the cap you'd be
shipping dependency source and possibly secrets (`.env`) into org metadata.

**Correct approach:** keep the app source in the project, put only the **built** output in
the bundle folder, and let `scripts/check_multi_framework_ui_bundles.py` flag `node_modules`,
dotenv files, and file counts near the cap before every deploy.
