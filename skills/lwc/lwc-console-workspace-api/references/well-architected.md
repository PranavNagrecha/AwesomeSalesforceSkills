# Well-Architected Notes — LWC Console Workspace API

## Relevant Pillars

- **User Experience** — Service Console agents work across many tabs simultaneously. The workspace API gives developers explicit control over tab placement, labeling, and refresh — turning the workspace into a coherent multi-record surface instead of a chaotic tab pile. Dynamic labels, icon badges, and respecting the agent's focused tab when opening new content materially reduce cognitive load during multi-case workflows.
- **Operational Excellence** — Console-aware LWCs that branch on `IsConsoleNavigation` are reusable: the same component runs in App Builder previews, Experience Cloud, and Service Console without per-environment forks. The fallback discipline ("every workspace-API call has a non-console path") is the operational equivalent of `try/catch` on platform code — it makes the bundle robust to future platform changes and admin reuse beyond the original deployment surface.
- **Reliability** — The workspace API throws when called outside a console host. A component that ignores `IsConsoleNavigation` is one App Builder preview away from a visible error. Robust wiring of the context detection plus per-promise rejection handling means the component degrades gracefully across host shifts (Aura → LWC framework changes, Experience Cloud preview, mobile container, future console rewrites).

## Architectural Tradeoffs

- **`lightning/platformWorkspaceApi` (LWC) vs. `lightning:workspaceAPI` (Aura).** The LWC modules supersede the Aura interface for new development — they're statically-imported, tree-shakeable, and TypeScript-friendly via the public LWC type definitions. The Aura interface is still supported for legacy components; migrate as part of normal LWC-modernization work, not as a standalone effort.
- **`getEnclosingTabId` vs. `getFocusedTabInfo`.** Enclosing is "the tab I'm in" (stable for the component's lifetime). Focused is "the tab the user is on" (mutable, changes when the user clicks elsewhere). Picking the wrong one causes refreshes on the wrong tab — silently and intermittently. Default to `getEnclosingTabId` unless the component is intentionally cross-tab (utility bar, message-driven background action).
- **`refreshTab` vs. `refreshApex`.** `refreshTab` invalidates the LDS cache for the tab; `refreshApex` re-runs a specific imperative-Apex-backed wire. Use `refreshTab` for record pages where multiple wires depend on the same record. Use `refreshApex` for narrowly-scoped imperative wires that don't go through LDS. Both is fine when both paths exist in the same component.

## Anti-Patterns

1. **Unconditional workspace-API calls.** Skipping `IsConsoleNavigation` makes the component work only in console hosts and silently throw elsewhere. Always wire the detection and provide an explicit non-console path.
2. **Persisting `tabId` across page reload.** Tab ids are opaque and ephemeral. Store domain identifiers (recordId) and re-resolve to tab id when needed.
3. **`refreshTab`-then-assert without microtask tick.** Tests that don't await one microtask after `refreshTab` are intermittently flaky. The refresh dispatches a signal; LDS re-runs wires asynchronously.
4. **`setTabLabel` on every wire emission.** Causes flicker. Compare displayed values before calling; debounce to meaningful record changes.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- `lightning/platformWorkspaceApi` Module Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-platform-workspace-api.html
- `lightning/platformUtilityBarApi` Module Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-platform-utility-bar-api.html
- Use Workspace and Utility Bar APIs in Lightning Web Components — https://developer.salesforce.com/docs/platform/lwc/guide/use-workspace-api.html
- Service Console Customization (Aura → LWC migration context) — https://developer.salesforce.com/docs/platform/lwc/guide/use-aura-methods.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
