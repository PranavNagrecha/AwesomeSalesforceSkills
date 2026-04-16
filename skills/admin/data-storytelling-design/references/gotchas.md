# Gotchas — Data Storytelling Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: No Platform-Enforced "Executive Summary" Widget Exists in CRM Analytics

**What happens:** Practitioners search the Analytics Studio widget palette for an "executive summary" or "narrative" widget type, expecting a built-in component. No such widget exists.

**Impact:** Practitioners without knowledge of text widgets either deliver dashboards with no narrative context (chart grids) or attempt to recreate narratives using chart titles, which are too small and non-dynamic.

**How to avoid:** All narrative in CRM Analytics must be built with text widgets. Text widgets support dynamic value binding. Treat the text widget as the primary narrative tool, not a secondary annotation.

---

## Gotcha 2: Smart Data Discovery Narrative API Does Not Auto-Embed in CRM Analytics Dashboards

**What happens:** Practitioners enable Einstein Discovery and expect the machine-generated insight narrative to automatically appear in CRM Analytics dashboards. The narrative API exists but produces text that must be consumed by custom code.

**Impact:** Teams expect to find narrative in their existing dashboards after enabling Smart Data Discovery and are surprised to find nothing changed.

**How to avoid:** The Smart Data Discovery narrative REST API (`/wave/smartdatadiscovery/narratives`) must be explicitly called and the response embedded in a custom LWC, Visualforce page, or Experience Cloud component. It does not inject into existing dashboards automatically.

---

## Gotcha 3: Animated Page Mode Locks Interactive Filters

**What happens:** CRM Analytics animated page mode (presentation mode) disables interactive filter controls during playback. Dashboard widgets become non-interactive.

**Impact:** Presenters using animated mode cannot respond to audience questions by applying live filters without exiting presentation mode, which breaks the visual flow.

**How to avoid:** If live filter interaction is needed during presentation, design the dashboard for interactive use rather than animated page mode. Use animated mode only for auto-play presentations with no audience interaction.
