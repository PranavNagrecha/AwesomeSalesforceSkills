# Well-Architected Notes — LWC Cross-Tab State Sync

## Relevant Pillars

- **User Experience** — Cross-tab sync makes a multi-tab workflow feel coherent: save in one tab, the other tabs immediately reflect the change. Without it, the second tab is silently stale and confidence in the data drops.
- **Reliability** — Treat cross-tab sync as best-effort signal, not a contract. Browsers can drop messages on backgrounded tabs; users may have storage disabled. Code that *requires* the sync to fire will misbehave for some users.

## Architectural Tradeoffs

- **BroadcastChannel vs. storage event:** Modern API vs. universal compatibility. Pick BroadcastChannel and provide a storage-event fallback only if old browsers are in scope.
- **Fan-out signal vs. payload:** Sending the full updated record across tabs is convenient but couples tabs and risks PII leakage. Sending just `{recordId, ts}` and letting receivers re-fetch is the cleaner pattern.
- **Synchronous vs. eventual consistency:** Cross-tab sync is eventually consistent. Don't make business logic depend on the second tab's view being current at any specific instant.

## Anti-Patterns

1. **Subscribe without unsubscribe** — Memory leak in long-lived workspace tabs; over a day, accumulates dozens of stale handlers and turns one save into many `refreshApex` calls.
2. **PII in localStorage** — Same-origin readable by any LWC; not encrypted; persists. Use opaque draft IDs and server-side draft storage.
3. **Cross-tab as a primary correctness mechanism** — Server-side events (CometD / Pub-Sub) are correct for "the data has changed" notifications across users, sessions, and devices. Cross-tab is purely a same-user same-browser quality-of-life enhancement.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Lightning Web Security — https://developer.salesforce.com/docs/platform/lightning-components-security/guide/intro-lws.html
- MDN BroadcastChannel — https://developer.mozilla.org/en-US/docs/Web/API/BroadcastChannel
