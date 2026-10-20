# Well-Architected Notes — API Governance and Rate Limits

**Reliability:** the 24-hour allocation is a shared, exhaustible resource enforced against the aggregate of all API calls, with no per-consumer isolation, so one consumer's change is every consumer's outage. The governance controls that matter are attribution (a connected app and user per consumer) and admission control (refuse to start a job that cannot fit in measured headroom). Retrying a spent daily allocation consumes the allocation it is waiting for; only the concurrency case recovers with backoff.

**Operational Excellence:** read the org's published meter rather than deriving an estimate. `/limits` reports `Max` and `Remaining` and is documented as accurate within five minutes of consumption, so thresholds belong at 70% and 85%, not 99%. `Sforce-Limit-Info` turns every response into a reading, and API Usage Notifications email a named user at a set percentage. Attribution cannot be reconstructed after the fact — it has to exist before the incident.

**Performance and cost:** the cheapest call is the one not made. `/composite` counts a whole series as one call; Bulk API 2.0 moves volume into few requests; Composite Batch saves round trips but not allocation. Buying add-ons is the last lever, after consumers are measured and fixed.

## Official Sources Used

Corpus: Summer '26 (API 67.0) PDFs; line numbers are `grep -n` positions in the `pdftotext -layout` text. The limits cheat sheet lines below are re-resolved against the Winter '27 (264) edition (2026-10-20); every value is unchanged, the section moved from 262 L469–690 to 264 L31–254.

- Limits cheat sheet (`salesforce_app_limits_cheatsheet.txt`) 264 L31–62 — three limit types; 25 / 5 concurrent requests of 20 seconds or longer; `REQUEST_LIMIT_EXCEEDED`; no limit under 20 seconds (gotcha 4, anti-pattern 1).
- Limits cheat sheet 264 L65–73 — 10-minute REST/SOAP timeout; for composite resources it applies to the whole request (Decision Guidance).
- Limits cheat sheet 264 L76–187 — total allocation table by edition and licence, Full sandbox 5,000,000 (L165); APIs that count (incl. Bulk API 2.0); mobile app calls excluded; `DebuggingHeader` separate 1,000; aggregate, not per user (L181–187) (Core Concepts, gotchas 1 and 3).
- Limits cheat sheet 264 L190–233 — monitoring options, API Usage Notifications, managed-package calls count (L212), over-limit headroom only for paid active orgs (L216–230) (gotchas 6 and 7).
- Limits cheat sheet 264 L249–254 — 115,000-call worked example; rolling 24-hour Developer Edition example (Core Concepts, anti-pattern 1).
- REST API Developer Guide (`api_rest.txt`) L915–932 — `Sforce-Limit-Info: api-usage=<used>/<limit>` on every response (examples.md Example 2).
- REST API Developer Guide L1145–1146 — 403 with `REQUEST_LIMIT_EXCEEDED` when API request limits are exceeded (gotcha 5).
- REST API Developer Guide L7790–7797 — `/limits`: accurate within five minutes; avoid concurrent or rapid requests; View Setup and Configuration (gotcha 6).
- REST API Developer Guide L20745–20755 and L22063–22065 — `/composite` counts as a single call; Composite Batch counts each subrequest (gotcha 2).
- Object Reference (`object_reference.txt`) L33714–33720, L33777, L33791 — `ApiTotalUsageEventLog` (API 61.0+, View Event Log Object Data), `ConnectedAppIdentifier`, `IsApiLimitCounted` (SKILL.md SOQL, gotcha 3).
- REST API Developer Guide L1987–1989 — Summer '24 = API version 61.0 (`salesforce-version`).
