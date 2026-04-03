# Well-Architected Mapping: Formula Fields

## Pillars Addressed

### Performance

Formula fields are easy to create and easy to overuse.

- Careful cross-object usage prevents avoidable reporting and page-load pain.
- Simple formulas reduce admin tendency to offload all logic into runtime recalculation.

### Reliability

Good formulas return the right value for real-world edge cases.

- Explicit blank handling reduces misleading outputs.
- Correct tool choice prevents formula fields from being misused as historical snapshots.

### Operational Excellence

Readable formulas are maintainable formulas.

- Documentation and simpler expressions reduce admin handoff risk.
- Review discipline prevents nested formula debt from spreading across the org.

## Pillars Not Addressed

- **Security** - formula design does not directly govern record access.
- **User Experience** - formulas can help UX, but this skill is about correctness and maintainability first.

## Official Sources Used

- Salesforce Well-Architected Overview — performance and maintainability framing for formula usage
- Object Reference — object and relationship semantics behind formula references
- Metadata API Developer Guide — formula metadata behavior during deployment
