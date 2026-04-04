# Well-Architected Notes — LWC Toast And Notifications

## Relevant Pillars

- **User Experience** — The primary pillar for this skill. Choosing the wrong notification primitive (a sticky toast for a simple success, a blocking alert where toast is sufficient) directly degrades the experience. Salesforce Well-Architected defines user experience quality in terms of discoverability, appropriate feedback timing, and respecting the user's attention budget. Toast and confirm patterns are the main mechanism for communicating system state changes in Lightning Experience.
- **Reliability** — Notifications that fail silently (toast in Experience Cloud) or that are accidentally dismissed (non-sticky error toasts) erode user trust in the system. A reliable component uses the primitive appropriate for the deployment context and uses `sticky` for errors that must be acknowledged.
- **Security** — Indirect applicability. Confirmation dialogs before destructive DML operations (`lightning-confirm`) are a UX-level safeguard against accidental data destruction. They do not replace server-side permission checks but do reduce the frequency of support escalations from accidental bulk operations.

## Architectural Tradeoffs

**Toast vs. lightning-alert:** Toast is non-blocking — the user can continue working while it is visible. `lightning-alert` is modal: execution pauses at the `await` and resumes only after dismissal. Use `lightning-alert` sparingly, only when the message is a true prerequisite for the next user action. Overusing `lightning-alert` trains users to dismiss it reflexively without reading it.

**lightning-confirm vs. LightningModal for destructive gates:** `lightning-confirm` is appropriate when the decision is a single binary question. If the destructive action requires additional context, a record name to verify, or a second option (e.g., archive vs. delete), use `LightningModal` instead so the interaction has room to breathe without cramming complexity into a single dialog line.

**Toast in multi-context components:** A component deployed to both Lightning Experience and Experience Cloud needs two notification paths. Adding a context-detection branch is the correct tradeoff — it adds a small amount of code but prevents silent failures that are hard to debug after deployment. Document the branch with a comment explaining why the dual path exists.

## Anti-Patterns

1. **Using `sticky` mode for all toasts** — treats every system message as equally urgent, which dilutes the signal for messages that actually require attention. Users learn to dismiss all toasts instantly, defeating the purpose of `sticky` for real errors.
2. **Using `ShowToastEvent` without verifying the deployment context** — a component that works perfectly in a sandbox Lightning page and silently breaks in a customer-facing Experience Cloud site. The failure mode has no visible error, making it difficult to diagnose from logs alone.
3. **Using `window.alert()` or `window.confirm()` in LWC** — these native browser calls are intercepted by Locker Service and behave inconsistently across deployment contexts. Locker does not throw an error, making the bug appear intermittent. The platform-native primitives (`ShowToastEvent`, `lightning-alert`, `lightning-confirm`) are the correct replacement.

## Official Sources Used

- LWC ShowToastEvent documentation — https://developer.salesforce.com/docs/component-library/bundle/lightning-platform-show-toast-event/documentation
- lightning-alert component documentation — https://developer.salesforce.com/docs/component-library/bundle/lightning-alert/documentation
- lightning-confirm component documentation — https://developer.salesforce.com/docs/component-library/bundle/lightning-confirm/documentation
- LWC Salesforce modules reference — https://developer.salesforce.com/docs/atlas.en-us.lwc.meta/lwc/reference_salesforce_modules.htm
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
