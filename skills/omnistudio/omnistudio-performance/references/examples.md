# Examples — OmniStudio Performance

## Example 1: Consolidating Five Per-Step DataRaptor Calls Into One Integration Procedure

**Context:** A commercial insurance quoting OmniScript had a step that displayed account summary, open opportunities, recent cases, active policies, and billing status. Each piece of data was fetched via a separate DataRaptor Extract Action element on the same step. Users reported the step taking 4–6 seconds to load on average.

**Problem:** Five independent DataRaptor calls fired serially on step entry. Each call completed before the next started because OmniScript executed the elements in sequence. With an average 800ms per DataRaptor round trip, the step accumulated 4+ seconds of serialized latency before rendering anything useful.

**Solution:**

Create a single Integration Procedure `IP_AccountSummaryBundle` with five DataRaptor Extract elements inside it, each mapped to a named output key:

```text
IP_AccountSummaryBundle
├── DR Extract: Account Summary      → output key: AccountSummary
├── DR Extract: Open Opportunities   → output key: Opportunities
├── DR Extract: Recent Cases         → output key: Cases
├── DR Extract: Active Policies      → output key: Policies
└── DR Extract: Billing Status       → output key: BillingStatus
```

Replace the five Action elements on the OmniScript step with a single Integration Procedure Action element calling `IP_AccountSummaryBundle`. Map the output keys to the OmniScript JSON node structure as before.

**Why it works:** The IP bundles all five queries into a single synchronous server-side call. All DataRaptors run inside Apex on the server before the response returns. Network round trips drop from five to one. Observed step load time in this scenario dropped from ~4.5 seconds to under 900ms.

---

## Example 2: DataRaptor Caching For A Read-Heavy Account Context Step

**Context:** A field service OmniScript loaded account contact information on every step because the technician could navigate back and forward freely. The same `DR_Extract_AccountContacts` fired on each forward or backward navigation that returned to the contacts step, regardless of whether anything had changed.

**Problem:** The account contact data was static for the duration of the OmniScript session (the technician was not editing contacts). Re-querying on every navigation event wasted SOQL queries and added 600–800ms on each revisit.

**Solution:**

On the `DR_Extract_AccountContacts` DataRaptor Extract asset, enable response caching and configure the cache key:

```text
Cache Key:  AccountId:{!OmniScriptContext.AccountId}
Cache Duration: Session
```

With this configuration, the first call on the step fires the SOQL query. Subsequent visits within the same OmniScript session return the cached result with no network call. The step transition drops from ~700ms to under 100ms on revisit.

**Why it works:** The cache key is tied to the AccountId from the OmniScript context. Two OmniScript sessions for different accounts get separate cache entries. Within one session, the result is reused. Because contacts are not being edited in this OmniScript, stale data is not a concern within the session window.

---

## Example 3: Fire-And-Forget Async Integration Procedure For Activity Logging

**Context:** A wealth management OmniScript submitted a recommendation to a client. At submission, an Integration Procedure created an Activity record, sent an email notification, and called an external compliance logging API. The user had to wait 3–5 seconds after clicking Submit before the confirmation screen appeared.

**Problem:** All three operations ran synchronously as part of the submit flow. The external compliance API accounted for most of the latency. None of these operations needed to return data to the OmniScript — the confirmation screen did not depend on the activity ID, email status, or compliance log response.

**Solution:**

Split the submit IP into two:

- `IP_SubmitRecommendation_Sync` — handles only the operations whose results the OmniScript needs (record update, response context).
- `IP_PostSubmitSideEffects_Async` — handles activity creation, email, and external compliance call.

In the OmniScript submit action, invoke `IP_SubmitRecommendation_Sync` synchronously, then invoke `IP_PostSubmitSideEffects_Async` as an asynchronous fire-and-forget call. Remove any data mappings that read from the async IP's output.

**Why it works:** The user's confirmation screen appears after the sync IP completes (typically under 500ms). The side-effect IP runs in the background. External API latency is fully removed from the user-visible path. The async IP includes its own error handling and retry logic for the external compliance call.

---

## Anti-Pattern: Enabling DataRaptor Caching On An Actively-Edited Record

**What practitioners do:** A DataRaptor Extract that reads the record being edited in the OmniScript has caching enabled with the record Id as the cache key. The goal is to avoid re-querying the record on step transitions.

**What goes wrong:** The user edits field values on earlier steps. When they navigate forward to a step that calls the cached DataRaptor, the cache returns the pre-edit state of the record from Salesforce. The OmniScript displays stale values, overwriting the user's edits if there is a data mapping that writes from the DataRaptor output to the OmniScript JSON node.

**Correct approach:** Only cache DataRaptors that read data the current OmniScript session does not modify. For actively-edited records, either disable caching or use a different cache key that incorporates a session-unique token so each OmniScript instance starts with a fresh entry. A simpler approach is to refetch the active record only once at session start using a pre-population IP, then pass the data through the OmniScript JSON state without re-querying.
