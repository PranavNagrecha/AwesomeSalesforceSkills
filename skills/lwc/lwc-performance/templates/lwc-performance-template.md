# LWC Performance — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `lwc-performance`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Setting / configuration:
- Slowness profile:
- Current data path:
- Optional UI that can be deferred:
- Known constraints such as Experience Cloud, managed package, or LWS:

## Approach

Pick the dominant optimization pattern:

- [ ] Data-minimized read model
- [ ] Progressive disclosure / lazy instantiation
- [ ] Bounded lists with stable keys
- [ ] Dynamic component loading

Decision summary:

- Why this pattern fits:
- What alternatives were rejected:
- What evidence supports the bottleneck call:

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Cheapest viable data path selected before custom Apex
- [ ] Explicit field list used instead of layout-based record fetch
- [ ] Optional UI gated with `lwc:if`, tab activation, or builder visibility
- [ ] Lists use stable non-index keys and bounded item count
- [ ] Legacy `if:true` / `if:false` directives removed or intentionally retained with justification
- [ ] Object and array updates use reassignment or deliberate `@track`
- [ ] Dynamic import justified and validated against LWS plus package constraints

## Notes

Record deviations, measurement notes, and any platform constraints that prevented the preferred pattern.
