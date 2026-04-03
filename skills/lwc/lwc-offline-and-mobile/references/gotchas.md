# Gotchas — LWC Offline And Mobile

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Supported Mobile Capability Does Not Mean Universal Availability

**What happens:** A component compiles and works in one test device, but fails in another container or browser.

**When it occurs:** Teams assume the API is universally available because it exists in the codebase.

**How to avoid:** Check capability availability at runtime and provide intentional fallback behavior.

---

## Offline Assumptions Collapse At Submit Time

**What happens:** Users can fill out the screen, but the final action fails because the component relies on server calls with no degraded path.

**When it occurs:** Teams design for intermittent reading but not intermittent writing.

**How to avoid:** Decide explicitly what the component should do when the network disappears before save.

---

## Resume Behavior Is Part Of Mobile Correctness

**What happens:** The user backgrounds the app, comes back later, and the component shows stale or inconsistent state.

**When it occurs:** Components are designed only for uninterrupted sessions.

**How to avoid:** Test background/resume flows and refresh or reconcile state intentionally.
