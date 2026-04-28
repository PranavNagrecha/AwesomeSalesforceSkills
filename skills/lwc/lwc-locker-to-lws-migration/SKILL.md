---
name: lwc-locker-to-lws-migration
description: "Migrating LWCs from Lightning Locker Service to Lightning Web Security (LWS) — flipping the org switch safely, identifying components likely to break, removing Locker workarounds that are now insecure, and validating third-party libraries that previously failed under SecureWindow/SecureElement proxies. NOT for Aura → LWC migration — see lwc/aura-to-lwc-migration. NOT for general LWC security review (XSS, public-API hardening) — see lwc/lwc-security and lwc/lwc-public-api-hardening."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - lwc
  - locker
  - lws
  - migration
  - security
  - third-party-libraries
  - csp
  - sandboxing
triggers:
  - "third-party library X works in Locker but not LWS"
  - "do I need to migrate before LWS becomes mandatory"
  - "how to test LWS before switching the org"
  - "what does securewrapper return now under LWS"
  - "jest tests pass under Locker but break after enabling LWS"
  - "library that broke under Locker — will it work under LWS"
  - "how to roll back if LWS breaks something in production"
inputs:
  - "List of LWC bundles (and their lwc.config.json / *.js-meta.xml files) deployed to the org"
  - "Inventory of third-party libraries loaded as static resources (charting, signing, PDF, crypto)"
  - "Current LWS-for-LWC toggle state on Session Settings (per-org Locker vs LWS state)"
  - "Components that historically depended on force:hasRecordId / force:hasSObjectName Aura interfaces"
  - "Existing Jest test suite and any jest.config.js mocks added to work around Locker proxies"
outputs:
  - "Per-component risk classification (safe, needs-shim, manual-test-required)"
  - "List of Locker-only workarounds in the codebase that should be removed (or hardened) before flipping LWS on"
  - "A pre-flight test plan covering sandbox enablement, smoke flow per Lightning page, and third-party-library exercise list"
  - "Runbook for the org switch covering who flips it, in which sandbox first, rollback steps, and comms"
  - "Updated Jest configuration (canvas / DOM polyfills no longer required under LWS — what to remove vs keep)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# LWC Locker → Lightning Web Security (LWS) Migration

Activate this skill when an org is preparing to flip from **Lightning Locker Service** (the old per-namespace JavaScript sandbox built on `SecureWindow`/`SecureElement` proxies) to **Lightning Web Security (LWS)**, the modern replacement based on JavaScript realms and standards-based browser primitives. LWS went GA for LWC in Spring '23, became the default for new orgs shortly after, and Salesforce has announced Locker for LWC will be retired — every org will eventually run on LWS.

The migration is a **per-org switch** controlled by the **"Use Lightning Web Security for Lightning web components"** setting on **Session Settings** (the metadata field is `SecuritySettings.lwsForLwcEnabled`; the older Locker-disable flag persists as `lws.disabled` in some legacy docs). Flipping it is one click — but the JavaScript runtime under every LWC changes, so the work is in **inventorying what could break, exercising it in a sandbox, and removing now-redundant Locker workarounds**.

This skill is NOT for Aura → LWC migration (see `lwc/aura-to-lwc-migration`) and NOT for generic LWC security review (see `lwc/lwc-security` and `lwc/lwc-public-api-hardening`). It is specifically the runbook for the Locker → LWS cutover.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Where the org sits today.** Is the org already on LWS (default for orgs created after Spring '23)? Check **Setup → Session Settings → "Use Lightning Web Security for Lightning web components."** If the box is checked, you are already on LWS — this skill becomes a clean-up exercise (remove obsolete Locker shims), not a migration.
- **Aura coexistence.** LWS for **LWC** and Locker for **Aura** are independent toggles. Flipping LWS on for LWC does NOT migrate Aura components — they continue to run under Aura Locker. Plan the LWC cutover without assuming Aura comes along.
- **Third-party library inventory.** Every library loaded via `loadScript`/`loadStyle` from a static resource is a migration risk surface. Chart.js, D3, jsPDF, PDF.js, signature pads, OCR libs, crypto libs, anything that touched `window`/`document` or used `eval`/`Function()` for hot paths — list them.
- **Locker-era workarounds in the codebase.** Search for `// LOCKER:`, `SecureElement`, `SecureWindow`, `unwrap()`, deep cloning before passing into a third-party lib, manual `JSON.parse(JSON.stringify(...))` to "escape the proxy" — these are now dead weight (and sometimes actively harmful under LWS).
- **The most common wrong assumption.** That LWS is "stricter" than Locker. It is not — LWS is **less intrusive at runtime** (no SecureElement proxy wrapping every DOM node) but **more strict at the realm boundary** (cross-namespace access is harder, prototype pollution is contained per-realm). Things that broke under Locker often **just work** under LWS; the regressions are concentrated in cross-namespace and prototype-extending code.
- **No partial rollout.** The setting is org-wide for LWC, not per-component. There is no "enable LWS for these 12 components only." Plan to flip it everywhere, in a sandbox, on a defined date.

---

## Core Concepts

### 1. Locker proxies vs LWS realms

Locker wraps every DOM node and every `window` reference your component touches in a `SecureElement` / `SecureWindow` **proxy**. The proxy filters property access to enforce per-namespace isolation. The cost: third-party libraries see a proxy, not a real `Element`, and many of them perform `instanceof HTMLElement` checks, prototype walks, or property descriptor lookups that the proxy doesn't satisfy. This is why Chart.js 2.x, jsPDF, and many DOM-touching libs needed elaborate workarounds under Locker.

LWS uses **JavaScript realms** (the same primitive that powers `<iframe>` isolation in browsers) instead. Each component's code runs in its own realm with its own copy of the built-in prototypes (`Array.prototype`, `Object.prototype`, etc.). The DOM nodes your code receives are **real DOM nodes** — `instanceof HTMLElement` is true, property descriptors look exactly like the spec, DevTools shows the actual element rather than `Proxy {}`. Third-party libraries see what they expect.

The cost is at the boundary: passing an object **between realms** (e.g., from a parent component in namespace `A` to a child in namespace `B`) causes a structured-clone-style copy. Functions don't transfer cleanly across realms, so you cannot pass a callback from one namespace into a library running in another namespace and expect identity.

### 2. The org switch and how LWS gets enabled

The setting lives at **Setup → Session Settings → Lightning Web Security for Lightning web components**. Metadata API exposes it on the `SecuritySettings` type. There is **no per-component opt-in/opt-out** for LWC — it is the entire org's LWC runtime, all at once.

For Aura, a separate **Lightning Web Security for Aura components** toggle controls whether Aura components run under LWS or under Aura Locker. As of Spring '25 this is still rolling out (treat as pilot/GA-rolling, verify per-org), so don't promise an unrelated team that flipping LWC also moves Aura.

`force:hasRecordId` and `force:hasSObjectName` are **Aura interfaces** historically used by Aura components to receive context. LWC equivalents are the `@api recordId` and `@api objectApiName` properties exposed automatically when a component is placed in a record context. Migrating to LWS does not change LWC's recordId/objectApiName behaviour — but if you have legacy LWCs that were exposed inside an Aura wrapper purely to consume `force:hasRecordId`, the wrapper is no longer required (and the LWC can be placed directly).

### 3. What changes for `eval`, `new Function()`, and dynamic code

Locker **blocked** `eval()` and `new Function()` outright in the per-component sandbox. Many libraries shipped a "Locker-compatible" build that pre-compiled templates or used a different code path to avoid these primitives.

LWS does **not** unconditionally block `eval`. It enforces the page's CSP policy, which on Lightning Experience disallows `unsafe-eval` for hosted code by default — but a library shipped via `<script>` from a Salesforce static resource and evaluated inside the LWS realm runs against the realm's CSP, which historically permits more than Locker did. **In practice:** assume `eval` and `new Function` are still off-limits at the page-CSP level for production code, but Locker-era pre-compilation workarounds may now be unnecessary because the library's standard build runs correctly under LWS.

Critical caveat for LLM-generated code: do **not** "unblock" Locker-era restrictions by reaching for `eval` "because LWS allows it now." LWS is not a license to ship `eval`-based code — the workaround was insecure under Locker and remains insecure under LWS. See `references/llm-anti-patterns.md`.

### 4. Cross-namespace, postMessage, and iframes

Locker filtered cross-namespace property access at the proxy boundary, which made some `postMessage` patterns awkward (you'd receive a proxy, not the raw message data). LWS uses realm boundaries: messages crossing a realm are structurally cloned, so:

- `postMessage` to/from an `<iframe>` works with **standard DOM semantics** — the message is a structured clone, no proxy unwrapping required.
- Cross-namespace component-to-component calls (parent in `acme__`, child in `widgets__`) cross a realm boundary; identity is not preserved across the hop.
- A function passed across realms is **not callable** on the other side. Use events with structured-cloneable detail payloads, not callbacks.

---

## Common Patterns

### Pattern 1: Library that broke under Locker, works native under LWS

**When to use:** any third-party library shipped as a static resource that needed Locker-era patches, custom shims, or a "Locker-compatible" fork.

**How it works:**
1. Identify the library (search `loadScript` / `loadStyle` callers).
2. Find the Locker workaround (a fork, a patched build, a shim file, or a `JSON.parse(JSON.stringify(x))` deep-clone before passing data in).
3. Switch back to the upstream build.
4. Remove the shim.
5. In a sandbox with LWS enabled, exercise the library's hot path (render a chart, generate a PDF, sign a signature pad, etc.).
6. Confirm DevTools shows real DOM nodes, not Proxy objects, in the library's render target.

**Why not "just leave the workaround in":** Locker-era shims often deep-clone data on the way in to escape the proxy. Under LWS, the deep-clone is now pure overhead and frequently strips functions / class identity that the library expected to preserve, causing **new** bugs.

### Pattern 2: Sandbox exercise plan before flipping production

**When to use:** every Locker → LWS cutover. Never flip in production without exercising in at least one sandbox first.

**How it works:**
1. In a Full or Partial sandbox, enable **LWS for LWC** in Session Settings.
2. Open every Lightning page that hosts custom LWCs (App Pages, Record Pages, Quick Actions, Utility Bar items, Experience Cloud sites).
3. Exercise every third-party-library-driven feature (charts render, PDFs download, signature captured, file uploads chunk correctly).
4. Open DevTools and confirm: no `Proxy {...}` wrappers in component logs, no console errors that mention `SecureElement` / `SecureWindow` / `[object SecureWindow]`.
5. Re-run the org's LWC Jest suite — many Locker-only mocks (e.g., `jest-canvas-mock` injected because Locker proxies confused canvas tests) may no longer be necessary; remove what is now unused.
6. Document any regressions, fix in the sandbox, then plan the production cutover with a rollback window.

**Why not "just flip prod and watch":** the switch is org-wide. There is no graceful per-component rollback — you either toggle the setting back off (which restores Locker for everyone) or you ship code fixes. Sandbox exercise is the only way to make the production flip uneventful.

### Pattern 3: Identifying components likely to break

**When to use:** triage step before the sandbox exercise — narrows the manual-test list.

**How it works:** scan the LWC bundles for these signals (the skill-local checker `scripts/check_lwc_locker_to_lws_migration.py` automates this):

- Direct references to `SecureElement`, `SecureWindow`, `SecureDocument`, `SecureObject` — Locker-only types that no longer exist under LWS.
- Calls to `unwrap()` / `getRawNode()` / `LightningElement.prototype` walking — Locker-era tricks.
- Static resource loads of known-broken-under-Locker libraries (Chart.js < 3.x patched builds, jsPDF < 2.x with custom forks, D3 v4 patched build) — likely have shims to remove.
- `instanceof HTMLElement` guards followed by a fallback path — the fallback was for Locker proxies and is now dead code.
- Jest mocks named `*-locker-shim*`, `mock-secure-window*`, or that explicitly set up `window` polyfills — likely obsolete under LWS.

**Why not just rely on automated tests:** Jest doesn't run inside Locker or LWS — Jest runs in Node with `@lwc/jest-preset`. Test passes are necessary but **not sufficient** evidence the runtime change is safe; manual sandbox exercise is required for any DOM/library-dependent feature.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org created after Spring '23, no custom LWCs predate it | Verify LWS is on, do a one-pass scan to remove Locker shims if any, no migration runbook needed | Org is already on LWS by default; this is hygiene, not migration |
| Org has custom LWCs from Winter '23 or earlier loading 5+ third-party libs | Full sandbox exercise + library-by-library smoke test before flipping | Highest concentration of Locker-era workarounds; library compat is the dominant risk |
| Org needs LWS but one critical library has documented LWS incompatibility | Stay on Locker, file with vendor / upgrade the library, retest, then flip | Better to delay than ship a broken page; per-component opt-out does not exist |
| Component uses `eval` / `new Function` for "Locker workaround" reasons | Remove the workaround, refactor to a non-eval pattern, then flip LWS | `eval` was insecure under Locker and remains insecure under LWS; LWS is not a license to keep it |
| Aura wrapper exists only to consume `force:hasRecordId` and forward to an LWC | Place the LWC directly on the page using `@api recordId`, retire the Aura wrapper | LWS migration is a good moment to retire Aura-only adapters |
| Cross-namespace component passes callbacks between parent and child | Refactor to events with structured-cloneable `detail` payloads before flipping LWS | Functions don't cross realm boundaries; callbacks silently break under LWS |

---

## Recommended Workflow

1. **Read the org state.** Check **Session Settings → Lightning Web Security for LWC** for the current toggle. Check Setup → Salesforce release notes for the active release to confirm LWS is GA in this org's instance. Note whether the Aura LWS toggle is on.
2. **Inventory the surface.** Collect: every LWC bundle path, every static resource loaded via `loadScript`/`loadStyle`, every third-party library version, every Jest mock specifically added for Locker. Build a CSV / table.
3. **Run the static checker.** `python3 skills/lwc/lwc-locker-to-lws-migration/scripts/check_lwc_locker_to_lws_migration.py <path-to-lwc-bundles>` to flag Locker-only references (`SecureElement`, `SecureWindow`, `unwrap()`, etc.) and known-suspect library names.
4. **Classify each component** as `safe` (no Locker-specific code, no third-party DOM lib), `needs-shim-removal` (has Locker workarounds to delete), or `manual-test-required` (loads a third-party library or touches `window`/`document` directly).
5. **Enable LWS in a sandbox.** Pick a Full or Partial Copy sandbox. Flip the Session Settings toggle. Exercise every `manual-test-required` component on every page where it appears. Capture DevTools console for errors.
6. **Remove obsolete workarounds.** Strip Locker shims, replace patched library builds with upstream, drop now-unnecessary Jest mocks. Re-run Jest.
7. **Plan the production cutover.** Pick a low-traffic window. Communicate to stakeholders. Identify the rollback path (toggle back off → Locker is restored, but redeployed code stays). Flip in production. Monitor for 24–48 hours.

---

## Review Checklist

- [ ] **Org switch state confirmed** — Session Settings inspected; current state (Locker / LWS) explicitly recorded
- [ ] **Static checker clean** — `check_lwc_locker_to_lws_migration.py` reports no `SecureElement` / `SecureWindow` / `unwrap()` references remain
- [ ] **Third-party libraries verified** — every library loaded via `loadScript`/`loadStyle` has been exercised in a sandbox under LWS
- [ ] **Locker-era shims removed** — patched library forks replaced with upstream; deep-clone-on-input workarounds deleted
- [ ] **Jest config rationalised** — Locker-only mocks (canvas polyfills, SecureWindow stubs) removed if no longer needed; suite still passes
- [ ] **Cross-namespace callbacks audited** — no function passed across realm boundaries between parent and child in different namespaces
- [ ] **Rollback runbook documented** — clear steps to flip the setting back if production exhibits an unrecoverable regression

---

## Salesforce-Specific Gotchas

1. **The toggle flips the entire org's LWC runtime at once** — there is no per-component or per-page LWS opt-in. Treat the flip as a release event, not a per-feature feature flag. (See `references/gotchas.md` for what happens to in-flight user sessions.)
2. **`SecureElement`/`SecureWindow` references are silent failures, not loud errors** — under LWS, code that reads `instanceof SecureElement` simply evaluates to `false` (the global no longer exists), which often steers code into a stale fallback path rather than throwing. Static scan for these symbols **before** flipping.
3. **Aura LWS is a separate toggle and lags LWC LWS** — don't assume that flipping LWC LWS also moves Aura components. Aura components remain on Aura Locker until the (separate) Aura LWS toggle is enabled, and that feature has had its own GA timeline.
4. **Third-party libraries that "broke under Locker" usually work under LWS — but the reverse can also happen** — a library that depended on a Locker-side effect (rare, but real for libs that probed for the proxy as a fingerprint) can break under LWS. The sandbox exercise is the only reliable check.
5. **`force:hasRecordId` Aura wrappers around LWCs become redundant** — once on LWS, an LWC placed directly on a record page receives `recordId` via `@api`. Retire wrappers as a clean-up step; do not retire them in the same change as the LWS flip — keep the changes separable for rollback clarity.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Component risk classification | Spreadsheet/table of every LWC bundle marked `safe` / `needs-shim-removal` / `manual-test-required` |
| Static checker report | Output of `scripts/check_lwc_locker_to_lws_migration.py` listing Locker-only references with file paths and line numbers |
| Sandbox exercise log | Per-component manual-test record (page exercised, browser, third-party feature exercised, pass/fail, DevTools snippet) |
| Workaround removal diff | Pull request or change-set diff that strips Locker shims, deep-clone hacks, and patched library forks |
| Production cutover runbook | Step-by-step doc: who flips, in which sandbox first, comms plan, monitoring window, rollback steps |
| Updated Jest config | Cleaned-up `jest.config.js` with Locker-only mocks (canvas, SecureWindow) removed where they are no longer needed |

---

## Related Skills

- `lwc/lwc-security` — general LWC security posture (XSS, sanitisation, CSP) — orthogonal to the runtime sandbox change LWS represents
- `lwc/lwc-public-api-hardening` — hardening `@api` boundaries; relevant because LWS realm boundaries make cross-namespace `@api` cleaner
- `lwc/lwc-testing` — Jest patterns; informs which Locker-only mocks can be retired
- `lwc/aura-to-lwc-migration` — separate migration; LWS migration is a good prompt to also retire residual Aura wrappers
- `lwc/common-lwc-runtime-errors` — diagnosing the runtime errors that show up immediately after flipping LWS in a sandbox
