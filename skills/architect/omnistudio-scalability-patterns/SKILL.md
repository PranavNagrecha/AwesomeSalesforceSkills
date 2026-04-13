---
name: omnistudio-scalability-patterns
description: "Use when OmniStudio components are degrading under high concurrent user load, when Integration Procedures are hitting governor limits at portal scale, or when designing an OmniStudio deployment for thousands of simultaneous Experience Cloud users. Trigger keywords: OmniScript concurrency, Integration Procedure SOQL limits portal, Queueable Chainable, Direct Platform Access, LWR CDN Experience Cloud high volume. NOT for generic scalability planning (use architect/limits-and-scalability-planning), NOT for single-session performance tuning (use omnistudio/omnistudio-performance)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Performance
  - Reliability
  - Operational Excellence
tags:
  - omnistudio
  - integration-procedure
  - omniscript
  - queueable-chainable
  - ip-chainable
  - direct-platform-access
  - lwr
  - cdn
  - experience-cloud
  - high-volume
  - concurrency
  - governor-limits
  - async-apex
  - caching
triggers:
  - "OmniScript performance degrading under high concurrent user load on Experience Cloud portal"
  - "Integration Procedure hitting SOQL limits or CPU limits when many portal users are active simultaneously"
  - "how to scale OmniStudio for high-volume Experience Cloud with hundreds or thousands of concurrent users"
  - "Queueable Chainable vs fire-and-forget for Integration Procedure governor limit relief"
  - "Direct Platform Access mode for Integration Procedures in Spring 25"
inputs:
  - "Peak concurrent user count on the Experience Cloud portal or OmniStudio channel"
  - "Integration Procedure design: element types, SOQL counts, HTTP callout targets"
  - "OmniScript complexity: number of steps, DataRaptor calls, conditional branching depth"
  - "Current async execution mode selection (fire-and-forget, IP Chainable, Queueable Chainable)"
  - "Org edition and whether Spring '25+ Direct Platform Access is enabled"
  - "LWR vs. Aura runtime for the Experience Cloud site"
  - "CDN configuration status for the portal"
outputs:
  - "Concurrency risk assessment for the OmniStudio deployment"
  - "Integration Procedure governor limit headroom analysis"
  - "Async execution mode recommendation (fire-and-forget vs. IP Chainable vs. Queueable Chainable)"
  - "Direct Platform Access enablement guidance"
  - "LWR + CDN deployment checklist for high-volume Experience Cloud"
  - "Caching strategy for Integration Procedures"
  - "Escalation criteria for MuleSoft middleware at extreme scale"
  - "Filled omnistudio-scalability-patterns-template.md"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

Use this skill when OmniStudio components — OmniScripts, Integration Procedures, FlexCards — degrade under high concurrent user load or when designing an OmniStudio deployment to serve thousands of simultaneous Experience Cloud portal users. It covers multi-user concurrency patterns, governor limit management across sessions, and the platform-level execution modes that allow Integration Procedures to escape Apex governor ceilings. It does NOT cover single-session performance tuning (use `omnistudio/omnistudio-performance`) and does NOT cover generic org scalability planning (use `architect/limits-and-scalability-planning`).

---

## Before Starting

- **What is the peak concurrent user count?** Concurrent long-running Apex requests are capped at 25 org-wide for requests lasting more than 20 seconds. Portal deployments exceeding this threshold will queue or error without proper async design.
- **Which async execution mode is the Integration Procedure using?** Fire-and-forget (`useFuture: true`) removes UI blocking but does NOT escape governor limits. Queueable Chainable runs the next IP step as async Apex with the full 60-second CPU and 12MB heap limits. These solve different problems.
- **Is Spring '25+ Direct Platform Access enabled?** This mode bypasses Apex CPU governors entirely for read-heavy Integration Procedures using native Salesforce data access. It is not yet available for write operations or external callouts.
- **Is the Experience Cloud site running on LWR (Lightning Web Runtime)?** LWR with CDN caching is required for high-volume portals; Aura-based sites do not benefit from CDN page caching and will not scale to thousands of concurrent users.

---

## Core Concepts

### IP Chainable vs. Queueable Chainable — Two Different Problems

OmniStudio Integration Procedures offer two distinct async mechanisms that are frequently confused:

**IP Chainable** links multiple Integration Procedures into a sequential chain, where each IP calls the next. IP Chainable runs synchronously within the same Apex transaction. It does not escape governor limits — all chained IPs share the same SOQL, CPU, and DML ceilings as the original transaction. IP Chainable is used for modularity and separation of concerns, not for governor limit relief.

**Queueable Chainable** runs the next Integration Procedure step as a Queueable Apex job — a genuinely async transaction with a fresh governor limit context. When the Queueable runs, it receives:
- CPU time: 60,000ms (6x the synchronous 10,000ms limit)
- Heap: 12MB (2x the synchronous 6MB limit)
- Fresh SOQL and DML quotas

Queueable Chainable is the correct mechanism when an IP step would breach governor limits under portal concurrency — not just when you want to avoid blocking the UI. The UI unblocking is a side effect; the purpose is governor limit escape.

**When to use each:**
- IP Chainable: modular IP design, separation of concerns, no governor limit pressure
- Fire-and-forget (`useFuture: true`): remove UI blocking for long-running operations when governor limits are not the constraint
- Queueable Chainable: any IP step that hits SOQL, CPU, or DML limits under concurrent portal load

### Concurrent Long-Running Apex Limit — The Org-Wide Ceiling

Salesforce enforces a hard limit of **25 concurrent long-running Apex requests** across the entire org. A request is "long-running" if it takes more than 20 seconds to complete. This limit is shared across all Apex execution contexts: triggers, future methods, Queueable jobs, Integration Procedures running via Apex, and more.

At a busy Experience Cloud portal with hundreds of simultaneous users submitting OmniScripts that invoke complex Integration Procedures, this ceiling is reached faster than many architects expect. When the 25-request ceiling is hit, additional requests queue or return errors — not timeout errors, but capacity errors that surface as OmniScript failures to users.

Mitigation strategies:
- Ensure IPs complete well under 20 seconds for the common case; only route genuinely long operations to Queueable Chainable
- Use caching (see below) to reduce redundant IP executions that all hit the same data
- Use Direct Platform Access mode for read-heavy IPs to reduce CPU time consumption

### Spring '25+ Direct Platform Access Mode

Introduced in Spring '25, Direct Platform Access (DPA) is an Integration Procedure execution mode that bypasses Apex CPU governors for read operations. Instead of routing data access through the Apex runtime (which accumulates CPU time toward the 10,000ms synchronous or 60,000ms async limit), DPA accesses Salesforce platform data natively, outside the Apex governor loop.

**Critical constraints:**
- DPA applies only to read operations: SOQL queries, DataRaptor Extracts, and Salesforce Object operations in read mode
- Write operations (insert, update, delete) still execute through Apex and consume CPU governors
- DPA requires LWR (Lightning Web Runtime) as the page runtime — it is not available on Aura-based Experience Cloud sites
- DPA must be explicitly enabled in the Integration Procedure's execution settings; it is not the default

For read-heavy portal IPs — member account lookups, product catalog queries, case history retrievals — enabling DPA can dramatically reduce CPU governor consumption, allowing more concurrent sessions to complete within limits.

### LWR + CDN for High-Volume Experience Cloud

Standard Experience Cloud page delivery (both Aura and LWR) renders page structure per request. At high concurrency, the Apex and server-side rendering load grows linearly with active users.

**Lightning Web Runtime (LWR)** enables CDN-level caching for Experience Cloud pages:
- Static page shells, component JavaScript bundles, and CSS are cached at the CDN edge
- Only dynamic data (Apex calls, Integration Procedure responses) hits the Salesforce servers
- CDN dramatically reduces the per-user server load for page initialization

Without LWR + CDN, a portal serving 2,000 concurrent users will load-test the Salesforce application servers with full page rendering for each session. With LWR + CDN, a large fraction of that load is absorbed by the CDN edge network.

**LWR + CDN is not optional for high-volume Experience Cloud deployments.** It is a prerequisite for portal scalability, not a nice-to-have optimization.

### Caching Strategies Within Integration Procedures

Repeated identical IP executions from concurrent users hitting the same data are a major source of unnecessary governor limit consumption. OmniStudio provides two caching levers within Integration Procedures:

- **IP-level caching:** The Integration Procedure can cache its output at the IP level for a configurable TTL. Multiple users requesting the same IP with the same inputs will receive the cached response; only the first request in the TTL window executes against the database.
- **DataRaptor Extract caching:** Individual DataRaptor Extract elements within an IP can cache query results. This is effective for relatively static reference data (product catalogs, configuration tables, enumeration values).

Cache TTL should reflect data freshness requirements. For near-real-time transactional data (account balances, order statuses), caching is inappropriate. For reference data that changes infrequently, a TTL of 5–60 minutes can eliminate the majority of redundant database calls under high concurrency.

### When to Escalate to MuleSoft

OmniStudio Integration Procedures are the right tool for most Salesforce-native integrations. At extreme scale, middleware escalation becomes appropriate:

| Signal | Implication |
|---|---|
| Peak concurrent sessions > 500 with complex IPs | Queueable Chainable + DPA may not be enough; MuleSoft can offload processing |
| External API rate limits are the bottleneck, not Salesforce governors | MuleSoft provides rate limiting, circuit breakers, and retry logic that OmniStudio lacks |
| IP response aggregates data from 5+ external systems | MuleSoft is better suited to fan-out/fan-in orchestration patterns |
| Sub-second response time SLAs under full load | MuleSoft's dedicated compute does not share Salesforce governor pools |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| IP blocks UI but governor limits are not a concern | Fire-and-forget (`useFuture: true`) | Removes UI blocking; simpler than Queueable Chainable |
| IP hits SOQL or CPU limits under concurrent portal load | Queueable Chainable for the offending step | Escapes governor limits with a fresh async transaction |
| Read-heavy IP consuming Apex CPU on a Spring '25+ org | Enable Direct Platform Access mode | Bypasses CPU governors for data-read steps |
| High-volume Experience Cloud portal (hundreds+ concurrent) | LWR runtime + CDN + IP-level caching | Reduces per-user server load and redundant IP executions |
| Reference data queried on every portal session | DataRaptor Extract caching with appropriate TTL | Eliminates redundant SOQL across concurrent sessions |
| IP aggregates 5+ external APIs at extreme scale | Escalate to MuleSoft for orchestration layer | OmniStudio is not designed as a heavy-fan-out orchestrator |
| Complex IPs chained for modularity only | IP Chainable | Correct use case; does not require async governor relief |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Establish the concurrency baseline** — determine peak concurrent user count, typical IP execution time, and whether any IP has been observed to exceed 20 seconds. Cross-reference against the 25-concurrent-long-running-Apex org-wide limit.
2. **Audit async execution modes** — review every Integration Procedure for its current execution mode (synchronous, fire-and-forget, IP Chainable, Queueable Chainable). Identify any IPs that are using fire-and-forget as a workaround for governor limit errors — these require Queueable Chainable, not fire-and-forget.
3. **Enable Direct Platform Access for eligible IPs** — identify read-heavy IPs on a Spring '25+ org with LWR. Enable DPA in execution settings. Verify that no write operations are present in the same IP path (write steps still require Apex execution).
4. **Validate LWR + CDN configuration** — confirm the Experience Cloud site is on LWR runtime. Confirm CDN caching is configured for static assets. Measure page load under simulated concurrent load before and after CDN enablement.
5. **Implement IP-level and DataRaptor caching** — identify reference data and low-churn queries within IPs. Configure IP output caching and DataRaptor Extract caching with TTLs appropriate to data freshness requirements.
6. **Load test and monitor** — simulate peak concurrent user load in a full-copy sandbox. Monitor Apex Flex Queue depth, Queueable job completion times, and the concurrent long-running Apex metric in Setup > Apex Jobs. Flag any sustained pressure on the 25-request ceiling.
7. **Document escalation criteria** — record the thresholds (concurrent users, IP complexity, external API count) at which MuleSoft middleware should be evaluated. Include this in the architecture decision log.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Peak concurrent user count is documented and cross-referenced against the 25-concurrent-long-running-Apex limit
- [ ] Every Integration Procedure's async execution mode (fire-and-forget vs. Queueable Chainable) matches its actual need (UI unblocking vs. governor limit escape)
- [ ] Direct Platform Access is enabled for read-heavy IPs on Spring '25+ orgs with LWR
- [ ] The Experience Cloud site is confirmed on LWR runtime with CDN caching active
- [ ] IP-level and DataRaptor caching is configured with appropriate TTLs for reference data
- [ ] MuleSoft escalation criteria are documented in the architecture decision record

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Fire-and-forget does NOT escape governor limits** — `useFuture: true` on an Integration Procedure removes the UI blocking wait but the IP still executes within a future Apex context with the same SOQL and DML limits (100 SOQL, 150 DML). Practitioners who see "limit errors in production" and add fire-and-forget to "fix" it are solving the wrong problem. Queueable Chainable is required to escape limits.
2. **The 25-concurrent-long-running-Apex limit is org-wide, not portal-specific** — this ceiling is shared with all Apex running in the org: batch jobs, triggers, other Queueable processes. A heavy nightly batch job scheduled at the same time as portal peak hours will consume capacity from the portal's concurrent session budget.
3. **Direct Platform Access does not cover write operations** — DPA bypasses Apex CPU governors for read paths only. An Integration Procedure that reads via DPA but also performs an insert or update will still consume Apex CPU for the write steps. Mixed read/write IPs do not fully escape CPU governors.
4. **LWR + CDN is a required prerequisite, not an optional enhancement** — standard Aura-based Experience Cloud sites cannot leverage CDN page caching. Deploying a high-volume portal on Aura and adding caching at the IP level will not compensate for the per-request server rendering cost. LWR must be the site runtime.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| omnistudio-scalability-patterns-template.md | Architecture review template for documenting concurrency baseline, async mode audit, DPA enablement status, and escalation criteria |

---

## Related Skills

- `omnistudio/omnistudio-performance` — single-session performance tuning (NOT this skill): OmniScript step optimization, DataRaptor query tuning for one user's session
- `omnistudio/integration-procedures` — Integration Procedure authoring patterns and safety settings
- `architect/limits-and-scalability-planning` — org-wide governor limit planning across all Apex (not OmniStudio-specific)
- `omnistudio/flexcard-requirements` — FlexCard design patterns, including data source selection at portal scale
- `architect/well-architected-review` — formal Well-Architected review process that includes scalability pillar assessment

## Official Sources Used

- OmniStudio Integration Procedures Help — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_dev_guide.meta/omnistudio_dev_guide/
- Salesforce Governor Limits Reference — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Experience Cloud LWR Sites — https://help.salesforce.com/s/articleView?id=sf.exp_cloud_lwr_intro.htm
