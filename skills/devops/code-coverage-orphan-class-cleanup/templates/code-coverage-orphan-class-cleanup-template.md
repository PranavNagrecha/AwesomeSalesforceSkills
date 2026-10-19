# Code Coverage Orphan Class Cleanup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `code-coverage-orphan-class-cleanup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Org-wide coverage now, and the gap to 75%:
- Date and test level of the last clean run that refreshed `ApexCodeCoverageAggregate`:
- Candidate list query (with `NamespacePrefix = NULL` filter):
- Failure modes to watch for: REST entry points, Flow actions, Setup-only schedules

## Approach

Pattern chosen (pre-deploy coverage rescue / scheduled tech-debt cleanup / package-deprecation cleanup) and why:

## Checklist

- [ ] Coverage data refreshed via clean local-tests run, not a stale snapshot
- [ ] Each candidate verified against four orphan criteria (coverage, source ref, metadata ref, REST entry)
- [ ] Active `CronTrigger` schedules checked for every `Schedulable` candidate
- [ ] Sandbox deploy of the destructive manifest passes all tests
- [ ] Org-wide coverage measured before and after; delta documented

## Notes

Deviations from the standard pattern and why:
