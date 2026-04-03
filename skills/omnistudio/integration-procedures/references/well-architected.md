# Well-Architected Mapping: OmniStudio Integration Procedures

---

## Pillars Addressed

### Reliability
`rollbackOnError: true` prevents partial data writes. `failOnStepError: true` ensures failures propagate and don't get swallowed. Fault handling on every step means no silent failures.

- WAF check: `rollbackOnError: true` in root `propertySetConfig`?
- WAF check: All steps have meaningful `failureResponse` (no placeholder text)?
- WAF check: Business-level error responses checked with Decision step after HTTP actions?

### Security
Named Credentials for all external callouts — no hardcoded URLs or tokens. Output contract strips internal fields before returning to OmniScript/FlexCard — no internal data leakage.

- WAF check: Every HTTP action uses a Named Credential?
- WAF check: Output contract documented — internal fields not exposed to caller?

### Performance
`chainableQueriesLimit: 50` and `chainableCpuLimit: 2000` prevent governor limit overruns. HTTP timeout configured to match external service SLA — no indefinite waits.

- WAF check: `chainableQueriesLimit` and `chainableCpuLimit` configured?
- WAF check: Every HTTP action has explicit `timeout` in `restOptions`?

### Operational Excellence
Input/output contracts documented before build. Step descriptions explain what each step does and why. No placeholder text in error messages.

- WAF check: IP description explains purpose, caller, and external system?
- WAF check: Every step has a `description` (not just a label)?
- WAF check: Input/output contract documented?

## Official Sources Used

- Salesforce Well-Architected Overview — reliability and operational framing for orchestration design
- REST API Developer Guide — request and response behavior grounding for external interactions
- Integration Patterns — sync and async system-boundary tradeoffs for IP design
