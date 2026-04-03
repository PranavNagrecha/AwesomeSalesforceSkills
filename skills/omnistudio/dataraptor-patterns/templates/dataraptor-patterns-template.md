# DataRaptor Patterns — Work Template

## Scope

**Skill:** `dataraptor-patterns`

**Request summary:** Describe the OmniStudio data problem and the current asset choice.

## Context Gathered

- Read, transform, or write responsibility:
- Caller and output contract:
- Performance expectations:
- Signs the asset is taking on orchestration work:

## Selected Pattern

- Extract, Turbo Extract, Transform, Load, or move out to IP/Apex:
- Why this choice fits:
- What contract or maintainability constraint matters most:

## Checklist

- [ ] DataRaptor type matches the responsibility
- [ ] Turbo Extract is used only for the right narrow case
- [ ] Mapping remains readable
- [ ] Load assets have safe write assumptions
- [ ] IP or Apex was considered where orchestration is growing

## Notes

Record any performance tradeoff or caller-contract dependency.
