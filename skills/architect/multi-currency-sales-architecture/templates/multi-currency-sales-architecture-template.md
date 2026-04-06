# Multi-Currency Sales Architecture — Work Template

Use this template when working on multi-currency architecture tasks in Sales Cloud.

## Scope

**Skill:** `multi-currency-sales-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Multi-currency status:** Is multi-currency enabled? Is ACM enabled? (ACM is irreversible)
- **Currency field inventory:** Which objects carry currency fields? (Opportunity, Quote, custom objects)
- **Rate maintenance method:** Manual entry in Setup / Integration from treasury / Third-party AppExchange
- **Active currencies:** List all active CurrencyIsoCode values and their current static rates
- **Reporting requirements:** Does finance require point-in-time accuracy or current-rate-only views?

## Current State Assessment

| Dimension | Current State | Target State | Gap |
|---|---|---|---|
| ACM enabled? | Yes / No | | |
| Rate update frequency | | | |
| Rate loading method | | | |
| Rate gap monitoring | | | |
| Roll-up summary fields on currency amounts | List them | | |
| Custom objects with currency fields | List them | | |
| Report currency override settings | | | |

## ACM Decision (if applicable)

| Factor | Assessment |
|---|---|
| Need for historical rate accuracy | Yes / No — explain |
| Number of active currencies | |
| Rate change frequency | |
| Custom objects requiring dated conversion | |
| Stakeholder sign-off obtained | Yes / No |
| **Decision** | Enable ACM / Stay with standard multi-currency |
| **Rationale** | |

## Approach

Which pattern from SKILL.md applies and why?

- [ ] Dated Rate Integration Pipeline — needed if ACM enabled and rates change frequently
- [ ] Report Currency Override Strategy — needed if multiple regions consume reports
- [ ] Custom Roll-Up Replacement — needed if roll-up summaries aggregate currency amounts under ACM
- [ ] Point-in-Time Snapshot — needed if finance requires stable historical converted values

## Implementation Plan

1. (Step from Recommended Workflow)
2. (Step from Recommended Workflow)
3. (Step from Recommended Workflow)

## Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] ACM enablement decision is documented with rationale and stakeholder sign-off
- [ ] All active currencies have current exchange rates with no date gaps
- [ ] Roll-up summary fields audited for static-rate-only conversion behavior
- [ ] Reports requiring corporate currency are explicitly overridden
- [ ] Custom objects with currency fields have documented conversion logic
- [ ] Rate maintenance process is automated or has documented manual SOP with monitoring
- [ ] End-to-end test confirms converted amounts match expected values

## Notes

Record any deviations from the standard patterns and why.
