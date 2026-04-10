# Well-Architected Notes — SSJS Server-Side JavaScript

## Relevant Pillars

- **Security** — SSJS running in Script Activities or Cloud Pages can read and write Data Extensions containing PII. Tokens, API keys, and credentials must never be hardcoded in SSJS source. Store secrets in a protected Data Extension with field-level encryption and retrieve them at runtime via `Platform.Function.Lookup()`. Cloud Pages that accept form input must validate and sanitize all user-supplied values before using them in WSProxy filter properties — unsanitized input can cause unintended data exposure.

- **Performance** — SSJS Script Activities are procedural and single-threaded. Looping over large datasets in SSJS is orders of magnitude slower than an equivalent SQL Query Activity operating on the same data set-based. Use SSJS for logic that cannot be expressed in SQL (API calls, conditional branching, stateful operations), and delegate bulk data transformation to Query Activities. WSProxy retrieve paging must be handled to avoid truncated results; however, paging also means large retrieves carry significant latency.

- **Reliability** — Uncaught exceptions in Script Activities cause the step to fail with a generic error and no diagnostic information. Proper `try/catch` blocks with `Write()` logging, combined with error-logging to a Data Extension, are the primary mechanisms for operational visibility. Script Activities have no built-in retry logic — Automation Studio marks a failed step as an error and stops (unless the Automation is configured to continue on error, which can cause downstream data integrity issues). Design critical Activities to be idempotent: if re-run after a failure, they should produce the same correct outcome.

- **Operational Excellence** — Script Activity execution is asynchronous and scheduler-driven. There is no real-time triggering (SSJS in a Script Activity cannot be invoked on-demand the same way a REST API endpoint can). The 30-minute timeout is a hard operational constraint that must inform solution design. Use `Write()` output and error-logging Data Extensions as the primary observability mechanisms, since Marketing Cloud does not provide structured application logging for SSJS.

## Architectural Tradeoffs

**WSProxy vs. raw HTTP for SOAP calls:** WSProxy is always preferred for Marketing Cloud SOAP API operations. The only reason to use `Script.Util.HttpRequest` for a SOAP call is when the target endpoint is a third-party SOAP service that WSProxy cannot reach. Raw HTTP SOAP construction adds significant maintenance burden and is fragile at token refresh boundaries.

**SSJS loops vs. SQL Query Activities:** For set-based data operations (filtering, joining, aggregating Data Extensions), SQL Query Activities are the architecturally correct choice. SSJS loops are appropriate only when the logic cannot be expressed in SQL — for example, when making per-record API calls or when the transformation requires state that SQL cannot maintain.

**Script Activity vs. Cloud Page SSJS:** Script Activities are the appropriate context for data processing, API orchestration, and Automation-driven logic. Cloud Pages are request/response — SSJS there runs synchronously within a web request, making it appropriate for form processing or REST-like endpoints, but not for long-running batch operations. Never put a data volume loop in a Cloud Page SSJS block.

## Anti-Patterns

1. **Hardcoding API tokens in SSJS source** — SSJS source is visible to anyone with access to the Script Activity in Automation Studio or the Content Builder block. Tokens hardcoded in source are exposed to all Marketing Cloud users with that permission level and cannot be rotated without code changes. Store tokens in an encrypted Data Extension field and retrieve with `Platform.Function.Lookup()` at runtime.

2. **No try/catch in Script Activities** — Without `try/catch`, any exception (network timeout, malformed JSON, WSProxy filter error, API 4xx/5xx) causes the Activity step to fail with no actionable error message in the Activity log. Practitioners then spend significant time diagnosing failures that would have been immediately obvious with a one-line `Write(e.message)` in the catch block.

3. **Processing unbounded data volumes in a single Script Activity** — Architectures that attempt to process all records in a large Data Extension in a single SSJS Script Activity will hit the 30-minute timeout as data grows. The correct pattern is to use SQL Query Activities for data reduction before the SSJS step, or to implement cursor-based chunking with state tracked in a dedicated Data Extension.

## Official Sources Used

- SSJS Overview — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/ssjs_overview.html
- WSProxy Documentation — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/ssjs_wsproxy.html
- HTTP Functions (Script.Util.HttpRequest) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/ssjs_httpFunctions.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
