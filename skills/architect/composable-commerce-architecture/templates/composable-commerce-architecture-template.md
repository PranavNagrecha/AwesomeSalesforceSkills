# Composable Commerce Architecture — Work Template

Use this template when working on tasks in this area. Fill every field; write "not applicable" with a reason rather than leaving a field blank.

## Scope

**Skill:** `composable-commerce-architecture`

**Request summary:** (one sentence: what the requester asked for)

## Context Gathered

Answers to the Questions to Ask Before Configuring in SKILL.md:

| Question | Answer | Source (person, document, or query) |
|---|---|---|
| Platform per journey (B2C Commerce SCAPI, or B2B/D2C on the core org) | | |
| Uncached BFF-to-org calls per session at peak; longest expected call | | |
| Peak SLAS login + refresh RPM per instance (production and staging) | | |
| SLAS client type per component (private for BFF, public for browser) | | |
| Journeys kept on SFRA during phasing; frontend for the rest | | |
| Per-route behavior on SCAPI 503 and 429 | | |

## Limit Budget

| Pool | Allowance | Planned peak use | Headroom | Source |
|---|---|---|---|---|
| Core org 24-hour API allocation | 100,000 + licences x calls per licence type | | | Limits Quick Reference |
| Core org long-running (20 s+) concurrency | 25 (production, sandbox) | | | Limits Quick Reference |
| SLAS, production instance | 24,000 RPM | | | SCAPI Load Shedding and Rate Limiting |
| SLAS, each non-production instance | 500 RPM | | | SCAPI Load Shedding and Rate Limiting |

## Approach

Which pattern from SKILL.md applies (Next.js storefront with SCAPI + BFF, multi-brand single Commerce Cloud, or incremental decomposition), and why the shipped storefront or PWA Kit was not chosen:

## Checklist

- [ ] Capability gap analysis shows composable is warranted
- [ ] BFF registered as a SLAS private client with Strict Client Auth; no secret in browser code
- [ ] BFF contract versioned and documented
- [ ] Caching strategy defined per route (edge / origin), with a stale-serve rule on `sfdc_load_status` WARN
- [ ] Every BFF-to-org call has a client timeout below 20 seconds and at most one retry
- [ ] Shopper identity derived from a verified token; every org query scoped by it
- [ ] Guest session rotated after order confirmation
- [ ] PCI scope minimized (checkout on hosted payment or tokenized)
- [ ] Observability: RUM, BFF logs, Commerce Cloud API metrics joined
- [ ] Rollback plan to shipped storefront documented

## Decisions And Deviations

Record each deviation from the patterns in SKILL.md, the reason, and the ADR number that holds it. Name any part of the design that is outside formal support (for example, session bridging between a custom frontend and SFRA) and its owner.
