---
name: lwc-debugging-devtools
description: "Use when you need to diagnose live Lightning Web Component behavior in the browser — setting breakpoints, stepping through @wire emits, inspecting component state with the Lightning Component Inspector, reading wire-adapter network traffic, and interpreting symptoms like silent render failures or 'works in dev but not in prod'. Triggers: 'how to set breakpoint in lwc', 'source maps missing', 'enable debug mode', 'lightning inspector chrome extension', 'lwc wire not emitting'. NOT for Jest test failures — use `lwc-testing` — and NOT for Apex debug logs, which are an Apex debugging concern. Specific runtime error messages (wire undefined, querySelector returns null, NavigationMixin errors) belong in `common-lwc-runtime-errors`; this skill covers the debug TOOLING itself."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "how to set a breakpoint inside a lightning web component"
  - "source maps are missing in chrome devtools for my lwc"
  - "how do i enable debug mode for my user in salesforce"
  - "which chrome extension is the lightning component inspector"
  - "my @wire adapter is not emitting and i cannot tell why"
  - "lwc silent render fail how do i diagnose a blank component"
  - "my lwc works in dev sandbox but not in production"
  - "console.log prints proxy handle instead of object in lwc"
  - "how to profile lwc render performance in chrome devtools"
  - "how to debug an lwc in experience cloud or mobile app"
tags:
  - lwc-debugging-devtools
  - debug-mode
  - chrome-devtools
  - lightning-inspector
  - source-maps
  - runtime-diagnosis
  - lightning-web-security
  - experience-cloud-debugging
inputs:
  - "the runtime symptom (blank render, silent wire, thrown error, slow render)"
  - "the target environment: Lightning Experience, Experience Cloud, or the Salesforce Mobile app"
  - "whether Debug Mode is currently enabled for the acting user"
  - "the component bundle path (e.g., force-app/main/default/lwc/myComponent)"
  - "browser version and whether the Lightning Component Inspector is installed"
outputs:
  - "a reproducible diagnosis path from symptom to root cause"
  - "a devtools workflow (breakpoint placement, wire network filter, Inspector state capture)"
  - "guidance on LWS-safe logging and object unwrapping"
  - "performance profile interpretation when render cost is the concern"
  - "checker output from scripts/check_lwc_debugging_devtools.py"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# LWC Debugging DevTools

Use this skill when an LWC compiles and deploys cleanly but misbehaves at runtime, and the next step is live browser debugging — breakpoints, the component tree inspector, wire network traces, and render profiles — rather than static code review. This skill is about the tooling; specific error-message diagnosis lives in `common-lwc-runtime-errors`.

---

## Before Starting

Gather this context before touching devtools:

- **Is Debug Mode enabled for the acting user?** Debug Mode is toggled per user under Setup → Debug Mode. Without it, the org serves minified LWC JavaScript, source maps are absent, and breakpoints land on unreadable framework code.
- **Which surface is failing?** Lightning Experience, Experience Cloud, and the Salesforce Mobile app each have different security policies, CSP rules, and debug affordances. A bug that reproduces in LEX may not reproduce in an Experience Cloud site because the CSP is stricter there.
- **Is Lightning Web Security (LWS) active?** LWS sandboxes module globals and wraps `this.template` and many records with Proxies. Under LWS, `console.log(this.record)` often prints a Proxy handle that looks empty — not because the object is empty, but because the logger cannot traverse the wrapper.
- **What is the reproducing path?** Record ID, page, user profile, and the exact action. Debug Mode slows the app noticeably; you do not want to hunt blind.

---

## Core Concepts

### Debug Mode Is Per User, Not Per Org

Salesforce serves minified LWC bundles by default for performance. Enabling Debug Mode for a specific user replaces the minified bundle with un-minified JavaScript and serves source maps. That means: you can enable Debug Mode for yourself to investigate a ticket without affecting any other user. End users continue to see the fast, minified version. Debug Mode lives in Setup and is also exposed to each user via their own Debug Mode page. It does not live under "Production Settings" — a common hallucination.

### Source Maps, Breakpoints, and the Sources Panel

With Debug Mode on and a hard refresh, Chrome DevTools' Sources panel shows the original component files under a virtual path that includes the component namespace and bundle name. You can set breakpoints by clicking the gutter, or by dropping a `debugger;` statement in the component (remove before commit). The Sources panel is also where you toggle "Pause on caught exceptions" — essential for catching errors that LWS or the framework swallows before they reach your listener. The top of the call stack will usually be your component code; frames lower in the stack belong to the LWC engine and `@salesforce/*` modules.

### The Lightning Component Inspector

The Lightning Component Inspector is an Anthropic-era Chromium extension that adds a panel to DevTools. It shows the component tree for the current page, the `@api` property values on any selected component, and the current state of each `@wire` on that component (loading, data, error). It is the fastest way to answer "is the wire emitting at all, and what is it returning?" without writing logging code. It is Chromium-only; there is no Firefox equivalent.

### Logging Under Lightning Web Security

LWS wraps many platform objects in membrane Proxies so that component code cannot reach into privileged internals. `console.log(obj)` with a Proxy-wrapped object often shows the handle, not the traversed contents. The workaround is to force a plain JSON copy: `console.log(JSON.parse(JSON.stringify(obj)))` or, when the structure is known to be clonable, `console.log(structuredClone(obj))`. Non-JSON-clonable values (functions, `Map`, `Set`) still need ad-hoc unwrapping.

### Wire Traffic on the Network Panel

UI API wire adapters (`getRecord`, `getRelatedListRecords`, the GraphQL adapter) hit `/services/data/vXX.X/ui-api/*`. Filter the Network panel by `/ui-api/` to see exactly which wires fire, their payload shape, and any 4xx/5xx. If a wire "never emits," there are two common causes: a reactive `$variable` is still `undefined`, so the adapter was never activated; or the adapter ran and the response was cached with `undefined` data (no fields requested).

### Render Profiling and Mobile

The Performance panel captures long tasks, render frames, and script execution for the LWC runtime. For mobile debugging, the Salesforce Mobile app exposes a debug bridge that lets desktop Chrome DevTools attach to the in-app webview; pair this with Debug Mode for the mobile user.

---

## Common Patterns

### Pattern 1: Prove the Wire Is Firing

**When to use:** `@wire` appears not to emit, component shows no data.

**How it works:** Enable Debug Mode, hard-refresh, open Network and filter by `/ui-api/`. Place a breakpoint on the first line of the wire handler function. Reproduce. If the breakpoint never hits and no network call fires, the reactive parameter is `undefined`; inspect the class property feeding `$recordId` in the Inspector panel. If the breakpoint hits with `data: undefined, error: undefined`, that is the normal first emission — step and watch for the second emission.

**Why not the alternative:** `console.log` alone tells you nothing about whether the adapter was activated at all.

### Pattern 2: Capture a Silent Render Failure

**When to use:** Component renders blank in production, works in dev sandbox.

**How it works:** Confirm Debug Mode is enabled for the prod user (this is the frequent miss), hard-refresh, open Sources, enable "Pause on exceptions" and "Pause on caught exceptions." Reproduce. If a throw is caught by LWS or the framework error boundary, the debugger pauses at the origin so you can read the real message instead of a swallowed one. Use the Inspector to confirm which child component is actually failing.

**Why not the alternative:** Relying on the browser console alone misses errors that LWS silently wraps or that a parent `errorCallback` swallows.

### Pattern 3: Readable Logging Under LWS

**When to use:** You need to dump component state and plain `console.log` shows a Proxy handle.

**How it works:** `console.log('state', JSON.parse(JSON.stringify(this.account)));` — this materializes the wrapped object into a plain JSON tree the console can expand. For shapes that include `Map`/`Set` or circular refs, log individual fields instead of the whole object.

**Why not the alternative:** `console.log(this.account)` in LWS shows `Proxy {}` or similar, making the log useless for diagnosing data shape.

---

## Decision Guidance

| Symptom | Start Here | Why |
|---|---|---|
| Component renders blank | Confirm Debug Mode is on, open Sources with pause-on-exceptions, scan for thrown errors | Many render failures are swallowed by framework error boundaries or LWS |
| `@wire` never emits | Network panel filtered by `/ui-api/`, breakpoint at top of wire handler | Distinguishes "adapter never activated" from "adapter returned empty" |
| Works in dev, fails in prod | Check Debug Mode status in the prod user; check CSP/Experience Cloud context | Minified code without source maps is the single biggest "I can't see anything" cause |
| Console logs show Proxy handles | Wrap with `JSON.parse(JSON.stringify(obj))` or log individual fields | LWS proxies block the default console traversal |
| Render feels slow | Performance panel, record a 10s profile around the interaction | Gives per-frame render cost and long-task attribution |
| Bug only reproduces on mobile | Enable Debug Mode for the mobile user, attach desktop Chrome via mobile debug bridge | No parity tool exists inside the mobile app itself |

---

## Recommended Workflow

1. **Enable Debug Mode for your user** — Setup → Debug Mode (or the per-user Debug Mode page). Confirm the badge appears in the app nav.
2. **Hard-refresh and confirm un-minified JS** — DevTools → Sources → search for your bundle filename. You should see readable code, not a single-line minified blob.
3. **Install the Lightning Component Inspector** — Chromium extension; reload the page; confirm the "Lightning" panel appears in DevTools.
4. **Reproduce with Pause on Exceptions on** — toggle both caught and uncaught pausing; reproduce the user action; let the debugger catch any thrown error.
5. **Inspect component state and wire responses** — use the Inspector to read `@api` values and wire state; use the Network panel filter `/ui-api/` to see raw wire payloads.
6. **Capture a Performance profile if perf-related** — record during the slow interaction; inspect long tasks and render frames.
7. **Disable Debug Mode when finished** — Debug Mode noticeably degrades perceived performance; leaving it on in production pollutes analytics and user experience.

---

## Review Checklist

- [ ] Debug Mode is enabled for the acting user (not assumed org-wide).
- [ ] Un-minified source is visible in the Sources panel after a hard refresh.
- [ ] The Lightning Component Inspector is installed and the Lightning panel appears.
- [ ] Any object logging under LWS uses `JSON.parse(JSON.stringify(...))` or per-field logs — not raw `console.log(this.x)`.
- [ ] `debugger;` statements are removed from the code before commit.
- [ ] Network filter `/ui-api/` was used (not just console) to confirm wire behavior.
- [ ] Debug Mode was turned off after the session so end users do not see degraded performance.
- [ ] CSP differences were considered when the bug is Experience Cloud or mobile-specific.

---

## Salesforce-Specific Gotchas

1. **Debug Mode is per user, not per org** — enabling it for yourself does not help an end user who is also seeing the bug; either enable it for their user, or reproduce under your own user.
2. **`console.log(this.record)` under LWS prints a Proxy handle** — looks like the object is empty; it is not. Unwrap with `JSON.parse(JSON.stringify(...))`.
3. **Breakpoints are meaningless without source maps** — without Debug Mode, the Sources panel shows minified code and your breakpoints land on the wrong line or a wrapper.
4. **The Lightning Component Inspector is Chromium-only** — Firefox users have no equivalent; switch to Chrome/Edge/Brave.
5. **`renderedCallback` breakpoints fire many times** — they run after every render. Use conditional breakpoints on a specific prop value or log-points to avoid storming the debugger.
6. **Experience Cloud CSP is stricter than LEX** — "works in LEX, fails in Experience Cloud" is often a Content Security Policy issue surfacing on a different surface.
7. **Leaving Debug Mode on globally is an anti-pattern** — real users see degraded perf, and analytics get skewed; always turn it off when the investigation ends.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Diagnosis path | Ordered devtools steps from symptom to root cause |
| Wire network trace | Filtered `/ui-api/` requests with payload and timing |
| Inspector capture | Component tree state, `@api` values, `@wire` state for the failing component |
| Performance profile summary | Long tasks, render frames, attributable scripts |
| Checker report | Output from `scripts/check_lwc_debugging_devtools.py` |

---

## Related Skills

- `lwc/common-lwc-runtime-errors` — use when the browser console shows a specific error message (wire undefined, querySelector null, NavigationMixin error); that skill is about error meanings, this one is about the debugging tools themselves.
- `lwc/lwc-performance` — use when the finding from a Performance profile points to payload or render cost that needs architectural fixes.
- `lwc/lwc-security` — use when the debugging session surfaces LWS or CSP behavior that needs to be understood structurally.
- `lwc/lwc-testing` — use when the right fix is a Jest test rather than a live browser debug session.
