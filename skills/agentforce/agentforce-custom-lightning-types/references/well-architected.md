# Well-Architected Notes — Agentforce Custom Lightning Types

## Relevant Pillars

- **Security** — a renderer/editor LWC runs in the user's session and receives the action's
  data payload via `@api value`. Treat that payload as data to display, not to re-query: don't
  use the editor/renderer to perform unbounded SOQL or expose fields the running user can't
  see. Respect CRUD/FLS in any Apex the component calls, and only annotate fields with
  `@AuraEnabled` that are safe to surface in the agent UI.
- **Operational Excellence** — the override is channel-scoped, so the same type can present
  differently (or fall back to default) across desktop, mobile, chat, and Experience Builder.
  Track which channel folders a bundle ships and verify each surface after deploy; a missing
  folder is a silent gap, not an error.
- **Performance** — keep editor/renderer LWCs lightweight; they render inline in the agent
  conversation. Avoid heavy imperative work on render.
- **Reliability** — because the Apex class is the source of truth for the projected schema,
  changing the class changes the contract; coordinate Apex and bundle changes so the LWC never
  receives fields it doesn't expect.

## Architectural Tradeoffs

- **Custom UI vs. typed simplicity.** Overriding the UI improves the agent experience but adds
  metadata and an LWC to maintain per channel. Use it where presentation genuinely matters
  (cards, interactive inputs, lists); leave low-value actions on the default UI.
- **Editor logic vs. Apex validation.** A custom editor can validate before submit, but pushing
  all validation into the LWC can duplicate server-side rules. Keep authoritative validation in
  Apex and use the editor for UX affordances, not as the only gate.
- **Per-property vs. whole-type override.** A `"$"` whole-type override is simplest; per-property
  overrides give finer control at the cost of more components to maintain. Start with `"$"`.

## Anti-Patterns

1. **Re-skinning a non-Apex action** — attempting to override an action whose input/output is a
   primitive. It silently no-ops; fix the Apex signature instead.
2. **One channel, assumed everywhere** — shipping only `lightningDesktopGenAi` and assuming
   mobile/chat inherit it. They fall back to the default UI with no warning.
3. **Display logic in the data contract** — returning pre-formatted display strings from Apex so
   the default UI "looks right," instead of returning typed fields and rendering them in the LWC.

## Official Sources Used

- Enhance the Agent UI with Custom LWCs and Lightning Types (Agentforce) — https://developer.salesforce.com/docs/ai/agentforce/guide/lightning-types.html
- Custom Lightning Types (Einstein GenAI) — https://developer.salesforce.com/docs/einstein/genai/guide/lightning-types-custom.html
- Core Concepts of Custom Lightning Types — https://developer.salesforce.com/docs/platform/lightning-types/guide/lightning-types-core.html
- Apex-Based Custom Lightning Types — https://developer.salesforce.com/docs/platform/lightning-types/guide/lightning-types-apex.html
- Lightning Type UI Configuration (componentOverrides) — https://developer.salesforce.com/docs/platform/lightning-types/guide/lightning-types-ui-config.html
- Top-Level Editor & Renderer Override example (Agentforce) — https://developer.salesforce.com/docs/ai/agentforce/guide/lightning-types-example-full-editor-renderer.html
- Metadata API Developer Guide — LightningTypeBundle — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_lightningtypebundle.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
