# Well-Architected Notes — LWC Imperative Apex

## Relevant Pillars

- **Security** — Every imperative Apex call crosses a trust boundary. The Apex class must enforce sharing rules, CRUD, and FLS explicitly. LWC running as a guest user or community user can call `@AuraEnabled` methods, so the Apex must not assume authenticated context unless `with sharing` is enforced and additional checks are in place.
- **Performance** — Each imperative call is a synchronous Apex execution and a network round-trip. Use `cacheable=true` for read-only data to allow the Lightning Data Service cache to serve repeat calls without a round-trip. Use `Promise.all` to parallelize independent calls rather than sequencing them.
- **Reliability** — Every imperative call can fail due to network issues, Apex exceptions, or governor limit violations. All calls must have a `catch` block that sets a visible error state. Silent catch blocks (`catch (e) {}`) mask real failures.
- **Operational Excellence** — Descriptive `AuraHandledException` messages make production issues debuggable. Log unexpected exceptions in Apex before rethrowing so they appear in event log files.

## Architectural Tradeoffs

**Imperative vs Wire:** Imperative calls give the component direct control over when data loads and when it refreshes. Wire gives the framework control and provides automatic reactivity to property changes. Choose wire when the data must stay in sync with reactive parameters; choose imperative when the trigger is an explicit user action or a one-shot lifecycle event.

**cacheable vs non-cacheable:** Marking a method `cacheable=true` allows the LDS cache to serve results without a server round-trip on repeat calls, but completely prohibits DML anywhere in the execution path. Non-cacheable methods are always fresh but incur a network round-trip every time. Do not use `cacheable=true` as a general performance optimization unless the data is genuinely read-only across the entire call stack.

**Promise.all vs sequential awaits:** Sequential `await` chains are easier to read and debug, but each call waits for the prior round-trip to complete. For two independent Apex calls, `Promise.all` can cut perceived load time in half on slow connections. Use sequential `await` only when the second call depends on the result of the first.

## Anti-Patterns

1. **Calling Apex in a loop** — Calling an Apex method inside a `forEach` or `map` over a list of records creates one network request and one Apex execution per item. This hits governor limits quickly. Instead, pass the full list to a single Apex method and let Apex bulk-process it.

2. **Using without sharing for LWC-facing Apex** — `without sharing` bypasses record-level security. Any user who can load the LWC component can then access records they should not see. Always use `with sharing` unless there is an explicit, documented reason to elevate sharing (for example, a background job running as an admin context), and in that case use `inherited sharing` or a dedicated inner class, not `without sharing` on the top-level class.

3. **Swallowing errors silently** — A `catch` block that updates no reactive property leaves the user staring at a spinner that never resolves or a blank component with no message. Always set an error state and surface a message, even if it is a generic fallback.

4. **Reading data on every component mount with no caching** — Calling a non-cacheable Apex method in `connectedCallback` on a component that re-mounts frequently (for example, inside a loop or a dynamic data table) bypasses all caching and creates a server call every time. Use `cacheable=true` for read-only data to allow the LDS cache to absorb repeat calls.

## Official Sources Used

- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- LWC Best Practices for Development — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Secure Apex Classes (LWC guide) — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
