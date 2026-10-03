# Migration Architecture Patterns — Work Template

Use this template when working on tasks in this area. Fill every field; write "not applicable" with a reason rather than leaving a field blank.

## Scope

**Skill:** `migration-architecture-patterns`

**Request summary:** (one sentence: what the requester asked for)

**Direction:** merge (N → 1) / split (1 → N) / coexistence (1 → 1+1 with bridge)

**Driver:** regulatory / M&A / divestiture / limits relief / business-unit autonomy

## Context Gathered

Answers to the Questions to Ask Before Configuring in SKILL.md:

| Question | Answer | Source (person, document, or query) |
|---|---|---|
| External systems that store Salesforce IDs, and in which form (15 or 18 characters) | | |
| Must created dates, creators, and owners survive the move? | | |
| Automation, validation rules, and sharing work active in the target during load | | |
| Coexistence: what crosses the bridge, and how it resyncs after refresh or org migration | | |
| Regulatory split: enforced boundary and sign-off owner | | |
| Logs and archives that must outlive the source org | | |

## Inventories

- Metadata delta map (objects, fields, picklists, validation rules, automation, record types, profiles, permission sets): link
- Data volume per object and parent-child depth: link
- External-system reference list with remapping plan: link

## Approach

Which pattern from SKILL.md applies (A: merge with phased cutover, B: regulatory split, C: permanent coexistence), and why the others were rejected:

## Load Controls

| Control | Setting for this migration |
|---|---|
| External ID field per moving object | |
| Set Audit Fields upon Record Creation enabled for the migration user | |
| Data Loader Time Zone | |
| Data Loader assignment rule setting (leave empty unless intended) | |
| Trigger, flow, and validation bypass flag | |
| Load order (users and roles, records with owners, groups and queues, sharing rules) | |

## Checklist

- [ ] Direction and driver named in writing
- [ ] Metadata audit complete; every delta has a decision
- [ ] External-system inventory complete; remapping table designed on 18-character IDs
- [ ] Audit-field preservation decided and enabled before wave 1
- [ ] Load bypasses defined and the post-load batch for wanted automation planned
- [ ] Coexistence bridge (if any) has a watermark-based resync and a sunset date
- [ ] Regulatory split (if any) has no runtime bridge into protected data
- [ ] Per-wave rollback documented
- [ ] Retention exports scheduled before source decommission
- [ ] Hand-off to the cutover team is explicit

## Decisions And Deviations

Record each deviation from the patterns in SKILL.md, the reason, and the ADR number that holds it.
